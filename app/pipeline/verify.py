"""④ 검증 (Context Check)

브리핑과 문맥 카드를 문서와 대조한다.
- 이 사건의 사실 주장 → 문서에 근거 있어야 함
- 일반 지식 설명 → 적절히 표시됐는지, 이 사건의 사실처럼 단정하지 않았는지
"""

import json

from app.llm import FAST_MODEL, complete_json

SYSTEM = """당신은 꼼꼼한 검증자입니다.
'읽기 전 브리핑'과 '문맥 카드'가 원문 문서와 모순되지 않는지,
일반 지식 설명이 이 사건의 구체적 사실인 것처럼 위장하지 않았는지 확인합니다."""

SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "description": "브리핑·문맥 카드 속 주요 주장들의 판정",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "주장 요약"},
                    "verdict": {
                        "type": "string",
                        "enum": ["문서근거", "일반지식", "문제"],
                    },
                    "note": {"type": "string", "description": "근거 또는 판단 이유"},
                },
                "required": ["claim", "verdict", "note"],
            },
        },
        "issues": {
            "type": "array",
            "description": "'문제' 판정만 담는다. 없으면 빈 배열.",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "reason": {"type": "string"},
                    "suggestion": {"type": "string"},
                },
                "required": ["claim", "reason", "suggestion"],
            },
        },
    },
    "required": ["claims", "issues"],
}

PROMPT_TEMPLATE = """아래 브리핑·문맥 카드를 문서와 대조하세요.

판정 기준:
- "문서근거": 이 사건에 대한 주장이 문서 내용으로 뒷받침됨 (표현이 달라도 내용이 같으면 OK)
- "일반지식": 제도·개념에 대한 일반적 설명으로, 이 사건의 사실이라고 단정하지 않음 (정상)
- "문제": (a) 문서와 모순되는 주장, (b) 일반 지식을 이 사건의 구체적 사실처럼 단정,
  (c) 원문의 결론을 통째로 스포일러해서 원문을 읽을 필요를 없앰

브리핑과 문맥 카드:
{bundle}

문서:
<document>
{document}
</document>"""


def verify(document: str, bundle: dict) -> dict:
    return complete_json(
        PROMPT_TEMPLATE.format(
            bundle=json.dumps(bundle, ensure_ascii=False, indent=1),
            document=document,
        ),
        schema=SCHEMA,
        system=SYSTEM,
        model=FAST_MODEL,
        max_tokens=3000,
    )
