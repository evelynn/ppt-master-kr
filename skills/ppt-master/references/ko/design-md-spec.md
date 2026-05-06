# DESIGN.md 사양 (PPT Master, 한국어 오버레이)

> Google `@google/design.md` 형식을 PPT 슬라이드 덱에 맞춰 변형한 디자인 시스템
> 사양서. 영문 마스터: `references/design-md-spec.md`. 본 문서는 한국어 사용자를
> 위한 설명서이며, 실제 `DESIGN.md` 파일에서 사용하는 **섹션 헤딩과 필드 키는
> 영문 그대로** 유지해야 한다 (파서가 영문 헤딩을 기준으로 동작).

## 토큰 시스템을 도입하는 이유

40장짜리 PPT는 보통 색상 6개, 글자 크기 4단계, 카드 스타일 3종, 라운드 1~2단을
반복한다. 이를 매 슬라이드마다 hex로 박아두면

- **테마 교체**(리브랜드, 다크모드)가 슬라이드 단위 노가다가 되고,
- **샘플 PPT 임포트** 시 어떤 색이 브랜드 색인지 기록할 캐논이 없으며,
- **일관성 점검**("이 `#ff5733`이 진짜 브랜드 색인지 LLM 환각인지")이 불가능하다.

`DESIGN.md`에 토큰을 모으고 Executor가 `fill="{colors.brand-coral}"`처럼 토큰
참조를 쓰면

1. 테마 교체는 한 줄 수정
2. PPTX → DESIGN.md 임포트의 추출 타깃이 명확
3. "팔레트에 없는 hex 사용 금지" 린트 가능
4. 편집 UI의 컬러 피커 한 번 → LLM 호출 없이 전체 덱 즉시 리렌더

## 파일 위치

```
templates/
  layouts/<slug>/
    DESIGN.md         ← 디자인 시스템 (이 사양)
    design_spec.md    ← 프로젝트 단위 적용 (어떤 슬라이드에 어떤 토큰)
    01_cover.svg ... 04_ending.svg
  components/         ← 공유 SVG 컴포넌트 라이브러리
    components_index.json
    product-cards/, cards/, badges/, decorations/, callouts/, slide-frames/
```

`DESIGN.md`는 다음 11개 섹션을 **이 순서대로** 영문 헤딩으로 가져야 한다:

1. `## Overview` — 브랜드/덱 톤 서술
2. `## Colors` — 색 토큰 (Brand & Accent / Surface / Text / Semantic)
3. `## Typography` — 폰트 패밀리 + Hierarchy 표
4. `## Layout` — 캔버스/마진/그리드/스페이싱
5. `## Elevation & Depth` — 그림자/외곽선 단계
6. `## Shapes` — 라운드/외곽선 토큰
7. `## Components` — 컴포넌트 카탈로그
8. `## Slide Templates` — 페이지 단위 매크로
9. `## Do's and Don'ts` — Executor 가드레일
10. `## Canvas Variants` — 16:9 / 4:3 / A4 스케일링
11. `## Known Gaps` — 미정의 영역

신규 템플릿은 `templates/DESIGN.template.md`를 복사해서 시작.

## 토큰 참조 문법

| 토큰 | 해석 결과 |
| ---- | -------- |
| `{colors.<name>}` | hex 값, 예 `#FF4E3A` |
| `{typography.<name>}` | px 단위 폰트 크기 (`.size`/`.pt`/`.weight`/`.line_height` 하위 속성 가능) |
| `{spacing.<name>}` | px |
| `{rounded.<name>}` | px |
| `{elevation.<name>}` | `filter="url(#shadow-N)"` 형태 |
| `{font.heading}` / `{font.body}` / `{font.code}` | font-family 스택 |

### 컴포넌트 임베드

기존 아이콘 임베드 컨벤션(`<use data-icon=...>`)과 동일한 XML-valid 패턴을
사용한다:

```xml
<use data-component="product-cards/coral"
     data-title="M2.7"
     data-subtitle="기초 모델"
     x="80" y="120" width="480" height="400"
     fill="{colors.brand-coral}"/>
```

후처리 단계에서 `<use>` 요소가 컴포넌트 SVG 그룹으로 치환되며, 컴포넌트 내부의
토큰도 함께 해석된다.

### 슬라이드 템플릿 참조

```xml
<use data-slide-template="content_split_5_5" .../>
```

페이지 단위 매크로. 주로 편집 UI에서 신규 슬라이드를 추가할 때 사용한다.

## 후처리 파이프라인 순서

```
svg_output/*.svg
  ↓
1. component_embedder  ← <use data-component> → 컴포넌트 SVG 그룹 치환
  ↓
2. token_resolver      ← {colors.*}, {typography.*}, {rounded.*} 등 해석
  ↓
3. embed_icons         ← <use data-icon> → 아이콘 SVG 치환 (기존 단계)
  ↓
4. crop_images / fix_aspect / embed_images / flatten_text / fix_rounded
  ↓
svg_final/*.svg
```

## 검증

```bash
# DESIGN.md 자체 검사
python3 scripts/design_tokens.py validate templates/layouts/<slug>/DESIGN.md

# 슬라이드 SVG가 팔레트 외 hex를 쓰는지 린트
python3 scripts/design_tokens.py lint-svg <slide.svg> \
    --design templates/layouts/<slug>/DESIGN.md
```

`<!-- design-md:freehex -->` 주석을 SVG에 두면 해당 슬라이드는 린트에서 제외된다.

## design_spec.md 와의 관계

| 파일 | 단위 | 책임 |
| ---- | ---- | ---- |
| `templates/layouts/<slug>/DESIGN.md` | 템플릿 단위 | 토큰/컴포넌트 정의 |
| `projects/<name>/design_spec.md` | 프로젝트 단위 | 어떤 슬라이드에 어떤 토큰/컴포넌트를 어떻게 쓸지 |
| `projects/<name>/outline.yaml` | 프로젝트 단위 | 슬라이드/섹션 구조 + 변경 추적 |

Strategist는 `design_spec.md`에서 "이 덱은 `templates/layouts/minimax_demo/DESIGN.md`를
사용한다" 한 줄을 적고, 이후 슬라이드별 컨텐츠와 컴포넌트 선택만 기술한다. 색
hex를 직접 쓰지 않는다.
