# Codex + Claude 에포트 라우터

Codex와 Claude Code가 같은 결정 규칙을 쓰도록 만드는 작은 공개 하네스입니다. 프롬프트를 Fast, Daily, Deep, Critical 네 단계로 분류하고, 원하면 `아침 → 조준 → 수렴 → 골 → 페이즈루프 → 감사` 습관을 선택형 스킬로 더할 수 있습니다. Codex 자동 위임 힌트는 현재 런타임에서 실제 확인된 내장 `explorer`, `worker`, `default`를 사용합니다.

중요한 한계가 있습니다. `UserPromptSubmit` 훅은 현재 부모 세션의 모델을 몰래 바꾸지 않습니다. 라우팅 문맥을 추가하고, 새 세션 프로필과 위임 대상을 알려주는 역할입니다.

## 설치

Python 3과 `jq`가 필요합니다.

```bash
python3 --version
jq --version
```

둘 중 하나가 없으면 운영체제의 패키지 관리자로 먼저 설치하세요. `--help`와 `--list-skills`는 두 도구 없이도 동작하지만 실제 설치와 `--dry-run`에는 둘 다 필요합니다.

7개 공용 스킬만 필요하면 저장소를 복제하지 않고 범용 Agent Skills CLI로 설치할 수 있습니다.

```bash
npx skills add Jason-hub-star/codex-claude-effort-router --list
npx skills add Jason-hub-star/codex-claude-effort-router --skill agent-starter -g -a codex -a claude-code
```

이 방법은 에포트 라우팅 훅과 Codex 프로필을 설치하지 않습니다. 전체 하네스는 아래처럼 설치합니다.

```bash
git clone https://github.com/Jason-hub-star/codex-claude-effort-router.git
cd codex-claude-effort-router
bash install.sh
```

전체 스타터 팩은 먼저 쓰기 없는 미리보기를 할 수 있습니다.

```bash
bash install.sh --starter --dry-run
bash install.sh --starter
```

설치 후 실행 중인 Codex와 Claude Code 세션을 다시 시작해야 새 에이전트 정의가 보입니다. Codex 커스텀 TOML 역할의 실제 노출 여부는 클라이언트/런타임마다 달라, 포함된 정의는 선택 기능으로 취급합니다.

코어 자동 제거기는 아직 없습니다. Codex나 Claude 디렉터리 전체를 삭제하지 말고, 되돌릴 때는 해당 `*.effort-router.bak`만 내용을 확인한 뒤 복원하세요. 외부 Agent Skills CLI로 설치한 스킬은 `npx skills remove`를 사용할 수 있습니다.

기본 설치는 라우터만 설치합니다. 사용 목적에 따라 아래처럼 고를 수 있습니다.

| 사용자 | 추천 시작 | 설치 범위 |
|---|---|---|
| 에이전트가 처음인 사람 | `bash install.sh --starter` | 코어 + 7개 작업 스킬 |
| 최신 하네스 습관을 시험할 사람 | `bash install.sh --skills morning-brief,evidence-audit` | 지정한 스킬만 추가 |
| 자기 하네스에 섞을 사람 | `bash install.sh --list-skills` | 설치 없이 목록 확인 |

## 선택형 작업 루프

```text
아침 → 조준 → [위험할 때 수렴] → 골 → [3단계 이상이면 페이즈루프] → 감사
```

- `morning-brief`(아침): 이전 결과, 빨간 신호, 미커밋 작업, 다음 행동 하나를 확인합니다.
- `aim-before-build`(조준): 이미 완료·부분 완료·미착수·충돌을 구현 전에 판정합니다.
- `converge-plan`(수렴): 비싼 결정을 반박하며 다듬고 가장 싼 반증 실험으로 끝냅니다.
- `goal-contract`(골): 여러 턴 작업의 완료 조건을 증거 중심 계약으로 고정합니다.
- `phase-loop`(페이즈루프): 단계별 검증을 통과할 때만 다음 단계로 갑니다.
- `evidence-audit`(감사): 직접 증거로 공유 준비 상태를 판정합니다.
- `agent-starter`: 초보자에게 지금 필요한 단계 하나만 골라줍니다.

전 단계를 매번 쓰는 절차가 아닙니다. 작은 질문과 한 줄 수정은 바로 처리합니다. 자세한 조합법은 [스킬 안내](skills/README.md)를 보세요.

`bash install.sh --help`에서 모든 설치 옵션을 확인할 수 있습니다. Superpowers·BMad·wshobson/agents·Compound Engineering과 비교한 [설치 UX 조사](docs/INSTALL-UX-RESEARCH.ko.md)도 남겼습니다. 현재 판정은 “기술 초보와 리믹스 사용자에게 사용 가능, 네이티브 마켓플레이스 수준의 발견·업데이트 경험은 아직 아님”입니다.

## 기본 라우팅

| 단계 | Codex | Claude | 작업 |
|---|---|---|---|
| Fast | Luna / medium | Haiku / medium | 정확한 조회, 목록, 형식 변경 |
| Daily | Terra / medium | Sonnet / medium | 조사, 검토, 설명 |
| Deep | Sol / high | Sonnet / high | 구현, 통합, 디버깅 |
| Critical | Astra / high | Opus / high | 보안, 안전, 되돌리기 어려운 결정 |

이 표는 출발점이지 벤치마크 결론이 아닙니다. 모델 버전, 계정, 업무에 따라 직접 재측정해야 합니다.

## 검증

```bash
bash scripts/check.sh
```

영문·한글 프롬프트 32종, 잘못된 JSON fail-open, 훅 보존, 중복 복구, 기본·선택·전체 스킬 설치, 설치 멱등성을 검사합니다. 자세한 내용은 [검증 기록](evidence/VALIDATION.md)에 있습니다.

![선택형 스타터 워크플로](assets/starter-workflow.svg)

[English README](README.md) · [15초 홍보 영상](assets/effort-router-demo.mp4)
