function generateMinervaMarkdown() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheets()[0]; 
  const data = sheet.getDataRange().getValues();
  
  if (data.length < 2) {
    console.log("回答データがありません。");
    return;
  }

  const row = data[data.length - 1]; 


  const pref_raw   = row[1].toString().trim().toLowerCase(); 
  const district   = row[2];  
  const name_ja    = row[3]; 
  const name_en    = row[4]; 
  const hasProportional = row[21]; 
  const prop_name_ja  = row[22];  
  const prop_name_en  = row[23];  
  const kouho_link = row[34]; 
  const party_main = row[35]; 
  const party_prop = row[36]; 

 
  const prefMap = {
    'hokkaido': '北海道', 'aomori': '青森', 'iwate': '岩手', 'miyagi': '宮城', 'akita': '秋田',
    'yamagata': '山形', 'fukushima': '福島', 'ibaraki': '茨城', 'tochigi': '栃木', 'gunma': '群馬',
    'saitama': '埼玉', 'chiba': '千葉', 'tokyo': '東京', 'kanagawa': '神奈川', 'niigata': '新潟',
    'toyama': '富山', 'ishikawa': '石川', 'fukui': '福井', 'yamanashi': '山梨', 'nagano': '長野',
    'gifu': '岐阜', 'shizuoka': '静岡', 'aichi': '愛知', 'mie': '三重', 'shiga': '滋賀',
    'kyoto': '京都', 'osaka': '大阪', 'hyogo': '兵庫', 'nara': '奈良', 'wakayama': '和歌山',
    'tottori': '鳥取', 'shimane': '島根', 'okayama': '岡山', 'hiroshima': '広島', 'yamaguchi': '山口',
    'tokushima': '徳島', 'kagawa': '香川', 'ehime': '愛媛', 'kochi': '高知', 'fukuoka': '福岡',
    'saga': '佐賀', 'nagasaki': '長崎', 'kumamoto': '熊本', 'oita': '大分', 'miyazaki': '宮崎',
    'kagoshima': '鹿児島', 'okinawa': '沖縄'
  };
  const pref_ja = prefMap[pref_raw] || pref_raw;
  const displayTitle = `${pref_ja}${district}区`;

  // 小選挙区
  let md = `---\ntitle: "${displayTitle}"\nurl: prefectures/${pref_raw}/${district}\n---\n\n`;
  md += `# [${name_ja}](/shu/${pref_raw}/${district}/${name_en})\n\n`;
  md += `${party_main}\n\n`; 

  for (let i = 5; i <= 20; i += 2) {
    let policy = row[i];
    let evidence = row[i+1];
    if (policy && policy.toString().trim() !== "") {
      md += formatPolicyLine(policy, evidence);
    }
  }
  


  // 比例
  if (hasProportional === "はい" || (prop_name_ja && prop_name_ja.toString().trim() !== "")) {
    md += `\n\n\n# [${prop_name_ja}](/shu/${pref_raw}/${district}/${prop_name_en})\n\n`;
    md += `${party_prop}\n\n`; 
    
    for (let j = 24; j <= 32; j += 2) {
      let p_policy = row[j];
      let p_url = row[j+1];
      if (p_policy && p_policy.toString().trim() !== "") {
        md += formatPolicyLine(p_policy, p_url);
      }
    }
    
  if (kouho_link && kouho_link.toString().trim() !== "") {
      md += `\n[選挙公報](${kouho_link.toString().trim()})\n`;
    }
  }

  // 表示
  try {
    const htmlOutput = HtmlService.createHtmlOutput(
      `<textarea readonly style="width:100%; height:450px; font-family:monospace; padding:10px;">${md}</textarea>`
    ).setWidth(800).setHeight(550);
    SpreadsheetApp.getUi().showModalDialog(htmlOutput, "生成されたMarkdown");
  } catch (e) {
    console.log("エディタ実行のためダイアログをスキップしました。");
  }

  // PR
  const filePath = `content/prefectures/${pref_raw}/${pref_raw}-district/${district}.md`;
 
  try {
    
    const prUrl = createGitHubPullRequestWithLink(filePath, md, displayTitle, pref_raw, pref_ja, district);
    if (prUrl) {
      SpreadsheetApp.getUi().alert("GitHubにプルリクエストを作成\n" + prUrl);
    }
  } catch (err) {
    console.log("エラー: " + err.message);
  } 

} 




function formatPolicyLine(title, evidence) {
  const cleanEvidence = evidence ? evidence.toString().trim() : "";
  if (cleanEvidence !== "") {
    return `✅ [${title}](${cleanEvidence})  \n`;
  } else {
    return `❌ ${title}  \n`;
  }
}




function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🛠️ Minerva')
    .addItem('AI自動収集（当/比/公報/公約）→ PR', 'autofillLatestRowAndGeneratePR')
    .addItem('最新の回答からMDを生成 & PR送信', 'generateMinervaMarkdown')
    .addToUi();
}


function createGitHubPullRequestWithLink(path, content, title, pref_en, pref_ja, district) {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const user  = props.getProperty('GITHUB_USER');
  const repo  = props.getProperty('GITHUB_REPO');

  const baseUrl = `https://api.github.com/repos/${user}/${repo}`;
  const headers = {
    "Authorization": "token " + token,
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
  };

  // mainから新規ブランチを作成
  const resMain = UrlFetchApp.fetch(`${baseUrl}/git/ref/heads/main`, {headers: headers});
  const mainSha = JSON.parse(resMain.getContentText()).object.sha;
  const branchName = "update-" + pref_en + "-" + district + "-" + new Date().getTime();
  UrlFetchApp.fetch(`${baseUrl}/git/refs`, {
    method: "post", headers: headers,
    payload: JSON.stringify({ref: "refs/heads/" + branchName, sha: mainSha})
  });

  // 選挙区個別ページ (.md) を作成してブランチに入れる
  UrlFetchApp.fetch(`${baseUrl}/contents/${path}`, {
    method: "put", headers: headers,
    payload: JSON.stringify({
      message: "feat: add district data for " + title,
      content: Utilities.base64Encode(content, Utilities.Charset.UTF_8),
      branch: branchName
    })
  });

  //都道府県インデックス (tokyo.md等) の読み取りとソート・追記
  const prefPath = `content/prefectures/${pref_en}/${pref_en}.md`;
  
  try {
    const resPref = UrlFetchApp.fetch(`${baseUrl}/contents/${prefPath}?ref=${branchName}`, {headers: headers});
    const prefData = JSON.parse(resPref.getContentText());
    let prefContent = Utilities.newBlob(Utilities.base64Decode(prefData.content)).getDataAsString();
    
    // 現在の新しいリンク
    const newLinkLine = `- [${pref_ja}${district}区](./${district}/)`;
    
    // 1. 内容を行ごとに分割
    let lines = prefContent.split("\n");
    
    // 2. 既存の選挙区リンク行と、それ以外（ヘッダーや「今後追加！」）を分ける
    let districtLines = lines.filter(line => line.match(/- \[.*?\d+区\]/));
    let otherLines = lines.filter(line => !line.match(/- \[.*?\d+区\]/) && line.trim() !== "" && line !== "今後追加！");

    // 3. 新しいリンクをリストに追加（重複がなければ）
    if (districtLines.indexOf(newLinkLine) === -1) {
      districtLines.push(newLinkLine);
    }

    // 4. 数字の順番でソート
    districtLines.sort((a, b) => {
      const numA = parseInt(a.match(/\d+/)[0]);
      const numB = parseInt(b.match(/\d+/)[0]);
      return numA - numB;
    });

    // 5. 全体を再構築（ヘッダー + ソート済みリスト + 今後追加！）
    let newContent = otherLines.join("\n") + "\n\n" + districtLines.join("\n") + "\n\n今後追加！\n";

    // 以前の内容と変わっている場合のみ更新
    if (newContent !== prefContent) {
      UrlFetchApp.fetch(`${baseUrl}/contents/${prefPath}`, {
        method: "put", headers: headers,
        payload: JSON.stringify({
          message: `fix: sort and update ${pref_ja} index links`,
          content: Utilities.base64Encode(newContent, Utilities.Charset.UTF_8),
          branch: branchName,
          sha: prefData.sha
        })
      });
    }
  } catch (e) {
    console.log("都道府県MDの更新スキップ: " + e.message);
  }

  // 4. まとめてPRを作成
  const resPr = UrlFetchApp.fetch(`${baseUrl}/pulls`, {
    method: "post", headers: headers,
    payload: JSON.stringify({
      title: "【データ追加】" + title,
      head: branchName,
      base: "main",
      body: `Google form を元に${title} の詳細データ作成と、都道府県トップページへのリンク追記を行いました。`
    })
  });

  return JSON.parse(resPr.getContentText()).html_url;
}

const MINERVA_HEADERS = {
  SENKYOKU_URL: "senkyoku_url", // シート1行目ヘッダー名
};

const OPENAI_ENDPOINT = "https://api.openai.com/v1/responses";

/***********************
 * 追加：入口（最新行を全部自動で埋めて PR）
 ***********************/
function autofillLatestRowAndGeneratePR() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheets()[0];

  const lastRow = sheet.getLastRow();
  if (lastRow < 2) throw new Error("データ行がありません。");

  // ヘッダー→列番号
  const headerMap = getHeaderMap_(sheet);

  // 最新行を取得
  const row = sheet.getRange(lastRow, 1, 1, sheet.getLastColumn()).getValues()[0];

  // 選挙区ページURL（go2senkyo）
  const senkyokuUrlCol = headerMap[MINERVA_HEADERS.SENKYOKU_URL];
  if (!senkyokuUrlCol) {
    throw new Error(`ヘッダー行に "${MINERVA_HEADERS.SENKYOKU_URL}" 列を追加してください。`);
  }
  const senkyokuUrl = (row[senkyokuUrlCol - 1] || "").toString().trim();
  if (!senkyokuUrl) throw new Error("senkyoku_url が空です。");

  // 1) go2senkyo 選挙区ページから 当選者/比例復活/選挙公報PDF を自動取得
  const parsed = parseSenkyokuPage_(senkyokuUrl);

  // 2) 行へ反映（既存列仕様に合わせる）
  applySenkyokuParsedToRow_(sheet, lastRow, parsed);

  // 3) 公報PDFから公約抽出して row[5..] / row[24..] を埋める（PDF file_url 入力）
  const filled = extractPoliciesFromKohoPdfAndFillRow_(sheet, lastRow);

  // 4) 既存のPR生成を実行
  generateMinervaMarkdown();

  // 軽いログ
  console.log("autofill done:", JSON.stringify({ parsed, filled }));
}

/***********************
 * 追加：ヘッダー→列番号Map
 ***********************/
function getHeaderMap_(sheet) {
  const lastCol = sheet.getLastColumn();
  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  const map = {};
  headers.forEach((h, idx) => {
    const key = (h || "").toString().trim();
    if (key) map[key] = idx + 1; // 1-based
  });
  return map;
}

/***********************
 * 追加：選挙区ページ解析（当/比/選挙公報PDF）
 *  - go2senkyoページのHTMLテキストから抽出
 ***********************/
function parseSenkyokuPage_(senkyokuUrl) {
  const html = UrlFetchApp.fetch(senkyokuUrl, {
    followRedirects: true,
    headers: { "User-Agent": "Mozilla/5.0 (compatible; MinervaBot/1.0)" }
  }).getContentText("UTF-8");

  // 選挙公報PDF（prod-cdn）を拾う（ページ末尾の「選挙公報」リンク）
  const pdfMatch = html.match(/https:\/\/prod-cdn\.go2senkyo\.com\/public\/senkyo_koho\/[^\s"'<>]+\.pdf[^\s"'<>]*/);
  const kohoPdfUrl = pdfMatch ? pdfMatch[0] : "";

  // 「当」「比」ブロック（例：東京2区ページでは "当" / "比" が候補者一覧の結果表に出る）
  // ざっくり： (当|比)\s+ Image: <名前> ... \n <名前>\n <年齢>歳｜<党名>
  const badgeRe = /(当|比)[\s\S]{0,300}?Image:\s*([^†\n]+)[\s\S]{0,120}?\n\s*\2\s*[\s\S]{0,120}?\n\s*\d+歳｜\s*([^\n<]+)/g;

  let winner = null;
  let revival = null;

  let m;
  while ((m = badgeRe.exec(html)) !== null) {
    const badge = (m[1] || "").trim(); // 当 or 比
    const name_ja = (m[2] || "").trim();
    const party_raw = (m[3] || "").trim();
    const party = normalizeParty_(party_raw);

    if (badge === "当" && !winner) winner = { name_ja, party };
    if (badge === "比" && !revival) revival = { name_ja, party };
  }

  return {
    senkyoku_url: senkyokuUrl,
    koho_pdf_url: kohoPdfUrl,
    winner,
    revival
  };
}

/***********************
 * 追加：党名正規化（最低限）
 *  - 必要に応じて辞書を増やしてOK
 ***********************/
function normalizeParty_(party) {
  const s = (party || "").toString().trim();
  if (!s) return "";

  const map = {
    "自民党": "自由民主党",
    "公明": "公明党",
    "立民": "立憲民主党",
    "維新": "日本維新の会",
    "共産": "日本共産党",
    "国民": "国民民主党",
    "れいわ": "れいわ新選組",
    "社民": "社会民主党",
    "参政": "参政党",
  };
  return map[s] || s;
}

/***********************
 * 追加：解析結果を既存列仕様へ反映
 * 既存 generateMinervaMarkdown() が参照する列:
 *  - pref_raw row[1], district row[2]
 *  - name_ja row[3], name_en row[4]
 *  - hasProportional row[21]
 *  - prop_name_ja row[22], prop_name_en row[23]
 *  - kouho_link row[34]
 *  - party_main row[35], party_prop row[36]
 ***********************/
function applySenkyokuParsedToRow_(sheet, rowIndex, parsed) {
  // kouho_link(row[34]) を埋める
  if (parsed.koho_pdf_url) {
    sheet.getRange(rowIndex, 35).setValue(parsed.koho_pdf_url); // 1-based col=35 => row[34]
  }

  // 当選者（小選挙区）
  if (parsed.winner) {
    sheet.getRange(rowIndex, 4).setValue(parsed.winner.name_ja); // col=4 => row[3] name_ja
    sheet.getRange(rowIndex, 36).setValue(parsed.winner.party);  // col=36 => row[35] party_main
    // name_en(row[4]) は後でOpenAIで補完
  }

  // 比例復活
  if (parsed.revival) {
    sheet.getRange(rowIndex, 22).setValue("はい");               // col=22 => row[21] hasProportional
    sheet.getRange(rowIndex, 23).setValue(parsed.revival.name_ja); // col=23 => row[22] prop_name_ja
    sheet.getRange(rowIndex, 37).setValue(parsed.revival.party);   // col=37 => row[36] party_prop
    // prop_name_en(row[23]) は後でOpenAIで補完
  }
}

/***********************
 * 追加：公報PDFから公約抽出→行に埋める
 *  - OpenAI Responses API に input_file(file_url) でPDFを渡す
 *  - Structured Outputs(JSON Schema固定)で戻す
 ***********************/
function extractPoliciesFromKohoPdfAndFillRow_(sheet, rowIndex) {
  const row = sheet.getRange(rowIndex, 1, 1, sheet.getLastColumn()).getValues()[0];
  const kohoPdfUrl = (row[34] || "").toString().trim(); // row[34] = kouho_link
  if (!kohoPdfUrl) throw new Error("選挙公報PDF URL（row[34]）が空です。");

  const winnerNameJa = (row[3] || "").toString().trim();
  const winnerParty = (row[35] || "").toString().trim();
  const revivalNameJa = (row[22] || "").toString().trim();
  const revivalParty = (row[36] || "").toString().trim();

  const schema = {
    name: "minerva_koho_extract",
    strict: true,
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        main: {
          type: "object",
          additionalProperties: false,
          properties: {
            name_ja: { type: "string" },
            name_en: { type: "string" },
            party:   { type: "string" },
            policies: {
              type: "array",
              items: { type: "string" },
              maxItems: 8
            },
            confidence: { type: "string", enum: ["high", "medium", "low"] }
          },
          required: ["name_ja", "name_en", "party", "policies", "confidence"]
        },
        prop: {
          anyOf: [
            { type: "null" },
            {
              type: "object",
              additionalProperties: false,
              properties: {
                name_ja: { type: "string" },
                name_en: { type: "string" },
                party:   { type: "string" },
                policies: {
                  type: "array",
                  items: { type: "string" },
                  maxItems: 5
                },
                confidence: { type: "string", enum: ["high", "medium", "low"] }
              },
              required: ["name_ja", "name_en", "party", "policies", "confidence"]
            }
          ]
        }
      },
      required: ["main", "prop"]
    }
  };

  const instruction =
`あなたは日本の選挙公報（PDF）から、候補者の「公約/重点政策/やること」を抽出し、Google Form入力用に短い箇条書きへ整形します。

ルール:
- 「公約」として読み取れる“実行宣言/実施する/実現する/やる”系を優先。スローガンのみは避ける（ただし政策がそれしか無い場合は採用可）。
- 1項目は短く（30〜60文字程度）。重複はまとめる。
- main は小選挙区の当選者（ヒント: ${winnerNameJa || "不明"} / ${winnerParty || "不明"}）。
- prop は比例復活がいる場合のみ（ヒント: ${revivalNameJa || "なし"} / ${revivalParty || "なし"}）。いなければ null。
- name_en は URL スラッグ形式: 例 "takebe-arata"（小文字・ハイフン区切り、英字のみ）。
- party はフォーム選択肢に寄せた正式名（例: 自由民主党 / 立憲民主党 / 国民民主党 / 日本維新の会 / 日本共産党 / れいわ新選組 / 社会民主党 / 参政党 / 公明党 / 他）。
- confidence は、公報内で政策欄が明確に読めたら high、怪しければ low。

出力はJSONのみ。`;

  const model = getScriptProp_("OPENAI_MODEL", "gpt-4o-mini");
  const resp = callOpenAIResponses_({
    model,
    response_format: { type: "json_schema", json_schema: schema },
    input: [
      {
        role: "user",
        content: [
          { type: "input_file", file_url: kohoPdfUrl },
          { type: "input_text", text: instruction }
        ]
      }
    ]
  });

  // Responses API: output_text にJSONが入る想定
  const jsonText = (resp.output_text || "").trim();
  if (!jsonText) throw new Error("OpenAI response.output_text が空です。");
  const out = JSON.parse(jsonText);

  // 行へ書き込み
  writePoliciesToRow_(sheet, rowIndex, out);

  // confidenceが低ければ上位モデル再試行（任意：ここでは medium/low のみ再実行）
  if (out.main && (out.main.confidence === "low")) {
    const fallbackModel = "gpt-4.1-mini";
    const resp2 = callOpenAIResponses_({
      model: fallbackModel,
      response_format: { type: "json_schema", json_schema: schema },
      input: [
        {
          role: "user",
          content: [
            { type: "input_file", file_url: kohoPdfUrl },
            { type: "input_text", text: instruction + "\n\n注意: 文字が小さいので丁寧に読み取ってください。" }
          ]
        }
      ]
    });
    const t2 = (resp2.output_text || "").trim();
    if (t2) {
      const out2 = JSON.parse(t2);
      writePoliciesToRow_(sheet, rowIndex, out2);
      return out2;
    }
  }

  return out;
}

/***********************
 * 追加：OpenAI Responses API 呼び出し
 ***********************/
function callOpenAIResponses_(payload) {
  const apiKey = getScriptProp_("OPENAI_API_KEY", "");
  if (!apiKey) throw new Error("ScriptProperties に OPENAI_API_KEY を設定してください。");

  const res = UrlFetchApp.fetch(OPENAI_ENDPOINT, {
    method: "post",
    contentType: "application/json",
    headers: {
      "Authorization": "Bearer " + apiKey
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const code = res.getResponseCode();
  const body = res.getContentText();
  if (code >= 300) throw new Error(`OpenAI API error: ${code} ${body}`);
  return JSON.parse(body);
}

function getScriptProp_(key, defaultValue) {
  const v = PropertiesService.getScriptProperties().getProperty(key);
  return (v === null || v === undefined || v === "") ? defaultValue : v;
}

/***********************
 * 追加：LLM出力を既存列へ書き込み
 ***********************/
function writePoliciesToRow_(sheet, rowIndex, out) {
  // 小選挙区: row[5],7,...,19 (8枠) / evidence は空でOK
  const main = out.main;
  if (main) {
    // name_ja(row[3]), name_en(row[4]), party_main(row[35])
    if (main.name_ja) sheet.getRange(rowIndex, 4).setValue(main.name_ja);
    if (main.name_en) sheet.getRange(rowIndex, 5).setValue(main.name_en);
    if (main.party)   sheet.getRange(rowIndex, 36).setValue(normalizeParty_(main.party));

    const policies = Array.isArray(main.policies) ? main.policies : [];
    for (let k = 0; k < 8; k++) {
      const policyCol0 = 5 + k * 2; // 0-based row index（row[5],7,...）の “列番号-1”
      const sheetCol = policyCol0 + 1 + 1; // 1-based + A列オフセット => (policyCol0はrow[] indexなので +1)
      // 分かりやすく直接指定：row[5]はシート列6（A=1）
      const col = 6 + k * 2;
      sheet.getRange(rowIndex, col).setValue(policies[k] || "");
      // 根拠URL列（col+1）は空にする（既存formatPolicyLineで❌扱い）
      sheet.getRange(rowIndex, col + 1).setValue("");
    }
  }

  // 比例: hasProportional(row[21]) が "はい" の場合のみ埋める
  const prop = out.prop;
  if (prop && prop !== null) {
    sheet.getRange(rowIndex, 22).setValue("はい"); // hasProportional
    if (prop.name_ja) sheet.getRange(rowIndex, 23).setValue(prop.name_ja);
    if (prop.name_en) sheet.getRange(rowIndex, 24).setValue(prop.name_en);
    if (prop.party)   sheet.getRange(rowIndex, 37).setValue(normalizeParty_(prop.party));

    const policies = Array.isArray(prop.policies) ? prop.policies : [];
    for (let k = 0; k < 5; k++) {
      // row[24] はシート列25
      const col = 25 + k * 2;
      sheet.getRange(rowIndex, col).setValue(policies[k] || "");
      sheet.getRange(rowIndex, col + 1).setValue("");
    }
  }
}
