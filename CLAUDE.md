# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

농작물 이미지에서 대표 색상을 추출하는 Python 데이터 처리 스크립트입니다. K-Means 클러스터링을 사용하여 이미지의 주요 색상을 HEX 코드로 변환합니다.

## Development Commands

### Environment Setup
```bash
# 가상환경 활성화 (반드시 먼저 실행)
source .venv/bin/activate

# Python 버전 확인
python --version  # Python 3.13.5 사용
```

### Script Execution
```bash
# 메인 스크립트 실행
python extract_crop_colors.py input.csv output.csv

# 예시: 기본 데이터 처리
python extract_crop_colors.py fm_staging.csv crop_colors.csv
```

### Data Verification
```bash
# 입력 데이터 확인
head -5 fm_staging.csv
wc -l fm_staging.csv  # 총 441개 농작물 데이터

# 출력 결과 확인
head -5 crop_colors.csv
tail -5 crop_colors.csv
```

## Architecture

### Core Components
- **extract_crop_colors.py**: 메인 처리 스크립트
  - `download_image()`: URL에서 이미지 다운로드 및 캐시 처리 (extract_crop_colors.py:34)
  - `dominant_color()`: K-Means 클러스터링으로 대표 색상 추출 (extract_crop_colors.py:49)
  - `main()`: CSV 배치 처리 및 결과 저장 (extract_crop_colors.py:67)

### Data Flow
```
fm_staging.csv (농작물명, 이미지 URL)
    ↓
이미지 다운로드 + 캐시 (.image_cache/)
    ↓
K-Means 클러스터링 색상 추출
    ↓
crop_colors.csv (농작물명, 이미지 URL, 대표색상)
```

### Dependencies
- **PIL (Pillow)**: 이미지 처리 및 RGB 변환
- **pandas**: CSV 데이터 입출력
- **scikit-learn**: K-Means 클러스터링 알고리즘
- **requests**: HTTP 이미지 다운로드
- **tqdm**: 진행률 표시

### Caching System
- `.image_cache/` 디렉토리에 이미지를 SHA256 해시로 캐시
- 중복 URL 처리 시 재다운로드 방지
- 캐시 파일명: `{sha256(url)}.img`

### Error Handling
- 이미지 다운로드 실패 시 경고 메시지 출력 후 계속 진행
- 처리 불가능한 이미지는 `dominant_color` 값을 `None`으로 설정
- 30초 HTTP 타임아웃 설정

## Data Format

### Input (fm_staging.csv)
```csv
crop_name,image_url
가지,https://static.farmmorning.com/crop/20230725/common_ic_eggplant.png
감,https://static.farmmorning.com/crop/20230725/common_ic_persimmon.png
```

### Output (crop_colors.csv)
```csv
crop_name,image_url,dominant_color
가지,https://static.farmmorning.com/crop/20230725/common_ic_eggplant.png,#000001
감,https://static.farmmorning.com/crop/20230725/common_ic_persimmon.png,#010100
```