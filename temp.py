import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- 設定 ---
BASE_URL = "https://sangiin.go2senkyo.com"
# 保存先のベースパス
BASE_SAVE_PATH = "data/raw_pdf/2022/san"

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
        pref_url = f"{BASE_URL}/2022/prefecture/{pref_id}"
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

    # ページ内からPDFまたは「選挙公報」リンクを抽出
    pdf_links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        text = a_tag.get_text(strip=True)

        # リンク先が.pdfか、テキスト/URLにキーワードが含まれている場合
        if href.lower().endswith('.pdf') or '選挙公報' in text or 'senkyo_koho' in href:
            full_url = urljoin(url, href)
            if full_url not in pdf_links:
                pdf_links.append(full_url)

    if not pdf_links:
        print(f"  × [{pref_name}] PDFリンクが見つかりませんでした")
        return

    # 見つかったPDFを順にダウンロード
    for idx, pdf_url in enumerate(pdf_links, 1):
        formatted_num = f"{idx:02d}"
        file_name = f"{pref_name}-{formatted_num}.pdf"
        
        # すでにファイルが存在する場合はスキップ
        if os.path.exists(os.path.join(save_dir, file_name)):
            print(f"  - スキップ: {file_name} は存在します")
            continue

        time.sleep(1.5)  # サーバー負荷軽減の待機
        download_pdf(pdf_url, file_name, save_dir)


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