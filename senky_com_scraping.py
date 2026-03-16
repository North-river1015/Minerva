import os
import time
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- 設定 ---
BASE_URL = "https://shugiin.go2senkyo.com"
# 保存先のベースパス
BASE_SAVE_PATH = "data/raw_pdf/2026/shu"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 47都道府県のリスト（JISコード順 01:北海道 〜 47:沖縄）
PREFECTURES = [
    "hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima",
    "ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa",
    "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu",
    "shizuoka", "aichi", "mie", "shiga", "kyoto", "osaka", "hyogo", "nara",
    "wakayama", "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
    "tokushima", "kagawa", "ehime", "kochi", "fukuoka", "saga", "nagasaki",
    "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa"
]



def get_all_japan_pdf():
    # 1番(北海道)から47番(沖縄)までループ
    for i, pref_name in enumerate(PREFECTURES, 1):
        pref_id = i  # JISコード
        pref_url = f"{BASE_URL}/51/prefecture/{pref_id}"
        save_dir = os.path.join(BASE_SAVE_PATH, pref_name)
        
        # フォルダ作成
        os.makedirs(save_dir, exist_ok=True)
        
        print(f"\n=== {pref_name.upper()} (ID:{pref_id}) の解析開始 ===")
        process_prefecture(pref_url, pref_name, save_dir)
        
        # 都道府県ごとの大きな待機（サーバー負荷軽減）
        time.sleep(3)

def process_prefecture(url, pref_name, save_dir):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"  × 一覧ページの取得失敗: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    district_tasks = []

    # 選挙区ページへのリンクを収集
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        href = a['href']
        
        # 「区」が含まれ、かつ href に /senkyoku/ が含まれるものを対象
        if '区' in text and '/senkyoku/' in href:
            # 数字を抽出（例：東京1区 -> 1）
            num_match = re.search(r'(\d+)区', text)
            if num_match:
                dist_num = int(num_match.group(1))
                full_url = urljoin(BASE_URL, href)
                
                if not any(d['url'] == full_url for d in district_tasks):
                    district_tasks.append({
                        'url': full_url,
                        'num': dist_num
                    })



    # 番号順にソート
    district_tasks.sort(key=lambda x: x['num'])

    if not district_tasks:
        print(f"  × {pref_name} の選挙区リンクが見つかりませんでした。")
        return

    for item in district_tasks:
        formatted_num = f"{item['num']:02}"
        file_name = f"{pref_name}-{formatted_num}.pdf"
        
        # すでにファイルが存在する場合はスキップ（効率化）
        if os.path.exists(os.path.join(save_dir, file_name)):
            print(f"  - スキップ: {file_name} は存在します")
            continue

        try:
            time.sleep(1.5) # 選挙区ごとの待機
            dist_res = requests.get(item['url'], headers=HEADERS, timeout=15)
            dist_soup = BeautifulSoup(dist_res.text, 'html.parser')

            pdf_url = None
            for a_tag in dist_soup.find_all('a', href=True):
                if '選挙公報' in a_tag.get_text() or 'senkyo_koho' in a_tag['href']:
                    pdf_url = urljoin(item['url'], a_tag['href'])
                    break
            
            if pdf_url:
                download_pdf(pdf_url, file_name, save_dir)
            else:
                print(f"  × [{pref_name}-{formatted_num}] リンクなし")

        except Exception as e:
            print(f"  × エラー: {e}")

def download_pdf(url, filename, save_dir):
    save_path = os.path.join(save_dir, filename)
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=30)
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  ◎ 保存完了: {filename}")
    except Exception as e:
        print(f"  × ダウンロード失敗: {e}")

if __name__ == "__main__":
    get_all_japan_pdf()