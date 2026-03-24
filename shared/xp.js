/* ─────────────────────────────────────────────
   NativeReal 共通XP System  v1.0
   /shared/xp.js
   全ツール共通の永続XP・レベル・連続日数管理
   ───────────────────────────────────────────── */
(function () {
  'use strict';

  var KEY = 'nativereal_xp';

  var LEVELS = [
    { name: 'Starter',     threshold: 0,    icon: '\uD83C\uDF31' },
    { name: 'Learner',     threshold: 30,   icon: '\uD83D\uDCD6' },
    { name: 'Explorer',    threshold: 100,  icon: '\uD83E\uDDED' },
    { name: 'Challenger',  threshold: 250,  icon: '\u26A1' },
    { name: 'Achiever',    threshold: 500,  icon: '\uD83C\uDFC5' },
    { name: 'Expert',      threshold: 1000, icon: '\uD83C\uDFAF' },
    { name: 'Master',      threshold: 2000, icon: '\uD83D\uDC51' },
  ];

  var TOOLS = {
    listenup: { label: 'ListenUp', path: '/', icon: '\uD83C\uDFA7' },
    grammar:  { label: 'GrammarUp', path: '/grammar/', icon: '\uD83D\uDCDD' },
    kioku:    { label: '記憶しない英単語', path: '/kioku-shinai/', icon: '\uD83E\uDDE0' },
  };

  function today() {
    return new Date().toISOString().slice(0, 10);
  }

  function load() {
    try {
      var d = JSON.parse(localStorage.getItem(KEY));
      if (d && typeof d.total === 'number') return d;
    } catch (_) {}
    return { total: 0, tools: {}, streak: 0, lastDate: '', history: [] };
  }

  function save(d) {
    try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (_) {}
  }

  function getLevel(xp) {
    for (var i = LEVELS.length - 1; i >= 0; i--) {
      if (xp >= LEVELS[i].threshold) return { index: i, def: LEVELS[i] };
    }
    return { index: 0, def: LEVELS[0] };
  }

  function updateStreak(d) {
    var t = today();
    if (d.lastDate === t) return;

    var yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    var yStr = yesterday.toISOString().slice(0, 10);

    if (d.lastDate === yStr) {
      d.streak++;
    } else if (d.lastDate !== t) {
      d.streak = 1;
    }
    d.lastDate = t;

    if (!d.history) d.history = [];
    if (d.history[d.history.length - 1] !== t) d.history.push(t);
    if (d.history.length > 30) d.history = d.history.slice(-30);
  }

  /* ── Public API ── */

  function addXP(tool, amount) {
    if (amount <= 0) return { leveled: false, data: load() };
    var d = load();
    var oldLv = getLevel(d.total);

    d.total += amount;
    if (!d.tools[tool]) d.tools[tool] = 0;
    d.tools[tool] += amount;

    updateStreak(d);
    save(d);

    var newLv = getLevel(d.total);
    var leveled = newLv.index > oldLv.index;

    if (leveled) showLevelUpToast(newLv.def, d);
    updateXPBar(d);

    return { leveled: leveled, data: d, newLevel: newLv.def };
  }

  function getData() {
    return load();
  }

  /* ── XP Bar (injected below site-header) ── */

  function createXPBar() {
    var d = load();
    if (d.lastDate) updateStreak(d);

    var lv = getLevel(d.total);
    var nextLv = LEVELS[lv.index + 1];
    var pct = 0;
    if (nextLv) {
      pct = Math.min(100, Math.round(
        (d.total - lv.def.threshold) / (nextLv.threshold - lv.def.threshold) * 100
      ));
    } else {
      pct = 100;
    }

    var bar = document.createElement('a');
    bar.id = 'nrXpBar';
    bar.href = '/my/';
    bar.style.display = 'block';
    bar.style.textDecoration = 'none';
    bar.style.color = 'inherit';
    bar.innerHTML =
      '<div class="nr-xp-inner">' +
        '<span class="nr-xp-level">' + lv.def.icon + ' Lv.' + (lv.index + 1) + ' ' + lv.def.name + '</span>' +
        '<div class="nr-xp-track"><div class="nr-xp-fill" id="nrXpFill" style="width:' + pct + '%"></div></div>' +
        '<span class="nr-xp-text" id="nrXpText">' + d.total + ' XP</span>' +
        (d.streak > 1 ? '<span class="nr-xp-streak" id="nrXpStreak">\uD83D\uDD25' + d.streak + '\u65E5</span>' : '<span class="nr-xp-streak" id="nrXpStreak"></span>') +
      '</div>';

    return bar;
  }

  function injectXPBar() {
    var header = document.getElementById('siteHeader');
    if (!header) return;
    var bar = createXPBar();
    header.parentNode.insertBefore(bar, header.nextSibling);
  }

  function updateXPBar(d) {
    if (!d) d = load();
    var lv = getLevel(d.total);
    var nextLv = LEVELS[lv.index + 1];
    var pct = nextLv
      ? Math.min(100, Math.round((d.total - lv.def.threshold) / (nextLv.threshold - lv.def.threshold) * 100))
      : 100;

    var levelEl = document.querySelector('.nr-xp-level');
    var fillEl = document.getElementById('nrXpFill');
    var textEl = document.getElementById('nrXpText');
    var streakEl = document.getElementById('nrXpStreak');

    if (levelEl) levelEl.textContent = lv.def.icon + ' Lv.' + (lv.index + 1) + ' ' + lv.def.name;
    if (fillEl) fillEl.style.width = pct + '%';
    if (textEl) textEl.textContent = d.total + ' XP';
    if (streakEl && d.streak > 1) streakEl.textContent = '\uD83D\uDD25' + d.streak + '\u65E5';
  }

  /* ── Level-up Toast ── */

  function showLevelUpToast(levelDef, d) {
    var existing = document.getElementById('nrLevelUpToast');
    if (existing) existing.remove();

    var suggest = getSuggestion(d);

    var toast = document.createElement('div');
    toast.id = 'nrLevelUpToast';
    toast.className = 'nr-levelup-toast';
    toast.innerHTML =
      '<div class="nr-lvup-icon">' + levelDef.icon + '</div>' +
      '<div class="nr-lvup-label">LEVEL UP!</div>' +
      '<div class="nr-lvup-name">Lv.' + (getLevel(d.total).index + 1) + ' ' + levelDef.name + '</div>' +
      (suggest ? '<a class="nr-lvup-suggest" href="' + suggest.path + '">' + suggest.icon + ' ' + suggest.label + ' \u3082\u8A66\u3057\u3066\u307F\u3088\u3046\uFF01</a>' : '');

    document.body.appendChild(toast);
    requestAnimationFrame(function () {
      toast.classList.add('show');
    });
    setTimeout(function () {
      toast.classList.remove('show');
      setTimeout(function () { toast.remove(); }, 400);
    }, 3000);
  }

  function getSuggestion(d) {
    var current = detectCurrentTool();
    var keys = Object.keys(TOOLS);
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      if (k === current) continue;
      if (!d.tools[k] || d.tools[k] === 0) return TOOLS[k];
    }
    for (var j = 0; j < keys.length; j++) {
      if (keys[j] !== current) return TOOLS[keys[j]];
    }
    return null;
  }

  function detectCurrentTool() {
    var path = location.pathname;
    if (path.indexOf('/grammar') === 0) return 'grammar';
    if (path.indexOf('/kioku-shinai') === 0) return 'kioku';
    return 'listenup';
  }

  /* ── Init ── */

  function init() {
    injectCSS();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', injectXPBar);
    } else {
      injectXPBar();
    }
  }

  function injectCSS() {
    var style = document.createElement('style');
    style.textContent =
      '#nrXpBar{background:var(--surface,#f5f5f7);border-bottom:1px solid var(--border,rgba(0,0,0,.06));padding:6px 16px;z-index:90;position:relative}' +
      '.nr-xp-inner{display:flex;align-items:center;gap:8px;max-width:800px;margin:0 auto;font-size:12px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}' +
      '.nr-xp-level{font-weight:700;color:var(--text-1,#1d1d1f);white-space:nowrap;min-width:110px}' +
      '.nr-xp-track{flex:1;height:5px;background:var(--surface-2,rgba(0,0,0,.06));border-radius:3px;overflow:hidden;min-width:60px}' +
      '.nr-xp-fill{height:100%;background:linear-gradient(90deg,#34d399,#3b82f6);border-radius:3px;transition:width .5s ease}' +
      '.nr-xp-text{color:var(--text-3,#86868b);font-weight:600;white-space:nowrap}' +
      '.nr-xp-streak{color:#f59e0b;font-weight:700;white-space:nowrap}' +
      '.nr-levelup-toast{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%) scale(.8);background:linear-gradient(135deg,#f59e0b,#34d399);color:#fff;padding:24px 36px;border-radius:20px;z-index:9999;opacity:0;transition:all .35s ease;pointer-events:none;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.25)}' +
      '.nr-levelup-toast.show{opacity:1;transform:translate(-50%,-50%) scale(1)}' +
      '.nr-lvup-icon{font-size:36px;margin-bottom:4px}' +
      '.nr-lvup-label{font-size:12px;font-weight:700;letter-spacing:2px;opacity:.85}' +
      '.nr-lvup-name{font-size:22px;font-weight:800;margin-top:2px}' +
      '.nr-lvup-suggest{display:inline-block;margin-top:10px;font-size:13px;color:#fff;text-decoration:underline;pointer-events:auto}' +
      '@media(max-width:480px){.nr-xp-level{min-width:auto;font-size:11px}.nr-xp-text{font-size:11px}}';
    document.head.appendChild(style);
  }

  init();

  /* ── Expose global ── */
  window.NR = {
    addXP: addXP,
    getData: getData,
    getLevel: getLevel,
    LEVELS: LEVELS,
    TOOLS: TOOLS,
  };
})();
