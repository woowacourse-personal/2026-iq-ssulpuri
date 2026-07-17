# 갈피 (galpi) — 읽기 전 배경지식 브리핑

> 뉴스가 어려운 건 당신 탓이 아니라, **빠진 배경지식** 탓입니다.

뉴스는 연재물이다. 오늘 기사는 대개 이전 사건들의 후속편이라, 지난 편들을 못 본 독자는
용어가 아니라 **"왜 이 일이 벌어졌는지"** 부터 막힌다.

**갈피**는 뉴스 기사(특히 국제정세·경제)를 넣으면, 그 기사가 독자가 이미 안다고 전제하는
**개념과 이전 사건의 연쇄**를 찾아 **읽기 전 브리핑**으로 채워준다.
이름은 "갈피를 못 잡겠다"의 갈피이자, 책에 꽂는 책갈피의 갈피다.

**요약 서비스가 아니다.** 요약은 원문을 안 읽게 만들고, 브리핑은 원문을 읽을 수 있게 만든다.
그래서 갈피는 기사의 결론을 절대 대신 말하지 않는다 — 읽는 건 여전히 당신이다.

## 주요 기능

**웹** (`http://localhost:8000`)
- 기사 붙여넣기 / URL 입력 → 신문 1면 조판의 브리핑 카드
- 브리핑 → 개념 카드(형광펜) → 답해주지 않는 배경 → 읽기 경로 → 테이크어웨이
- SSE로 파이프라인 진행 단계가 실시간 표시 (가짜 로딩 아님)

**크롬 확장** (`extension/`, MV3)
- 기사 페이지에서 툴바 아이콘 → 사이드패널 → **원클릭 브리핑**
- 개념 용어를 기사 본문에 **형광펜 하이라이트**, 카드 클릭 시 해당 위치로 스크롤
- **"광고 없이 읽기"** — 새 탭에 좌측 브리핑 + 우측 기사 본문(이미지 포함) 2단 리더 뷰
- 본문 추출은 Mozilla Readability.js + 휴리스틱 폴백

**믿을 수 있게 만드는 장치**
- ④ 검증 단계가 브리핑의 모든 주장을 원문과 대조 — 모순·결론 스포일러·일반지식 위장을 잡아내면 1회 자동 수정
- 기사 밖 일반 지식은 **"일반 지식" 배지**로 구분 표시
- 모델이 모르는 최신 전개는 지어내지 않고 "이후 전개는 기사가 다루는 부분"으로 기사에 넘기도록 설계

## 동작 원리 — 4단계 파이프라인

```
[기사] → ① 분석 → ② 배경지식 채우기 → ③ 브리핑 작성 → ④ 검증 → [읽기 전 브리핑]
        (전제 찾기)  (개념·이전 사건)    (읽기 경로 포함)    ↑
                                        문제 발견 시 수정 재생성 1회
```

| 단계 | 파일 | 역할 | 모델 |
|---|---|---|---|
| ① 분석 | `app/pipeline/analyze.py` | 기사가 전제하는 개념(≤6)·사건 연쇄 질문(≤4) 추출 | Haiku (저비용) |
| ② 배경지식 채우기 | `app/pipeline/contextualize.py` | 각 개념을 "이 기사에서 왜 중요한지" 중심으로 설명 | Sonnet |
| ③ 브리핑 작성 | `app/pipeline/compose.py` | 읽기 전 브리핑 + 원문 읽기 경로. 결론 스포 금지 | Sonnet |
| ④ 검증 | `app/pipeline/verify.py` | 원문 대조 — 모순 / 일반지식 위장 / 스포일러 감시 | Haiku (저비용) |

- 구조화 출력은 전부 **tool use + 명시적 JSON 스키마** (텍스트 JSON 파싱 장애를 3번 겪고 정착한 원칙)
- 확장은 얇은 클라이언트 — LLM 호출은 전부 서버 경유, **API 키는 서버 `.env`에만 존재**
- 기사 본문은 파이프라인 입력으로만 쓰이고 **어디에도 저장되지 않는다** ([PRIVACY.md](PRIVACY.md))

## 시작하기

```bash
# 1. 서버
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # ANTHROPIC_API_KEY 입력
uvicorn app.main:app --reload # → http://localhost:8000

# 2. 테스트 (LLM 호출 없음, 무료·1초)
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

**크롬 확장 설치**
1. `chrome://extensions` → 개발자 모드 ON
2. "압축해제된 확장 프로그램 로드" → `extension/` 선택
3. 기사 페이지에서 갈피 아이콘 클릭 → "이 기사 갈피 잡기"
   (위 로컬 서버가 켜져 있어야 동작)

브리핑 1회 ≈ LLM 4~6콜, 1~2분, $0.05~0.15.

## 프로젝트 구조

```
app/
├── main.py                 # FastAPI — /api/transform, /api/transform/stream(SSE)
├── llm.py                  # Anthropic 래퍼 (tool use 강제 구조화 출력)
├── pipeline/               # ① analyze ② contextualize ③ compose(+repair) ④ verify
└── static/index.html       # 웹 UI (단일 파일, 신문 1면 조판)
extension/
├── manifest.json           # MV3 — sidePanel + activeTab/scripting
├── sidepanel.html/js/css   # 브리핑 패널 (책갈피 리본 시그니처)
├── reader.html/js/css      # 광고 없는 리더 뷰 (브리핑+본문 2단)
└── vendor/Readability.js   # Mozilla 본문 추출 엔진 (Apache 2.0)
tests/                      # pytest 41개 — 단계 단위·스키마 회귀·API·CORS
docs/                       # 기획 히스토리, 웹스토어 배포 가이드
```

## 피봇 히스토리

| 버전 | 컨셉 | 배운 것 |
|---|---|---|
| v0.1~0.2 썰풀이 | 문서를 재미있는 썰로 각색 | 하네스를 2번 갈아도 "재미"는 소재 의존적 |
| v0.3 행간 | 재미 → **문맥 이해**로 피봇 | 사용자는 "그럴듯하게 틀린 AI"를 강하게 거부 → 검증 단계·일반지식 배지 |
| v0.4 갈피 | **뉴스 타겟 특화** + 크롬 확장 | 뉴스의 빠진 문맥은 용어보다 '이전 사건의 연쇄' |

상세: [docs/planning.md](docs/planning.md) (구 기획서)

## 로드맵

- [x] 뉴스 특화 프롬프트 (사건 연쇄 중심)
- [x] 크롬 확장 — 사이드패널·하이라이트·리더 뷰·아이콘
- [ ] web search 그라운딩 (최신 사건 배경의 컷오프 환각 제거)
- [ ] 서버 호스팅 + 요청 제한 → 크롬 웹스토어 제출 (준비물은 [docs/webstore.md](docs/webstore.md)에 완료)
- [ ] 브리핑 유/무 이해도 비교 실험 (H1 검증)

## 검증 가설

- **H1**: 브리핑을 먼저 읽으면, 같은 기사의 이해도·완독률이 유의미하게 오른다.
  → 실험 설계: `experiments/prototype-3-context-test.md`

## 서드파티 & 고지

- [Mozilla Readability](https://github.com/mozilla/readability) — Apache License 2.0 (`extension/vendor/`)
- 브리핑은 기사 독해를 돕기 위한 것으로 법률·투자 자문이 아닙니다. 기사 본문은 저장되지 않습니다.

---
우아한테크코스 8기 레벨3 개인 프로젝트
