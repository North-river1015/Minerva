import os
import json
import re
from pathlib import Path

# --- パスの設定 ---
# ウェブ公約のデータ (assign_ids.py で処理した後のデータ)
WEB_DATA_DIR = Path("output/finaldata")  # または output/finaldata
# 選挙公報のテキストデータ
BULLETIN_DATA_DIR = Path("data/ai_output/2026/shu")
BULLETIN_MANIFESTO_DIR = Path("output/manifesto")  # 公約抽出後のデータ
# 統合後のJSONを保存するフォルダ (Hugoが読み込む場所)
OUTPUT_DIR = Path("data/2026/shu")

def load_json(filepath):
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_json(filepath, data):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_bulletin_text(raw_text):
    """
    選挙公報のテキストを段落ごとに分け、
    header(見出し) と body(<br>区切りの本文) の辞書リストに変換する
    """
    blocks = []
    if not raw_text:
        return blocks

    paragraphs = raw_text.split("\n\n")
    for p in paragraphs:
        lines = p.strip().split("\n")
        if lines:
            header = lines[0] # 1行目を見出しとする
            body = "<br>".join(lines[1:]) if len(lines) > 1 else "" # 2行目以降を<br>でつなぐ
            blocks.append({
                "header": header,
                "body": body
            })
    return blocks

def merge_district_data(district, district_num):
    # ファイル名の作成 (例: tokyo-01)
    filename_base = f"{district}-{district_num:02d}"
    
    # データ読み込み
    web_data = load_json(WEB_DATA_DIR / f"{district}/{filename_base}-api.json")
    bulletin_data = load_json(BULLETIN_DATA_DIR / f"{district}/{filename_base}.json")
    
    # 【修正】公約抽出済みの選挙公報JSON（output/manifesto/tokyo/tokyo-01.json）を読み込む
    bulletin_manifesto_data = load_json(BULLETIN_MANIFESTO_DIR / f"{district}/{filename_base}.json")
    
    if not web_data or not bulletin_data:
        print(f"スキップ: {filename_base} の基本データ（WEBまたは公報テキスト）が揃っていません。")
        return

    # 統合先の枠組みを作成
    merged = {
        "district": web_data.get("district", ""),
        "district_code": f"2026-shu-{district}-{district_num}",
        "candidates": []
    }

    # web_data の候補者をベースに処理
    for web_candidate in web_data.get("candidates", []):
        cand_name = web_candidate.get("name")
        
        # bulletin_data（テキスト側）から同じ名前の候補者を探す
        bulletin_cand = next((c for c in bulletin_data.get("candidates", []) if c.get("name") == cand_name), {})
        
        # 選挙公報テキストの整形
        raw_text = bulletin_cand.get("full_text", "")
        formatted_blocks = format_bulletin_text(raw_text)

        # 【修正】抽出済み公報データ（bulletin_manifesto_data）から、この候補者の公約リストを探す
        extracted_manifestos = []
        if bulletin_manifesto_data:
            # 構造が「直下に manifesto キー」の場合
            if "manifesto" in bulletin_manifesto_data:
                extracted_manifestos = bulletin_manifesto_data.get("manifesto", [])
            # 構造が「candidates の中に各候補者ごとの manifesto」があるパターンの場合（安全のための分岐）
            elif "candidates" in bulletin_manifesto_data:
                m_cand = next((c for c in bulletin_manifesto_data.get("candidates", []) if c.get("name") == cand_name), {})
                extracted_manifestos = m_cand.get("manifesto", [])

        # 1人の候補者のデータを組み立てる
        merged_candidate = {
            "name": cand_name,
            "party": web_candidate.get("party", ""),
            "bulletin": {
                "full_text_blocks": formatted_blocks,
                # 【修正】正しく抽出された公約データをセットする
                "manifesto": extracted_manifestos 
            },
            "web": {
                # ウェブからの公約（policy_id付き）
                "manifesto": web_candidate.get("manifesto", []),
                # ウェブからの非公約（元のJSONに not_manifesto があれば取得）
                "not_manifesto": web_candidate.get("not_manifesto", [])
            }
        }
        merged["candidates"].append(merged_candidate)

    # 統合したデータを保存
    output_path = OUTPUT_DIR / f"{district}/{filename_base}.json"
    save_json(output_path, merged)
    print(f"保存完了: {output_path}")

if __name__ == "__main__":
    # 東京1区と2区を処理する (必要に応じて範囲を広げてください)
    district_list=["hokkaido","akita","aomori","chiba","fukushima","gunma","ibaraki","iwate","kanagawa","miyagi","saitama","tochigi","yamagata"]
    for district in district_list:
        for i in range(1, 31):
            merge_district_data(district,i)