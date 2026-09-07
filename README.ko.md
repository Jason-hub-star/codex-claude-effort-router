# Effort Lanes

코딩 에이전트 런타임 다섯 개(Codex · Claude Code · OpenCode · OpenClaw · Hermes Agent)가 **같은 노력 정책** 하나를 쓰게 하는 라우터와, 하네스를 쓰이는 크기로 유지하는 작업 습관 모음입니다.

프롬프트마다 **fast · daily · deep · critical** 네 차선 중 하나로 분류합니다. 분류기는 의존성 없는 Python 파일 하나이고, Codex·Claude Code에서는 셸 훅으로, OpenCode·OpenClaw·Hermes에서는 얇은 플러그인 뒤에서 같은 파일이 돕니다. 훅이 모델·추론 강도를 바꿀 수 있는 런타임에서는 차선을 **강제**할 수 있고, 아닌 곳에서는 라우팅 힌트만 넣고 그 사실을 숨기지 않습니다.

![15초 데모](assets/effort-router-demo.gif)

## 왜

모든 프롬프트에 최대 추론을 쓰면 느리고 비싸고, 운영 마이그레이션에 최소 추론을 쓰면 사고가 납니다. 대부분은 설정 하나를 고른 뒤 잊습니다. Effort Lanes는 프롬프트 단위로, 결정적으로, 50ms 안에 고르고, 절대 프롬프트를 막지 않습니다(잘못된 입력·설정·라우터 부재 모두 fail-open).

| 차선 | 신호 | 강도 | Codex 기본 | Claude 기본 |
|---|---|---|---|---|
| Fast | 짧은 조회·개수·정렬 | medium | Luna / medium | Haiku / medium |
| Daily | 조사·검토·설명 | medium | Terra / medium | Sonnet / medium |
| Deep | 구현·리팩터·디버그·E2E | high | Sol / high | Sonnet / high |
| Critical | 보안·운영·결제·안전·반복 실패 | high | Astra / high | Opus / high |

안전 신호가 최우선입니다(`lane=fast audit security`도 Critical). 명시 요청(`lane=deep`, `effort-fast`)이 키워드보다 우선하고, 프로젝트 floor는 차선을 올릴 수만 있습니다.

## 런타임별로 실제로 바뀌는 것

프롬프트 훅은 실행 중인 세션의 모델을 몰래 바꾸지 못합니다. 아래 표가 전부이며, 각 행은 실제 설치에서 실행해 확인했습니다([증거](docs/evidence/VALIDATION.md)).

| 런타임 | 훅 | 문맥 주입 | 프롬프트별 강도·모델 변경 | 검증 |
|---|---|---|---|---|
| Claude Code | `UserPromptSubmit` 셸 훅 | 예 | 아니오 — 차선별 서브에이전트·프로필 제공 | 훅 계약·설치기 |
| Codex | `UserPromptSubmit` 셸 훅 | 예 | 아니오 — 다음 세션용 `codex -p effort-deep` | 훅 계약·설치기·빌트인 위임 |
| **OpenCode** | 플러그인 `chat.message` + `chat.params` | 예 | **예, opt-in** — 호출마다 `reasoningEffort` 지정 | 실행: 모델이 주입된 차선을 그대로 답함 |
| **OpenClaw** | 플러그인 `before_prompt_build` + `before_model_resolve` | 예 | **예, opt-in** — 차선별 provider/model 교체 | `openclaw plugins doctor` 통과, `before_model_resolve` 실발화 |
| Hermes Agent | 플러그인 `pre_llm_call` 또는 같은 이벤트의 셸 훅 | 예 | 아니오 — 상류 이슈 #23739 / #7273 미해결 | `hermes plugins doctor` OK, `hermes hooks test` 파싱 확인 |

강제는 기본 꺼짐입니다. 세션 중 모델이 바뀌면 프롬프트 캐시가 깨지고 사람이 놀라니, 켜는 건 명시적으로 합니다(전역 설정 `"enforce": {"opencode": true}` / OpenClaw 플러그인 설정 `enforce: true`).

## 1분 설치

요구: Python 3, Codex/Claude 훅 병합용 `jq`, OpenCode/OpenClaw 플러그인용 Node.

```bash
git clone https://github.com/Jason-hub-star/effort-lanes.git
cd effort-lanes
bash install.sh                 # 감지된 모든 런타임, 코어만
bash install.sh --starter       # + 워크플로 스킬 10종
bash install.sh --runtimes claude,opencode --skills decision-sheet,evidence-audit
bash install.sh --dry-run
```

설치기는 공유 라우터를 `~/.config/effort-lanes/effort_router.py`에 한 벌 두고, 기존 훅을 건드리지 않고 자기 항목만 병합하며, 중복은 정확히 하나로 수렴시키고, 1회성 `*.effort-router.bak` 백업을 만들고, 설정 JSON이 깨져 있으면 쓰기 전에 멈춥니다. 설치 후 열린 세션은 재시작하세요.

다른 경로:

- **Claude Code 플러그인 마켓플레이스** — `/plugin marketplace add Jason-hub-star/effort-lanes` → `/plugin install effort-lanes@effort-lanes`
- **스킬만** — `npx skills add Jason-hub-star/effort-lanes --list`
- **OpenClaw** — `openclaw plugins install ./openclaw` (CLI가 있으면 설치기가 대신 실행)
- **Hermes** — 설치기가 플러그인을 복사하고 `hermes plugins enable effort-lanes`를 실행. 프로세스 분리를 원하면 `~/.hermes/config.yaml`에 `hooks.pre_llm_call` 셸 훅으로 같은 라우터를 걸면 됩니다.

## 설정

프로젝트에 `.effort-lanes.json`(작업 디렉터리에서 위로 올라가며 탐색) 또는 전역 `~/.config/effort-lanes/config.json`. 프로젝트 값이 이기고 키워드는 합쳐집니다. 모든 키가 선택이고 깨진 파일은 무시됩니다.

```json
{
  "floor": "deep",
  "keywords": { "critical": ["movej", "joint motion"] },
  "lanes": { "critical": { "opencode": "anthropic/claude-opus-5" } },
  "enforce": { "opencode": false }
}
```

`floor`는 오판이 비싼 레포(하드웨어·운영 인프라)용입니다. 예시는 [`router/config.example.json`](router/config.example.json).

## 워크플로 스킬 10종

```text
morning-brief → aim-before-build → decision-sheet? → converge-plan? → goal-contract? → phase-loop? → evidence-audit
                                   harness-audit ⇄ absorb   (정비 축: 세트를 작게 유지)
```

| 스킬 | 별칭 | 한 줄 |
|---|---|---|
| `aim-before-build` | 조준 | 코드 기준으로 이미 됨/부분/미착수/상충 판정. 안 만들어도 되는 걸 아는 게 제일 싼 결과 |
| `decision-sheet` | 그릴미 | 권장답을 미리 채운 질문 파일. 빈 답변 = 동의. Matt Pocock `grill-me`의 파일 왕복 변형 |
| `converge-plan` | 수렴 | 봉인 루브릭·적대적 반박·가장 싼 킬 실험 |
| `goal-contract` | 골 | 6요소 골 계약, 런타임 중립 |
| `phase-loop` | 페이즈루프 | phase 3개 이상을 게이트 통과로만 진행 |
| `evidence-audit` | 감사 | 증거만으로 공개 준비도 판정 |
| `harness-audit` | 정비 | 세션 로그로 스킬 회수율 측정. 死 = 호출 0 **그리고** 진입점 없음. 18개 상한(14개 레포 실측: ≤18은 33–83%, 26–27은 19–30% 회수) |
| `absorb` | 흡수 | 외부 소스를 이미 있음/보강/신규로 판정, 비채택 사유 기록 |
| `morning-brief` | 아침 | 어제 배턴과 다음 한 수 |
| `agent-starter` | — | 초심자에게 단계 하나만 지목 |

## 문서 게이트와 스캐폴드

적어둔 규약은 지켜지지 않고, 실패하는 스크립트는 지켜집니다. `scaffold/scripts/check-docs.sh`는 ① `docs/` 루트에 진입 문서 외 파일 ② 보관 이름 규칙(`<이름>-<사유>-<날짜>.<확장자>`)·인덱스 미등재 ③ Doc Sync Matrix의 source truth 경로 부재 ④ 스킬 18개 초과에서 실패합니다.

```bash
bash install.sh --scaffold ~/code/my-project   # docs/ 골격 + 게이트, 기존 파일은 안 건드림
bash scripts/check-docs.sh
```

이 레포도 CI에서 같은 게이트를 자기 자신에게 돌리며, 첫 실행에서 떠돌이 파일 하나를 잡았습니다.

## 검증

```bash
bash scripts/check.sh
```

프롬프트 32개(한/영)·두 셸 훅 계약·깨진 설정·floor·Node 플러그인 계약 2종·Hermes 플러그인·5런타임 설치기·문서 게이트 파손 테스트 10종을 덮습니다. 실런타임 증거와 기록으로 남긴 실패는 [docs/evidence/VALIDATION.md](docs/evidence/VALIDATION.md).

## 벤치마크

`bench/`는 같은 과제 15개·같은 모델에서 **노력 선택 방식 한 축만** 바꿔 잽니다. 조건 4개(라우터 없음·항상 high·조언·강제), 에이전트가 못 보는 숨은 검증, 실행 전에 적어둔 예측.

파일럿 1(2026-09-08, `opencode-go/gpt-5.6-luna`, 1회 반복 60런): critical 과제에서 `강제`가 `항상 high`와 같은 통과율(5/5)을 4% 싸게 냈고, 라우터 없음 대비 critical 미스 1건을 13% 비용으로 잡았어요. 반면 fast 과제에서는 이 프로바이더에서 라우터가 추론 토큰을 **아끼지 못하고 더 썼고**(46→153), 키워드 표가 짧은 영어 프롬프트 5/15를 놓쳤어요(오프라인 수정 후 15/15). 실패한 예측 둘이 코드와 로드맵을 바꿨어요 — [bench/results/pilot-1.md](bench/results/pilot-1.md).

## 포지셔닝

v0.2까지는 일부러 Codex+Claude 전용의 좁은 라우터였습니다. v0.3에서 훅이 실제로 강도를 바꿀 수 있는 자리를 실측한 뒤 크로스 런타임 하네스로 넓혔습니다. 비교와 배운 점은 [docs/research/COMPARISON.md](docs/research/COMPARISON.md). 유지하는 원칙: 분류기 파일 하나, 라우팅 경로에 LLM 없음, 자동 강제 없음, 모든 기능 주장은 기록된 실행으로 뒷받침.

## 안전

- 훅은 fail-open. 라우터는 사용자 텍스트를 실행하지 않고, 플러그인은 프롬프트를 셸이 아닌 프로세스 인자로 넘깁니다.
- 설치되는 파일은 전부 고정 자산이며 프롬프트로 생성되지 않습니다.
- OpenClaw·OpenCode 플러그인은 런타임과 같은 신뢰 수준으로 in-process 실행됩니다. 설치 전에 읽고, OpenClaw에서는 `plugins.allow`에 `effort-lanes`를 넣으세요.

MIT. [English README](README.md)
