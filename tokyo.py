import os
import json
import time
import google.genai as genai
from pathlib import Path
import fitz

# 東京の当選者リスト（1区〜30区）
TOKYO_WINNERS = {
    1: "山田みき", 2: "辻清人", 3: "石原宏高", 4: "平将明", 5: "若宮健嗣",
    6: "畦元将吾", 7: "丸川珠代", 8: "門寛子", 9: "菅原一秀", 10: "鈴木隼人",
    11: "下村博文", 12: "高木啓", 13: "土田慎", 14: "松島みどり", 15: "大空幸星",
    16: "大西洋平", 17: "平沢勝栄", 18: "福田かおる", 19: "松本洋平", 20: "木原誠二",
    21: "小田原潔", 22: "伊藤達也", 23: "川松真一朗", 24: "萩生田光一", 25: "井上信治",
    26: "今岡植", 27: "黒崎祐一", 28: "安藤高夫", 29: "長澤興祐", 30: "長島昭久"
}

# --- 設定 ---
client = genai.Client(api_key="AIzaSyBN_oeavULmi8Y--9bCEMUHuNk281mKd5Y")

PDF_DIR = Path("data/raw_pdf/2026/shu/tokyo/")
OUT_DIR = Path("data/ai_output/2026/shu/tokyo/")
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
  "district": "東京〇区",
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
    """
    
    # 画像リストとプロンプトを同時に投げる
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        contents=[prompt] + image_files, # 全ページの画像を渡す
        config={"response_mime_type": "application/json"}
    )
    
    return json.loads(response.text)


def crop_by_gemini_coords(pdf_path, page_num, coords, winner_name):
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    w, h = page.rect.width, page.rect.height
    
    ymin, xmin, ymax, xmax = coords
    
    # --- 改善ロジック ---
    # 1. 横幅は強制的に「端から端まで(0-1000)」にする
    new_xmin = 0
    new_xmax = 1000
    
    # 2. 上下はAIの回答より少し広め（上下に5%ずつ）確保する
    # これにより、枠線ギリギリの文字が切れるのを防ぎます
    new_ymin = max(0, ymin - 20) 
    new_ymax = min(1000, ymax + 20) 
    # ------------------

    rect = fitz.Rect(
        new_xmin * w / 1000, 
        new_ymin * h / 1000, 
        new_xmax * w / 1000, 
        new_ymax * h / 1000
    )
    
    zoom = 400 / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect)
    output_path = f"temp_cropped_{pdf_path.stem}.png"
    pix.save(output_path)
    doc.close()
    return output_path


def process():
    #ここは今後　pdf_path in sorted(PDF_DIR.glob("*.pdf")):　に変更
# ✅ 修正案
# 1つのファイルパスをリスト [] に入れる
    test_files = []
    for num in range(26, 31):
        pdf_path = PDF_DIR / f"tokyo-{num:02d}.pdf"
        if pdf_path.exists(): # ファイルがある場合だけ追加
            test_files.append(pdf_path)

    for pdf_path in test_files:
        print(f"⌛ 解析中: {pdf_path.name}")
            


        try:
            dist_num = int(pdf_path.stem.split("-")[-1])
            winner_name = TOKYO_WINNERS.get(dist_num)
        except ValueError:
            continue
        if not winner_name: continue
        
        # --- STEP 1: 全ページを低解像度で画像化して場所を探す ---
        doc = fitz.open(pdf_path)
        temp_scan_paths = []
        scan_files = []
        print(f"   🔍 候補者「{winner_name}」を探索中...")
        
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(150/72, 150/72)) # 低解像度でOK
            p = Path(f"scan_{pdf_path.stem}_p{i}.jpg")
            pix.save(str(p))
            temp_scan_paths.append(p)
            scan_files.append(client.files.upload(file=str(p)))

        # ACTIVE待ち
        for f in scan_files:
            while client.files.get(name=f.name).state.name != "ACTIVE":
                time.sleep(1)

        # 座標特定
        find_result = find_candidate_page_and_coords(scan_files, winner_name)
        

        # 不要になったスキャン画像を削除
        for f in scan_files: client.files.delete(name=f.name)
        for p in temp_scan_paths: p.unlink()


        # ✅ find_result が辞書であることを確認してから get を呼ぶ
        if not isinstance(find_result, dict) or not find_result.get("found"):
            print(f"   ⚠️ {winner_name} が見つかりませんでした。")
            continue



        # --- STEP 2: 特定された座標を「どアップ」で切り出す ---
        print(f"   ✂️ {find_result['page_index']+1}ページ目を高解像度で切り出し中...")
        crop_path = crop_by_gemini_coords(pdf_path, find_result['page_index'], find_result['coords'], winner_name)
        
        # --- STEP 3: 切り出した画像をAIに投げて詳細解析 ---
        print(f"   🤖 詳細解析（公約抽出）を実行中...")
        crop_file = client.files.upload(file=crop_path)
        while client.files.get(name=crop_file.name).state.name != "ACTIVE":
            time.sleep(1)

      

        # プロンプト内の「東京〇区」を正しい数字に置換して、AIの迷いをなくす
        target_district = f"東京{dist_num}区"
        current_prompt = PROMPT.replace("{winner_name}", winner_name).replace("東京〇区", target_district)

        # 保存処理
        json_text = response.text.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(json_text)
            out_file = OUT_DIR / f"{pdf_path.stem}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 保存完了: {out_file.name}")
        except json.JSONDecodeError:
            print(f"❌ 解析失敗\n{response.text[:200]}")

        # 後片付け
        client.files.delete(name=crop_file.name)
        Path(crop_path).unlink()
        doc.close()

        time.sleep(5)

if __name__ == "__main__":
    process()