/**
 * HEXDRIFT — Live Data Module
 * Fetches real-time FIFA World Cup 2026 data from ESPN public API (no key required).
 * Falls back gracefully to static PREDICTIONS data if API is unavailable.
 *
 * ESPN scoreboard: https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard
 * ESPN summary:   https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event=ID
 */

const ESPN_BASE = 'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world';
const REFRESH_LIVE   = 30_000;  // 30s when a match is live
const REFRESH_IDLE   = 120_000; // 2min when no live match

// ── TEAM CODE MAPPING (ESPN full names → our 3-letter codes) ──────────────────
const ESPN_NAME_MAP = {
  'Argentina':             'ARG', 'Brazil':              'BRA', 'France':           'FRA',
  'Spain':                 'ESP', 'England':             'ENG', 'Germany':          'GER',
  'Portugal':              'POR', 'Netherlands':         'NED', 'Belgium':          'BEL',
  'Uruguay':               'URU', 'Mexico':              'MEX', 'USA':              'USA',
  'United States':         'USA', 'Canada':              'CAN', 'Japan':            'JPN',
  'South Korea':           'KOR', 'Australia':           'AUS', 'Morocco':          'MAR',
  'Senegal':               'SEN', 'Ghana':               'GHA', 'Egypt':            'EGY',
  'Nigeria':               'NGA', 'Cameroon':            'CMR', 'South Africa':     'RSA',
  "Côte d'Ivoire":         'CIV', 'Ivory Coast':         'CIV', 'Algeria':          'ALG',
  'Switzerland':           'SUI', 'Croatia':             'CRO', 'Austria':          'AUT',
  'Sweden':                'SWE', 'Norway':              'NOR', 'Denmark':          'DEN',
  'Poland':                'POL', 'Serbia':              'SRB', 'Iran':             'IRN',
  'Saudi Arabia':          'KSA', 'Qatar':               'QAT', 'Ecuador':          'ECU',
  'Colombia':              'COL', 'Chile':               'CHI', 'Paraguay':         'PAR',
  'Bolivia':               'BOL', 'Peru':                'PER', 'Uruguay':          'URU',
  'Bosnia and Herzegovina':'BIH', 'Bosnia':              'BIH', 'DR Congo':         'COD',
  'Congo DR':              'COD', 'Cape Verde':          'CPV', 'Cabo Verde':       'CPV',
  'Jordan':                'JOR', 'New Zealand':         'NZL', 'Curaçao':          'CUR',
  'Curacao':               'CUR', 'Tunisia':             'TUN', 'Iraq':             'IRQ',
  'Uzbekistan':            'UZB', 'Czech Republic':      'CZE', 'Czechia':          'CZE',
  'Haiti':                 'HAI', 'Scotland':            'SCO', 'Ireland':          'IRL',
  'Northern Ireland':      'NIR', 'Turkey':              'TUR',
};

function espnNameToCode(name) {
  return ESPN_NAME_MAP[name] || name.substring(0, 3).toUpperCase();
}

// ── SCOREBOARD FETCH ──────────────────────────────────────────────────────────
async function fetchScoreboard() {
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const url = `${ESPN_BASE}/scoreboard?dates=${today}`;
  try {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) return null;
    const json = await res.json();
    return json.events || [];
  } catch {
    return null;
  }
}

// ── MATCH SUMMARY FETCH (lineups + events) ──────────────────────────────────
async function fetchMatchSummary(eventId) {
  try {
    const res = await fetch(`${ESPN_BASE}/summary?event=${eventId}`, { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// ── FORMAT A UTC ISO DATE STRING AS LOCAL TIME ────────────────────────────────
function formatMatchTime(isoDate) {
  if (!isoDate) return '–';
  try {
    const d = new Date(isoDate);
    // Show local time in HH:MM format
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true }).replace(' ', ' ');
  } catch {
    return '–';
  }
}

// Look up the time stored in static PREDICTIONS for a given pair of team codes
function predictionTime(hCode, aCode) {
  if (typeof PREDICTIONS === 'undefined') return null;
  const p = PREDICTIONS.find(x =>
    (x.home === hCode && x.away === aCode) ||
    (x.home === aCode && x.away === hCode)
  );
  return p ? (p.time || null) : null;
}

// ── PARSE ESPN EVENT INTO SIMPLE OBJECT ──────────────────────────────────────
function parseEvent(ev) {
  const comp   = ev.competitions?.[0];
  if (!comp) return null;
  const home   = comp.competitors?.find(c => c.homeAway === 'home');
  const away   = comp.competitors?.find(c => c.homeAway === 'away');
  const status = ev.status?.type;
  const state  = status?.state || 'pre';

  const homeCode = espnNameToCode(home?.team?.displayName || '');
  const awayCode = espnNameToCode(away?.team?.displayName || '');

  // For upcoming (pre) matches ESPN just says "Scheduled" — use our stored time or format from ISO date
  let displayTime = status?.shortDetail || '';
  if (state === 'pre' && (!displayTime || displayTime.toLowerCase() === 'scheduled')) {
    displayTime = predictionTime(homeCode, awayCode) || formatMatchTime(ev.date);
  }

  return {
    id:          ev.id,
    homeCode,
    awayCode,
    homeName:    home?.team?.displayName || '',
    awayName:    away?.team?.displayName || '',
    homeScore:   parseInt(home?.score ?? '-1'),
    awayScore:   parseInt(away?.score ?? '-1'),
    statusState: state,
    statusShort: displayTime,
    statusName:  status?.name || '',
    date:        ev.date,
    venue:       comp.venue?.fullName || '',
    note:        ev.shortName || '',
  };
}

// ── UPDATE BANNER WITH LIVE ESPN DATA ─────────────────────────────────────────
function applyEspnToBanner(events) {
  if (!events || !events.length) return;

  const live     = events.filter(e => e.statusState === 'in');
  const finished = events.filter(e => e.statusState === 'post');
  const upcoming = events.filter(e => e.statusState === 'pre');

  // Mirror finished results into static PREDICTIONS for accuracy tracking
  finished.forEach(ev => {
    const pred = (typeof PREDICTIONS !== 'undefined' ? PREDICTIONS : []).find(p =>
      (p.home === ev.homeCode && p.away === ev.awayCode) ||
      (p.home === ev.awayCode && p.away === ev.homeCode)
    );
    if (pred && pred.status !== 'completed') {
      pred.status = 'completed';
      pred.actualScore = { h: ev.homeScore, a: ev.awayScore };
      pred.correct = (
        pred.predictedScore.h === ev.homeScore &&
        pred.predictedScore.a === ev.awayScore
      );
    }
  });

  // Build banner pool: live first, then today's upcoming
  const pool = [...live, ...upcoming].slice(0, 3);
  if (!pool.length) return; // keep static banner if ESPN returns nothing today

  const inner = document.getElementById('banner-inner');
  if (!inner) return;

  // Use the same HTML structure as renderBanner() in app.js
  const _teams = typeof TEAMS !== 'undefined' ? TEAMS : {};
  inner.innerHTML = pool.map(ev => {
    const ht = _teams[ev.homeCode] || { name: ev.homeName, flag: '' };
    const at = _teams[ev.awayCode] || { name: ev.awayName, flag: '' };
    const isLive = ev.statusState === 'in';

    let scoreOrTime;
    if (isLive) {
      scoreOrTime = `<span class="live-badge">LIVE ${ev.homeScore}–${ev.awayScore} ${ev.statusShort}</span>`;
    } else if (ev.statusState === 'post') {
      scoreOrTime = `<span class="time-badge">${ev.homeScore}–${ev.awayScore} FT</span>`;
    } else {
      scoreOrTime = `<span class="time-badge">${ev.statusShort || '–'}</span>`;
    }

    return `<div class="banner-match ${isLive ? 'live' : 'upcoming'}">
      <div class="banner-teams">
        <span class="banner-team">${ht.flag} ${ht.name}</span>
        <span class="banner-score">${scoreOrTime}</span>
        <span class="banner-team">${at.flag} ${at.name}</span>
      </div>
    </div>`;
  }).join('<span class="banner-sep">·</span>');

  // Update widget button dot colour
  const dot = document.querySelector('.widget-dot');
  if (dot) dot.style.background = live.length ? 'var(--red)' : 'var(--green)';
  const btn = document.getElementById('widget-btn');
  if (btn) {
    const textNode = [...btn.childNodes].find(n => n.nodeType === 3);
    if (textNode) textNode.textContent = live.length ? ' LIVE' : ' NEXT';
  }
}

// ── UPDATE WIDGET WITH LIVE ESPN SUMMARY ─────────────────────────────────────
async function applyEspnToWidget(liveEvent) {
  if (!liveEvent) return;
  const summary = await fetchMatchSummary(liveEvent.id);
  if (!summary) return;

  const _t = typeof TEAMS !== 'undefined' ? TEAMS : {};
  const ht = _t[liveEvent.homeCode] || { name: liveEvent.homeName, flag: '', color: '#888' };
  const at = _t[liveEvent.awayCode] || { name: liveEvent.awayName, flag: '', color: '#888' };

  // Update header
  const wh = document.getElementById('w-score-h');
  const wm = document.getElementById('w-score-mid');
  const wa = document.getElementById('w-score-a');
  if (wh) wh.innerHTML = `<span class="w-flag">${ht.flag}</span><span class="w-team-name">${liveEvent.homeCode}</span>`;
  if (wm) wm.innerHTML = `<span class="w-score">${liveEvent.homeScore}</span><span class="w-dash">–</span><span class="w-score">${liveEvent.awayScore}</span>`;
  if (wa) wa.innerHTML = `<span class="w-team-name">${liveEvent.awayCode}</span><span class="w-flag">${at.flag}</span>`;

  const wMin = document.getElementById('w-min');
  if (wMin) wMin.textContent = liveEvent.statusShort;

  // Build events from ESPN plays
  const plays = summary.plays || summary.keyPlays || [];
  window._liveESPNEvents = plays.map(play => ({
    min: play.clock?.displayValue || play.period?.displayValue || '?',
    type: classifyPlay(play.type?.text || ''),
    teamCode: play.team?.abbreviation || '',
    player:   play.participants?.[0]?.athlete?.displayName || play.text || '',
    desc:     play.text || ''
  }));

  // Lineups from ESPN rosters
  const rosters = summary.rosters || [];
  window._liveESPNLineups = rosters;

  // Re-render if events tab is active
  if (window.widgetTab === 'events' || window.widgetTab === 'lineups') {
    renderWidgetContent();
  }
}

function classifyPlay(typeText) {
  const t = (typeText || '').toLowerCase();
  if (t.includes('goal'))        return 'goal';
  if (t.includes('yellow'))      return 'yellow';
  if (t.includes('red'))         return 'red';
  if (t.includes('sub'))         return 'sub';
  if (t.includes('corner'))      return 'corner';
  if (t.includes('penalty'))     return 'penalty';
  return 'event';
}

// ── MAIN REFRESH LOOP ─────────────────────────────────────────────────────────
let _refreshTimer = null;

async function liveRefresh() {
  const events = await fetchScoreboard();
  let hasLive = false;

  if (events && events.length) {
    const parsed = events.map(parseEvent).filter(Boolean);
    applyEspnToBanner(parsed);

    const liveMatch = parsed.find(e => e.statusState === 'in');
    if (liveMatch) {
      hasLive = true;
      await applyEspnToWidget(liveMatch);
    }
  }

  // Schedule next refresh
  clearTimeout(_refreshTimer);
  _refreshTimer = setTimeout(liveRefresh, hasLive ? REFRESH_LIVE : REFRESH_IDLE);
}

// ── BOOT ─────────────────────────────────────────────────────────────────────
// Wait until DOM + app.js static render is done, then overlay live data
document.addEventListener('DOMContentLoaded', () => {
  // Small delay so app.js renderBanner() runs first with static data
  setTimeout(liveRefresh, 800);
});
