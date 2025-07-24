# 농작물 이미지 색상 추출기

농작물 이미지에서 대표 색상을 추출하는 Python 프로젝트입니다. K-Means 클러스터링을 사용하여 이미지의 주요 색상을 HEX 코드로 변환합니다.

## 특징

- **HSV 색공간 기반**: 색조(Hue) 중심 클러스터링으로 그라데이션에 강함
- **투명 영역 처리**: RGBA 이미지의 투명 배경을 적절히 처리
- **극단 색상 필터링**: 순백/순흑 픽셀 제거로 정확한 색상 추출
- **이미지 캐시**: 중복 다운로드 방지로 빠른 처리
- **HTML 뷰어**: 추출된 색상을 시각적으로 확인 가능

## 설치 및 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# 기본 색상 추출 (HSV 방식 권장)
python extract_crop_colors_hsv.py fm_staging.csv crop_colors.csv

# HTML 뷰어 생성
python generate_color_viewer.py crop_colors.csv color_viewer.html
```

## 파일 구조

- `extract_crop_colors_hsv.py`: HSV 색공간 기반 색상 추출기 (권장)
- `extract_crop_colors_improved.py`: RGB 개선 버전
- `extract_crop_colors.py`: 원본 버전
- `generate_color_viewer.py`: HTML 뷰어 생성기
- `fm_staging.csv`: 입력 데이터 (농작물명, 이미지 URL)

## 알고리즘 비교

| 방식 | 고구마 | 감귤 | 특징 |
|------|--------|------|------|
| 기존 | `#010000` (검은색) | `#010100` (검은색) | 투명 영역 문제 |
| RGB 개선 | `#ffad4e` (주황색) | `#fc8532` (주황색) | 투명 처리 개선 |
| **HSV** | `#a8297f` (보라색) | `#fa8138` (주황색) | **그라데이션 대응** |

## 주요 개선사항

### HSV 색공간 방식
1. **색조 중심 클러스터링**: 밝기 변화에 덜 민감
2. **채도 필터링**: 회색 계열 픽셀 제거
3. **순환적 Hue 처리**: 비슷한 색조 자동 그룹핑

### 데이터 처리
- 442개 농작물 데이터 처리
- 56개 고유 이미지 URL
- 자동 캐싱으로 빠른 재처리