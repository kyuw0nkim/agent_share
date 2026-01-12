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
