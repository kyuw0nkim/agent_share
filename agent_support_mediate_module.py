PROMPTS = {
    "system_main": (
        "You are a neutral mediator between User 1 and User 2.\n"
        "Identity: 그룹 중재자 (Group Mediator).\n"
        "Meta rule: User 1/2는 인간 참가자이며 에이전트는 제3자다.\n"
        "Goals: clarify points, find common ground, reduce conflict.\n"
        "Constraints: 1-2 sentences per message.\n"
        "Never speak as User 1 or User 2; respond only as the Mediator.\n"
        "Language: 기본은 한국어. 필요하면 자연스럽게 영어 용어/짧은 문장 섞어도 됨."
    ),
    "system_message_template": "{system_main}\n\n{task_block}\n{group_summary_block}\n{user_models}\n",
    "user_model_line_template": "- {user_label} model: {model}",
    "task_block_template": "[Task]\n{task}\n",
    "group_summary_block_template": "[Group Summary]\n{summary}\n",
    "reflection_system": (
        "너는 사용자 발화의 핵심을 요약해 장기 메모리로 저장하는 역할을 한다.\n"
        "사용자의 핵심 주장, 선호, 우려를 간단히 정리하라.\n"
        "1~2문장, 한국어로 간결하게."
    ),
    "reflection_user_template": "### [USER]\n{user_label}\n\n### [CHAT HISTORY]\n{chat}\n\n### [REFLECTION OUTPUT]\n- 1~2문장 한국어 요약",
    "user_model_system": (
        "너는 사용자 모델을 업데이트하는 역할을 한다.\n"
        "아래 요약들을 바탕으로 사용자의 성향/관심/우려를 간단히 정리하라.\n"
        "1~2문장, 한국어로 간결하게."
    ),
    "user_model_user_template": "### [USER]\n{user_label}\n\n### [REFLECTIONS]\n{reflections}\n\n### [UPDATED USER MODEL]",
    "batch_user_update_system": (
        "너는 User 1과 User 2의 리플렉션과 사용자 모델을 동시에 갱신하는 역할이다.\n"
        "각 사용자에 대해 최근 발화와 누적 리플렉션을 읽고,\n"
        "새 리플렉션(1~2문장)과 업데이트된 사용자 모델(1~2문장)을 생성하라.\n"
        "최근 발화가 없으면 reflection은 null로 두고, model은 기존 값을 유지하기 위해 null로 두어라.\n"
        "반드시 JSON object로만 답하라."
    ),
    "batch_user_update_user_template": (
        "### [USER 1 RECENT]\n{user1_recent}\n\n"
        "### [USER 1 REFLECTIONS]\n{user1_reflections}\n\n"
        "### [USER 2 RECENT]\n{user2_recent}\n\n"
        "### [USER 2 REFLECTIONS]\n{user2_reflections}\n\n"
        "JSON output schema:\n"
        "{{\n"
        '  "user1": {{"reflection": "<string|null>", "model": "<string|null>"}},\n'
        '  "user2": {{"reflection": "<string|null>", "model": "<string|null>"}}\n'
        "}}\n"
    ),
    "action_manager_system": (
        "너는 그룹 대화에서 중재 에이전트가 지금 응답해야 하는지 판단하는 액션 매니저다.\n"
        "다음 기준을 우선적으로 고려하라:\n"
        "- 갈등 완화/오해 해소가 필요하거나 감정이 격화되는 징후가 있는가?\n"
        "- 사용자가 중재자에게 직접 질문하거나 호출하고 있는가?\n"
        "- 대화가 교착 상태이거나 합의점을 찾기 위해 정리가 필요한가?\n"
        "- 단순한 일상 대화/서로의 대화가 자연스럽게 이어지는 경우라면 침묵할 수 있는가?\n"
        "출력은 반드시 아래 중 하나의 단어로만 답하라:\n"
        "respond\n"
        "skip"
    ),
    "action_manager_user_template": "### [CHAT HISTORY]\n{chat}\n\n### [DECISION]\n",
    "group_summary_system": (
        "너는 그룹 대화의 누적 요약을 관리하는 전문가다.\n"
        "이전 요약과 최근 대화 기록을 읽고, 핵심 쟁점/합의/대립을 3~5문장으로 갱신하라.\n"
        "중립적인 톤으로 간결하게 작성하라."
    ),
    "group_summary_user_template": (
        "### [PREVIOUS GROUP SUMMARY]\n{summary}\n\n"
        "### [RECENT CHAT]\n{chat}\n\n"
        "### [UPDATED GROUP SUMMARY]\n"
        "- 3~5문장 한국어 요약"
    ),
}


@dataclass
class ConversationEntry:
    speaker: str
    content: str

import json
from typing import Deque, Dict, List, Optional, Tuple


def generate_reflection(
    client,
    user_id: str,
    recent_user_msgs: List[str],
    *,
    prompts: Dict[str, str],
    model_name: str,
    user_labels: Dict[str, str],
) -> Optional[str]:
    if not recent_user_msgs:
        return None

    chat_text = "\n".join(recent_user_msgs)
    r = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompts["reflection_system"]},
            {
                "role": "user",
                "content": prompts["reflection_user_template"].format(
                    user_label=user_labels[user_id],
                    chat=chat_text,
                ),
            },
        ],
    )
    return r.choices[0].message.content.strip()


def update_user_model(
    client,
    user_id: str,
    reflections: List[str],
    *,
    prompts: Dict[str, str],
    model_name: str,
    user_labels: Dict[str, str],
) -> Optional[str]:
    if not reflections:
        return None

    reflection_text = "\n".join(f"- {r}" for r in reflections)
    r = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompts["user_model_system"]},
            {
                "role": "user",
                "content": prompts["user_model_user_template"].format(
                    user_label=user_labels[user_id],
                    reflections=reflection_text,
                ),
            },
        ],
    )
    return r.choices[0].message.content.strip()


def batch_update_user_states(
    client,
    short_mem: Deque,
    long_mem: Dict[str, List[str]],
    user_models: Dict[str, str],
    *,
    prompts: Dict[str, str],
    model_name: str,
    user_ids: List[str],
    user_labels: Dict[str, str],
) -> Tuple[Dict[str, List[str]], Dict[str, str]]:
    recent_by_user = {user_id: [] for user_id in user_ids}
    for entry in list(short_mem):
        recent_by_user[entry.speaker].append(f"{user_labels[entry.speaker]}: {entry.content}")

    user1_recent = "\n".join(recent_by_user[user_ids[0]])
    user2_recent = "\n".join(recent_by_user[user_ids[1]])
    user1_reflections = "\n".join(f"- {r}" for r in long_mem.get(user_ids[0], []))
    user2_reflections = "\n".join(f"- {r}" for r in long_mem.get(user_ids[1], []))

    r = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": prompts["batch_user_update_system"]},
            {
                "role": "user",
                "content": prompts["batch_user_update_user_template"].format(
                    user1_recent=user1_recent or "(없음)",
                    user1_reflections=user1_reflections or "(없음)",
                    user2_recent=user2_recent or "(없음)",
                    user2_reflections=user2_reflections or "(없음)",
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    data = r.choices[0].message.content or "{}"
    parsed = json.loads(data)

    for user_id in user_ids:
        payload = parsed.get(user_id, {}) if isinstance(parsed, dict) else {}
        reflection = payload.get("reflection")
        model = payload.get("model")
        if isinstance(reflection, str) and reflection.strip():
            long_mem[user_id].append(reflection.strip())
        if isinstance(model, str) and model.strip():
            user_models[user_id] = model.strip()

    return long_mem, user_models
