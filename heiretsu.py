import os
import json
import time
import google.genai as genai
from pathlib import Path
import fitz
from dotenv import load_dotenv 
import concurrent.futures
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
from tenacity import retry, stop_after_attempt, wait_fixed
from htmldate import find_date
from datetime import datetime

def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else None

load_dotenv()


#official, winner など追加
#読みにくい、改善
#今後printを減らす


#googleのdeep researchに公約を抽出させていたものを、URLのみ抽出に変更
#research1は公式サイトを対象に、research2は公式サイト以外のURLを主に抽出するプロンプトになっています。
#その後URLからウェブの内容を取り、Gemmaが政策を書いているかを、政策であればGeminiが公約か否かを判定します。
#gemmaの方がAPIに余裕があるのでこの形です



#Overlapping,まだ完成していません
#憲法改正が二度出てきたので取り除きたかったですが
#また別の機会にします
def overlapping (district, num):
    
    manifesto_file = Path(f"output/fin/{district}-{num:02d}-final.json")
    print("overlapping start", manifesto_file.exists())
    with open(manifesto_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)

        except Exception as e:
            print("JSON読み込み失敗",e)
            return

        data_str = json.dumps(data["candidates"][0]["manifesto"], ensure_ascii=False)

        prompt= """JsonファイルのManifestoの欄を確認し、重複が存在するかをチェックしてください。
        同じ内容の公約がJsonに重複して存在する場合、is_overlappingはTrueです。存在しない場合、is_overlappingはFalseです。
        同じ文字でなくとも内容が同じであれば重複と見做してください。
        応答は必ず以下のJSON形式のみとし、一切の解説や挨拶、Markdown装飾（```json 等）を禁止します。
        
        {"is_overlapping": true} または {"is_overlapping": false}

        """


        print("AI")
        response = safe_generate_content(
            client=client,
            model='gemini-3.1-flash-lite-preview',
            contents=[prompt, data_str],
            config={
        "response_mime_type": "application/json",
        
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "is_overlapping": {"type": "BOOLEAN"} 
            },
            "required": ["is_overlapping"]
        }
    }
        )


        print("ai fin")
        print(response.text)
        try:
            raw = response.text
            cleaned = clean_json_text(raw)
            json_text = extract_json(cleaned)
            res_data = json.loads(json_text)

            val = res_data.get("is_overlapping")
            if isinstance(val, bool):
                is_overlapping = val
            elif isinstance(val, str):
                is_overlapping = val.lower() == "true"
            #else:
                # is_policy = False
        
        
        except Exception as e:
            is_overlapping = False

        if is_overlapping:
            print(f"重複あり: {district} {num}区")
            overlapping_prompt= """
あなたはJSONデータクリーナーです。
以下のJsonを処理してください。

【目的】
重複している公約を統合し、冗長なデータを削除する。

【重複判定ルール】
- titleが完全一致するものは同一とする
- titleが意味的に同じ（表記ゆれ・略称・同義）ものも同一とする
  例：「憲法への自衛隊明記」と「憲法改正による自衛隊明記」

【統合ルール】
1. 各グループから1件だけ残す
2. 残す基準は以下の優先順：
   (a) sourcesの情報がより新しいもの
   (b) sourcesが複数あるもの
   (c) より具体的な記述のもの
3. reasonは統合して簡潔に1つにまとめる
4. sourcesは最も代表的なもの1つのみ残す
5. quote_textは最も代表的なもの1つのみ残す（任意で最新ソース優先）
6. JSON構造は絶対に変更しない（manifesto以外は触らない）

【出力ルール】
- JSON形式のみ出力する
- 説明文は禁止


            """

            response = safe_generate_content(
                client=client,
                model='gemini-3.1-flash-lite-preview',
                contents=[overlapping_prompt,data_str],
                config={"response_mime_type": "application/json"}
        )


        
            print("呼び出し終了")
            print(response.text)
            


            OUT_DIR = Path("output/fin/")
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out_file = OUT_DIR / f"{district}-{num:02d}-final.json"
            
            result = json.loads(clean_json_text(response.text))
            print(result)

            data["candidates"][0]["manifesto"] = result
            
          # with open(out_file, "w", encoding="utf-8") as f:
           #     json.dump({"manifesto": result}, f, ensure_ascii=False, indent=2)

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


            time.sleep(3)
    with open(manifesto_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)

        except Exception as e:
            print("JSON読み込み失敗",e)
            return

        data_str = json.dumps(data["candidates"][0]["not-manifesto"], ensure_ascii=False)

        prompt= """Jsonファイルのnot-manifestoの欄を確認し、重複が存在するかをチェックしてください。
        同じ内容の公約がJsonに重複して存在する場合、is_overlappingはTrueです。存在しない場合、is_overlappingはFalseです。
        応答は必ず以下のJSON形式のみとし、一切の解説や挨拶、Markdown装飾（```json 等）を禁止します。
        
        {"is_overlapping": true} または {"is_overlapping": false}

        """


        print("AI")
        response = safe_generate_content(
            client=client,
            model='gemma-4-31b-it',
            contents=[prompt, data_str],
            config={
        "response_mime_type": "application/json",
        
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "is_overlapping": {"type": "BOOLEAN"} 
            },
            "required": ["is_overlapping"]
        }
    }
        )


        print("ai fin")
        print(response.text)
        try:
            raw = response.text
            cleaned = clean_json_text(raw)
            json_text = extract_json(cleaned)
            res_data = json.loads(json_text)

            val = res_data.get("is_overlapping")
            if isinstance(val, bool):
                is_overlapping = val
            elif isinstance(val, str):
                is_overlapping = val.lower() == "true"
            #else:
                # is_policy = False
        
        
        except Exception as e:
            is_overlapping = False

        if is_overlapping:
            print(f"重複あり: {district} {num}区")
            overlapping_prompt= """
あなたはJSONデータクリーナーです。
以下のJsonを処理してください。

【目的】
重複している公約を統合し、冗長なデータを削除する。

【重複判定ルール】
- titleが完全一致するものは同一とする
- titleが意味的に同じ（表記ゆれ・略称・同義）ものも同一とする
  例：「憲法への自衛隊明記」と「憲法改正による自衛隊明記」

【統合ルール】
1. 各グループから1件だけ残す
2. 残す基準は以下の優先順：
   (a) sourcesの情報がより新しいもの
   (b) sourcesが複数あるもの
   (c) より具体的な記述のもの
3. reasonは統合して簡潔に1つにまとめる
4. sourcesは最も代表的なもの1つのみ残す
5. quote_textは最も代表的なもの1つのみ残す（任意で最新ソース優先）
6. JSON構造は絶対に変更しない（manifesto以外は触らない）

【出力ルール】
- JSON形式のみ出力する
- 説明文は禁止


            """

            response = safe_generate_content(
                client=client,
                model='gemini-3.1-flash-lite-preview',
                contents=[overlapping_prompt,data_str],
                config={"response_mime_type": "application/json"}
        )


        
            print("呼び出し終了")
            print(response.text)
            


            OUT_DIR = Path("output/fin/")
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out_file = OUT_DIR / f"{district}-{num:02d}-final.json"
            
            result = json.loads(clean_json_text(response.text))
            print(result)

            data["candidates"][0]["not-manifesto"] = result
            
          # with open(out_file, "w", encoding="utf-8") as f:
           #     json.dump({"manifesto": result}, f, ensure_ascii=False, indent=2)

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


            time.sleep(3)





@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def safe_request_get(url):
    res = requests.get(url, timeout=(5, 10))
    res.raise_for_status() 
    return res

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def safe_generate_content(client, model, contents, config):
    return client.models.generate_content(model=model, contents=contents, config=config)





save_lock = threading.Lock()

def save_append_data(out_file, district, num, winner, new_manifesto, new_not_manifesto):
    with save_lock: 
        data = {"district": f"{district}{num}区", "candidates": [{"name": winner, "party": "", "manifesto": [], "not-manifesto": []}]}
        
      
        if out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    pass

        data["candidates"][0]["manifesto"].extend(new_manifesto)
        data["candidates"][0]["not-manifesto"].extend(new_not_manifesto)
        
    
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)




key = os.environ.get('GEMINI_API')

client = genai.Client(api_key= key)

ALL_WINNERS = {
    "tokyo": {
        1: {
            "name": "山田みき",
            "official": "https://www.miki-yamada.com/",
            "party": "自由民主党"
        },
        2: {
            "name": "辻清人",
            "official": "https://k-tsuji.jp/",
            "party": "自由民主党"
        },
    }
}




def clean_json_text(text):
    text = text.strip()
    text = re.sub(r'^```(json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text


def get_manifesto(district,winner,num,party):
    out_file = Path(f"output/fin/{district}-{num:02d}-final.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    final_data = {
        "district": f"東京{num}区",
        "candidates": [
            {
                "name": winner,
                "party": party,
                "manifesto": [],
                "not-manifesto": []
            }
        ]
    }
   


    input_file = f"output/draftresearch/{district}-{num:02d}-final.json"
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            urls = data.get("urls", [])
            print(f"URLリストを読み込みました。合計{len(urls)}件のURLが見つかりました。")
    except Exception as e:
        print(f"URLリストの読み込みに失敗しました: {e}")
        return


    manifesto_url=[]
    def process_url(url):
        print(f"  -> チェック中: {url}")

        if url.lower().endswith(('.pdf', '.doc', '.docx', '.xlsx', '.ppt', '.pptx')):
            print(f"  -> スキップ（PDF/文書ファイル）")
            return

        start = time.time()
        try:
            print(f"  -> ページを取得しています: {url}")
            res = safe_request_get(url)
            


        except Exception as e:
            print(f"  -> ページ取得失敗: {url} | {e}")

            return
        


        
        date=find_date(res.text)
        if date is not None:
            year = int(str(date)[:4])

            if year < 2025:
                print(f"  -> スキップ（{year}年のページ）: {url}")
                return
        
        else:
            print(f"  -> 日付が特定できませんでした（判定を続行）: {url}")



        if "text/html" not in res.headers.get("Content-Type", ""):
            print("  -> HTML以外なのでスキップ:", res.headers.get("Content-Type"))
            return
        print("PAGE 取れた")
        soup = BeautifulSoup(res.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        
        clean_text = soup.get_text(separator=' ', strip=True)

        clean_text = clean_text[:30000]
        print(clean_text)

        
        print("AI")
        prompt= f"""初めにページが{winner}についてのページか考えてください。ページが{winner}についてではなければFalseと返しここで考えを止めてください,{winner}についてであればTrueと返してください。
        {winner}についてである、かつページが2026年以前のものであれば、Falseと返してください。{winner}についてである、さらに2026年であれば、入力されたページの全文を読み込み、公約について少しでも書いているページか判断してください。
    公約を書いていればTrue,書いていなければFalseと返答してください。なお、政策は存在するが、ページではなくメニューページの場合もFalseとしてください。

    応答は必ず以下のJSON形式のみとし、一切の解説や挨拶、Markdown装飾（```json 等）を禁止します。

    {{"is_policy": true}} または {{"is_policy": false}}

    """
        
        response = safe_generate_content(
            client=client,
            model='gemma-4-31b-it',
            contents=[prompt, clean_text],
            config={
        "response_mime_type": "application/json",
        
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "is_policy": {"type": "BOOLEAN"} 
            },
            "required": ["is_policy"]
        }
    }
        )


        print("ai fin")
        try:
            raw = response.text
            cleaned = clean_json_text(raw)
            json_text = extract_json(cleaned)
            res_data = json.loads(json_text)

            val = res_data.get("is_policy")
            if isinstance(val, bool):
                is_policy = val
            elif isinstance(val, str):
                is_policy = val.lower() == "true"
            #else:
                # is_policy = False
        
        
        except Exception as e:
            is_policy = False


        if is_policy:

            print(f"  -> 政策ページを確認。抽出を実行します。")

            organized_text = organize_text(clean_text)

            print(organized_text)

            manifesto_url.append(url)
        
            extracted_data = filter_manifesto(district, winner, num, organized_text, url)
            
            if extracted_data and "candidates" in extracted_data:
                candidate = extracted_data["candidates"][0]
                new_manifesto = candidate.get("manifesto", [])
                new_not_manifesto = candidate.get("not-manifesto", [])
                
                with save_lock:
                    save_append_data(out_file, district, num, winner, new_manifesto, new_not_manifesto)
                    print(f"  -> {url} の保存完了！")
        elif not is_policy:
            return
        else:
            print("format function has error, response is not True or False")
            print(response.text)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_url, urls)
    print(f"finished {district} {num} district")
    print(manifesto_url)




def organize_text(text):
    print("organize text")
    prompt = f"""
    以下のテキストを、政治家の政策抽出に適した形式に整理してください。
    1. 政策ごとに段落を分ける
    2. 不要な空白や改行を削除する
    3. 政策ではなくヘッダーや自己紹介などの部分が存在すればカットしてください


    応答は、整理されたテキストのみを返してください。解説や挨拶、Markdown装飾（```json等）は一切禁止します。
    """
    
    response = safe_generate_content(
        client=client,
        model='gemma-4-31b-it',
        contents=[prompt,text],
        config={"response_mime_type": "text/plain"}
    )
    print("organize text fin")
    print(response.text)
    return response.text.strip()




def filter_manifesto(district,winner,num,input,url):



    PROMPT_FILTER = f"""
# Role
あなたは政治学の専門家かつ、冷徹なデータアナリストです。
提供された「公約候補リスト」を精査し、以下の【排除基準】に1つでも該当するものは**容赦なくnot-manifestoに含めて**ください。



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
- **「動詞」だけで判断しない**: 「導入」「構築」「実施」という言葉があっても、その対象（名詞）が「能力主義」「枠組み」「体制」「環境」などの抽象的な概念である場合は、必ず `not-manifesto` に分類してください。
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





- sourcesを勝手に「提供テキスト」などと捏造せず、必ずurlを記載してください。

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
          "sources": ["{url}"],
          "quote_text": "（断定的な意思表明が含まれる部分を引用）"
        }}
      ],
      "not-manifesto": [
        {{
          "title": "（公約から除外された政策の要約）",
          "reason": "（なぜ公約としてみなせないのか？） ",
          "sources": ["{url}"],
          "quote_text": "（）"
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
          "title": "価格転嫁ガイドラインの法的拘束力強化",
          "reason": "「法的拘束力の付与」という制度的変更（ステータスの変更）を指しており、法改正という具体的なアクションを伴うため。",
          "sources": [
            "{{url}}"
          ],
          "quote_text": "価格転嫁ガイドラインの法的拘束力強化"
        }},
        {{
          "title": "税・社会保険料未納情報の共有および在留審査への活用",
          "reason": "行政機関間での「データ共有」と「審査への反映」という、システムの運用ルール変更を具体的に指しているため。",
          "sources": [
            "{{url}}"
          ],
          "quote_text": "税や社会保険料の未納情報を行政機関間で共有し、その情報を在留審査に活用する"
        }},
        {{
          "title": "国土全域での土地実質的支配者情報の把握と公開",
          "reason": "情報の「公開」および「把握」という、透明性向上のための制度設計を指しており、公報等で実施が確認可能であるため。",
          "sources": [
            "{{url}}"
          ],
          "quote_text": "国土全域で土地等の実質的支配者情報等を把握し国民に公開"
        }},
        {{
          "title": "AI・データサイエンス教育の早期必修化",
          "reason": "公教育における「必修化」という、学習指導要領の変更という具体的かつ観測可能な制度変更を指しているため。",
          "sources": [
            "{{url}}"
          ],
          "quote_text": "AIやデータサイエンスに関する教育を早期から必修化"
        }},
        {{
          "title": "対日外国投資委員会（日本版CFIUS）の創設",
          "reason": "特定の新規制度の設立を明言しており、その存否が客観的に確認可能なため。",
          "sources": [
            "https://go2senkyo.com/seijika/142007"
          ],
          "quote_text": "対日外国投資委員会（日本版CFIUS）を創設"
        }},
        {{
          "title": "住宅ローン減税の床面積要件を緩和",
          "reason": "「床面積要件」という税制上の具体的なパラメータの変更を明示しており、法改正が実施されたかによって検証が可能であるため。",
          "sources": [
            "{{url}}"
          ],
          "quote_text": "住宅ローン減税の床面積要件を緩和"
        }},
        {{
          "title": "日本版DBS（性犯罪歴確認仕組み）の導入",
          "reason": "「日本版DBS」という特定の新規制度の設立を指しており、その存否によって実施の有無を明確に判定できるため。",
          "sources": [
            "{{url}}"
          ],
          "quote_text": "教育・保育・医療等の業務従事者の性犯罪歴を確認する仕組み（日本版DBS）を導入"
        }},
        {{
          "title": "憲法への「自衛隊」明記",
          "reason": "「憲法改正」という最高法規の条文変更という、究極的に具体的かつ断定的な政治アクションを指しているため。",
          "sources": [
            "{{url}}"
          ],
          "quote_text": "憲法改正により「自衛隊」を明記"
        }}
      ]
      "not-manifesto": [
        {{
          "title": "燃料油価格の定額引下げ",
          "reason": "「価格の引下げ」という、数値や制度の裏付けのない目標であり実施の有無が客観的に判断できないため。",
          "sources": [
            "{{URL}}"
          ],
          "quote_text": "燃料油価格の定額引下げ"
        }},
        {{
          "title": "高等教育の授業料等減免の対象拡大",
          "reason": "対象拡大、は具体的にどの変数を変更するのかが不明（世帯年収の基準、多子家庭への支援の増加など） ",
          "sources": ["https://miki-yamada.com/blog/12591.html"],
          "quote_text": "高等教育の授業料等減免の対象拡大"
        }}
        {{
          "title": "都心部における固定資産税や相続税などについて、税負担の軽減",
          "reason": "「軽減」とあるが何を変更することにより税負担を軽減させるのかが不明。",
          "sources": ["https://miki-yamada.com/blog/12601.html"],
          "quote_text": "都心部における固定資産税や相続税などについて、税負担の軽減"
        }}
        {{
          "title": "福祉分野を含む全産業の労務費転嫁と処遇改善を後押しします",
          "reason": "「後押し」の有無は客観的に判断することができない。また、「後押し」は結果へのコミットではない。",
          "sources": ["https://miki-yamada.com/blog/12572.html"],
          "quote_text": "福祉分野を含む全産業の労務費転嫁と処遇改善を後押しします"
        }}
        {{
          "title": "保険料と公費負担のバランスを見直し",
          "reason": "「バランスの見直し」が何を意味するのか不明瞭であり、具体的にどの変数をどのように変更するのかが示されていない。また、「見直し」が実際に行われたかどうかの判断も主観的であるうえ、結果へのコミットではないため。",
          "sources": ["https://miki-yamada.com/blog/12587.html"],
          "quote_text": "保険料と公費負担のバランスを見直し、全世代で公平に支える財源を安定させます"
        }}
        {{
          "title": "下請Gメンや公正取引委員会の人材（定員）の拡充",
          "reason": "「拡充」の有無が客観的に判断できない。また、水準が不明であるため。",
          "sources": [
            "{{url}}"
          ],
          "quote_text": "下請Gメンや公正取引委員会の人材拡充"
        }},

      ]
    }}
  ]
}}

"""



    print(f"started filtering for manifesto, {winner} in {district} {num} district")
    print("呼び出し")
    print("API call start")
    response = safe_generate_content(
        client=client,
        
        #model='gemma-4-31b-it',
        model='gemini-3.1-flash-lite-preview',
        contents=[PROMPT_FILTER,input],
        config={"response_mime_type": "application/json"}
    )
    print("呼び出し終了")
    time.sleep(3)
    print(response)
    try:
        return json.loads(response.text)
    except Exception as e:
        return None




def process(district,winner,num,official,party):
  #  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
   #     future1 = executor.submit(research1, district, winner, num, official)
    #    future2 = executor.submit(research2, district, winner, num)
        
        
      #  concurrent.futures.wait([future1, future2])
    #research1(district,winner,num)
    #research2(district,winner,num)
    get_manifesto(district, winner, num,party)
    overlapping(district, num)
    overlapping(district, num)


'''if __name__ == "__main__":
    for district, winners in ALL_WINNERS.items():
        for num, winner_name in winners.items():
            winner=winner_name
            research(district,winner,num)
            filter(district, winner ,num)
    '''


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures=[]
        for district, winners in ALL_WINNERS.items():
            for num, info in winners.items():
                name = info["name"]
                official = info["official"]
                party= info["party"]
                executor.submit(process, district, name, num, official,party)

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"スレッド実行中にエラーが発生しました: {exc}")