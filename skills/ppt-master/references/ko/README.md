# PPT Master — 한국어 참조 문서

이 디렉터리는 `references/`의 주요 역할 정의 파일의 한국어 오버레이를 담고 있습니다.
`settings.json`의 `language`가 `ko`일 때 PPT Master는 다음 순서로 문서를 참조합니다.

1. `references/ko/<filename>.md` — 한국어 오버레이(사용자 커뮤니케이션, 체크리스트, 요약 지침)
2. `references/<filename>.md` — 원본 영문 기술 사양(SVG 제약, 필드 구조 등 정확도 중요 섹션)

## 제공 파일

| 파일 | 내용 |
|------|------|
| `SKILL.md` | 메인 워크플로 한국어판 |
| `strategist.md` | 전략가 역할 한국어 오버레이 |
| `executor-base.md` | 실행자 공통 규칙 한국어 오버레이 |
| `image-generator.md` | 이미지 생성기 한국어 오버레이 |

## 번역되지 않는 항목 (의도적)

- `design_spec.md` 템플릿의 **섹션 제목 및 필드명** — 후속 스크립트가 영문 식별자로 파싱하므로 원본 유지.
- SVG 금지 요소/패턴 목록 — 정확도를 위해 원본 영문 문서(`references/shared-standards.md`)를 그대로 참조.
- 역할 전환 헤더의 영문 태그(예: "BLOCKING", "GATE") — 파이프라인 식별용 키워드로 보존.

## 한국어 전환 명령

```bash
python3 skills/ppt-master/scripts/settings.py set-language ko
```

설정이 저장되면 이후 모든 PPT Master 스크립트 출력과 AI 응답이 한국어로 제공됩니다.
