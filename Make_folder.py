import os

# ベースとなるディレクトリ
BASE_DIR = "data/raw_pdf/2026/shu"

# 47都道府県のリスト（JISコード順）
prefectures = [
    "hokkaido", "aomori", "iwate", "miyagi", "akita", "yamagata", "fukushima",
    "ibaraki", "tochigi", "gunma", "saitama", "chiba", "tokyo", "kanagawa",
    "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu",
    "shizuoka", "aichi", "mie", "shiga", "kyoto", "osaka", "hyogo", "nara",
    "wakayama", "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
    "tokushima", "kagawa", "ehime", "kochi", "fukuoka", "saga", "nagasaki",
    "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa"
]

def create_pref_folders():
    for i, pref in enumerate(prefectures, 1):
        # フォルダ名の形式を選択してください
        # パターンA: "osaka" (シンプル)
        # folder_name = pref
        
        # パターンB: "27_osaka" (JISコード順に並ぶので管理が楽)
        folder_name = f"{pref}" # 今回はご要望に合わせてシンプルに
        
        path = os.path.join(BASE_DIR, folder_name)
        
        # フォルダ作成（既に存在していてもエラーにしない）
        os.makedirs(path, exist_ok=True)
        
    print(f"完了: {BASE_DIR} 内に 47 都道府県のフォルダを作成しました。")

if __name__ == "__main__":
    create_pref_folders()