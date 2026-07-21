import os
import json
import time
import re
import requests
from pathlib import Path
from dotenv import load_dotenv 
from tenacity import retry, stop_after_attempt, wait_fixed
from openrouter import OpenRouter


#finaldataが前にPref作ったので反映されていないかもしれない



# 環境変数の読み込み
load_dotenv()
api_key_openrouter = os.environ.get('OPENROUTER')
url = os.environ.get('URL')

# ファイルパスの設定
INPUT_DIR = "output/finaldata/"
OUTPUT_DIR = "data/"
POLICIES_FILE = os.path.join(OUTPUT_DIR, "policies.json")

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

@retry(stop=stop_after_attempt(5), wait=wait_fixed(5))
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
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error Response Text: {e.response.text}")
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
    - ゆらぎは許容しません。「食料品消費税0％」と「消費税0％」は対象範囲が異なるため、別物として扱ってください。
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
        # OpenRouter用の関数を正しく呼び出す
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

def process_district_file(prefecture,filename, master_policies):
    """1つの選挙区ファイルを処理する (manifesto 直下を処理)"""
    input_path = os.path.join(INPUT_DIR, prefecture, filename)
    
    if not os.path.exists(input_path):
        print(f"スキップ: ファイルが存在しません -> {input_path}")
        return master_policies

    data = load_json(input_path)
    
    if not data or "candidates" not in data:
        print(f"警告: データが空か、形式が正しくありません: {filename}")
        return master_policies

    print(f"\n--- {filename} の処理を開始します ---")

    for candidate in data["candidates"]:
        print(f"候補者: {candidate['name']} の公約データを処理中...")
        
        # manifesto 直下のデータを取得
        manifesto_list = candidate.get("manifesto", [])
        
        for policy in manifesto_list:
            title = policy["title"]
            
            # AIに判定させる
            matched_id = get_policy_id(title, master_policies)
            
            if matched_id == "ERROR":
                print(f"  [スキップ] 通信エラーのため保留: {title}")
                continue
                
            if matched_id == "NEW":
                new_number = len(master_policies) + 1
                new_id = f"policy_{new_number:03}"
                
                master_policies[new_id] = {
                    "title": title, 
                    "status": "未確認",
                    "last_updated": "2026-05-05",
                    "evidence": ""
                }      

                policy["policy_id"] = new_id
                print(f"  [manifesto-新規] {title} -> {new_id}")
            else:
                policy["policy_id"] = matched_id
                print(f"  [manifesto-一致] {title} -> {matched_id}")
            
            time.sleep(0.5)
            
    # 元のファイルを直接上書き保存する
    save_json(input_path, data)
    print(f"元のファイルを直接更新しました: {input_path}")
    
    return master_policies

# --- メイン処理 ---
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    master_policies = load_json(POLICIES_FILE)
    
    # =================【設定エリア】=================
    PREFECTURES = ["gifu"] 
#gunma 3,5 まだ

    #"hokkaido","akita","aomori","chiba","fukushima","gunma","ibaraki","iwate","kanagawa","miyagi","saitama","tochigi","yamagata""fukui","gifu","ishikawa","nagano","niigata","toyama",
    ALL_DISTRICTS = True
    START_DISTRICT = 1
    END_DISTRICT = 30
    # ===============================================
    
    all_files = os.listdir(INPUT_DIR) if os.path.exists(INPUT_DIR) else []
    
    for pref in PREFECTURES:
        # 1. 各都道府県のフォルダパスを正確に作る (例: output/finaldata/hokkaido)
        pref_dir = os.path.join(INPUT_DIR, pref)
        
        if ALL_DISTRICTS:
            print(f"\n=== 【都道府県一括モード】{pref} の全ファイルを処理します ===")
            
            # フォルダ自体が存在しない場合はスキップする防衛策
            if not os.path.exists(pref_dir):
                print(f"警告: フォルダが存在しません -> {pref_dir}")
                continue
                
            # 2. 都道府県フォルダの「中身」を直接スキャンする
            # (中身は ['hokkaido-01-api.json', 'hokkaido-02-api.json'] のようになっている)
            pref_files = []
            for filename in os.listdir(pref_dir):
                if filename.startswith(f"{pref}-") and filename.endswith("-api.json"):
                    master_policies = process_district_file(pref, filename, master_policies)

        else:
            print(f"\n=== 【選挙区範囲指定モード】{pref} の {START_DISTRICT:02}区 ～ {END_DISTRICT:02}区 を処理します ===")
            for dist_num in range(START_DISTRICT, END_DISTRICT + 1):
                filename = f"{pref}-{dist_num:02}-api.json"
                master_policies = process_district_file(pref,filename, master_policies)
    
    # 最終的なマスタデータを保存
    save_json(POLICIES_FILE, master_policies)
    print("\nすべての指定処理が完了し、マスタデータを更新しました！")