# agent_share

## English

### Overview
This repository contains two Python modules that handle argument generation and user state updates (reflections/user models) for a dialogue-based agent.

### 1) `agent_peer_argument module.py`

#### Workflow
1. **Generate stance from task/choice**: `build_task_profile_components` creates a stance using persona and task/choice inputs.
2. **Collect value-based arguments**: The same function requests value-based arguments in JSON and converts them into an `Argument` list.
3. **Select a hint group**: `select_hint_group` picks the first unseen argument group as a hint.
4. **Build system prompt**: `build_system_prompt` composes a system message from persona, stance, reflections, group summary, and hint.
5. **Prepare final prompt**: `prepare_prompt_with_hint` finalizes the hint group and returns the system prompt and logs.

#### Inputs
- `client`: LLM API client
- `task_text`, `choice_text`: task/choice text
- `persona`: dict with name/description
- `prompts`: dict of system/user templates
- `model_name`: model identifier
- `value_groups`: list of value groups
- `short_mem`, `long_mem`: short/long memory structures
- `arg_bank`: list of `Argument`

#### Outputs
- `build_task_profile_components`: `(stance: str, arg_bank: List[Argument], log: str)`
- `select_hint_group`: `Optional[str]` (selected argument group)
- `build_system_prompt`: `str` (system message)
- `prepare_prompt_with_hint`: `(system_prompt: str, hint_group: Optional[str], log: str)`

### 2) `agent_support_mediate_module.py`

#### Workflow
1. **Generate reflection from recent chat**: `generate_reflection` creates a reflection based on recent user messages.
2. **Update user model**: `update_user_model` refreshes the user model from accumulated reflections.
3. **Batch update**: `batch_update_user_states` evaluates two users at once and updates reflections/models from JSON output.

#### Inputs
- `client`: LLM API client
- `user_id`, `user_ids`: user identifiers
- `recent_user_msgs`: list of recent messages
- `short_mem`: short-term memory (Deque)
- `long_mem`: dict of reflections per user
- `user_models`: dict of user model descriptions
- `prompts`: dict of system/user templates
- `model_name`: model identifier
- `user_labels`: user label map

#### Outputs
- `generate_reflection`: `Optional[str]` (reflection text)
- `update_user_model`: `Optional[str]` (user model text)
- `batch_update_user_states`: `(long_mem: Dict[str, List[str]], user_models: Dict[str, str])`


### 1) `agent_peer_argument module.py`

#### 워크플로우
1. **과제/선택지 기반 입장 생성**: `build_task_profile_components`가 persona와 task/choice를 이용해 모델로부터 입장(stance)을 생성합니다.
2. **가치 기반 논거 수집**: 같은 함수에서 가치(value) 중심 논거를 JSON 형식으로 받아 `Argument` 목록으로 변환합니다.
3. **힌트 그룹 선택**: `select_hint_group`가 아직 언급되지 않은 논거 그룹을 찾아 힌트로 사용합니다.
4. **시스템 프롬프트 구성**: `build_system_prompt`가 persona, stance, 기억(반성), 그룹 요약, 힌트를 반영하여 시스템 메시지를 조립합니다.
5. **최종 프롬프트 준비**: `prepare_prompt_with_hint`가 힌트 그룹을 확정하고 시스템 프롬프트 및 로그를 반환합니다.

#### 인풋
- `client`: LLM API 클라이언트
- `task_text`, `choice_text`: 과제/선택지 텍스트
- `persona`: 이름과 설명을 포함한 딕셔너리
- `prompts`: 시스템/유저 템플릿을 담은 딕셔너리
- `model_name`: 사용할 모델명
- `value_groups`: 가치 그룹 목록
- `short_mem`, `long_mem`: 메모리(최근/장기) 구조
- `arg_bank`: `Argument` 리스트

#### 아웃풋
- `build_task_profile_components`: `(stance: str, arg_bank: List[Argument], log: str)`
- `select_hint_group`: `Optional[str]` (선택된 논거 그룹)
- `build_system_prompt`: `str` (시스템 메시지)
- `prepare_prompt_with_hint`: `(system_prompt: str, hint_group: Optional[str], log: str)`

### 2) `agent_support_mediate_module.py`

#### 워크플로우
1. **최근 대화 반성 생성**: `generate_reflection`이 최근 사용자 메시지를 요약/반성문으로 생성합니다.
2. **사용자 모델 업데이트**: `update_user_model`이 누적 반성을 기반으로 사용자 모델을 갱신합니다.
3. **배치 업데이트**: `batch_update_user_states`가 두 사용자의 최근 대화/반성을 동시에 평가해 반성과 모델을 JSON으로 받아 갱신합니다.

#### 인풋
- `client`: LLM API 클라이언트
- `user_id`, `user_ids`: 사용자 식별자
- `recent_user_msgs`: 최근 사용자 메시지 리스트
- `short_mem`: 최근 대화 메모리(Deque)
- `long_mem`: 사용자별 반성 리스트 딕셔너리
- `user_models`: 사용자별 모델 설명 딕셔너리
- `prompts`: 시스템/유저 템플릿을 담은 딕셔너리
- `model_name`: 사용할 모델명
- `user_labels`: 사용자 라벨 맵

#### 아웃풋
- `generate_reflection`: `Optional[str]` (반성 텍스트)
- `update_user_model`: `Optional[str]` (사용자 모델 텍스트)
- `batch_update_user_states`: `(long_mem: Dict[str, List[str]], user_models: Dict[str, str])`
