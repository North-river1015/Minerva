import json
import re
from pathlib import Path

# パス設定
JSON_DIR = Path("data/ai_output/2026/shu/tokyo")
CONTENT_DIR = Path("content/2026/shu/prefectures/tokyo")

def update_md_with_json(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Checking: {json_file.name}")
    print(f"District Value: '{data.get('district')}'")

    district_num = re.search(r'\d+', data["district"]).group()
    winner = data["candidates"][0] # 当選者のみのJSONなので0番目を取得
    
    # 既存のmdファイルを探す (1.md)
    md_path = CONTENT_DIR / f"{district_num}.md"

    # Markdownの内容を構築
    # 前回のやり取りで提示された既存のフロントマター項目を保持・更新
    new_content = f"""---
title: "{data['district']}"
url: "/2026/shu/prefectures/tokyo/{district_num}/"
district_code: "2026-shu-tokyo-{district_num}"
candidate_name: "{winner['name']}"
party: "{winner['party']}"
pledge_ids: 
last_updated: "2026-03-16"
---



---

### 選挙公報での政策
{winner['full_text']}
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated: {md_path}")

# 東京のJSONファイルをすべて処理
for json_f in JSON_DIR.glob("*.json"):
    update_md_with_json(json_f)