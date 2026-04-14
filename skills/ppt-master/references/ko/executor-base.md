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

## SVG 기술 제약

SVG 기술 제약(금지 요소, 조건부 허용 규칙)은 **원본 영문 문서(`references/shared-standards.md`)의 사양을 정확히 따릅니다**.
번역 과정에서 제약 사양이 달라질 위험을 피하기 위해, 기술 제약은 원본 문서의 영문 용어를 그대로 사용합니다.

## 참조

- 원본 영문 기본 규칙: `references/executor-base.md`
- SVG 공유 제약: `references/shared-standards.md`
- 이미지 레이아웃: `references/image-layout-spec.md`
- 이미지 임베딩: `references/svg-image-embedding.md`
