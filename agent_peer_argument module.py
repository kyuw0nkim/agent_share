VALUE_GROUPS_19 = [
    "Self-direction–thought",
    "Self-direction–action",
    "Stimulation",
    "Hedonism",
    "Achievement",
    "Power–dominance",
    "Power–resources",
    "Face",
    "Security–personal",
    "Security–societal",
    "Tradition",
    "Conformity–rules",
    "Conformity–interpersonal",
    "Humility",
    "Benevolence–dependability",
    "Benevolence–caring",
    "Universalism–concern",
    "Universalism–nature",
    "Universalism–tolerance",
]

PERSONA = {"name": "윤서", "description": "참여자의 동료 (대학생)"}

PROMPTS = {
    # 대화용 시스템 프롬프트
    "system_main": (
        "You are a fellow undergraduate student having a casual discussion with the user.\n"
        "Atmosphere: egalitarian, friendly, not formal.\n"
        "Constraints: 1-2 sentences per message.\n"
        "Language: 기본은 한국어. 필요하면 자연스럽게 영어 용어/짧은 문장 섞어도 됨."
    ),
    "persona_template": "You are {name}: {description}. Your goal is to support the stance: {stance}",
    "system_message_template": (
        "{system_main}\n"
        "{persona_line}\n"
        "{memory_block}"
        "{hint_block}"
    ),
    "memory_block_template": "\n\n[Long-term memory / reflections]\n{reflections}\n",
    "hint_block_template": "\n\n(Hint: If it fits naturally, bring up '{group}' perspective.)",

    # (A) stance 생성
    "task_stance_system": (
        "너는 토론 파트너 에이전트의 '입장(stance)'을 수립하는 전문가다.\n"
        "주어진 과제/선택지를 바탕으로, 파트너가 일관되게 지지할 논리(핵심 주장, 근거축, 주의점)를\n"
        "짧고 실행 가능하게 한국어 마크다운으로 작성하라."
    ),
    "task_stance_user_template": (
        "### Persona\n- name: {name}\n- description: {description}\n\n"
        "### Task\n{task}\n\n"
        "### Partner Choice (stance to support)\n{choice}\n\n"
        "요구사항:\n"
        "- 한국어 불릿 3~5개\n"
        "- 간결하고 단호한 톤\n"
    ),

    # (B) 19개 가치 기반 argument bank 생성 (JSON)
    "value_args_system": (
        "너는 Schwartz 19 values 기반으로 주장(Argument) 뱅크를 만드는 전문가다.\n"
        "입장(stance)을 지지하는 방향으로, 각 가치 그룹 관점에서 사용할 수 있는 '짧은 주장 문장'을 생성하라.\n"
        "반드시 JSON object로만 답하라.\n\n"
        "출력 스키마:\n"
        "{\n"
        '  "items": [\n'
        '    {"group": "<VALUE_GROUP>", "claim": "<one sentence claim in Korean>"},\n'
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "규칙:\n"
        f"- group은 반드시 다음 중 하나여야 한다: {VALUE_GROUPS_19}\n"
        "- items는 19개(각 group 1개씩) 생성하라.\n"
        "- claim은 한국어 1문장, 자연스러운 구어체로 작성.\n"
        "- 기술적 전문 용어는 피하고, 실생활 이유/원인을 포함하라.\n"
        "- 표현은 '~할 수 있습니다', '~할 가능성이 큽니다' 중 하나를 포함하라.\n"
    ),
    "value_args_user_with_stance_support": (
        "### Task\n{task}\n\n"
        "### Stance to Support\n{stance}\n\n"
        "위 stance를 지지하는 방향으로, 19개 가치 그룹 각각에 대해 주장(claim) 1개씩 생성해줘."
    ),

    # (C) 가치 커버리지 판별
    "coverage_judge_system": (
        "너는 가치 지향점 분석 전문가다.\n"
        "대화 기록을 보고, 아래 제공된 TARGET VALUES(인덱스/그룹명)가 '논의되었는지' 판별하라.\n"
        "문장 일치가 아니라 '의도/정당화 논리/가치관'이 드러났는지를 본다.\n\n"
        "반드시 JSON object로만 응답:\n"
        "{\n"
        '  "items": [\n'
        '    {"index": 0, "mentioned": true, "rationale": "짧게"},\n'
        "    ...\n"
        "  ]\n"
        "}\n"
    ),
    "coverage_judge_user_template": "### [CHAT HISTORY]\n{chat}\n\n### [TARGET VALUES TO CHECK]\n{mapping}",

    # (D) reflection 생성
    "reflection_system": (
        "너는 최근 대화에서 저장할 장기 메모리 인사이트를 추출하는 역할이다.\n"
        "요약이나 평가가 아니라, 가치 관점이나 성향에 대한 한 가지 인사이트를 추론하라.\n"
        "반드시 JSON object로만 응답:\n"
        '{ "insight": "<한 문장 한국어>", "evidence": "<근거가 되는 발화>" }'
    ),
    "reflection_user_template": "### [CHAT HISTORY]\n{chat}\n\n### [REFLECTION OUTPUT]\nJSON으로만 출력",
    # (E) hint 그룹 선택
    "hint_selector_system": (
        "너는 토론 파트너 에이전트의 다음 힌트 가치 관점을 선택하는 역할이다.\n"
        "최근 대화 맥락과 미언급 가치 후보 목록을 보고, 다음 턴에 자연스럽게 꺼낼 가치를 하나 고르라.\n"
        "미언급 후보를 우선하되, 최근 힌트와의 연속성을 고려하라.\n"
        "너무 자주 관점을 바꾸지 않도록 주의하라."
    ),
    "hint_selector_user_template": (
        "### [CHAT HISTORY]\n{chat}\n\n"
        "### [CURRENT HINT]\n{current_hint}\n\n"
        "### [UNMENTIONED VALUE CANDIDATES]\n{candidates}\n\n"
        "JSON으로만 응답:\n"
        "{{\n"
        '  "group": "<VALUE_GROUP>",\n'
        '  "rationale": "<짧은 이유>"\n'
        "}}\n"
    ),
    # (F) action manager
    "action_manager_system": (
        "너는 그룹 대화에 참여하는 peer 에이전트의 발화 여부를 판단하는 액션 매니저다.\n"
        "기여 가치, 사회적 적절성, 타이밍을 고려해 지금 응답할지 판단하라.\n"
        "반드시 JSON object로만 응답:\n"
        '{ "decision": "Respond/Don\'t respond", "reason": "<짧은 이유>" }'
    ),
    "action_manager_user_template": (
        "### [CHAT HISTORY]\n{chat}\n\n"
        "### [ARGUMENT OPTIONS]\n{arguments}\n\n"
        "### [LONG-TERM MEMORY]\n{memory}\n\n"
        "JSON으로만 출력"
    ),
    # (G) response generator
    "response_generator_system": (
        "너는 그룹 대화에 참여하는 동료 역할의 응답 생성기다.\n"
        "한국어로 1~2문장, 15~20단어로 자연스럽게 말하라.\n"
        "하나의 생각만 말하고, 설명하거나 지시하지 마라."
    ),
    "response_generator_user_template": (
        "### [ACTION DECISION]\n{decision}\n\n"
        "### [SELECTED ARGUMENT]\n{argument}\n\n"
        "### [CHAT HISTORY]\n{chat}\n\n"
        "### [LONG-TERM MEMORY]\n{memory}\n\n"
        "### [RESPONSE OUTPUT]\n"
        "- 1~2문장 한국어"
    ),
}

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Argument:
    group: str
    claim: str
    keywords: List[str] = field(default_factory=list)
    mentioned: bool = False


def build_task_profile_components(
    client,
    task_text: str,
    choice_text: str,
    persona: Dict[str, str],
    *,
    prompts: Dict[str, str],
    model_name: str,
    value_groups: List[str],
) -> Tuple[str, List[Argument], str]:
    s_res = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompts["task_stance_system"]},
            {
                "role": "user",
                "content": prompts["task_stance_user_template"].format(
                    task=task_text, choice=choice_text, **persona
                ),
            },
        ],
    )
    stance = s_res.choices[0].message.content

    a_res = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompts["value_args_system"]},
            {
                "role": "user",
                "content": prompts["value_args_user_with_stance_support"].format(
                    task=task_text, stance=stance
                ),
            },
        ],
        response_format={"type": "json_object"},
    )

    res_data = json.loads(a_res.choices[0].message.content)
    raw_args = res_data.get("items", [])

    arg_bank: List[Argument] = []
    for it in raw_args:
        if isinstance(it, dict) and "claim" in it:
            arg_bank.append(
                Argument(
                    group=it.get("group", "기타"),
                    claim=it.get("claim", ""),
                    keywords=[],
                    mentioned=False,
                )
            )

    log = (
        "[Setup]\n"
        f"- choice: {choice_text}\n"
        f"- stance_len: {len(stance)}\n"
        f"- arg_bank_size: {len(arg_bank)}\n"
        f"- value_groups_count: {len(value_groups)}\n"
    )
    return stance, arg_bank, log


def select_hint_group(arg_bank: List[Argument]) -> Optional[str]:
    unseen = [a for a in arg_bank if not a.mentioned]
    return unseen[0].group if unseen else None


def build_system_prompt(
    persona: Dict[str, str],
    stance_md: str,
    reflections: List[str],
    hint_group: Optional[str],
    *,
    prompts: Dict[str, str],
) -> str:
    memory_block = ""
    if reflections:
        memory_block = prompts["memory_block_template"].format(
            reflections="\n".join(f"- {r}" for r in reflections)
        )
    hint_block = ""
    if hint_group:
        hint_block = prompts["hint_block_template"].format(group=hint_group)

    persona_line = prompts["persona_template"].format(
        name=persona["name"], description=persona["description"], stance=stance_md
    )
    return prompts["system_message_template"].format(
        system_main=prompts["system_main"],
        persona_line=persona_line,
        memory_block=memory_block,
        hint_block=hint_block,
    )


def prepare_prompt_with_hint(
    short_mem,
    long_mem: Dict[str, object],
    persona: Dict[str, str],
    stance_md: str,
    arg_bank: List[Argument],
    hint_group: Optional[str] = None,
    *,
    prompts: Dict[str, str],
) -> Tuple[str, Optional[str], str]:
    if hint_group is None:
        hint_group = select_hint_group(arg_bank)
    reflections = long_mem.get("reflections", [])
    sys_content = build_system_prompt(
        persona,
        stance_md,
        reflections,
        hint_group,
        prompts=prompts,
    )

    prompt_log = (
        "[Prompt Snapshot]\n"
        f"- short_mem_turns: {len(short_mem)}\n"
        f"- long_mem_items: {len(reflections)}\n"
        f"- hint_group: {hint_group or 'none'}\n"
        f"- system_len: {len(sys_content)}\n"
    )
    return sys_content, hint_group, prompt_log


def generate_action_decision(
    client,
    chat_history: List[str],
    argument_options: List[str],
    long_mem: List[str],
    *,
    prompts: Dict[str, str],
    model_name: str,
) -> Dict[str, str]:
    decision = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompts["action_manager_system"]},
            {
                "role": "user",
                "content": prompts["action_manager_user_template"].format(
                    chat="\n".join(chat_history),
                    arguments="\n".join(argument_options),
                    memory="\n".join(long_mem) if long_mem else "(없음)",
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    data = decision.choices[0].message.content or "{}"
    parsed = json.loads(data)
    return parsed if isinstance(parsed, dict) else {}


def generate_peer_response(
    client,
    action_decision: Dict[str, str],
    selected_argument: str,
    chat_history: List[str],
    long_mem: List[str],
    *,
    prompts: Dict[str, str],
    model_name: str,
) -> str:
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompts["response_generator_system"]},
            {
                "role": "user",
                "content": prompts["response_generator_user_template"].format(
                    decision=json.dumps(action_decision, ensure_ascii=False),
                    argument=selected_argument,
                    chat="\n".join(chat_history),
                    memory="\n".join(long_mem) if long_mem else "(없음)",
                ),
            },
        ],
    )
    return response.choices[0].message.content.strip()
