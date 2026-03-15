import json
from pathlib import Path



４６８１０、１４、１６、２０、２６、ミス


# --- 設定 ---
JSON_INPUT_DIR = Path("data/ai_output/2026/shu/tokyo")
TARGET_DIR = Path("/Users/home/Minerva-1/content/2026/shu/prefectures/tokyo/tokyo-district")

def update_tokyo_districts():
    # 保存先フォルダを確保
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # JSONファイルを一つずつ処理
    for json_path in JSON_INPUT_DIR.glob("*.json"):
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"❌ 解析エラー: {json_path}")
                continue


        district_name = data.get("district") 
        
        # ✅ 追加：もし district_name が空（None）なら、そのファイルをスキップする
        if district_name is None:
            print(f"⚠️ スキップ: 'district' 項目が見つかりません ({json_path.name})")
            continue

        candidates = data.get("candidates", [])
        
        # 数字の抽出（ここでのエラーを防げます）
        dist_num = "".join(filter(str.isdigit, district_name))

        md_file = TARGET_DIR / f"{dist_num}.md"

        # --- フロントマターの構築 ---
        # 政党のみをTaxonomyとして抽出
        all_parties = sorted(list(set(c['party'] for c in candidates)))

        lines = [
            "---",
            f'title: "{district_name}"',
            f'date: 2026-03-13',
            f'parties: {json.dumps(all_parties, ensure_ascii=False)}',
            f'url: "/2026/shu/prefectures/tokyo/{dist_num}/"',
            "---",
            f"\n# {district_name} 候補者一覧\n"
        ]

        # --- 候補者ごとの本文流し込み ---
        for c in candidates:
            lines.append(f"## {c['name']}（{c['party']}）")
            lines.append("\n### 選挙公報全文")
            # 信頼できないPledgeは飛ばし、全文（full_text）のみを配置
            lines.append(f"{c['full_text']}")
            lines.append("\n---\n")

        # 上書き保存
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"✅ 更新完了: {md_file.name}")

if __name__ == "__main__":
    update_tokyo_districts()