/* ==========================================================
   app.js — Spot On! frontend logic
   ========================================================== */

const API = 'http://127.0.0.1:8000';

// ---- State ----
let currentLeagueId = null;
let allTeams = [];

// ---- DOM refs ----
const selLeague   = document.getElementById('sel-league');
const selHome     = document.getElementById('sel-home');
const selAway     = document.getElementById('sel-away');
const btnAnalyze  = document.getElementById('btn-analyze');
const btnNew      = document.getElementById('btn-new');
const viewSelect  = document.getElementById('view-select');
const viewLoading = document.getElementById('view-loading');
const viewResult  = document.getElementById('view-result');
const errorBanner = document.getElementById('error-banner');
const errorMsg    = document.getElementById('error-msg');

// ---- Init ----
(async function init() {
  await loadLeagues();
})();

// ==========================================================
// Load leagues
// ==========================================================
async function loadLeagues() {
  try {
    const res = await fetch(`${API}/api/leagues`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const leagues = await res.json();

    selLeague.innerHTML = '<option value="">— Escolha uma competição —</option>';

    // Split into clubs and national
    const clubs    = leagues.filter(l => l.type !== 'national');
    const national = leagues.filter(l => l.type === 'national');

    function buildOptgroup(label, items) {
      const grp = document.createElement('optgroup');
      grp.label = label;
      items.forEach(l => {
        const opt = document.createElement('option');
        opt.value = l.id;
        opt.textContent = `${l.name}  ·  ${l.country}`;
        opt.dataset.type = l.type || 'club';
        grp.appendChild(opt);
      });
      return grp;
    }

    if (clubs.length)    selLeague.appendChild(buildOptgroup('🏟️ Ligas de Clubes', clubs));
    if (national.length) selLeague.appendChild(buildOptgroup('🌍 Seleções Nacionais', national));

  } catch (e) {
    showError('Não foi possível conectar ao servidor. Verifique se o backend está rodando.');
  }
}

// ==========================================================
// League change → load teams
// ==========================================================
selLeague.addEventListener('change', async () => {
  const leagueId = selLeague.value;
  currentLeagueId = leagueId;
  hideError();

  selHome.innerHTML = '<option value="">— Carregando… —</option>';
  selAway.innerHTML = '<option value="">— Carregando… —</option>';
  selHome.disabled = true;
  selAway.disabled = true;
  btnAnalyze.disabled = true;

  if (!leagueId) {
    selHome.innerHTML = '<option value="">— Escolha um time —</option>';
    selAway.innerHTML = '<option value="">— Escolha um time —</option>';
    return;
  }

  // Adapt labels for national vs club competitions
  const national = isNational(leagueId);
  const labelHome = document.getElementById('label-home');
  const labelAway = document.getElementById('label-away');
  if (labelHome) labelHome.textContent = national ? '🌍 Time 1 (Mando)' : '🏠 Mandante';
  if (labelAway) labelAway.textContent = national ? '🌍 Time 2 (Visitante)' : '✈️ Visitante';

  try {
    const res = await fetch(`${API}/api/teams?league=${leagueId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allTeams = (await res.json()).sort((a, b) => a.name.localeCompare(b.name));
    populateTeamSelects();
    selHome.disabled = false;
    selAway.disabled = false;
  } catch (e) {
    showError('Erro ao carregar times. Tente novamente.');
    selHome.innerHTML = '<option value="">— Erro —</option>';
    selAway.innerHTML = '<option value="">— Erro —</option>';
  }
});

// ==========================================================
// Populate team selects (with mutual exclusion)
// ==========================================================
function populateTeamSelects() {
  const homeVal = selHome.value;
  const awayVal = selAway.value;

  selHome.innerHTML = '<option value="">— Escolha o mandante —</option>';
  selAway.innerHTML = '<option value="">— Escolha o visitante —</option>';

  allTeams.forEach(t => {
    if (String(t.id) !== awayVal) {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.name;
      if (String(t.id) === homeVal) opt.selected = true;
      selHome.appendChild(opt);
    }
  });

  allTeams.forEach(t => {
    if (String(t.id) !== homeVal) {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.name;
      if (String(t.id) === awayVal) opt.selected = true;
      selAway.appendChild(opt);
    }
  });

  updateAnalyzeBtn();
}

selHome.addEventListener('change', () => { populateTeamSelects(); updateAnalyzeBtn(); });
selAway.addEventListener('change', () => { populateTeamSelects(); updateAnalyzeBtn(); });

function updateAnalyzeBtn() {
  btnAnalyze.disabled = !(selHome.value && selAway.value);
}

// ==========================================================
// Analyze
// ==========================================================
btnAnalyze.addEventListener('click', async () => {
  hideError();
  const homeId = parseInt(selHome.value, 10);
  const awayId = parseInt(selAway.value, 10);

  if (!homeId || !awayId) { showError('Selecione os dois times antes de analisar.'); return; }
  if (homeId === awayId)  { showError('Os dois times devem ser diferentes.'); return; }

  showView('loading');

  try {
    const res = await fetch(`${API}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        home_team_id: homeId,
        away_team_id: awayId,
        league_id:    currentLeagueId,
      }),
    });

    if (res.status === 429) {
      showView('select');
      showError('Muitas requisições. Aguarde um momento e tente novamente.');
      return;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    renderResult(data);
    showView('result');

  } catch (e) {
    showView('select');
    showError(e.message || 'Erro inesperado. Verifique o backend.');
  }
});

// ==========================================================
// New analysis
// ==========================================================
btnNew.addEventListener('click', () => {
  showView('select');
  hideError();
});

// ==========================================================
// Render result card
// ==========================================================
function isNational(leagueId) {
  return ['WC','EC','CA','CAN','WCQ'].includes(leagueId);
}

function renderResult(d) {
  // Teams
  document.getElementById('res-home').textContent = d.home_team;
  document.getElementById('res-away').textContent = d.away_team;
  document.getElementById('res-league').textContent =
    selLeague.options[selLeague.selectedIndex]?.text || currentLeagueId;

  // For national competitions: relabel home/away to avoid misleading "home advantage"
  const national = isNational(currentLeagueId);
  document.getElementById('res-home-label').textContent = national ? 'Time 1'  : 'Vitória';
  document.getElementById('res-away-label').textContent = national ? 'Time 2'  : 'Derrota';
  document.getElementById('res-draw-label').textContent = 'Empate';
  const leagueIcon = document.getElementById('league-icon');
  if (leagueIcon) leagueIcon.textContent = national ? '🌍' : '⚽';

  // Probabilities
  const hw = (d.home_win * 100).toFixed(1);
  const dw = (d.draw     * 100).toFixed(1);
  const aw = (d.away_win * 100).toFixed(1);

  document.getElementById('res-home-pct').textContent  = `${hw}%`;
  document.getElementById('res-draw-pct').textContent  = `${dw}%`;
  document.getElementById('res-away-pct').textContent  = `${aw}%`;
  document.getElementById('res-home-team').textContent = d.home_team;
  document.getElementById('res-away-team').textContent = d.away_team;

  // Probability bar — trigger after paint
  requestAnimationFrame(() => {
    document.getElementById('bar-home').style.width = `${hw}%`;
    document.getElementById('bar-draw').style.width = `${dw}%`;
    document.getElementById('bar-away').style.width = `${aw}%`;
  });

  // Expected goals
  document.getElementById('res-lambda-home').textContent = `${d.home_team} ${d.lambda_home}`;
  document.getElementById('res-lambda-away').textContent = `${d.away_team} ${d.lambda_away}`;

  // Top scorelines
  const grid = document.getElementById('scores-grid');
  grid.innerHTML = '';
  d.top_scores.forEach((s, idx) => {
    const tile = document.createElement('div');
    tile.className = 'score-tile' + (idx === 0 ? ' top-pick' : '');

    const val = document.createElement('div');
    val.className = 'score-value';
    val.textContent = s.score;

    const prob = document.createElement('div');
    prob.className = 'score-prob';
    prob.textContent = `${(s.probability * 100).toFixed(1)}%`;

    tile.appendChild(val);
    tile.appendChild(prob);
    grid.appendChild(tile);
  });

  // Footer
  const confLabels = { high: '🟢 Alta', medium: '🟡 Média', low: '🔴 Baixa' };
  const confClasses = { high: 'confidence-high', medium: 'confidence-medium', low: 'confidence-low' };
  const badge = document.getElementById('confidence-badge');
  badge.textContent = confLabels[d.confidence] || d.confidence;
  badge.className = `confidence-badge ${confClasses[d.confidence] || ''}`;

  document.getElementById('res-data-note').textContent = d.data_based_on;
}

// ==========================================================
// View management
// ==========================================================
function showView(name) {
  viewSelect.classList.add('hidden');
  viewLoading.classList.add('hidden');
  viewResult.classList.add('hidden');

  if (name === 'select')  { viewSelect.classList.remove('hidden');  viewSelect.classList.add('fade-in'); }
  if (name === 'loading') { viewLoading.classList.remove('hidden'); viewLoading.classList.add('fade-in'); }
  if (name === 'result')  { viewResult.classList.remove('hidden');  viewResult.classList.add('fade-in'); }
}

// ==========================================================
// Error helpers
// ==========================================================
function showError(msg) {
  errorMsg.textContent = msg;
  errorBanner.classList.remove('hidden');
}

function hideError() {
  errorBanner.classList.add('hidden');
}
