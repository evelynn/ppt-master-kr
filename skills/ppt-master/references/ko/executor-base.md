# 역할: 실행자(Executor) 기본 규칙 — 한국어 오버레이

> 이 파일은 `references/executor-base.md`의 한국어 가이드 오버레이입니다.
> 상세 기술 사양(SVG 제약, 폰트 메트릭, 레이아웃 공식 등)은 원본 영문 문서를 함께 참조하고,
> 사용자에게 보여지는 메시지와 체크리스트는 **한국어**로 출력합니다.

## 핵심 책임

- 설계 사양(`design_spec.md`)에 따라 SVG 페이지를 **한 번에 한 페이지씩 순차 생성**합니다.
- 모든 페이지는 동일한 캔버스 뷰박스, 색상 체계, 폰트 계획을 공유합니다.
- 스피커 노트(`notes/total.md`)를 생성합니다.

## 디자인 파라미터 확인 (필수)

첫 번째 SVG를 생성하기 전에 다음을 출력하여 사양 준수를 확인합니다.

```markdown
## 🎨 디자인 파라미터 확인
- 캔버스 크기: <viewBox> (<width>x<height>)
- 색상 체계: Primary <hex> / Secondary <hex> / Accent <hex>
- 폰트 계획: 제목 <폰트> / 본문 <폰트>
- 본문 폰트 크기: <px>
```

## 생성 리듬 규칙

- ⚠️ **메인 에이전트 전용**: 페이지 SVG 생성을 서브 에이전트에 위임하지 않습니다.
- ⚠️ **페이지 배치 금지**: "5페이지씩"처럼 배치로 생성하지 않고, 한 페이지씩 연속 생성합니다.

## 체크포인트 출력 양식 (한국어)

각 페이지 생성 후 다음과 같이 표시합니다.
```markdown
📄 페이지 <N>/<총페이지수> 생성 완료: <파일명>.svg
```

모든 페이지 완료 후:
```markdown
## ✅ 실행자 단계 완료
- [x] 모든 SVG가 svg_output/에 생성됨
- [x] 스피커 노트가 notes/total.md에 생성됨
- [ ] 다음: Step 7 후처리로 자동 진행
```

## DESIGN.md 토큰과 컴포넌트 라이브러리 (DESIGN.md가 있을 때)

프로젝트 템플릿이 `DESIGN.md` (영문 사양 `references/design-md-spec.md`,
한국어 설명 `references/ko/design-md-spec.md`)를 가질 때, Executor는 hex
값을 직접 박지 않고 **디자인 토큰을 참조하는 SVG**를 생성해야 한다.
후처리 파이프라인이 finalize 단계에서 컴포넌트를 임베드하고 토큰을 해석한다.

### 토큰 참조 문법 (SVG 속성값)

| 토큰 | 용도 |
| ---- | ---- |
| `{colors.<name>}` | 색 (예: `fill="{colors.brand-1}"`) |
| `{typography.<name>.size}` | 폰트 크기 px |
| `{typography.<name>.weight}` | 폰트 굵기 |
| `{rounded.<name>}` | rx/ry 값 (예: `rx="{rounded.hero}"`) |
| `{spacing.<name>}` | 스페이싱 px |
| `{font.heading}` / `{font.body}` / `{font.code}` | font-family 스택 |

### 컴포넌트 임베드

`templates/components/`의 카드/뱃지/콜아웃을 재사용하려면 아이콘 임베드와
같은 `<use>` 패턴을 쓴다:

```xml
<use data-component="product-cards/coral"
     data-title="M2.7"
     data-subtitle="기초 모델"
     data-footer="200B · +18%"
     x="80" y="120" width="480" height="400"/>
```

후처리기가 컴포넌트 SVG 그룹으로 치환하고, 박스에 맞춰 스케일하며,
`data-<slot>` 값으로 슬롯 텍스트를 채운다. 사용 가능한 컴포넌트와 슬롯
목록은 `templates/components/components_index.json`에 있다.

### Do / Don't

매 프로젝트의 DESIGN.md `## Do's and Don'ts` 섹션을 먼저 읽는다. 공통:

- **Do**: 색은 `{colors.<token>}`로 참조 (hex 직접 사용 금지)
- **Do**: 한 역할에 한 사이즈 (커버 = `hero-display`, 슬라이드 제목 = `heading-lg`)
- **Do**: 카드/뱃지는 `<use data-component="...">`로 삽입
- **Don't**: 팔레트 외 색 도입 금지
- **Don't**: `<g opacity>` 금지 (PPT 호환성)
- **Don't**: `class=` 또는 `<style>` 금지 (SVG 제약)

차트 시리즈처럼 일회성 hex가 꼭 필요할 때만 슬라이드 상단에
`<!-- design-md:freehex -->` 주석을 두면 린터가 제외한다.

## SVG 기술 제약

SVG 기술 제약(금지 요소, 조건부 허용 규칙)은 **원본 영문 문서(`references/shared-standards.md`)의 사양을 정확히 따릅니다**.
번역 과정에서 제약 사양이 달라질 위험을 피하기 위해, 기술 제약은 원본 문서의 영문 용어를 그대로 사용합니다.

## 참조

- 원본 영문 기본 규칙: `references/executor-base.md`
- SVG 공유 제약: `references/shared-standards.md`
- 이미지 레이아웃: `references/image-layout-spec.md`
- 이미지 임베딩: `references/svg-image-embedding.md`
