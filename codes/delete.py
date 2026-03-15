from pathlib import Path

# --- 設定 ---
BASE_CONTENT_DIR = Path("/Users/home/Minerva-1/content/2026/shu/prefectures")

def remove_index_files():
    # 全ての都道府県フォルダを巡回
    # prefectures/*/index.md (大文字小文字を問わず) を探す
    for index_file in BASE_CONTENT_DIR.rglob("*"):
        if index_file.is_file() and index_file.name.lower() == "index.md":
            try:
                index_file.unlink()
                print(f"🗑️ 削除しました: {index_file}")
            except Exception as e:
                print(f"❌ 削除失敗: {index_file} ({e})")

if __name__ == "__main__":
    # 実行前に確認メッセージ
    print(f"🔎 {BASE_CONTENT_DIR} 内の index.md を一括削除します。")
    confirm = input("実行してよろしいですか？ (y/n): ")
    
    if confirm.lower() == 'y':
        remove_index_files()
        print("✅ 削除処理が完了しました。")
    else:
        print("中止しました。")