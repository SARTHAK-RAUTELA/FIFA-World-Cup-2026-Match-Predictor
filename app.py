"""
FIFA 2026 Match Prediction - Web Dashboard
Run: streamlit run app.py  |  FIFA_Web.bat
"""
from datetime import date, datetime
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="FIFA 2026 Predictor",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal global styles — no custom class names, only element overrides
st.markdown("""
<style>
.block-container { padding-top: 0.8rem; }
[data-testid="stMetricValue"] { font-size: 1.2rem; }
[data-testid="stMetricLabel"] { font-size: 0.74rem; color: #7fa8d1; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# Cached resources
# ════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="Loading prediction engine...")
def load_engine():
    from prediction.engine import PredictionEngine
    return PredictionEngine()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_fixtures(_engine, date_str: str) -> List[Dict]:
    return _engine.aggregator.get_today_matches(date.fromisoformat(date_str))


@st.cache_data(ttl=300, show_spinner=False)
def fetch_prediction(
    _engine, home: str, away: str,
    match_id: str, sofascore_id: Optional[int],
    city: str, match_date: str,
) -> Dict:
    return _engine.predict_match(
        home_team=home, away_team=away,
        match_id=match_id or None, sofascore_id=sofascore_id,
        venue_city=city or "Dallas", match_date=match_date,
    )


# ════════════════════════════════════════════════════════════════════════
# Low-level HTML builders — INLINE STYLES ONLY (no class names)
# ════════════════════════════════════════════════════════════════════════

def _mhdr(title: str):
    """Dark section header with cyan left border."""
    st.markdown(
        f'<div style="background:#131d30;border-left:3px solid #00e5ff;'
        f'padding:8px 14px;border-radius:4px;margin:14px 0 8px;'
        f'font-size:.87rem;font-weight:600;color:#cdd9e5">{title}</div>',
        unsafe_allow_html=True,
    )


def _bet_card(col, label: str, odds: float, prob: float,
               is_value: bool = False, edge: float = None):
    """Single odds button rendered inside a Streamlit column."""
    border  = "2px solid #00e676" if is_value else "1px solid #2d4a6e"
    glow    = "box-shadow:0 0 10px rgba(0,230,118,.25);" if is_value else ""
    bg      = "#0d2318" if is_value else "#1a2637"
    edge_h  = (f'<div style="color:#00e676;font-size:.62rem;font-weight:700;'
               f'margin-top:3px">+{edge:.1f}% edge</div>') if (is_value and edge) else ""
    col.markdown(
        f'<div style="background:{bg};border:{border};border-radius:8px;'
        f'padding:12px 6px;text-align:center;{glow}">'
        f'<div style="color:#7fa8d1;font-size:.74rem;margin-bottom:5px;'
        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{label}</div>'
        f'<div style="color:#00e5ff;font-size:1.2rem;font-weight:700">{odds:.2f}</div>'
        f'<div style="color:#8899aa;font-size:.69rem;margin-top:3px">{prob*100:.1f}%</div>'
        f'{edge_h}</div>',
        unsafe_allow_html=True,
    )


def _odds_row(options: List[Dict], vkeys: set = None, vedges: Dict = None):
    """
    Render a row of odds buttons.
    options: [{label, odds, prob}]  vkeys: set of value-bet labels
    """
    cols = st.columns(len(options))
    for col, opt in zip(cols, options):
        lbl     = opt["label"]
        is_val  = bool(vkeys and lbl in vkeys)
        edge    = vedges.get(lbl) if vedges else None
        _bet_card(col, lbl, opt["odds"], opt["prob"], is_val, edge)


# ════════════════════════════════════════════════════════════════════════
# Market section renderers
# ════════════════════════════════════════════════════════════════════════

def _tab_main(markets: Dict, home: str, away: str, vbets: List[Dict]):
    h, a = home[:14], away[:14]

    def _vk(mkt):  return {v["selection"] for v in vbets if v["market"] == mkt}
    def _ve(mkt):  return {v["selection"]: v["edge_pct"] for v in vbets if v["market"] == mkt}

    # Match Winner 1X2
    x = markets["1x2"]
    _mhdr("Match Winner — Full Time")
    _odds_row([
        {"label": h,      "odds": x["home"]["odds"], "prob": x["home"]["prob"]},
        {"label": "Draw", "odds": x["draw"]["odds"], "prob": x["draw"]["prob"]},
        {"label": a,      "odds": x["away"]["odds"], "prob": x["away"]["prob"]},
    ], _vk("1X2"), _ve("1X2"))

    c1, c2 = st.columns(2)
    with c1:
        _mhdr("Both Teams to Score — Full Time")
        b = markets["btts"]
        _odds_row([
            {"label": "Yes", "odds": b["yes"]["odds"], "prob": b["yes"]["prob"]},
            {"label": "No",  "odds": b["no"]["odds"],  "prob": b["no"]["prob"]},
        ], _vk("BTTS"), _ve("BTTS"))

        _mhdr("Draw No Bet")
        d = markets["draw_no_bet"]
        _odds_row([
            {"label": h, "odds": d["home"]["odds"], "prob": d["home"]["prob"]},
            {"label": a, "odds": d["away"]["odds"], "prob": d["away"]["prob"]},
        ], _vk("DNB"), _ve("DNB"))

    with c2:
        _mhdr("Double Chance")
        dc = markets["double_chance"]
        _odds_row([
            {"label": f"{h} or Draw", "odds": dc["home_draw"]["odds"], "prob": dc["home_draw"]["prob"]},
            {"label": f"{a} or Draw", "odds": dc["away_draw"]["odds"], "prob": dc["away_draw"]["prob"]},
            {"label": f"{h} or {a}",  "odds": dc["home_away"]["odds"], "prob": dc["home_away"]["prob"]},
        ], _vk("DC"), _ve("DC"))

        _mhdr("Clean Sheet")
        cs = markets["clean_sheet"]
        cs_cols = st.columns(4)
        _bet_card(cs_cols[0], f"{h} yes", cs["away"]["odds"], cs["away"]["prob"])
        p_hno = 1 - cs["away"]["prob"]
        _bet_card(cs_cols[1], f"{h} no",
                  round(1/p_hno, 2) if p_hno > 0.01 else 99, p_hno)
        _bet_card(cs_cols[2], f"{a} yes", cs["home"]["odds"], cs["home"]["prob"])
        p_ano = 1 - cs["home"]["prob"]
        _bet_card(cs_cols[3], f"{a} no",
                  round(1/p_ano, 2) if p_ano > 0.01 else 99, p_ano)

    # 1st Goal
    _mhdr("1st Goal of Match")
    fg = markets["first_goal"]
    _odds_row([
        {"label": h,         "odds": fg["home"]["odds"], "prob": fg["home"]["prob"]},
        {"label": "No Goal", "odds": fg["none"]["odds"], "prob": fg["none"]["prob"]},
        {"label": a,         "odds": fg["away"]["odds"], "prob": fg["away"]["prob"]},
    ])

    # Correct Score
    _mhdr("Correct Score (Top 16)")
    cs_list = markets["correct_score"][:16]
    cs_cols = st.columns(4)
    for i, s in enumerate(cs_list):
        p = s["probability"]
        o = round(1/p, 2) if p > 0 else 999
        score_lbl = f"{s['home']}-{s['away']}"
        cs_cols[i % 4].markdown(
            f'<div style="background:#1a2637;border:1px solid #2d4a6e;'
            f'border-radius:6px;padding:8px 4px;text-align:center;margin-bottom:6px">'
            f'<div style="color:#cdd9e5;font-size:.92rem;font-weight:700">{score_lbl}</div>'
            f'<div style="color:#00e5ff;font-size:1rem;font-weight:700">{o:.2f}</div>'
            f'<div style="color:#8899aa;font-size:.66rem">{p*100:.1f}%</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _tab_goals(markets: Dict, home: str, away: str):
    # Total Goals Exact
    _mhdr("Total Goals — Exact Count")
    tge = markets["total_goals_exact"]
    _odds_row([{"label": f"{r['goals']} Goals", "odds": r["odds"], "prob": r["prob"]} for r in tge])

    c1, c2 = st.columns(2)
    with c1:
        _mhdr("Both Teams to Score — 1st Half")
        b1 = markets["btts_ht"]
        _odds_row([
            {"label": "Yes", "odds": b1["yes"]["odds"], "prob": b1["yes"]["prob"]},
            {"label": "No",  "odds": b1["no"]["odds"],  "prob": b1["no"]["prob"]},
        ])
    with c2:
        _mhdr("Both Teams to Score — 2nd Half")
        b2 = markets["btts_2h"]
        _odds_row([
            {"label": "Yes", "odds": b2["yes"]["odds"], "prob": b2["yes"]["prob"]},
            {"label": "No",  "odds": b2["no"]["odds"],  "prob": b2["no"]["prob"]},
        ])

    # Asian Total table
    _mhdr("Asian Total (Over / Under)")
    rows = []
    for line, d in markets["asian_total"].items():
        rows.append({
            "Line":       float(line),
            "Over %":     f"{d['over']['prob']*100:.1f}%",
            "Over Odds":  f"{d['over']['odds']:.2f}",
            "Under %":    f"{d['under']['prob']*100:.1f}%",
            "Under Odds": f"{d['under']['odds']:.2f}",
        })
    st.dataframe(pd.DataFrame(rows).set_index("Line"), use_container_width=True)


def _tab_asian(markets: Dict, home: str, away: str):
    h, a = home[:14], away[:14]
    _mhdr(f"Asian Handicap ({h} perspective)")
    rows = []
    for h_val, d in markets["asian_handicap"].items():
        rows.append({
            "Handicap":  f"{h_val:+.2f}",
            f"{h} %":    f"{d['home']['prob']*100:.1f}%",
            f"{h} Odds": f"{d['home']['odds']:.2f}",
            "Push %":    f"{d['push']*100:.1f}%",
            f"{a} %":    f"{d['away']['prob']*100:.1f}%",
            f"{a} Odds": f"{d['away']['odds']:.2f}",
        })
    st.dataframe(pd.DataFrame(rows).set_index("Handicap"), use_container_width=True)


def _tab_half(markets: Dict, home: str, away: str):
    h, a = home[:14], away[:14]

    # HT 1X2
    _mhdr("Half-Time Result (1X2)")
    ht = markets["halftime"]
    _odds_row([
        {"label": h,      "odds": ht["home"]["odds"], "prob": ht["home"]["prob"]},
        {"label": "Draw", "odds": ht["draw"]["odds"], "prob": ht["draw"]["prob"]},
        {"label": a,      "odds": ht["away"]["odds"], "prob": ht["away"]["prob"]},
    ])

    # HT/FT 3×3 grid
    htft_mkt = markets.get("htft_combo", {})
    if htft_mkt:
        _mhdr("Half-Time / Full-Time  (HT result / FT result)")
        st.caption("1 = Home win · X = Draw · 2 = Away win")
        order = ["1", "X", "2"]
        names = {"1": h, "X": "Draw", "2": a}
        for ht_r in order:
            ft_cols = st.columns(3)
            for i, ft_r in enumerate(order):
                key  = f"{ht_r}/{ft_r}"
                d    = htft_mkt.get(key, {"prob": 0, "odds": 999})
                prob = d["prob"]
                odds = d["odds"]
                alpha = min(0.15 + prob * 3.0, 0.9)
                ft_cols[i].markdown(
                    f'<div style="background:rgba(26,38,55,{alpha:.2f});'
                    f'border:1px solid #2d4a6e;border-radius:6px;'
                    f'padding:8px 5px;text-align:center;margin-bottom:4px">'
                    f'<div style="color:#7fa8d1;font-size:.69rem;margin-bottom:4px">'
                    f'{names[ht_r]} / {names[ft_r]}</div>'
                    f'<div style="color:#00e5ff;font-size:1.05rem;font-weight:700">{odds:.2f}</div>'
                    f'<div style="color:#8899aa;font-size:.67rem;margin-top:2px">{prob*100:.1f}%</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


def _tab_goalscorers(data: Dict, home: str, away: str):
    home_sc  = data.get("home_scorers", [])
    away_sc  = data.get("away_scorers", [])
    home_1st = data.get("home_1st_scorers", [])
    away_1st = data.get("away_1st_scorers", [])

    if not (home_sc or away_sc):
        st.info(
            "Goalscorer predictions need lineup data. "
            "Lineups confirmed ~1 hour before kickoff."
        )
        return

    confirmed  = data.get("lineup_confirmed", False)
    tsc        = data.get("top_scorers_count", 0)
    notes = []
    if confirmed: notes.append("Confirmed lineup")
    if tsc > 0:   notes.append(f"{tsc} WC scorers in model")
    if notes:
        st.caption("Model: " + " · ".join(notes) + " · Poisson per player")

    def _scorer_section(scorers, title, prob_key, odds_key):
        _mhdr(title)
        top = [s for s in scorers if s.get(prob_key, 0) > 0.005][:12]
        if not top:
            st.caption("No data.")
            return
        n = min(4, len(top))
        cols = st.columns(n)
        for i, s in enumerate(top):
            name  = s.get("name", "—")
            pos   = s.get("position", "—")
            prob  = s.get(prob_key, 0)
            odds  = s.get(odds_key, 99)
            goals = s.get("goals_in_comp", 0)
            is_key = s.get("is_key_scorer", False)

            border = "2px solid #f9a825" if is_key else "1px solid #2d4a6e"
            glow   = "box-shadow:0 0 8px rgba(249,168,37,.25);" if is_key else ""
            gbadge = (f'<span style="background:#f9a825;color:#000;padding:1px 4px;'
                      f'border-radius:3px;font-size:.6rem;font-weight:700;margin-right:3px">{goals}g</span>') if goals else ""
            star   = " &#9733;" if is_key else ""

            cols[i % n].markdown(
                f'<div style="background:#1a2637;border:{border};border-radius:8px;'
                f'padding:10px 6px;text-align:center;margin-bottom:6px;{glow}">'
                f'<div style="color:#cdd9e5;font-size:.78rem;font-weight:600;margin-bottom:2px">'
                f'{gbadge}{name}{star}</div>'
                f'<div style="color:#6b8099;font-size:.67rem;margin-bottom:5px">{pos}</div>'
                f'<div style="color:#00e5ff;font-size:1.1rem;font-weight:700">{odds:.2f}</div>'
                f'<div style="color:#8899aa;font-size:.67rem;margin-top:2px">{prob*100:.1f}%</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    c1, c2 = st.columns(2)
    with c1:
        _scorer_section(home_sc,  f"Anytime Goalscorer — {home}", "prob",       "odds")
        _scorer_section(home_1st, f"1st Goalscorer — {home}",      "first_prob", "first_odds")
    with c2:
        _scorer_section(away_sc,  f"Anytime Goalscorer — {away}", "prob",       "odds")
        _scorer_section(away_1st, f"1st Goalscorer — {away}",      "first_prob", "first_odds")


# ════════════════════════════════════════════════════════════════════════
# Bet Recommendation — the "where should I bet" answer
# ════════════════════════════════════════════════════════════════════════

def _render_bet_recommendation(markets: Dict, vbets: List[Dict],
                                home: str, away: str, odds_src: Optional[str]):
    """
    Clear, actionable betting recommendation:
    - If value bets exist → highlight the best edge
    - If no edge → advise against betting or show fair prices
    """
    if vbets:
        best = vbets[0]  # already sorted by edge descending
        p = best["model_prob"]
        risk_label = "Lower risk" if p > 0.55 else ("Medium risk" if p > 0.40 else "Higher risk")
        risk_col   = "#00e676" if p > 0.55 else ("#f9a825" if p > 0.40 else "#ef5350")

        st.markdown(
            f'<div style="background:#0a2718;border:2px solid #00e676;'
            f'border-radius:10px;padding:16px 20px;margin:12px 0 4px">'
            f'<div style="color:#00e676;font-weight:800;font-size:.95rem;margin-bottom:8px">'
            f'RECOMMENDED BET — VALUE FOUND</div>'
            f'<div style="font-size:1.05rem;color:#ffffff;font-weight:700;margin-bottom:8px">'
            f'{best["market"]} &nbsp;&#8594;&nbsp; {best["selection"]}</div>'
            f'<div style="display:flex;gap:20px;flex-wrap:wrap;font-size:.82rem;margin-bottom:6px">'
            f'<span style="color:#cdd9e5">Our fair odds: '
            f'<b style="color:#00e5ff">{best["model_odds"]:.2f}</b></span>'
            f'<span style="color:#cdd9e5">Bookmaker: '
            f'<b style="color:#f9a825">{best["bookie_odds"]:.2f}</b></span>'
            f'<span style="color:#00e676;font-weight:700">+{best["edge_pct"]:.1f}% edge</span>'
            f'<span style="color:#8899aa">Prob: {best["model_prob"]*100:.1f}%</span>'
            f'<span style="color:{risk_col}">{risk_label}</span>'
            f'</div>'
            f'<div style="color:#5c8a6a;font-size:.74rem">'
            f'Expected value: {best["expected_value"]:+.3f} per unit &nbsp;·&nbsp; '
            f'Confidence in prediction: {best["model_prob"]*100:.1f}%'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if len(vbets) > 1:
            other = vbets[1:]
            lines = "  ·  ".join(
                f'{v["market"]} {v["selection"]} ({v["bookie_odds"]:.2f}, +{v["edge_pct"]:.1f}%)'
                for v in other
            )
            st.caption(f"Also value: {lines}")

    else:
        # No value bets — show most likely outcome and fair price guidance
        x = markets["1x2"]
        probs = [
            (x["home"]["prob"], x["home"]["odds"], f"{home} Win"),
            (x["draw"]["prob"], x["draw"]["odds"], "Draw"),
            (x["away"]["prob"], x["away"]["odds"], f"{away} Win"),
        ]
        best_prob, best_odds, best_outcome = max(probs, key=lambda t: t[0])

        if odds_src:
            advice = ("No edge found at current bookmaker prices. "
                      "Skip or wait for better odds.")
        else:
            advice = (f"No bookmaker odds loaded yet. Our fair odds are {best_odds:.2f} for "
                      f"{best_outcome}. If you find higher odds at your bookmaker, that is value.")

        st.markdown(
            f'<div style="background:#1a2637;border:1px solid #2d4a6e;'
            f'border-radius:10px;padding:14px 18px;margin:12px 0 4px">'
            f'<div style="color:#f9a825;font-weight:700;font-size:.88rem;margin-bottom:6px">'
            f'NO EDGE DETECTED</div>'
            f'<div style="color:#cdd9e5;font-size:.85rem;margin-bottom:6px">'
            f'Most likely: <b>{best_outcome}</b> &nbsp;|&nbsp; '
            f'Model probability: <b style="color:#00e5ff">{best_prob*100:.1f}%</b> '
            f'&nbsp;|&nbsp; Fair odds: <b>{best_odds:.2f}</b></div>'
            f'<div style="color:#6b8099;font-size:.78rem">{advice}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════════════
# Match header
# ════════════════════════════════════════════════════════════════════════

def _render_match_header(pred: Dict):
    home    = pred["home_team"]
    away    = pred["away_team"]
    conf    = pred["confidence"]
    markets = pred["markets"]
    diag    = pred.get("diagnostics", {})
    data    = pred.get("data", {})
    oddsrc  = pred.get("bookmaker_odds_source")

    conf_pct  = conf["total"]
    predicted = conf.get("predicted_outcome", "?")
    pred_prob = conf.get("predicted_outcome_prob", 0)

    if conf_pct >= 93:
        bar_col = "#00e676"
        tag     = "ABOVE 93% THRESHOLD"
    elif conf_pct >= 65:
        bar_col = "#ff9800"
        tag     = "Medium confidence"
    else:
        bar_col = "#ef5350"
        tag     = "Below threshold"

    odds_badge = ""
    if oddsrc == "sofascore":
        odds_badge = ('<span style="background:#004d40;color:#00e676;padding:2px 7px;'
                     'border-radius:4px;font-size:.7rem;margin-left:10px">LIVE ODDS</span>')

    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0d1b2a,#142138);'
        f'padding:18px 24px;border-radius:12px;margin-bottom:14px;'
        f'border:1px solid #1e3351">'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:flex-start;flex-wrap:wrap;gap:12px">'
        f'<div>'
        f'<div style="font-size:1.45rem;font-weight:800;color:#fff;letter-spacing:.5px">'
        f'{home} <span style="color:#2d4a6e">vs</span> {away}</div>'
        f'<div style="color:#6b8099;font-size:.76rem;margin-top:3px">'
        f'FIFA World Cup 2026{odds_badge}</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div style="font-size:1.65rem;font-weight:800;color:#00e5ff">{conf_pct:.1f}%</div>'
        f'<div style="font-size:.71rem;color:#cdd9e5">{tag}</div>'
        f'<div style="font-size:.73rem;color:#8899aa;margin-top:2px">'
        f'Predicted: <b style="color:#cdd9e5">{predicted}</b> ({pred_prob:.1f}%)</div>'
        f'</div></div>'
        f'<div style="margin-top:10px;background:#0e1826;border-radius:4px;'
        f'height:5px;overflow:hidden">'
        f'<div style="width:{min(conf_pct,100):.1f}%;height:100%;'
        f'background:{bar_col};border-radius:4px"></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # Metrics row
    lh = markets["lam_home"]
    la = markets["lam_away"]
    mc = st.columns(6)
    mc[0].metric(f"{home[:9]} xG",   f"{lh:.2f}")
    mc[1].metric(f"{away[:9]} xG",   f"{la:.2f}")
    mc[2].metric(f"{home[:8]} ELO",  f"{diag.get('elo_home', 0):.0f}")
    mc[3].metric(f"{away[:8]} ELO",  f"{diag.get('elo_away', 0):.0f}")
    mc[4].metric(f"{home[:8]} Form", f"{diag.get('home_form_score', 0.5):.2f}")
    mc[5].metric(f"{away[:8]} Form", f"{diag.get('away_form_score', 0.5):.2f}")

    # Weather
    wx = data.get("weather")
    if wx:
        icon = "🌧" if wx.get("impact_factor", 1) < 0.95 else "☀"
        st.caption(
            f"{icon} {wx.get('description','')} · {wx.get('temperature_c','?')}°C · "
            f"Wind {wx.get('wind_speed_kmh','?')} km/h · Impact {wx.get('impact_factor',1):.2f}x"
        )

    # Missing players
    for mp, label in [
        (data.get("missing_home_players", []), home),
        (data.get("missing_away_players", []), away),
    ]:
        if mp:
            st.warning(f"{label} missing: {', '.join(mp)}")

    # Lineups expander
    h_lu = data.get("home_lineup", [])
    a_lu = data.get("away_lineup", [])
    if h_lu or a_lu:
        confirmed = data.get("lineup_confirmed", False)
        hf = data.get("home_formation", "")
        af = data.get("away_formation", "")
        lu_lbl = "Confirmed" if confirmed else "Expected (unconfirmed)"
        form_s = f" · {hf} vs {af}" if (hf or af) else ""
        with st.expander(f"Starting Lineups — {lu_lbl}{form_s}", expanded=False):
            lc1, lc2 = st.columns(2)
            def _pn(p): return p.get("name", "") if isinstance(p, dict) else str(p)
            with lc1:
                st.markdown(f"**{home}**" + (f"  `{hf}`" if hf else ""))
                for i, p in enumerate(h_lu[:11], 1):
                    pos = p.get("position", "") if isinstance(p, dict) else ""
                    st.write(f"{i}. {_pn(p)}" + (f" · *{pos}*" if pos else ""))
            with lc2:
                st.markdown(f"**{away}**" + (f"  `{af}`" if af else ""))
                for i, p in enumerate(a_lu[:11], 1):
                    pos = p.get("position", "") if isinstance(p, dict) else ""
                    st.write(f"{i}. {_pn(p)}" + (f" · *{pos}*" if pos else ""))


# ════════════════════════════════════════════════════════════════════════
# Data analysis expander
# ════════════════════════════════════════════════════════════════════════

def _render_data_analysis(pred: Dict):
    data = pred.get("data", {})
    conf = pred["confidence"]
    diag = pred.get("diagnostics", {})

    with st.expander("Data Analysis & Model Breakdown", expanded=False):
        comp = conf["components"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Prediction Clarity", f"{comp['prediction_clarity']:.1f}%")
        c2.metric("Data Quality",       f"{comp['data_quality']:.1f}%")
        c3.metric("Model Agreement",    f"{comp['model_agreement']:.1f}%")
        c4.metric("Lineup Certainty",   f"{comp['lineup_certainty']:.1f}%")
        st.progress(min(conf["total"]/100, 1.0),
                    text=f"Overall: {conf['total']:.1f}%  (93% threshold)")

        ca, cb = st.columns(2)
        with ca:
            st.markdown("**Matches analysed:**")
            st.write(f"- {pred['home_team']}: {data.get('home_form_count',0)} form matches")
            st.write(f"- {pred['away_team']}: {data.get('away_form_count',0)} form matches")
            st.write(f"- Head-to-head: {data.get('h2h_count',0)} past meetings")
            st.write(f"- WC scorers in model: {data.get('top_scorers_count',0)}")

        with cb:
            st.markdown("**Model inputs:**")
            hc = diag.get("home_composite", {})
            ac = diag.get("away_composite", {})
            if hc:
                st.write(f"- {pred['home_team']} base xG: {hc.get('base_lam',0):.2f}")
                st.write(f"- {pred['home_team']} ELO adj: {hc.get('elo_adj',1):.2f}x")
                st.write(f"- {pred['home_team']} form adj: {hc.get('form_adj',1):.2f}x")
            if ac:
                st.write(f"- {pred['away_team']} base xG: {ac.get('base_lam',0):.2f}")
                st.write(f"- {pred['away_team']} ELO adj: {ac.get('elo_adj',1):.2f}x")
                st.write(f"- {pred['away_team']} form adj: {ac.get('form_adj',1):.2f}x")

        # H2H summary
        h2h = data.get("h2h", [])
        if h2h:
            st.markdown("**Head-to-Head (last 5):**")
            hw = sum(1 for m in h2h[:5] if m.get("result") == "home")
            dr = sum(1 for m in h2h[:5] if m.get("result") == "draw")
            aw = sum(1 for m in h2h[:5] if m.get("result") == "away")
            st.write(
                f"{pred['home_team']} wins: **{hw}** · "
                f"Draws: **{dr}** · "
                f"{pred['away_team']} wins: **{aw}**"
            )
            for m in h2h[:5]:
                st.caption(
                    f"{m.get('date','')[:10]}  "
                    f"{m.get('home_team','?')} {m.get('home_score','?')}-{m.get('away_score','?')} "
                    f"{m.get('away_team','?')}"
                )

        srcs = data.get("data_sources", [])
        if srcs:
            st.caption("Sources: " + "  ·  ".join(srcs))


# ════════════════════════════════════════════════════════════════════════
# Value bets table
# ════════════════════════════════════════════════════════════════════════

def _render_value_bets_table(vbets: List[Dict], odds_src: Optional[str]):
    if not vbets:
        if odds_src:
            st.caption("No value bets found at current bookmaker prices.")
        return

    rows = []
    for v in vbets:
        rows.append({
            "Market":    v["market"],
            "Selection": v["selection"],
            "Our Prob":  f"{v['model_prob']*100:.1f}%",
            "Our Odds":  f"{v['model_odds']:.2f}",
            "Book Odds": f"{v['bookie_odds']:.2f}",
            "Edge":      f"+{v['edge_pct']:.1f}%",
            "EV":        f"{v['expected_value']:+.3f}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.apply(
            lambda _: ["background-color:#0a2718;color:#00e676"] * len(df.columns),
            axis=1,
        ),
        hide_index=True,
        use_container_width=True,
    )


# ════════════════════════════════════════════════════════════════════════
# Main prediction renderer
# ════════════════════════════════════════════════════════════════════════

def render_prediction(pred: Dict):
    if "error" in pred:
        st.error(f"Prediction error: {pred['error']}")
        return

    home    = pred["home_team"]
    away    = pred["away_team"]
    markets = pred["markets"]
    vbets   = pred.get("value_bets", [])
    data    = pred.get("data", {})
    oddsrc  = pred.get("bookmaker_odds_source")

    # 1. Match header (confidence bar, xG, lineups)
    _render_match_header(pred)

    # 2. Best bet recommendation — answers "what to bet on"
    _render_bet_recommendation(markets, vbets, home, away, oddsrc)

    if vbets:
        with st.expander(f"All Value Bets ({len(vbets)} found)", expanded=False):
            _render_value_bets_table(vbets, oddsrc)

    st.divider()

    # 3. Market tabs — matches Stake's navigation
    tabs = st.tabs(["Main", "Goals", "Asian Lines", "Half", "Goalscorers"])

    with tabs[0]:
        _tab_main(markets, home, away, vbets)

    with tabs[1]:
        _tab_goals(markets, home, away)

    with tabs[2]:
        _tab_asian(markets, home, away)

    with tabs[3]:
        _tab_half(markets, home, away)

    with tabs[4]:
        _tab_goalscorers(data, home, away)

    # 4. Data analysis
    _render_data_analysis(pred)


# ════════════════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════════════════

st.markdown(
    '<div style="background:linear-gradient(135deg,#0a1524,#0d2040);'
    'padding:16px 26px;border-radius:10px;margin-bottom:16px;'
    'border:1px solid #1e3351">'
    '<h1 style="margin:0;color:#00e5ff;font-family:monospace;'
    'letter-spacing:3px;font-size:1.6rem">FIFA 2026 — MATCH PREDICTOR</h1>'
    '<p style="margin:4px 0 0;color:#6b8099;font-size:.8rem">'
    'Poisson &middot; Dixon-Coles &middot; ELO &middot; Form &middot; '
    'Sofascore &middot; Goalscorer Model</p></div>',
    unsafe_allow_html=True,
)

engine = load_engine()

with st.sidebar:
    st.markdown("## FIFA 2026 Predictor")
    st.caption(f"ELO database: {len(engine.elo_ratings)} teams")
    st.divider()

    mode = st.radio("Mode", ["Today's Matches", "Specific Match"], index=0)

    if "Today" in mode:
        target_date = st.date_input("Match date", value=date.today())
        date_str    = target_date.isoformat()
    else:
        st.markdown("**Teams:**")
        home_input = st.text_input("Home Team", placeholder="e.g. Brazil")
        away_input = st.text_input("Away Team", placeholder="e.g. Morocco")
        date_str   = date.today().isoformat()

    st.divider()
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"5-min cache · {datetime.now().strftime('%H:%M:%S')}")
    st.divider()
    st.caption(
        "**Sources:**\nfootball-data.org · Sofascore\n"
        "TheSportsDB · NewsAPI · GNews\nOpen-Meteo"
    )

# ── Today's matches ────────────────────────────────────────────────────
if "Today" in mode:
    with st.spinner("Fetching fixtures..."):
        fixtures = fetch_fixtures(engine, date_str)

    if not fixtures:
        st.warning("No FIFA 2026 matches found. Try a different date or Specific Match mode.")
        st.stop()

    d_label    = date.fromisoformat(date_str).strftime("%A %d %B %Y")
    auto_count = sum(1 for f in fixtures if f.get("sofascore_id"))
    st.markdown(
        f"**{len(fixtures)} match{'es' if len(fixtures) != 1 else ''} "
        f"· {d_label}** — {auto_count} with live odds"
    )

    tab_labels = [
        f"{f.get('home_team','?')} vs {f.get('away_team','?')}"
        for f in fixtures
    ]
    match_tabs = st.tabs(tab_labels)

    for tab, fixture in zip(match_tabs, fixtures):
        with tab:
            h     = fixture.get("home_team", "")
            a     = fixture.get("away_team", "")
            fid   = str(fixture.get("id", ""))
            sfid  = fixture.get("sofascore_id")
            city  = fixture.get("city") or fixture.get("venue") or "Dallas"
            mdate = fixture.get("date", "")[:10] or date_str
            status = (fixture.get("sofascore_status") or fixture.get("status") or "").strip()

            if status:
                s_lo = status.lower()
                if "ended" in s_lo or "finished" in s_lo:
                    st.info(f"Match finished — {status}")
                elif "progress" in s_lo or "live" in s_lo:
                    st.success(f"LIVE — {status}")
                else:
                    st.caption(f"Status: {status}")

            with st.spinner(f"Predicting {h} vs {a}..."):
                try:
                    pred = fetch_prediction(engine, h, a, fid, sfid, city, mdate)
                    render_prediction(pred)
                except Exception as exc:
                    st.error(f"Prediction failed: {exc}")

# ── Specific match ─────────────────────────────────────────────────────
else:
    if not home_input.strip() or not away_input.strip():
        st.info("Enter both team names in the sidebar.")
    else:
        h = home_input.strip()
        a = away_input.strip()
        st.markdown(f"## {h}  vs  {a}")
        with st.spinner(f"Predicting {h} vs {a}..."):
            try:
                pred = fetch_prediction(engine, h, a, "", None, "Dallas", date_str)
                render_prediction(pred)
            except Exception as exc:
                st.error(f"Prediction failed: {exc}")
