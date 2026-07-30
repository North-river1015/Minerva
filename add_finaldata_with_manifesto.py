import os
import json
import re
from pathlib import Path

# --- パスの設定 ---
# ウェブ公約のデータ (assign_ids.py で処理した後のデータ)
WEB_DATA_DIR = Path("output/finaldata/2022/san")  # または output/finaldata
# 選挙公報のテキストデータ
BULLETIN_DATA_DIR = Path("data/ai_output/2022/san")
BULLETIN_MANIFESTO_DIR = Path("output/manifesto/2022/san")  # 公約抽出後のデータ
# 統合後のJSONを保存するフォルダ (Hugoが読み込む場所)
OUTPUT_DIR = Path("data/2022/san")




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







def load_json(filepath):
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_json(filepath, data):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_bulletin_text(raw_text):
    """
    選挙公報のテキストを段落ごとに分け、
    header(見出し) と body(<br>区切りの本文) の辞書リストに変換する
    """
    blocks = []
    if not raw_text:
        return blocks

    paragraphs = raw_text.split("\n\n")
    for p in paragraphs:
        lines = p.strip().split("\n")
        if lines:
            header = lines[0] # 1行目を見出しとする
            body = "<br>".join(lines[1:]) if len(lines) > 1 else "" # 2行目以降を<br>でつなぐ
            blocks.append({
                "header": header,
                "body": body
            })
    return blocks

def merge_district_data(district, district_num):
    # ファイル名の作成 (例: tokyo-01)
    filename_base = f"{district}-{district_num:02d}"
    filename_num = f"{district}-{district_num}"
    # データ読み込み
    try:
        name_of_winner=ALL_WINNERS[district][district_num]["name"]
        web_data = load_json(WEB_DATA_DIR / f"{district}/{filename_base}-api.json")
        bulletin_data = load_json(BULLETIN_DATA_DIR / f"{district}/{district_num}_{name_of_winner}.json")
        print(web_data)
        print(bulletin_data)
        print("本当はoutput/manifesto/2022/san/aichi/aichi-1.json")

        print(BULLETIN_DATA_DIR / f"{district}/{district_num}_{name_of_winner}.json")
        # 【修正】公約抽出済みの選挙公報JSON（output/manifesto/tokyo/tokyo-01.json）を読み込む
        bulletin_manifesto_data = load_json(BULLETIN_DATA_DIR / f"{district}/{district_num}_{name_of_winner}.json")
        
        if not web_data or not bulletin_data:
            print(f"スキップ: {filename_base} の基本データ（WEBまたは公報テキスト）が揃っていません。")
            return

        # 統合先の枠組みを作成
        merged = {
            "district": web_data.get("district", ""),
            "district_code": f"2022-san-{district}-{district_num}",
            "candidates": []
        }

        # web_data の候補者をベースに処理
        for web_candidate in web_data.get("candidates", []):
            cand_name = web_candidate.get("name")
            
            # bulletin_data（テキスト側）から同じ名前の候補者を探す
            bulletin_cand = next((c for c in bulletin_data.get("candidates", []) if c.get("name") == cand_name), {})
            
            # 選挙公報テキストの整形
            raw_text = bulletin_cand.get("full_text", "")
            formatted_blocks = format_bulletin_text(raw_text)

            # 【修正】抽出済み公報データ（bulletin_manifesto_data）から、この候補者の公約リストを探す
            extracted_manifestos = []
            if bulletin_manifesto_data:
                # 構造が「直下に manifesto キー」の場合
                if "manifesto" in bulletin_manifesto_data:
                    extracted_manifestos = bulletin_manifesto_data.get("manifesto", [])
                # 構造が「candidates の中に各候補者ごとの manifesto」があるパターンの場合（安全のための分岐）
                elif "candidates" in bulletin_manifesto_data:
                    m_cand = next((c for c in bulletin_manifesto_data.get("candidates", []) if c.get("name") == cand_name), {})
                    extracted_manifestos = m_cand.get("manifesto", [])

            # 1人の候補者のデータを組み立てる
            merged_candidate = {
                "name": cand_name,
                "party": web_candidate.get("party", ""),
                "bulletin": {
                    "full_text_blocks": formatted_blocks,
                    # 【修正】正しく抽出された公約データをセットする
                    "manifesto": extracted_manifestos 
                },
                "web": {
                    # ウェブからの公約（policy_id付き）
                    "manifesto": web_candidate.get("manifesto", []),
                    # ウェブからの非公約（元のJSONに not_manifesto があれば取得）
                    "not_manifesto": web_candidate.get("not_manifesto", [])
                }
            }
            merged["candidates"].append(merged_candidate)

        # 統合したデータを保存
        output_path = OUTPUT_DIR / f"{district}/{filename_base}.json"
        save_json(output_path, merged)
        print(f"保存完了: {output_path}")

    except Exception as e:
        print("ないかも")

    

if __name__ == "__main__":
    # 東京1区と2区を処理する (必要に応じて範囲を広げてください)
    district_list=["tokyo", "kanagawa",
        "niigata", "toyama", "ishikawa", "fukui", "yamanashi", "nagano", "gifu",
        "shizuoka", "aichi", "mie", "shiga", "kyoto", "osaka", "hyogo", "nara",
        "wakayama", "tottori", "shimane", "okayama", "hiroshima", "yamaguchi",
        "tokushima", "kagawa", "ehime", "kochi", "fukuoka", "saga", "nagasaki",
        "kumamoto", "oita", "miyazaki", "kagoshima", "okinawa","tokushima_kochi","tottori_shimane"]
    for district in district_list:
        for i in range(1, 31):
            merge_district_data(district,i)