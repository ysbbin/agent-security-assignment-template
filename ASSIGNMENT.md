# 과제 안내

## 목표

AI Office Agent의 코드와 실행 Trace를 분석하여 서로 다른 Root Cause를 갖는 취약 동작을 최소 2개 발견하고 재현한다. 이후 방어 기법을 구현하고 공격 전후의 Security와 정상 Task Utility를 비교한다.

## 1단계: Red Team

각 취약점에 대해 다음 내용을 제출한다.

1. Vulnerability Description
2. Attack Scenario
3. Attack Payload 또는 재현 절차
4. Execution Trace와 핵심 Evidence
5. Security Effect
6. OWASP Mapping과 근거
7. Root Cause 분석

최종 응답 문장만으로는 재현을 인정하지 않는다. 실제 Tool Call과 Mock 상태 변화를 Trace로 입증해야 한다. 동일한 Root Cause를 Payload만 바꿔 반복한 경우에는 별도 취약점으로 계산하지 않는다.

## 2단계: Blue Team

- 하나 이상의 방어 기법을 직접 설계하고 구현한다.
- 공개한 공격과 학생이 발견한 공격을 다시 실행한다.
- 정상 Task도 함께 실행한다.
- 공격 성공률과 정상 Task 성공률을 방어 전후로 비교한다.
- 특정 문자열만 차단하는 방식은 충분한 방어로 인정되지 않을 수 있다.

## 제출물

- 수정된 Agent 코드
- `submission/red_team/` 분석 문서, Exploit, 선별 Trace
- `submission/blue_team/defense_report.md`
- `submission/blue_team/results.json`
- 최종 PDF 보고서 5~7장
- 학번, 이름, 개인 GitHub Repository URL

별도 시연 영상은 제출하지 않는다.

## 평가

| 영역 | 점수 |
|---|---:|
| Red Team 취약점 2개 | 40 |
| Blue Team 방어 설계·구현 | 30 |
| Security / Utility 평가 | 20 |
| 보고서·재현성·GitHub 제출 품질 | 10 |

필수 개수를 초과한 서로 다른 취약점에는 하나당 5점, 최대 15점의 보너스를 부여한다.

## OWASP 기준 자료

수업 시작 시 `OWASP Top 10 for Agentic Applications` 고정본 링크를 이 절에 제공한다. 학기 중 분류 기준은 배포 시점의 수업용 고정본이며 이후 온라인 문서 변경은 채점 기준에 반영하지 않는다.

> 개발 상태: 배포용 고정본 링크를 Release 전에 입력해야 한다.

## 금지사항

- 실제 개인정보, 실제 이메일 및 학교 데이터 사용
- Mock 환경 밖의 전송·공유·삭제 시도
- API Key 또는 `.env` Commit
- 타 학생 Repository 접근 및 결과 공유
- 지정 모델·temperature·max steps 변경
