import os
import json
import time
import re
import requests
from pathlib import Path
from dotenv import load_dotenv 
from openrouter import OpenRouter

#manifestoにprefつけたので反映が必要かもしれない

# 環境変数の読み込み
load_dotenv()
api_key_openrouter = os.environ.get('OPENROUTER')
url = os.environ.get('URL')

# 基本パスの設定
BASE_INPUT_DIR = "output/manifesto/"  # 読み込み・書き込み元のルート
OUTPUT_DIR = "data/"
POLICIES_FILE = os.path.join(OUTPUT_DIR, "policies.json") # マスタデータ

def load_json(filepath):
    """JSONファイルを読み込む"""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    """JSONファイルを保存する"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def safe_generate_content(model, contents):
    """OpenRouter経由で安全にテキストを生成する"""
    full_text = "\n\n".join(str(c) for c in contents)

    try:
        with OpenRouter(api_key=api_key_openrouter) as client:
            response = client.chat.send(
                model=model,
                messages=[{"role": "user", "content": full_text}],
                server_url=url
            )
            content = response.choices[0].message.content
            
            class SimpleResponse:
                def __init__(self, text):
                    self.text = text
            return SimpleResponse(content)
        
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP Error occurred: {http_err}")
        try:
            error_json = http_err.response.json()
            print(f"OpenRouter Error Details: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
        except Exception:
            print(f"Raw Response Content: {http_err.response.text}")
        raise http_err

    except Exception as e:
        print(f"❌ An unexpected error occurred: {str(e)}")
        raise e

def get_policy_id(new_policy_title, master_policies):
    """
    OpenRouterを使って、新しい公約がマスタデータのどれに該当するか判定する
    """
    if not master_policies:
        return "NEW"

    master_text = "\n".join([f"ID: {pid} | タイトル: {info.get('title', '⚠️タイトル未設定')}" for pid, info in master_policies.items()])

    prompt = f"""
    あなたは厳密な政治公約の分類アシスタントです。
    以下の【既存の公約マスタ】の中に、【新しい公約】と「意味・対象範囲が完全に一致する」ものがあるか判定してください。

    【厳密なルール】
    - ゆらぎは換算しません。「食料品消費税0％」と「消費税0％」は対象範囲が異なるため、別物として扱ってください。
    - 単なる言い回しの違い（例：「食品消費税のゼロ化」と「食料品の消費税をゼロにする」）であれば、同じとみなしてください。

    【既存の公約マスタ】
    {master_text}

    【新しい公約】
    {new_policy_title}

    【出力形式】
    完全に一致するものがあれば、その「ID（例: policy_001）」のみを出力してください。
    一致するものがなければ、「NEW」とだけ出力してください。
    説明や言い訳は一切不要です。
    """

    try:
        response = safe_generate_content(
            model='gemma-4-31b-it', 
            contents=[prompt],
        )
        result = response.text.strip()
        
        if result == "NEW" or re.match(r"^policy_\d+$", result):
            return result
        else:
            print(f"警告: AIの予期せぬ返答: {result}")
            return "NEW"
    except Exception as e:
        print(f"エラーが発生したため、判定を保留(ERROR)にします: {e}")
        return "ERROR"

def process_single_file(prefecture, filename, master_policies):
    """
    指定された単一のファイルを処理して policy_id を追加し、直接上書きする
    """
    # パス構築: output/manifesto/tokyo/tokyo-01.json
    target_path = os.path.join(BASE_INPUT_DIR, prefecture, filename)
    
    if not os.path.exists(target_path):
        print(f"スキップ: ファイルが見つかりません: {target_path}")
        return master_policies

    file_data = load_json(target_path)

    print(f"\n--- {prefecture}/{filename} の処理を開始します ---")

    # JSON直下に "manifesto" キーがある構造に対応
    manifesto_list = file_data.get("manifesto", [])
    
    if not manifesto_list:
        print(f"警告: 'manifesto' データが見つからないか空です: {filename}")
        return master_policies

    for manifesto in manifesto_list:
        title = manifesto["title"]
        
        # AIに判定させる
        matched_id = get_policy_id(title, master_policies)
        
        if matched_id == "ERROR":
            print(f"  [スキップ] 通信エラーのため保留: {title}")
            continue
            
        if matched_id == "NEW":
            # 現在のマスタ内、および今回生成されたIDも含めて最大の数値を探す
            existing_ids = [int(pid.split('_')[1]) for pid in master_policies.keys() if re.match(r"^policy_\d+$", pid)]
            next_num = max(existing_ids) + 1 if existing_ids else 1
            new_id = f"policy_{next_num:03d}"
            
            # マスタに即時追加（これで次のループの max() は 140 を検知できるようになります）
            master_policies[new_id] = {
                "title": title, 
                "status": "未確認",
                "last_updated": "2026-07-11",
                "evidence": ""
            }      
            manifesto["policy_id"] = new_id
            print(f"  [新規] {title} -> {new_id}")
        else:
            manifesto["policy_id"] = matched_id
            print(f"  [一致] {title} -> {matched_id}")
            
        time.sleep(0.5)

    # 元のファイルに直接上書き保存
    save_json(target_path, file_data)
    print(f"元のファイルを直接更新しました: {target_path}")
    
    return master_policies


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    master_policies = load_json(POLICIES_FILE)
    
    # =================【設定セクション】=================

    TARGET_PREFECTURE = ["okayama"]
#"hokkaido","akita","aomori","chiba","fukushima","gunma","ibaraki","iwate","kanagawa","miyagi","saitama","tochigi","yamagata"
    # fukui gifu  ishikawa    nagano niigata  shiga  toyama  "fukui","gifu","ishikawa","nagano","niigata","toyama","shiga","kyoto","mie"

    TARGET_DISTRICTS = list(range(1, 31))  


    # ===================================================
    
    print(f"【指定範囲の処理を開始】対象: {TARGET_PREFECTURE} の {TARGET_DISTRICTS} 区")

    for prefecture in TARGET_PREFECTURE:

        for district_num in TARGET_DISTRICTS:
            # 例: tokyo-01.json
            filename = f"{prefecture}-{district_num:02d}.json"
            
            # ファイルを処理し、マスタデータを更新
            master_policies = process_single_file(prefecture, filename, master_policies)
        
        # すべての処理が終わったら、最後にマスタデータを保存
        save_json(POLICIES_FILE, master_policies)
        print("\n指定された範囲の処理がすべて完了し、マスタデータを更新しました！")