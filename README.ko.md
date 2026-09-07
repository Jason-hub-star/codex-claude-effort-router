# Codex + Claude 에포트 라우터

Codex와 Claude Code가 같은 결정 규칙을 쓰도록 만드는 작은 공개 하네스입니다. 프롬프트를 Fast, Daily, Deep, Critical 네 단계로 분류하고, 다음 세션용 Codex 프로필과 에이전트 정의를 함께 설치합니다. Codex 자동 위임 힌트는 현재 런타임에서 실제 확인된 내장 `explorer`, `worker`, `default`를 사용합니다.

중요한 한계가 있습니다. `UserPromptSubmit` 훅은 현재 부모 세션의 모델을 몰래 바꾸지 않습니다. 라우팅 문맥을 추가하고, 새 세션 프로필과 위임 대상을 알려주는 역할입니다.

## 설치

Python 3과 `jq`가 필요합니다.

```bash
git clone https://github.com/Jason-hub-star/codex-claude-effort-router.git
cd codex-claude-effort-router
bash install.sh
```

설치 후 실행 중인 Codex와 Claude Code 세션을 다시 시작해야 새 에이전트 정의가 보입니다. Codex 커스텀 TOML 역할의 실제 노출 여부는 클라이언트/런타임마다 달라, 포함된 정의는 선택 기능으로 취급합니다.

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

영문·한글 프롬프트 32종, 잘못된 JSON fail-open, 훅 보존, 중복 복구, 설치 멱등성을 검사합니다. 자세한 내용은 [검증 기록](evidence/VALIDATION.md)에 있습니다.

[English README](README.md) · [15초 홍보 영상](assets/effort-router-demo.mp4)
