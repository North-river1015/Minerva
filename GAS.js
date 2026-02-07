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
  const policy_reason = row[37];

 
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

  let hasMainPolicy = false;
  for (let i = 5; i <= 20; i += 2) {
    let policy = row[i];
    let evidence = row[i+1];
    if (policy && policy.toString().trim() !== "") {
      md += formatPolicyLine(policy, evidence);
      hasMainPolicy = true;
    }
  }
  


  // 比例
  const propNameJaClean = prop_name_ja ? prop_name_ja.toString().trim() : "";
  const propNameEnClean = prop_name_en ? prop_name_en.toString().trim() : "";
  const propSlugOk = /^[a-z0-9-]+$/.test(propNameEnClean);

  if ((hasProportional === "はい" || propNameJaClean !== "")
      && propNameJaClean !== ""
      && propSlugOk) {
    md += `\n\n\n# [${propNameJaClean}](/shu/${pref_raw}/${district}/${propNameEnClean})\n\n`;
    md += `${party_prop}\n\n`; 

    for (let j = 24; j <= 32; j += 2) {
      let p_policy = row[j];
      let p_url = row[j+1];
      if (p_policy && p_policy.toString().trim() !== "") {
        md += formatPolicyLine(p_policy, p_url);
      }
    }
    
  }

  const reasonText = policy_reason ? policy_reason.toString().trim() : "";
  if (!hasMainPolicy && reasonText) {
    md += `\n（公約抽出: ${reasonText}）\n`;
  }

  if (kouho_link && kouho_link.toString().trim() !== "") {
    md += `\n[選挙公報](${kouho_link.toString().trim()})\n`;
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
      try {
        SpreadsheetApp.getUi().alert("GitHubにプルリクエストを作成\n" + prUrl);
      } catch (e) {
        console.log("UI alert skipped: " + e.message);
      }
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

      const winnerNameJa = (formSheet.getRange(newRowIndex, 4).getValue() || "").toString().trim();
      if (!winnerNameJa) {
        throw new Error("当選者名が取得できません。候補者一覧と照合してください。");
      }

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

  try {
    SpreadsheetApp.getUi().alert(`処理完了: ${processed}件（BATCH_SIZE=${batchSize}）`);
  } catch (e) {
    console.log("UI alert skipped: " + e.message);
  }
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
  const candidateSectionText = getCandidateSectionText_(html);
  const candidateNames = extractCandidateNamesFromHtml_(html);

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

  // 当/比の候補者名・党（結果グラフのブロックを優先）
  const graphBlockRe = /p_senkyoku_graph_block_elected[\s\S]*?<span>\s*(当|比)\s*<\/span>[\s\S]*?p_senkyoku_graph_block_profile_ttl[^>]*>[\s\S]*?<a[^>]*>([^<]+)<\/a>[\s\S]*?p_senkyoku_graph_block_profile_data_para[^>]*>([^<]+)<\/div>/g;

  let winner = null;
  let revival = null;
  let m;
  while ((m = graphBlockRe.exec(html)) !== null) {
    const badge = (m[1] || "").trim();
    const name_ja = stripTags_(m[2] || "").trim();
    const dataPara = stripTags_(m[3] || "").trim();
    const partyMatch = dataPara.match(/｜\s*([^\s]+)/);
    const party = normalizeParty_(partyMatch ? partyMatch[1].trim() : "");

    if (badge === "当" && !winner) winner = { name_ja, party };
    if (badge === "比" && !revival) revival = { name_ja, party };
  }

  if (!winner || !revival) {
    const textForSearch = candidateSectionText;
    const badgeTextRe = /(当|比)\s+([^\s]+(?:\s+[^\s]+)?)\s+(?:\d+歳)?\s*[｜|]\s*([^\s]+)/g;
    let m2;
    while ((m2 = badgeTextRe.exec(textForSearch)) !== null) {
      const badge = (m2[1] || "").trim();
      const name_ja = (m2[2] || "").trim();
      const party = normalizeParty_((m2[3] || "").trim());
      if (badge === "当" && !winner) winner = { name_ja, party };
      if (badge === "比" && !revival) revival = { name_ja, party };
      if (winner && revival) break;
    }
  }

  if (!winner || !revival) {
    const fullText = stripTags_(html);
    const badgeTextRe = /(当|比)\s*([^\s｜|]{2,10}(?:\s+[^\s｜|]{2,10})?)\s*(?:\d+歳)?\s*[｜|]\s*([^\s]+)/g;
    let m3;
    while ((m3 = badgeTextRe.exec(fullText)) !== null) {
      const badge = (m3[1] || "").trim();
      const name_ja = (m3[2] || "").trim();
      const party = normalizeParty_((m3[3] || "").trim());
      if (badge === "当" && !winner) winner = { name_ja, party };
      if (badge === "比" && !revival) revival = { name_ja, party };
      if (winner && revival) break;
    }
  }

  if (candidateNames.size > 0) {
    if (winner && !candidateNames.has(normalizeName_(winner.name_ja))) {
      console.log(`当選者名が候補者一覧にないため破棄: ${winner.name_ja}`);
      winner = null;
    }
    if (revival && !candidateNames.has(normalizeName_(revival.name_ja))) {
      console.log(`比例候補者名が候補者一覧にないため破棄: ${revival.name_ja}`);
      revival = null;
    }
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

function getCandidateSectionText_(html) {
  const text = stripTags_(html);
  const anchorIndex = text.indexOf("小選挙区候補者");
  let section = anchorIndex >= 0 ? text.slice(anchorIndex) : text;
  const endMarkers = ["この選挙区の前回の結果", "前回の結果", "選挙区をデータで見る", "候補者アンケートについて"];
  let endIndex = section.length;
  for (const marker of endMarkers) {
    const idx = section.indexOf(marker);
    if (idx >= 0 && idx < endIndex) endIndex = idx;
  }
  section = section.slice(0, endIndex);
  return section;
}

function extractCandidateNamesFromHtml_(html) {
  const nameSet = new Set();
  const listNameRe = /p_senkyoku_list_block_name[^>]*>[\s\S]*?<p class="text">([\s\S]*?)<\/p>/g;
  const graphNameRe = /p_senkyoku_graph_block_profile_ttl[^>]*>[\s\S]*?<a[^>]*>([^<]+)<\/a>/g;

  let m;
  while ((m = listNameRe.exec(html)) !== null) {
    const name = normalizeName_(stripTags_(m[1] || ""));
    if (name) nameSet.add(name);
  }

  while ((m = graphNameRe.exec(html)) !== null) {
    const name = normalizeName_(stripTags_(m[1] || ""));
    if (name) nameSet.add(name);
  }

  return nameSet;
}

function normalizeName_(name) {
  return (name || "").toString().replace(/\s+/g, "").trim();
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

  const debugPdfText = getScriptProp_("DEBUG_PDF_TEXT", "false").toString().toLowerCase() === "true";
  const useVisionOcr = getScriptProp_("USE_VISION_OCR", "false").toString().toLowerCase() === "true";
  const useDriveOcr = getScriptProp_("USE_DRIVE_OCR", "false").toString().toLowerCase() === "true";
  const hasVisionKey = !!getScriptProp_("VISION_API_KEY", "");
  console.log("OCR flags: useVisionOcr=" + useVisionOcr + ", useDriveOcr=" + useDriveOcr + ", debugPdfText=" + debugPdfText + ", hasVisionKey=" + hasVisionKey);
  let ocrText = "";
  let ocrSource = "";
  const winnerNameJa = (row[3] || "").toString().trim();
  const winnerParty = (row[35] || "").toString().trim();
  const revivalNameJa = (row[22] || "").toString().trim();
  const revivalParty = (row[36] || "").toString().trim();

  if (useVisionOcr) {
    console.log("Vision OCR start");
    try {
      ocrText = extractPdfTextWithVisionOcr_(kohoPdfUrl, winnerNameJa, winnerParty);
      ocrSource = "vision";
      if (!ocrText) console.log("Vision OCR returned empty text");
    } catch (e) {
      console.log("Vision OCR failed: " + e.message);
    }
  }

  if (!ocrText && useDriveOcr) {
    try {
      ocrText = extractPdfTextWithDriveOcr_(kohoPdfUrl);
      ocrSource = "drive";
    } catch (e) {
      console.log("Drive OCR failed: " + e.message);
    }
  }

  let focusedOcrText = "";
  if (ocrText && winnerNameJa) {
    focusedOcrText = buildCandidateFocusedText_(ocrText, winnerNameJa, winnerParty);
    if (focusedOcrText) {
      console.log("OCR focused text length: " + focusedOcrText.length);
    }
  }

  const rawOcr = focusedOcrText || ocrText;
  const cleanedOcr = rawOcr ? removeCandidateListLines_(rawOcr) : "";
  const candidatePolicyText = cleanedOcr ? buildPolicyCandidateText_(cleanedOcr, winnerNameJa, winnerParty) : "";
  if (candidatePolicyText) {
    console.log("OCR policy candidate lines: " + candidatePolicyText.split("\n").length);
  }

  if (debugPdfText) {
    try {
      if (ocrText && ocrSource === "vision") {
        console.log("Vision OCR text (head):");
        console.log(ocrText.length > 4000 ? ocrText.slice(0, 4000) : ocrText);
        if (focusedOcrText) {
          console.log("Vision OCR focused text (head):");
          console.log(focusedOcrText.length > 2000 ? focusedOcrText.slice(0, 2000) : focusedOcrText);
        }
        if (candidatePolicyText) {
          console.log("Vision OCR policy candidates (head):");
          console.log(candidatePolicyText.length > 2000 ? candidatePolicyText.slice(0, 2000) : candidatePolicyText);
        }
      } else if (useDriveOcr && ocrText) {
        console.log("Drive OCR text (head):");
        console.log(ocrText.length > 4000 ? ocrText.slice(0, 4000) : ocrText);
        if (focusedOcrText) {
          console.log("Drive OCR focused text (head):");
          console.log(focusedOcrText.length > 2000 ? focusedOcrText.slice(0, 2000) : focusedOcrText);
        }
        if (candidatePolicyText) {
          console.log("Drive OCR policy candidates (head):");
          console.log(candidatePolicyText.length > 2000 ? candidatePolicyText.slice(0, 2000) : candidatePolicyText);
        }
      } else {
        const pdfText = extractPdfTextForDebug_(kohoPdfUrl);
        console.log("PDF extracted text (head):");
        console.log(pdfText);
      }
    } catch (e) {
      console.log("PDF text debug failed: " + e.message);
    }
  }

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
              items: {
                type: "object",
                additionalProperties: false,
                properties: {
                  policy: { type: "string" },
                  evidence: { type: "string" },
                  type: { type: "string", enum: ["policy", "achievement"] }
                },
                required: ["policy", "evidence", "type"]
              },
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
                  items: {
                    type: "object",
                    additionalProperties: false,
                    properties: {
                      policy: { type: "string" },
                      evidence: { type: "string" },
                      type: { type: "string", enum: ["policy", "achievement"] }
                    },
                    required: ["policy", "evidence", "type"]
                  },
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
- PDFに明記された内容のみ抽出。推測・一般論は禁止。
- 入力テキストには見出しと箇条書きが混在する。見出しと箇条書きの関係を解釈して政策か実績かを判断する。
- policy は「これから実行すること/実現すること/進めること」。achievement は「実績/達成済み/経歴/プロフィール/活動」。
- 各項目に type を必ず付ける（policy または achievement）。
- 1項目は短く（30〜60文字程度）。重複はまとめる。
- evidence はPDF内の原文から短く「完全一致」で引用（20〜40文字程度）。見出しだけの引用は不可。
- evidence を原文から抜き出せない場合、その項目は出力しない。
  - policy が無ければ policies は空配列にし、confidence は low。
  - 見出しが複数ある場合は、可能なら見出しごとに1件ずつ抽出する（合計は最大8件）。
- main は小選挙区の当選者（ヒント: ${winnerNameJa || "不明"} / ${winnerParty || "不明"}）。
- prop は比例復活がいる場合のみ（ヒント: ${revivalNameJa || "なし"} / ${revivalParty || "なし"}）。いなければ null。
- name_en は URL スラッグ形式: 例 "takebe-arata"（小文字・ハイフン区切り、英字のみ）。
- party はフォーム選択肢に寄せた正式名（例: 自由民主党 / 立憲民主党 / 国民民主党 / 日本維新の会 / 日本共産党 / れいわ新選組 / 社会民主党 / 参政党 / 公明党 / 他）。
- confidence は、公報内で政策欄が明確に読めたら high、怪しければ low。

出力はJSONのみ。`;

  const model = getScriptProp_("OPENAI_MODEL", "gpt-4o-mini");
  const ocrTextForPrompt = candidatePolicyText
    ? (candidatePolicyText.length > 12000 ? candidatePolicyText.slice(0, 12000) : candidatePolicyText)
    : (rawOcr ? (rawOcr.length > 12000 ? rawOcr.slice(0, 12000) : rawOcr) : "");
  const resp = callOpenAIResponses_({
    model,
    text: { format: { name: "minerva_koho_extract", type: "json_schema", strict: true, schema: schema.schema } },
    input: [
      {
        role: "user",
        content: [
          ...(ocrTextForPrompt
            ? [{ type: "input_text", text: instruction + "\n\n[OCR_TEXT]\n" + ocrTextForPrompt }]
            : [
                { type: "input_file", file_url: kohoPdfUrl },
                { type: "input_text", text: instruction }
              ])
        ]
      }
    ]
  });

  const jsonText = extractOutputText_(resp);
  if (!jsonText) throw new Error("OpenAIの出力が空です。");
  console.log("OpenAI raw output JSON:");
  console.log(jsonText);
  const out = JSON.parse(jsonText);
  if (!revivalNameJa) {
    out.prop = null;
  }
  const beforeMainPolicies = (out.main && Array.isArray(out.main.policies)) ? out.main.policies.length : 0;
  const beforePropPolicies = (out.prop && Array.isArray(out.prop.policies)) ? out.prop.policies.length : 0;
  let removedByEvidence = { main: 0, prop: 0 };
  if (rawOcr) {
    removedByEvidence = validatePoliciesWithEvidence_(out, rawOcr);
  }
  let addedFromCandidates = { main: 0, prop: 0 };
  if (rawOcr && candidatePolicyText) {
    addedFromCandidates = fillPoliciesFromCandidates_(out, candidatePolicyText, rawOcr);
  }
  const policyContext = {
    winnerNameJa,
    winnerParty,
    ocrSource,
    hasOcrText: !!ocrText,
    hasFocusedText: !!focusedOcrText,
    candidateLineCount: candidatePolicyText ? candidatePolicyText.split("\n").length : 0,
    beforeMainPolicies,
    beforePropPolicies,
    removedByEvidence,
    addedFromCandidates
  };
  logPolicyExtractionSummary_(out, policyContext);
  const policyReason = computePolicyExtractionReason_(out, policyContext);
  sheet.getRange(rowIndex, 38).setValue(policyReason || "");

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

function extractPdfTextForDebug_(kohoPdfUrl) {
  const model = getScriptProp_("OPENAI_MODEL", "gpt-4o-mini");
  const resp = callOpenAIResponses_({
    model,
    input: [
      {
        role: "user",
        content: [
          { type: "input_file", file_url: kohoPdfUrl },
          { type: "input_text", text: "PDFの本文をテキスト化して、先頭4000文字だけを出力してください。出力は本文テキストのみ。" }
        ]
      }
    ]
  });

  const text = extractOutputText_(resp);
  if (!text) return "";
  return text.length > 4000 ? text.slice(0, 4000) : text;
}

function extractPdfTextWithDriveOcr_(kohoPdfUrl) {
  const blob = UrlFetchApp.fetch(kohoPdfUrl).getBlob().setName("koho.pdf");
  const resource = {
    title: "koho_ocr_" + new Date().getTime()
  };

  let docId = "";
  try {
    const file = Drive.Files.insert(resource, blob, { ocr: true, ocrLanguage: "ja", convert: true });
    docId = file.id;
    return DocumentApp.openById(docId).getBody().getText();
  } finally {
    if (docId) {
      try {
        Drive.Files.remove(docId);
      } catch (e) {
        console.log("Drive OCR cleanup failed: " + e.message);
      }
    }
  }
}

function extractPdfTextWithVisionOcr_(kohoPdfUrl, winnerNameJa, winnerParty) {
  const apiKey = getScriptProp_("VISION_API_KEY", "");
  if (!apiKey) throw new Error("ScriptProperties に VISION_API_KEY を設定してください。");

  const debug = getScriptProp_("DEBUG_PDF_TEXT", "false").toString().toLowerCase() === "true";

  const blob = UrlFetchApp.fetch(kohoPdfUrl).getBlob();
  const content = Utilities.base64Encode(blob.getBytes());

  const payload = {
    requests: [
      {
        inputConfig: {
          content: content,
          mimeType: "application/pdf"
        },
        features: [
          { type: "DOCUMENT_TEXT_DETECTION" }
        ]
      }
    ]
  };

  const res = UrlFetchApp.fetch("https://vision.googleapis.com/v1/files:annotate?key=" + apiKey, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const code = res.getResponseCode();
  const body = res.getContentText();
  if (code >= 300) throw new Error("Vision API error: " + code + " " + body);

  const json = JSON.parse(body);
  if (!json.responses || !Array.isArray(json.responses)) return "";
  if (debug) console.log("Vision OCR responses: " + json.responses.length);
  const texts = [];
  let focusedText = "";
  const winnerKey = normalizeName_(winnerNameJa);
  for (const r of json.responses) {
    if (debug && r.error && r.error.message) {
      console.log("Vision OCR response error: " + r.error.message);
    }
    if (Array.isArray(r.responses)) {
      if (debug) console.log("Vision OCR page responses: " + r.responses.length);
      for (let pageIndex = 0; pageIndex < r.responses.length; pageIndex++) {
        const page = r.responses[pageIndex];
        if (debug && page.error && page.error.message) {
          console.log("Vision OCR page error: " + page.error.message);
        }
        if (page.fullTextAnnotation && page.fullTextAnnotation.text) {
          texts.push(page.fullTextAnnotation.text);
        }
        if (!focusedText && winnerKey && page.fullTextAnnotation && page.fullTextAnnotation.pages) {
          const blockTexts = extractVisionBlockTexts_(page.fullTextAnnotation.pages);
          const focus = focusVisionBlocks_(blockTexts, winnerKey, winnerParty, 2, 8);
          if (focus) {
            focusedText = focus;
            if (debug) console.log("Vision OCR block focus: page=" + (pageIndex + 1));
          }
        }
      }
      continue;
    }
    if (r.fullTextAnnotation && r.fullTextAnnotation.text) {
      texts.push(r.fullTextAnnotation.text);
    }
  }
  if (debug && texts.length === 0) console.log("Vision OCR responses had no fullTextAnnotation");
  if (focusedText) return focusedText;
  return texts.join("\n");
}

function extractVisionBlockTexts_(pages) {
  const blocks = [];
  for (const page of pages) {
    const pageBlocks = page.blocks || [];
    const pageWidth = page.width || 0;
    const pageHeight = page.height || 0;
    for (const block of pageBlocks) {
      const text = extractVisionBlockText_(block);
      if (!text) continue;
      const info = {
        text: text,
        box: normalizeVisionBlockBox_(block.boundingBox),
        pageWidth: pageWidth,
        pageHeight: pageHeight
      };
      blocks.push(info);
    }
  }
  return blocks;
}

function extractVisionBlockText_(block) {
  const parts = [];
  const paragraphs = block.paragraphs || [];
  for (const paragraph of paragraphs) {
    const words = paragraph.words || [];
    for (const word of words) {
      const symbols = word.symbols || [];
      const wordText = symbols.map(s => s.text || "").join("");
      if (wordText) parts.push(wordText);
    }
  }
  return parts.join(" ").trim();
}

function focusVisionBlocks_(blockTexts, winnerKey, winnerParty, beforeCount, afterCount) {
  if (!blockTexts || blockTexts.length === 0 || !winnerKey) return "";
  const hits = [];
  for (let i = 0; i < blockTexts.length; i++) {
    const key = normalizeName_(blockTexts[i].text);
    if (key.includes(winnerKey)) {
      hits.push(i);
    }
  }
  if (hits.length === 0) return "";

  let anchorIndex = hits[0];
  for (const idx of hits) {
    const text = blockTexts[idx].text;
    if (isPolicyCueText_(text) && !isCandidateListBlock_(text)) {
      anchorIndex = idx;
      break;
    }
  }

  const anchor = blockTexts[anchorIndex];
  const bandsFromFrames = collectCandidateBandsFromFrames_(blockTexts, 0.05);
  const fallbackBands = [];
  const winnerBand = findCandidateBandByWinnerFrame_(blockTexts, winnerKey);
  if (winnerBand) fallbackBands.push(winnerBand);
  const anchorBand = findCandidateBandForBlock_(blockTexts, anchor);
  if (anchorBand) fallbackBands.push(anchorBand);

  const candidateBands = bandsFromFrames.length > 0 ? bandsFromFrames : fallbackBands;
  const scoredBand = pickBestBandByScore_(candidateBands, blockTexts, winnerKey, winnerParty);
  if (!scoredBand) return "";

  const otherNames = extractOtherCandidateNamesFromOcr_(blockTexts.map(b => b.text || ""), winnerKey);
  const focusedBlocks = blockTexts.filter(b => boxesOverlapY_(b.box, scoredBand)
    && !isElectionNoticeBlock_(b.text)
    && !isOtherCandidateBlock_(b.text, winnerKey, winnerParty, otherNames));
  if (focusedBlocks.length === 0) return "";

  const hasWinnerName = focusedBlocks.some(b => normalizeName_(b.text).includes(winnerKey));
  if (!hasWinnerName) return "";

  if (winnerParty) {
    const winnerPartyKey = normalizePartyText_(winnerParty);
    let hasWinnerParty = false;
    let hasOtherParty = false;
    for (const block of focusedBlocks) {
      const text = (block.text || "").toString();
      if (!hasWinnerParty && winnerPartyKey && normalizePartyText_(text).indexOf(winnerPartyKey) >= 0) {
        hasWinnerParty = true;
      }
      if (!hasOtherParty && findOtherPartyInText_(text, winnerParty)) {
        hasOtherParty = true;
      }
    }
    if (hasOtherParty && !hasWinnerParty) return "";
  }

  let pickedBlocks = focusedBlocks;
  const nameBand = findNameBandFromBlocks_(blockTexts, winnerKey, 0.06);
  if (nameBand) {
    const narrowed = focusedBlocks.filter(b => boxesOverlapY_(b.box, nameBand));
    if (narrowed.length > 0) {
      const narrowedText = narrowed.map(b => b.text).join("\n");
      const hasPolicyCue = narrowed.some(b => isPolicyCueText_(b.text));
      if (narrowedText.replace(/\s+/g, "").length >= 200 || hasPolicyCue) {
        pickedBlocks = narrowed;
      }
    }
  }

  const focused = pickedBlocks.map(b => b.text).join("\n");
  if (focused.replace(/\s+/g, "").length < 200) return "";
  return focused;
}

function collectCandidateBandsFromFrames_(blockTexts, toleranceRatio) {
  if (!blockTexts || blockTexts.length === 0) return [];
  const pageHeight = blockTexts[0].pageHeight || 0;
  const pageWidth = blockTexts[0].pageWidth || 0;
  if (!pageHeight || !pageWidth) return [];

  const lineBlocks = blockTexts.filter(block => {
    if (!block.box || block.pageHeight !== pageHeight) return false;
    const widthRatio = (block.box.width || 0) / pageWidth;
    const heightRatio = (block.box.height || 0) / pageHeight;
    if (widthRatio < 0.7) return false;
    if (heightRatio > 0.05) return false;
    return true;
  }).sort((a, b) => a.box.minY - b.box.minY);

  if (lineBlocks.length < 2) return [];

  const frames = [];
  for (let i = 0; i < lineBlocks.length - 1; i++) {
    const top = lineBlocks[i];
    const bottom = lineBlocks[i + 1];
    const height = bottom.box.maxY - top.box.minY;
    const heightRatio = height / pageHeight;
    if (heightRatio < 0.08 || heightRatio > 0.7) continue;
    frames.push({
      minY: top.box.minY,
      maxY: bottom.box.maxY,
      heightRatio: heightRatio,
      pageHeight: pageHeight
    });
  }
  if (frames.length === 0) return [];

  let bestHeight = null;
  let bestCount = 0;
  for (const frame of frames) {
    let count = 0;
    for (const other of frames) {
      if (Math.abs(other.heightRatio - frame.heightRatio) <= toleranceRatio) count++;
    }
    if (count > bestCount || (count === bestCount && (!bestHeight || frame.heightRatio < bestHeight))) {
      bestCount = count;
      bestHeight = frame.heightRatio;
    }
  }

  return frames.filter(frame => Math.abs(frame.heightRatio - bestHeight) <= toleranceRatio);
}

function pickBestBandByScore_(bands, blockTexts, winnerKey, winnerParty) {
  if (!bands || bands.length === 0) return null;
  let best = null;
  let bestScore = -Infinity;
  for (const band of bands) {
    const score = scoreCandidateBand_(band, blockTexts, winnerKey, winnerParty);
    if (score > bestScore) {
      bestScore = score;
      best = band;
    }
  }
  return best;
}

function scoreCandidateBand_(band, blockTexts, winnerKey, winnerParty) {
  if (!band) return -Infinity;
  const blocks = blockTexts.filter(b => b.box && boxesOverlapY_(b.box, band));
  if (blocks.length === 0) return -Infinity;

  const otherNames = extractOtherCandidateNamesFromOcr_(blockTexts.map(b => b.text || ""), winnerKey);

  let score = 0;
  let policyHits = 0;
  let noiseHits = 0;
  let winnerHit = false;
  let otherNameHits = 0;
  let partyHits = 0;
  let otherPartyHits = 0;

  const winnerPartyKey = winnerParty ? normalizePartyText_(winnerParty) : "";

  for (const block of blocks) {
    const text = (block.text || "").toString();
    const key = normalizeName_(text);
    const normalizedText = normalizePartyText_(text);
    if (key.includes(winnerKey)) winnerHit = true;
    if (otherNames.size > 0) {
      for (const other of otherNames) {
        if (other && key.includes(other)) {
          otherNameHits += 1;
          break;
        }
      }
    }
    if (isPolicyCueText_(text)) policyHits += 1;
    if (isCandidateListBlock_(text)) noiseHits += 1;
    if (isElectionNoticeBlock_(text)) noiseHits += 2;
    if (/プロフィール|経歴|略歴|実績/.test(text)) noiseHits += 1;

    if (winnerParty) {
      if (winnerPartyKey && normalizedText.indexOf(winnerPartyKey) >= 0) partyHits += 1;
      const otherParty = findOtherPartyInText_(text, winnerParty);
      if (otherParty) otherPartyHits += 1;
    }
  }

  if (winnerHit) score += 120;
  score += policyHits * 12;
  score -= noiseHits * 10;
  score -= otherNameHits * 18;
  score += partyHits * 15;
  score -= otherPartyHits * 20;

  if (band.heightRatio && band.pageHeight) {
    const heightScore = Math.max(0, 20 - Math.round(band.heightRatio * 100));
    score += heightScore;
  }

  return score;
}

function findOtherPartyInText_(text, winnerParty) {
  const s = (text || "").toString();
  if (!s) return "";
  const normalized = normalizePartyText_(s);
  const parties = [
    "自由民主党",
    "自民党",
    "公明党",
    "立憲民主党",
    "日本維新の会",
    "日本維新会",
    "日本共産党",
    "国民民主党",
    "れいわ新選組",
    "社会民主党",
    "参政党"
  ];
  const winnerKey = normalizePartyText_(winnerParty);
  for (const party of parties) {
    const partyKey = normalizePartyText_(party);
    if (!partyKey) continue;
    if (partyKey === winnerKey) continue;
    if (normalized.indexOf(partyKey) >= 0) return party;
  }
  return "";
}

function normalizePartyText_(text) {
  return (text || "").toString().replace(/[\s\u3000]+/g, "").replace(/[・·･]/g, "").trim();
}

function isOtherPartyCueLine_(line, winnerParty) {
  const s = (line || "").toString();
  if (!s) return false;
  if (findOtherPartyInText_(s, winnerParty)) return true;
  if (/(共産主義|赤旗)/.test(s)) return true;
  if (/SANSEITO/i.test(s)) return true;
  return false;
}

function isOtherCandidateBlock_(text, winnerKey, winnerParty, otherNames) {
  const s = (text || "").toString();
  if (!s) return false;
  const key = normalizeName_(s);
  if (winnerKey && key.includes(winnerKey)) return false;
  if (winnerParty) {
    const normalized = normalizePartyText_(s);
    const winnerPartyKey = normalizePartyText_(winnerParty);
    if (winnerPartyKey && normalized.indexOf(winnerPartyKey) >= 0) return false;
  }

  if (otherNames && otherNames.size > 0) {
    for (const other of otherNames) {
      if (other && key.includes(other)) return true;
    }
  }

  if (winnerParty) {
    const otherParty = findOtherPartyInText_(s, winnerParty);
    if (otherParty) {
      if (/(公認|比例|公約|党\s*公約|党\s*比例|党\s*へ|SANSEITO)/.test(s)) return true;
      if (isCandidateListBlock_(s)) return true;
    }
  }

  return false;
}

function isAcademicProfileLine_(line) {
  const s = (line || "").toString().trim();
  if (!s) return false;
  const hasSchool = /(大学院|大学|学部|高校|中学校|小学校)/.test(s);
  const hasBio = /(卒業|修了|教授|准教授|講師|研究)/.test(s);
  return hasSchool && hasBio;
}

function expandStarBulletLines_(lines) {
  const out = [];
  for (const line of lines) {
    if (line.indexOf("★") === -1) {
      out.push(line);
      continue;
    }
    const parts = line.split("★");
    const prefix = (parts[0] || "").trim();
    if (prefix.length >= 20) out.push(prefix);
    for (let i = 1; i < parts.length; i++) {
      const body = (parts[i] || "").trim();
      if (!body) continue;
      out.push("★ " + body);
    }
  }
  return out;
}

function findNameBandFromBlocks_(blockTexts, winnerKey, padRatio) {
  let minY = Infinity;
  let maxY = -Infinity;
  let pageHeight = 0;
  for (const block of blockTexts) {
    const key = normalizeName_(block.text);
    if (!key.includes(winnerKey)) continue;
    if (!block.box) continue;
    minY = Math.min(minY, block.box.minY);
    maxY = Math.max(maxY, block.box.maxY);
    if (block.pageHeight) pageHeight = block.pageHeight;
  }
  if (!isFinite(minY) || !isFinite(maxY)) return null;
  const ratio = typeof padRatio === "number" ? padRatio : 0.2;
  const pad = pageHeight > 0 ? pageHeight * ratio : 200;
  return {
    minY: Math.max(0, minY - pad),
    maxY: maxY + pad
  };
}

function findCandidateBandByWinnerFrame_(blockTexts, winnerKey) {
  const winnerBlocks = blockTexts.filter(block => {
    if (!block.box) return false;
    const key = normalizeName_(block.text);
    return key.includes(winnerKey);
  });
  if (winnerBlocks.length === 0) return null;

  let winnerCenter = 0;
  for (const block of winnerBlocks) {
    winnerCenter += (block.box.minY + block.box.maxY) / 2;
  }
  winnerCenter = winnerCenter / winnerBlocks.length;

  let best = null;
  let fallback = null;
  for (const block of blockTexts) {
    if (!block.box || !block.pageHeight) continue;
    const pageWidth = block.pageWidth || 0;
    const pageHeight = block.pageHeight || 0;
    const width = block.box.width || 0;
    const height = block.box.height || 0;
    const widthRatio = pageWidth > 0 ? width / pageWidth : 0;
    const heightRatio = pageHeight > 0 ? height / pageHeight : 0;
    if (widthRatio < 0.7) continue;
    if (heightRatio < 0.08 || heightRatio > 0.6) continue;
    const band = { minY: block.box.minY, maxY: block.box.maxY, heightRatio: heightRatio, pageHeight: pageHeight };
    const hasWinner = winnerBlocks.some(w => boxesOverlapY_(w.box, band));
    const bandBlocks = blockTexts.filter(b => b.box && boxesOverlapY_(b.box, band));
    const hasPolicy = bandBlocks.some(b => isPolicyCueText_(b.text) && !isCandidateListBlock_(b.text) && !isElectionNoticeBlock_(b.text));
    if (hasWinner && hasPolicy) {
      if (!best || heightRatio < best.heightRatio) best = band;
      continue;
    }
    if (!hasPolicy) continue;
    const distance = band.minY >= winnerCenter
      ? band.minY - winnerCenter
      : (winnerCenter - band.maxY) + pageHeight;
    if (!fallback || distance < fallback.distance) fallback = { band: band, distance: distance };
  }
  if (!best && fallback) best = fallback.band;
  if (!best) return null;
  const pageHeight = best.pageHeight || 0;
  const pad = pageHeight > 0 ? pageHeight * 0.04 : 40;
  return { minY: Math.max(0, best.minY - pad), maxY: best.maxY + pad };
}

function findCandidateBandByFrameLines_(blockTexts, winnerKey, toleranceRatio) {
  const winnerBlocks = blockTexts.filter(block => {
    if (!block.box) return false;
    const key = normalizeName_(block.text);
    return key.includes(winnerKey);
  });
  if (winnerBlocks.length === 0) return null;

  const pageHeight = winnerBlocks[0].pageHeight || 0;
  const pageWidth = winnerBlocks[0].pageWidth || 0;
  if (!pageHeight || !pageWidth) return null;

  const lineBlocks = blockTexts.filter(block => {
    if (!block.box || block.pageHeight !== pageHeight) return false;
    const widthRatio = (block.box.width || 0) / pageWidth;
    const heightRatio = (block.box.height || 0) / pageHeight;
    if (widthRatio < 0.7) return false;
    if (heightRatio > 0.05) return false;
    return true;
  }).sort((a, b) => a.box.minY - b.box.minY);

  if (lineBlocks.length < 2) return null;

  const frames = [];
  for (let i = 0; i < lineBlocks.length - 1; i++) {
    const top = lineBlocks[i];
    const bottom = lineBlocks[i + 1];
    const height = bottom.box.maxY - top.box.minY;
    const heightRatio = height / pageHeight;
    if (heightRatio < 0.08 || heightRatio > 0.7) continue;
    frames.push({
      minY: top.box.minY,
      maxY: bottom.box.maxY,
      heightRatio: heightRatio
    });
  }
  if (frames.length === 0) return null;

  let bestHeight = null;
  let bestCount = 0;
  for (const frame of frames) {
    let count = 0;
    for (const other of frames) {
      if (Math.abs(other.heightRatio - frame.heightRatio) <= toleranceRatio) count++;
    }
    if (count > bestCount || (count === bestCount && (!bestHeight || frame.heightRatio < bestHeight))) {
      bestCount = count;
      bestHeight = frame.heightRatio;
    }
  }

  const accepted = frames.filter(frame => Math.abs(frame.heightRatio - bestHeight) <= toleranceRatio);
  if (accepted.length === 0) return null;

  const winnerCenter = winnerBlocks.reduce((sum, block) => sum + (block.box.minY + block.box.maxY) / 2, 0) / winnerBlocks.length;
  let best = null;
  for (const frame of accepted) {
    const hasWinner = winnerBlocks.some(block => boxesOverlapY_(block.box, frame));
    if (hasWinner) {
      if (!best || frame.heightRatio < best.heightRatio) best = frame;
    }
  }
  if (!best) {
    let closest = null;
    let bestDistance = Infinity;
    for (const frame of accepted) {
      const distance = frame.minY <= winnerCenter && frame.maxY >= winnerCenter
        ? 0
        : Math.min(Math.abs(frame.minY - winnerCenter), Math.abs(frame.maxY - winnerCenter));
      if (distance < bestDistance) {
        bestDistance = distance;
        closest = frame;
      }
    }
    best = closest;
  }
  if (!best) return null;

  const pad = pageHeight * 0.02;
  return { minY: Math.max(0, best.minY - pad), maxY: best.maxY + pad };
}

function normalizeVisionBlockBox_(boundingBox) {
  const vertices = (boundingBox && boundingBox.vertices) ? boundingBox.vertices : [];
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const v of vertices) {
    const x = typeof v.x === "number" ? v.x : 0;
    const y = typeof v.y === "number" ? v.y : 0;
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }
  if (!isFinite(minX) || !isFinite(minY) || !isFinite(maxX) || !isFinite(maxY)) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 };
  }
  return { minX: minX, minY: minY, maxX: maxX, maxY: maxY, width: maxX - minX, height: maxY - minY };
}

function findCandidateBandForBlock_(blocks, anchor) {
  if (!anchor || !anchor.box || !anchor.pageHeight) return null;
  const pageHeight = anchor.pageHeight;
  const pageWidth = anchor.pageWidth || 0;
  const anchorCenter = (anchor.box.minY + anchor.box.maxY) / 2;
  let best = null;
  for (const block of blocks) {
    if (!block.box || !block.pageHeight) continue;
    const width = block.box.width || 0;
    const height = block.box.height || 0;
    const widthRatio = pageWidth > 0 ? width / pageWidth : 0;
    const heightRatio = pageHeight > 0 ? height / pageHeight : 0;
    if (widthRatio < 0.7) continue;
    if (heightRatio < 0.08 || heightRatio > 0.45) continue;
    if (anchorCenter < block.box.minY || anchorCenter > block.box.maxY) continue;
    if (!best || heightRatio > best.heightRatio) {
      best = { minY: block.box.minY, maxY: block.box.maxY, heightRatio: heightRatio };
    }
  }
  if (!best) {
    const pad = pageHeight * 0.12;
    return { minY: Math.max(0, anchor.box.minY - pad), maxY: anchor.box.maxY + pad };
  }
  const pad = pageHeight * 0.04;
  return { minY: Math.max(0, best.minY - pad), maxY: best.maxY + pad };
}

function boxesOverlapY_(box, band) {
  if (!box || !band) return false;
  return box.maxY >= band.minY && box.minY <= band.maxY;
}

function isPolicyCueText_(text) {
  const s = (text || "").toString();
  return /政策|重点政策|大政策|つの挑戦|ビジョン|公約|\d+つの策|挑戦|計画|推進|目指|実現|\u2460|\u2461|\u2462|\u2463|\u2464/.test(s);
}

function isCandidateListBlock_(text) {
  const s = (text || "").toString();
  if (isPolicyCueText_(s)) return false;
  const tokens = s.split(/\s+/).filter(t => t !== "");
  if (tokens.length < 6) return false;
  const shortCount = tokens.filter(t => t.length <= 3).length;
  if (shortCount >= 6 && !/[。．\.！？!]/.test(s)) return true;
  return false;
}

function buildCandidateFocusedText_(ocrText, nameJa, partyJa) {
  const lines = (ocrText || "").split(/\r?\n/).map(l => l.trim()).filter(l => l !== "");
  if (lines.length === 0) return "";

  const nameKey = normalizeName_(nameJa);
  if (!nameKey) return "";

  const nameParts = (nameJa || "").toString().trim().split(/\s+/).filter(p => p !== "");
  const otherNames = extractOtherCandidateNamesFromOcr_(lines, nameKey);
  let hitIndex = -1;

  for (let i = 0; i < lines.length; i++) {
    const lineKey = normalizeName_(lines[i]);
    const nextKey = i + 1 < lines.length ? normalizeName_(lines[i + 1]) : "";
    if ((lineKey + nextKey).includes(nameKey)) {
      hitIndex = i;
      break;
    }
    if (lineKey.includes(nameKey)) {
      hitIndex = i;
      break;
    }
    if (nameParts.length >= 2) {
      const partMatch = nameParts.some(part => lineKey.includes(part));
      if (partMatch) {
        hitIndex = i;
        break;
      }
    }
  }

  if (hitIndex < 0) return "";

  let windowBefore = 60;
  let windowAfter = otherNames.size > 0 ? 900 : 1200;
  const picked = [];
  let start = Math.max(0, hitIndex - windowBefore);
  let sawPolicySection = false;

  const starScanLimit = Math.min(lines.length, hitIndex + 120);
  for (let k = hitIndex; k < starScanLimit; k++) {
    if (/^\s*★/.test(lines[k])) {
      start = k;
      windowBefore = 0;
      windowAfter = Math.min(windowAfter, 300);
      break;
    }
  }

  for (let j = start; j < lines.length && j <= hitIndex + windowAfter; j++) {
    const lineKey = normalizeName_(lines[j]);
    const nextKey = j + 1 < lines.length ? normalizeName_(lines[j + 1]) : "";
    if (lineKey && (lineKey + nextKey).includes(nameKey)) {
      picked.push(lines[j]);
      continue;
    }
    if (/8つの策|\d+つの策/.test(lines[j]) || /^[①-⑳]/.test(lines[j])) {
      sawPolicySection = true;
    }
    if (sawPolicySection && /プロフィール/.test(lines[j])) {
      return picked.join("\n");
    }
    if (partyJa && isOtherPartyCueLine_(lines[j], partyJa)) {
      if (sawPolicySection) return picked.join("\n");
      continue;
    }

    if (!sawPolicySection && otherNames.size > 0) {
      for (const other of otherNames) {
        if (lineKey.includes(other)) {
          return picked.join("\n");
        }
      }
    }
    picked.push(lines[j]);
  }

  return picked.join("\n");
}

function buildPolicyCandidateText_(ocrText, winnerNameJa, winnerParty) {
  const rawLines = (ocrText || "").split(/\r?\n/).map(l => l.trim()).filter(l => l !== "");
  const lines = expandStarBulletLines_(rawLines);
  if (lines.length === 0) return "";

  const winnerKey = normalizeName_(winnerNameJa);
  const otherNames = winnerKey ? extractOtherCandidateNamesFromOcr_(lines, winnerKey) : new Set();

  const capCount = inferPolicyCountCap_(lines);
  const sections = [];
  let currentHeading = "";
  let currentItems = [];
  let prevWasBullet = false;
  let skipSection = false;
  let currentLimit = 0;
  let sawPolicyItem = false;
  let inStarSection = false;
  let nonBulletAfterStar = 0;
  let otherPartyLock = false;

  const hasWinnerInLine = (idx) => {
    if (!winnerKey) return false;
    const lineKey = normalizeName_(lines[idx]);
    const nextKey = idx + 1 < lines.length ? normalizeName_(lines[idx + 1]) : "";
    return (lineKey + nextKey).includes(winnerKey) || lineKey.includes(winnerKey);
  };

  const flush = () => {
    if (currentItems.length === 0) return;
    const title = currentHeading ? currentHeading : "その他";
    sections.push({ heading: title, items: currentItems.slice() });
    currentItems = [];
  };

  const hasAnyHeading = lines.some(line => isHeadingLine_(line));
  const forceSingleSection = !hasAnyHeading;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let workLine = line;
    const inlineHeading = findPolicyHeadingCountInLine_(workLine);
    if (inlineHeading.count) {
      if (!currentHeading) currentHeading = inlineHeading.heading;
      currentLimit = inlineHeading.count;
      if (inlineHeading.cleanedLine) {
        workLine = inlineHeading.cleanedLine;
      } else {
        continue;
      }
    }
    const policyHeading = currentHeading && /(政策|重点政策|大政策|つの政策|つの挑戦|ビジョン)/.test(currentHeading);

    if (isAcademicProfileLine_(workLine)) {
      continue;
    }

    if (hasWinnerInLine(i)) {
      otherPartyLock = false;
    }

    if (winnerKey && isOtherPartyCueLine_(workLine, winnerParty)) {
      if (hasWinnerInLine(i) || sawPolicyItem || inStarSection) {
        flush();
        break;
      }
      otherPartyLock = true;
      continue;
    }

    if (otherPartyLock) {
      continue;
    }

    if (winnerKey && isOtherCandidateBlock_(workLine, winnerKey, winnerParty, otherNames)) {
      continue;
    }

    if (isCandidateListLine_(workLine)) {
      continue;
    }

    if (isElectionNoticeLine_(workLine)) {
      continue;
    }

    if (prevWasBullet && currentItems.length > 0 && !isBulletLine_(workLine) && isLikelyContinuationLine_(workLine)) {
      const last = currentItems[currentItems.length - 1];
      if (last.indexOf(workLine) === -1) {
        currentItems[currentItems.length - 1] = (last + " " + workLine).trim();
      }
      continue;
    }

    const strippedHeading = workLine.replace(/^\s*[・●•\-]\s*/, "").trim();
    if (/政策/.test(strippedHeading) && strippedHeading.length <= 30 && !/[。．\.]/.test(strippedHeading)) {
      flush();
      currentHeading = strippedHeading;
      skipSection = /(実績|プロフィール|経歴|略歴)/.test(currentHeading);
      prevWasBullet = false;
      continue;
    }

    const treatCircledAsBullet = policyHeading && /^[①-⑳]/.test(workLine);
    const treatNumberedAsBullet = policyHeading && isNumberedPolicyLine_(workLine);
    if (!forceSingleSection && !treatCircledAsBullet && !treatNumberedAsBullet && isHeadingLine_(workLine)) {
      if (currentHeading && currentItems.length === 0 && isNumberedHeading_(currentHeading) && isLabelHeading_(line)) {
        continue;
      }
      flush();
      currentHeading = workLine.replace(/\s+/g, " ").trim();
      currentLimit = inferPolicyCountFromHeading_(currentHeading);
      const nextLine = i + 1 < lines.length ? lines[i + 1] : "";
      skipSection = /(実績|プロフィール|経歴|略歴)/.test(currentHeading)
        || (isProfileHeadingCandidate_(currentHeading) && isLikelyProfileLine_(nextLine));
      prevWasBullet = false;
      continue;
    }

    if (skipSection) continue;

    const isBullet = treatCircledAsBullet || treatNumberedAsBullet || isBulletLine_(workLine);
    if (inStarSection) {
      if (!isBullet) {
        nonBulletAfterStar += 1;
        if (nonBulletAfterStar >= 2) {
          flush();
          break;
        }
      } else {
        nonBulletAfterStar = 0;
      }
    }
    if (!isBullet && prevWasBullet && currentItems.length > 0 && !isHeadingLine_(workLine)) {
      currentItems[currentItems.length - 1] = (currentItems[currentItems.length - 1] + " " + workLine).trim();
      continue;
    }
    if (!treatCircledAsBullet && !treatNumberedAsBullet && !isLikelyPolicyLine_(workLine)) continue;
    const hasFuture = hasFutureVerb_(workLine);
    if (!isBullet && !(prevWasBullet && hasFuture)) continue;

    let merged = workLine;
    const next = i + 1 < lines.length ? lines[i + 1] : "";
    if (next && next.length <= 20 && !isLikelyPolicyLine_(next) && !isHeadingLine_(next)) {
      merged = line + " " + next;
    }
    merged = merged.replace(/^\s*[★●・•\-*\d\.\)\(①-⑳]+\s*/, "").trim();
    if (winnerKey && (sawPolicyItem || inStarSection) && isOtherPartyCueLine_(merged, winnerParty)) {
      flush();
      break;
    }
    if (/(実現|成功|達成)/.test(merged)) continue;
    if (merged.length < 8) continue;
    currentItems.push(merged);
    sawPolicyItem = true;
    if (/^★/.test(workLine)) inStarSection = true;
    prevWasBullet = isBullet;
    if (currentLimit > 0 && currentItems.length >= currentLimit) {
      flush();
      currentHeading = "";
      currentLimit = 0;
      skipSection = false;
      prevWasBullet = false;
    }
  }

  flush();

  const blocks = [];
  if (capCount && sections.length > 0) {
    const perHeading = Math.max(1, Math.floor(capCount / sections.length));
    let remaining = capCount - perHeading * sections.length;

    for (const section of sections) {
      const picked = section.items.slice(0, perHeading);
      if (remaining > 0 && section.items.length > perHeading) {
        picked.push(section.items[perHeading]);
        remaining -= 1;
      }
      if (picked.length === 0) continue;
      blocks.push("## " + section.heading);
      for (const item of picked) blocks.push("- " + item);
    }
  } else {
    for (const section of sections) {
      blocks.push("## " + section.heading);
      for (const item of section.items) blocks.push("- " + item);
    }
  }

  return blocks.slice(0, 120).join("\n");
}

function removeCandidateListLines_(text) {
  if (!text) return "";
  const lines = text.split(/\r?\n/);
  const kept = [];
  for (const line of lines) {
    if (isCandidateListLine_(line)) continue;
    if (isElectionNoticeLine_(line)) continue;
    kept.push(line);
  }
  return kept.join("\n");
}

function fillPoliciesFromCandidates_(out, candidateText, sourceText) {
  if (!out || !out.main || !Array.isArray(out.main.policies)) return { main: 0, prop: 0 };
  const existing = new Set(out.main.policies.map(item => (item.evidence || "").toString().trim()).filter(v => v !== ""));
  const candidates = extractPolicyLinesFromCandidates_(candidateText);
  let addedMain = 0;
  for (const line of candidates) {
    if (out.main.policies.length >= 8) break;
    if (existing.has(line)) continue;
    const item = { policy: line, evidence: line, type: "policy" };
    if (hasEvidence_(item, sourceText)) {
      out.main.policies.push(item);
      existing.add(line);
      addedMain += 1;
    }
  }
  return { main: addedMain, prop: 0 };
}

function extractPolicyLinesFromCandidates_(candidateText) {
  const lines = (candidateText || "").split(/\r?\n/);
  const out = [];
  for (const line of lines) {
    const trimmed = (line || "").trim();
    if (trimmed.startsWith("- ")) {
      const body = trimmed.slice(2).trim();
      if (body) out.push(body);
    }
  }
  return out;
}

function isLikelyPolicyLine_(line) {
  const s = (line || "").toString().trim();
  if (!s) return false;
  if (/プロフィール|経歴|略歴|実績|就任|当選|生まれ|卒業|年齢|歳|趣味|スローガン|しんぶん|赤旗/.test(s)) return false;
  if (/実現!|成功|達成/.test(s)) return false;

  const hasBullet = /^\s*[★●・\-*\d\.\)\(]+/.test(s);
  const hasFuture = hasFutureVerb_(s);
  return hasBullet || hasFuture;
}

function hasFutureVerb_(line) {
  const s = (line || "").toString().trim();
  return /目指|進め|推進|拡充|整備|支援|実施|充実|確立|改善|強化|促進|導入/.test(s);
}

function isBulletLine_(line) {
  const s = (line || "").toString().trim();
  return /^\s*(★|●|・|•|-|\d+[\.\)])\s*/.test(s);
}

function isHeadingLine_(line) {
  const s = (line || "").toString().trim();
  if (!s) return false;
  if (/、$/.test(s)) return false;
  if (isBulletLine_(s)) return false;
  if (/^(と|に|を|へ|で|から|より|また|さらに|そして|そのため|このため|これにより)/.test(s) && s.length <= 30) return false;
  if (/実現|成功|達成/.test(s)) return false;
  if (s.length <= 10 && !/(ます|する|目指|推進|拡充|整備|支援|実施|充実|確立|改善|強化|促進|導入|進め)/.test(s)) return false;
  if (/[。．\.！？!]/.test(s)) return false;
  if (s.length <= 3 && !/^[①-⑳]|^\d+/.test(s)) return false;
  if (/^[①-⑳]/.test(s)) return true;
  if (/^\d+\s*つの策/.test(s)) return true;
  if (/のために$/.test(s)) return true;
  if (/へ$/.test(s) && s.length <= 20) return true;
  if (/^\d+\s*$/.test(s)) return true;
  if (/^\d+\s+/.test(s) && !/[。．\.]/.test(s)) return true;
  if (!/[。．\.]/.test(s) && !/(ます|する|目指|推進|拡充|支援|実施|充実|確立|改善|強化|促進|導入|進め)/.test(s) && s.length <= 22) return true;
  return false;
}

function isLikelyContinuationLine_(line) {
  const s = (line || "").toString().trim();
  if (!s) return false;
  if (s.length <= 10) return true;
  if (s.length <= 25 && !/[。．\.！？!]/.test(s)) return true;
  if (/^(と|に|を|へ|で|から|より|また|さらに|そして|そのため|このため|これにより)/.test(s)) return true;
  if (/(に備えた|により|など)/.test(s)) return true;
  if (/^ます[。．\.]?$/.test(s)) return true;
  return false;
}

function isProfileHeadingCandidate_(heading) {
  const s = (heading || "").toString().trim();
  if (!s) return false;
  if (s.length > 12) return false;
  if (/[\(\)（）]/.test(s)) return false;
  if (/(政策|重点政策|大政策|実績|プロフィール|経歴|略歴)/.test(s)) return false;
  return true;
}

function isLikelyProfileLine_(line) {
  const s = (line || "").toString().trim();
  if (!s) return false;
  return /(薬剤師|弁護士|医師|議員|元|卒|生まれ|年|歳|資格|趣味|事務所|SNS)/.test(s);
}

function isNumberedHeading_(heading) {
  const s = (heading || "").toString().trim();
  return /^[①-⑳]/.test(s) || /^\d+/.test(s);
}

function isLabelHeading_(line) {
  const s = (line || "").toString().trim();
  if (!s) return false;
  if (/のために$/.test(s)) return false;
  if (/へ$/.test(s)) return false;
  if (/\d+つの策/.test(s)) return false;
  if (/^[①-⑳]/.test(s)) return false;
  if (s.length <= 6 && !/\s/.test(s)) return true;
  if (s.length <= 12 && /[\(（].+[\)）]/.test(s)) return true;
  return false;
}

function inferPolicyCountCap_(lines) {
  const joined = lines.join(" ");
  const m = joined.match(/(\d+)\s*つの策/);
  if (!m) return 0;
  const n = parseInt(m[1], 10);
  if (Number.isNaN(n) || n <= 0) return 0;
  return Math.min(n, 12);
}

function inferPolicyCountFromHeading_(heading) {
  const s = (heading || "").toString();
  const m = s.match(/(\d+)\s*(つ|項|本|大|個)\s*(の)?\s*(政策|重点政策|挑戦|ビジョン)/);
  if (!m) return 0;
  const n = parseInt(m[1], 10);
  if (Number.isNaN(n) || n <= 0) return 0;
  return Math.min(n, 12);
}

function findPolicyHeadingCountInLine_(line) {
  const s = (line || "").toString();
  const m = s.match(/(\d+)\s*つ\s*の\s*(政策|重点政策|挑戦|ビジョン)/);
  if (!m) return { count: 0, heading: "", cleanedLine: "" };
  const n = parseInt(m[1], 10);
  if (Number.isNaN(n) || n <= 0) return { count: 0, heading: "", cleanedLine: "" };
  const cleaned = s.replace(/\s*.*?目指す\s*\d+\s*つ\s*の\s*(政策|重点政策|挑戦|ビジョン).*$/, "").trim();
  return { count: Math.min(n, 12), heading: `${Math.min(n, 12)}つの政策`, cleanedLine: cleaned };
}

function isNumberedPolicyLine_(line) {
  const s = (line || "").toString().trim();
  return /^\d{1,2}\b/.test(s) || /^0\d\b/.test(s);
}

function isCandidateListLine_(line) {
  const s = (line || "").toString().trim();
  if (!s) return false;
  if (/(党|公認|政策|重点政策|プロフィール|経歴|略歴|実績|歳)/.test(s)) return false;
  const tokens = s.split(/\s+/).filter(t => t !== "");
  if (tokens.length < 3) return false;
  const shortTokens = tokens.filter(t => t.length <= 4).length;
  if (shortTokens < 3) return false;
  if (/[。．\.！？!]/.test(s)) return false;
  return true;
}

function isElectionNoticeLine_(line) {
  const s = (line || "").toString().trim();
  if (!s) return false;
  if (/(投票日|期日前投票|投票時間|選挙管理委員会|小選挙区は|比例代表は|投票に参加|期日前投票制度)/.test(s)) return true;
  if (/(午前\s*\d+時|午後\s*\d+時|\d{1,2}\/\d{1,2})/.test(s) && /(投票|期日前)/.test(s)) return true;
  if (/(touhyo1027\.com|投票所|ご注意ください)/.test(s)) return true;
  return false;
}

function isElectionNoticeBlock_(text) {
  const s = (text || "").toString().trim();
  if (!s) return false;
  const lines = s.split(/\r?\n/);
  for (const line of lines) {
    if (isElectionNoticeLine_(line)) return true;
  }
  if (/(投票日|期日前投票|投票時間|選挙管理委員会)/.test(s)) return true;
  return false;
}

function extractOtherCandidateNamesFromOcr_(lines, winnerNameKey) {
  const nameSet = new Set();
  const profileRe = /(.+?)(?:の)?プロフィール/;
  const policyRe = /(.+?)(?:の)?政策/;

  for (const line of lines) {
    let m = line.match(profileRe);
    if (m && m[1]) {
      const name = normalizeName_(m[1]);
      if (name && name !== winnerNameKey) nameSet.add(name);
      continue;
    }
    m = line.match(policyRe);
    if (m && m[1]) {
      const name = normalizeName_(m[1]);
      if (name && name !== winnerNameKey) nameSet.add(name);
    }
  }

  return nameSet;
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
    if (main.name_en && existingNameJa && !isPlaceholderValue_(main.name_en)) sheet.getRange(rowIndex, 5).setValue(main.name_en);

    const policies = Array.isArray(main.policies) ? main.policies : [];
    for (let k = 0; k < 8; k++) {
      const col = 6 + k * 2; // policy列
      const item = policies[k] || "";
      if (item && typeof item === "object") {
        sheet.getRange(rowIndex, col).setValue(item.policy || "");
        sheet.getRange(rowIndex, col + 1).setValue(item.evidence || "");
      } else {
        sheet.getRange(rowIndex, col).setValue(item || "");
        sheet.getRange(rowIndex, col + 1).setValue("");
      }
    }
  }

  const prop = out.prop;
  if (prop && prop !== null) {
    sheet.getRange(rowIndex, 22).setValue("はい");
    if (prop.name_en && existingPropNameJa && !isPlaceholderValue_(prop.name_en)) sheet.getRange(rowIndex, 24).setValue(prop.name_en);

    const policies = Array.isArray(prop.policies) ? prop.policies : [];
    for (let k = 0; k < 5; k++) {
      const col = 25 + k * 2;
      const item = policies[k] || "";
      if (item && typeof item === "object") {
        sheet.getRange(rowIndex, col).setValue(item.policy || "");
        sheet.getRange(rowIndex, col + 1).setValue(item.evidence || "");
      } else {
        sheet.getRange(rowIndex, col).setValue(item || "");
        sheet.getRange(rowIndex, col + 1).setValue("");
      }
    }
  }
}

function validatePoliciesWithEvidence_(out, sourceText) {
  if (!out || !sourceText) return { main: 0, prop: 0 };
  const src = sourceText.replace(/\s+/g, " ");
  let removedMain = 0;
  let removedProp = 0;

  if (out.main && Array.isArray(out.main.policies)) {
    const before = out.main.policies.length;
    out.main.policies = out.main.policies.filter(item => isPolicyItem_(item) && hasEvidence_(item, src));
    removedMain = Math.max(0, before - out.main.policies.length);
    if (out.main.policies.length === 0) out.main.confidence = "low";
  }

  if (out.prop && Array.isArray(out.prop.policies)) {
    const before = out.prop.policies.length;
    out.prop.policies = out.prop.policies.filter(item => isPolicyItem_(item) && hasEvidence_(item, src));
    removedProp = Math.max(0, before - out.prop.policies.length);
    if (out.prop.policies.length === 0) out.prop.confidence = "low";
  }
  return { main: removedMain, prop: removedProp };
}

function logPolicyExtractionSummary_(out, context) {
  const reason = computePolicyExtractionReason_(out, context);
  if (!reason) return;

  console.log(
    "Policy extraction empty: reason=" + reason
      + ", winner=" + (context.winnerNameJa || "")
      + ", party=" + (context.winnerParty || "")
      + ", ocr=" + (context.ocrSource || "")
      + ", candidateLines=" + (context.candidateLineCount || 0)
      + ", openaiMain=" + (context.beforeMainPolicies || 0)
      + ", removedByEvidence=" + (context.removedByEvidence.main || 0)
      + ", addedFromCandidates=" + (context.addedFromCandidates.main || 0)
  );
}

function computePolicyExtractionReason_(out, context) {
  const mainPolicies = out && out.main && Array.isArray(out.main.policies) ? out.main.policies.length : 0;
  const propPolicies = out && out.prop && Array.isArray(out.prop.policies) ? out.prop.policies.length : 0;
  if (mainPolicies > 0 || propPolicies > 0) return "";

  if (!context.hasOcrText) {
    return "ocr_empty";
  }
  if (!context.hasFocusedText && !context.candidateLineCount) {
    return "no_policy_candidates";
  }
  if (context.beforeMainPolicies === 0 && context.addedFromCandidates.main === 0) {
    return "openai_empty";
  }
  if (context.beforeMainPolicies > 0 && context.removedByEvidence.main >= context.beforeMainPolicies) {
    return "evidence_rejected";
  }
  return "no_verified_policy";
}

function isPolicyItem_(item) {
  if (!item || typeof item !== "object") return false;
  const t = (item.type || "").toString().trim().toLowerCase();
  return t === "policy";
}

function hasEvidence_(item, sourceText) {
  if (!item || typeof item !== "object") return false;
  const evidence = (item.evidence || "").toString().trim();
  if (!evidence) return false;
  if (evidence.includes("…") || evidence.includes("...")) return false;
  if (evidence.length < 8) return false;
  if (isHeadingLine_(evidence)) return false;
  return sourceText.indexOf(evidence) >= 0;
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

function isPlaceholderValue_(value) {
  const v = (value || "").toString().trim().toLowerCase();
  return v === "" || v === "不明" || v === "unknown";
}
