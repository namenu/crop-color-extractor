#!/usr/bin/env python3
"""
HSV 색공간 기반 농작물 이미지 색상 추출기

주요 개선사항:
1. HSV 색공간에서 클러스터링 (색조 기준)
2. 밝기 변화에 덜 민감한 색상 추출
3. 색상 계열별 그룹핑

Usage:
    python extract_crop_colors_hsv.py input.csv output.csv
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
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
    return img

def rgb_to_hsv_array(rgb_array):
    """RGB 배열을 HSV로 변환"""
    hsv_array = np.zeros_like(rgb_array, dtype=np.float32)
    for i in range(len(rgb_array)):
        r, g, b = rgb_array[i] / 255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        hsv_array[i] = [h * 360, s * 100, v * 100]  # H(0-360), S(0-100), V(0-100)
    return hsv_array

def hsv_to_rgb(h, s, v):
    """HSV를 RGB로 변환"""
    r, g, b = colorsys.hsv_to_rgb(h/360.0, s/100.0, v/100.0)
    return int(r*255), int(g*255), int(b*255)

def is_extreme_color(r, g, b, threshold=20):
    """극단적인 색상(너무 어둡거나 밝은 색상) 판별"""
    if r < threshold and g < threshold and b < threshold:
        return True
    if r > (255-threshold) and g > (255-threshold) and b > (255-threshold):
        return True
    return False

def dominant_color_hsv(img: Image.Image, k=5, resize=(150, 150)) -> str:
    """HSV 색공간 기반 대표 색상 추출"""
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
    
    if len(filtered_pixels) < len(pixels) * 0.1:
        filtered_pixels = pixels
    else:
        filtered_pixels = np.array(filtered_pixels)
    
    # RGB를 HSV로 변환
    hsv_pixels = rgb_to_hsv_array(filtered_pixels)
    
    # 채도가 너무 낮은 픽셀 제거 (회색 계열)
    high_saturation_mask = hsv_pixels[:, 1] > 15  # 채도 15% 이상
    if high_saturation_mask.sum() > len(hsv_pixels) * 0.1:
        hsv_pixels = hsv_pixels[high_saturation_mask]
        filtered_pixels = filtered_pixels[high_saturation_mask]
    
    if len(hsv_pixels) == 0:
        # 폴백: 원본 데이터 사용
        hsv_pixels = rgb_to_hsv_array(pixels)
        filtered_pixels = pixels
    
    # HSV 공간에서 K-Means 클러스터링 (H와 S에 가중치)
    # Hue는 순환적이므로 sin/cos 변환
    h_rad = np.radians(hsv_pixels[:, 0])
    clustering_features = np.column_stack([
        np.cos(h_rad) * 2,  # Hue cosine (가중치 2)
        np.sin(h_rad) * 2,  # Hue sine (가중치 2) 
        hsv_pixels[:, 1] / 50,  # Saturation (0-2 range)
        hsv_pixels[:, 2] / 100  # Value (0-1 range)
    ])
    
    # K-Means 클러스터링
    n_clusters = min(k, len(hsv_pixels))
    kmeans = KMeans(n_clusters=n_clusters, n_init="auto", random_state=0)
    labels = kmeans.fit_predict(clustering_features)
    
    # 각 클러스터 분석
    cluster_info = []
    unique_labels, counts = np.unique(labels, return_counts=True)
    
    for label, count in zip(unique_labels, counts):
        cluster_hsv = hsv_pixels[labels == label]
        cluster_rgb = filtered_pixels[labels == label]
        
        # 클러스터의 평균 HSV 값
        avg_h = np.degrees(np.arctan2(
            np.mean(np.sin(np.radians(cluster_hsv[:, 0]))),
            np.mean(np.cos(np.radians(cluster_hsv[:, 0])))
        )) % 360
        avg_s = np.mean(cluster_hsv[:, 1])
        avg_v = np.mean(cluster_hsv[:, 2])
        
        # RGB 변환
        r, g, b = hsv_to_rgb(avg_h, avg_s, avg_v)
        
        # 점수 계산: 크기 + 채도 가중치
        score = count * (1 + avg_s / 50)  # 채도가 높을수록 점수 증가
        
        cluster_info.append({
            'color': (r, g, b),
            'count': count,
            'saturation': avg_s,
            'value': avg_v,
            'hue': avg_h,
            'score': score
        })
    
    # 점수가 가장 높은 클러스터 선택
    best_cluster = max(cluster_info, key=lambda x: x['score'])
    r, g, b = best_cluster['color']
    
    return f"#{r:02x}{g:02x}{b:02x}"

def main(input_path: str, output_path: str):
    df = pd.read_csv(input_path)
    unique_urls = df["image_url"].dropna().unique()

    url_to_color = {}
    for url in tqdm(unique_urls, desc="Processing images (HSV)"):
        try:
            img = download_image(url)
            url_to_color[url] = dominant_color_hsv(img)
        except Exception as e:
            print(f"[WARN] {url} 처리 실패: {e}")
            url_to_color[url] = None

    df["dominant_color"] = df["image_url"].map(url_to_color)
    df.to_csv(output_path, index=False)
    print(f"완료! 결과 저장: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_crop_colors_hsv.py input.csv output.csv")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])