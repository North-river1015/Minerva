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
    
    manifesto_file = Path(f"output/finaldata/{district}-{num:02d}-final.json")
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
            


            OUT_DIR = Path("output/final/")
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out_file = OUT_DIR / f"{district}-{num:02d}-overlapping.json"
            
            result = json.loads(clean_json_text(response.text))
            print(result)

            data["candidates"][0]["manifesto"] = result
            
          # with open(out_file, "w", encoding="utf-8") as f:
           #     json.dump({"manifesto": result}, f, ensure_ascii=False, indent=2)

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


            time.sleep(5)





@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def safe_request_get(url):
    res = requests.get(url, timeout=(5, 10))
    res.raise_for_status() 
    return res

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def safe_generate_content(client, model, contents, config):
    return client.models.generate_content(model=model, contents=contents, config=config)





save_lock = threading.Lock()

def wait_for_research(client, interaction_id):
    while True:
        interaction = client.interactions.get(interaction_id)
        if interaction.status == "completed":
            print("research completed")
            final_result = interaction.outputs[-1].text
            return final_result

        elif interaction.status == "failed":
            print(f"Research failed: {interaction.error}")
            break
        time.sleep(10)

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

        2: {
            "name": "辻清人",
            "official": "https://k-tsuji.jp/",
            "party": "自由民主党"
        },
    }
}


'''    
 3: {
            "name": "石原宏高",
            "official": "https://www.ishihara-hirotaka.com/",
            "party": "自由民主党"
        },
      4: {
            "name": "平将明",
            "official": "https://www.taira-m.jp/",
            "party": "自由民主党"
        },
        5: {
            "name": "若宮健嗣",
            "official": "https://k-wakamiya.com/",
            "party": "自由民主党"
        },
        6: {
            "name": "畦元将吾",
            "official": "https://azemoto.jp/",
            "party": "自由民主党"
        },
        7: {
            "name": "丸川珠代",
            "official": "https://t-marukawa.jp/",
            "party": "自由民主党"
        },
        8: {
            "name": "門寛子",
            "official": "https://kado-hiroko.jp/",
            "party": "自由民主党"
        },
        9: {
            "name": "菅原一秀",
            "official": "https://isshu.online/",
            "party": "自由民主党"
        },
        10: {
            "name": "鈴木隼人",
            "official": "https://www.suzukihayato.jp/",
            "party": "自由民主党"
        },
        11: {
            "name": "下村博文",
            "official": "https://www.hakubun.biz/",
            "party": "自由民主党"
        },
        12: {
            "name": "高木啓",
            "official": "https://takagi-kei.com/",
            "party": "自由民主党"
        },
        13: {
            "name": "土田慎",
            "official": "http://www.tsuchida-shin.jp/",
            "party": "自由民主党"
        },
        14: {
            "name": "松島みどり",
            "official": "https://www.matsushima-midori.jp/",
            "party": "自由民主党"
        },
        15: {
            "name": "大空幸星",
            "official": "https://ozorakoki.com/",
            "party": "自由民主党"
        },
        16: {
            "name": "大西洋平",
            "official": "https://youhei.me/",
            "party": "自由民主党"
        },
        17: {
            "name": "平沢勝栄",
            "official": "https://hirasawa.net/",
            "party": "自由民主党"
        },
        18: {
            "name": "福田かおる",
            "official": "https://fukuda-kaoru.com/",
            "party": "自由民主党"
        },
        19: {
            "name": "松本洋平",
            "official": "https://matsumoto-yohei.com/",
            "party": "自由民主党"
        },
        20: {
            "name": "木原誠二",
            "official": "https://kiharaseiji.com/",
            "party": "自由民主党"
        },
        21: {
            "name": "小田原潔",
            "official": "https://odawarakiyoshi.jp/",
            "party": "自由民主党"
        },
        22: {
            "name": "伊藤達也",
            "official": "https://www.tatsuyaito.com/",
            "party": "自由民主党"
        },
        23: {
            "name": "川松真一朗",
            "official": "https://kawamatsu2011.com/",
            "party": "自由民主党"
        },
        24: {
            "name": "萩生田光一",
            "official": "https://www.ko-1.jp/",
            "party": "自由民主党"
        },
        25: {
            "name": "井上信治",
            "official": "https://www.inoue-s.jp/",
            "party": "自由民主党"
        },
        26: {
            "name": "今岡植",
            "official": "https://imaoka-ueki.com/",
            "party": "自由民主党"
        },
        27: {
            "name": "黒崎祐一",
            "official": "https://kuro1.jp/",
            "party": "自由民主党"
        },
        28: {
            "name": "安藤高夫",
            "official": "https://andotakao.jp/",
            "party": "自由民主党"
        },
        29: {
            "name": "長澤興祐",
            "official": "http://www.kosukenagasawa.com/",
            "party": "自由民主党"
        },
        30: {
            "name": "長島昭久",
            "official": "https://nagashima30.com/",
            "party": "自由民主党"
        }

        '''





def clean_json_text(text):
    text = text.strip()
    text = re.sub(r'^```(json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text


def research1(district,winner,num,official):
    print("research1 started")
    #official="https://miki-yamada.com/"
    PROMPT = f"""
    1. 応答の開始から終了まで、一切の説明文、挨拶、レポート、Markdown装飾（```json等）を禁止します。
    2. 出力は、以下のJSONフォーマットに従った純粋なデータ構造のみとしてください。
    3. もしレポートや文章が含まれた場合、システムエラーとして処理されます。
    

    # Role
    あなたは政治学とデータ分析に精通した、極めて執念深いJSONデータ抽出エンジンです。
    指定された政治家の政策を含んだページのURLを最低20個抽出してください。
    後で選別するため、少しでも「具体的」と感じるものはすべて含めてください。質より量を求めています。
    「実現可能性」や「重要度」をあなたが判断して**切り捨てることを厳禁**します。
    具体的であれば、たとえ小さな項目であっても全てリストアップしてください。複数ページのURLを取り出すだけで、満足しないでください。最低でも30個のリンクを期待します。しつこく執念深く検索を続けてください。
   
   「政策ページ」とは以下を全て含む：
        明示的な政策・公約ページ
        活動報告・ブログ・お知らせ内で具体的施策に言及しているページ
        記者会見・演説・インタビュー記事
        PDF形式の政策資料・提言書
        予算・法案・制度に関する具体的記述があるページ
    政策と明記されていないページでも、具体的施策・数値・制度・予算・法案への言及があれば必ず含めること

    # Task
    公式サイト{official}のみを対象にクロールを行う。
    1. Google Search Groundingを使用し、{official}内で、政策や公約が記載されている可能性のあるページを**全て**クロールしてください。

    「公約」とのページ以外にも、ブログの欄などに政策がある可能性もあるため、公式ウェブサイトのリンクから政策がある可能性があるページをクロールしてください。公式ウェブサイトに関してはサイトマップを執念深く確認してください。
    
    2. 以下のクエリを一つずつGoogle search groundingを使用し検索すること。その上で、見つけたページに政策が含まれている場合はURLを保存すること。

    経済・税制・物価高 after:2025-03-30 site:{official}
    外交・安保・憲法 after:2025-03-30 site:{official}
    教育・子育て・デジタル after:2025-03-30 site:{official}
    厚生労働・医療・地域課題 after:2025-03-30 site:{official}
    - "{winner} 政策 after:2025-03-30 site:{official}"
    - "{winner} 公約 after:2025-03-30 site:{official}"
    - "{winner} マニフェスト site:{official}"
    - "site:{official} 政策"
    - "site:{official} 公約"

    3.以上のクエリ検索終了後、独自に site:{official} を含めた検索クエリを20個以上作ってください。一つずつGoogle search groundingを使用し検索すること。
    その上で、見つけたページに政策が含まれている場合はURLを保存すること。
    

    

    4. 抽出したURLを、必ず以下のJSONフォーマットの形式でリスト化してください。発見したURLは全てJsonにまとめてください。
    5. 今回の選挙・選挙区の考察や挨拶などは不要のため、プロンプトに対しJsonのみで返答してください。レポートを求めていません。あくまでURLの抽出が目的です。
    6. 「似たような内容だから」という理由でURLを統合することを厳禁します。URLが異なれば、それは別のソースとして全て出力してください。

   
    
# Target
    対象議員：{winner}
    対象期間：2026年2月の衆議院選挙に際して、{winner}が{official}に発表したもののリンクを検索してください。
    



JSONフォーマット：

{{
  "urls": [
    "URL1",
    "URL2",
    "URL3"
  ]
}}


※重要：３つ以上ある際は全てjsonで乗せてください。
※重要：キー名に日本語や具体的な公約内容を入れず、必ず上記の見本と同じキー名（urls）を使用してください。
見つかった全てのURLを、上記のJSONと同じ構造でリスト内に追加してください。
JSONとして正しい形で返してください。
最低でも20個のURLを返してください。
    """



    interaction = client.interactions.create(
        input=PROMPT,
        agent='deep-research-pro-preview-12-2025',
        background=True
    )

    print(f"started researching {winner} in {district} {num} district")
    interaction_id = interaction.id
    final_result = wait_for_research(client,interaction_id)

    OUT_DIR = Path("output/draftresearch/")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"{district}-{num:02d}-final.json"
            

    try:
        new_data = json.loads(clean_json_text(final_result))
        new_urls = new_data.get("urls", [])
    except Exception as e:
        print(f"JSON parse error: {e}")
        new_urls = []

    OUT_DIR = Path("output/draftresearch/")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"{district}-{num:02d}-final.json"


    with save_lock:
        existing_urls = []
        if out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                    existing_urls = existing_data.get("urls", [])
                except Exception as e:
                    print(f"File load error: {e}")
                    existing_urls = []

       
        combined_urls = list(set(existing_urls + new_urls))

 
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"urls": combined_urls}, f, ensure_ascii=False, indent=2)

    print(f"New URLs found: {len(new_urls)}")
    print("research 1 finished")

     



def research2(district,winner,num):
    print("research 2 started")
    PROMPT = f"""
    1. 応答の開始から終了まで、一切の説明文、挨拶、レポート、Markdown装飾（```json等）を禁止します。
    2. 出力は、以下のJSONフォーマットに従った純粋なデータ構造のみとしてください。
    3. もしレポートや文章が含まれた場合、システムエラーとして処理されます。
    
    # Role
    あなたは政治学とデータ分析に精通した、極めて執念深いJSONデータ抽出エンジンです。
    指定された政治家の政策を含んだページのURLを抽出してください。
    後で選別するため、少しでも「具体的」と感じるものはすべて含めてください。
    「実現可能性」や「重要度」をあなたが判断して**切り捨てることを厳禁**します。
    具体的であれば、たとえ小さな項目であっても全てリストアップしてください。複数ページのURLを取り出すだけで、満足しないでください。しつこく執念深く検索を続けてください。
   
    # Task
    1. Google Search Groundingを使用し、対象者の政策や公約が記載されている可能性のあるページを**全て**クロールしてください。
    なお、{winner}のNote.comをafter:2025-03-30で検索した際に、対象者のNoteアカウントが見つかった場合は、Note.comも同様に分析してください。
    また、{winner}のブログをafter:2025-03-30で検索した際に、対象者のブログが見つかった場合は、ブログも同様に分析してください。

    対象者の公式ウェブサイトは確認しないでください。
    
    2. 検索クエリを20個以上作ってください。その際、以下のクエリを必ず含めること。

    経済・税制・物価高 after:2025-03-30
    外交・安保・憲法 after:2025-03-30
    教育・子育て・デジタル after:2025-03-30
    厚生労働・医療・地域課題 after:2025-03-30
    - "{winner} 政策 after:2025-03-30"
    - "{winner} 公約 after:2025-03-30"
    - "{winner} マニフェスト"
    - "{winner} ブログ 政策"
    - "{winner} note 政策"
    - "{winner} インタビュー 政策"
    - "{winner} NHK アンケート"
    - "{winner} 朝日新聞 候補者アンケート"

    3. 抽出したURLを、必ず以下のJSONフォーマットの形式でリスト化してください。発見したURLは全てJsonにまとめてください。
    4. 今回の選挙・選挙区の考察や挨拶などは不要のため、プロンプトに対しJsonのみで返答してください。レポートを求めていません。あくまでURLの抽出が目的です。
    5. 「似たような内容だから」という理由でURLを統合することを厳禁します。URLが異なれば、それは別のソースとして全て出力してください。

    - JSON以外の説明文、挨拶、Markdownの装飾は一切含めず、純粋なJSON文字列のみを返してください。
    - プロフィールや挨拶などは省いてください。



    
# Target
    対象議員：{winner}
    対象期間：2026年2月の衆議院選挙に際して、{winner}が発表した政策内容をソースとしてください。
    



JSONフォーマット：

{{
  "urls": [
    "URL1",
    "URL2",
    "URL3"
  ]
}}


※重要：３つ以上ある際は全てjsonで乗せてください。
※重要：キー名に日本語や具体的な公約内容を入れず、必ず上記の見本と同じキー名（urls）を使用してください。
見つかった全てのURLを、上記のJSONと同じ構造でリスト内に追加してください。
JSONとして正しい形で返してください。
    """



    interaction = client.interactions.create(
        input=PROMPT,
        agent='deep-research-pro-preview-12-2025',
        background=True
    )

    print(f"started researching {winner} in {district} {num} district")

    interaction_id = interaction.id
    final_result= wait_for_research(client,interaction_id)

    OUT_DIR = Path("output/draftresearch/")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"{district}-{num:02d}-final.json"
            
    try:
        new_data = json.loads(clean_json_text(final_result))
        new_urls = new_data.get("urls", [])
    except Exception as e:
        new_urls = []


    if out_file.exists():
        with open(out_file, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                existing_urls = existing_data.get("urls", [])
            except Exception as e:
                existing_urls = []
    else:
        existing_urls = []

    combined_urls = list(set(existing_urls + new_urls))


    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"urls": combined_urls}, f, ensure_ascii=False, indent=2)

    print(f"New URLs found: {len(new_urls)}")
    print("research 2 finished")



def get_manifesto(district,winner,num):
    out_file = Path(f"output/finaldata/{district}-{num:02d}-final.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    final_data = {
        "district": f"東京{num}区",
        "candidates": [
            {
                "name": winner,
                "party": "", 
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

    for url in urls:
        print(f"  -> チェック中: {url}")

        if url.lower().endswith(('.pdf', '.doc', '.docx', '.xlsx', '.ppt', '.pptx')):
            print(f"  -> スキップ（PDF/文書ファイル）")
            continue

        start = time.time()
        try:
            print(f"  -> ページを取得しています: {url}")
            res = safe_request_get(url)
           


        except Exception as e:
            print(f"  -> ページ取得失敗: {url} | {e}")

            continue
        

 
        
        date=find_date(res.text)
        if date is not None:
            year = int(str(date)[:4])

            if year < 2025:
                print(f"  -> スキップ（{year}年のページ）: {url}")
                continue
        
        else:
            print(f"  -> 日付が特定できませんでした（判定を続行）: {url}")



        if "text/html" not in res.headers.get("Content-Type", ""):
            print("  -> HTML以外なのでスキップ:", res.headers.get("Content-Type"))
            continue
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
  

            manifesto_url.append(url)
        
            extracted_data = filter_manifesto(district, winner, num, clean_text, url)
            
            if extracted_data and "candidates" in extracted_data:
                candidate = extracted_data["candidates"][0]
                new_manifesto = candidate.get("manifesto", [])
                new_not_manifesto = candidate.get("not-manifesto", [])
                
         
                save_append_data(out_file, district, num, winner, new_manifesto, new_not_manifesto)
                print(f"  -> {url} の保存完了！")
        elif not is_policy:
            continue
        else:
            print("format function has error, response is not True or False")
            print(response.text)

    print(f"finished {district} {num} district")
    print(manifesto_url)







def filter_manifesto(district,winner,num,input,url):



    PROMPT_FILTER = f"""
# Role
あなたは政治学の専門家かつ、冷徹なデータアナリストです。
提供された「公約候補リスト」を精査し、以下の【排除基準】に1つでも該当するものは**容赦なくnot-manifestoに含めて**ください。

# 判定基準（すべて満たすもののみ残す）
1. 【具体的かつ観測可能】: 「〜の検討」は即座に削除。「〜法の改正」「〜予算の確保」など、後に達成度が検証できるもの。
2. 【政治的行動への意思】: 「〜を目指す」「〜したい」「努力する」は即座に削除。「〜を導入する」「〜を改正する」といった**断定的なコミットメント**のみを残す。
3. 【公共性】: 特定地域への利益誘導ではなく、全国的な制度変更や法的措置であること。
4. {winner}または信頼できるソースによるものであること。

    1. **数値・条件の変更**: 基礎控除の引き上げ、床面積要件の緩和など。
    2. **制度のステータス変更**: 「法的拘束力の付与」「必修化」「情報の公開」「システム共有」など。
    3. **新規制度の設立**: 「日本版DBSの導入」「新法の制定」など。
上記1-3はコミットメントとして扱う。

# 排除基準（これらは公約ではないです）
- 抽象的なスローガン（例：日本を元気にする、都民の暮らしを守る）
- 単なる現状認識（例：少子化は国難である）
- 挨拶や感謝（例：皆様のおかげで当選できました）
- 曖昧な意気込み（例：しっかりと取り組んでまいります）
- 他者のコメントの引用など、{winner}自身の政策表明とみなせないもの


# Task
上記基準をクリアした「真の公約」のみを抽出し、以下のJSON形式で出力してください。
JSON以外の文字、解説、Markdownの装飾（```json等）は一切禁止します。

ステップ1：各候補の政策について、Rubric（判定基準）に照らして「採択」か「却下」かを判断し、その理由を1行でメモしてください。
ステップ2：合格したもの（採択されたもの）だけを、最終的なJSON形式でmanifestoの欄にまとめてください。

# 思考の出力例(reasonの欄に出力)
- ✅ 採択：住宅ローン減税の「床面積要件」を緩和（単一変数の操作）
- ✅ 採択：消費税をゼロに減税（実施の有無が判断できる、変数が明確）
- ✅ 採択：日本版DBSの「導入」（Yes/Noが明確な具体的行動）
- ❌ 却下：所得税減税（変数が不特定）
- ❌ 却下：下請Gメンの「執行体制」を拡充（体制は中身が不透明で検証不能）
- ❌ 却下：〜を検討、推進、目指す（単なる手続き表現）
- ❌ 却下：下請Gメンの「人材（定員）」を拡充（「拡充」の有無は恣意的、明確にYes/Noで判断できない）
操作する変数が特定されているものだけが「公約」です。


※重要：manifestoは必ず「オブジェクトの配列（リスト形式）」にしてください。
※重要：キー名に日本語や具体的な公約内容を入れず、必ず上記の見本と同じキー名（title, sources, quote_text）を使用してください。
見つかった全ての公約を、上記のJSONと同じ構造でリスト内に追加してください。
JSONとして正しい形で返してください。
一つの文章に複数の要素が含まれる場合、**それぞれを分解**し、独立して要件を満たす部分のみを公約として扱う。


# 【排除基準】
1. **手続き・意欲表現**: 「検討」「議論」「調査」「推進」「目指す」「努める」が含まれるものは、内容に関わらず公約ではありません。
2. **現状維持**: 既に実施中の政策の継続や再確認（例：今年度予算の着実な実施）。例え具体的であっても即座に却下。
ただし、時限立法など廃止が制度的に予見される際は公約として扱う。
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
      "not-manifesto": [
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
    time.sleep(5)
    print(response)
    try:
        return json.loads(response.text)
    except Exception as e:
        return None




def process(district,winner,num,official):
  #  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
   #     future1 = executor.submit(research1, district, winner, num, official)
    #    future2 = executor.submit(research2, district, winner, num)
        
        
      #  concurrent.futures.wait([future1, future2])
    #research1(district,winner,num)
    #research2(district,winner,num)
    #get_manifesto(district, winner, num)
    overlapping(district, num)


'''if __name__ == "__main__":
    for district, winners in ALL_WINNERS.items():
        for num, winner_name in winners.items():
            winner=winner_name
            research(district,winner,num)
            filter(district, winner ,num)
    '''


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        futures=[]
        for district, winners in ALL_WINNERS.items():
            for num, info in winners.items():
                name = info["name"]
                official = info["official"]
                executor.submit(process, district, name, num, official)

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"スレッド実行中にエラーが発生しました: {exc}")