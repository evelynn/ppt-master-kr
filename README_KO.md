# PPT Master — 어떤 문서든 네이티브 편집 가능한 PPTX로 자동 생성

[![Version](https://img.shields.io/badge/version-v2.3.0-blue.svg)](https://github.com/hugohe3/ppt-master/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](./README.md) | [中文](./README_CN.md) | 한국어

> PDF, DOCX, URL, Markdown 등 어떤 원본 문서도 드롭하면 **PowerPoint에서 바로 편집 가능한** 슬라이드(실제 도형·텍스트 상자·차트)로 변환됩니다. 이미지가 아닙니다 — 아무 요소나 클릭해서 수정할 수 있습니다.

---

## ✨ 왜 PPT Master인가?

- **진짜 PowerPoint** — 모든 요소가 직접 클릭·편집 가능한 네이티브 DrawingML 도형입니다.
- **투명하고 예측 가능한 비용** — 도구 자체는 무료/오픈소스. 본인이 쓰는 AI 에디터의 토큰 비용만 지불합니다(VS Code Copilot 기준 덱 1개당 약 $0.08).
- **데이터는 로컬에서 처리** — AI 모델 통신 외의 모든 파이프라인은 사용자의 머신에서 실행됩니다.
- **플랫폼 락인 없음** — Claude Code, Cursor, VS Code Copilot 등 다양한 에디터와 Claude, GPT, Gemini, Kimi 등 주요 모델을 지원합니다.

---

## 🌐 한국어 모드 사용법

PPT Master는 `skills/ppt-master/settings.json`에 **언어 설정**을 저장합니다. 한국어로 전환하면 모든 CLI 메시지와 AI 응답(추천안, 체크리스트, 진행 보고, 스피커 노트, 기능 설명 등)이 한국어로 제공됩니다.

```bash
# 한국어로 전환
python3 skills/ppt-master/scripts/settings.py set-language ko

# 영어로 전환
python3 skills/ppt-master/scripts/settings.py set-language en

# 시스템 로케일 자동 감지 (기본)
python3 skills/ppt-master/scripts/settings.py set-language auto

# 현재 설정 확인
python3 skills/ppt-master/scripts/settings.py show
```

환경 변수로 세션별 오버라이드도 가능합니다.

```bash
PPT_MASTER_LANG=ko python3 skills/ppt-master/scripts/project_manager.py init my_deck
```

> 📘 한국어 참조 문서: [`skills/ppt-master/references/ko/SKILL.md`](./skills/ppt-master/references/ko/SKILL.md)
> 📘 영어 원본 워크플로: [`skills/ppt-master/SKILL.md`](./skills/ppt-master/SKILL.md)

### 언어 설정 동작 방식

| 설정값 | 동작 |
|--------|------|
| `ko` | 모든 스크립트 출력과 AI 응답이 한국어. AI는 `references/ko/*.md` 오버레이를 우선 참조합니다. |
| `en` | 모든 출력이 영어. |
| `auto` | `PPT_MASTER_LANG` → 시스템 LANG/LC_ALL 순서로 자동 감지합니다. 사용자가 대화 중 특정 언어를 요구하면 즉시 해당 언어로 전환합니다. |

### 번역되지 않는 항목 (의도적)

- `design_spec.md`의 **섹션 제목·필드명**은 영문 원본을 유지합니다. 후속 스크립트(`finalize_svg.py`, `svg_to_pptx.py` 등)가 영문 식별자로 파싱하기 때문입니다. **값(values)** 은 한국어로 작성됩니다.
- SVG 기술 제약(금지 요소, 조건부 허용 규칙)은 정확도를 위해 영어 원본(`references/shared-standards.md`)을 그대로 참조합니다.

---

## 🚀 빠른 시작

```bash
# 1. 저장소 클론
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 한국어 모드 활성화(선택)
python3 skills/ppt-master/scripts/settings.py set-language ko

# 4. 프로젝트 초기화
python3 skills/ppt-master/scripts/project_manager.py init my_presentation --format ppt169
```

이후 Claude Code, Cursor, VS Code Copilot 등 AI 에디터에서 PPT 생성을 요청하면 워크플로가 자동으로 진행됩니다. 자세한 파이프라인은 [한국어 SKILL 문서](./skills/ppt-master/references/ko/SKILL.md)를 참고하세요.

---

## 🧭 파이프라인 요약

```
원본 문서 → 프로젝트 생성 → 템플릿 선택 → 전략가(Strategist)
          → [이미지 생성(Image_Generator)] → 실행자(Executor)
          → 후처리 → PPTX 내보내기
```

| 단계 | 주요 산출물 |
|------|-------------|
| 전략가 | `design_spec.md` (8개 확인 항목 + 콘텐츠 아웃라인) |
| 이미지 생성(조건부) | `images/image_prompts.md`, 실제 이미지 파일 |
| 실행자 | `svg_output/*.svg`, `notes/total.md` |
| 후처리 | `svg_final/*.svg`, `exports/<name>_<timestamp>.pptx` |

---

## 📚 추가 문서

- [한국어 SKILL.md](./skills/ppt-master/references/ko/SKILL.md)
- [한국어 참조 문서 안내](./skills/ppt-master/references/ko/README.md)
- [FAQ (영문)](./docs/faq.md)
- [왜 PPT Master인가 (영문)](./docs/why-ppt-master.md)
- [기술 설계 (영문)](./docs/technical-design.md)

## 📜 라이선스

MIT License — 자유롭게 사용·수정·배포할 수 있으며, 저작자 표시가 필요합니다.
