import os
import json
import time
import google.genai as genai
from pathlib import Path
import fitz

LAYOUT_WEIRD = [
    "kyoto", "gifu", "kagawa", "kochi", 
    "miyagi", "miyazaki", "toyama", "yamaguchi"
]

ALL_WINNERS = {
 'osaka': {18: '遠藤敬', 19: '谷川とむ'}, 'saga': {1: '岩田和親', 2: '古川康'}, 'saitama': {1: '村井英樹', 2: '新藤義孝', 3: '黄川田仁志', 4: '穂坂泰', 5: '井原隆', 6: '尾花瑛仁', 7: '中野英幸', 8: '柴山昌彦', 9: '大塚拓', 10: '山口晋', 11: '小泉龍司', 12: '野中厚', 13: '三ッ林裕巳', 14: '藤田誠', 15: '田中良生', 16: '土屋品子'}, 'shiga': {1: '大岡敏孝', 2: '上野賢一郎', 3: '武村展英'}, 'shimane': {1: '高階恵美子', 2: '高見康裕'}, 'shizuoka': {1: '上川陽子', 2: '井林辰憲', 3: '山本裕三', 4: '深澤陽一', 5: '細野豪志', 6: '勝俣孝明', 7: '城内実', 8: '稲葉大輔'}, 'tochigi': {1: '船田元', 2: '五十嵐清', 3: '渡邊真太朗', 4: '石坂太', 5: '茂木敏充'}, 'tokushima': {1: '仁木博文', 2: '山口俊一'}, 'tottori': {1: '石破茂', 2: '赤沢亮正'}, 'toyama': {1: '中田宏', 2: '上田英俊', 3: '橘慶一郎'}, 'wakayama': {1: '山本大地', 2: '世耕弘成'}, 'yamagata': {1: '遠藤寛明', 2: '鈴木憲和', 3: '加藤鮎子'}, 'yamaguchi': {1: '高村正大', 2: '岸信千世', 3: '林芳正'}, 'yamanashi': {1: '中谷真一', 2: '堀内詔子'}}
# --- 設定 ---
client = genai.Client(api_key="AIzaSyBN_oeavULmi8Y--9bCEMUHuNk281mKd5Y")

PDF_DIR = Path("data/raw_pdf/2026/shu/")
OUT_DIR = Path("data/ai_output/2026/shu/")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 判定基準（rubric.mdの内容を要約して指示に組み込む）
PROMPT = """
あなたは選挙公報の解析を専門とする政治データアナリストです。

添付の選挙公報から[{winner_name}]の情報のみを抽出し、指定のフォーマットで出力してください。

### 手順
1. 画像内から [ {winner_name} ] の名前が記載された区画（セクション）を特定する。
2. その区画内の政策に関する全テキストを `full_text` として、チラシの構造（見出し・箇条書き）を維持して文字起こしする。
3. 文字起こしした内容から、以下の【公約判定ルール】に基づき 単なる方針（〜を目指す、重視する）ではなく、具体的なアクション（〜を創設する、〜をゼロにする、〜を改正する）のみを `pledges` に抽出する。

【公約判定ルール】
1. 具体的かつ客観的に達成・未達成が検証可能であること。
2. 「検討」「議論」「推進」「目指す」といった手続き表現ではなく「実施する」「導入する」等のコミットがあること。
3. 単なる信念やスローガン（例：日本を豊かに）は除外。



【full_text の整形ルール】
- AIが読み取った内容を、チラシの見出しごとに改行し、読みやすく構造化して記載してください。
- 文末に適切な改行を入れてください。
- プロフィールや挨拶などは省いてください。

JSONフォーマット：
{
  "district": "都道府県名(県、都、府などは不要）〇区",
  "candidates": [
    {
      "name": "{winner_name}",
      "party": "政党名",
      "step1_ocr_raw_text": "まずここに、候補者枠内の全ての文字を、改行含め一字一句漏らさず書き起こしてください。判定はまだしないでください。",
      "step2_selected_pledges": ["step1で書き出した中から、ルールに基づき具体的な公約のみを5つ以上厳選して抽出してください。"],
      "full_text": "step1の内容を構造化して整形したもの"
    }
  ]
}

【特別指示】
- 「1円単位の減税」「〇〇手当の創設」「所得制限の撤廃」など、法律や予算に直結する動詞に注目してください。
- 候補者の写真や氏名の周囲にある「大きな見出し」だけでなく、その下に続く「小さな注釈」まで一言一句読み飛ばさないでください。

### 制約事項
- JSON以外の説明文、挨拶、Markdownの装飾は一切含めず、純粋なJSON文字列のみを返してください。
- 対象候補者が見つからない場合は、全フィールドを null にして返してください。

【文字起こしの精度向上ルール】
OCRプロトコル: 左上から右下へ、視覚的なブロック（枠線）を意識して順番に読み取ってください。
縦書き対応: 日本語特有の縦書きテキストが含まれる場合、行の並び順を正しく維持してください。
ノイズ除去: 背景のデザインや写真に重なっている文字も、文脈から判断して正確に復元してください。
勝手な要約の禁止: full_text は文字起こしです。AIの判断で言葉を削ったり、言い換えたりせず、記載されている通りに書き出してください。

"""


def find_candidate_page_and_coords(image_files, winner_name):

    # ページ番号を付与してプロンプトを作成
    prompt = f"""
    添付された複数の画像の中から「{winner_name}」の選挙公報が含まれるページを特定してください。
    
    出力フォーマット(JSON):
    {{
      "found": true/false,
      "page_index": ページ番号(0から始まるインデックス),
      "coords": [ymin, xmin, ymax, xmax] (0-1000の数値)
    }}

    リストで出力しないように。
    """
    
    # 画像リストとプロンプトを同時に投げる
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        contents=[prompt] + image_files, # 全ページの画像を渡す
        config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)
    print(result)
    # もし結果がリストで返ってきたら、その最初の1つ（中身の辞書）を取り出す
    if isinstance(result, list) and len(result) > 0:
        result = result[0]
        
    return result


def crop_by_gemini_coords(pdf_path, page_num, coords, winner_name, pref_name):
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    w, h = page.rect.width, page.rect.height
    
    ymin, xmin, ymax, xmax = coords
    
   # 1. 横幅の判定
    if pref_name in LAYOUT_WEIRD:
        # 2列構成の県は、AIの判定（xmin, xmax）を信じる
        # ただし、少しだけ左右にマージン（3%ずつ）を持たせる
        new_xmin = max(0, xmin - 30)
        new_xmax = min(1000, xmax + 30)
    else:
        # 1列構成の県（地方部など）は、端から端まで
        new_xmin = 0
        new_xmax = 1000
    
    # 2. 上下の判定
    # 上下はどの県でもAIの回答より少し広め（2%ずつ）確保する
    new_ymin = max(0, ymin - 20) 
    new_ymax = min(1000, ymax + 20) 
    
    # ------------------

    rect = fitz.Rect(
        new_xmin * w / 1000, 
        new_ymin * h / 1000, 
        new_xmax * w / 1000, 
        new_ymax * h / 1000
    )
    
    # 高解像度で書き出し（zoom=400/72 は約300dpi相当）
    zoom = 400 / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect)
    output_path = f"temp_cropped_{pdf_path.stem}.png"
    pix.save(output_path)
    doc.close()
    return output_path

def process_all_japan():
    # 都道府県ごとのフォルダを巡回
    for pref_dir in sorted(PDF_DIR.iterdir()):
        if not pref_dir.is_dir(): continue

        pref_name = pref_dir.name.lower().strip()
        pref_winners = ALL_WINNERS.get(pref_name, {})
        
        # 出力先作成
        out_pref_dir = OUT_DIR / pref_name
        out_pref_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🌍 都道府県: {pref_name.upper()} を処理中...")

        # 各PDF（選挙区）を処理
        for pdf_path in sorted(pref_dir.glob("*.pdf")):
            try:
                # ファイル名 "tokyo-01.pdf" から区番号を取得
                dist_num = int(re.search(r'-(\d+)', pdf_path.stem).group(1))
                winner_name = pref_winners.get(dist_num)
            except (AttributeError, ValueError):
                continue

            if not winner_name:
                print(f"   ⏩ スキップ: {pdf_path.name} (当選者データなし)")
                continue

            print(f"⌛ 解析中: {pdf_path.name} [{winner_name}]")
            
            # --- 解析フロー ---
            doc = fitz.open(pdf_path)
            scan_files = []
            temp_images = []

            # 1. ページ探索
            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
                img_path = f"scan_{pdf_path.stem}_p{i}.jpg"
                pix.save(img_path)
                scan_files.append(client.files.upload(file=img_path))
                temp_images.append(img_path)

            # ファイルがACTIVEになるまで待機
            for f in scan_files:
                while client.files.get(name=f.name).state.name != "ACTIVE": time.sleep(1)

            find_result = find_candidate_page_and_coords(scan_files, winner_name)
            
            # スキャン用ゴミ捨て
            for f in scan_files: client.files.delete(name=f.name)
            for p in temp_images: Path(p).unlink()

            if not find_result.get("found"):
                print(f"   ⚠️ {winner_name} が見つかりませんでした。")
                continue

            # 2. 高解像度切り出し & 詳細解析
            crop_path = crop_by_gemini_coords(pdf_path, find_result['page_index'], find_result['coords'],winner_name, pref_name)
            crop_file = client.files.upload(file=crop_path)
            while client.files.get(name=crop_file.name).state.name != "ACTIVE": time.sleep(1)

            # 3. AIによる内容抽出
            current_prompt = PROMPT.replace("[{winner_name}]", winner_name) \
                       .replace("{winner_name}", winner_name) \
                       .replace("pref_display", pref_name) \
                       .replace("dist_num", str(dist_num))
            
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=[current_prompt, crop_file],
                config={"response_mime_type": "application/json"}
            )

            # 4. 保存
            out_file = out_pref_dir / f"{pdf_path.stem}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            print(f"✅ 保存完了: {out_file.relative_to(OUT_DIR)}")

            # 後片付け
            client.files.delete(name=crop_file.name)
            Path(crop_path).unlink()
            doc.close()
            time.sleep(2) # レートリミット対策

if __name__ == "__main__":
    import re
    process_all_japan()