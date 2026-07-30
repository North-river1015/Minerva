#openrouterへ変更

import os
import json
import time
from pathlib import Path
import fitz
from dotenv import load_dotenv 
import concurrent.futures
import requests
import re
from urllib.parse import urljoin
import threading
from tenacity import retry, stop_after_attempt, wait_fixed
from openrouter import OpenRouter

load_dotenv()

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





api_key_openrouter = os.environ.get('OPENROUTER')
url = os.environ.get('URL')

@retry(stop=stop_after_attempt(5), wait=wait_fixed(5))
def safe_generate_content(client, model, contents, config):
    full_text = "\n\n".join(str(c) for c in contents)

    with OpenRouter(api_key=api_key_openrouter) as client:
        response = client.chat.send(
            model="z-ai/glm-5.2",
            messages=[{"role": "user", "content": full_text}],
            response_format=config ,
            server_url=url,
            #max_tokens=10000 
        )
        
        content = response.choices[0].message.content
        print(content)
        

        class SimpleResponse:
            def __init__(self, text):
                self.text = text
        return SimpleResponse(content)





  



def filter_manifesto(district,winner,num):



    PROMPT_FILTER = f"""
# Role
あなたは政治学の専門家かつ、冷徹なデータアナリストです。
提供された「公約候補リスト」を精査し、以下の【排除基準】に1つでも該当するものは**容赦なく、即座にnot-manifestoに含めて**ください。
排除基準に当てはまらない政策は、【判定基準】に従って厳格にmanifestoかnot-manifestoのどちらかに分類してください。

# 重要!!!!排除基準（これらは公約ではないです）
- 抽象的なスローガン（例：日本を元気にする、都民の暮らしを守る）
- 単なる現状認識（例：少子化は国難である）
- 挨拶や感謝（例：皆様のおかげで当選できました）
- 曖昧な意気込み（例：しっかりと取り組んでまいります）
- 他者のコメントの引用など、{winner}自身の政策表明とみなせないもの
-  **手続き・意欲表現**: 「検討」「議論」「調査」「推進」「目指す」「努める」が含まれるものは、内容に関わらず公約ではありません。
- **現状維持**: 既に実施中の政策の継続や再確認（例：今年度予算の着実な実施や「厳正な対処」など）。例え具体的であっても即座に却下。
    ただし、時限立法など廃止が制度的に予見される際は公約として扱う。
- **利益誘導**: 特定地域（例：〇〇駅、〇〇バイパス）への利益還元。
- **「動詞」だけで判断しない**: 「導入」「構築」「実施」という言葉があっても、その対象（名詞）が「能力主義」「枠組み」「体制」「環境」「安定財源の確保」などの抽象的な概念である場合は、必ず `not-manifesto` に分類してください。
- **固有名詞の罠に注意**: 既存の法律名が入っていても、そのアクションが「徹底」「推進」「周知」であれば、それは公約ではなく「努力目標」です。既存の法律を「厳正に執行する」「徹底する」という内容は、行政の当然の責務であり、政治的な「新規公約」とはみなさない。
- **変数の有無を再確認**: その公約が達成されたかどうかを、第三者が「数字」や「条文の有無」で100%客観的に判定できるか自問自答してください。
- **動詞チェック**: 「徹底」「強化」「促進」「後押し」「見直し」「着手」が含まれるものは、直ちに却下。

# 判定基準（すべて満たすもののみ公約です）
1. 【具体的かつ観測可能】: 「〜の検討」は即座に削除。「〜法の改正」「〜予算の確保」など、後に達成度が検証できるもの。
2. 【政治的行動への意思】: 「〜を目指す」「〜したい」「努力する」は即座に削除。「〜を導入する」「〜を改正する」といった**断定的なコミットメント**のみを残す。
3. 【公共性】: 特定地域への利益誘導ではなく、全国的な制度変更や法的措置であること。
4. {winner}または信頼できるソースによるものであること。

    1. **数値・条件の変更**: 「消費税を0%に減税する」、「5万円の給付を行う」など。
    2. **制度のステータス変更**: 「法的拘束力の付与」「必修化」「情報の公開」「システム共有」など。
    3. **新規制度の設立**: 「日本版DBSの導入」「新法の制定」など。
上記1-3はコミットメントとして扱う。




# Task
上記基準をクリアした「真の公約」のみを抽出し、以下のJSON形式で出力してください。
JSON以外の文字、解説、Markdownの装飾（```json等）は一切禁止します。

ステップ1：各候補の政策について、Rubric（判定基準）に照らして「採択」か「却下」かを判断し、その理由を1行でメモしてください。
ステップ2：合格したもの（採択されたもの）だけを、最終的なJSON形式でmanifestoの欄にまとめてください。

# 思考の出力例(reasonの欄に出力)
- ✅ 採択：消費税を0%に減税（具体的な数値で実施の有無は明確）
- ✅ 採択：消費税をゼロに減税（実施の有無が判断できる、変数が明確）
- ✅ 採択：日本版DBSの「導入」（Yes/Noが明確な具体的行動）
- ✅ 採択：価格転嫁ガイドラインの「法的拘束力の付与」（制度のステータス変更）
- ✅ 採択：再エネ賦課金の徴収停止（制度の停止という具体的なステータス変更）
- ✅ 採択：所得税減税（法改正の有無によって実行されたかが客観的に判断可能）
- ✅ 採択：自衛官の給与改善（法改正の有無によって実行されたかが客観的に判断可能）
- ❌ 却下：下請Gメンの「執行体制」を拡充（「体制」は中身が不透明で検証不能）
- ❌ 却下：省エネ基準適合義務化を着実に実施（「着実に実施」であり新たな政治的アクションではなく既存の制度の実施を再度述べるのみであるため）
- ❌ 却下：〜を検討、推進、目指す（単なる手続き表現）
- ❌ 却下：下請Gメンの「人材（定員）」を拡充（「拡充」の有無は恣意的、明確にYes/Noで判断できない）
- ❌ 却下：電気代の値下げ（どの制度をどう操作して実現するかが不明）
- ❌ 却下：公務員の人事制度を能力主義・実力主義へ移行（何を指しているのかが不明、曖昧で定義されていない内容。客観的に判断できない。）

操作する変数が特定されているものだけが「公約」です。


※重要：manifestoは必ず「オブジェクトの配列（リスト形式）」にしてください。
※重要：キー名に日本語や具体的な公約内容を入れず、必ず上記の見本と同じキー名（title, sources, quote_text）を使用してください。
見つかった全ての公約を、上記のJSONと同じ構造でリスト内に追加してください。
JSONとして正しい形で返してください。
一つの文章に複数の要素が含まれる場合、**それぞれを分解**し、独立して要件を満たす部分のみを公約として扱う。


# JSONフォーマット

"manifesto": [
{{
    "title": "（具体的施策の要約）",
    "reason": "（なぜ公約なのか？）",
    "quote_text": "（断定的な意思表明が含まれる部分を引用）"
}}
],
"not-manifesto": [
{{
    "title": "（公約から除外された政策の要約）",
    "reason": "（なぜ公約としてみなせないのか？） ",
    "quote_text": "（）"
}}
]




リスポンスの例：

"manifesto": [
{{
    "title": "価格転嫁ガイドラインの法的拘束力強化",
    "reason": "「法的拘束力の付与」という制度的変更（ステータスの変更）を指しており、法改正という具体的なアクションを伴うため。",
    "quote_text": "価格転嫁ガイドラインの法的拘束力強化"
}},
{{
    "title": "税・社会保険料未納情報の共有および在留審査への活用",
    "reason": "行政機関間での「データ共有」と「審査への反映」という、システムの運用ルール変更を具体的に指しているため。",
    "quote_text": "税や社会保険料の未納情報を行政機関間で共有し、その情報を在留審査に活用する"
}},
{{
    "title": "国土全域での土地実質的支配者情報の把握と公開",
    "reason": "情報の「公開」および「把握」という、透明性向上のための制度設計を指しており、公報等で実施が確認可能であるため。",
    "quote_text": "国土全域で土地等の実質的支配者情報等を把握し国民に公開"
}},
{{
    "title": "AI・データサイエンス教育の早期必修化",
    "reason": "公教育における「必修化」という、学習指導要領の変更という具体的かつ観測可能な制度変更を指しているため。",
    "quote_text": "AIやデータサイエンスに関する教育を早期から必修化"
}},
{{
    "title": "対日外国投資委員会（日本版CFIUS）の創設",
    "reason": "特定の新規制度の設立を明言しており、その存否が客観的に確認可能なため。",
    "quote_text": "対日外国投資委員会（日本版CFIUS）を創設"
}},
{{
    "title": "住宅ローン減税の床面積要件を緩和",
    "reason": "「床面積要件」という税制上の具体的なパラメータの変更を明示しており、法改正が実施されたかによって検証が可能であるため。",
    "quote_text": "住宅ローン減税の床面積要件を緩和"
}},
{{
    "title": "日本版DBS（性犯罪歴確認仕組み）の導入",
    "reason": "「日本版DBS」という特定の新規制度の設立を指しており、その存否によって実施の有無を明確に判定できるため。",
    "quote_text": "教育・保育・医療等の業務従事者の性犯罪歴を確認する仕組み（日本版DBS）を導入"
}},
{{
    "title": "憲法への「自衛隊」明記",
    "reason": "「憲法改正」という最高法規の条文変更という、究極的に具体的かつ断定的な政治アクションを指しているため。",
    "quote_text": "憲法改正により「自衛隊」を明記"
}}
]
"not-manifesto": [
{{
    "title": "燃料油価格の定額引下げ",
    "reason": "「価格の引下げ」という、数値や制度の裏付けのない目標であり実施の有無が客観的に判断できないため。",
    "quote_text": "燃料油価格の定額引下げ"
}},
{{
    "title": "高等教育の授業料等減免の対象拡大",
    "reason": "対象拡大、は具体的にどの変数を変更するのかが不明（世帯年収の基準、多子家庭への支援の増加など） ",
    "quote_text": "高等教育の授業料等減免の対象拡大"
}}
{{
    "title": "都心部における固定資産税や相続税などについて、税負担の軽減",
    "reason": "「軽減」とあるが何を変更することにより税負担を軽減させるのかが不明。",
    "quote_text": "都心部における固定資産税や相続税などについて、税負担の軽減"
}}
{{
    "title": "福祉分野を含む全産業の労務費転嫁と処遇改善を後押しします",
    "reason": "「後押し」の有無は客観的に判断することができない。また、「後押し」は結果へのコミットではない。",
    "quote_text": "福祉分野を含む全産業の労務費転嫁と処遇改善を後押しします"
}}
{{
    "title": "保険料と公費負担のバランスを見直し",
    "reason": "「バランスの見直し」が何を意味するのか不明瞭であり、具体的にどの変数をどのように変更するのかが示されていない。また、「見直し」が実際に行われたかどうかの判断も主観的であるうえ、結果へのコミットではないため。",
    "quote_text": "保険料と公費負担のバランスを見直し、全世代で公平に支える財源を安定させます"
}}
{{
    "title": "下請Gメンや公正取引委員会の人材（定員）の拡充",
    "reason": "「拡充」の有無が客観的に判断できない。また、水準が不明であるため。",
    "quote_text": "下請Gメンや公正取引委員会の人材拡充"
}},

]


"""
    #num = f"{num:02d}"
    print(num)
    manifesto_file= Path(f"data/ai_output/2022/san/{district}/{num}_{winner}.json")
    print(manifesto_file)
    with open(manifesto_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)

        except Exception as e:
            print("JSON読み込み失敗",e)
            return
        
    print(data)
    print(f"started filtering for manifesto, {winner} in {district} {num} district")
    print("呼び出し")
    print("API call start")
    response = safe_generate_content(
        client=None,
        #model='gemma-4-31b-it',
        model='gemini-3.1-flash-lite',
        contents=[PROMPT_FILTER,data],
        config = {
    "type": "json_schema",
    "json_schema": {
        "name": "manifesto_schema", # スキーマ名（英数字のみ）
        "strict": True,               # スキーマを厳格に守らせる設定
        "schema": {
            "type": "object",
            "properties": {
                "manifesto": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "具体的施策の要約"},
                            "reason": {"type": "string", "description": "なぜ公約なのか？"},
                            "quote_text": {"type": "string", "description": "断定的な意思表明が含まれる部分を引用"}
                        },
                        "required": ["title", "reason", "quote_text"],
                        "additionalProperties": False
                    }
                },
                "not-manifesto": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "公約から除外された政策の要約"},
                            "reason": {"type": "string", "description": "なぜ公約としてみなせないのか？"},
                            "quote_text": {"type": "string", "description": "引用部分"}
                        },
                        "required": ["title", "reason", "quote_text"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["manifesto", "not-manifesto"],
            "additionalProperties": False
        }
    }
}
    )
    print("呼び出し終了")
    time.sleep(3)
    print(response)
    final_data=json.loads(response.text)

    out_file = Path(f"output/manifesto/2022/san/{district}/{district}-{num}.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    print("start")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures=[]
        for district, winners in ALL_WINNERS.items():
            for num, info in winners.items():
                name = info["name"]
                party= info["party"]
                f=executor.submit(filter_manifesto, district, name, num)
                futures.append(f)
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"スレッド実行中にエラーが発生しました: {exc}")

