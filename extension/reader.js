// 갈피 리더 뷰 — 좌: 브리핑, 우: Readability로 추출한 기사 본문 (광고 없음).
// 데이터는 chrome.storage.session(메모리 전용)에서 받는다 — 디스크·서버 어디에도 저장되지 않는다 (원문 미저장 원칙).
// 이미지는 원본 URL 참조만 하며 복제하지 않는다.

function el(id) { return document.getElementById(id); }

function showError(msg) {
  const box = el('error');
  box.textContent = msg;
  box.className = 'error show';
  el('spread').style.display = 'none';
}

// Readability 출력 HTML을 확장 페이지에 넣기 전 소독:
// 실행 가능 요소와 이벤트 핸들러, javascript: URL 제거 (확장 CSP가 2차 방어선)
function sanitize(html) {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  doc.querySelectorAll('script, style, iframe, object, embed, form, link, meta, noscript').forEach(e => e.remove());
  doc.querySelectorAll('*').forEach(node => {
    for (const attr of Array.from(node.attributes)) {
      if (/^on/i.test(attr.name)) node.removeAttribute(attr.name);
      if ((attr.name === 'href' || attr.name === 'src') && /^\s*javascript:/i.test(attr.value)) {
        node.removeAttribute(attr.name);
      }
    }
  });
  return doc.body;
}

// 본문 컨테이너의 텍스트 노드에서 용어를 형광펜으로 감싼다 (용어당 최대 5곳)
function highlightTerms(root, terms) {
  const SKIP = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'MARK']);
  const found = new Set();
  for (const term of terms) {
    let count = 0;
    let first = true;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: n => (!n.parentElement || SKIP.has(n.parentElement.tagName)
        || n.parentElement.closest('.galpi-mark'))
        ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      if (count >= 5) break;
      const idx = node.textContent.indexOf(term);
      if (idx === -1) continue;
      const range = document.createRange();
      range.setStart(node, idx);
      range.setEnd(node, idx + term.length);
      const mark = document.createElement('mark');
      mark.className = 'galpi-mark';
      try { range.surroundContents(mark); } catch (e) { continue; }
      if (first) { mark.dataset.galpiFirst = term; first = false; found.add(term); }
      count++;
    }
  }
  return found;
}

function scrollToTerm(term) {
  const mark = document.querySelector(`[data-galpi-first="${CSS.escape(term)}"]`);
  if (!mark) return;
  mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
  mark.classList.add('flash');
  setTimeout(() => mark.classList.remove('flash'), 1400);
}

function renderBriefing(d, foundTerms) {
  el('b-headline').textContent = d.headline;
  el('b-level').textContent = d.level === 'intermediate' ? '중급' : '입문';

  const briefEl = el('b-briefing');
  (d.before_reading || '').split(/\n\n+/).forEach(par => {
    const p = document.createElement('p');
    p.textContent = par.trim();
    if (p.textContent) briefEl.appendChild(p);
  });

  const conceptsEl = el('b-concepts');
  (d.concepts || []).forEach(c => {
    const card = document.createElement('div');
    const inPage = foundTerms.has(c.term);
    card.className = 'concept' + (inPage ? ' clickable' : '');
    const isDoc = c.knowledge_type === '문서내용';
    card.innerHTML = `
      <div class="term-row">
        <span class="term"></span>
        <span class="ktype ${isDoc ? 'doc' : 'gen'}">${isDoc ? '이 글에서' : '일반 지식'}</span>
      </div>
      <div class="expl"></div>
      <div class="why"><b>이 글에서 중요한 이유</b> · <span></span></div>
      ${inPage ? '<span class="find">본문에서 찾기 →</span>' : ''}`;
    card.querySelector('.term').textContent = c.term;
    card.querySelector('.expl').textContent = c.explanation;
    card.querySelector('.why span').textContent = c.why_it_matters_here;
    if (inPage) card.addEventListener('click', () => scrollToTerm(c.term));
    conceptsEl.appendChild(card);
  });

  const bgEl = el('b-background');
  const bgs = d.background || [];
  el('b-bg-label').style.display = bgs.length ? '' : 'none';
  bgs.forEach(b => {
    const card = document.createElement('div');
    card.className = 'concept';
    const isDoc = b.knowledge_type === '문서내용';
    card.innerHTML = `
      <div class="term-row">
        <span class="term"></span>
        <span class="ktype ${isDoc ? 'doc' : 'gen'}">${isDoc ? '이 글에서' : '일반 지식'}</span>
      </div>
      <div class="expl"></div>`;
    card.querySelector('.term').textContent = b.question;
    card.querySelector('.expl').textContent = b.answer;
    bgEl.appendChild(card);
  });

  const pathEl = el('b-path');
  (d.reading_path || []).forEach((p, i) => {
    const row = document.createElement('div');
    row.className = 'path-item';
    row.innerHTML = `<div class="path-num">${i + 1}</div>
      <div class="path-body"><span class="step"></span> — <span class="notice"></span></div>`;
    row.querySelector('.step').textContent = p.step;
    row.querySelector('.notice').textContent = p.what_to_notice;
    pathEl.appendChild(row);
  });

  el('b-takeaway').textContent = d.takeaway;
}

document.addEventListener('DOMContentLoaded', async () => {
  const { readerData } = await chrome.storage.session.get('readerData');
  if (!readerData || !readerData.article || !readerData.briefing) {
    return showError('읽을 기사가 없습니다. 기사 페이지에서 갈피 사이드패널로 브리핑을 만든 뒤 "광고 없이 읽기"를 눌러주세요.');
  }
  const { article, briefing } = readerData;

  document.title = `갈피 — ${article.title}`;
  el('m-title').textContent = article.title;
  el('m-site').textContent = article.siteName || '';
  el('m-byline').textContent = article.byline || '';
  const origin = el('m-origin');
  origin.href = article.url;

  el('a-title').textContent = article.title;
  el('a-byline').textContent = [article.siteName, article.byline].filter(Boolean).join(' · ');

  const body = el('a-body');
  body.replaceChildren(...sanitize(article.html).childNodes);

  const terms = (briefing.concepts || []).map(c => c.term);
  const foundTerms = highlightTerms(body, terms);
  renderBriefing(briefing, foundTerms);
});
