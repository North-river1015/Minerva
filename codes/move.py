from pathlib import Path
import shutil

# --- 設定 ---
BASE_CONTENT_DIR = Path("/Users/home/Minerva-1/content/2026/shu/prefectures")

# 各都道府県の設定
PREF_CONFIG = [
    {"en": "hokkaido", "jp": "北海道", "count": 12},
    {"en": "aomori", "jp": "青森", "count": 3},
    {"en": "iwate", "jp": "岩手", "count": 3},
    {"en": "miyagi", "jp": "宮城", "count": 5},
    {"en": "akita", "jp": "秋田", "count": 3},
    {"en": "yamagata", "jp": "山形", "count": 3},
    {"en": "fukushima", "jp": "福島", "count": 4},
    {"en": "ibaraki", "jp": "茨城", "count": 7},
    {"en": "tochigi", "jp": "栃木", "count": 5},
    {"en": "gunma", "jp": "群馬", "count": 5},
    {"en": "saitama", "jp": "埼玉", "count": 16},
    {"en": "chiba", "jp": "千葉", "count": 14},
    {"en": "tokyo", "jp": "東京", "count": 30},
    {"en": "kanagawa", "jp": "神奈川", "count": 20},
    {"en": "niigata", "jp": "新潟", "count": 5},
    {"en": "toyama", "jp": "富山", "count": 3},
    {"en": "ishikawa", "jp": "石川", "count": 3},
    {"en": "fukui", "jp": "福井", "count": 2},
    {"en": "yamanashi", "jp": "山梨", "count": 2},
    {"en": "nagano", "jp": "長野", "count": 5},
    {"en": "gifu", "jp": "岐阜", "count": 5},
    {"en": "shizuoka", "jp": "静岡", "count": 8},
    {"en": "aichi", "jp": "愛知", "count": 16},
    {"en": "mie", "jp": "三重", "count": 4},
    {"en": "shiga", "jp": "滋賀", "count": 3},
    {"en": "kyoto", "jp": "京都", "count": 6},
    {"en": "osaka", "jp": "大阪", "count": 19},
    {"en": "hyogo", "jp": "兵庫", "count": 12},
    {"en": "nara", "jp": "奈良", "count": 3},
    {"en": "wakayama", "jp": "和歌山", "count": 2},
    {"en": "tottori", "jp": "鳥取", "count": 2},
    {"en": "shimane", "jp": "島根", "count": 2},
    {"en": "okayama", "jp": "岡山", "count": 4},
    {"en": "hiroshima", "jp": "広島", "count": 6},
    {"en": "yamaguchi", "jp": "山口", "count": 3},
    {"en": "tokushima", "jp": "徳島", "count": 2},
    {"en": "kagawa", "jp": "香川", "count": 3},
    {"en": "ehime", "jp": "愛媛", "count": 3},
    {"en": "kochi", "jp": "高知", "count": 2},
    {"en": "fukuoka", "jp": "福岡", "count": 11},
    {"en": "saga", "jp": "佐賀", "count": 2},
    {"en": "nagasaki", "jp": "長崎", "count": 3},
    {"en": "kumamoto", "jp": "熊本", "count": 4},
    {"en": "oita", "jp": "大分", "count": 3},
    {"en": "miyazaki", "jp": "宮崎", "count": 3},
    {"en": "kagoshima", "jp": "鹿児島", "count": 4},
    {"en": "okinawa", "jp": "沖縄", "count": 4},
]

def move_district_files():
    for config in PREF_CONFIG:
        pref_slug = config["en"]
        pref_dir = BASE_CONTENT_DIR / pref_slug
        
        if not pref_dir.exists():
            continue
        
        # 移動先フォルダ: tokyo/tokyo-district/
        dist_dir = pref_dir / f"{pref_slug}-district"
        dist_dir.mkdir(parents=True, exist_ok=True)
        
        # 1.md, 2.md ... count.md までをループで探して移動
        for i in range(1, config["count"] + 1):
            file_name = f"{i}.md"
            source_file = pref_dir / file_name
            target_file = dist_dir / file_name
            
            if source_file.exists():
                shutil.move(str(source_file), str(target_file))
                print(f"🚚 移動: {source_file.name} -> {pref_slug}-district/")
            else:
                # すでに移動済みか、ファイルが存在しない場合はパス
                pass

if __name__ == "__main__":
    move_district_files()