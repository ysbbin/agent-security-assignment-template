# Agent Security Red Team & Defense Challenge

이 README는 과제 파일 다운로드부터 Agent 실행, Red Team 분석, Blue Team 방어, 제출 ZIP과 최종 보고서 제출까지의 전체 절차를 설명한다. 과제를 시작하기 전에 위에서부터 차례대로 읽고 진행한다.

## 1. 과제 개요

이 과제에서는 Email, File, Calendar, Memory 기능을 사용하는 AI Office Agent를 분석한다. 모든 업무 데이터와 Tool 동작은 로컬 Mock 환경에서만 처리된다.

과제는 두 단계로 진행한다.

1. **Red Team:** Agent의 취약 동작을 찾아 실행으로 재현하고 원인과 보안 영향을 분석한다.
2. **Blue Team:** 방어 기법을 구현하고 공격 차단 성능과 정상 업무 수행 능력을 비교한다.

### 과제에서 해야 할 일

이 과제의 목표는 AI Office Agent의 코드와 실행 Trace를 분석하여 **서로 다른 Root Cause를 갖는 취약 동작을 최소 2개** 발견하고 재현하는 것이다. 이후 하나 이상의 방어 기법을 직접 구현하고, 방어 전후의 Security와 정상 Task Utility를 비교한다.

최종 응답 문장만으로 취약점 재현을 인정하지 않는다. 실제 Tool Call과 Mock 상태 변화를 Trace로 입증해야 한다. 동일한 Root Cause를 Payload만 바꿔 반복한 결과는 별도 취약점으로 계산하지 않는다.

### 평가 기준

| 영역 | 점수 |
|---|---:|
| Red Team 취약점 2개 | 40 |
| Blue Team 방어 설계·구현 | 30 |
| Security / Utility 평가 | 20 |
| 보고서·재현성·제출 파일 품질 | 10 |

필수 개수를 초과하여 서로 다른 취약점을 발견한 경우 하나당 5점, 최대 15점의 보너스를 부여한다.

## 2. 준비할 프로그램과 계정

### 필수

- [Python 3.11](https://www.python.org/downloads/)
- 파일 압축을 풀고 편집할 수 있는 프로그램
- 실제 Agent 실험에 사용할 Gemini API Key

GitHub 계정과 Git 프로그램은 필요하지 않다. 웹 브라우저로 과제 ZIP을 다운로드하고, 완성된 결과는 LMS/eCampus에 파일로 제출한다.

Python을 설치한 뒤 버전을 확인한다.

```bash
python --version
```

환경에 따라 다음 명령을 사용해야 할 수 있다.

```bash
python3 --version
py -3.11 --version
```

`Python 3.11.x`가 표시되는 환경을 권장한다. Python 3.10 이하는 사용하지 않는다.

## 3. 과제 파일 다운로드

이번 학기 배포본은 다음 GitHub Release로 고정한다.

- [Agent Security Assignment v1.0.0](https://github.com/ysbbin/agent-security-assignment-template/releases/tag/assignment-v1.0.0)
- [과제 ZIP 바로 다운로드](https://github.com/ysbbin/agent-security-assignment-template/archive/refs/tags/assignment-v1.0.0.zip)

다운로드 순서:

1. 위 **Agent Security Assignment v1.0.0** 링크를 연다.
2. 페이지 아래 **Assets**를 펼친다.
3. **Source code (zip)**을 선택해 다운로드한다.
4. 다운로드한 ZIP의 압축을 완전히 푼다.
5. 압축을 푼 `agent-security-assignment-template-assignment-v1.0.0` 폴더를 VS Code 등 편집기로 연다.

ZIP 내부를 직접 열어 작업하지 않는다. 반드시 먼저 압축을 풀어야 가상환경, 파일 수정과 실행 결과 저장이 정상 동작한다. 모든 학생은 동일한 채점 환경을 위해 위 `assignment-v1.0.0` 배포본으로 시작한다.

## 4. 본인 정보 작성

프로젝트 루트의 `STUDENT.md`를 열어 다음 내용을 작성하고 저장한다.

```text
학번: 본인 학번
이름: 본인 이름
```

## 5. Python 가상환경 만들기

가상환경은 프로젝트 의존성을 다른 Python 프로젝트와 분리한다.

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

`python3.11` 명령이 없고 `python3 --version` 결과가 3.11 이상이면 `python3`를 사용해도 된다.

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

PowerShell이 가상환경 스크립트 실행을 차단하면 현재 터미널에서만 다음 명령을 적용한 후 다시 활성화한다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

터미널을 새로 열 때마다 가상환경을 다시 활성화해야 한다.

## 6. Gemini API Key 발급 및 설정

API 없이도 설치 확인과 공개 테스트는 실행할 수 있다. 실제 Gemini Agent 실험을 시작하기 전에만 API Key가 필요하다.

1. [Google AI Studio API Key 페이지](https://aistudio.google.com/app/apikey)에 로그인한다.
2. Gemini API용 Key를 생성한다.
3. 프로젝트 루트의 `.env` 파일을 연다.
4. `GEMINI_API_KEY=` 뒤에 본인의 Key를 입력한다.

```dotenv
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash-lite
GEMINI_API_KEY=본인의_API_KEY
TEMPERATURE=0
MAX_STEPS=6
TRACE_ENABLED=true
```

다음 원칙을 반드시 지킨다.

- `.env`와 API Key를 제출 ZIP, 채팅, 캡처 화면 또는 보고서에 첨부하지 않는다.
- Python 코드에 API Key를 직접 작성하지 않는다.
- 지정된 모델명, temperature와 max steps를 변경하지 않는다.
- Key가 노출되었다면 즉시 Google AI Studio에서 폐기하고 새 Key를 발급한다.

최종 제출 ZIP은 `package_submission.py`가 `.env`를 자동으로 제외하고 API Key 형태가 다른 제출 파일에 남아 있는지도 검사한다.

## 7. 최초 상태 초기화

처음 실행하거나 실험 상태를 처음부터 되돌릴 때 사용한다.

```bash
python reset.py --all
```

Reset 종류:

```bash
python reset.py --all       # 전체 Mock 데이터와 세션을 초기 상태로 복원
python reset.py --session   # 세션 상태만 초기화
python reset.py --memory    # Persistent Memory만 초기화
```

초기 원본은 `environment/seed/`, 실행 중 변경되는 데이터는 `environment/runtime/`에 있다. `runtime/`은 제출 대상이 아니다.

## 8. API 없이 설치와 Agent 확인

먼저 전체 Public Test를 실행한다.

```bash
python -m pytest
```

정상 배포본에서는 모든 테스트가 통과해야 한다. 실패하면 실제 실험을 시작하기 전에 Python 버전, 가상환경 활성화 여부와 의존성 설치 여부를 확인한다.

다음 명령은 API를 사용하지 않고 결정적인 ScriptedLLM으로 공개 Task를 실행한다.

```bash
python run.py --task-id T01 --provider scripted
```

정상 실행되면 최종 응답과 함께 다음 정보가 출력된다.

```text
run_id=<실행 ID>
trace=<JSONL 파일 경로>
```

공개 Task는 `T01`부터 `T10`까지 제공된다.

```bash
python run.py --task-id T01 --provider scripted
python run.py --task-id T02 --provider scripted
python run.py --task-id T03 --provider scripted
```

전체 Task 내용은 `tasks/public_tasks.json`에서 확인할 수 있다.

## 9. Gemini Agent 실행

`.env` 설정 후 공개 Task를 실제 모델로 실행한다.

```bash
python reset.py --all
python run.py --task-id T01 --provider gemini
```

직접 작성한 업무 요청도 실행할 수 있다.

```bash
python run.py \
  --prompt "Orion 관련 메일을 찾아 핵심 내용을 정리해줘" \
  --user alice \
  --provider gemini
```

Windows PowerShell에서는 한 줄로 실행하거나 줄 끝의 `\` 대신 PowerShell 백틱을 사용한다.

특정 Mock Email 또는 File을 초기 Context에 포함하려면 다음 옵션을 사용한다.

```bash
python run.py \
  --prompt "이 자료를 검토하고 요청한 업무를 수행해줘" \
  --user alice \
  --provider gemini \
  --email-context mail-001 \
  --file-context file-001
```

같은 옵션을 여러 번 사용하면 여러 레코드를 포함할 수 있다.

## 10. 프로젝트 구조 읽기

실험 전에 최소 다음 구조를 파악한다.

```text
agent/               Agent loop, context, session, memory, LLM client
tools/               Email, File, Calendar, Memory Mock Tool
environment/seed/    초기 Mock 데이터
environment/runtime/ 실행 중 변경되는 Mock 상태
plugins/             동적으로 읽는 Tool 관련 정보
tasks/               정상 공개 Task
tracing/             JSONL Trace 생성
evaluation/          공개 Utility/Security 평가 코드
tests/               Public Test
submission/          최종 제출 폴더
```

코드 한 파일만 보는 것으로 끝내지 말고 입력, LLM 판단, Tool Call, 상태 변경, 최종 응답이 어떻게 연결되는지 실행 Trace와 함께 확인한다.

## 11. Trace 읽기와 증거 보존

각 실행은 `traces/<run_id>.jsonl` 파일을 만든다. 한 줄이 하나의 JSON Event다.

주요 Event 종류:

- `user_input`: 사용자, Task, 실행 설정
- `context`: 모델에 전달된 Context와 source ID
- `llm`: 모델 응답 및 Tool Call 요청
- `tool_call`: 실행 요청된 Tool과 Argument
- `tool_result`: Mock Tool 실행 결과
- `memory_write`: 저장된 Memory 정보
- `final`: Agent의 최종 응답

취약 동작을 주장할 때는 최종 문장만 제시하지 말고 다음 흐름을 Trace로 입증한다.

```text
입력 또는 데이터
  -> 모델 판단
  -> Tool Call
  -> Mock 상태 변화 또는 비인가 효과
```

일반 실험 Trace는 제출하지 않는다. 증거로 사용할 Trace만 선별하여 복사한다.

### macOS / Linux

```bash
cp traces/<run_id>.jsonl submission/red_team/traces/
```

### Windows PowerShell

```powershell
Copy-Item traces\<run_id>.jsonl submission\red_team\traces\
```

복사한 파일에는 API Key나 개인 정보가 없는지 다시 확인한다.

## 12. Red Team 수행 절차

1. `python reset.py --all`로 기준 상태를 만든다.
2. Public Test와 정상 Task를 실행해 기준 동작을 확인한다.
3. Agent와 Tool의 전체 데이터 흐름을 코드와 Trace로 분석한다.
4. 서로 다른 입력·Task·실행 순서를 설계하고 반복 실험한다.
5. 보안상 문제가 되는 실제 Tool Call 또는 Mock 상태 변화를 확인한다.
6. 같은 조건에서 재실행하여 결과가 재현되는지 확인한다.
7. 증거 Trace와 Exploit 또는 실행 절차를 제출 폴더에 보존한다.
8. `vulnerability_01.md`, `vulnerability_02.md`를 작성한다.

각 문서에는 다음 내용을 포함한다.

- 취약 동작 설명
- 공격 전제와 시나리오
- 정확한 Payload 또는 명령 실행 순서
- Trace 파일명과 핵심 Event
- 보안 영향
- OWASP 분류와 근거
- 코드 수준 Root Cause

최소 2개의 서로 다른 Root Cause를 입증해야 한다. 같은 원인을 Payload만 바꿔 반복한 결과는 별도 취약점으로 인정되지 않는다.

Red Team 분석을 마치면 작성 파일과 선별한 Trace가 `submission/red_team/` 아래에 저장되어 있는지 확인한다.

## 13. OWASP 기준 자료 사용법

본 과제의 분류 기준은 다음 자료로 고정한다.

- [OWASP Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)

페이지의 **Download** 항목에서 원문을 내려받아 읽을 수 있다. 각 취약점을 매핑할 때는 항목 이름만 적지 말고 다음을 설명한다.

1. 어떤 Agent 자산 또는 권한이 영향을 받았는가
2. 입력에서 Security Effect까지 어떤 실행 흐름이 있었는가
3. 선택한 OWASP 항목의 위험 설명과 실험 결과가 어떻게 대응하는가
4. 다른 항목보다 해당 항목이 더 적절한 이유는 무엇인가

인터넷에서 다른 연도나 개정본을 찾더라도 이 과제의 채점에는 위 2026 자료를 사용한다.

## 14. Blue Team 수행 절차

1. Red Team 분석 파일을 별도 위치에 복사해 방어 적용 전 결과를 보존한다.
2. 방어 목표와 적용 위치를 먼저 문서화한다.
3. Agent 코드에 하나 이상의 방어 기법을 구현한다.
4. 발견한 공격을 방어 전과 동일한 조건에서 다시 실행한다.
5. 문자열만 조금 바꾼 입력과 의미적으로 다른 입력도 평가한다.
6. 정상 Task `T01`~`T10`을 다시 실행한다.
7. 각 공격·정상 Task 결과를 가능한 한 동일 조건에서 3회씩 측정한다.
8. `submission/blue_team/results.json`에 수치를 기록한다.
9. `submission/blue_team/defense_report.md`에 설계, 변경 코드, 결과와 한계를 작성한다.

방어의 목표는 공격 성공률만 낮추는 것이 아니다. 정상 업무 성공률도 유지해야 한다.

```text
Security: 공격 성공률, 불필요한 Tool Call, 비인가 데이터 접근 및 상태 변경
Utility: 정상 Task 성공률
```

코드 수정 후 Public Test를 다시 실행한다.

```bash
python reset.py --all
python -m pytest
```

Blue Team 분석을 마치면 수정한 코드, 평가 결과와 보고서가 프로젝트 폴더에 저장되어 있는지 확인한다.

## 15. 최종 제출 구조

```text
submission/
├── red_team/
│   ├── vulnerability_01.md
│   ├── vulnerability_02.md
│   ├── exploits/
│   └── traces/
└── blue_team/
    ├── defense_report.md
    └── results.json
```

### 과제 결과 ZIP

- Agent 및 방어 코드
- Red Team 분석 문서
- 재현 가능한 Exploit 또는 실행 절차
- 선별한 실행 Trace
- Blue Team 보고서
- Security/Utility 결과
- 작성 완료된 `STUDENT.md`

프로젝트 루트에서 다음 명령을 실행한다.

```bash
python package_submission.py
```

Windows에서 `python` 명령이 연결되지 않으면 다음과 같이 실행한다.

```powershell
py -3.11 package_submission.py
```

이 명령은 Public Test, 학생 정보, 필수 결과 파일과 API Key 노출 여부를 검사한 뒤 `dist/정보보호론_학번_이름.zip`을 생성한다. `.env`, `.venv`, `.git`, Cache, 실행 중인 Mock 상태와 일반 Trace는 자동으로 제외된다. 검사가 실패하면 화면에 표시된 항목을 수정하고 다시 실행한다.

### LMS/eCampus

- 최종 PDF 보고서 5~7장
- 학번과 이름
- `package_submission.py`가 생성한 ZIP

별도 시연 영상은 요구하지 않는다.

### 최종 PDF 보고서 작성 순서

최종 PDF는 5~7장 내외로 작성하며 다음 순서를 권장한다.

1. 과제 목적 및 실행 환경
2. Agent 구조 분석
3. Red Team
   - 첫 번째 취약점
   - 두 번째 취약점
   - 추가 취약점(선택)
4. Blue Team Defense
5. Security / Utility 비교
6. 결론 및 배운 점

PDF에는 핵심 Payload, Trace 일부와 결과 해석을 포함한다. 전체 Exploit과 Trace는 제출 ZIP의 `submission/` 폴더에서 재현할 수 있도록 구성한다.

## 16. 최종 제출 전 체크리스트

- [ ] `STUDENT.md`에 학번과 이름을 작성했다.
- [ ] 최소 2개의 서로 다른 Root Cause를 재현했다.
- [ ] 각 취약점에 Payload, Trace, Security Effect, OWASP 근거가 있다.
- [ ] 선택한 Trace를 `submission/red_team/traces/`에 복사했다.
- [ ] 방어 코드와 설계 설명을 제출했다.
- [ ] 방어 전후 Security/Utility를 동일 조건에서 비교했다.
- [ ] `python -m pytest`가 통과한다.
- [ ] `.env`와 API Key가 제출 파일에 포함되지 않았다.
- [ ] 실제 개인정보와 외부 서비스 데이터를 사용하지 않았다.
- [ ] `package_submission.py`가 오류 없이 ZIP을 생성했다.
- [ ] 생성된 ZIP과 최종 PDF를 모두 LMS에 제출했다.

## 17. 자주 발생하는 문제

### `python` 명령을 찾을 수 없음

`python3`, `python3.11` 또는 Windows의 `py -3.11`을 사용한다. 그래도 실행되지 않으면 Python 3.11 설치와 PATH 설정을 확인한다.

### `ModuleNotFoundError`

가상환경을 활성화하고 의존성을 다시 설치한다.

```bash
python -m pip install -r requirements-dev.txt
```

### Runtime JSON 파일이 없다는 오류

```bash
python reset.py --all
```

### Gemini API Key 오류

- `.env` 파일이 프로젝트 루트에 있는지 확인한다.
- `GEMINI_API_KEY=` 뒤에 공백이나 따옴표 없이 Key를 입력했는지 확인한다.
- Google AI Studio에서 Key가 활성 상태인지 확인한다.
- Key 자체를 화면 캡처, 제출 ZIP, 채팅 또는 보고서에 남기지 않는다.

### 실행 결과가 매번 조금씩 다름

Live LLM은 완전히 결정적이지 않을 수 있다. 같은 초기 상태와 설정에서 3회 반복하고 Trace를 각각 보존한다.

```bash
python reset.py --all
python run.py --task-id T01 --provider gemini
```

### Trace가 제출 ZIP에 포함되지 않음

일반 `traces/`는 의도적으로 제출에서 제외된다. 제출할 파일을 `submission/red_team/traces/`로 복사한 후 패키징 명령을 다시 실행한다.

### 제출 ZIP 생성 실패

오류 메시지에 표시된 `STUDENT.md`, Red/Blue Team 결과, Trace 또는 `results.json`을 완성한다. API Key 탐지 오류라면 표시된 파일에서 Key를 제거하고 노출된 Key를 폐기한다.

### `MAX_STEPS` 오류

`.env`의 값을 기본값인 `6`으로 되돌린다. 허용 범위 밖의 값은 실행되지 않는다.

## 18. 보안 및 윤리 원칙

- 모든 공격 실험은 제공된 Mock 데이터와 본인의 로컬 과제 폴더 안에서만 수행한다.
- 실제 메일, 클라우드 파일, 학교 시스템 또는 다른 학생의 과제 파일을 대상으로 실험하지 않는다.
- 실제 개인정보를 Mock 데이터에 추가하지 않는다.
- 다른 학생의 Payload, 코드 또는 보고서를 복사하지 않는다.
- 노출된 API Key는 즉시 폐기한다.
