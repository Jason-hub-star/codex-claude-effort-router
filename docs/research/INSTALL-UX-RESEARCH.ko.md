# 유명 하네스 설치 UX 조사와 로컬 검증

조사일: 2026-09-07 (Asia/Seoul). 별 수는 GitHub REST API의 당일 스냅샷이며 품질 점수가 아니다.

## 공식 설치 경로 비교

| 프로젝트 | 별 | 초보자 설치 경로 | 선택·유지 경험 |
|---|---:|---|---|
| [obra/superpowers](https://github.com/obra/superpowers#installation) | 282,667 | Claude와 Codex 공식 마켓플레이스 | 호스트별 재설치·업데이트가 쉽지만 여러 호스트를 쓰면 각각 설치해야 한다. |
| [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD/blob/main/docs/how-to/install-bmad.md) | 52,753 | `npx bmad-method install` 대화형 설치 | 모듈·AI 도구·버전 채널을 선택하며 설치 후 `bmad-help`가 다음 행동을 안내한다. |
| [wshobson/agents](https://github.com/wshobson/agents/blob/main/docs/harnesses.md) | 39,466 | 마켓플레이스 또는 `gh skill`/`npx skills` | 큰 번들을 플러그인이나 스킬 하나 단위로 설치할 수 있다. |
| [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin#install) | 24,930 | Claude·Codex를 포함한 다수 호스트별 명령 | 업데이트 절차와 설치 후 `/ce-setup`을 명시하지만 문서량이 많다. |

공통 성공 패턴은 세 가지였다.

1. 복사해서 실행할 수 있는 짧은 설치 명령
2. 전부가 아닌 모듈·플러그인·스킬 단위 선택
3. 설치 직후 상태를 확인하거나 다음 행동을 알려주는 진입점

이 저장소는 2번을 `--skills`와 표준 `skills/<name>/SKILL.md` 구조로 충족한다. [Vercel의 공개 Agent Skills CLI](https://github.com/vercel-labs/skills)는 이 구조에서 7개 스킬을 모두 발견했고, 로컬 임시 프로젝트에 `agent-starter`를 정확히 복사했다. 코어 훅과 프로필은 런타임별 설정을 병합해야 하므로 별도 Bash 설치기를 유지한다.

## 깨끗한 환경 테스트

실제 사용자 홈을 건드리지 않고 임시 Codex/Claude 홈에서 실행했다.

| 시나리오 | 결과 |
|---|---|
| 기본 설치 | PASS — 코어만 설치하고 스킬 디렉터리는 만들지 않음 |
| `--starter` | PASS — 7개 스킬이 두 런타임에 각각 설치됨 |
| `--skills` | PASS — 쉼표 뒤 공백 허용, 지정 스킬만 설치 |
| 중복 스킬 | PASS — 한 번만 설치하고 실제 개수 1로 보고 |
| `--list-skills` | PASS — 쓰기와 `jq` 없이 7개 표시 |
| `--help`, `--dry-run` | PASS — 사용법 표시와 무변경 사전 점검 |
| 기존 스킬 | PASS — 두 런타임 모두 1회 `.effort-router.bak` 보존 |
| 경로에 공백 | PASS — 두 런타임 설치 성공 |
| `jq` 또는 Python 3 없음 | PASS — 쓰기 전 명확한 오류로 중단 |
| 기존 설정 JSON 손상 | PASS — 어느 런타임에도 새 파일을 쓰지 않고 중단 |
| Claude 홈이 파일인 반쪽 설치 조건 | PASS — Codex를 쓰기 전에 중단 |
| 재설치 | PASS — 훅·스킬 해시 동일, 자체 훅은 정확히 하나 |
| 잘못된·빈 스킬 이름 | PASS — 쓰기 전 비정상 종료 |
| `npx skills ... --list` | PASS — 7개 표준 스킬 발견 |
| `npx skills ... --skill agent-starter --copy` | PASS — 임시 프로젝트에 원본과 동일한 파일 설치 |

자동 검증은 `bash scripts/check.sh`에 포함된다. `npx skills` 실험은 외부 CLI와 네트워크 상태에 영향을 받으므로 저장소 CI의 필수 게이트로 만들지 않았다.

## 현재 판정

**7.5/10 — 기술 초보와 기존 하네스 리믹스 사용자에게 공개 사용 가능한 상태.**

강점은 작은 기본 설치, 한 번에 전부 또는 개별 스킬 선택, 기존 훅 보존, 1회 백업, fail-open, 재실행 수렴, 깨끗한 홈 회귀 테스트다. 스킬만 필요한 사용자는 범용 CLI로 저장소 복제 없이 시작할 수 있다.

남은 차이는 네이티브 마켓플레이스 등록, 코어 설치 상태·업데이트·제거 명령, Windows 검증이다. 또한 사전 점검으로 알려진 반쪽 설치 조건은 막았지만 디스크 고장처럼 쓰기 도중 발생하는 운영체제 실패까지 트랜잭션으로 되돌리지는 않는다. 따라서 현재는 “원클릭 소비자 제품”보다 “검증 가능한 공개 개발자 하네스”에 가깝다.

다음 우선순위는 사용자가 생긴 뒤 실제 이탈 지점을 측정하고, 필요할 때 `--status`/안전 제거 또는 Codex·Claude 마켓플레이스 패키지를 추가하는 것이다.
