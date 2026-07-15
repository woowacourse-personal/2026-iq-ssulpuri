"""③ 브리핑 작성 (Briefing Composition)

분석 + 문맥을 조립해 '읽기 전 브리핑'을 만든다.
목표는 요약이 아니다 — 독자가 원문을 스스로 읽을 수 있게 만드는 것.
"""

import json

from app.llm import SMART_MODEL, complete_json

SYSTEM = """당신은 '읽기 전 브리핑'을 쓰는 사람입니다.
독자가 어려운 원문을 곧 읽을 예정이고, 당신의 브리핑은 그 독서를 가능하게 만드는 준비운동입니다.

절대 규칙:
1. 요약하지 않는다. 원문의 결론을 대신 말해버리면 실패다. 원문을 읽을 이유를 남겨둔다.
2. 이 사건의 구체적 사실은 문서에 있는 것만. 일반 지식 설명은 "일반적으로" 톤으로.
3. 친절한 구어체. 과장, 낚시, 감탄사 없이. 유능한 선배가 5분 브리핑해주는 톤.
4. 비실명 당사자의 신원 추정 금지. 투자 권유 표현 금지."""

SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "description": "이 글을 한 줄로 — 결론 스포 없이 '무엇에 관한 글인지'"},
        "before_reading": {
            "type": "string",
            "description": "읽기 전 브리핑 2~3문단 (문단은 빈 줄로 구분, 총 300~500자). 이 글이 왜 존재하는지, 뭘 두고 다투는지, 어디가 어려운지",
        },
        "reading_path": {
            "type": "array",
            "description": "원문을 읽는 경로 3~5단계",
            "items": {
                "type": "object",
                "properties": {
                    "step": {"type": "string", "description": "원문의 어느 부분을"},
                    "what_to_notice": {"type": "string", "description": "무엇에 주목하며 읽을지"},
                },
                "required": ["step", "what_to_notice"],
            },
        },
        "takeaway": {"type": "string", "description": "이 글이 중요한 이유 한 단락 (2~4문장)"},
    },
    "required": ["headline", "before_reading", "reading_path", "takeaway"],
}

PROMPT_TEMPLATE = """아래 재료로 '읽기 전 브리핑'을 작성하세요.

독자 수준: {level}

분석 결과:
{analysis}

문맥 카드 (이미 독자에게 함께 제공됨 — 중복 설명하지 말 것):
{context}

문서:
<document>
{document}
</document>"""

# 검증 실패 시 수정용 — 브리핑과 문맥 카드를 한 번에 고친다
BUNDLE_SCHEMA = {
    "type": "object",
    "properties": {
        **SCHEMA["properties"],
        "concepts": {"type": "array", "items": {"type": "object"}},
        "background": {"type": "array", "items": {"type": "object"}},
    },
    "required": SCHEMA["required"] + ["concepts", "background"],
}

REPAIR_PROMPT = """검증 결과 아래 문제가 발견되었습니다.
문제가 된 부분만 고치고 나머지는 유지해, 전체 번들(브리핑 + concepts + background)을 다시 출력하세요.
concepts/background 항목의 구조(term, explanation, why_it_matters_here, knowledge_type / question, answer, knowledge_type)는 유지합니다.

발견된 문제:
{issues}

현재 번들:
{bundle}

문서:
<document>
{document}
</document>"""


def compose(document: str, analysis: dict, context: dict, level: str) -> dict:
    return complete_json(
        PROMPT_TEMPLATE.format(
            level="입문" if level == "beginner" else "중급",
            analysis=json.dumps(analysis, ensure_ascii=False, indent=1),
            context=json.dumps(context, ensure_ascii=False, indent=1),
            document=document,
        ),
        schema=SCHEMA,
        system=SYSTEM,
        model=SMART_MODEL,
        max_tokens=3000,
    )


def repair(bundle: dict, issues: list, document: str) -> dict:
    return complete_json(
        REPAIR_PROMPT.format(
            issues=json.dumps(issues, ensure_ascii=False, indent=1),
            bundle=json.dumps(bundle, ensure_ascii=False, indent=1),
            document=document,
        ),
        schema=BUNDLE_SCHEMA,
        system=SYSTEM,
        model=SMART_MODEL,
        max_tokens=4000,
    )
