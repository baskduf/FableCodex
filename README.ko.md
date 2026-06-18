<div align="center">
  <img width="280" height="280" alt="FableCodex" src="https://github.com/user-attachments/assets/7dd154af-f885-49ca-8d94-33756e340920" />

  <h1>FableCodex</h1>

  <p>
    <strong>Codex를 위한 증거 기반 워크플로 게이트.</strong>
  </p>

  <p>
    <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-Skill-black?style=for-the-badge" />
    <img alt="Claude Style" src="https://img.shields.io/badge/Claude--style-Guidance-D97745?style=for-the-badge" />
    <img alt="License AGPL-3.0-or-later" src="https://img.shields.io/badge/License-AGPL--3.0--or--later-blue?style=for-the-badge" />
    <a href="https://github.com/baskduf/FableCodex/actions/workflows/ci.yml">
      <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/baskduf/FableCodex/ci.yml?branch=main&label=CI&style=for-the-badge" />
    </a>
  </p>

  <p>
    <a href="README.md">English</a> |
    한국어 |
    <a href="README.ja.md">日本語</a> |
    <a href="README.zh-CN.md">简体中文</a> |
    <a href="README.zh-TW.md">繁體中文（台灣）</a>
  </p>
</div>

---

FableCodex는 Codex 작업에 Fable식 운영 습관을 더하는 Codex 플러그인입니다. 먼저 확인하고, 목표를 추적하고, 근거를 남기고, 리뷰 finding을 닫고, 완료를 말하기 전에 검증하도록 만듭니다.

작은 절차 비용보다 누락된 단계의 비용이 더 큰 작업에서 특히 유용합니다.

> FableCodex는 Fable 5 모델을 복제하거나 잠금 해제하거나 대체하지 않습니다.
> 모델 가중치, 컨텍스트 길이, 학습 내용, 숨겨진 안전 시스템을 바꾸지 못합니다.
> Codex에서 쓸 수 있는 워크플로 가이드, 로컬 ledger, 예제, coverage accounting, 선택적 routing 문서만 제공합니다.

## 빠른 시작

안정 버전을 설치합니다.

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.4.3
codex plugin add codex-fable5@fablecodex
```

Codex를 다시 시작한 뒤, 프롬프트에서 skill을 호출합니다.

```text
@codex-fable5 이 변경을 구현해.
작업이 여러 단계라면 goal ledger를 만들어.
최종 완료 전에 findings를 추적해.
완료했다고 말하기 전에 프로젝트 테스트를 실행해.
```

가볍게 쓰고 싶다면 이렇게 말합니다.

```text
@codex-fable5 빠르게 리뷰해.
goal ledger는 만들지 말고, 핵심 근거만 확인해서 actionable finding만 보고해.
```

## Codex에서 달라지는 점

`@codex-fable5`를 호출하면 Codex는 skill을 읽고 더 엄격한 절차를 적용합니다.

1. 행동하기 전에 작업을 분류합니다.
2. 워크스페이스, 파일, 도구, 인용된 출처를 먼저 확인합니다.
3. 기억에 의존하지 않고 Codex의 실제 도구를 사용합니다.
4. 긴 작업은 evidence checkpoint가 있는 goal로 추적합니다.
5. 리뷰 민감 작업은 finding을 기록하고 최종 findings gate를 요구합니다.
6. 테스트, lint, typecheck, screenshot, command output, source inspection, connector readback 등으로 검증합니다.
7. 무엇을 바꿨고, 무엇을 검증했고, 어떤 위험이 남았는지 보고합니다.

이 skill은 절차를 강화합니다. 모델 자체의 성능을 올리는 도구는 아닙니다.

## 언제 쓰면 좋은가

이럴 때 사용하세요.

- 여러 단계의 구현이나 리팩터링.
- 원인이 뚜렷하지 않은 디버깅.
- CI 실패, 릴리스 작업, 마이그레이션, 보안 민감 변경.
- unresolved finding이 최종 완료를 막아야 하는 리뷰.
- Claude/Fable식 프롬프트를 Codex-native 가이드로 바꾸는 작업.
- 이미 허가된 모델 접근 권한이 있는 상태에서 provider bridge를 설정하는 작업.

이럴 때는 굳이 쓰지 않아도 됩니다.

- 짧은 답변.
- 아주 작은 단일 파일 수정.
- 검증이 필요 없는 브레인스토밍.
- ledger 절차가 실제 작업보다 더 무거운 경우.

## 사용자가 제어하는 방법

사용자는 프롬프트로 이 skill을 제어합니다. 범위, 엄격함, 검증 기준, 중단 조건을 명확히 적는 것이 좋습니다.

엄격 모드:

```text
@codex-fable5 엄격하게 진행해.
goal ledger를 사용하고, 리뷰 finding을 기록하고, 테스트와 findings gate가 통과하기 전에는 끝났다고 하지 마.
```

분석만:

```text
@codex-fable5 분석만 해.
파일은 수정하지 말고, 파일/라인 근거가 있는 finding으로 보고해.
```

제한이 있는 구현:

```text
@codex-fable5 수정까지 구현해.
commit, push, branch 삭제는 하지 마.
unit test를 실행하고 남은 위험을 보고해.
```

디버깅:

```text
@codex-fable5 이 실패를 디버깅해.
먼저 재현하고, 여러 가설을 유지하고, 반증 근거를 모은 다음 수정하고 검증해.
```

## Goal Ledger

긴 작업에서는 helper가 `.codex-fable5/goals.json`에 로컬 상태를 저장합니다.

```bash
export PATH="$PWD/plugins/codex-fable5/bin:$PATH"

codex-fable5 goals create --brief "Migration" \
  --goal "inspect::현재 동작과 테스트 확인" \
  --goal "change::마이그레이션 구현" \
  --goal "verify::테스트를 실행하고 결과 확인"

codex-fable5 goals next
```

각 goal은 완료할 때 evidence가 필요합니다.

```bash
codex-fable5 goals checkpoint \
  --id G001 \
  --status complete \
  --evidence "importer.ts와 import.test.ts를 읽었고, 현재 parser가 따옴표 안의 쉼표를 거부하는 것을 확인했다."
```

마지막 goal은 검증 근거도 필요합니다.

```bash
codex-fable5 goals checkpoint \
  --id G003 \
  --status complete \
  --evidence "따옴표가 있는 CSV parsing을 구현하고 테스트를 업데이트했다." \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "모든 테스트가 통과했다."
```

## Findings Gate

Finding은 최종 완료 전에 잊으면 안 되는, 받아들인 리뷰 이슈입니다. `.codex-fable5/findings.json`에 저장됩니다.

```bash
codex-fable5 findings add \
  --title "최종 검증 누락" \
  --severity high \
  --source review \
  --location "plugins/codex-fable5/skills/codex-fable5/scripts/codex_goals.py" \
  --evidence "테스트 실행 증거가 없어도 final checkpoint가 완료될 수 있다."
```

수정과 검증이 끝난 뒤에만 finding을 resolve합니다.

```bash
codex-fable5 findings resolve \
  --id F001 \
  --evidence "이제 final checkpoint가 verification evidence를 요구한다." \
  --verify-cmd "python3 -m unittest discover -s tests -v" \
  --verify-evidence "회귀 테스트가 통과했다."
```

최종 완료 전에 gate를 실행합니다.

```bash
codex-fable5 findings gate
```

`open` 또는 `blocked` finding이 남아 있으면 gate는 실패합니다. 최종 goal completion도 blocking finding이 남아 있으면 실패합니다.

## 명령어 요약

| 명령어 | 용도 |
| --- | --- |
| `codex-fable5 status` | findings와 goal 진행 상태를 봅니다. |
| `codex-fable5 goals create` | 로컬 multi-step goal ledger를 만듭니다. |
| `codex-fable5 goals next` | 다음 goal을 시작하거나 재개합니다. |
| `codex-fable5 goals checkpoint` | goal을 evidence와 함께 complete, failed, blocked로 표시합니다. |
| `codex-fable5 findings add` | 근거가 있는 리뷰 finding을 기록합니다. |
| `codex-fable5 findings next` | 가장 우선순위가 높은 open finding을 보여줍니다. |
| `codex-fable5 findings resolve` | resolution과 verification evidence로 finding을 닫습니다. |
| `codex-fable5 findings gate` | open 또는 blocked finding이 남아 있으면 실패합니다. |

`PATH`를 바꾸지 않으려면 checkout helper를 직접 실행합니다.

```bash
plugins/codex-fable5/bin/codex-fable5 status
```

## 설치 옵션

안정 버전:

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.4.3
codex plugin add codex-fable5@fablecodex
```

개발 버전:

```bash
codex plugin marketplace add baskduf/FableCodex --ref main
codex plugin add codex-fable5@fablecodex
```

로컬 개발:

```bash
codex plugin marketplace add ~/Desktop/FableCodex
codex plugin add codex-fable5@fablecodex
```

플러그인을 설치하거나 업데이트한 뒤에는 Codex를 다시 시작하세요.

## 로컬 상태

FableCodex는 로컬 작업 상태를 `.codex-fable5/` 아래에 기록합니다.

- `goals.json`: 현재 goal plan과 evidence.
- `findings.json`: 리뷰 finding과 closeout evidence.
- `ledger.jsonl`: append-only 이벤트 기록.

이 파일들은 로컬 작업 상태입니다. 작업 transcript를 의도적으로 남기려는 경우가 아니라면 commit하지 마세요.

## Coverage Accounting

로컬에 `CLAUDE-FABLE-5.md` 사본이 있다면 source heading coverage를 확인할 수 있습니다.

```bash
python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py \
  --source /path/to/CLAUDE-FABLE-5.md
```

목표는 source heading 100% accounting입니다. 즉, 모든 source section에 대해 Codex-native 결정이 있어야 합니다: implemented, adapted, unsupported, not applicable. 이것은 모델 가중치나 숨겨진 Claude/Fable runtime parity를 뜻하지 않습니다.

## 선택적 Provider Bridge

모델 라우팅은 다음 문서를 보세요.

```text
plugins/codex-fable5/skills/codex-fable5/references/provider-bridge.md
```

유효한 Anthropic 접근 권한과 LiteLLM 같은 OpenAI-compatible gateway가 필요합니다. 이 저장소는 모델 접근 권한을 제공하지 않습니다.

## 테스트

stdlib-only 테스트를 실행합니다.

```bash
python3 -m unittest discover -s tests -v
```

## 출처 메모

이 프로젝트는 다음 자료에서 아이디어를 얻어 Codex-native 방식으로 재구성했습니다.

- `elder-plinius/CL4R1T4S` `ANTHROPIC/CLAUDE-FABLE-5.md` at commit `dc626fed52b06d687cdc812d51090c95ed03d575`.
- `fivetaku/fablize` at commit `15912466994e71a234d18fe9c74b46a68fb6a07d`.
- `itsinseong/value-for-fable` at commit `35a9bd27de961a49c343f41ac47c49114d51a328`.

원본 prompt나 문서를 재현하지 않고, workflow 아이디어를 요약하고 Codex에 맞게 바꿉니다.

## 인정

- FableCodex는 [sickn33/antigravity-awesome-skills#686](https://github.com/sickn33/antigravity-awesome-skills/pull/686)에 listed되었습니다.

## 라이선스

AGPL-3.0-or-later. `LICENSE`, `NOTICE`, `plugins/codex-fable5/skills/codex-fable5/references/provenance.md`를 참고하세요.
