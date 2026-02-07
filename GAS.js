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
    .addItem('① 都道府県ページから全選挙区URLをキュー作成', 'enqueueAllSenkyokuUrls')
    .addItem('② キューをN件処理（自動収集→PR）', 'processSenkyokuQueueBatch')
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

/**
 * GitHub上の既存選挙区ファイル一覧を取得
 * @return {Set<string>} "pref_raw/district" 形式のセット
 */
function getExistingDistrictFiles_() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const user  = props.getProperty('GITHUB_USER');
  const repo  = props.getProperty('GITHUB_REPO');

  const baseUrl = `https://api.github.com/repos/${user}/${repo}`;
  const headers = {
    "Authorization": "token " + token,
    "Accept": "application/vnd.github.v3+json"
  };

  try {
    // mainブランチのツリーを再帰的に取得
    const resMain = UrlFetchApp.fetch(`${baseUrl}/git/ref/heads/main`, {headers: headers});
    const mainSha = JSON.parse(resMain.getContentText()).object.sha;

    const resTree = UrlFetchApp.fetch(`${baseUrl}/git/trees/${mainSha}?recursive=1`, {headers: headers});
    const tree = JSON.parse(resTree.getContentText()).tree;

    const existingSet = new Set();
    // content/prefectures/{pref}/{pref}-district/{district}.md のパターンを抽出
    const pattern = /^content\/prefectures\/([^\/]+)\/\1-district\/([^\/]+)\.md$/;

    for (const item of tree) {
      if (item.type === "blob") {
        const match = item.path.match(pattern);
        if (match) {
          const pref = match[1];
          const district = match[2];
          existingSet.add(`${pref}/${district}`);
        }
      }
    }

    return existingSet;
  } catch (e) {
    console.log(`既存ファイル一覧の取得失敗: ${e.message}`);
    return new Set();
  }
}

/**
 * GitHub上に選挙区ファイルが既に存在するかチェック
 */
function checkDistrictFileExists_(pref_raw, district) {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  const user  = props.getProperty('GITHUB_USER');
  const repo  = props.getProperty('GITHUB_REPO');

  const filePath = `content/prefectures/${pref_raw}/${pref_raw}-district/${district}.md`;
  const url = `https://api.github.com/repos/${user}/${repo}/contents/${filePath}`;

  try {
    const res = UrlFetchApp.fetch(url, {
      method: "get",
      headers: {
        "Authorization": "token " + token,
        "Accept": "application/vnd.github.v3+json"
      },
      muteHttpExceptions: true
    });
    return res.getResponseCode() === 200;
  } catch (e) {
    return false;
  }
}

/*******************************************************
 * 追加：キュー（SenkyokuQueue）関連
 *******************************************************/
const QUEUE_SHEET_NAME = "SenkyokuQueue";

/**
 * キューシートを準備
 * columns: senkyoku_url | status | last_error | pr_url | updated_at
 * status: PENDING / DONE / ERROR
 */
function ensureQueueSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(QUEUE_SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(QUEUE_SHEET_NAME);
    sheet.getRange(1, 1, 1, 5).setValues([["senkyoku_url", "status", "last_error", "pr_url", "updated_at"]]);
  }
  return sheet;
}

/**
 * ① 都道府県ページから全選挙区URLをキューに積む（初回1回でOK）
 * - https://shugiin.go2senkyo.com/50/prefecture/{prefId} をprefId=1..47で巡回
 * - href="/50/senkyoku/xxxxx" を抽出
 */
function enqueueAllSenkyokuUrls() {
  const queueSheet = ensureQueueSheet_();
  const existing = loadQueueUrlSet_(queueSheet);

  // GitHub上の既存選挙区ファイルを一括取得
  const existingFiles = getExistingDistrictFiles_();
  console.log(`既存ファイル: ${existingFiles.size}件`);

  const base = "https://shugiin.go2senkyo.com";
  const prefBase = "https://shugiin.go2senkyo.com/50/prefecture/";

  let added = 0;
  let skipped = 0;

  for (let prefId = 1; prefId <= 47; prefId++) {
    const url = prefBase + prefId;
    try {
      const html = fetchHtml_(url);
      const matches = [...html.matchAll(/href="(\/50\/senkyoku\/\d+)"/g)].map(m => m[1]);
      const uniq = [...new Set(matches)].map(p => base + p);

      for (const senkyokuUrl of uniq) {
        if (!existing.has(senkyokuUrl)) {
          // 選挙区ページからpref/districtを簡易チェック（軽量）
          try {
            const parsed = parseSenkyokuPageRich_(senkyokuUrl);
            if (parsed.pref_raw && parsed.district) {
              const key = `${parsed.pref_raw}/${parsed.district}`;
              if (existingFiles.has(key)) {
                console.log(`SKIP ${senkyokuUrl}: 既存ファイル ${key}`);
                skipped++;
                continue;
              }
            }
          } catch (e) {
            console.log(`選挙区ページ解析エラー ${senkyokuUrl}: ${e.message}`);
          }

          queueSheet.appendRow([senkyokuUrl, "PENDING", "", "", new Date()]);
          existing.add(senkyokuUrl);
          added++;
        }
      }
      Utilities.sleep(500); // レート制御
    } catch (e) {
      console.log(`pref ${prefId} skip: ${e.message}`);
    }
  }

  SpreadsheetApp.getUi().alert(`キュー追加完了: ${added}件 (既存スキップ: ${skipped}件)`);
}

function loadQueueUrlSet_(queueSheet) {
  const values = queueSheet.getDataRange().getValues();
  const set = new Set();
  for (let i = 1; i < values.length; i++) {
    const u = (values[i][0] || "").toString().trim();
    if (u) set.add(u);
  }
  return set;
}

/**
 * ② キューからN件処理（自動収集→PR）
 * - 1実行あたり件数を小さくして、時間主導トリガー運用しやすくする
 */
function processSenkyokuQueueBatch() {
  const props = PropertiesService.getScriptProperties();
  const batchSize = parseInt(props.getProperty("BATCH_SIZE") || "3", 10);

  const queueSheet = ensureQueueSheet_();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const formSheet = ss.getSheets()[0];

  const values = queueSheet.getDataRange().getValues();
  if (values.length < 2) {
    SpreadsheetApp.getUi().alert("キューが空です。まず①を実行してください。");
    return;
  }

  let processed = 0;

  for (let i = 2; i <= values.length && processed < batchSize; i++) {
    const senkyokuUrl = (values[i - 1][0] || "").toString().trim();
    const status = (values[i - 1][1] || "").toString().trim();

    if (!senkyokuUrl || status !== "PENDING") continue;

    try {
      // 1) フォーム回答シートに新規行を作る（列構造は既存のまま）
      const newRowIndex = appendEmptyResponseRow_(formSheet);

      // 2) 選挙区ページから pref/district/当/比/公報 を取得して行に反映
      const parsed = parseSenkyokuPageRich_(senkyokuUrl);
      applyParsedToResponseRow_(formSheet, newRowIndex, parsed);

      // 3) 公報PDFから公約抽出（OpenAI）→行に入力
      const out = extractPoliciesFromKohoPdfAndFillRow_(formSheet, newRowIndex);

      // 4) 既存関数は「最終行」を見るので、そのまま呼ぶ
      generateMinervaMarkdown();

      // PR URL は generateMinervaMarkdown 内で alert するだけなので、
      // ここでは「DONE」にする（必要なら createGitHubPullRequestWithLink の戻りを返すよう改修可）
      queueSheet.getRange(i, 2).setValue("DONE");
      queueSheet.getRange(i, 3).setValue("");
      queueSheet.getRange(i, 5).setValue(new Date());

      processed++;
      Utilities.sleep(800);
    } catch (e) {
      queueSheet.getRange(i, 2).setValue("ERROR");
      queueSheet.getRange(i, 3).setValue(e.message);
      queueSheet.getRange(i, 5).setValue(new Date());
      processed++;
      console.log(`ERROR ${senkyokuUrl}: ${e.message}`);
      Utilities.sleep(800);
    }
  }

  SpreadsheetApp.getUi().alert(`処理完了: ${processed}件（BATCH_SIZE=${batchSize}）`);
}

/**
 * フォーム回答シートに「空の行」を追加する
 * - フォームの最初の列(0)がタイムスタンプなら、それだけ入れる
 * - 既存列数に合わせて空配列を作る（列ずらしを防ぐ）
 */
function appendEmptyResponseRow_(formSheet) {
  const lastCol = formSheet.getLastColumn();
  const row = new Array(lastCol).fill("");
  row[0] = new Date(); // timestamp相当
  formSheet.appendRow(row);
  return formSheet.getLastRow();
}

/*******************************************************
 * 追加：選挙区ページ解析（よりリッチに）
 * - pref(日本語) と district番号も取って、pref_rawへ変換
 * - winner(当) / revival(比) / koho_pdf_url を抽出
 *******************************************************/
function parseSenkyokuPageRich_(senkyokuUrl) {
  const html = fetchHtml_(senkyokuUrl);

  // タイトルや見出しに「北海道12区」等が含まれる前提で抽出（ゆらぎに強め）
  const titleMatch = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  const titleText = titleMatch ? stripTags_(titleMatch[1]) : "";

  // 「北海道12区」的な部分を拾う
  const areaMatch = titleText.match(/(北海道|青森|岩手|宮城|秋田|山形|福島|茨城|栃木|群馬|埼玉|千葉|東京|神奈川|新潟|富山|石川|福井|山梨|長野|岐阜|静岡|愛知|三重|滋賀|京都|大阪|兵庫|奈良|和歌山|鳥取|島根|岡山|広島|山口|徳島|香川|愛媛|高知|福岡|佐賀|長崎|熊本|大分|宮崎|鹿児島|沖縄)\s*([0-9]{1,2})\s*区/);
  const pref_ja = areaMatch ? areaMatch[1] : "";
  const district = areaMatch ? areaMatch[2] : "";

  // 公報PDF
  const pdfMatch = html.match(/https:\/\/prod-cdn\.go2senkyo\.com\/public\/senkyo_koho\/[^\s"'<>]+\.pdf[^\s"'<>]*/);
  const kohoPdfUrl = pdfMatch ? pdfMatch[0] : "";

  // 当/比の候補者名・党（ページ構造が変わる可能性があるので、見つかる範囲で）
  const badgeRe = /(当|比)[\s\S]{0,400}?Image:\s*([^†\n]+)[\s\S]{0,200}?\n\s*\2\s*[\s\S]{0,200}?\n\s*\d+歳｜\s*([^\n<]+)/g;

  let winner = null;
  let revival = null;
  let m;
  while ((m = badgeRe.exec(html)) !== null) {
    const badge = (m[1] || "").trim();
    const name_ja = (m[2] || "").trim();
    const party = normalizeParty_((m[3] || "").trim());

    if (badge === "当" && !winner) winner = { name_ja, party };
    if (badge === "比" && !revival) revival = { name_ja, party };
  }

  return {
    senkyoku_url: senkyokuUrl,
    pref_ja,
    pref_raw: prefJaToRaw_(pref_ja),
    district,
    koho_pdf_url: kohoPdfUrl,
    winner,
    revival
  };
}

function stripTags_(s) {
  return (s || "").replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();
}

function prefJaToRaw_(pref_ja) {
  const map = {
    '北海道':'hokkaido','青森':'aomori','岩手':'iwate','宮城':'miyagi','秋田':'akita',
    '山形':'yamagata','福島':'fukushima','茨城':'ibaraki','栃木':'tochigi','群馬':'gunma',
    '埼玉':'saitama','千葉':'chiba','東京':'tokyo','神奈川':'kanagawa','新潟':'niigata',
    '富山':'toyama','石川':'ishikawa','福井':'fukui','山梨':'yamanashi','長野':'nagano',
    '岐阜':'gifu','静岡':'shizuoka','愛知':'aichi','三重':'mie','滋賀':'shiga',
    '京都':'kyoto','大阪':'osaka','兵庫':'hyogo','奈良':'nara','和歌山':'wakayama',
    '鳥取':'tottori','島根':'shimane','岡山':'okayama','広島':'hiroshima','山口':'yamaguchi',
    '徳島':'tokushima','香川':'kagawa','愛媛':'ehime','高知':'kochi','福岡':'fukuoka',
    '佐賀':'saga','長崎':'nagasaki','熊本':'kumamoto','大分':'oita','宮崎':'miyazaki',
    '鹿児島':'kagoshima','沖縄':'okinawa'
  };
  return map[pref_ja] || "";
}

/**
 * parse結果をフォーム回答行（既存列仕様）へ入れる
 * 既存列仕様:
 *  row[1]=pref_raw, row[2]=district, row[3]=name_ja, row[4]=name_en
 *  row[21]=hasProportional, row[22]=prop_name_ja, row[23]=prop_name_en
 *  row[34]=kouho_link, row[35]=party_main, row[36]=party_prop
 */
function applyParsedToResponseRow_(sheet, rowIndex, parsed) {
  // pref_raw (col=2)
  if (parsed.pref_raw) sheet.getRange(rowIndex, 2).setValue(parsed.pref_raw);
  // district (col=3)
  if (parsed.district) sheet.getRange(rowIndex, 3).setValue(parsed.district);

  // 公報PDF (row[34] => col=35)
  if (parsed.koho_pdf_url) sheet.getRange(rowIndex, 35).setValue(parsed.koho_pdf_url);

  // winner -> name_ja (col=4), party_main (col=36)
  if (parsed.winner) {
    sheet.getRange(rowIndex, 4).setValue(parsed.winner.name_ja);
    sheet.getRange(rowIndex, 36).setValue(parsed.winner.party);
  }

  // revival -> hasProportional (col=22), prop_name_ja (col=23), party_prop (col=37)
  if (parsed.revival) {
    sheet.getRange(rowIndex, 22).setValue("はい");
    sheet.getRange(rowIndex, 23).setValue(parsed.revival.name_ja);
    sheet.getRange(rowIndex, 37).setValue(parsed.revival.party);
  }
}

/*******************************************************
 * 追加：OpenAI（PDF入力）で公約抽出→行へ入力
 *******************************************************/
const OPENAI_ENDPOINT = "https://api.openai.com/v1/responses";

function extractPoliciesFromKohoPdfAndFillRow_(sheet, rowIndex) {
  const lastCol = sheet.getLastColumn();
  const row = sheet.getRange(rowIndex, 1, 1, lastCol).getValues()[0];

  const kohoPdfUrl = (row[34] || "").toString().trim();
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
    text: { format: { name: "minerva_koho_extract", type: "json_schema", strict: true, schema: schema.schema } },
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

  const jsonText = extractOutputText_(resp);
  if (!jsonText) throw new Error("OpenAIの出力が空です。");
  const out = JSON.parse(jsonText);

  // 行へ書き込み
  writePoliciesToRow_(sheet, rowIndex, out);

  // confidenceが低ければ上位モデル再試行（任意：ここでは medium/low のみ再実行）
  if (out.main && (out.main.confidence === "low")) {
    const fallbackModel = "gpt-4.1-mini";
    const resp2 = callOpenAIResponses_({
      model: fallbackModel,
      text: { format: { name: "minerva_koho_extract", type: "json_schema", strict: true, schema: schema.schema } },
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

/**
 * Responses APIの出力からテキスト(JSON文字列)を取り出す
 * - output_text があればそれを使う
 * - なければ output[].content[].text を連結
 */
function extractOutputText_(resp) {
  if (resp.output_text && resp.output_text.toString().trim() !== "") {
    return resp.output_text.toString().trim();
  }
  if (!resp.output || !Array.isArray(resp.output)) return "";
  let acc = "";
  for (const o of resp.output) {
    if (!o.content || !Array.isArray(o.content)) continue;
    for (const c of o.content) {
      if (c.type === "output_text" && c.text) acc += c.text;
      if (c.type === "text" && c.text) acc += c.text;
    }
  }
  return acc.trim();
}

function getScriptProp_(key, defaultValue) {
  const v = PropertiesService.getScriptProperties().getProperty(key);
  return (v === null || v === undefined || v === "") ? defaultValue : v;
}

/**
 * LLM出力を既存列に書き込み
 * - 小選挙区 policies -> row[5],7,...,19（シート列6,8,...,20）
 * - 比例 policies -> row[24],26,...,32（シート列25,27,...,33）
 * - name_enは row[4]（シート列5）
 * - prop_name_enは row[23]（シート列24）
 */
function writePoliciesToRow_(sheet, rowIndex, out) {
  const existingNameJa = (sheet.getRange(rowIndex, 4).getValue() || "").toString().trim();
  const existingPartyMain = (sheet.getRange(rowIndex, 36).getValue() || "").toString().trim();
  const existingPropNameJa = (sheet.getRange(rowIndex, 23).getValue() || "").toString().trim();
  const existingPartyProp = (sheet.getRange(rowIndex, 37).getValue() || "").toString().trim();
  const main = out.main;

  if (main) {
    if (main.name_ja && !existingNameJa) sheet.getRange(rowIndex, 4).setValue(main.name_ja);
    if (main.name_en) sheet.getRange(rowIndex, 5).setValue(main.name_en);
    if (main.party && !existingPartyMain) sheet.getRange(rowIndex, 36).setValue(normalizeParty_(main.party));

    const policies = Array.isArray(main.policies) ? main.policies : [];
    for (let k = 0; k < 8; k++) {
      const col = 6 + k * 2; // policy列
      sheet.getRange(rowIndex, col).setValue(policies[k] || "");
      sheet.getRange(rowIndex, col + 1).setValue(""); // evidence列は空
    }
  }

  const prop = out.prop;
  if (prop && prop !== null) {
    sheet.getRange(rowIndex, 22).setValue("はい");
    if (prop.name_ja && !existingPropNameJa) sheet.getRange(rowIndex, 23).setValue(prop.name_ja);
    if (prop.name_en) sheet.getRange(rowIndex, 24).setValue(prop.name_en);
    if (prop.party && !existingPartyProp) sheet.getRange(rowIndex, 37).setValue(normalizeParty_(prop.party));

    const policies = Array.isArray(prop.policies) ? prop.policies : [];
    for (let k = 0; k < 5; k++) {
      const col = 25 + k * 2;
      sheet.getRange(rowIndex, col).setValue(policies[k] || "");
      sheet.getRange(rowIndex, col + 1).setValue("");
    }
  }
}

function fetchHtml_(url) {
  const res = UrlFetchApp.fetch(url, {
    followRedirects: true,
    muteHttpExceptions: true,
    headers: { "User-Agent": "Mozilla/5.0 (compatible; MinervaBot/1.0; +https://minerva-project.org)" }
  });
  const code = res.getResponseCode();
  if (code < 200 || code >= 300) throw new Error(`Fetch failed: ${code} ${url}`);
  return res.getContentText("UTF-8");
}

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
