#!/usr/bin/env python3
"""
Usage:
    python extract_crop_colors.py input.csv output.csv

input.csv  : 원본 (crop_name,image_url)
output.csv : 대표 색상 추가된 결과

예)
    python extract_crop_colors.py fm_staging.csv crop_colors.csv
"""

import sys
import os
import hashlib
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
import numpy as np
from sklearn.cluster import KMeans
from tqdm import tqdm

CACHE_DIR = ".image_cache"

def ensure_cache():
    if not os.path.isdir(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def filename_for_url(url: str) -> str:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, h + ".img")

def download_image(url: str) -> Image.Image:
    """다운로드 후 캐시에 저장/재사용."""
    ensure_cache()
    path = filename_for_url(url)
    if not os.path.exists(path):
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        with open(path, "wb") as f:
            f.write(resp.content)
    with open(path, "rb") as f:
        img = Image.open(BytesIO(f.read()))
        # GIF 등 팔레트 이미지를 일관되게 처리하기 위해 RGB 변환
        img = img.convert("RGB")
    return img

def dominant_color(img: Image.Image, k=4, resize=(120, 120)) -> str:
    """K-Means 기반 대표 색상 HEX 반환."""
    # 연산량 절감을 위해 리사이즈
    img_small = img.resize(resize)
    arr = np.asarray(img_small, dtype=np.uint8)
    pixels = arr.reshape(-1, 3)

    # 완전한 검정/흰색이 너무 많으면 배경일 수 있으므로 약간 샘플 필터링 (선택사항)
    # 여기서는 간단히 그대로 사용
    kmeans = KMeans(n_clusters=k, n_init="auto", random_state=0)
    labels = kmeans.fit_predict(pixels)
    # 가장 큰 클러스터 선택
    _, counts = np.unique(labels, return_counts=True)
    dominant_idx = counts.argmax()
    color = kmeans.cluster_centers_[dominant_idx]
    r, g, b = [int(round(c)) for c in color]
    return f"#{r:02x}{g:02x}{b:02x}"

def main(input_path: str, output_path: str):
    df = pd.read_csv(input_path)
    # 고유 URL만 처리
    unique_urls = df["image_url"].dropna().unique()

    url_to_color = {}
    for url in tqdm(unique_urls, desc="Processing images"):
        try:
            img = download_image(url)
            url_to_color[url] = dominant_color(img)
        except Exception as e:
            print(f"[WARN] {url} 처리 실패: {e}")
            url_to_color[url] = None

    df["dominant_color"] = df["image_url"].map(url_to_color)
    df.to_csv(output_path, index=False)
    print(f"완료! 결과 저장: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_crop_colors.py input.csv output.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
    