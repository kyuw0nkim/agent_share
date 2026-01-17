# agent_share

## ENG

### Overview
This repository contains two Python modules that handle argument generation and user state updates (reflections/user models) for a dialogue-based agent.
Both modules load the canonical, non-templated prompt text from `raw_prompt_modules.py` so the original prompt blocks are used verbatim.

### 1) `agent_peer_argument module.py`

#### Workflow
1. **Generate stance from task/choice**: `build_task_profile_components` creates a stance using persona and task/choice inputs.
2. **Collect value-based arguments**: The same function requests value-based arguments in JSON and converts them into an `Argument` list.
3. **Judge coverage**: Use the coverage prompt and parse the JSON output.
4. **Mark mentioned groups**: `update_argument_mentions_from_coverage` flags covered groups in the argument bank.
5. **Select a hint group**: `generate_hint_selection` picks a hint from unmentioned candidates (default cadence: every turn).
6. **Build system prompt**: `build_system_prompt` composes a system message from persona, stance, reflections, and hint.
7. **Prepare final prompt**: `prepare_prompt_with_hint` finalizes the hint group and returns the system prompt and logs.
8. **Decide to respond**: `generate_action_decision` returns a JSON decision for whether to respond.
9. **Generate peer response**: `generate_peer_response` creates a 1–2 sentence response.

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
- `generate_hint_selection`: `Optional[str]` (LLM hint selection with update cadence)
- `format_value_mapping`: `str` (index → group mapping for coverage prompts)
- `update_argument_mentions_from_coverage`: `None` (mutates `Argument.mentioned`)
- `build_system_prompt`: `str` (system message)
- `prepare_prompt_with_hint`: `(system_prompt: str, hint_group: Optional[str], log: str)`
- `generate_action_decision`: `Dict[str, str]` (JSON decision)
- `generate_peer_response`: `str` (peer response)

### 2) `agent_support_mediate_module.py`

#### Workflow
1. **Generate reflection from recent chat**: `generate_reflection` creates a reflection based on recent user messages.
2. **Update user model**: `update_user_model` refreshes the user model from accumulated reflections.
3. **Generate support LTM**: `generate_support_ltm` returns user_1/user_2/global JSON insights.
4. **Batch update**: `batch_update_user_states` evaluates two users at once and updates reflections/models from JSON output.

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
- `generate_support_ltm`: `Optional[Dict[str, Dict[str, str]]]` (JSON insights)
- `batch_update_user_states`: `(long_mem: Dict[str, List[str]], user_models: Dict[str, str])`

## KOR

### 프롬프트 모듈 정리 (초안)

아래는 현재 프롬프트를 **Peer Agent**와 **Supporting Agent**로 분리해, 모듈 이름/입력/출력/역할 흐름을 일관되게 정리한 초안입니다. 실제 적용 전, 용어·스키마는 필요에 따라 조정 가능합니다.
`raw_prompt_modules.py`에는 처음 제공된 프롬프트를 템플릿화하지 않고 그대로 담아둔 원문 프롬프트 묶음이 포함되어 있습니다.

#### A. Peer Agent (토론 파트너)

**전체 흐름**
1) Stance Generation → 2) Argument Generation → 3) Coverage Judgement → 4) Long-Term Memory Generation → 5) Action Manager → 6) Response Generator

**1) Stance Generation (New Module)**
- **입력**: `TASK`, `CHOICE`
- **역할**: 선택지를 지지하는 간결한 입장(한국어)
- **출력**: 한국어 불릿 3~5개

**2) Argument Generation (New Module)**
- **입력**: `TASK`, `STANCE`
- **역할**: 19개 가치 프레임워크마다 1개 논거 생성
- **출력(JSON)**:
```json
{
  "items": [
    { "group": "Self-direction–thought", "claim": "..." }
  ]
}
```
- **조건**: 한국어 1문장, “~할 수 있습니다/가능성이 큽니다” 형식, 이유/원인 포함

**3) Coverage Judgement (New Module)**
- **입력**: `CHAT HISTORY`, `TARGET VALUES`
- **역할**: 각 가치 그룹이 대화에서 언급되었는지 판정
- **출력(JSON)**:
```json
{
  "items": [
    { "index": 0, "mentioned": true, "rationale": "..." }
  ]
}
```
- **조건**: `rationale` 필드 필수

**4) Long-Term Memory Generation (New Module)**
- **입력**: 최근 5개 발화
- **역할**: 저장할 1개 인사이트 도출(가치/성향 중심)
- **출력(JSON)**:
```json
{ "insight": "...", "evidence": "..." }
```

**5) Action Manager (New Module)**
- **입력**: 논거 후보, 대화 맥락, 장기 메모리
- **역할**: 지금 발화할지 결정
- **출력(JSON)**:
```json
{ "decision": "Respond/Don't respond", "reason": "..." }
```

**6) Response Generator (New Module)**
- **입력**: Action Manager 결정, 선택 논거, 대화 맥락
- **역할**: 15~20단어, 1~2문장, 동료 톤의 한국어 응답 생성
- **출력**: 한국어 1~2문장

#### B. Supporting Agent (중재/지원)

**전체 흐름**
1) Long-Term Memory Generation → 2) Action Manager → 3) Response Generator

**1) Long-Term Memory Generation (Supporting Agent)**
- **입력**: 최근 발화들
- **역할**: 사용자별 + 전체 그룹 인사이트 추론
- **출력(JSON)**:
```json
{
  "user_1": { "insight": "...", "evidence": "..." },
  "user_2": { "insight": "...", "evidence": "..." },
  "global": { "insight": "...", "evidence": "..." }
}
```

**2) Action Manager (Supporting Agent)**
- **입력**: 대화 맥락 요약, 사용자 모델, 장기 메모리
- **역할**: 개입 여부 + 단일 지원 전략 선택
- **출력(JSON)**:
```json
{
  "decision": "Respond / Don't respond",
  "reason": "...",
  "category": "Constructive reasoning | Interactive reasoning | Uncertainty handling | Social expressions | n/a",
  "strategy": "..." 
}
```
 - **조건**: `category`/`strategy`는 고정된 집합에서만 선택

**3) Response Generator (Supporting Agent)**
- **입력**: Action Manager 결정, 전략, 맥락
- **역할**: 15~20단어, 1~2문장, 촉진형 발화
- **출력**: 한국어 1~2문장

#### 결정 사항 반영
- Stance Generation: 불릿 **3~5개**로 유연하게 생성
- Coverage Judgement: `rationale` **필수**
- Supporting Agent Action Manager: `category`/`strategy`는 **고정된 집합 강제**

#### Peer Agent 힌트 그룹(비동기) 흐름 메모
- **의도**: 메인 대화 응답과 별도로, 다음 턴에서 쓸 가치 관점을 미리 선정해 일관된 흐름을 유지.
- **동작**: Coverage Judgement로 미언급 가치 후보를 갱신 → Hint Selector가 다음 힌트 그룹 1개 선택 → 다음 턴 system prompt에 hint로 삽입.
- **선정 방식**: 기본은 **미언급 후보 우선 + 최근 힌트와 연속성**을 고려해 1개를 고름. 대화 맥락과 어색함 여부를 함께 판단하며, 필요하면 현재 힌트를 유지해 관점 전환 빈도를 낮춘다.
- **효과**: 매 턴 즉흥적으로 관점을 바꾸기보다, “지금-다음” 1턴 앞을 보고 자연스럽게 주제 전개.

#### Colab 간단 테스트 코드
- 각 파이프라인을 빠르게 점검하려면 `colab_pipeline_quick_test.py`를 참고하세요.

### 1) `agent_peer_argument module.py`

#### 워크플로우
1. **과제/선택지 기반 입장 생성**: `build_task_profile_components`가 persona와 task/choice를 이용해 모델로부터 입장(stance)을 생성합니다.
2. **가치 기반 논거 수집**: 같은 함수에서 가치(value) 중심 논거를 JSON 형식으로 받아 `Argument` 목록으로 변환합니다.
3. **커버리지 판정**: Coverage Judgement JSON을 파싱합니다.
4. **언급 여부 반영**: `update_argument_mentions_from_coverage`로 논거의 `mentioned` 상태를 갱신합니다.
5. **힌트 그룹 선택**: `generate_hint_selection`으로 미언급 후보 중 하나를 선택합니다(기본: 매 턴 업데이트).
6. **시스템 프롬프트 구성**: `build_system_prompt`가 persona, stance, 기억(반성), 힌트를 반영하여 시스템 메시지를 조립합니다.
7. **최종 프롬프트 준비**: `prepare_prompt_with_hint`가 힌트 그룹을 확정하고 시스템 프롬프트 및 로그를 반환합니다.
8. **발화 여부 판단**: `generate_action_decision`가 JSON 결정값을 반환합니다.
9. **응답 생성**: `generate_peer_response`가 1~2문장 응답을 생성합니다.

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
- `generate_action_decision`: `Dict[str, str]` (JSON 결정)
- `generate_peer_response`: `str` (피어 응답)

### 2) `agent_support_mediate_module.py`

#### 워크플로우
1. **최근 대화 반성 생성**: `generate_reflection`이 최근 사용자 메시지를 요약/반성문으로 생성합니다.
2. **사용자 모델 업데이트**: `update_user_model`이 누적 반성을 기반으로 사용자 모델을 갱신합니다.
3. **지원 LTM 생성**: `generate_support_ltm`이 user_1/user_2/global JSON 인사이트를 생성합니다.
4. **배치 업데이트**: `batch_update_user_states`가 두 사용자의 최근 대화/반성을 동시에 평가해 반성과 모델을 JSON으로 받아 갱신합니다.

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
- `generate_support_ltm`: `Optional[Dict[str, Dict[str, str]]]` (지원 LTM JSON)
- `batch_update_user_states`: `(long_mem: Dict[str, List[str]], user_models: Dict[str, str])`
