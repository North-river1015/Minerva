
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


load_dotenv()

key = os.environ.get('GEMINI_API')

client = genai.Client(api_key= key)

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

def research():

    PROMPT='''
# Role  

あなたは日本の国政選挙および政治家データに精通した調査スペシャリストです。



# Task

[対象：東京都1区山田美樹2区辻清人3区石原宏高4区平将明5区若宮健嗣6区畦元将吾7区丸川珠代8区門寛子9区菅原一秀10区鈴木隼人11区下村博文12区高木啓13区土田慎14区松島みどり15区大空幸星16区大西洋平17区平沢勝栄18区福田かおる19区松本洋平20区木原誠二21区小田原潔22区伊藤達也23区川松真一朗24区萩生田光一25区井上信治26区今岡植27区黒崎祐一28区安藤高夫29区長澤興祐30区長島昭久]について、以下の辞書形式（Python dictionary format）でデータを整理してください。それぞれの議員についてWikipediaへ行き、そこから公式サイトへのリンクを見つけるように。



# Constraints (厳守事項)

1. **URLの検証**: URLは必ずブラウザでアクセス可能な最新の公式サイト、または公式プロフィールページ（政党内ページやSNSではなく独自ドメインを優先）を特定してください。推測で生成せず、不明な場合は "N/A" と記載してください。

2. **所属政党の正確性**: 当選時点の最新情報を反映してください。

3. **フォーマット**: 提供する `ALL_WINNERS` 変数の構造を完全に維持してください。

4. **検索プロセス**:

   - まず、各選挙区の当選者氏名リストを確定させる。

   - 次に、氏名 + 「公式サイト」「事務所」「選挙区」で検索し、URLの整合性を確認する。



# Output Format

ALL_WINNERS = {

    "tokyo": {

        1: {

            "name": "氏名",

            "official": "URL",

            "party": "政党名"

        },

        ...

    }

}



# Target Data

対象地域: 東京都

選挙区: 第1区から第30区まで全て、2026年　　１−30区の全ての議員についてWikipediaを確認して。JSONの形に忠実に。

※重要：キー名に日本語や別の英語を入れず、必ず上記の見本と同じキー名を使用してください。 '''


    interaction = client.interactions.create(
        input=PROMPT,
        agent='deep-research-pro-preview-12-2025',
        background=True
    )

    print(f"started researching ")
    interaction_id = interaction.id
    final_result = wait_for_research(client,interaction_id)

    OUT_DIR = Path("output/url/")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"url.json"
            
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    research()




