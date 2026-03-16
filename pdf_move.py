import shutil
from pathlib import Path

prefectures = [
    "hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima",
    "ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa",
    "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu",
    "shizuoka", "aichi", "mie", "shiga", "kyoto", "osaka", "hyogo", "nara",
    "wakayama", "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
    "tokushima", "kagawa", "ehime", "kochi", "fukuoka", "saga", "nagasaki",
    "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa"
]

pdf_count = 0
for pref in prefectures:
    src_dir = Path(f"/Users/home/Minerva-1/data/raw_pdf/2026/shu/{pref}")
    dst_dir = Path(f"static/pdf/2026/shu/{pref}")
    dst_dir.mkdir(parents=True, exist_ok=True)
    for pdf_file in src_dir.glob("*.pdf"):
        # 移動先でのファイルパスを生成
        target_path = dst_dir / pdf_file.name
        
        # ファイルをコピー（元のファイルを残したい場合は copy、消していいなら move）
        shutil.copy2(pdf_file, target_path) # copy2 は作成日時などの属性も保持します
        
        print(f"Copied: {pdf_file.name}")
        pdf_count += 1

print(f"--- 完了！ {pdf_count} 件のPDFを {dst_dir} にコピーしました ---")