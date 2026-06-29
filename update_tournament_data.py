"""
Tournament data updater — adds all FIFA 2026 results from June 21-29 to the JSON
and applies ELO updates. Run once to bring the system up to date.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "data", "fifa_2026_results.json")
ANALYSIS_PATH = os.path.join(os.path.dirname(__file__), "data", "team_analysis.json")


# ─── All new match results ──────────────────────────────────────────────────
NEW_RESULTS = [
    # ── MD2: Group G (June 21) ─────────────────────────────────────────
    {"match_id":"WC2026_G3","date":"2026-06-21","matchday":2,"group":"G","stage":"group_stage",
     "home_team":"Belgium","away_team":"Iran","home_goals":2,"away_goals":0,"result":"H",
     "venue":"BC Place","city":"Vancouver","country":"Canada",
     "scorers":{"home":["De Bruyne","Doku"],"away":[]},
     "notes":"Belgium controlled the match. De Bruyne and Doku on the scoresheet."},
    {"match_id":"WC2026_G4","date":"2026-06-21","matchday":2,"group":"G","stage":"group_stage",
     "home_team":"New Zealand","away_team":"Egypt","home_goals":1,"away_goals":2,"result":"A",
     "venue":"NRG Stadium","city":"Houston","country":"USA",
     "scorers":{"home":["Wood"],"away":["Salah","Elneny"]},
     "notes":"Egypt came from behind to beat New Zealand 2-1. Salah and Elneny scored."},
    # ── MD2: Group H (June 21) ─────────────────────────────────────────
    {"match_id":"WC2026_H3","date":"2026-06-21","matchday":2,"group":"H","stage":"group_stage",
     "home_team":"Spain","away_team":"Saudi Arabia","home_goals":2,"away_goals":0,"result":"H",
     "venue":"Mercedes-Benz Stadium","city":"Atlanta","country":"USA",
     "scorers":{"home":["Morata","Olmo"],"away":[]},
     "notes":"Spain bounced back from 0-0 vs Cabo Verde with convincing 2-0 win."},
    {"match_id":"WC2026_H4","date":"2026-06-21","matchday":2,"group":"H","stage":"group_stage",
     "home_team":"Uruguay","away_team":"Cabo Verde","home_goals":0,"away_goals":1,"result":"A",
     "venue":"Hard Rock Stadium","city":"Miami","country":"USA",
     "scorers":{"home":[],"away":["Garry Rodrigues"]},
     "notes":"Cabo Verde major upset — beat Uruguay 1-0 to go top of Group H on goal difference. Garry Rodrigues the hero."},
    # ── MD2: Group I (June 22) ─────────────────────────────────────────
    {"match_id":"WC2026_I3","date":"2026-06-22","matchday":2,"group":"I","stage":"group_stage",
     "home_team":"France","away_team":"Iraq","home_goals":2,"away_goals":0,"result":"H",
     "venue":"Empower Field","city":"Denver","country":"USA",
     "scorers":{"home":["Mbappé","Dembélé"],"away":[]},
     "notes":"France professional win. Mbappé and Dembélé both on target."},
    {"match_id":"WC2026_I4","date":"2026-06-22","matchday":2,"group":"I","stage":"group_stage",
     "home_team":"Senegal","away_team":"Norway","home_goals":2,"away_goals":3,"result":"A",
     "venue":"Camping World Stadium","city":"Orlando","country":"USA",
     "scorers":{"home":["Sarr","Diatta"],"away":["Haaland","Haaland","Odegaard"]},
     "notes":"Norway edge thriller 3-2. Haaland scored twice again. Both teams with 3 goals in 2 games."},
    # ── MD2: Group J (June 22) ─────────────────────────────────────────
    {"match_id":"WC2026_J3","date":"2026-06-22","matchday":2,"group":"J","stage":"group_stage",
     "home_team":"Argentina","away_team":"Austria","home_goals":2,"away_goals":0,"result":"H",
     "venue":"Allegiant Stadium","city":"Las Vegas","country":"USA",
     "scorers":{"home":["Messi","Lautaro Martínez"],"away":[]},
     "notes":"Messi scores again as Argentina qualify. Historic moment — Messi now oldest WC scorer ever in consecutive games."},
    {"match_id":"WC2026_J4","date":"2026-06-22","matchday":2,"group":"J","stage":"group_stage",
     "home_team":"Algeria","away_team":"Jordan","home_goals":1,"away_goals":0,"result":"H",
     "venue":"Levi's Stadium","city":"Santa Clara","country":"USA",
     "scorers":{"home":["Mahrez"],"away":[]},
     "notes":"Algeria survive with narrow 1-0 win. Mahrez the difference-maker."},
    # ── MD2: Group K (June 23) ─────────────────────────────────────────
    {"match_id":"WC2026_K3","date":"2026-06-23","matchday":2,"group":"K","stage":"group_stage",
     "home_team":"Portugal","away_team":"Uzbekistan","home_goals":3,"away_goals":0,"result":"H",
     "venue":"NRG Stadium","city":"Houston","country":"USA",
     "scorers":{"home":["Ronaldo","Félix","B.Silva"],"away":[]},
     "notes":"Portugal put Uzbekistan to the sword 3-0. Ronaldo penalty. Portugal back on track."},
    {"match_id":"WC2026_K4","date":"2026-06-23","matchday":2,"group":"K","stage":"group_stage",
     "home_team":"Colombia","away_team":"DR Congo","home_goals":2,"away_goals":0,"result":"H",
     "venue":"Estadio Azteca","city":"Mexico City","country":"Mexico",
     "scorers":{"home":["Luis Díaz","James Rodríguez"],"away":[]},
     "notes":"Colombia dominant again. Díaz and James on the scoresheet. Colombia top Group K."},
    # ── MD2: Group L (June 23) ─────────────────────────────────────────
    {"match_id":"WC2026_L3","date":"2026-06-23","matchday":2,"group":"L","stage":"group_stage",
     "home_team":"England","away_team":"Ghana","home_goals":2,"away_goals":0,"result":"H",
     "venue":"AT&T Stadium","city":"Dallas","country":"USA",
     "scorers":{"home":["Kane","Bellingham"],"away":[]},
     "notes":"England clinical 2-0 win. Kane and Bellingham both scoring. England already through."},
    {"match_id":"WC2026_L4","date":"2026-06-23","matchday":2,"group":"L","stage":"group_stage",
     "home_team":"Croatia","away_team":"Panama","home_goals":2,"away_goals":0,"result":"H",
     "venue":"BMO Field","city":"Toronto","country":"Canada",
     "scorers":{"home":["Modrić","Perisic"],"away":[]},
     "notes":"Croatia ease past Panama 2-0. Modrić and Perisic goals."},

    # ── MD3: Group A (June 24) ─────────────────────────────────────────
    {"match_id":"WC2026_A5","date":"2026-06-24","matchday":3,"group":"A","stage":"group_stage",
     "home_team":"Mexico","away_team":"Czech Republic","home_goals":3,"away_goals":0,"result":"H",
     "venue":"Estadio Azteca","city":"Mexico City","country":"Mexico",
     "scorers":{"home":["Raúl Jiménez","Álvarez","Antuna"],"away":[]},
     "notes":"Mexico finish Group A unbeaten. Jiménez leads the line. Czech Republic eliminated."},
    {"match_id":"WC2026_A6","date":"2026-06-24","matchday":3,"group":"A","stage":"group_stage",
     "home_team":"South Africa","away_team":"South Korea","home_goals":1,"away_goals":0,"result":"H",
     "venue":"Estadio Akron","city":"Guadalajara","country":"Mexico",
     "scorers":{"home":["Percy Tau"],"away":[]},
     "notes":"South Africa stun South Korea to qualify. Percy Tau the hero. South Korea eliminated despite entering MD3 in 2nd."},
    # ── MD3: Group B (June 24) ─────────────────────────────────────────
    {"match_id":"WC2026_B5","date":"2026-06-24","matchday":3,"group":"B","stage":"group_stage",
     "home_team":"Switzerland","away_team":"Canada","home_goals":3,"away_goals":1,"result":"H",
     "venue":"Levi's Stadium","city":"San Francisco Bay Area","country":"USA",
     "scorers":{"home":["Shaqiri","Embolo","Amdouni"],"away":["Larin"]},
     "notes":"Switzerland claim Group B top spot. Canada finish 2nd despite late Larin goal."},
    {"match_id":"WC2026_B6","date":"2026-06-24","matchday":3,"group":"B","stage":"group_stage",
     "home_team":"Bosnia-Herzegovina","away_team":"Qatar","home_goals":3,"away_goals":1,"result":"H",
     "venue":"BMO Field","city":"Toronto","country":"Canada",
     "scorers":{"home":["Dzeko","Prevljak","Kolasinac"],"away":["Al-Haydos"]},
     "notes":"Bosnia beat Qatar 3-1 to finish 3rd in Group B and qualify as one of the best 3rd-place teams. Dzeko impressive."},
    # ── MD3: Group C (June 25) ─────────────────────────────────────────
    {"match_id":"WC2026_C5","date":"2026-06-25","matchday":3,"group":"C","stage":"group_stage",
     "home_team":"Brazil","away_team":"Scotland","home_goals":3,"away_goals":0,"result":"H",
     "venue":"Rose Bowl","city":"Los Angeles","country":"USA",
     "scorers":{"home":["Vinicius Jr.","Matheus Cunha","Rodrygo"],"away":[]},
     "notes":"Brazil cruise. Vinicius hat-trick-ish performance with a goal and assist. Scotland eliminated."},
    {"match_id":"WC2026_C6","date":"2026-06-25","matchday":3,"group":"C","stage":"group_stage",
     "home_team":"Morocco","away_team":"Haiti","home_goals":2,"away_goals":0,"result":"H",
     "venue":"MetLife Stadium","city":"East Rutherford","country":"USA",
     "scorers":{"home":["Saibari","Ziyech"],"away":[]},
     "notes":"Morocco clinical. Saibari continues brilliant tournament. Haiti exit winless."},
    # ── MD3: Group D (June 25) ─────────────────────────────────────────
    {"match_id":"WC2026_D5","date":"2026-06-25","matchday":3,"group":"D","stage":"group_stage",
     "home_team":"Turkey","away_team":"USA","home_goals":3,"away_goals":2,"result":"H",
     "venue":"AT&T Stadium","city":"Dallas","country":"USA",
     "scorers":{"home":["Calhanoglu","Yilmaz","Akturkoglu"],"away":["Pulisic","Balogun"]},
     "notes":"UPSET! Turkey beat USA 3-2 despite USA already qualified. Pulisic fitness scare but played. Turkey eliminated — too little too late."},
    {"match_id":"WC2026_D6","date":"2026-06-25","matchday":3,"group":"D","stage":"group_stage",
     "home_team":"Paraguay","away_team":"Australia","home_goals":0,"away_goals":0,"result":"D",
     "venue":"SoFi Stadium","city":"Los Angeles","country":"USA",
     "scorers":{"home":[],"away":[]},
     "notes":"Goalless draw means Australia finish 2nd on GD. Paraguay qualify as 3rd-place team. Turkey eliminated."},
    # ── MD3: Group E (June 25) ─────────────────────────────────────────
    {"match_id":"WC2026_E5","date":"2026-06-25","matchday":3,"group":"E","stage":"group_stage",
     "home_team":"Ivory Coast","away_team":"Curaçao","home_goals":2,"away_goals":0,"result":"H",
     "venue":"Gillette Stadium","city":"Boston","country":"USA",
     "scorers":{"home":["Haller","Kessié"],"away":[]},
     "notes":"Ivory Coast top 6pts. Curaçao eliminated."},
    {"match_id":"WC2026_E6","date":"2026-06-25","matchday":3,"group":"E","stage":"group_stage",
     "home_team":"Ecuador","away_team":"Germany","home_goals":2,"away_goals":1,"result":"H",
     "venue":"Lincoln Financial Field","city":"Philadelphia","country":"USA",
     "scorers":{"home":["Pacho","Caicedo"],"away":["Havertz"]},
     "notes":"MASSIVE UPSET! Ecuador beat Germany 2-1 in a historic result. Germany already qualified but still humbling. Ecuador qualify as 3rd-place team with 4 pts. Caicedo midfield masterclass."},
    # ── MD3: Group F (June 25) ─────────────────────────────────────────
    {"match_id":"WC2026_F5","date":"2026-06-25","matchday":3,"group":"F","stage":"group_stage",
     "home_team":"Netherlands","away_team":"Tunisia","home_goals":3,"away_goals":1,"result":"H",
     "venue":"SoFi Stadium","city":"Los Angeles","country":"USA",
     "scorers":{"home":["Gakpo","Depay","Brobbey"],"away":["Khazri"]},
     "notes":"Netherlands win comfortably. Gakpo scores again. Brobbey comes off the bench to add 3rd."},
    {"match_id":"WC2026_F6","date":"2026-06-25","matchday":3,"group":"F","stage":"group_stage",
     "home_team":"Japan","away_team":"Sweden","home_goals":1,"away_goals":1,"result":"D",
     "venue":"Rose Bowl","city":"Los Angeles","country":"USA",
     "scorers":{"home":["Mitoma"],"away":["Isak"]},
     "notes":"Japan and Sweden draw 1-1. Sweden qualify 2nd in Group F despite the draw. Japan out."},
    # ── MD3: Group G (June 26) ─────────────────────────────────────────
    {"match_id":"WC2026_G5","date":"2026-06-26","matchday":3,"group":"G","stage":"group_stage",
     "home_team":"Belgium","away_team":"New Zealand","home_goals":5,"away_goals":1,"result":"H",
     "venue":"NRG Stadium","city":"Houston","country":"USA",
     "scorers":{"home":["De Bruyne (2)","Doku","Batshuayi","Trossard"],"away":["Wood"]},
     "notes":"Belgium demolish New Zealand 5-1. De Bruyne brace. Belgium top Group G convincingly."},
    {"match_id":"WC2026_G6","date":"2026-06-26","matchday":3,"group":"G","stage":"group_stage",
     "home_team":"Egypt","away_team":"Iran","home_goals":1,"away_goals":1,"result":"D",
     "venue":"BC Place","city":"Vancouver","country":"Canada",
     "scorers":{"home":["Salah"],"away":["Taremi"]},
     "notes":"Egypt and Iran play out 1-1 draw. Egypt qualify 2nd. Iran eliminated. Salah and Taremi exchange goals."},
    # ── MD3: Group H (June 26) ─────────────────────────────────────────
    {"match_id":"WC2026_H5","date":"2026-06-26","matchday":3,"group":"H","stage":"group_stage",
     "home_team":"Spain","away_team":"Uruguay","home_goals":1,"away_goals":0,"result":"H",
     "venue":"Mercedes-Benz Stadium","city":"Atlanta","country":"USA",
     "scorers":{"home":["Pedri"],"away":[]},
     "notes":"Spain win Group H. Pedri winner. Uruguay eliminated — could not cope with Spain's pressing."},
    {"match_id":"WC2026_H6","date":"2026-06-26","matchday":3,"group":"H","stage":"group_stage",
     "home_team":"Saudi Arabia","away_team":"Cabo Verde","home_goals":0,"away_goals":0,"result":"D",
     "venue":"Hard Rock Stadium","city":"Miami","country":"USA",
     "scorers":{"home":[],"away":[]},
     "notes":"0-0 goalless draw. Cabo Verde qualify 2nd from Group H on goal difference over Saudi Arabia. Saudi Arabia eliminated."},
    # ── MD3: Group I (June 26) ─────────────────────────────────────────
    {"match_id":"WC2026_I5","date":"2026-06-26","matchday":3,"group":"I","stage":"group_stage",
     "home_team":"Norway","away_team":"France","home_goals":4,"away_goals":1,"result":"H",
     "venue":"Camping World Stadium","city":"Orlando","country":"USA",
     "scorers":{"home":["Haaland (2)","Odegaard","Isak"],"away":["Mbappé"]},
     "notes":"SHOCK RESULT! Norway beat France 4-1 to top Group I. Haaland brace — now 6 goals in 3 group games. Erling is unstoppable. France still qualify 2nd with 6pts. This sets up an incredible knockout stage."},
    {"match_id":"WC2026_I6","date":"2026-06-26","matchday":3,"group":"I","stage":"group_stage",
     "home_team":"Senegal","away_team":"Iraq","home_goals":5,"away_goals":0,"result":"H",
     "venue":"Empower Field","city":"Denver","country":"USA",
     "scorers":{"home":["Sarr (2)","Diatta","Ndiaye","Mendy"],"away":[]},
     "notes":"Senegal obliterate Iraq 5-0. Sarr brace. Senegal finish 3rd in Group I but qualify as one of the best 3rd-place teams. Iraq winless and exit."},
    # ── MD3: Group J (June 27) ─────────────────────────────────────────
    {"match_id":"WC2026_J5","date":"2026-06-27","matchday":3,"group":"J","stage":"group_stage",
     "home_team":"Argentina","away_team":"Jordan","home_goals":3,"away_goals":1,"result":"H",
     "venue":"Allegiant Stadium","city":"Las Vegas","country":"USA",
     "scorers":{"home":["Messi (2)","Lautaro Martínez"],"away":["Al-Tamari"]},
     "notes":"Messi scores twice including a stunning long-range goal. Argentina win Group J with 9 points. Messi now has 6 goals in 3 group games — leading the Golden Boot race."},
    {"match_id":"WC2026_J6","date":"2026-06-27","matchday":3,"group":"J","stage":"group_stage",
     "home_team":"Austria","away_team":"Algeria","home_goals":3,"away_goals":3,"result":"D",
     "venue":"Levi's Stadium","city":"Santa Clara","country":"USA",
     "scorers":{"home":["Sabitzer","Baumgartner","Alaba"],"away":["Mahrez (2)","Benrahma"]},
     "notes":"Wild 3-3 draw! Austria lead twice but Algeria fight back each time. Mahrez brace for Algeria — they finish 3rd with 2pts. Austria qualify 2nd in Group J with 4pts."},
    # ── MD3: Group K (June 27) ─────────────────────────────────────────
    {"match_id":"WC2026_K5","date":"2026-06-27","matchday":3,"group":"K","stage":"group_stage",
     "home_team":"Colombia","away_team":"Portugal","home_goals":0,"away_goals":0,"result":"D",
     "venue":"NRG Stadium","city":"Houston","country":"USA",
     "scorers":{"home":[],"away":[]},
     "notes":"Both already qualified. Neither side takes risks. Colombia 1st (7pts, GD +5), Portugal 2nd (5pts, GD +3)."},
    {"match_id":"WC2026_K6","date":"2026-06-27","matchday":3,"group":"K","stage":"group_stage",
     "home_team":"DR Congo","away_team":"Uzbekistan","home_goals":3,"away_goals":1,"result":"H",
     "venue":"Estadio Azteca","city":"Mexico City","country":"Mexico",
     "scorers":{"home":["Manzambi (2)","Kayembe"],"away":["Shomurodov"]},
     "notes":"DR Congo qualify as a 3rd-place team (4pts). Manzambi brace — Johan Manzambi has 3 goals in the tournament. Uzbekistan eliminated winless."},
    # ── MD3: Group L (June 27) ─────────────────────────────────────────
    {"match_id":"WC2026_L5","date":"2026-06-27","matchday":3,"group":"L","stage":"group_stage",
     "home_team":"England","away_team":"Panama","home_goals":2,"away_goals":0,"result":"H",
     "venue":"AT&T Stadium","city":"Dallas","country":"USA",
     "scorers":{"home":["Saka","Kane"],"away":[]},
     "notes":"England win Group L with 9pts. Dominant throughout. Kane leads England into knockouts."},
    {"match_id":"WC2026_L6","date":"2026-06-27","matchday":3,"group":"L","stage":"group_stage",
     "home_team":"Croatia","away_team":"Ghana","home_goals":2,"away_goals":1,"result":"H",
     "venue":"BMO Field","city":"Toronto","country":"Canada",
     "scorers":{"home":["Modrić","Gvardiol"],"away":["Kudus"]},
     "notes":"Croatia beat Ghana 2-1 to finish 2nd. Ghana qualify as 3rd-place team (3pts). Modrić inspires Croatia."},

    # ── Round of 32 (June 28) ─────────────────────────────────────────
    {"match_id":"WC2026_R32_01","date":"2026-06-28","matchday":None,"group":None,"stage":"round_of_32",
     "home_team":"South Africa","away_team":"Canada","home_goals":0,"away_goals":1,"result":"A",
     "venue":"Rose Bowl","city":"Los Angeles","country":"USA",
     "scorers":{"home":[],"away":["Eustaquio (90+5')"]},
     "notes":"DRAMATIC! Canada 1-0 South Africa. Stephen Eustaquio scores in the 95th minute to send Canada through. Stephen Eustaquio hero. Canada's first ever World Cup knockout stage win."},
]

# ── ELO updates for all new matches ──────────────────────────────────────────
NEW_ELO_UPDATES = [
    # MD2 Groups G-L
    {"home":"Belgium","away":"Iran","hg":2,"ag":0},
    {"home":"New Zealand","away":"Egypt","hg":1,"ag":2},
    {"home":"Spain","away":"Saudi Arabia","hg":2,"ag":0},
    {"home":"Uruguay","away":"Cabo Verde","hg":0,"ag":1},
    {"home":"France","away":"Iraq","hg":2,"ag":0},
    {"home":"Senegal","away":"Norway","hg":2,"ag":3},
    {"home":"Argentina","away":"Austria","hg":2,"ag":0},
    {"home":"Algeria","away":"Jordan","hg":1,"ag":0},
    {"home":"Portugal","away":"Uzbekistan","hg":3,"ag":0},
    {"home":"Colombia","away":"DR Congo","hg":2,"ag":0},
    {"home":"England","away":"Ghana","hg":2,"ag":0},
    {"home":"Croatia","away":"Panama","hg":2,"ag":0},
    # MD3 All groups
    {"home":"Mexico","away":"Czech Republic","hg":3,"ag":0},
    {"home":"South Africa","away":"South Korea","hg":1,"ag":0},
    {"home":"Switzerland","away":"Canada","hg":3,"ag":1},
    {"home":"Bosnia-Herzegovina","away":"Qatar","hg":3,"ag":1},
    {"home":"Brazil","away":"Scotland","hg":3,"ag":0},
    {"home":"Morocco","away":"Haiti","hg":2,"ag":0},
    {"home":"Turkey","away":"USA","hg":3,"ag":2},
    {"home":"Paraguay","away":"Australia","hg":0,"ag":0},
    {"home":"Ivory Coast","away":"Curaçao","hg":2,"ag":0},
    {"home":"Ecuador","away":"Germany","hg":2,"ag":1},
    {"home":"Netherlands","away":"Tunisia","hg":3,"ag":1},
    {"home":"Japan","away":"Sweden","hg":1,"ag":1},
    {"home":"Belgium","away":"New Zealand","hg":5,"ag":1},
    {"home":"Egypt","away":"Iran","hg":1,"ag":1},
    {"home":"Spain","away":"Uruguay","hg":1,"ag":0},
    {"home":"Saudi Arabia","away":"Cabo Verde","hg":0,"ag":0},
    {"home":"Norway","away":"France","hg":4,"ag":1},
    {"home":"Senegal","away":"Iraq","hg":5,"ag":0},
    {"home":"Argentina","away":"Jordan","hg":3,"ag":1},
    {"home":"Austria","away":"Algeria","hg":3,"ag":3},
    {"home":"Colombia","away":"Portugal","hg":0,"ag":0},
    {"home":"DR Congo","away":"Uzbekistan","hg":3,"ag":1},
    {"home":"England","away":"Panama","hg":2,"ag":0},
    {"home":"Croatia","away":"Ghana","hg":2,"ag":1},
    # R32
    {"home":"South Africa","away":"Canada","hg":0,"ag":1,"stage":"round_of_32"},
]

# ── Updated final group standings ─────────────────────────────────────────────
FINAL_STANDINGS = {
    "A": [
        {"team":"Mexico","played":3,"won":3,"drawn":0,"lost":0,"gf":6,"ga":0,"gd":6,"pts":9,"status":"QUALIFIED_1ST"},
        {"team":"South Africa","played":3,"won":1,"drawn":1,"lost":1,"gf":2,"ga":3,"gd":-1,"pts":4,"status":"QUALIFIED_2ND"},
        {"team":"South Korea","played":3,"won":1,"drawn":0,"lost":2,"gf":2,"ga":3,"gd":-1,"pts":3,"status":"ELIMINATED"},
        {"team":"Czech Republic","played":3,"won":0,"drawn":1,"lost":2,"gf":2,"ga":6,"gd":-4,"pts":1,"status":"ELIMINATED"},
    ],
    "B": [
        {"team":"Switzerland","played":3,"won":2,"drawn":1,"lost":0,"gf":8,"ga":3,"gd":5,"pts":7,"status":"QUALIFIED_1ST"},
        {"team":"Canada","played":3,"won":1,"drawn":1,"lost":1,"gf":8,"ga":4,"gd":4,"pts":4,"status":"QUALIFIED_2ND"},
        {"team":"Bosnia-Herzegovina","played":3,"won":1,"drawn":1,"lost":1,"gf":5,"ga":6,"gd":-1,"pts":4,"status":"QUALIFIED_3RD_BEST"},
        {"team":"Qatar","played":3,"won":0,"drawn":1,"lost":2,"gf":2,"ga":10,"gd":-8,"pts":1,"status":"ELIMINATED"},
    ],
    "C": [
        {"team":"Brazil","played":3,"won":2,"drawn":1,"lost":0,"gf":7,"ga":1,"gd":6,"pts":7,"status":"QUALIFIED_1ST"},
        {"team":"Morocco","played":3,"won":2,"drawn":1,"lost":0,"gf":4,"ga":1,"gd":3,"pts":7,"status":"QUALIFIED_2ND"},
        {"team":"Scotland","played":3,"won":1,"drawn":0,"lost":2,"gf":1,"ga":4,"gd":-3,"pts":3,"status":"ELIMINATED"},
        {"team":"Haiti","played":3,"won":0,"drawn":0,"lost":3,"gf":0,"ga":6,"gd":-6,"pts":0,"status":"ELIMINATED"},
    ],
    "D": [
        {"team":"USA","played":3,"won":2,"drawn":0,"lost":1,"gf":8,"ga":4,"gd":4,"pts":6,"status":"QUALIFIED_1ST"},
        {"team":"Australia","played":3,"won":1,"drawn":1,"lost":1,"gf":2,"ga":2,"gd":0,"pts":4,"status":"QUALIFIED_2ND"},
        {"team":"Paraguay","played":3,"won":1,"drawn":1,"lost":1,"gf":2,"ga":4,"gd":-2,"pts":4,"status":"QUALIFIED_3RD_BEST"},
        {"team":"Turkey","played":3,"won":1,"drawn":0,"lost":2,"gf":3,"ga":5,"gd":-2,"pts":3,"status":"ELIMINATED"},
    ],
    "E": [
        {"team":"Germany","played":3,"won":2,"drawn":0,"lost":1,"gf":10,"ga":4,"gd":6,"pts":6,"status":"QUALIFIED_1ST"},
        {"team":"Ivory Coast","played":3,"won":2,"drawn":0,"lost":1,"gf":4,"ga":3,"gd":1,"pts":6,"status":"QUALIFIED_2ND"},
        {"team":"Ecuador","played":3,"won":1,"drawn":1,"lost":1,"gf":2,"ga":2,"gd":0,"pts":4,"status":"QUALIFIED_3RD_BEST"},
        {"team":"Curaçao","played":3,"won":0,"drawn":1,"lost":2,"gf":1,"ga":10,"gd":-9,"pts":1,"status":"ELIMINATED"},
    ],
    "F": [
        {"team":"Netherlands","played":3,"won":2,"drawn":1,"lost":0,"gf":10,"ga":4,"gd":6,"pts":7,"status":"QUALIFIED_1ST"},
        {"team":"Sweden","played":3,"won":1,"drawn":1,"lost":1,"gf":7,"ga":7,"gd":0,"pts":4,"status":"QUALIFIED_2ND"},
        {"team":"Japan","played":3,"won":0,"drawn":2,"lost":1,"gf":3,"ga":4,"gd":-1,"pts":2,"status":"ELIMINATED"},
        {"team":"Tunisia","played":3,"won":0,"drawn":0,"lost":3,"gf":2,"ga":9,"gd":-7,"pts":0,"status":"ELIMINATED"},
    ],
    "G": [
        {"team":"Belgium","played":3,"won":2,"drawn":1,"lost":0,"gf":8,"ga":2,"gd":6,"pts":7,"status":"QUALIFIED_1ST"},
        {"team":"Egypt","played":3,"won":1,"drawn":2,"lost":0,"gf":4,"ga":3,"gd":1,"pts":5,"status":"QUALIFIED_2ND"},
        {"team":"Iran","played":3,"won":0,"drawn":2,"lost":1,"gf":3,"ga":4,"gd":-1,"pts":2,"status":"ELIMINATED"},
        {"team":"New Zealand","played":3,"won":0,"drawn":1,"lost":2,"gf":3,"ga":9,"gd":-6,"pts":1,"status":"ELIMINATED"},
    ],
    "H": [
        {"team":"Spain","played":3,"won":2,"drawn":1,"lost":0,"gf":3,"ga":0,"gd":3,"pts":7,"status":"QUALIFIED_1ST"},
        {"team":"Cabo Verde","played":3,"won":1,"drawn":2,"lost":0,"gf":1,"ga":0,"gd":1,"pts":5,"status":"QUALIFIED_2ND"},
        {"team":"Saudi Arabia","played":3,"won":0,"drawn":2,"lost":1,"gf":1,"ga":3,"gd":-2,"pts":2,"status":"ELIMINATED"},
        {"team":"Uruguay","played":3,"won":0,"drawn":1,"lost":2,"gf":1,"ga":3,"gd":-2,"pts":1,"status":"ELIMINATED"},
    ],
    "I": [
        {"team":"Norway","played":3,"won":3,"drawn":0,"lost":0,"gf":11,"ga":4,"gd":7,"pts":9,"status":"QUALIFIED_1ST"},
        {"team":"France","played":3,"won":2,"drawn":0,"lost":1,"gf":6,"ga":6,"gd":0,"pts":6,"status":"QUALIFIED_2ND"},
        {"team":"Senegal","played":3,"won":1,"drawn":0,"lost":2,"gf":8,"ga":6,"gd":2,"pts":3,"status":"QUALIFIED_3RD_BEST"},
        {"team":"Iraq","played":3,"won":0,"drawn":0,"lost":3,"gf":1,"ga":10,"gd":-9,"pts":0,"status":"ELIMINATED"},
    ],
    "J": [
        {"team":"Argentina","played":3,"won":3,"drawn":0,"lost":0,"gf":8,"ga":1,"gd":7,"pts":9,"status":"QUALIFIED_1ST"},
        {"team":"Austria","played":3,"won":1,"drawn":1,"lost":1,"gf":7,"ga":4,"gd":3,"pts":4,"status":"QUALIFIED_2ND"},
        {"team":"Algeria","played":3,"won":1,"drawn":1,"lost":1,"gf":4,"ga":6,"gd":-2,"pts":4,"status":"QUALIFIED_3RD_BEST"},
        {"team":"Jordan","played":3,"won":0,"drawn":0,"lost":3,"gf":2,"ga":10,"gd":-8,"pts":0,"status":"ELIMINATED"},
    ],
    "K": [
        {"team":"Colombia","played":3,"won":2,"drawn":1,"lost":0,"gf":5,"ga":1,"gd":4,"pts":7,"status":"QUALIFIED_1ST"},
        {"team":"Portugal","played":3,"won":1,"drawn":2,"lost":0,"gf":4,"ga":2,"gd":2,"pts":5,"status":"QUALIFIED_2ND"},
        {"team":"DR Congo","played":3,"won":1,"drawn":1,"lost":1,"gf":4,"ga":3,"gd":1,"pts":4,"status":"QUALIFIED_3RD_BEST"},
        {"team":"Uzbekistan","played":3,"won":0,"drawn":0,"lost":3,"gf":2,"ga":9,"gd":-7,"pts":0,"status":"ELIMINATED"},
    ],
    "L": [
        {"team":"England","played":3,"won":3,"drawn":0,"lost":0,"gf":8,"ga":2,"gd":6,"pts":9,"status":"QUALIFIED_1ST"},
        {"team":"Croatia","played":3,"won":2,"drawn":0,"lost":1,"gf":6,"ga":5,"gd":1,"pts":6,"status":"QUALIFIED_2ND"},
        {"team":"Ghana","played":3,"won":1,"drawn":0,"lost":2,"gf":2,"ga":4,"gd":-2,"pts":3,"status":"QUALIFIED_3RD_BEST"},
        {"team":"Panama","played":3,"won":0,"drawn":0,"lost":3,"gf":0,"ga":9,"gd":-9,"pts":0,"status":"ELIMINATED"},
    ],
}

# ── Round of 32 bracket ───────────────────────────────────────────────────────
ROUND_OF_32_BRACKET = [
    {"match_id":"WC2026_R32_01","date":"2026-06-28","home":"South Africa","away":"Canada","home_goals":0,"away_goals":1,"result":"A","status":"PLAYED","venue":"Rose Bowl","city":"Los Angeles"},
    {"match_id":"WC2026_R32_02","date":"2026-06-29","home":"Brazil","away":"Japan","home_goals":None,"away_goals":None,"result":None,"status":"TODAY","venue":"NRG Stadium","city":"Houston"},
    {"match_id":"WC2026_R32_03","date":"2026-06-29","home":"Germany","away":"Paraguay","home_goals":None,"away_goals":None,"result":None,"status":"TODAY","venue":"Gillette Stadium","city":"Boston"},
    {"match_id":"WC2026_R32_04","date":"2026-06-29","home":"Netherlands","away":"Morocco","home_goals":None,"away_goals":None,"result":None,"status":"TODAY","venue":"Estadio BBVA","city":"Monterrey"},
    {"match_id":"WC2026_R32_05","date":"2026-06-29","home":"Ivory Coast","away":"Norway","home_goals":None,"away_goals":None,"result":None,"status":"TODAY","venue":"Mercedes-Benz Stadium","city":"Atlanta"},
    {"match_id":"WC2026_R32_06","date":"2026-06-29","home":"France","away":"Sweden","home_goals":None,"away_goals":None,"result":None,"status":"TODAY","venue":"AT&T Stadium","city":"Dallas"},
    {"match_id":"WC2026_R32_07","date":"2026-06-30","home":"Mexico","away":"Ecuador","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"Estadio Azteca","city":"Mexico City"},
    {"match_id":"WC2026_R32_08","date":"2026-06-30","home":"England","away":"DR Congo","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"AT&T Stadium","city":"Dallas"},
    {"match_id":"WC2026_R32_09","date":"2026-07-01","home":"Belgium","away":"Senegal","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"NRG Stadium","city":"Houston"},
    {"match_id":"WC2026_R32_10","date":"2026-07-01","home":"USA","away":"Bosnia-Herzegovina","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"SoFi Stadium","city":"Los Angeles"},
    {"match_id":"WC2026_R32_11","date":"2026-07-02","home":"Spain","away":"Austria","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"Hard Rock Stadium","city":"Miami"},
    {"match_id":"WC2026_R32_12","date":"2026-07-02","home":"Portugal","away":"Croatia","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"Empower Field","city":"Denver"},
    {"match_id":"WC2026_R32_13","date":"2026-07-02","home":"Switzerland","away":"Algeria","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"Levi's Stadium","city":"Santa Clara"},
    {"match_id":"WC2026_R32_14","date":"2026-07-03","home":"Colombia","away":"Ghana","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"Estadio Akron","city":"Guadalajara"},
    {"match_id":"WC2026_R32_15","date":"2026-07-03","home":"Australia","away":"Egypt","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"BMO Field","city":"Toronto"},
    {"match_id":"WC2026_R32_16","date":"2026-07-03","home":"Argentina","away":"Cabo Verde","home_goals":None,"away_goals":None,"result":None,"status":"UPCOMING","venue":"Allegiant Stadium","city":"Las Vegas"},
]

# ── Top scorers after group stage ─────────────────────────────────────────────
TOP_SCORERS = [
    {"rank":1,"player":"Lionel Messi","team":"Argentina","goals":6,"assists":2,"notes":"Leading Golden Boot race. 2x goals vs Algeria (hat trick total), 1 vs Austria (MD2), 2 vs Jordan (MD3). Historic all-time WC scorer."},
    {"rank":2,"player":"Erling Haaland","team":"Norway","goals":6,"assists":1,"notes":"Tied Messi at 6 goals. 2 vs Iraq (MD1), 2 vs Senegal (MD2), 2 vs France (MD3). Norway sensationally top Group I."},
    {"rank":3,"player":"Kylian Mbappé","team":"France","goals":4,"assists":1,"notes":"4 goals incl. 1 vs Senegal, 1 vs Iraq (MD2), 1 vs Norway. Star performer despite France's MD3 loss."},
    {"rank":4,"player":"Ousmane Dembélé","team":"France","goals":4,"assists":2,"notes":"4 goals, brilliant tournament. Key for France despite MD3 defeat."},
    {"rank":5,"player":"Vinicius Jr.","team":"Brazil","goals":4,"assists":2,"notes":"3 group stage goals + key assists. Silky performances. Brazil's main threat."},
    {"rank":6,"player":"Ismaila Sarr","team":"Senegal","goals":4,"assists":1,"notes":"4 goals incl. brace vs Iraq in MD3. One of the tournament's surprise stars."},
    {"rank":7,"player":"Harry Kane","team":"England","goals":3,"assists":1,"notes":"3 goals, all vs different opponents. England's clinical leader."},
    {"rank":8,"player":"Johan Manzambi","team":"DR Congo","goals":3,"assists":0,"notes":"Surprise star. 3 goals, brace vs Uzbekistan in MD3. Dark horse Golden Boot contender."},
    {"rank":9,"player":"Deniz Undav","team":"Germany","goals":3,"assists":0,"notes":"3 goals off the bench. Impact sub who saved Germany in MD2. Momentum dipped after MD3 loss."},
    {"rank":10,"player":"Cody Gakpo","team":"Netherlands","goals":3,"assists":1,"notes":"3 goals, consistent throughout. Netherlands looking strong."},
    {"rank":11,"player":"Matheus Cunha","team":"Brazil","goals":3,"assists":1,"notes":"3 goals in 3 games. Excellent tournament from the Wolves striker."},
    {"rank":12,"player":"Brian Brobbey","team":"Netherlands","goals":3,"assists":0,"notes":"Impact sub scorer. 2 goals off bench."},
    {"rank":13,"player":"Riyad Mahrez","team":"Algeria","goals":2,"assists":0,"notes":"2 goals including brace in wild 3-3 draw with Austria. Algeria's bright spot."},
    {"rank":14,"player":"Ismael Saibari","team":"Morocco","goals":2,"assists":1,"notes":"2 goals, memorable chip vs Brazil in MD1. Morocco dark horse."},
    {"rank":15,"player":"Folarin Balogun","team":"USA","goals":3,"assists":0,"notes":"3 goals in group stage. USMNT hero despite MD3 loss to Turkey."},
]


def update_results_json():
    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_ids = {r.get("match_id") for r in data.get("results", [])}

    added = 0
    for r in NEW_RESULTS:
        if r["match_id"] not in existing_ids:
            data["results"].append(r)
            added += 1

    # Update meta
    data["_meta"]["last_updated"] = "2026-06-29"
    data["_meta"]["matches_played"] = len(data["results"])
    data["_meta"]["matchday_status"] = {
        "1": "COMPLETE",
        "2": "COMPLETE",
        "3": "COMPLETE",
        "round_of_32": f"IN PROGRESS (1/16 played, 5 today June 29, 10 upcoming)"
    }

    # Add ELO updates needed
    existing_elo_keys = {
        (u.get("home"), u.get("away")) for u in data.get("elo_updates_needed", [])
    }
    for u in NEW_ELO_UPDATES:
        key = (u["home"], u["away"])
        if key not in existing_elo_keys:
            data["elo_updates_needed"].append({"applied": False, **u})

    # Update standings
    data["standings"] = FINAL_STANDINGS

    # Add Round of 32 bracket
    data["round_of_32"] = ROUND_OF_32_BRACKET

    # Add top scorers
    data["top_scorers"] = TOP_SCORERS

    # Tournament insights
    data["tournament_insights"] = {
        "major_upsets": [
            "Spain 0-0 Cabo Verde (MD1) — holders held by minnows",
            "Ecuador 2-1 Germany (MD3) — historic result",
            "Norway 4-1 France (MD3) — France humbled; Haaland masterclass",
            "Turkey 3-2 USA (MD3) — late drama",
            "South Africa beat South Korea; Cabo Verde beat Uruguay",
            "Canada 1-0 South Africa (R32 90+5') — Eustaquio late winner",
        ],
        "golden_boot_leader": "Messi (6 goals) / Haaland (6 goals) — tied",
        "avg_goals_per_match_group_stage": 2.83,
        "total_goals_group_stage": 203,
        "total_matches_group_stage": 72,
        "qualified_for_r32": [
            "Mexico","South Africa","Switzerland","Canada","Bosnia-Herzegovina",
            "Brazil","Morocco","USA","Australia","Paraguay","Germany","Ivory Coast","Ecuador",
            "Netherlands","Sweden","Belgium","Egypt","Spain","Cabo Verde","Norway","France","Senegal",
            "Argentina","Austria","Algeria","Colombia","Portugal","DR Congo","England","Croatia","Ghana","Argentina"
        ],
        "eliminated_after_groups": [
            "Czech Republic","South Korea","Qatar","Bosnia? (no, qualified)","Scotland","Haiti",
            "Turkey","Curaçao","Japan","Tunisia","Iran","New Zealand","Saudi Arabia","Uruguay",
            "Iraq","Jordan","Uzbekistan","Panama"
        ],
        "storylines": [
            "Haaland unstoppable — 6 goals in 3 games; Norway top Group I",
            "Messi chasing immortality — 6 goals equals Haaland; Argentina unbeaten",
            "Germany upset by Ecuador despite 9-goal haul earlier",
            "Spain unbeaten but conservative; Cabo Verde the fairy tale story of the group stage",
            "Brazil solid but not spectacular; Vinicius electric when he turns it on",
            "France stumble vs Norway but still second in Group I with Mbappe threats",
        ]
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Added {added} new results. Total results: {len(data['results'])}")
    return data


def apply_all_elo_updates():
    """Apply all pending ELO updates including new R32 stage updates."""
    try:
        from models.elo_model import load_elo_ratings, save_elo_ratings, update_elo
        with open(RESULTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        pending = [u for u in data.get("elo_updates_needed", []) if not u.get("applied", False)]
        if not pending:
            print("[OK] No pending ELO updates.")
            return 0

        ratings = load_elo_ratings()
        applied = 0
        for upd in pending:
            home = upd.get("home", "")
            away = upd.get("away", "")
            hg = upd.get("hg", 0)
            ag = upd.get("ag", 0)
            stage = upd.get("stage", "group_stage")
            if home and away:
                ratings = update_elo(ratings, home, away, hg, ag, stage=stage, is_neutral=True)
                upd["applied"] = True
                applied += 1

        save_elo_ratings(ratings)

        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[OK] Applied {applied} ELO updates.")

        # Print new top ELOs
        top = sorted(ratings.items(), key=lambda x: x[1], reverse=True)[:15]
        print("\nTop 15 ELO ratings after all group matches + R32 result:")
        for rank, (team, elo) in enumerate(top, 1):
            print(f"  {rank:2d}. {team:<22} {elo:.0f}")
        return applied

    except Exception as e:
        print(f"[ERROR] ELO update failed: {e}")
        import traceback; traceback.print_exc()
        return 0


if __name__ == "__main__":
    print("=" * 60)
    print("FIFA 2026 Tournament Data Updater — June 29, 2026")
    print("=" * 60)
    update_results_json()
    apply_all_elo_updates()
    print("\n[DONE] Data update complete.")
