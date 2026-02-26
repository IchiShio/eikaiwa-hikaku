#!/usr/bin/env node
// 455問をLv1〜5に再分類するスクリプト
// Usage: node reclassify.js

const fs = require('fs');
const https = require('https');

const API_KEY = process.env.ANTHROPIC_API_KEY;
const BATCH_SIZE = 20;

// ─── 問題データを行単位で抽出 ───
const html = fs.readFileSync('./index.html', 'utf8');
const lines = html.split('\n');

// DATA配列内の問題行を特定
const questionLines = []; // { lineIdx, diff, wordCount, text, kp }
let inData = false;
for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  if (line.includes('const DATA = [')) { inData = true; continue; }
  if (inData && line.trim().startsWith('];')) { inData = false; break; }
  if (inData) {
    const diffMatch = line.match(/diff:\s*"([^"]+)"/);
    const textMatch = line.match(/text:\s*"([^"]+)"/);
    const kpMatch = line.match(/kp:\s*\[([^\]]*)\]/);
    if (diffMatch && textMatch) {
      // kpはそのまま文字列として取得（パースしない）
      const kpRaw = kpMatch ? kpMatch[1].replace(/"/g, '').replace(/'/g, '').split(',').map(s => s.trim()).filter(Boolean) : [];
      questionLines.push({
        lineIdx: i,
        diff: diffMatch[1],
        wordCount: textMatch[1].split(' ').length,
        text: textMatch[1],
        kp: kpRaw
      });
    }
  }
}
console.log(`問題数: ${questionLines.length}件を読み込みました`);

// ─── Claude API呼び出し ───
function callClaude(prompt) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 300,
      messages: [{ role: 'user', content: prompt }]
    });
    const req = https.request({
      hostname: 'api.anthropic.com',
      path: '/v1/messages',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY,
        'anthropic-version': '2023-06-01',
        'Content-Length': Buffer.byteLength(body)
      }
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const j = JSON.parse(data);
          if (j.error) reject(new Error(j.error.message));
          else resolve(j.content[0].text.trim());
        } catch (e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ─── バッチ分類 ───
async function classifyBatch(batch) {
  const items = batch.map((q, i) =>
    `[${i}] (${q.wordCount}語) "${q.text}" kp:${JSON.stringify(q.kp)}`
  ).join('\n');

  const prompt = `英語リスニング問題を「何回聴けば理解できるか」でLv1〜5に分類してください。

基準:
Lv1: ≤13語・基本語彙・直接的・1回で確実
Lv2: 14〜17語・日常語彙・基本イディオム≤1個・1〜2回
Lv3: 18〜21語・中級語彙・イディオム1〜2個・2回
Lv4: 22〜26語・スラング・慣用句・ニュアンス推測・2〜3回
Lv5: ≥27語 or 高度な慣用表現・含意・文脈依存・3回以上

問題:
${items}

回答形式（この形式のみ、他の文章不要）:
[0]:lv2
[1]:lv3
...`;

  const result = await callClaude(prompt);
  const levels = {};
  for (const line of result.split('\n')) {
    const m = line.match(/\[(\d+)\]\s*:\s*lv(\d)/i);
    if (m) levels[parseInt(m[1])] = `lv${m[2]}`;
  }
  return levels;
}

// ─── フォールバック分類（語数ベース）───
function fallbackLevel(wc) {
  if (wc <= 13) return 'lv1';
  if (wc <= 17) return 'lv2';
  if (wc <= 21) return 'lv3';
  if (wc <= 26) return 'lv4';
  return 'lv5';
}

// ─── メイン処理 ───
async function main() {
  console.log('再分類を開始します...\n');

  // 全問題に新しいレベルを割り当て
  const newLevels = new Array(questionLines.length);

  for (let i = 0; i < questionLines.length; i += BATCH_SIZE) {
    const batch = questionLines.slice(i, i + BATCH_SIZE);
    const end = Math.min(i + BATCH_SIZE, questionLines.length);
    process.stdout.write(`[${i}〜${end - 1}] 処理中... `);

    try {
      const levels = await classifyBatch(batch);
      let missing = 0;
      for (let j = 0; j < batch.length; j++) {
        newLevels[i + j] = levels[j] || fallbackLevel(batch[j].wordCount);
        if (!levels[j]) missing++;
      }
      console.log(`完了${missing ? ` (${missing}件フォールバック)` : ''}`);
    } catch (e) {
      console.error(`エラー: ${e.message} → フォールバック使用`);
      for (let j = 0; j < batch.length; j++) {
        newLevels[i + j] = fallbackLevel(batch[j].wordCount);
      }
    }

    if (i + BATCH_SIZE < questionLines.length) {
      await new Promise(r => setTimeout(r, 600));
    }
  }

  // ─── 結果集計 ───
  const counts = {};
  newLevels.forEach(lv => counts[lv] = (counts[lv] || 0) + 1);
  console.log('\n分類結果:');
  ['lv1','lv2','lv3','lv4','lv5'].forEach(k => console.log(`  ${k}: ${counts[k] || 0}問`));

  // ─── HTMLを行単位で更新 ───
  console.log('\nindex.htmlを更新中...');
  const newLines = [...lines];
  let changed = 0;
  for (let i = 0; i < questionLines.length; i++) {
    const { lineIdx, diff } = questionLines[i];
    const newDiff = newLevels[i];
    if (diff !== newDiff) {
      newLines[lineIdx] = newLines[lineIdx].replace(
        `diff: "${diff}"`,
        `diff: "${newDiff}"`
      );
      changed++;
    }
  }
  console.log(`${changed}件のdiff値を変更しました`);

  // バックアップ
  fs.writeFileSync('./index.html.bak', html);
  console.log('バックアップ: index.html.bak');

  fs.writeFileSync('./index.html', newLines.join('\n'));
  console.log('index.htmlを保存しました');

  // デバッグ用JSON
  const debug = questionLines.map((q, i) => ({
    idx: i,
    old: q.diff,
    new: newLevels[i],
    words: q.wordCount,
    text: q.text.substring(0, 60)
  }));
  fs.writeFileSync('./reclassify_result.json', JSON.stringify(debug, null, 2));
  console.log('詳細: reclassify_result.json\n完了!');
}

main().catch(console.error);
