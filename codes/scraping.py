import os
import time
import requests

# --- 設定 ---
# 末尾が01, 02...となるように組み立てます
BASE_URL_HEAD = "https://www.senkyo.metro.tokyo.lg.jp/documents/d/senkyo/r8syuin_shou_"
SAVE_DIR = "data/raw_pdf/2026/shu/tokyo/"
os.makedirs(SAVE_DIR, exist_ok=True)

def download_tokyo_direct_01():
    print("🚀 東京1区〜20区のPDFをダウンロードします（01〜20形式）...")
    
    count = 0

    headers = {"User-Agent": "Mozilla/5.0"}

    for i in range(21, 31):
        # 【修正ポイント】i:02d とすることで、1を01、10を10として出力します
        dist_str = f"{i:02d}"
        pdf_url = f"{BASE_URL_HEAD}{dist_str}-" 
        
        # 保存するファイル名も統一感をもたせるために tokyo-01.pdf にします
        new_file_name = f"tokyo-{dist_str}.pdf"
        save_path = os.path.join(SAVE_DIR, new_file_name)

        if os.path.exists(save_path):
            print(f"⏭️  Skip: {new_file_name}")
            continue

        try:
            print(f"📥 取得中 ({dist_str}/20): {pdf_url}")
            # 行政サイトはタイムアウトしやすいので少し長めに設定
            response = requests.get(pdf_url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ 保存完了: {new_file_name}")
                count += 1
            else:
                # もし 404 エラーが出る場合は、URLの末尾に .pdf が必要かもしれません
                print(f"⚠️  失敗 (Status {response.status_code}): {pdf_url}")
            
            time.sleep(1.5)

        except Exception as e:
            print(f"❌ エラー発生 ({new_file_name}): {e}")

    print(f"\n🏁 完了！合計 {count} 個のファイルを保存しました。")

if __name__ == "__main__":
    download_tokyo_direct_01()