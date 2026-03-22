
import os
import json
import time
import google.genai as genai
from pathlib import Path
import fitz
from dotenv import load_dotenv 

load_dotenv()


key = os.environ.get('GEMINI_API')

client = genai.Client(api_key= key)

ALL_WINNERS = {
    'tokyo': {
        1: '山田みき',
        2: '辻清人',
        3: '石原宏高',
        4: '平将明',
        5: '若宮健嗣',
        6: '畦元将吾',
        7: '丸川珠代',
        8: '門寛子',
        9: '菅原一秀',
        10: '鈴木隼人',
        11: '下村博文',
        12: '高木啓',
        13: '土田慎',
        14: '松島みどり',
        15: '大空幸星',
        16: '大西洋平',
        17: '平沢勝栄',
        18: '福田かおる',
        19: '松本洋平',
        20: '木原誠二',
        21: '小田原潔',
        22: '伊藤達也',
        23: '川松真一朗',
        24: '萩生田光一',
        25: '井上信治',
        26: '今岡植',
        27: '黒崎祐一',
        28: '安藤高夫',
        29: '長澤興祐',
        30: '長島昭久'
    }
}


def research():
    for district, winners in ALL_WINNERS.items():
        for num, winner_name in winners.items():
            winner=winner_name
            PROMPT = f"""
            1. 応答の開始から終了まで、一切の説明文、挨拶、レポート、Markdown装飾（```json等）を禁止します。
            2. 出力は、以下のJSONフォーマットに従った純粋なデータ構造のみとしてください。
            3. もしレポートや文章が含まれた場合、システムエラーとして処理されます。
            
            # Role
            あなたは政治学とデータ分析に精通したJSONデータ抽出エンジンです。
            指定された政治家の「公約」を、以下の【判定基準】に従って客観的に抽出してください。

            # 判定基準
            以下の3条件をすべて満たす記述のみを「公約」として抽出してください：
            1. 【具体的かつ観測可能】: 数値目標、法律の制定・改正、予算措置など、達成度が客観的に検証できること。
            2. 【政治的行動への意思】: 「実施する」「導入する」「改正する」などのコミットメントがあること（「検討する」「目指す」は除外）。
            3. 【公共性】: 特定の地域への利益誘導ではなく、制度や全国的な波及効果を主目的としていること。


            # Task
            1. Google Search Groundingを使用し、対象者の[公式サイト][公式ブログ][信頼できるニュースメディア][議事録]を横断的に分析し、公約を漏れなく抽出してください。
            2. 抽出した公約を、必ず以下のJSONフォーマットの形式でリスト化してください。発見した公約は全てJsonにまとめてください。全ての関連ウェブサイトを分析してください。
            3. 今回の選挙・選挙区の考察や挨拶などは不要のため、プロンプトに対しJsonのみで返答してください。レポートを求めていたのではないで、あくまで公約の抽出が目的です。公約以外の情報は一切含めないでください。
            4. マークダウンのコードブロック（```json など）は使用せず、純粋なJSON文字列の波括弧 から終了の波括弧  までのみを出力してください。
            - JSON以外の説明文、挨拶、Markdownの装飾は一切含めず、純粋なJSON文字列のみを返してください。
            - プロフィールや挨拶などは省いてください。

        # Target
            対象議員：{winner}
            対象期間：2026年2月の衆議院選挙に際して、{winner}個人が発表した**『選挙公報』『政見放送』『マニフェスト』**などをソースとしてください。
            



        JSONフォーマット：

        {{
        "district": "東京{num}区",
        "candidates": [
            {{
            "name": "{winner}",
            "party": "所属政党名をここに記入",
            "manifesto": [
                {{
                "title": "公約の要約タイトルをここに記入",
                "sources": ["ソースへのURLをここに記入"],
                "quote_text": "出典元から該当部分を100文字程度引用"
                }},
                {{
                "title": "2つ目の公約タイトル",
                "sources": ["URL"],
                "quote_text": "引用テキスト"
                }},
                {{
                "title": "3つ目の公約タイトル",
                "sources": ["URL"],
                "quote_text": "引用テキスト"
                }}
            ]
            }}
        ]
        }}

        ※重要：manifestoは必ず「オブジェクトの配列（リスト形式）」にしてください。
        ※重要：キー名に日本語や具体的な公約内容を入れず、必ず上記の見本と同じキー名（title, sources, quote_text）を使用してください。
        見つかった全ての公約を、上記のJSONと同じ構造でリスト内に追加してください。
            
            """


            print(f"started researching {winner} in {district} {num} district")

            interaction = client.interactions.create(
                input=PROMPT,
                agent='deep-research-pro-preview-12-2025',
                background=True
            )

            print(f"Research started: {interaction.id}")

            while True:
                interaction = client.interactions.get(interaction.id)
                if interaction.status == "completed":
                    print("research completed")
                    final_result = interaction.outputs[-1].text
                    break

                elif interaction.status == "failed":
                    print(f"Research failed: {interaction.error}")
                    break
                time.sleep(10)

            OUT_DIR = Path("output/research/")
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out_file = OUT_DIR / f"{district}-{num:02d}.json"
                    

            with open(out_file, "w", encoding="utf-8") as f:
                    # Use the variable we extracted above
                    f.write(final_result)
if __name__ == "__main__":
    research()