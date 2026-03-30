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
    }
}

def research(district,winner,num):
    PROMPT = f"""
    1. 応答の開始から終了まで、一切の説明文、挨拶、レポート、Markdown装飾（```json等）を禁止します。
    2. 出力は、以下のJSONフォーマットに従った純粋なデータ構造のみとしてください。
    3. もしレポートや文章が含まれた場合、システムエラーとして処理されます。
    
    # Role
    あなたは政治学とデータ分析に精通した、極めて執念深いJSONデータ抽出エンジンです。
    指定された政治家の政策を抽出してください。
    具体的かつ公共性のある公約と思われる記述を、出典URLとセットで漏れなくリストアップしてください。
    後で選別するため、少しでも「具体的」と感じるものはすべて含めてください。
    「実現可能性」や「重要度」をあなたが判断して**切り捨てることを厳禁**します。
    具体的であれば、たとえ小さな項目であっても全てリストアップしてください。最低でも20〜30件の公約を抽出することを目指してください。複数ページから政策を取り出すだけで、満足しないでください。しつこく執念深く検索を続けてください。
   
     # Task
    1. Google Search Groundingを使用し、after:2025-03-30 の対象者の公式ウェブサイトや公式ブログ、報道機関によるアンケートなどを分析し、公約を漏れなく抽出してください。「公約」とのページ以外にも、ブログの欄などに政策がある可能性もあるため、公式ウェブサイトのリンクから政策がある可能性があるページをクロールしてください。公式ウェブサイトに関してはサイトマップを執念深く確認してください。
    2. 以下の4カテゴリをそれぞれ個別に検索し、各カテゴリ最低5件以上（合計20件以上）を抽出してください。
    経済・税制・物価高 after:2025-03-30
    外交・安保・憲法 after:2025-03-30
    教育・子育て・デジタル after:2025-03-30
    厚生労働・医療・地域課題 after:2025-03-30
    3. 抽出した公約を、必ず以下のJSONフォーマットの形式でリスト化してください。発見した公約は全てJsonにまとめてください。全ての関連ウェブサイトを分析してください。
    4. 今回の選挙・選挙区の考察や挨拶などは不要のため、プロンプトに対しJsonのみで返答してください。レポートを求めていません。あくまで公約の抽出が目的です。公約以外の情報は一切含めないでください。
    5. マークダウンのコードブロック（```json など）は使用せず、純粋なJSON文字列の波括弧 から終了の波括弧  までのみを出力してください。


    - JSON以外の説明文、挨拶、Markdownの装飾は一切含めず、純粋なJSON文字列のみを返してください。
    - プロフィールや挨拶などは省いてください。
    - 公式サイトの**全階層を巡回**し、異なるURLに分散している政策を統合してください。3ページ程度で探索を終了せず、しつこく執念深く検索してください。
    - 公式サイトの検索の際は、検索の際は、site:（公式サイトのリンク） 政策 after:2025-03-30 や site:（公式サイトのリンク） 公約 after:2025-03-30 などのサイト内検索クエリを自ら生成して実行し、ページの見落としがないか二重にチェックしてください。
   


# Target
    対象議員：{winner}
    対象期間：2026年2月の衆議院選挙に際して、{winner}個人が発表した内容をソースとしてください。
    



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

※重要：３つ以上ある際は全てjsonで乗せてください。
manifestoは必ず「オブジェクトの配列（リスト形式）」にしてください。
※重要：キー名に日本語や具体的な公約内容を入れず、必ず上記の見本と同じキー名（title, sources, quote_text）を使用してください。
見つかった全ての公約を、上記のJSONと同じ構造でリスト内に追加してください。
JSONとして正しい形で返してください。
quoteでは要約をせず、必ず出典元から該当部分を100文字程度引用してください。
titleでも要約をせず、必ず出典元から語尾も含めて抜き出してください。 


    """



    interaction = client.interactions.create(
        input=PROMPT,
        agent='deep-research-pro-preview-12-2025',
        background=True
    )

    print(f"started researching {winner} in {district} {num} district")

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
    out_file = OUT_DIR / f"{district}-{num:02d}-prev.json"
            

    with open(out_file, "w", encoding="utf-8") as f:
            f.write(final_result)



def filter(district,winner,num):
        
    deep_research_output=open(f"output/research/{district}-{num:02d}-prev.json").read()

    PROMPT_FILTER = f"""
# Role
あなたは政治学の専門家かつ、冷徹なデータアナリストです。
提供された「公約候補リスト」を精査し、以下の【排除基準】に1つでも該当するものは**容赦なく削除**してください。

# 判定基準（すべて満たすもののみ残す）
1. 【具体的かつ観測可能】: 「〜の検討」は即座に削除。「〜法の改正」「〜予算の確保」など、後に達成度が検証できるもの。
2. 【政治的行動への意思】: 「〜を目指す」「〜したい」「努力する」は即座に削除。「〜を導入する」「〜を改正する」といった**断定的なコミットメント**のみを残す。
3. 【公共性】: 特定地域への利益誘導ではなく、全国的な制度変更や法的措置であること。

    1. **数値・条件の変更**: 基礎控除の引き上げ、床面積要件の緩和、定員の拡充など。
    2. **制度のステータス変更**: 「法的拘束力の付与」「必修化」「情報の公開」「システム共有」など。
    3. **新規制度の設立**: 「日本版DBSの導入」「新法の制定」など。
上記１−3はコミットメントとして扱う。

# 排除基準（これらは公約ではないので削除してください）
- 抽象的なスローガン（例：日本を元気にする、都民の暮らしを守る）
- 単なる現状認識（例：少子化は国難である）
- 挨拶や感謝（例：皆様のおかげで当選できました）
- 曖昧な意気込み（例：しっかりと取り組んでまいります）

# Input Data (Deep Researchの結果)
{deep_research_output}

# Task
上記基準をクリアした「真の公約」のみを抽出し、以下のJSON形式で出力してください。
JSON以外の文字、解説、Markdownの装飾（```json等）は一切禁止します。

ステップ1：各候補の政策について、Rubric（判定基準）に照らして「採択」か「却下」かを判断し、その理由を1行でメモしてください。
ステップ2：合格したもの（採択されたもの）だけを、最終的なJSON形式にまとめてください。

# 思考の出力例(reasonの欄に出力)
- ✅ 採択：住宅ローン減税の「床面積要件」を緩和（単一変数の操作）
- ✅ 採択：下請Gメンの「人材（定員）」を拡充（統計で確認可能な数値）
- ✅ 採択：日本版DBSの「導入」（Yes/Noが明確な具体的行動）
- ❌ 却下：所得税減税（変数が不特定）
- ❌ 却下：下請Gメンの「執行体制」を拡充（体制は中身が不透明で検証不能）
- ❌ 却下：〜を検討、推進、目指す（単なる手続き表現）
操作する変数が特定されているものだけが「公約」です。


※重要：manifestoは必ず「オブジェクトの配列（リスト形式）」にしてください。
※重要：キー名に日本語や具体的な公約内容を入れず、必ず上記の見本と同じキー名（title, sources, quote_text）を使用してください。
見つかった全ての公約を、上記のJSONと同じ構造でリスト内に追加してください。
JSONとして正しい形で返してください。
一つの文章に複数の要素が含まれる場合、**それぞれを分解**し、独立して要件を満たす部分のみを公約として扱う。


# 【排除基準】
1. **手続き・意欲表現**: 「検討」「議論」「調査」「推進」「目指す」「努める」が含まれるものは、内容に関わらず即座に削除。
2. **現状維持**: 既に実施中の政策の継続や再確認（例：今年度予算の着実な実施）。
3. **利益誘導**: 特定地域（例：〇〇駅、〇〇バイパス）への利益還元。
4. **スローガン**: 「日本を再生」「暮らしを守る」などの精神論。


# JSONフォーマット
{{
  "district": "東京{num}区",
  "candidates": [
    {{
      "name": "{winner}",
      "party": "政党名",
      "manifesto": [
        {{
          "title": "（具体的施策の要約）",
          "reason": " ",
          "sources": ["（URL）"],
          "quote_text": "（断定的な意思表明が含まれる部分を引用）"
        }}
      ]
    }}
  ]
}}



リスポンスの例：
{{
  "district": "東京1区",
  "candidates": [
    {{
      "name": "山田みき",
      "party": "自由民主党",
      "manifesto": [
        {{
          "title": "燃料油価格の定額引下げ",
          "reason": "「価格の引下げ」という、家計や企業に直結する具体的な数値（価格）を操作する政策であり、達成の是非が統計的に確認可能であるため。",
          "sources": [
            "（URL）"
          ],
          "quote_text": "燃料油価格の定額引下げ"
        }},
        {{
          "title": "価格転嫁ガイドラインの法的拘束力強化",
          "reason": "「法的拘束力の付与」という制度的変更（ステータスの変更）を指しており、法改正という具体的なアクションを伴うため。",
          "sources": [
            "（URL）"
          ],
          "quote_text": "価格転嫁ガイドラインの法的拘束力強化"
        }},
        {{
          "title": "下請Gメンや公正取引委員会の人材（定員）の拡充",
          "reason": "行政組織の「定員（人数）」という、予算書や組織図で客観的に確認可能なリソースの投入を明言しているため。",
          "sources": [
            "（URL）"
          ],
          "quote_text": "下請Gメンや公正取引委員会の人材拡充"
        }},
        {{
          "title": "税・社会保険料未納情報の共有および在留審査への活用",
          "reason": "行政機関間での「データ共有」と「審査への反映」という、システムの運用ルール変更を具体的に指しているため。",
          "sources": [
            "（URL）"
          ],
          "quote_text": "税や社会保険料の未納情報を行政機関間で共有し、その情報を在留審査に活用する"
        }},
        {{
          "title": "国土全域での土地実質的支配者情報の把握と公開",
          "reason": "情報の「公開」および「把握」という、透明性向上のための制度設計を指しており、公報等で実施が確認可能であるため。",
          "sources": [
            "（URL）"
          ],
          "quote_text": "国土全域で土地等の実質的支配者情報等を把握し国民に公開"
        }},
        {{
          "title": "AI・データサイエンス教育の早期必修化",
          "reason": "公教育における「必修化」という、学習指導要領の変更という具体的かつ観測可能な制度変更を指しているため。",
          "sources": [
            "（URL）"
          ],
          "quote_text": "AIやデータサイエンスに関する教育を早期から必修化"
        }},
        {{
          "title": "住宅ローン減税の床面積要件を緩和",
          "reason": "「床面積要件」という税制上の具体的な数値基準（パラメータ）の変更を明示しており、検証が極めて容易であるため。",
          "sources": [
            "（URL）"
          ],
          "quote_text": "住宅ローン減税の床面積要件を緩和"
        }},
        {{
          "title": "日本版DBS（性犯罪歴確認仕組み）の導入",
          "reason": "「日本版DBS」という特定の新規制度の設立を指しており、その存否によって実施の有無を明確に判定できるため。",
          "sources": [
            "（URL）"
          ],
          "quote_text": "教育・保育・医療等の業務従事者の性犯罪歴を確認する仕組み（日本版DBS）を導入"
        }},
        {{
          "title": "憲法への「自衛隊」明記",
          "reason": "「憲法改正」という最高法規の条文変更という、究極的に具体的かつ断定的な政治アクションを指しているため。",
          "sources": [
            "（URL）"
          ],
          "quote_text": "憲法改正により「自衛隊」を明記"
        }}
      ]
    }}
  ]
}}

"""
    print(f"started filtering for manifesto, {winner} in {district} {num} district")
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        contents=PROMPT_FILTER,
        config={"response_mime_type": "application/json"}
    )
    final_json = response.text
    out_file = f"output/data/{district}-{num:02d}-prev.json"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(final_json)            
        print("保存しました。")
    


if __name__ == "__main__":
    for district, winners in ALL_WINNERS.items():
        for num, winner_name in winners.items():
            winner=winner_name
            research(district,winner,num)
            filter(district, winner ,num)