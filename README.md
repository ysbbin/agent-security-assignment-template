# Agent Security Red Team & Defense Challenge

Mock Email, Drive, Calendar와 Memory를 사용하는 로컬 AI Office Agent 실습 환경이다. 모든 Tool 동작은 이 저장소의 JSON 상태만 변경한다.

## 먼저 읽을 문서

- [STUDENT_GUIDE.md](STUDENT_GUIDE.md): 프로그램 설치부터 Agent 실행, Red/Blue Team 수행, GitHub 및 최종 제출까지의 전체 절차
- [ASSIGNMENT.md](ASSIGNMENT.md): 필수 산출물과 평가 기준
- [REPORT_GUIDE.md](REPORT_GUIDE.md): 최종 PDF 구성
- [OWASP Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/): 취약점 분류 기준

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

처음 참여하는 학생은 명령을 실행하기 전에 `STUDENT_GUIDE.md`를 처음부터 끝까지 읽는다.
