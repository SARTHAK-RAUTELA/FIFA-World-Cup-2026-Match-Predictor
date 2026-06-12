"""
FIFA 2026 Match Prediction - Web Dashboard
Run: streamlit run app.py  |  FIFA_Web.bat
"""
from datetime import date, datetime
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

# Auto-refresh for live matches (graceful fallback if not installed)
try:
    from streamlit_autorefresh import st_autorefresh as _st_autorefresh
    _AUTOREFRESH_OK = True
except ImportError:
    _AUTOREFRESH_OK = False

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
# Live data cache (short TTL — 30 s)
# ════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def get_live_collector():
    from collectors.live_collector import LiveMatchCollector
    return LiveMatchCollector()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_live_data(_collector, event_id: int) -> Dict:
    return _collector.get_live_data(event_id)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_commentary(_collector, event_id: int) -> List[Dict]:
    return _collector.get_commentary(event_id)


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
# Bet Recommendation — always shows top 3 picks + confirms value bets
# ════════════════════════════════════════════════════════════════════════

def _build_top_picks(markets: Dict, home: str, away: str) -> List[Dict]:
    """
    Build the 3 highest-confidence model picks across all markets.
    Returns list of {market, selection, prob, fair_odds, why, risk}
    """
    candidates = []

    x  = markets["1x2"]
    b  = markets["btts"]
    d  = markets["draw_no_bet"]
    dc = markets["double_chance"]
    lh = markets["lam_home"]
    la = markets["lam_away"]

    # 1X2 picks
    for label, prob, odds in [
        (f"{home} Win", x["home"]["prob"], x["home"]["odds"]),
        ("Draw",         x["draw"]["prob"], x["draw"]["odds"]),
        (f"{away} Win",  x["away"]["prob"], x["away"]["odds"]),
    ]:
        elo_note = f"xG {lh:.2f} vs {la:.2f}"
        candidates.append({
            "market": "Match Winner (1X2)", "selection": label,
            "prob": prob, "fair_odds": odds,
            "why": f"Outright match winner. {elo_note}.",
        })

    # Draw No Bet — removes draw risk
    for label, prob, odds in [
        (f"{home}", d["home"]["prob"], d["home"]["odds"]),
        (f"{away}", d["away"]["prob"], d["away"]["odds"]),
    ]:
        candidates.append({
            "market": "Draw No Bet", "selection": label,
            "prob": prob, "fair_odds": odds,
            "why": "Bet refunded if draw. Lower odds, lower risk.",
        })

    # BTTS
    for label, prob, odds in [
        ("Yes", b["yes"]["prob"], b["yes"]["odds"]),
        ("No",  b["no"]["prob"],  b["no"]["odds"]),
    ]:
        total_xg = lh + la
        candidates.append({
            "market": "Both Teams to Score", "selection": label,
            "prob": prob, "fair_odds": odds,
            "why": f"Total xG {total_xg:.2f}. {'High-scoring game expected.' if total_xg > 2.5 else 'Tight game expected.'}",
        })

    # Double Chance (safest bet family)
    dc_opts = [
        (f"{home} or Draw", dc["home_draw"]["prob"], dc["home_draw"]["odds"]),
        (f"{away} or Draw", dc["away_draw"]["prob"], dc["away_draw"]["odds"]),
    ]
    for label, prob, odds in dc_opts:
        candidates.append({
            "market": "Double Chance", "selection": label,
            "prob": prob, "fair_odds": odds,
            "why": "Covers 2 of 3 possible results. Safer, lower odds.",
        })

    # Sort by probability and take top 3 (avoid duplicates on same team/market family)
    seen_markets = set()
    picks = []
    for c in sorted(candidates, key=lambda x: x["prob"], reverse=True):
        mkey = c["market"].split(" ")[0]  # rough dedup by first word
        if mkey not in seen_markets or c["market"] not in seen_markets:
            seen_markets.add(c["market"])
            p = c["prob"]
            c["risk"] = "Lower risk" if p > 0.62 else ("Medium risk" if p > 0.48 else "Higher risk")
            c["risk_col"] = "#00e676" if p > 0.62 else ("#f9a825" if p > 0.48 else "#ef5350")
            picks.append(c)
        if len(picks) == 3:
            break

    return picks


def _render_bet_recommendation(markets: Dict, vbets: List[Dict],
                                home: str, away: str, odds_src: Optional[str]):
    """
    Always shows top 3 picks + confirmed value bets when available.
    Green box = confirmed value vs bookmaker (BET NOW).
    Numbered picks = model's best bets (check your bookmaker price).
    """

    # ── Confirmed value bets (green — bookmaker price > fair price) ──────
    if vbets:
        best = vbets[0]
        p   = best["model_prob"]
        rc  = "#00e676" if p > 0.55 else ("#f9a825" if p > 0.40 else "#ef5350")
        rl  = "Lower risk" if p > 0.55 else ("Medium risk" if p > 0.40 else "Higher risk")
        st.markdown(
            f'<div style="background:#061c0f;border:2px solid #00e676;'
            f'border-radius:10px;padding:14px 18px;margin:10px 0 6px">'
            f'<div style="color:#00e676;font-weight:800;font-size:.92rem;'
            f'margin-bottom:6px">VALUE BET FOUND — BET THIS NOW</div>'
            f'<div style="font-size:1.1rem;color:#fff;font-weight:700;margin-bottom:8px">'
            f'{best["market"]}  &#8594;  {best["selection"]}</div>'
            f'<div style="display:flex;gap:16px;flex-wrap:wrap;font-size:.82rem;margin-bottom:5px">'
            f'<span style="color:#8fc">Our fair: <b>{best["model_odds"]:.2f}</b></span>'
            f'<span style="color:#fa0">Bookmaker offers: <b>{best["bookie_odds"]:.2f}</b></span>'
            f'<span style="color:#00e676;font-weight:700">Edge: +{best["edge_pct"]:.1f}%</span>'
            f'<span style="color:#aaa">Prob: {p*100:.1f}%</span>'
            f'<span style="color:{rc}">{rl}</span>'
            f'</div>'
            f'<div style="color:#3a7a4a;font-size:.74rem">'
            f'Expected value +{best["expected_value"]:.3f} per unit staked'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        if len(vbets) > 1:
            extras = "  ·  ".join(
                f'{v["market"]} → {v["selection"]} (+{v["edge_pct"]:.1f}%)'
                for v in vbets[1:]
            )
            st.caption(f"Also value: {extras}")
        st.markdown("")

    # ── Top 3 model picks — always shown ────────────────────────────────
    picks = _build_top_picks(markets, home, away)

    st.markdown(
        f'<div style="background:#0d1b2e;border:1px solid #1e3351;'
        f'border-radius:10px;padding:14px 18px;margin:6px 0 4px">'
        f'<div style="color:#00e5ff;font-weight:800;font-size:.92rem;'
        f'margin-bottom:4px">TOP 3 MODEL PICKS</div>'
        f'<div style="color:#6b8099;font-size:.74rem;margin-bottom:12px">'
        f'Based on Poisson model · ELO · Form data. '
        f'{"Bookmaker odds compared above." if vbets else "Compare these fair odds with your bookmaker — bet only if their price is HIGHER."}'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    pick_cols = st.columns(3)
    rank_labels = ["#1  BEST BET", "#2  GOOD BET", "#3  CONSIDER"]
    rank_bgs    = ["#0d2318", "#0d1f30", "#1a2637"]
    rank_borders = ["#00e676", "#00b0ff", "#7fa8d1"]

    for col, pick, rank_lbl, bg, border in zip(
        pick_cols, picks, rank_labels, rank_bgs, rank_borders
    ):
        col.markdown(
            f'<div style="background:{bg};border:1px solid {border};'
            f'border-radius:8px;padding:14px 12px;height:100%">'
            f'<div style="color:{border};font-size:.72rem;font-weight:700;'
            f'margin-bottom:8px;letter-spacing:.5px">{rank_lbl}</div>'
            f'<div style="color:#ffffff;font-size:1.0rem;font-weight:700;'
            f'margin-bottom:3px">{pick["selection"]}</div>'
            f'<div style="color:#7fa8d1;font-size:.75rem;margin-bottom:10px">'
            f'{pick["market"]}</div>'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;margin-bottom:8px">'
            f'<div style="text-align:center">'
            f'<div style="color:#8899aa;font-size:.67rem">Our probability</div>'
            f'<div style="color:#00e5ff;font-size:1.1rem;font-weight:700">'
            f'{pick["prob"]*100:.1f}%</div>'
            f'</div>'
            f'<div style="text-align:center">'
            f'<div style="color:#8899aa;font-size:.67rem">Min odds to bet</div>'
            f'<div style="color:#f9a825;font-size:1.1rem;font-weight:700">'
            f'{pick["fair_odds"]:.2f}</div>'
            f'</div></div>'
            f'<div style="background:#0a1220;border-radius:4px;padding:6px 8px;'
            f'font-size:.71rem;color:#5d7a90;margin-bottom:6px">{pick["why"]}</div>'
            f'<div style="color:{pick["risk_col"]};font-size:.7rem;font-weight:600">'
            f'{pick["risk"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Betting rule ─────────────────────────────────────────────────────
    st.markdown(
        f'<div style="background:#0a0f18;border:1px solid #1a2637;'
        f'border-radius:6px;padding:10px 14px;margin:8px 0 4px;'
        f'font-size:.76rem;color:#6b8099">'
        f'<b style="color:#cdd9e5">HOW TO USE:</b> '
        f'Open Stake.com &#8594; find the market &#8594; '
        f'if their odds are <b style="color:#f9a825">HIGHER</b> than '
        f'"Min odds to bet" above &#8594; '
        f'<b style="color:#00e676">place the bet</b>. '
        f'If lower &#8594; skip. Never bet more than you can afford to lose.'
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
# Live Match Tracker tab
# ════════════════════════════════════════════════════════════════════════

def _stat_bar(label: str, home_val: str, away_val: str):
    """Render a horizontal stat comparison bar."""
    def _num(v):
        try:
            return float(str(v).replace("%", "").strip())
        except Exception:
            return 0.0

    h = _num(home_val)
    a = _num(away_val)
    total = h + a
    h_pct = (h / total * 100) if total > 0 else 50.0
    a_pct = 100.0 - h_pct

    st.markdown(
        f'<div style="margin-bottom:10px">'
        f'<div style="display:flex;justify-content:space-between;'
        f'font-size:.76rem;color:#cdd9e5;margin-bottom:3px">'
        f'<span style="font-weight:600">{home_val}</span>'
        f'<span style="color:#7fa8d1">{label}</span>'
        f'<span style="font-weight:600">{away_val}</span>'
        f'</div>'
        f'<div style="display:flex;height:6px;border-radius:3px;overflow:hidden">'
        f'<div style="width:{h_pct:.1f}%;background:#00b0ff"></div>'
        f'<div style="width:{a_pct:.1f}%;background:#ff5252"></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _tab_live(fixture: Dict, pred: Dict, live_collector):
    """Complete live match tracker: score, events, stats, updated prediction."""
    from models.live_model import update_live, live_recommendations

    event_id = fixture.get("sofascore_id") or fixture.get("event_id")
    home     = pred["home_team"]
    away     = pred["away_team"]
    lam_h    = pred["markets"]["lam_home"]
    lam_a    = pred["markets"]["lam_away"]

    if not event_id:
        st.info("Live tracking needs a Sofascore match ID. Not available for this fixture.")
        return

    # ── Auto-refresh control ─────────────────────────────────────────
    cr1, cr2, cr3 = st.columns([2, 1, 2])
    with cr1:
        if st.button("Refresh Now", key=f"ref_{event_id}"):
            st.cache_data.clear()
            st.rerun()
    with cr2:
        auto = st.toggle("Auto 60s", key=f"auto_{event_id}",
                         value=st.session_state.get(f"auto_{event_id}", False))
        st.session_state[f"auto_{event_id}"] = auto
    with cr3:
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    if auto and _AUTOREFRESH_OK:
        _st_autorefresh(interval=60_000, key=f"ar_{event_id}")
    elif auto:
        st.caption("Install `streamlit-autorefresh` for true auto-refresh. Showing manual refresh.")

    # ── Fetch live data ──────────────────────────────────────────────
    with st.spinner("Fetching live data..."):
        live = fetch_live_data(live_collector, event_id)

    if live.get("error"):
        st.warning(f"Live data unavailable: {live['error']}")
        return

    h_sc = live["home_score"]
    a_sc = live["away_score"]
    minute = live["minute"] or 0
    status = live["status"]
    is_live = live["is_live"]
    is_ht   = live["is_halftime"]
    is_fin  = live["is_finished"]

    # ── Live scoreboard ──────────────────────────────────────────────
    if is_live:
        status_color, status_label = "#ef5350", f"LIVE  {minute}'"
    elif is_ht:
        status_color, status_label = "#f9a825", "HALF TIME"
    elif is_fin:
        status_color, status_label = "#7fa8d1", "FULL TIME"
    else:
        status_color, status_label = "#6b8099", status

    ht_h = live.get("ht_home_score")
    ht_a = live.get("ht_away_score")
    ht_str = f"  HT: {ht_h}-{ht_a}" if ht_h is not None else ""

    st.markdown(
        f'<div style="background:#0d1b2e;border:1px solid #1e3351;'
        f'border-radius:12px;padding:20px 28px;text-align:center;margin-bottom:16px">'
        f'<div style="color:{status_color};font-size:.8rem;font-weight:700;'
        f'letter-spacing:2px;margin-bottom:10px">{status_label}</div>'
        f'<div style="display:flex;justify-content:center;align-items:center;gap:32px">'
        f'<div style="font-size:1.1rem;font-weight:700;color:#cdd9e5;text-align:right;min-width:120px">{home}</div>'
        f'<div style="font-size:3rem;font-weight:900;color:#ffffff;letter-spacing:4px">'
        f'{h_sc}  –  {a_sc}</div>'
        f'<div style="font-size:1.1rem;font-weight:700;color:#cdd9e5;text-align:left;min-width:120px">{away}</div>'
        f'</div>'
        f'<div style="color:#6b8099;font-size:.74rem;margin-top:6px">{ht_str}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── In-play prediction update ────────────────────────────────────
    if is_live or is_ht or is_fin:
        live_pred = update_live(lam_h, lam_a, h_sc, a_sc, minute, is_ht)
        lx = live_pred["1x2"]

        orig_x = pred["markets"]["1x2"]

        def _arrow(new, old):
            if new > old + 0.02:  return " ▲"
            if new < old - 0.02:  return " ▼"
            return " ─"

        _mhdr("Updated Match Prediction (In-Play)")
        c1, c2, c3 = st.columns(3)
        for col, label, new_p, old_p in [
            (c1, f"{home} Win", lx["home"],  orig_x["home"]["prob"]),
            (c2, "Draw",        lx["draw"],   orig_x["draw"]["prob"]),
            (c3, f"{away} Win", lx["away"],   orig_x["away"]["prob"]),
        ]:
            arrow = _arrow(new_p, old_p)
            arrow_col = "#00e676" if "▲" in arrow else ("#ef5350" if "▼" in arrow else "#7fa8d1")
            col.markdown(
                f'<div style="background:#1a2637;border:1px solid #2d4a6e;'
                f'border-radius:8px;padding:12px 8px;text-align:center">'
                f'<div style="color:#7fa8d1;font-size:.74rem;margin-bottom:4px">{label}</div>'
                f'<div style="color:#00e5ff;font-size:1.3rem;font-weight:700">'
                f'{new_p*100:.1f}%</div>'
                f'<div style="color:{arrow_col};font-size:.72rem;margin-top:3px">'
                f'{arrow} was {old_p*100:.1f}%</div>'
                f'<div style="color:#6b8099;font-size:.68rem">odds {round(1/new_p,2) if new_p > 0.01 else 99}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Live bet recommendations ─────────────────────────────────
        live_recs = live_recommendations(live_pred, pred, home, away)
        if live_recs:
            _mhdr("Live Bet Recommendations")
            st.caption("Based on current score, elapsed time, and remaining xG.")
            for i, rec in enumerate(live_recs, 1):
                urg_col = "#00e676" if rec["urgency"] == "HIGH" else ("#f9a825" if rec["urgency"] == "MEDIUM" else "#6b8099")
                st.markdown(
                    f'<div style="background:#0d1b2e;border-left:3px solid {urg_col};'
                    f'border-radius:6px;padding:10px 14px;margin-bottom:6px;'
                    f'display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">'
                    f'<div>'
                    f'<div style="color:{urg_col};font-size:.68rem;font-weight:700;margin-bottom:2px">'
                    f'#{i}  {rec["urgency"]} PRIORITY</div>'
                    f'<div style="color:#fff;font-size:.9rem;font-weight:700">'
                    f'{rec["market"]}  →  {rec["selection"]}</div>'
                    f'<div style="color:#6b8099;font-size:.72rem;margin-top:2px">{rec["why"]}</div>'
                    f'</div>'
                    f'<div style="text-align:right">'
                    f'<div style="color:#00e5ff;font-size:1.15rem;font-weight:700">'
                    f'{rec["fair_odds"]:.2f}</div>'
                    f'<div style="color:#7fa8d1;font-size:.72rem">{rec["prob"]*100:.1f}%</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

        # ── Next goal + more goals strip ─────────────────────────────
        if not is_fin:
            ng = live_pred["next_goal"]
            mg = live_pred["more_goals"]
            _mhdr("In-Play Markets")
            mc1, mc2, mc3, mc4 = st.columns(4)
            for col, lbl, p in [
                (mc1, f"{home} next goal", ng["home"]),
                (mc2, f"{away} next goal", ng["away"]),
                (mc3, "No more goals",      ng["no_goal"]),
                (mc4, "More goals (yes)",   mg["yes"]),
            ]:
                _bet_card(col, lbl, round(1/p, 2) if p > 0.01 else 99, p)

    st.divider()

    # ── Event timeline (commentary) ──────────────────────────────────
    incidents = live["incidents"]
    commentary = fetch_commentary(live_collector, event_id)

    cl1, cl2 = st.columns([3, 2])

    with cl1:
        _mhdr(f"Match Events  ({len(incidents)} total)")
        if not incidents:
            st.caption("No events recorded yet.")
        else:
            # Show most recent first
            for inc in reversed(incidents):
                is_h = inc["is_home"]
                team_col = "#00b0ff" if is_h else "#ff5252"
                bg_col   = "#0a1e2e" if inc["is_goal"] else "#0d1b2e"
                border   = "2px solid #00e676" if inc["is_goal"] else "1px solid #1e3351"
                side     = "←" if is_h else "→"
                st.markdown(
                    f'<div style="background:{bg_col};border:{border};'
                    f'border-radius:6px;padding:8px 12px;margin-bottom:4px;'
                    f'display:flex;align-items:center;gap:12px">'
                    f'<div style="color:#6b8099;font-size:.75rem;min-width:38px;text-align:right">'
                    f'{inc["minute_str"]}</div>'
                    f'<div style="font-size:1.1rem">{inc["icon"]}</div>'
                    f'<div style="flex:1">'
                    f'<div style="color:{team_col};font-size:.7rem;font-weight:600">'
                    f'{side} {inc["team"]}</div>'
                    f'<div style="color:#cdd9e5;font-size:.82rem">{inc["desc"]}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    with cl2:
        _mhdr("Live Statistics")
        stats = live["statistics"]
        if not stats:
            st.caption("Statistics not yet available.")
        else:
            from collectors.live_collector import _STAT_ORDER
            shown = 0
            for stat_name in _STAT_ORDER:
                if stat_name in stats:
                    s = stats[stat_name]
                    _stat_bar(stat_name, s["home"], s["away"])
                    shown += 1
            # Any remaining stats not in our order list
            for k, v in stats.items():
                if k not in _STAT_ORDER and shown < 14:
                    _stat_bar(k, v["home"], v["away"])
                    shown += 1

        # Legend
        st.markdown(
            f'<div style="display:flex;gap:16px;margin-top:8px;font-size:.7rem">'
            f'<span style="color:#00b0ff">■ {home}</span>'
            f'<span style="color:#ff5252">■ {away}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Text commentary ──────────────────────────────────────────────
    if commentary:
        _mhdr(f"Live Commentary  ({len(commentary)} entries)")
        for line in commentary[:30]:
            important = line.get("important", False)
            bg   = "#0a1e2e" if important else "#0d1421"
            col_ = "#f9a825" if important else "#6b8099"
            st.markdown(
                f'<div style="background:{bg};border-radius:5px;'
                f'padding:6px 12px;margin-bottom:3px;display:flex;gap:10px">'
                f'<span style="color:#2d4a6e;font-size:.72rem;min-width:30px">'
                f'{line["minute"]}\''
                f'</span>'
                f'<span style="color:{col_};font-size:.78rem">{line["text"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════════════
# Main prediction renderer
# ════════════════════════════════════════════════════════════════════════

def render_prediction(pred: Dict, fixture: Dict = None):
    if "error" in pred:
        st.error(f"Prediction error: {pred['error']}")
        return

    home    = pred["home_team"]
    away    = pred["away_team"]
    markets = pred["markets"]
    vbets   = pred.get("value_bets", [])
    data    = pred.get("data", {})
    oddsrc  = pred.get("bookmaker_odds_source")
    fixture = fixture or {}

    # Detect if this match is live or finished (for tab ordering)
    status = (
        fixture.get("sofascore_status") or
        fixture.get("status") or ""
    ).lower()
    has_live = bool(
        fixture.get("sofascore_id") and
        ("progress" in status or "live" in status or
         "halftime" in status or "ended" in status or
         "finished" in status)
    )

    # 1. Match header
    _render_match_header(pred)

    # 2. Bet recommendation
    _render_bet_recommendation(markets, vbets, home, away, oddsrc)

    if vbets:
        with st.expander(f"All Value Bets ({len(vbets)} found)", expanded=False):
            _render_value_bets_table(vbets, oddsrc)

    st.divider()

    # 3. Market tabs — Live tab first when match is active
    if has_live:
        tab_list = ["Live Tracker", "Main", "Goals", "Asian Lines", "Half", "Goalscorers"]
    else:
        tab_list = ["Main", "Goals", "Asian Lines", "Half", "Goalscorers"]

    tabs = st.tabs(tab_list)

    if has_live:
        with tabs[0]:
            live_col = get_live_collector()
            _tab_live(fixture, pred, live_col)
        offset = 1
    else:
        offset = 0

    with tabs[offset + 0]:
        _tab_main(markets, home, away, vbets)
    with tabs[offset + 1]:
        _tab_goals(markets, home, away)
    with tabs[offset + 2]:
        _tab_asian(markets, home, away)
    with tabs[offset + 3]:
        _tab_half(markets, home, away)
    with tabs[offset + 4]:
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
                    render_prediction(pred, fixture)
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
