#!/usr/bin/env python3
"""
개선된 농작물 이미지 색상 추출기

주요 개선사항:
1. 투명 영역 제거 (RGBA → RGB 변환 시 흰색 배경 합성)
2. 극단적 색상 (순백/순흑) 필터링
3. 색상 클러스터 중 가장 채도가 높은 색상 선택
4. 더 정확한 대표 색상 추출

Usage:
    python extract_crop_colors_improved.py input.csv output.csv
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
import colorsys

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
        
        # RGBA 이미지의 경우 투명 영역을 흰색 배경과 합성
        if img.mode == 'RGBA':
            # 흰색 배경 생성
            background = Image.new('RGB', img.size, (255, 255, 255))
            # 알파 채널을 마스크로 사용하여 합성
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
    return img

def rgb_to_hsv(r, g, b):
    """RGB를 HSV로 변환"""
    return colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)

def is_extreme_color(r, g, b, threshold=20):
    """극단적인 색상(너무 어둡거나 밝은 색상) 판별"""
    # 너무 어두운 색상
    if r < threshold and g < threshold and b < threshold:
        return True
    # 너무 밝은 색상  
    if r > (255-threshold) and g > (255-threshold) and b > (255-threshold):
        return True
    return False

def get_color_saturation(r, g, b):
    """색상의 채도 계산"""
    h, s, v = rgb_to_hsv(r, g, b)
    return s

def dominant_color(img: Image.Image, k=5, resize=(150, 150)) -> str:
    """개선된 대표 색상 추출 알고리즘"""
    # 연산량 절감을 위해 리사이즈
    img_small = img.resize(resize)
    arr = np.asarray(img_small, dtype=np.uint8)
    pixels = arr.reshape(-1, 3)
    
    # 극단적인 색상 필터링
    filtered_pixels = []
    for pixel in pixels:
        r, g, b = pixel
        if not is_extreme_color(r, g, b):
            filtered_pixels.append(pixel)
    
    # 필터링된 픽셀이 너무 적으면 원본 사용
    if len(filtered_pixels) < len(pixels) * 0.1:
        filtered_pixels = pixels
    else:
        filtered_pixels = np.array(filtered_pixels)
    
    # K-Means 클러스터링
    kmeans = KMeans(n_clusters=min(k, len(filtered_pixels)), n_init="auto", random_state=0)
    labels = kmeans.fit_predict(filtered_pixels)
    
    # 각 클러스터의 크기와 채도 계산
    cluster_info = []
    unique_labels, counts = np.unique(labels, return_counts=True)
    
    for i, (label, count) in enumerate(zip(unique_labels, counts)):
        color = kmeans.cluster_centers_[label]
        r, g, b = [int(round(c)) for c in color]
        saturation = get_color_saturation(r, g, b)
        
        cluster_info.append({
            'color': (r, g, b),
            'count': count,
            'saturation': saturation,
            'score': count * (1 + saturation * 2)  # 크기 + 채도 가중치
        })
    
    # 점수가 가장 높은 색상 선택
    best_cluster = max(cluster_info, key=lambda x: x['score'])
    r, g, b = best_cluster['color']
    
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
        print("Usage: python extract_crop_colors_improved.py input.csv output.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])