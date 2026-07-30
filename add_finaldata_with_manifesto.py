import os
import json
import re
from pathlib import Path

# --- パスの設定 ---
# ウェブ公約のデータ (assign_ids.py で処理した後のデータ)
WEB_DATA_DIR = Path("output/finaldata/2025/san")  # または output/finaldata
# 選挙公報のテキストデータ
BULLETIN_DATA_DIR = Path("data/ai_output/2025/san")
BULLETIN_MANIFESTO_DIR = Path("output/manifesto/2025/san")  # 公約抽出後のデータ
# 統合後のJSONを保存するフォルダ (Hugoが読み込む場所)
OUTPUT_DIR = Path("data/2025/san")




ALL_WINNERS = {
    "kanagawa": {
        1: {
            "name": "牧山ひろえ",
            "official": "https://makiyama-hiroe.jp",
            "party": "立憲民主党"
        },
        2: {
            "name": "籠島彰宏",
            "official": "https://akagoshima.jp",
            "party": "国民民主党"
        },
        3: {
            "name": "脇雅昭",
            "official": "https://waki.link",
            "party": "自由民主党"
        },
        4: {
            "name": "初鹿野裕樹",
            "official": "N/A",
            "party": "参政党"
        }
    },
    "aichi": {
        1: {
            "name": "水野孝一",
            "official": "https://mizuno.ne.jp",
            "party": "国民民主党"
        },
        2: {
            "name": "田島麻衣子",
            "official": "https://maiko-tajima.com",
            "party": "立憲民主党"
        },
        3: {
            "name": "杉本純子",
            "official": "https://junkosugimoto.jp",
            "party": "参政党"
        },
        4: {
            "name": "酒井庸行",
            "official": "https://www.sakai-yasuyuki.com/",
            "party": "自由民主党"
        }
    },
    "osaka": {
        1: {
            "name": "佐々木理江",
            "official": "https://sasaki-rie.jp/",
            "party": "日本維新の会"
        },
        2: {
            "name": "岡崎ふとし",
            "official": "https://futoshi-ishin.com/",
            "party": "日本維新の会"
        },
        3: {
            "name": "宮出千慧",
            "official": "https://miyade-chisato.hp.peraichi.com/",
            "party": "参政党"
        },
        4: {
            "name": "杉久武",
            "official": "https://sugi-hisatake.com/",
            "party": "公明党"
        }
    },
    "tokyo": {
        1: {
            "name": "鈴木大地",
            "official": "https://daichi55.com",
            "party": "自由民主党"
        },
        2: {
            "name": "さや",
            "official": "https://sayanokai.jp",
            "party": "参政党"
        },
        3: {
            "name": "牛田茉友",
            "official": "https://ushidamayu.info",
            "party": "国民民主党"
        },
        4: {
            "name": "川村雄大",
            "official": "https://kawamura-yudai.com/",
            "party": "公明党"
        },
        5: {
            "name": "奥村祥大",
            "official": "https://yoshihiro-okumura.com",
            "party": "国民民主党"
        },
        6: {
            "name": "吉良佳子",
            "official": "https://kirayoshiko.com/",
            "party": "日本共産党"
        },
        7: {
            "name": "塩村文夏",
            "official": "https://shiomura-ayaka.com",
            "party": "立憲民主党"
        }
    },
    "saitama": {
        1: {
            "name": "古川俊治",
            "official": "https://www.toshiharu-furukawa.jp/",
            "party": "自由民主党"
        },
        2: {
            "name": "江原久美子",
            "official": "https://www.eharakumiko.net/",
            "party": "国民民主党"
        },
        3: {
            "name": "熊谷裕人",
            "official": "https://www.kumachan55.jp/",
            "party": "立憲民主党"
        },
        4: {
            "name": "大津力",
            "official": "https://ohtsu-tsutomu.com/",
            "party": "参政党"
        }
    },
    "hyogo": {
        1: {
            "name": "泉房穂",
            "official": "https://izumi-fusaho.com",
            "party": "立憲民主党"
        },
        2: {
            "name": "高橋光男",
            "official": "https://takahashi-mitsuo.com",
            "party": "公明党"
        },
        3: {
            "name": "加田裕之",
            "official": "https://kadahiroyuki.com",
            "party": "自由民主党"
        }
    },
    "fukuoka": {
        1: {
            "name": "松山政司",
            "official": "https://matsuyama-masaji.jp",
            "party": "自由民主党"
        },
        2: {
            "name": "中田優子",
            "official": "https://nakadayuko.jp/",
            "party": "参政党"
        },
        3: {
            "name": "下野六太",
            "official": "https://shimono-rokuta.jp/",
            "party": "公明党"
        }
    },
    "hokkaido": {
        1: {
            "name": "高橋はるみ",
            "official": "https://haruchan.jp",
            "party": "自由民主党"
        },
        2: {
            "name": "勝部賢志",
            "official": "https://katsube-kenji.jp/",
            "party": "立憲民主党"
        },
        3: {
            "name": "岩本剛人",
            "official": "https://tsuyohito.jp",
            "party": "自由民主党"
        }
    },
    "chiba": {
        1: {
            "name": "小林さやか",
            "official": "https://sayakakobayashi.com",
            "party": "国民民主党"
        },
        2: {
            "name": "長浜博行",
            "official": "https://www.nagahamahiroyuki.com/",
            "party": "立憲民主党"
        },
        3: {
            "name": "石井準一",
            "official": "http://www.ishii-junichi.com/",
            "party": "自由民主党"
        }
    },
    "ibaraki": {
        1: {
            "name": "上月良祐",
            "official": "https://kouzuki-r.com",
            "party": "自由民主党"
        },
        2: {
            "name": "櫻井祥子",
            "official": "N/A",
            "party": "参政党"
        }
    },
    "shizuoka": {
        1: {
            "name": "榛葉賀津也",
            "official": "https://k-shimba.com",
            "party": "国民民主党"
        },
        2: {
            "name": "牧野京夫",
            "official": "https://makino-net.com/",
            "party": "自由民主党"
        }
    },
    "kyoto": {
        1: {
            "name": "新実彰平",
            "official": "https://niimi-shohei.org/",
            "party": "日本維新の会"
        },
        2: {
            "name": "西田昌司",
            "official": "https://www.showyou.jp/",
            "party": "自由民主党"
        }
    },
    "hiroshima": {
        1: {
            "name": "西田英範",
            "official": "https://www.nishitahidenori.jp/",
            "party": "自由民主党"
        },
        2: {
            "name": "森本真治",
            "official": "https://morimori.net/",
            "party": "立憲民主党"
        }
    },
    "aomori": {
        1: {
            "name": "福士珠美",
            "official": "https://fukushimasumi.jp",
            "party": "立憲民主党"
        }
    },
    "iwate": {
        1: {
            "name": "横澤高徳",
            "official": "https://yokozawa-takanori.jp",
            "party": "立憲民主党"
        }
    },
    "miyagi": {
        1: {
            "name": "石垣のりこ",
            "official": "https://noriko-ishigaki.jp",
            "party": "立憲民主党"
        }
    },
    "akita": {
        1: {
            "name": "寺田静",
            "official": "https://teratashizuka.com/",
            "party": "無所属"
        }
    },
    "yamagata": {
        1: {
            "name": "芳賀道也",
            "official": "https://hagamichiya.com",
            "party": "無所属"
        }
    },
    "fukushima": {
        1: {
            "name": "森まさこ",
            "official": "https://morimasako.com",
            "party": "自由民主党"
        }
    },
    "tochigi": {
        1: {
            "name": "高橋克法",
            "official": "https://takahashi-katsunori.jp",
            "party": "自由民主党"
        }
    },
    "gunma": {
        1: {
            "name": "清水真人",
            "official": "https://shimizu-masato.jp",
            "party": "自由民主党"
        }
    },
    "niigata": {
        1: {
            "name": "打越さく良",
            "official": "https://uchikoshi-sakura.jp",
            "party": "立憲民主党"
        }
    },
    "toyama": {
        1: {
            "name": "庭田幸恵",
            "official": "https://niwatayukie.jp",
            "party": "国民民主党"
        }
    },
    "ishikawa": {
        1: {
            "name": "宮本周司",
            "official": "https://miyamoto-shuji.jp",
            "party": "自由民主党"
        }
    },
    "fukui": {
        1: {
            "name": "滝波宏文",
            "official": "https://takinami.info",
            "party": "自由民主党"
        }
    },
    "yamanashi": {
        1: {
            "name": "後藤斎",
            "official": "https://go510.jp/",
            "party": "国民民主党"
        }
    },
    "nagano": {
        1: {
            "name": "羽田次郎",
            "official": "https://hatajiro.com",
            "party": "立憲民主党"
        }
    },
    "gifu": {
        1: {
            "name": "若井敦子",
            "official": "https://atsuko-wakai.com",
            "party": "自由民主党"
        }
    },
    "mie": {
        1: {
            "name": "小島智子",
            "official": "https://kojima-tomoko.jp",
            "party": "立憲民主党"
        }
    },
    "shiga": {
        1: {
            "name": "宮本和宏",
            "official": "https://miyamoto-kazuhiro.jp",
            "party": "自由民主党"
        }
    },
    "nara": {
        1: {
            "name": "堀井巌",
            "official": "https://horii-iwao.jp",
            "party": "自由民主党"
        }
    },
    "wakayama": {
        1: {
            "name": "望月良男",
            "official": "https://mochizukiyoshio.jp",
            "party": "無所属"
        }
    },
    "tottori_shimane": {
        1: {
            "name": "出川桃子",
            "official": "https://degawa-momoko.jp",
            "party": "自由民主党"
        }
    },
    "okayama": {
        1: {
            "name": "小林孝一郎",
            "official": "https://koichiro-k.net",
            "party": "自由民主党"
        }
    },
    "yamaguchi": {
        1: {
            "name": "北村経夫",
            "official": "https://kitamura-tsuneo.jp",
            "party": "自由民主党"
        }
    },
    "kagawa": {
        1: {
            "name": "原田秀一",
            "official": "https://harada-hidekazu.jp",
            "party": "国民民主党"
        }
    },
    "tokushima_kochi": {
        1: {
            "name": "広田一",
            "official": "https://hirota1.jp",
            "party": "無所属"
        }
    },
    "ehime": {
        1: {
            "name": "永江孝子",
            "official": "https://nagae-takako.jp",
            "party": "無所属"
        }
    },
    "saga": {
        1: {
            "name": "山下雄平",
            "official": "https://yamashita-yuhei.jp",
            "party": "自由民主党"
        }
    },
    "nagasaki": {
        1: {
            "name": "古賀友一郎",
            "official": "https://koga-yuichiro.jp",
            "party": "自由民主党"
        }
    },
    "kumamoto": {
        1: {
            "name": "馬場成志",
            "official": "https://baba-seishi.jp",
            "party": "自由民主党"
        }
    },
    "oita": {
        1: {
            "name": "吉田忠智",
            "official": "https://yoshidatadatomo.jp",
            "party": "立憲民主党"
        }
    },
    "miyazaki": {
        1: {
            "name": "山内佳菜子",
            "official": "https://yamakana.net",
            "party": "立憲民主党"
        }
    },
    "kagoshima": {
        1: {
            "name": "尾辻朋実",
            "official": "https://otsujitomomi.com/",
            "party": "無所属"
        }
    },
    "okinawa": {
        1: {
            "name": "高良沙哉",
            "official": "https://takara-sachika.jp/",
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
        print("本当はoutput/manifesto/2025/san/aichi/aichi-1.json")

        print(BULLETIN_DATA_DIR / f"{district}/{district_num}_{name_of_winner}.json")
        # 【修正】公約抽出済みの選挙公報JSON（output/manifesto/tokyo/tokyo-01.json）を読み込む
        bulletin_manifesto_data = load_json(BULLETIN_DATA_DIR / f"{district}/{district_num}_{name_of_winner}.json")
        
        if not web_data or not bulletin_data:
            print(f"スキップ: {filename_base} の基本データ（WEBまたは公報テキスト）が揃っていません。")
            return

        # 統合先の枠組みを作成
        merged = {
            "district": web_data.get("district", ""),
            "district_code": f"2025-san-{district}-{district_num}",
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