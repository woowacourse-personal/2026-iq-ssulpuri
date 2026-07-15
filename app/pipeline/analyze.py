"""① 문서 분석 (Assumption Mining)

문서가 '독자가 이미 안다'고 전제하는 개념과 배경을 찾아낸다.
이 글이 어려운 이유(빠진 문맥)의 목록을 만드는 단계.

v0.4 뉴스 특화: 뉴스는 연재물이다 — 오늘 기사는 이전 사건들의 후속편인 경우가 많고,
빠진 문맥의 핵심은 용어보다 '사건의 연쇄'인 경우가 많다.
"""

from app.llm import FAST_MODEL, complete_json

SYSTEM = """당신은 뉴스 기사 분석가입니다.
기사(특히 국제정세·경제)를 읽고, 이 글이 독자에게 설명 없이 전제하는 것들을 찾아냅니다.

뉴스는 연재물입니다. 오늘 기사는 대개 이전 사건들의 후속편이라,
독자가 그 흐름을 모르면 "왜 이 일이 벌어졌는지"부터 막힙니다.
그래서 두 종류의 빠진 문맥을 찾습니다:
1. "이 단어를 모르면 이 글이 안 읽힌다" 싶은 개념·용어
2. "이 기사 이전에 무슨 일이 있었는지 모르면 안 읽힌다" 싶은 사건의 연쇄 — 이쪽을 최우선으로

기사가 아닌 문서(판결문·공시·보고서)가 들어와도 같은 기준으로 분석합니다."""

SCHEMA = {
    "type": "object",
    "properties": {
        "doc_type": {"type": "string", "description": "기사|판결문|공시|보고서|기타"},
        "core_summary": {"type": "string", "description": "이 문서가 다루는 것 한 줄"},
        "key_points": {
            "type": "array",
            "description": "문서의 뼈대가 되는 핵심 지점 3~6개",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "K1, K2, ..."},
                    "description": {"type": "string"},
                },
                "required": ["id", "description"],
            },
        },
        "assumed_concepts": {
            "type": "array",
            "description": "문서가 설명 없이 쓰는 개념·용어 중 이해에 결정적인 것만 최대 6개",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "role_in_doc": {"type": "string", "description": "이 문서에서 이 개념이 하는 역할"},
                },
                "required": ["term", "role_in_doc"],
            },
        },
        "missing_background": {
            "type": "array",
            "items": {"type": "string"},
            "description": "문서가 답해주지 않지만 독자가 궁금할 배경 질문 최대 4개 (질문 형태로). "
            "'이 사건 이전에 무슨 일이 있었나', '이 기사는 어떤 사건의 후속인가' 같은 사건 연쇄 질문을 우선",
        },
    },
    "required": ["doc_type", "core_summary", "key_points", "assumed_concepts"],
}

PROMPT_TEMPLATE = """다음 문서를 분석하세요.

규칙:
- assumed_concepts는 '이걸 모르면 이 글이 안 읽힌다' 기준으로만 고른다. 사소한 용어는 제외.
- missing_background는 사건의 연쇄를 우선한다 — 이 기사가 어떤 사건의 후속인지,
  이전에 무슨 일이 있었는지를 묻는 질문이 용어 질문보다 먼저다.
- 판결문처럼 비실명 처리된 문서는 표기(A, B, 갑, 을 등)를 그대로 유지한다.

문서:
<document>
{document}
</document>"""


def analyze(document: str) -> dict:
    return complete_json(
        PROMPT_TEMPLATE.format(document=document),
        schema=SCHEMA,
        system=SYSTEM,
        model=FAST_MODEL,
        max_tokens=2500,
    )
