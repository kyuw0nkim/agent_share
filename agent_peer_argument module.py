import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import raw_prompt_modules

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

    # Raw prompt blocks (non-templated)
    "task_stance_prompt": raw_prompt_modules.PEER_AGENT_PROMPTS["stance_generation"],
    "value_args_prompt": raw_prompt_modules.PEER_AGENT_PROMPTS["argument_generation"],
    "coverage_judge_prompt": raw_prompt_modules.PEER_AGENT_PROMPTS["coverage_judgement"],
    "reflection_prompt": raw_prompt_modules.PEER_AGENT_PROMPTS["peer_ltm"],
    "action_manager_prompt": raw_prompt_modules.PEER_AGENT_PROMPTS["peer_action_manager"],
    "response_generator_prompt": raw_prompt_modules.PEER_AGENT_PROMPTS[
        "peer_response_generator"
    ],

    # Additional wrappers for structured inputs
    "coverage_judge_user_template": "### [CHAT HISTORY]\n{chat}\n\n### [TARGET VALUES TO CHECK]\n{mapping}",
    "reflection_user_template": "### [CHAT HISTORY]\n{chat}\n\n### [REFLECTION OUTPUT]\nJSON으로만 출력",
    "action_manager_user_template": (
        "### [CHAT HISTORY]\n{chat}\n\n"
        "### [ARGUMENT OPTIONS]\n{arguments}\n\n"
        "### [LONG-TERM MEMORY]\n{memory}\n\n"
        "JSON으로만 출력"
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
    stance_prompt = (
        prompts["task_stance_prompt"]
        .replace("{{task}}", task_text)
        .replace("{{choice}}", choice_text)
    )
    s_res = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": stance_prompt}],
    )
    stance = s_res.choices[0].message.content

    value_prompt = (
        prompts["value_args_prompt"]
        .replace("{{task}}", task_text)
        .replace("{{stance}}", stance)
    )
    a_res = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": value_prompt}],
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


def format_value_mapping(value_groups: List[str]) -> str:
    return "\n".join(f"{idx}: {group}" for idx, group in enumerate(value_groups))


def update_argument_mentions_from_coverage(
    coverage: Dict[str, object],
    arg_bank: List[Argument],
    value_groups: List[str],
) -> None:
    items = coverage.get("items", []) if isinstance(coverage, dict) else []
    if not isinstance(items, list):
        return

    index_to_group = {idx: group for idx, group in enumerate(value_groups)}
    group_to_arg = {arg.group: arg for arg in arg_bank}
    for item in items:
        if not isinstance(item, dict):
            continue
        if not item.get("mentioned"):
            continue
        index = item.get("index")
        if isinstance(index, int):
            group = index_to_group.get(index)
            if group and group in group_to_arg:
                group_to_arg[group].mentioned = True


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
            {"role": "system", "content": prompts["action_manager_prompt"]},
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
            {"role": "system", "content": prompts["response_generator_prompt"]},
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
