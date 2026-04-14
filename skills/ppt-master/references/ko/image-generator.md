# 역할: 이미지 생성기(Image_Generator) — 한국어 오버레이

> 이 파일은 `references/image-generator.md`의 한국어 가이드 오버레이입니다.
> 프롬프트 작성법, 프로바이더 매트릭스 등 상세 기술 내용은 원본 영문 문서를 함께 참조합니다.
> 사용자에게 노출되는 메시지와 진행 보고는 **한국어**로 작성합니다.

## 트리거 조건

- 설계 사양의 이미지 방침에 "AI 생성"이 포함된 경우 본 단계가 활성화됩니다.
- 그 외(사용자 제공 이미지만 사용 / 이미지 미사용)에는 Step 6 실행자 단계로 바로 진행합니다.

## 산출물

1. `<project_path>/images/image_prompts.md` — 각 이미지의 프롬프트 정의 문서.
2. `<project_path>/images/*.{jpg,png}` — 실제 생성된 이미지 파일.

## 실행 절차

1. 설계 사양에서 "생성 대기(pending generation)" 상태의 모든 이미지를 추출합니다.
2. 각 이미지의 프롬프트를 영문 기준으로 작성하되 **한국어 주석/설명을 병기**합니다.
3. 다음 CLI로 이미지를 생성합니다.
   ```bash
   python3 ${SKILL_DIR}/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
   ```

## 사용자 보고 양식 (한국어)

```markdown
## ✅ 이미지 생성 단계 완료
- [x] 프롬프트 문서 작성됨
- [x] 모든 이미지가 images/ 에 저장됨
```

## 참조

원본 영문 역할 정의: `references/image-generator.md`
