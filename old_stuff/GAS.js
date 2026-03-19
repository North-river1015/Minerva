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
  let md = `---\ntitle: "${displayTitle}"\nurl: archive/2024/prefectures/${pref_raw}/${district}\n---\n\n`;
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

