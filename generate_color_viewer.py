#!/usr/bin/env python3
"""
농작물 색상 뷰어 HTML 생성기

Usage:
    python generate_color_viewer.py crop_colors.csv color_viewer.html
"""

import sys
import json
import pandas as pd

def generate_html(csv_file, output_file):
    # CSV 데이터 로드
    df = pd.read_csv(csv_file)
    
    # JavaScript 배열로 변환
    crop_data = []
    for _, row in df.iterrows():
        crop_data.append({
            'crop_name': row['crop_name'],
            'image_url': row['image_url'], 
            'dominant_color': row['dominant_color']
        })
    
    # JSON 문자열로 변환
    crop_data_json = json.dumps(crop_data, ensure_ascii=False, indent=8)
    
    html_template = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>농작물 대표 색상 뷰어</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }}
        .search-box {{
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-bottom: 20px;
            box-sizing: border-box;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .crop-card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.2s ease;
        }}
        .crop-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        .color-bar {{
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            font-size: 18px;
        }}
        .crop-info {{
            padding: 16px;
        }}
        .crop-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }}
        .crop-image {{
            width: 40px;
            height: 40px;
            object-fit: contain;
            border-radius: 6px;
            background: #f8f8f8;
            padding: 4px;
        }}
        .crop-name {{
            font-size: 18px;
            font-weight: 600;
            color: #333;
            flex: 1;
        }}
        .color-code {{
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            color: #666;
            background: #f8f8f8;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 8px;
        }}
        .image-link {{
            font-size: 12px;
            color: #888;
            text-decoration: none;
            word-break: break-all;
            line-height: 1.4;
        }}
        .image-link:hover {{
            color: #0066cc;
        }}
        .stats {{
            text-align: center;
            margin-bottom: 20px;
            color: #666;
        }}
        .no-results {{
            text-align: center;
            color: #666;
            font-size: 18px;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌾 농작물 대표 색상 뷰어</h1>
        
        <input type="text" class="search-box" id="searchInput" placeholder="농작물명으로 검색...">
        
        <div class="stats" id="stats"></div>
        
        <div class="grid" id="cropGrid"></div>
        
        <div class="no-results" id="noResults" style="display: none;">
            검색 결과가 없습니다.
        </div>
    </div>

    <script>
        // 임베드된 데이터
        const cropData = {crop_data_json};
        
        // 색상의 밝기를 계산하는 함수 (텍스트 색상 결정용)
        function getTextColor(hexColor) {{
            const r = parseInt(hexColor.substr(1, 2), 16);
            const g = parseInt(hexColor.substr(3, 2), 16);
            const b = parseInt(hexColor.substr(5, 2), 16);
            const brightness = (r * 299 + g * 587 + b * 114) / 1000;
            return brightness > 128 ? '#000000' : '#ffffff';
        }}
        
        // 농작물 카드를 생성하는 함수
        function createCropCard(crop) {{
            const textColor = getTextColor(crop.dominant_color);
            
            return `
                <div class="crop-card">
                    <div class="color-bar" style="background-color: ${{crop.dominant_color}}; color: ${{textColor}};">
                        ${{crop.dominant_color}}
                    </div>
                    <div class="crop-info">
                        <div class="crop-header">
                            <img src="${{crop.image_url}}" alt="${{crop.crop_name}}" class="crop-image" loading="lazy">
                            <div class="crop-name">${{crop.crop_name}}</div>
                        </div>
                        <div class="color-code">${{crop.dominant_color}}</div>
                        <a href="${{crop.image_url}}" target="_blank" class="image-link">
                            ${{crop.image_url}}
                        </a>
                    </div>
                </div>
            `;
        }}
        
        // 그리드를 렌더링하는 함수
        function renderGrid(data) {{
            const grid = document.getElementById('cropGrid');
            const noResults = document.getElementById('noResults');
            
            if (data.length === 0) {{
                grid.style.display = 'none';
                noResults.style.display = 'block';
            }} else {{
                grid.style.display = 'grid';
                noResults.style.display = 'none';
                grid.innerHTML = data.map(createCropCard).join('');
            }}
            
            // 통계 업데이트
            document.getElementById('stats').textContent = `총 ${{data.length}}개의 농작물`;
        }}
        
        // 검색 기능
        function filterCrops(searchTerm) {{
            const filtered = cropData.filter(crop => 
                crop.crop_name.toLowerCase().includes(searchTerm.toLowerCase())
            );
            renderGrid(filtered);
        }}
        
        // 초기 렌더링
        renderGrid(cropData);
        
        // 검색 이벤트 리스너
        document.getElementById('searchInput').addEventListener('input', (e) => {{
            filterCrops(e.target.value);
        }});
    </script>
</body>
</html>'''
    
    # HTML 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"HTML 뷰어 생성 완료: {output_file}")
    print(f"총 {len(crop_data)}개의 농작물 데이터 포함")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_color_viewer.py input.csv output.html")
        sys.exit(1)
    
    generate_html(sys.argv[1], sys.argv[2])