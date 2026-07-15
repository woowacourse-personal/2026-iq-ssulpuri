"""② 문맥 채우기 (Context Filling)

분석 단계가 찾아낸 개념·배경을 '이 문서 맥락 기준으로' 설명한다.
사전적 정의가 아니라 "이 글에서 왜 중요한지"가 핵심.
"""

import json

from app.llm import SMART_MODEL, complete_json

SYSTEM = """당신은 어려운 문서를 읽으려는 사람 옆에 앉은 친절한 해설가입니다.

절대 규칙:
1. 이 사건·이 글의 구체적 사실(누가, 언제, 얼마)은 문서에 있는 것만 말한다.
2. 개념·제도·통상적 절차의 설명은 일반 지식을 사용할 수 있다.
   단, 그 경우 knowledge_type을 "일반지식"으로 표시하고, 확신이 서지 않으면 "일반적으로 ~"처럼 완곡하게 쓴다.
3. 용어 설명은 사전 정의가 아니라 "이 글에서 이게 왜 중요한지" 중심으로 쓴다.
4. 비실명 처리된 당사자(A, B, 갑, 을)의 신원을 추정하지 않는다.
5. 특정 종목·자산의 매수/매도를 권하지 않는다."""

SCHEMA = {
    "type": "object",
    "properties": {
        "concepts": {
            "type": "array",
            "description": "개념 카드들 — 분석 단계의 assumed_concepts 각각에 대응",
            "items": {
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "explanation": {
                        "type": "string",
                        "description": "2~3문장. 쉬운 말로, 필요하면 비유 사용",
                    },
                    "why_it_matters_here": {
                        "type": "string",
                        "description": "이 글에서 이 개념이 왜 결정적인지 1~2문장",
                    },
                    "knowledge_type": {"type": "string", "enum": ["문서내용", "일반지식"]},
                },
                "required": ["term", "explanation", "why_it_matters_here", "knowledge_type"],
            },
        },
        "background": {
            "type": "array",
            "description": "배경 질문에 대한 답 — 분석 단계의 missing_background 각각에 대응",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string", "description": "2~4문장"},
                    "knowledge_type": {"type": "string", "enum": ["문서내용", "일반지식"]},
                },
                "required": ["question", "answer", "knowledge_type"],
            },
        },
    },
    "required": ["concepts", "background"],
}

LEVEL_GUIDE = {
    "beginner": "독자는 이 분야를 처음 접합니다. 비유를 적극 사용하고, 전문용어 없이 설명하세요.",
    "intermediate": "독자는 기본 개념은 압니다. 간결하게, 이 글 특유의 맥락에 집중하세요.",
}

PROMPT_TEMPLATE = """아래 문서와 분석 결과를 바탕으로 문맥을 채워주세요.

독자 수준: {level_guide}

분석 결과 (이 개념·질문들에 답해야 함):
{analysis}

문서:
<document>
{document}
</document>"""


def contextualize(document: str, analysis: dict, level: str) -> dict:
    return complete_json(
        PROMPT_TEMPLATE.format(
            level_guide=LEVEL_GUIDE.get(level, LEVEL_GUIDE["beginner"]),
            analysis=json.dumps(analysis, ensure_ascii=False, indent=1),
            document=document,
        ),
        schema=SCHEMA,
        system=SYSTEM,
        model=SMART_MODEL,
        max_tokens=3500,
    )
