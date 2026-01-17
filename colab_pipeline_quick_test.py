from collections import deque
import importlib.util
import json

from openai import OpenAI

import agent_support_mediate_module as support_module


def load_peer_module(path: str = "agent_peer_argument module.py"):
    spec = importlib.util.spec_from_file_location("agent_peer_argument_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_peer_pipeline(client: OpenAI, model_name: str):
    peer_module = load_peer_module()
    task_text = "대학 캠퍼스 내 밤 10시 이후 통금 규칙을 도입할지 논의한다."
    choice_text = "통금 규칙을 도입한다."

    stance, arg_bank, log = peer_module.build_task_profile_components(
        client,
        task_text,
        choice_text,
        peer_module.PERSONA,
        prompts=peer_module.PROMPTS,
        model_name=model_name,
        value_groups=peer_module.VALUE_GROUPS_19,
    )
    coverage = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": peer_module.PROMPTS["coverage_judge_prompt"],
            },
            {
                "role": "user",
                "content": peer_module.PROMPTS["coverage_judge_user_template"].format(
                    chat="User: 통금은 안전을 높일 수 있어요.",
                    mapping=peer_module.format_value_mapping(
                        peer_module.VALUE_GROUPS_19
                    ),
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    coverage_data = json.loads(coverage.choices[0].message.content or "{}")
    peer_module.update_argument_mentions_from_coverage(
        coverage_data, arg_bank, peer_module.VALUE_GROUPS_19
    )
    hint_group = peer_module.select_hint_group(arg_bank)
    sys_prompt = peer_module.build_system_prompt(
        peer_module.PERSONA,
        stance,
        reflections=[],
        hint_group=hint_group,
        prompts=peer_module.PROMPTS,
    )

    print("== Peer Pipeline ==")
    print(log)
    print("stance:\n", stance)
    print("hint_group:", hint_group)
    print("system prompt preview:\n", sys_prompt[:400], "...")
    print("coverage:\n", coverage.choices[0].message.content)

    decision = peer_module.generate_action_decision(
        client,
        chat_history=["User: 통금은 안전을 높일 수 있어요."],
        argument_options=[arg.claim for arg in arg_bank[:3]],
        long_mem=[],
        prompts=peer_module.PROMPTS,
        model_name=model_name,
    )
    response = peer_module.generate_peer_response(
        client,
        action_decision=decision,
        selected_argument=arg_bank[0].claim if arg_bank else "",
        chat_history=["User: 통금은 안전을 높일 수 있어요."],
        long_mem=[],
        prompts=peer_module.PROMPTS,
        model_name=model_name,
    )
    print("action decision:\n", decision)
    print("peer response:\n", response)


def run_supporting_pipeline(client: OpenAI, model_name: str):
    short_mem = deque(
        [
            support_module.ConversationEntry(
                speaker="user_1", content="나는 비용이 너무 늘어나는 게 걱정이야."
            ),
            support_module.ConversationEntry(
                speaker="user_2", content="하지만 안전을 위해서는 필요하다고 봐."
            ),
        ]
    )
    long_mem = {"user_1": [], "user_2": []}
    user_models = {"user_1": "", "user_2": ""}
    user_labels = {"user_1": "User 1", "user_2": "User 2"}

    long_mem, user_models = support_module.batch_update_user_states(
        client,
        short_mem,
        long_mem,
        user_models,
        prompts=support_module.PROMPTS,
        model_name=model_name,
        user_ids=["user_1", "user_2"],
        user_labels=user_labels,
    )

    print("== Supporting Pipeline ==")
    print("long_mem:", long_mem)
    print("user_models:", user_models)

    support_ltm = support_module.generate_support_ltm(
        client,
        recent_chat=[
            "User 1: 나는 비용이 너무 늘어나는 게 걱정이야.",
            "User 2: 하지만 안전을 위해서는 필요하다고 봐.",
        ],
        prompts=support_module.PROMPTS,
        model_name=model_name,
    )
    print("support_ltm:", support_ltm)


if __name__ == "__main__":
    # Colab에서 실행 시:
    # 1) pip install openai
    # 2) 환경변수 OPENAI_API_KEY 설정
    client = OpenAI()
    model = "gpt-4o-mini"

    run_peer_pipeline(client, model)
    run_supporting_pipeline(client, model)
