    "https://www.yomiuri.co.jp/election/shugiin/2026/YC84XXXXXX000/135734/",
    "https://www.youtube.com/watch?v=PY3v69RtQ_A",
    "https://www.kanno-ko.com/2017/10/13/%E3%80%8C%E8%BE%BB%E6%B8%85%E4%BA%BA%E3%81%95%E3%82%93%E3%81%A3%E3%81%A6%E3%81%A9%E3%82%93%E3%81%AA%E4%BA%BA%EF%BC%9F%E3%80%8D%EF%BC%881013%EF%BC%89/",
    "https://go2senkyo.com/seijika/142007/posts/year/2026/month/3",
    "https://www.kantei.go.jp/jp/headline/sougoukeizaitaisaku2025/bukkadakataiou.html",
    "https://go2senkyo.com/seijika/142007",
    "https://www.jimin.jp/election/results/sen_shu51/candidate/detail/tsuji-kiyoto.html",
    "https://www.komei.or.jp/content/p415532/",
    "https://www.shugiin.go.jp/Internet/itdb_kaigiroku.nsf/html/kaigiroku/000121720250618035.htm",
    "https://k-tsuji.jp/performance/",
    "https://www.jimin.jp/news/libre_sp/202501/",
    "https://cdp-japan.jp/visions/policies2025/19",
    "https://www.shugiin.go.jp/Internet/itdb_kaigiroku.nsf/html/kaigiroku%20/000221720250611027.htm",
    "https://googol.club/survey/dvanke.html",
    "https://go2senkyo.com/seijika/142007/posts/1277735",
    "https://shuinsen2026.afee.jp/",
    "https://www.jimin.jp/news/policy/203484.html",
    "https://k-tsuji.jp/2021/02/16/489/",
    "https://nichizeisei.jp/wp-content/uploads/2015/09/%E3%80%8C%E6%97%A5%E6%9C%AC%E7%A8%8E%E6%94%BF%E9%80%A3%E3%80%8D%E7%AC%AC%EF%BC%95%EF%BC%92%E5%8F%B7%E5%B9%B3%E6%88%90%EF%BC%92%EF%BC%97%E5%B9%B4%EF%BC%99%E6%9C%88%EF%BC%91%E6%97%A5%E7%99%BA%E8%A1%8C.pdf",
    "https://www.eri-arfiya.jp/tag/%E8%BE%BB%E6%B8%85%E4%BA%BA/",
    "https://www.youtube.com/watch?v=4F7-H9Vq3x0",
    "https://www.m3.com/news/iryoishin/1318392",


## AIは抽出せず
- 燃料油価格の定額引下げ
- 価格転嫁ガイドラインの法的拘束力強化
- 下請Gメンや公正取引委員会の人材を拡充

## 以下、AIも抽出
- 税や社会保険料の未納情報を行政機関間で共有し、その情報を在留審査に活用する
- 都市部のマンションなどの取得を含めた国土全域で土地等の実質的支配者情報等を把握し国民に公開
- AIやデータサイエンスに関する教育を早期から必修化
- 住宅ローン減税の床面積要件を緩和
- 教育・保育・医療等の業務従事者の性犯罪歴を確認する仕組み（日本版DBS）を導入
- 憲法改正により「自衛隊」を明記

[AIの判断(json file)](output/data/tokyo-01-prev.json)



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

選挙区: 第1区から第30区まで全て、2026年　　１−30区の全ての議員についてWikipediaを確認して。JSONの形に忠実に。name, official, partyの順番や名前を変えないように。当選者はプロンプトにある。