import os




pref_data = [
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
    {"en": "saitama", "jp": "埼玉", "count": 16}, # 1増
    {"en": "chiba", "jp": "千葉", "count": 14},   # 1増
    {"en": "tokyo", "jp": "東京", "count": 30},   # 5増
    {"en": "kanagawa", "jp": "神奈川", "count": 20}, # 2増
    {"en": "niigata", "jp": "新潟", "count": 5},
    {"en": "toyama", "jp": "富山", "count": 3},
    {"en": "ishikawa", "jp": "石川", "count": 3},
    {"en": "fukui", "jp": "福井", "count": 2},
    {"en": "yamanashi", "jp": "山梨", "count": 2},
    {"en": "nagano", "jp": "長野", "count": 5},
    {"en": "gifu", "jp": "岐阜", "count": 5},
    {"en": "shizuoka", "jp": "静岡", "count": 8},
    {"en": "aichi", "jp": "愛知", "count": 16},   # 1増
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

base_path = "content/2026/shu/prefectures"

def generate_2026_pages():
    for data in pref_data:
        en_name = data["en"]
        jp_name = data["jp"]
        count = data["count"]

        # フォルダ作成
        folder_path = os.path.join(base_path, en_name)
        os.makedirs(folder_path, exist_ok=True)

        for i in range(1, count + 1):
            file_path = os.path.join(folder_path, f"{i}.md")

            # Front Matterの作成
            # titleを「愛知1区」に設定
            content = f"""---
title: "{jp_name}{i}区"
url: "/2026/shu/prefectures/{en_name}/{i}/"
district_code: "2026-shu-{en_name}-{i}"
candidate_name: ""
manifesto: ""
last_updated: ""
---

"""

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    print("✅ 全ファイルの生成が完了しました！")

if __name__ == "__main__":
    print("🚀 スクリプトを開始しました") 
    generate_2026_pages()
    print("🏁 すべての処理が終了しました") 