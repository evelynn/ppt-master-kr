---
name: ppt-master (한국어)
description: >
  AI 기반 멀티 포맷 SVG 콘텐츠 생성 시스템. 원본 문서(PDF/DOCX/URL/Markdown)를
  다중 역할 협업을 통해 고품질 SVG 페이지로 변환하고 PPTX로 내보냅니다.
  사용자가 "PPT 만들어줘", "프레젠테이션 제작", "발표 자료 만들기" 등을 요청할 때 사용합니다.
---

# PPT Master Skill (한국어판)

> 이 문서는 영문 `SKILL.md`의 한국어 번역본입니다. 설정에서 언어가 `ko`로 지정되면
> 이 문서의 워크플로와 규칙을 따르고, 모든 사용자 응답 및 설명을 한국어로 제공합니다.

**핵심 파이프라인**: `원본 문서 → 프로젝트 생성 → 템플릿 선택 → 전략가(Strategist) → [이미지 생성(Image_Generator)] → 실행자(Executor) → 후처리 → 내보내기`

> [!CAUTION]
> ## 🚨 전역 실행 원칙 (필수 준수)
>
> **이 워크플로는 엄격한 직렬 파이프라인입니다. 아래 규칙은 최고 우선순위이며, 하나라도 위반하면 실행 실패로 간주합니다.**
>
> 1. **직렬 실행** — 단계는 순서대로 실행해야 하며, 각 단계의 산출물은 다음 단계의 입력이 됩니다. BLOCKING이 아닌 인접 단계는 전제 조건이 충족되면 사용자가 "계속"이라고 말하지 않아도 연속으로 진행할 수 있습니다.
> 2. **BLOCKING = 반드시 정지** — ⛔ BLOCKING으로 표시된 단계는 즉시 정지하고 사용자의 명시적인 응답을 기다려야 하며, 사용자를 대신해 결정해서는 안 됩니다.
> 3. **단계 교차 금지** — 여러 단계를 묶어서 한 번에 처리하는 것은 금지됩니다. (4단계의 8개 확인 항목은 ⛔ BLOCKING이므로 추천안을 제시하고 사용자의 명시적 확인을 기다려야 합니다. 확인 후에는 이후의 비-BLOCKING 단계 — 설계 사양 출력, SVG 생성, 스피커 노트, 후처리 — 가 사용자 추가 확인 없이 자동으로 진행됩니다.)
> 4. **진입 전 게이트 확인** — 각 Step 상단에 전제 조건(🚧 GATE)이 명시되어 있으며, 해당 Step을 시작하기 전에 반드시 검증해야 합니다.
> 5. **선행 실행 금지** — 이후 단계의 내용물을 "미리 준비"하는 것은 금지됩니다(예: 전략가 단계에서 SVG 코드를 작성).
> 6. **서브 에이전트 SVG 생성 금지** — Step 6의 SVG 생성은 컨텍스트 의존적이므로 현재 메인 에이전트가 처음부터 끝까지 수행해야 합니다. 페이지 SVG 생성을 서브 에이전트에 위임하는 것은 금지됩니다.
> 7. **순차 페이지 생성만 허용** — Step 6에서 전역 디자인 컨텍스트가 확정된 이후에는 SVG 페이지를 연속적인 하나의 흐름으로 한 페이지씩 순차 생성해야 합니다. 5페이지 단위 등 배치 생성은 금지됩니다.

> [!IMPORTANT]
> ## 🌐 언어 및 커뮤니케이션 규칙
>
> - **응답 언어 규칙**: `skills/ppt-master/settings.json`의 `language` 값이 `ko`이면 모든 응답(대화, 추천, 체크리스트, 설명, 스피커 노트 등)을 **한국어**로 작성합니다. `en`이면 영어로, `auto`이면 사용자의 입력 및 원본 자료 언어에 맞춰 응답합니다.
> - **명시적 재지정**: 사용자가 특정 언어를 명시적으로 요구하면(예: "영어로 답해줘") 그 언어를 우선합니다.
> - **템플릿 형식**: `design_spec.md` 파일은 대화 언어와 관계없이 원본 영문 템플릿 구조(섹션 제목, 필드명)를 유지해야 합니다. 템플릿 내부의 값은 사용자의 언어로 작성할 수 있습니다.

> [!IMPORTANT]
> ## 🔌 일반 코딩 스킬과의 호환성
>
> - `ppt-master`는 일반적인 애플리케이션 스캐폴드가 아니라 이 저장소 전용 워크플로 스킬입니다.
> - 기본적으로 `.worktrees/`, `tests/`, 브랜치 워크플로 등 일반적인 엔지니어링 구조를 요구하거나 생성하지 마세요.
> - 다른 일반 코딩 스킬이 이 워크플로와 충돌하는 저장소 관례를 제안한다면, 사용자가 명시적으로 다른 요구를 하지 않는 한 이 스킬을 우선 따릅니다.

## 메인 파이프라인 스크립트

| 스크립트 | 목적 |
|--------|------|
| `${SKILL_DIR}/scripts/source_to_md/pdf_to_md.py` | PDF → Markdown |
| `${SKILL_DIR}/scripts/source_to_md/doc_to_md.py` | 문서 → Markdown (Pandoc 이용 — DOCX/EPUB/HTML/LaTeX/RST 등) |
| `${SKILL_DIR}/scripts/source_to_md/ppt_to_md.py` | PowerPoint → Markdown |
| `${SKILL_DIR}/scripts/source_to_md/web_to_md.py` | 웹페이지 → Markdown |
| `${SKILL_DIR}/scripts/source_to_md/web_to_md.cjs` | WeChat/고보안 사이트 → Markdown |
| `${SKILL_DIR}/scripts/project_manager.py` | 프로젝트 초기화 / 검증 / 관리 |
| `${SKILL_DIR}/scripts/analyze_images.py` | 이미지 분석 |
| `${SKILL_DIR}/scripts/image_gen.py` | AI 이미지 생성(멀티 프로바이더) |
| `${SKILL_DIR}/scripts/svg_quality_checker.py` | SVG 품질 검사 |
| `${SKILL_DIR}/scripts/total_md_split.py` | 스피커 노트 분할 |
| `${SKILL_DIR}/scripts/finalize_svg.py` | SVG 후처리(통합 엔트리) |
| `${SKILL_DIR}/scripts/svg_to_pptx.py` | PPTX 내보내기 |
| `${SKILL_DIR}/scripts/settings.py` | 언어 등 전역 설정 관리 |

## 설정 및 언어 전환

```bash
# 현재 설정 보기
python3 ${SKILL_DIR}/scripts/settings.py show

# 한국어로 전환 (이후 모든 출력과 AI 응답이 한국어로 표시)
python3 ${SKILL_DIR}/scripts/settings.py set-language ko

# 영어로 전환
python3 ${SKILL_DIR}/scripts/settings.py set-language en

# 시스템 로케일을 따름
python3 ${SKILL_DIR}/scripts/settings.py set-language auto
```

## 워크플로

### Step 1: 원본 콘텐츠 처리

🚧 **GATE**: 사용자가 원본 자료(PDF / DOCX / EPUB / URL / Markdown 파일 / 텍스트 설명 / 대화 내용 — 어떤 형태든)를 제공함.

Markdown이 아닌 콘텐츠가 제공되면 즉시 변환합니다.

**✅ 체크포인트** — 원본 콘텐츠가 준비되었음을 확인한 뒤 Step 2로 진행합니다.

---

### Step 2: 프로젝트 초기화

🚧 **GATE**: Step 1 완료; 원본 콘텐츠 준비 완료.

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

포맷 옵션: `ppt169`(기본), `ppt43`, `xhs`, `story` 등.

> ⚠️ **반드시 `--move` 사용**: 모든 원본 파일은 `sources/`로 **이동**해야 합니다(복사가 아님).

**✅ 체크포인트** — 프로젝트 구조 생성 확인, Step 3로 진행.

---

### Step 3: 템플릿 선택

🚧 **GATE**: Step 2 완료; 프로젝트 디렉터리 준비 완료.

⛔ **BLOCKING**: 사용자가 템플릿 사용 여부를 아직 명확히 말하지 않은 경우, 선택지를 제시하고 **사용자의 명시적 응답을 기다려야** 합니다.

> 💡 **AI 추천**: 콘텐츠 주제(간단한 요약)를 바탕으로 **[특정 템플릿 / 자유 디자인]**을(를) 추천드립니다. 이유는 ... 입니다.
>
> - **A) 기존 템플릿 사용** — 검증된 "구조+스타일" 프리셋(템플릿 이름 또는 스타일 선호를 알려주세요)
> - **B) 자유 디자인(대부분의 경우 권장)** — AI가 콘텐츠에 맞게 구조와 스타일을 맞춤 설계합니다.

**✅ 체크포인트** — 사용자가 템플릿 선택을 응답함. Step 4로 진행.

---

### Step 4: 전략가(Strategist) 단계 (필수, 건너뛸 수 없음)

🚧 **GATE**: Step 3 완료; 사용자가 템플릿 선택을 확인함.

먼저 역할 정의를 읽습니다.
```
Read references/strategist.md  (한국어 환경에서는 references/ko/strategist.md 를 함께 참조)
```

**8개 확인 항목을 반드시 완료해야 합니다**(전체 템플릿 구조는 `templates/design_spec_reference.md`에 있음):

⛔ **BLOCKING**: 8개 확인 항목은 **하나의 추천 묶음**으로 사용자에게 제시해야 하며, **사용자의 확인/수정이 있을 때까지 설계 사양 및 콘텐츠 아웃라인을 출력해서는 안 됩니다**. 이는 워크플로의 핵심 확인 지점 두 개 중 하나입니다(다른 하나는 템플릿 선택). 확인 후에는 이후 스크립트 실행과 슬라이드 생성이 완전 자동으로 진행됩니다.

1. 캔버스 포맷
2. 페이지 수 범위
3. 대상 청중
4. 스타일 목표
5. 색상 체계
6. 아이콘 사용 방침
7. 타이포그래피 계획
8. 이미지 사용 방침

**산출물**: `<project_path>/design_spec.md`

**✅ 체크포인트** — 단계 산출물 완료, 다음 단계로 자동 진행.

---

### Step 5: 이미지 생성(Image_Generator) 단계 (조건부)

🚧 **GATE**: Step 4 완료; 설계 사양 및 콘텐츠 아웃라인 생성 및 확인됨.

> **발동 조건**: 이미지 방침에 "AI 생성"이 포함된 경우. 그렇지 않으면 Step 6로 건너뜁니다.

`references/image-generator.md` 를 읽습니다(한국어 환경에서는 `references/ko/image-generator.md` 참조).

```bash
python3 ${SKILL_DIR}/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
```

**✅ 체크포인트** — 모든 이미지 준비 완료 확인, Step 6로 진행.

---

### Step 6: 실행자(Executor) 단계

🚧 **GATE**: Step 4(및 해당 시 Step 5) 완료; 모든 선행 산출물 준비 완료.

선택된 스타일에 따라 역할 정의를 읽습니다.
```
Read references/executor-base.md            # 필수: 공통 가이드라인
Read references/executor-general.md         # 범용 유연 스타일
Read references/executor-consultant.md      # 컨설팅 스타일
Read references/executor-consultant-top.md  # 최상급 컨설팅 스타일(MBB급)
```

**디자인 파라미터 확인(필수)**: 첫 번째 SVG를 생성하기 전에 Executor는 설계 사양에서 주요 디자인 파라미터(캔버스 크기, 색상 체계, 폰트 계획, 본문 폰트 크기)를 검토·출력하여 사양 준수를 확인해야 합니다.

**시각 구성 단계**:
- SVG 페이지를 **한 번에 한 페이지씩** 연속적으로 순차 생성 → `<project_path>/svg_output/`

**논리 구성 단계**:
- 스피커 노트 생성 → `<project_path>/notes/total.md`

**✅ 체크포인트** — 모든 SVG와 스피커 노트 완성 확인, Step 7로 바로 진행.

---

### Step 7: 후처리 및 내보내기

🚧 **GATE**: Step 6 완료; 모든 SVG가 `svg_output/`에 생성됨; `notes/total.md` 생성됨.

> ⚠️ 아래 3개 하위 단계는 **반드시 하나씩 개별적으로 실행**해야 합니다. 각 명령이 정상 완료된 것을 확인한 다음 단계를 실행하세요.
> ❌ **절대** 세 명령을 한 코드 블록이나 단일 셸 호출로 묶지 마세요.

**Step 7.1** — 스피커 노트 분할:
```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Step 7.2** — SVG 후처리:
```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```

**Step 7.3** — PPTX 내보내기(스피커 노트 기본 포함):
```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> -s final
```

> ❌ `finalize_svg.py` 대신 `cp`를 사용하지 마세요 — 여러 핵심 처리 단계를 수행합니다.
> ❌ `svg_output/`에서 직접 내보내지 마세요 — 반드시 `-s final`을 사용해 `svg_final/`에서 내보내야 합니다.
> ❌ `--only` 같은 추가 플래그를 임의로 붙이지 마세요.

---

## 역할 전환 프로토콜

역할을 전환하기 전에 **반드시 해당 참조 파일을 먼저 읽어야** 합니다 — 건너뛰기는 금지입니다. 출력 표시:

```markdown
## [역할 전환: <역할 이름>]
📖 역할 정의 읽는 중: references/<파일명>.md
📋 현재 과제: <간단한 설명>
```

---

## 참고 리소스

| 리소스 | 경로 |
|--------|------|
| 공유 기술 제약 | `references/shared-standards.md` |
| 캔버스 포맷 사양 | `references/canvas-formats.md` |
| 이미지 레이아웃 사양 | `references/image-layout-spec.md` |
| SVG 이미지 임베딩 | `references/svg-image-embedding.md` |

---

## 참고 사항

- 후처리 명령에 `--only` 같은 추가 플래그를 임의로 붙이지 마세요.
- 로컬 미리보기: `python3 -m http.server -d <project_path>/svg_final 8000`
- **문제 해결**: 생성 중 문제가 발생하면(레이아웃 넘침, 내보내기 오류, 빈 이미지 등) `docs/faq.md`를 확인하도록 안내하세요.
