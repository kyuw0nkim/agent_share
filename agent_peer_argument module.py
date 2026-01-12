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
    group_summary: str,
    hint_group: Optional[str],
    *,
    prompts: Dict[str, str],
) -> str:
    memory_block = ""
    if reflections:
        memory_block = prompts["memory_block_template"].format(
            reflections="\n".join(f"- {r}" for r in reflections)
        )
    group_summary_block = ""
    if group_summary:
        group_summary_block = prompts["group_summary_block_template"].format(summary=group_summary)
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
        group_summary_block=group_summary_block,
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
    group_summary = long_mem.get("group_summary", "")
    sys_content = build_system_prompt(
        persona,
        stance_md,
        reflections,
        group_summary,
        hint_group,
        prompts=prompts,
    )

    prompt_log = (
        "[Prompt Snapshot]\n"
        f"- short_mem_turns: {len(short_mem)}\n"
        f"- long_mem_items: {len(reflections)}\n"
        f"- group_summary_len: {len(group_summary)}\n"
        f"- hint_group: {hint_group or 'none'}\n"
        f"- system_len: {len(sys_content)}\n"
    )
    return sys_content, hint_group, prompt_log
