# Agent Security Red Team & Defense Challenge

Mock Email, Drive, Calendar와 Memory를 사용하는 로컬 AI Office Agent 실습 환경이다. 모든 Tool 동작은 이 저장소의 JSON 상태만 변경한다.

## 요구 환경

- Python 3.11 이상
- 실제 실험 시 개인 Gemini API Key

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python reset.py --all
```

Windows PowerShell에서는 `.venv\Scripts\Activate.ps1`을 사용한다.

## API 없이 공개 Task 실행

```bash
python run.py --task-id T01 --provider scripted
python -m pytest
```

## Gemini로 실행

`.env`의 `GEMINI_API_KEY`를 개인 Key로 설정한 뒤 실행한다.

```bash
python run.py --task-id T01 --provider gemini
```

모델명, temperature와 max steps는 과제에서 지정한 값을 변경하지 않는다.

## 상태 초기화

```bash
python reset.py --all
python reset.py --session
python reset.py --memory
```

일반 실행 Trace는 `traces/`에 생성된다. 제출할 증거만 `submission/red_team/traces/`로 복사한다. `.env`, runtime 상태와 일반 Trace는 Commit하지 않는다.

세부 요구사항은 `ASSIGNMENT.md`, 보고서 형식은 `REPORT_GUIDE.md`를 확인한다.
