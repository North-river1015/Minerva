import os
import json
import time
import google.genai as genai
from pathlib import Path
import fitz
from dotenv import load_dotenv 
from PIL import Image

load_dotenv()

LAYOUT_WEIRD = [
    "kyoto", "gifu", "kagawa", "kochi", 
    "miyagi", "miyazaki", "toyama", "yamaguchi"
]




ALL_WINNERS = {
    "tokyo": {
        1: {
            "name": "朝日健太郎",
            "official": "https://asahikentaro.tokyo",
            "party": "自由民主党"
        },
        2: {
            "name": "竹谷とし子",
            "official": "https://takeya-toshiko.jp",
            "party": "公明党"
        },
        3: {
            "name": "山添拓",
            "official": "https://yamazoetaku.com",
            "party": "日本共産党"
        },
        4: {
            "name": "蓮舫",
            "official": "https://renho.jp",
            "party": "立憲民主党"
        },
        5: {
            "name": "生稲晃子",
            "official": "https://ikuina-akiko.com",
            "party": "自由民主党"
        },
        6: {
            "name": "山本太郎",
            "official": "https://taro-yamamoto.jp",
            "party": "れいわ新選組"
        }
    },
    "kanagawa": {
        1: {
            "name": "三原じゅん子",
            "official": "http://miharajunco.org",
            "party": "自由民主党"
        },
        2: {
            "name": "松沢成文",
            "official": "https://www.matsuzawa.com/",
            "party": "日本維新の会"
        },
        3: {
            "name": "三浦信祐",
            "official": "https://miura-nobuhiro.com",
            "party": "公明党"
        },
        4: {
            "name": "浅尾慶一郎",
            "official": "https://asao.net",
            "party": "自由民主党"
        },
        5: {
            "name": "水野素子",
            "official": "https://mizunomotoko.com/",
            "party": "立憲民主党"
        }
    },
    "saitama": {
        1: {
            "name": "関口昌一",
            "official": "http://sekiguchi-masakazu.com",
            "party": "自由民主党"
        },
        2: {
            "name": "上田清司",
            "official": "https://ueda-kiyoshi.com",
            "party": "無所属"
        },
        3: {
            "name": "西田実仁",
            "official": "https://nishida-makoto.jp",
            "party": "公明党"
        },
        4: {
            "name": "高木真理",
            "official": "https://marit.main.jp/",
            "party": "立憲民主党"
        }
    },
    "aichi": {
        1: {
            "name": "藤川政人",
            "official": "https://fujikawa-masahito.com/",
            "party": "自由民主党"
        },
        2: {
            "name": "里見隆治",
            "official": "https://satomi-ryuji.com/",
            "party": "公明党"
        },
        3: {
            "name": "斎藤嘉隆",
            "official": "https://saitoyoshitaka.com/",
            "party": "立憲民主党"
        },
        4: {
            "name": "伊藤孝恵",
            "official": "https://itoutakae.info/",
            "party": "国民民主党"
        }
    },
    "osaka": {
        1: {
            "name": "高木佳保里",
            "official": "https://kaori-takagi.com/",
            "party": "日本維新の会"
        },
        2: {
            "name": "松川るい",
            "official": "https://www.matsukawa-rui.jp/",
            "party": "自由民主党"
        },
        3: {
            "name": "浅田均",
            "official": "http://asd2a.com/",
            "party": "日本維新の会"
        },
        4: {
            "name": "石川博崇",
            "official": "https://www.hiro-ishikawa.net/",
            "party": "公明党"
        }
    },
    "hokkaido": {
        1: {
            "name": "長谷川岳",
            "official": "https://hasegawagaku0216.com",
            "party": "自由民主党"
        },
        2: {
            "name": "徳永エリ",
            "official": "https://tokunaga-eri.jp",
            "party": "立憲民主党"
        },
        3: {
            "name": "船橋利実",
            "official": "https://funahashi-toshimitsu.jp",
            "party": "自由民主党"
        }
    },
    "chiba": {
        1: {
            "name": "臼井正一",
            "official": "https://shoichi.info",
            "party": "自由民主党"
        },
        2: {
            "name": "猪口邦子",
            "official": "http://www.kunikoinoguchi.jp/",
            "party": "自由民主党"
        },
        3: {
            "name": "小西洋之",
            "official": "https://konishi-hiroyuki.jp/",
            "party": "立憲民主党"
        }
    },
    "hyogo": {
        1: {
            "name": "片山大介",
            "official": "http://www.katayama-daisuke.com/",
            "party": "日本維新の会"
        },
        2: {
            "name": "末松信介",
            "official": "https://suematsu.org/",
            "party": "自由民主党"
        },
        3: {
            "name": "伊藤孝江",
            "official": "https://ito-takae.com/",
            "party": "公明党"
        }
    },
    "fukuoka": {
        1: {
            "name": "大家敏志",
            "official": "https://oie-satoshi.com/",
            "party": "自由民主党"
        },
        2: {
            "name": "古賀之士",
            "official": "https://koga-yukihito.jp/",
            "party": "立憲民主党"
        },
        3: {
            "name": "秋野公造",
            "official": "https://akino-kozo.com/",
            "party": "公明党"
        }
    },
    "ibaraki": {
        1: {
            "name": "加藤明良",
            "official": "https://katoakiyoshi.jp",
            "party": "自由民主党"
        },
        2: {
            "name": "堂込麻紀子",
            "official": "https://dougomi.jp",
            "party": "無所属"
        }
    },
    "shizuoka": {
        1: {
            "name": "若林洋平",
            "official": "https://yohei-wakabayashi.com",
            "party": "自由民主党"
        },
        2: {
            "name": "平山佐知子",
            "official": "https://hirayamasachiko.net",
            "party": "無所属"
        }
    },
    "kyoto": {
        1: {
            "name": "吉井章",
            "official": "https://akira-yoshii.com/",
            "party": "自由民主党"
        },
        2: {
            "name": "福山哲郎",
            "official": "https://www.fukuyama.gr.jp/",
            "party": "立憲民主党"
        }
    },
    "hiroshima": {
        1: {
            "name": "宮沢洋一",
            "official": "https://www.miyazawa-yoichi.com/",
            "party": "自由民主党"
        },
        2: {
            "name": "三上絵里",
            "official": "https://mikamieri.net/",
            "party": "無所属"
        }
    },
    "aomori": {
        1: {
            "name": "田名部匡代",
            "official": "https://masayo.gr.jp",
            "party": "立憲民主党"
        }
    },
    "iwate": {
        1: {
            "name": "広瀬めぐみ",
            "official": "N/A",
            "party": "自由民主党"
        }
    },
    "miyagi": {
        1: {
            "name": "桜井充",
            "official": "https://dr-sakurai.jp",
            "party": "自由民主党"
        }
    },
    "akita": {
        1: {
            "name": "石井浩郎",
            "official": "https://ishii-hiroo.jp",
            "party": "自由民主党"
        }
    },
    "yamagata": {
        1: {
            "name": "舟山康江",
            "official": "https://www.y-funayama.jp/",
            "party": "国民民主党"
        }
    },
    "fukushima": {
        1: {
            "name": "星北斗",
            "official": "https://hoshi-hokuto.jp",
            "party": "自由民主党"
        }
    },
    "tochigi": {
        1: {
            "name": "上野通子",
            "official": "https://ueno-michiko.org/",
            "party": "自由民主党"
        }
    },
    "gunma": {
        1: {
            "name": "中曽根弘文",
            "official": "https://hiro-nakasone.com/",
            "party": "自由民主党"
        }
    },
    "niigata": {
        1: {
            "name": "小林一大",
            "official": "https://kobayashikazuhiro.com",
            "party": "自由民主党"
        }
    },
    "toyama": {
        1: {
            "name": "野上浩太郎",
            "official": "https://kotaro.net",
            "party": "自由民主党"
        }
    },
    "ishikawa": {
        1: {
            "name": "岡田直樹",
            "official": "https://okada-naoki.net/",
            "party": "自由民主党"
        }
    },
    "fukui": {
        1: {
            "name": "山崎正昭",
            "official": "https://masaaki-yamazaki.com/",
            "party": "自由民主党"
        }
    },
    "yamanashi": {
        1: {
            "name": "永井学",
            "official": "https://nagai-manabu.jp",
            "party": "自由民主党"
        }
    },
    "nagano": {
        1: {
            "name": "杉尾秀哉",
            "official": "https://sugio.club/",
            "party": "立憲民主党"
        }
    },
    "gifu": {
        1: {
            "name": "渡辺猛之",
            "official": "https://watanabetakeyuki.jp/",
            "party": "自由民主党"
        }
    },
    "mie": {
        1: {
            "name": "山本佐知子",
            "official": "https://sachiko-yamamoto.jp",
            "party": "自由民主党"
        }
    },
    "shiga": {
        1: {
            "name": "小鑓隆史",
            "official": "https://koyaritakashi.net",
            "party": "自由民主党"
        }
    },
    "nara": {
        1: {
            "name": "佐藤啓",
            "official": "https://sato-kei.jp",
            "party": "自由民主党"
        }
    },
    "wakayama": {
        1: {
            "name": "鶴保庸介",
            "official": "https://tsuruho.com",
            "party": "自由民主党"
        }
    },
    "tottori_shimane": {
        1: {
            "name": "青木一彦",
            "official": "https://www.aokikazuhiko.jp/",
            "party": "自由民主党"
        }
    },
    "okayama": {
        1: {
            "name": "小野田紀美",
            "official": "https://onodakimi.com",
            "party": "自由民主党"
        }
    },
    "yamaguchi": {
        1: {
            "name": "江島潔",
            "official": "https://kiyoshi-ejima.jp/",
            "party": "自由民主党"
        }
    },
    "kagawa": {
        1: {
            "name": "磯崎仁彦",
            "official": "https://isozaki-yoshihiko.com",
            "party": "自由民主党"
        }
    },
    "tokushima_kochi": {
        1: {
            "name": "中西祐介",
            "official": "https://yusuke-nakanishi.info",
            "party": "自由民主党"
        }
    },
    "ehime": {
        1: {
            "name": "山本順三",
            "official": "https://yamamoto-junzo.com",
            "party": "自由民主党"
        }
    },
    "saga": {
        1: {
            "name": "福岡資麿",
            "official": "https://www.takamaro.jp/",
            "party": "自由民主党"
        }
    },
    "nagasaki": {
        1: {
            "name": "山本啓介",
            "official": "https://yamamotokeisuke.jp",
            "party": "自由民主党"
        }
    },
    "kumamoto": {
        1: {
            "name": "松村祥史",
            "official": "https://yoshifumi.net/",
            "party": "自由民主党"
        }
    },
    "oita": {
        1: {
            "name": "古庄玄知",
            "official": "https://koshou.net",
            "party": "自由民主党"
        }
    },
    "miyazaki": {
        1: {
            "name": "松下新平",
            "official": "https://shinnpei.com/",
            "party": "自由民主党"
        }
    },
    "kagoshima": {
        1: {
            "name": "野村哲郎",
            "official": "https://nomura-tetsuro.com",
            "party": "自由民主党"
        }
    },
    "okinawa": {
        1: {
            "name": "伊波洋一",
            "official": "https://ihayoichi.jp/",
            "party": "無所属"
        }
    }
}



#GoogleのGeminiを使いました。
key = os.environ.get('GEMINI_API')

client = genai.Client(api_key= key)

PDF_DIR = Path("static/pdf/2022/san/")
OUT_DIR = Path("data/ai_output/2022/san/")

# RubricからPromptに入れて見ましたが、公約判断の精度は非常に低いです。
#AIに選挙区を書かせましたが、Nullや誤りが多いので今後改善（自動で？）
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
    
   
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        contents=[prompt] + image_files,
        config={"response_mime_type": "application/json"}
    )
    
    result = json.loads(response.text)

   #何度かリストで返されたので、念のため
    if isinstance(result, list) and len(result) > 0:
        result = result[0]
        
    return result


def crop_by_gemini_coords(pdf_path, page_num, coords, winner_name, pref_name):
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    w, h = page.rect.width, page.rect.height
    
    ymin, xmin, ymax, xmax = coords
    
 
    if pref_name in LAYOUT_WEIRD:
        # これらの県は二人ずつ並んでいる
        # 少しだけ左右にマージンを
        new_xmin = max(0, xmin - 30)
        new_xmax = min(1000, xmax + 30)
    else:
        # 1列構成の県は、端から端まで
        new_xmin = 0
        new_xmax = 1000
    
  
    # 上下はどの県でもAIの回答より少し広めに確保
    new_ymin = max(0, ymin - 20) 
    new_ymax = min(1000, ymax + 20) 
    
  


    rect = fitz.Rect(
        new_xmin * w / 1000, 
        new_ymin * h / 1000, 
        new_xmax * w / 1000, 
        new_ymax * h / 1000
    )
    
    # 高解像度で
    zoom = 400 / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect)
    output_path = f"temp_cropped_{pdf_path.stem}.png"
    pix.save(output_path)
    doc.close()
    return output_path

def process_all_japan():
    # 都道府県ごとのフォルダ
    for pref_dir in sorted(PDF_DIR.iterdir()):
        if not pref_dir.is_dir():
            continue
        
        pref_name = pref_dir.name.lower().strip()
        pref_winners = ALL_WINNERS.get(pref_name, {})
        
        # 当選者データがない県はスキップ
        if not pref_winners:
            continue

        # 出力先作成
        out_pref_dir = OUT_DIR / pref_name
        out_pref_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n======================================")
        print(f"都道府県: {pref_name.upper()} を処理中...")
        print(f"======================================")

        # 県内の全PDFを取得 (参議院などの場合、県単位で1〜複数ファイルが想定される)
        pdf_files = list(sorted(pref_dir.glob("*.pdf")))
        if not pdf_files:
            print(f"  スキップ: 該当するPDFが見つかりません")
            continue

        scan_files = []
        temp_images = []
        # Geminiが返す「0から始まる連番インデックス」から、元のPDFパスとページ番号を逆引きするためのリスト
        page_mapping = [] 

        # 1. ページ探索用の画像を準備・一括アップロード (県単位で1回だけ実行)
        print(f"  [準備] 県内のPDFを画像化・アップロード中...")
        for pdf_path in pdf_files:
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
                img_path = f"scan_{pref_name}_{pdf_path.stem}_p{i}.jpg"
                pix.save(img_path)
                
                uploaded_file = client.files.upload(file=img_path)
                scan_files.append(uploaded_file)
                temp_images.append(img_path)
                page_mapping.append((pdf_path, i))
            doc.close()

        # 全アップロードファイルのACTIVE待機
        for f in scan_files:
            while client.files.get(name=f.name).state.name != "ACTIVE":
                time.sleep(1)

        # 2. 当選者ごとにループして解析
        for winner_id, winner_info in pref_winners.items():
            winner_name = winner_info.get("name")
            if not winner_name:
                continue

            print(f"  解析中: [{winner_name}]")

            # 位置特定 (アップロード済みの県内全ページ画像を使い回す)
            find_result = find_candidate_page_and_coords(scan_files, winner_name)

            if not find_result.get("found"):
                print(f"    -> 公報内に見つかりませんでした。")
                continue

            found_global_index = find_result.get('page_index')
            if found_global_index is None or found_global_index >= len(page_mapping):
                print(f"    -> ページインデックスが不正です。")
                continue

            # 逆引きして、該当するPDFとページを特定
            target_pdf_path, target_page_num = page_mapping[found_global_index]

            # 3. 切り出し・詳細解析
            crop_path = crop_by_gemini_coords(target_pdf_path, target_page_num, find_result['coords'], winner_name, pref_name)
            crop_file = client.files.upload(file=crop_path)


            while client.files.get(name=crop_file.name).state.name != "ACTIVE":
                time.sleep(1)

            # 抽出プロンプトのフォーマット設定
            current_prompt = PROMPT.replace("[{winner_name}]", winner_name) \
                                   .replace("{winner_name}", winner_name) \
                                   .replace("pref_display", pref_name) \
                                   .replace("dist_num", str(winner_id))



            response = client.models.generate_content(
                model='gemini-3.1-flash-lite-preview',
                contents=[current_prompt, crop_file],
                config={"response_mime_type": "application/json"}
            )

            # 4. 保存 (ファイル名は winner_id と winner_name で一意にする)
            out_file = out_pref_dir / f"{winner_id}_{winner_name}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(response.text)

            print(f"    -> 保存完了: {out_file.relative_to(OUT_DIR)}")

            # 個別切り出し画像のクリーンアップ
            client.files.delete(name=crop_file.name)
            Path(crop_path).unlink()
            time.sleep(2)  # レートリミット対策

        # 5. 県ごとの処理が全て終わったら、探索用画像をクリーンアップ
        print(f"  [片付け] 一時ファイルを削除中...")
        for f in scan_files:
            client.files.delete(name=f.name)
        for p in temp_images:
            Path(p).unlink()

if __name__ == "__main__":
    process_all_japan()