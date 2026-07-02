// =============================================
// HEXDRIFT — Football Predictions Engine
// =============================================

const TEAMS = {
  // South America
  ARG: { name: 'Argentina',    flag: '🇦🇷', color: '#74ACDF', alt: '#FFFFFF' },
  BRA: { name: 'Brazil',       flag: '🇧🇷', color: '#009C3B', alt: '#FEDD00' },
  URU: { name: 'Uruguay',      flag: '🇺🇾', color: '#5EB6E4', alt: '#FFFFFF' },
  COL: { name: 'Colombia',     flag: '🇨🇴', color: '#FCD116', alt: '#003087' },
  ECU: { name: 'Ecuador',      flag: '🇪🇨', color: '#FFD100', alt: '#003893' },
  PAR: { name: 'Paraguay',     flag: '🇵🇾', color: '#D52B1E', alt: '#FFFFFF' },
  // Europe
  FRA: { name: 'France',       flag: '🇫🇷', color: '#002395', alt: '#ED2939' },
  GER: { name: 'Germany',      flag: '🇩🇪', color: '#000000', alt: '#DD0000' },
  ESP: { name: 'Spain',        flag: '🇪🇸', color: '#AA151B', alt: '#F1BF00' },
  POR: { name: 'Portugal',     flag: '🇵🇹', color: '#006600', alt: '#FF0000' },
  ENG: { name: 'England',      flag: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', color: '#CF091F', alt: '#FFFFFF' },
  NED: { name: 'Netherlands',  flag: '🇳🇱', color: '#FF6600', alt: '#FFFFFF' },
  BEL: { name: 'Belgium',      flag: '🇧🇪', color: '#000000', alt: '#EF3340' },
  CRO: { name: 'Croatia',      flag: '🇭🇷', color: '#FF0000', alt: '#FFFFFF' },
  NOR: { name: 'Norway',       flag: '🇳🇴', color: '#EF2B2D', alt: '#002868' },
  SWE: { name: 'Sweden',       flag: '🇸🇪', color: '#006AA7', alt: '#FECC02' },
  SUI: { name: 'Switzerland',  flag: '🇨🇭', color: '#FF0000', alt: '#FFFFFF' },
  AUT: { name: 'Austria',      flag: '🇦🇹', color: '#ED2939', alt: '#FFFFFF' },
  SCO: { name: 'Scotland',     flag: '🏴󠁧󠁢󠁳󠁣󠁴󠁿', color: '#003399', alt: '#FFFFFF' },
  POL: { name: 'Poland',       flag: '🇵🇱', color: '#DC143C', alt: '#FFFFFF' },
  CZE: { name: 'Czechia',      flag: '🇨🇿', color: '#D7141A', alt: '#FFFFFF' },
  BIH: { name: 'Bosnia',       flag: '🇧🇦', color: '#002395', alt: '#FECB00' },
  ITA: { name: 'Italy',        flag: '🇮🇹', color: '#003399', alt: '#FFFFFF' },
  // CONCACAF
  USA: { name: 'USA',          flag: '🇺🇸', color: '#B22234', alt: '#3C3B6E' },
  MEX: { name: 'Mexico',       flag: '🇲🇽', color: '#006847', alt: '#CE1126' },
  CAN: { name: 'Canada',       flag: '🇨🇦', color: '#FF0000', alt: '#FFFFFF' },
  PAN: { name: 'Panama',       flag: '🇵🇦', color: '#DA121A', alt: '#1F3B7D' },
  QAT: { name: 'Qatar',        flag: '🇶🇦', color: '#8D1B3D', alt: '#FFFFFF' },
  // Africa
  MAR: { name: 'Morocco',      flag: '🇲🇦', color: '#C1272D', alt: '#006233' },
  SEN: { name: 'Senegal',      flag: '🇸🇳', color: '#00853F', alt: '#FDEF42' },
  RSA: { name: 'S.Africa',     flag: '🇿🇦', color: '#007A4D', alt: '#FFB612' },
  GHA: { name: 'Ghana',        flag: '🇬🇭', color: '#EF3340', alt: '#FCD116' },
  EGY: { name: 'Egypt',        flag: '🇪🇬', color: '#CE1126', alt: '#C8A951' },
  COD: { name: 'DR Congo',     flag: '🇨🇩', color: '#007FFF', alt: '#F7D618' },
  CIV: { name: "C. d'Ivoire",  flag: '🇨🇮', color: '#F77F00', alt: '#009A44' },
  ALG: { name: 'Algeria',      flag: '🇩🇿', color: '#006233', alt: '#FFFFFF' },
  CPV: { name: 'Cabo Verde',   flag: '🇨🇻', color: '#003893', alt: '#CF2027' },
  HAI: { name: 'Haiti',        flag: '🇭🇹', color: '#00209F', alt: '#D21034' },
  // Asia / Oceania
  JPN: { name: 'Japan',        flag: '🇯🇵', color: '#BC002D', alt: '#FFFFFF' },
  KOR: { name: 'S. Korea',     flag: '🇰🇷', color: '#003478', alt: '#CD2E3A' },
  AUS: { name: 'Australia',    flag: '🇦🇺', color: '#00843D', alt: '#FFCD00' },
  IRN: { name: 'Iran',         flag: '🇮🇷', color: '#239F40', alt: '#DA0000' },
  KSA: { name: 'Saudi Arabia', flag: '🇸🇦', color: '#006C35', alt: '#FFFFFF' },
  JOR: { name: 'Jordan',       flag: '🇯🇴', color: '#007A3D', alt: '#FFFFFF' },
  IRQ: { name: 'Iraq',         flag: '🇮🇶', color: '#CE1126', alt: '#007A3D' },
  UZB: { name: 'Uzbekistan',   flag: '🇺🇿', color: '#1EB53A', alt: '#FFFFFF' },
  NZL: { name: 'New Zealand',  flag: '🇳🇿', color: '#00247D', alt: '#CC142B' },
  TUN: { name: 'Tunisia',      flag: '🇹🇳', color: '#E70013', alt: '#FFFFFF' },
  CUR: { name: 'Curaçao',      flag: '🇨🇼', color: '#002B7F', alt: '#F9E300' },
  TUR: { name: 'Turkey',       flag: '🇹🇷', color: '#E30A17', alt: '#FFFFFF' },
};

const PREDICTIONS = [
  // ── GROUP STAGE (real completed matches) ────────────────────────────────────
  {
    id: 1, date: '2026-06-11',
    home: 'MEX', away: 'RSA',
    predictedScore: { h: 2, a: 0 }, actualScore: { h: 2, a: 0 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group A',
    venue: 'Estadio Azteca, Mexico City', confidence: 74,
    analysis: "Mexico with home altitude advantage at the Azteca. Lozano and Jimenez too much for South Africa. Called it perfectly — Jimenez late goal sealed it."
  },
  {
    id: 2, date: '2026-06-12',
    home: 'USA', away: 'PAR',
    predictedScore: { h: 2, a: 1 }, actualScore: { h: 4, a: 1 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group D',
    venue: 'MetLife Stadium, New York/NJ', confidence: 66,
    analysis: "USA on home soil in front of 82k fans. Called the winner right but massively underestimated Pulisic's impact — he ran Paraguay ragged all night."
  },
  {
    id: 3, date: '2026-06-14',
    home: 'GER', away: 'CUR',
    predictedScore: { h: 4, a: 0 }, actualScore: { h: 7, a: 1 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group E',
    venue: 'AT&T Stadium, Dallas', confidence: 89,
    analysis: "Germany's statement game of the tournament. Predicted a big win but nobody saw 7-1 coming. Musiala, Wirtz and Havertz in unstoppable form."
  },
  {
    id: 4, date: '2026-06-15',
    home: 'ESP', away: 'CPV',
    predictedScore: { h: 2, a: 0 }, actualScore: { h: 0, a: 0 },
    status: 'completed', correct: false,
    league: 'FIFA World Cup 2026', round: 'Group H',
    venue: 'Rose Bowl, Los Angeles', confidence: 83,
    analysis: "Got this badly wrong. Cabo Verde's deep 5-4-1 block frustrated Spain completely — Yamal and Williams couldn't find space. One of the tournament's biggest early shocks."
  },
  {
    id: 5, date: '2026-06-16',
    home: 'ARG', away: 'ALG',
    predictedScore: { h: 2, a: 0 }, actualScore: { h: 3, a: 0 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group J',
    venue: 'SoFi Stadium, Los Angeles', confidence: 88,
    analysis: "Argentina dominant from the first whistle. Messi with two goals and an assist — still the best player on the planet. Score was even better than predicted."
  },
  {
    id: 6, date: '2026-06-17',
    home: 'ENG', away: 'CRO',
    predictedScore: { h: 2, a: 1 }, actualScore: { h: 4, a: 2 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group L',
    venue: 'Hard Rock Stadium, Miami', confidence: 75,
    analysis: "England's forward line clicked into gear immediately. Bellingham's first-half header set the tone. Croatia's Modrić scored a beauty but couldn't drag them back into it."
  },
  {
    id: 7, date: '2026-06-17',
    home: 'COL', away: 'UZB',
    predictedScore: { h: 2, a: 1 }, actualScore: { h: 3, a: 1 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group K',
    venue: 'State Farm Stadium, Phoenix', confidence: 72,
    analysis: "Colombia's flair was too much for the physically strong Uzbeks. James Rodríguez ran the show in the opening 60 minutes before being rested."
  },
  {
    id: 8, date: '2026-06-19',
    home: 'BRA', away: 'HAI',
    predictedScore: { h: 3, a: 0 }, actualScore: { h: 3, a: 0 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group C',
    venue: 'Gillette Stadium, Boston', confidence: 92,
    analysis: "Perfect prediction. Vinicius Jr. opened the scoring, Rodrygo added a brace. Haiti were spirited but Brazil's class was in a different league entirely."
  },
  {
    id: 9, date: '2026-06-20',
    home: 'GER', away: 'CIV',
    predictedScore: { h: 2, a: 1 }, actualScore: { h: 2, a: 1 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group E',
    venue: 'NRG Stadium, Houston', confidence: 65,
    analysis: "Nailed the exact score! Germany trailed at half-time but Wirtz equalised and Musiala's 89th-minute winner showed Germany's mental strength."
  },
  {
    id: 10, date: '2026-06-20',
    home: 'NED', away: 'SWE',
    predictedScore: { h: 3, a: 1 }, actualScore: { h: 5, a: 1 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group F',
    venue: 'Allegiant Stadium, Las Vegas', confidence: 78,
    analysis: "Netherlands in scintillating form. Called the winner easily but 5-1 was emphatic — Gakpo ran Sweden's defence ragged and van Persie's spirit lives on in this Dutch team."
  },
  {
    id: 11, date: '2026-06-26',
    home: 'BEL', away: 'NZL',
    predictedScore: { h: 3, a: 0 }, actualScore: { h: 5, a: 1 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Group G',
    venue: 'Empower Field, Denver', confidence: 86,
    analysis: "Belgium's golden generation still has plenty left. De Bruyne pulled the strings brilliantly. New Zealand's Weir goal was a consolation in a one-sided contest."
  },
  {
    id: 12, date: '2026-06-26',
    home: 'NOR', away: 'FRA',
    predictedScore: { h: 1, a: 3 }, actualScore: { h: 4, a: 1 },
    status: 'completed', correct: false,
    league: 'FIFA World Cup 2026', round: 'Group I',
    venue: 'NRG Stadium, Houston', confidence: 61,
    analysis: "Biggest miss of the tournament so far. Haaland was absolutely unstoppable — hat-trick inside 71 minutes. Norway tore France's high line apart on the counter. Nobody saw this coming."
  },
  {
    id: 13, date: '2026-06-25',
    home: 'ECU', away: 'GER',
    predictedScore: { h: 1, a: 2 }, actualScore: { h: 2, a: 1 },
    status: 'completed', correct: false,
    league: 'FIFA World Cup 2026', round: 'Group E',
    venue: 'Lincoln Financial Field, Philadelphia', confidence: 58,
    analysis: "Ecuador's physicality and quick transitions proved too much for a tired Germany side. Estupiñán's brace early on was clinical — Germany pushed late but couldn't get the equaliser."
  },
  // ── ROUND OF 32 ──
  {
    id: 14, date: '2026-06-29',
    home: 'RSA', away: 'CAN',
    predictedScore: { h: 0, a: 1 }, actualScore: { h: 0, a: 1 },
    status: 'completed', correct: true,
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'AT&T Stadium, Dallas', confidence: 62, time: 'FT',
    analysis: "Canada have been impressive all tournament. South Africa spirited but lack the depth for this stage. Alphonso Davies and Jonathan David should prove too much."
  },
  {
    id: 15, date: '2026-06-30',
    home: 'BRA', away: 'JPN',
    predictedScore: { h: 3, a: 1 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'SoFi Stadium, Los Angeles', confidence: 85, time: '7:00 AM',
    analysis: "Brazil are in devastating form. Japan will be organised and defensive but Brazil's attacking firepower is simply too much. Vinicius Jr. and Rodrygo to run riot."
  },
  {
    id: 16, date: '2026-06-30',
    home: 'GER', away: 'PAR',
    predictedScore: { h: 2, a: 0 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'Empower Field, Denver', confidence: 72, time: '10:30 AM',
    analysis: "Germany's youthful squad powered by Musiala and Wirtz should overpower Paraguay. German pressing game will suffocate Paraguay's counter-attacking threat."
  },
  {
    id: 17, date: '2026-06-30',
    home: 'NED', away: 'MAR',
    predictedScore: { h: 2, a: 1 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'Rose Bowl, Los Angeles', confidence: 68, time: '3:00 PM',
    analysis: "Morocco will make this incredibly tough. Their defensive organisation is elite. Netherlands' quality in attack should eventually prove decisive but expect a nervy win."
  },
  {
    id: 18, date: '2026-06-30',
    home: 'CIV', away: 'NOR',
    predictedScore: { h: 1, a: 2 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'Levi\'s Stadium, San Francisco', confidence: 55, time: '7:00 AM',
    analysis: "Norway are flying with Haaland in incredible form. Côte d'Ivoire have heart but Norway's physical and technical quality makes them slight favourites here."
  },
  {
    id: 19, date: '2026-06-30',
    home: 'FRA', away: 'SWE',
    predictedScore: { h: 3, a: 0 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'Hard Rock Stadium, Miami', confidence: 88, time: '11:00 AM',
    analysis: "France are one of the tournament favourites. Sweden are a well-drilled side but France's individual quality — Mbappé, Griezmann, Camavinga — is on another level."
  },
  {
    id: 20, date: '2026-06-30',
    home: 'MEX', away: 'ECU',
    predictedScore: { h: 2, a: 1 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'Estadio Azteca, Mexico City', confidence: 63, time: '3:00 PM',
    analysis: "Mexico at altitude in the Azteca is a genuine home game advantage. Ecuador will be dangerous on the counter but Mexico's experience in this environment should prove crucial."
  },
  {
    id: 21, date: '2026-07-01',
    home: 'ENG', away: 'COD',
    predictedScore: { h: 3, a: 0 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'MetLife Stadium, New York', confidence: 78, time: '6:00 AM',
    analysis: "England should win comfortably. DR Congo's physical style could cause problems early on but England's quality in the final third should shine through. Bellingham in form."
  },
  {
    id: 22, date: '2026-07-01',
    home: 'BEL', away: 'SEN',
    predictedScore: { h: 2, a: 1 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'Allegiant Stadium, Las Vegas', confidence: 66, time: '10:00 AM',
    analysis: "Belgium vs Senegal is a genuinely difficult call. Belgium's golden generation may be fading but De Bruyne's class can still unlock Senegal's solid defence."
  },
  {
    id: 23, date: '2026-07-01',
    home: 'USA', away: 'BIH',
    predictedScore: { h: 2, a: 1 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'NRG Stadium, Houston', confidence: 61, time: '2:00 PM',
    analysis: "USA on home soil with 100,000 fans behind them. Bosnia will be competitive but the atmosphere and America's pace in attack should carry them through."
  },
  {
    id: 24, date: '2026-07-02',
    home: 'ESP', away: 'AUT',
    predictedScore: { h: 3, a: 0 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'AT&T Stadium, Dallas', confidence: 86, time: '9:00 AM',
    analysis: "Spain are perhaps the best team in the tournament. Austria are competent but Spain's tiki-taka possession game and Yamal/Williams/Pedri will be too much to handle."
  },
  {
    id: 25, date: '2026-07-02',
    home: 'POR', away: 'CRO',
    predictedScore: { h: 2, a: 1 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'Gillette Stadium, Boston', confidence: 70, time: '1:00 PM',
    analysis: "Portugal vs Croatia is a genuine 50-50. Croatia are experienced and composed. Portugal's individual quality — Ronaldo still dangerous — gives them the edge."
  },
  {
    id: 26, date: '2026-07-02',
    home: 'SUI', away: 'ALG',
    predictedScore: { h: 1, a: 1 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'State Farm Stadium, Phoenix', confidence: 50, time: '5:00 PM',
    analysis: "Algeria have been one of the tournament's surprises. Switzerland are solid and hard to beat. Predict this goes to extra time with a penalty shootout deciding it."
  },
  {
    id: 27, date: '2026-07-03',
    home: 'AUS', away: 'EGY',
    predictedScore: { h: 2, a: 0 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'Arrowhead Stadium, Kansas City', confidence: 67, time: '8:00 AM',
    analysis: "Australia's physical and organised style should overcome Egypt. The Socceroos love a knock-out game. Expect a solid defensive display and clinical finishing from the Australians."
  },
  {
    id: 28, date: '2026-07-03',
    home: 'ARG', away: 'CPV',
    predictedScore: { h: 5, a: 0 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'SoFi Stadium, Los Angeles', confidence: 96, time: '12:00 PM',
    analysis: "Cabo Verde are a massive fairytale story to be here but this is where Argentina end the dream. Messi and co. will be relentless. Expect a big scoreline from the champions."
  },
  {
    id: 29, date: '2026-07-03',
    home: 'COL', away: 'GHA',
    predictedScore: { h: 2, a: 1 }, actualScore: null,
    status: 'upcoming',
    league: 'FIFA World Cup 2026', round: 'Round of 32',
    venue: 'Hard Rock Stadium, Miami', confidence: 60, time: '3:30 PM',
    analysis: "Colombia's flair and James Rodriguez's creativity should be the difference. Ghana are dangerous on the counter with their pace up front but Colombia's quality edges it."
  }
];

// Real Group Stage standings — verified from fifa_2026_results.json
const GROUPS = [
  { id: 'A', teams: [
    { code: 'MEX', p: 3, w: 3, d: 0, l: 0, gf: 6, ga: 0, pts: 9 },
    { code: 'RSA', p: 3, w: 1, d: 1, l: 1, gf: 2, ga: 3, pts: 4 },
    { code: 'KOR', p: 3, w: 1, d: 0, l: 2, gf: 2, ga: 3, pts: 3 },
    { code: 'CZE', p: 3, w: 0, d: 1, l: 2, gf: 2, ga: 6, pts: 1 },
  ]},
  { id: 'B', teams: [
    { code: 'SUI', p: 3, w: 2, d: 1, l: 0, gf: 8, ga: 3, pts: 7 },
    { code: 'CAN', p: 3, w: 1, d: 1, l: 1, gf: 8, ga: 4, pts: 4 },
    { code: 'BIH', p: 3, w: 1, d: 1, l: 1, gf: 5, ga: 6, pts: 4 },
    { code: 'QAT', p: 3, w: 0, d: 1, l: 2, gf: 2, ga: 10, pts: 1 },
  ]},
  { id: 'C', teams: [
    { code: 'BRA', p: 3, w: 2, d: 1, l: 0, gf: 7, ga: 1, pts: 7 },
    { code: 'MAR', p: 3, w: 2, d: 1, l: 0, gf: 4, ga: 1, pts: 7 },
    { code: 'SCO', p: 3, w: 1, d: 0, l: 2, gf: 1, ga: 4, pts: 3 },
    { code: 'HAI', p: 3, w: 0, d: 0, l: 3, gf: 0, ga: 6, pts: 0 },
  ]},
  { id: 'D', teams: [
    { code: 'USA', p: 3, w: 2, d: 0, l: 1, gf: 8, ga: 4, pts: 6 },
    { code: 'AUS', p: 3, w: 1, d: 1, l: 1, gf: 2, ga: 2, pts: 4 },
    { code: 'PAR', p: 3, w: 1, d: 1, l: 1, gf: 2, ga: 4, pts: 4 },
    { code: 'TUR', p: 3, w: 1, d: 0, l: 2, gf: 3, ga: 5, pts: 3 },
  ]},
  { id: 'E', teams: [
    { code: 'GER', p: 3, w: 2, d: 0, l: 1, gf: 10, ga: 4, pts: 6 },
    { code: 'CIV', p: 3, w: 2, d: 0, l: 1, gf: 4,  ga: 2, pts: 6 },
    { code: 'ECU', p: 3, w: 1, d: 1, l: 1, gf: 2,  ga: 2, pts: 4 },
    { code: 'CUR', p: 3, w: 0, d: 1, l: 2, gf: 1,  ga: 9, pts: 1 },
  ]},
  { id: 'F', teams: [
    { code: 'NED', p: 3, w: 2, d: 1, l: 0, gf: 10, ga: 4, pts: 7 },
    { code: 'JPN', p: 3, w: 1, d: 2, l: 0, gf: 5,  ga: 3, pts: 5 },
    { code: 'SWE', p: 3, w: 1, d: 1, l: 1, gf: 7,  ga: 7, pts: 4 },
    { code: 'TUN', p: 3, w: 0, d: 0, l: 3, gf: 2,  ga: 10, pts: 0 },
  ]},
  { id: 'G', teams: [
    { code: 'BEL', p: 3, w: 2, d: 1, l: 0, gf: 8, ga: 2, pts: 7 },
    { code: 'EGY', p: 3, w: 1, d: 2, l: 0, gf: 4, ga: 3, pts: 5 },
    { code: 'IRN', p: 3, w: 0, d: 2, l: 1, gf: 3, ga: 4, pts: 2 },
    { code: 'NZL', p: 3, w: 0, d: 1, l: 2, gf: 4, ga: 9, pts: 1 },
  ]},
  { id: 'H', teams: [
    { code: 'ESP', p: 3, w: 2, d: 1, l: 0, gf: 3, ga: 0, pts: 7 },
    { code: 'CPV', p: 3, w: 1, d: 2, l: 0, gf: 1, ga: 0, pts: 5 },
    { code: 'KSA', p: 3, w: 0, d: 2, l: 1, gf: 1, ga: 3, pts: 2 },
    { code: 'URU', p: 3, w: 0, d: 1, l: 2, gf: 1, ga: 4, pts: 1 },
  ]},
  { id: 'I', teams: [
    { code: 'NOR', p: 3, w: 3, d: 0, l: 0, gf: 11, ga: 4, pts: 9 },
    { code: 'FRA', p: 3, w: 2, d: 0, l: 1, gf: 6,  ga: 5, pts: 6 },
    { code: 'SEN', p: 3, w: 1, d: 0, l: 2, gf: 8,  ga: 6, pts: 3 },
    { code: 'IRQ', p: 3, w: 0, d: 0, l: 3, gf: 1,  ga: 11, pts: 0 },
  ]},
  { id: 'J', teams: [
    { code: 'ARG', p: 3, w: 3, d: 0, l: 0, gf: 8, ga: 1, pts: 9 },
    { code: 'AUT', p: 3, w: 1, d: 1, l: 1, gf: 6, ga: 6, pts: 4 },
    { code: 'ALG', p: 3, w: 1, d: 1, l: 1, gf: 4, ga: 6, pts: 4 },
    { code: 'JOR', p: 3, w: 0, d: 0, l: 3, gf: 2, ga: 7, pts: 0 },
  ]},
  { id: 'K', teams: [
    { code: 'COL', p: 3, w: 2, d: 1, l: 0, gf: 5, ga: 1, pts: 7 },
    { code: 'POR', p: 3, w: 1, d: 2, l: 0, gf: 4, ga: 1, pts: 5 },
    { code: 'COD', p: 3, w: 1, d: 1, l: 1, gf: 4, ga: 4, pts: 4 },
    { code: 'UZB', p: 3, w: 0, d: 0, l: 3, gf: 2, ga: 9, pts: 0 },
  ]},
  { id: 'L', teams: [
    { code: 'ENG', p: 3, w: 3, d: 0, l: 0, gf: 8, ga: 2, pts: 9 },
    { code: 'CRO', p: 3, w: 2, d: 0, l: 1, gf: 6, ga: 5, pts: 6 },
    { code: 'GHA', p: 3, w: 1, d: 0, l: 2, gf: 2, ga: 4, pts: 3 },
    { code: 'PAN', p: 3, w: 0, d: 0, l: 3, gf: 0, ga: 5, pts: 0 },
  ]},
];

const BRACKET = {
  r32: [
    // Jun 29
    { h: 'RSA', a: 'CAN', winner: 'CAN', score: '0-1', status: 'done', date: 'Jun 29' },
    // Jun 30
    { h: 'BRA', a: 'JPN', winner: null, score: null, status: 'upcoming', date: 'Jun 30', time: '7:00 AM' },
    { h: 'GER', a: 'PAR', winner: null, score: null, status: 'upcoming', date: 'Jun 30', time: '10:30 AM' },
    { h: 'NED', a: 'MAR', winner: null, score: null, status: 'upcoming', date: 'Jun 30', time: '3:00 PM' },
    { h: 'CIV', a: 'NOR', winner: null, score: null, status: 'upcoming', date: 'Jun 30', time: '7:00 AM' },
    { h: 'FRA', a: 'SWE', winner: null, score: null, status: 'upcoming', date: 'Jun 30', time: '11:00 AM' },
    { h: 'MEX', a: 'ECU', winner: null, score: null, status: 'upcoming', date: 'Jun 30', time: '3:00 PM' },
    // Jul 1
    { h: 'ENG', a: 'COD', winner: null, score: null, status: 'upcoming', date: 'Jul 1', time: '6:00 AM' },
    { h: 'BEL', a: 'SEN', winner: null, score: null, status: 'upcoming', date: 'Jul 1', time: '10:00 AM' },
    { h: 'USA', a: 'BIH', winner: null, score: null, status: 'upcoming', date: 'Jul 1', time: '2:00 PM' },
    // Jul 2
    { h: 'ESP', a: 'AUT', winner: null, score: null, status: 'upcoming', date: 'Jul 2', time: '9:00 AM' },
    { h: 'POR', a: 'CRO', winner: null, score: null, status: 'upcoming', date: 'Jul 2', time: '1:00 PM' },
    { h: 'SUI', a: 'ALG', winner: null, score: null, status: 'upcoming', date: 'Jul 2', time: '5:00 PM' },
    // Jul 3
    { h: 'AUS', a: 'EGY', winner: null, score: null, status: 'upcoming', date: 'Jul 3', time: '8:00 AM' },
    { h: 'ARG', a: 'CPV', winner: null, score: null, status: 'upcoming', date: 'Jul 3', time: '12:00 PM' },
    { h: 'COL', a: 'GHA', winner: null, score: null, status: 'upcoming', date: 'Jul 3', time: '3:30 PM' },
  ],
  r16: [
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 5–6' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 5–6' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 5–6' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 5–6' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 7–8' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 7–8' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 7–8' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 7–8' },
  ],
  qf: [
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 11–12' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 11–12' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 13–14' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 13–14' },
  ],
  sf: [
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 17' },
    { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 18' },
  ],
  final: { h: 'TBD', a: 'TBD', winner: null, score: null, status: 'upcoming', time: 'Jul 21' }
};

// Widget shows next upcoming match — BRA vs JPN (Jun 30, 7:00 AM)
const NEXT_MATCH = {
  match: { h: 'BRA', a: 'JPN', label: 'Jun 30 · 7:00 AM', league: 'FIFA WC 2026 — R32', venue: 'SoFi Stadium, Los Angeles' },
  events: [
    { min: '?', type: 'goal',   team: 'h', player: 'Vinicius Jr.',   desc: 'Predicted: Left-foot finish on the break' },
    { min: '?', type: 'goal',   team: 'h', player: 'Rodrygo',        desc: 'Predicted: Clinical finish from Vinicius assist' },
    { min: '?', type: 'yellow', team: 'a', player: 'Endo',           desc: 'Predicted: Tactical foul in midfield' },
    { min: '?', type: 'goal',   team: 'a', player: 'Mitoma',         desc: 'Predicted: Japan consolation — counter' },
    { min: '?', type: 'goal',   team: 'h', player: 'Endrick',        desc: 'Predicted: Late third, game sealed' },
  ],
  homeXI: [
    [{ n: 'Ederson', no: 1 }],
    [{ n: 'Danilo', no: 2 }, { n: 'Marquinhos', no: 5 }, { n: 'Gabriel Magalhães', no: 4 }, { n: 'Guilherme Arana', no: 6 }],
    [{ n: 'Casemiro', no: 5 }, { n: 'Bruno Guimarães', no: 8 }, { n: 'Lucas Paquetá', no: 10 }],
    [{ n: 'Rodrygo', no: 11 }, { n: 'Endrick', no: 9 }, { n: 'Vinicius Jr.', no: 7 }],
  ],
  awayXI: [
    [{ n: 'Gonda', no: 12 }],
    [{ n: 'Sugawara', no: 2 }, { n: 'Itakura', no: 4 }, { n: 'Yoshida', no: 22 }, { n: 'Machino', no: 3 }],
    [{ n: 'Endo', no: 6 }, { n: 'Kamada', no: 10 }, { n: 'Tanaka', no: 7 }],
    [{ n: 'Doan', no: 8 }, { n: 'Ueda', no: 9 }, { n: 'Mitoma', no: 11 }],
  ],
  commentary: [
    { min: 'PRE', text: "Brazil vs Japan — Round of 32 opener at SoFi Stadium, Los Angeles. Brazil are massive favourites." },
    { min: 'PRE', text: "VINICIUS JR WATCH: 5 goal contributions in group stage. Japan's defence will have their hands full." },
    { min: 'PRE', text: "JAPAN'S STRENGTH: Disciplined defensive block. They eliminated Germany in 2022. Never underestimate them." },
    { min: 'PRE', text: "KEY DUEL: Casemiro vs Kamada — Brazil need to control midfield to unleash their front three." },
    { min: 'PRE', text: "PREDICTION: Brazil win 3-1. Japan will score but Brazil's attacking depth is too much." },
    { min: 'PRE', text: "Head-to-head: Brazil lead 6-1-2 vs Japan in all-time meetings." },
    { min: 'PRE', text: "Dorival Júnior: 'Japan are a quality side. We must respect them but go out and express ourselves.'" },
    { min: 'PRE', text: "Hajime Moriyasu: 'We proved in 2022 we can beat South American giants. We believe we can do it again.'" },
  ]
};

// =====================
// STATE
// =====================
let currentPage = 'home';
let currentChartTab = 'bracket';
let widgetOpen = false;
let widgetTab = 'events';
let predFilter = 'all';
let userPredictions = JSON.parse(localStorage.getItem('hx_predictions') || '[]');

// =====================
// COMPUTED STATS
// =====================
function getStats() {
  const all = [...PREDICTIONS, ...userPredictions];
  const completed = all.filter(p => p.status === 'completed');
  const correct = completed.filter(p => p.correct);
  const streak = getStreak(completed);
  return {
    total: all.length,
    completed: completed.length,
    correct: correct.length,
    accuracy: completed.length ? Math.round((correct.length / completed.length) * 100) : 0,
    streak,
    upcoming: all.filter(p => p.status === 'upcoming').length,
    live: all.filter(p => p.status === 'live').length,
  };
}

function getStreak(completed) {
  let streak = 0;
  for (let i = completed.length - 1; i >= 0; i--) {
    if (completed[i].correct) streak++;
    else break;
  }
  return streak;
}

// =====================
// NAVIGATION
// =====================
function navigate(page) {
  currentPage = page;
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  document.querySelector(`[data-page="${page}"]`)?.classList.add('active');
  window.scrollTo(0, 0);
  if (page === 'charts') renderCharts();
  if (page === 'predictions') renderPredictions();
}

// =====================
// RENDER BANNER
// =====================
function renderBanner() {
  // Pull live first, then today's upcoming, then any future upcoming — max 3 total
  const all = [...PREDICTIONS, ...userPredictions];
  const today = new Date().toISOString().slice(0, 10);
  const live     = all.filter(p => p.status === 'live');
  const todayUp  = all.filter(p => p.status === 'upcoming' && p.date === today);
  const futureUp = all.filter(p => p.status === 'upcoming' && p.date > today);
  const pool = [...live, ...todayUp, ...futureUp].slice(0, 3);

  if (!pool.length) {
    document.getElementById('banner-inner').innerHTML = '<span style="color:#555;font-size:12px;letter-spacing:2px;text-transform:uppercase;">No upcoming matches scheduled</span>';
    return;
  }

  const html = pool.map(p => {
    const h = TEAMS[p.home] || { name: p.home, flag: '🏳' };
    const a = TEAMS[p.away] || { name: p.away, flag: '🏳' };
    const isLive = p.status === 'live';
    const scoreOrTime = isLive
      ? `<span class="live-badge">LIVE</span>`
      : `<span class="time-badge">${p.time || p.date.slice(5).replace('-', '/')}</span>`;
    return `
      <div class="banner-match ${isLive ? 'live' : 'upcoming'}">
        <div class="banner-teams">
          <span class="banner-team">${h.flag} ${h.name}</span>
          <span class="banner-score">${scoreOrTime}</span>
          <span class="banner-team">${a.flag} ${a.name}</span>
        </div>
      </div>`;
  }).join('<span class="banner-sep">·</span>');
  document.getElementById('banner-inner').innerHTML = html;
}

// =====================
// RENDER HOME
// =====================
function renderHome() {
  const stats = getStats();
  document.getElementById('stat-accuracy').textContent = stats.accuracy + '%';
  document.getElementById('stat-total').textContent = stats.total;
  document.getElementById('stat-streak').textContent = stats.streak;
  document.getElementById('stat-upcoming').textContent = stats.upcoming + stats.live;

  const recent = [...PREDICTIONS].reverse().slice(0, 5);
  const recentHtml = recent.map(p => {
    const h = TEAMS[p.home] || { name: p.home, flag: '🏳' };
    const a = TEAMS[p.away] || { name: p.away, flag: '🏳' };
    const badge = p.status === 'live'
      ? '<span class="badge badge-live">LIVE</span>'
      : p.status === 'upcoming'
        ? `<span class="badge badge-upcoming">${p.time || 'TBD'}</span>`
        : p.correct
          ? '<span class="badge badge-correct">✓</span>'
          : '<span class="badge badge-wrong">✗</span>';
    return `
      <div class="recent-card ${p.status}" onclick="navigate('predictions')">
        <div class="rc-header">
          <span class="rc-round">${p.round}</span>
          ${badge}
        </div>
        <div class="rc-teams">
          <span class="rc-team"><span class="rc-flag">${h.flag}</span>${h.name}</span>
          <div class="rc-score-block">
            <div class="rc-predicted">${p.predictedScore.h}–${p.predictedScore.a}</div>
            <div class="rc-label">Predicted</div>
            ${p.actualScore ? `<div class="rc-actual">${p.actualScore.h}–${p.actualScore.a}</div><div class="rc-label">Actual</div>` : ''}
          </div>
          <span class="rc-team"><span class="rc-flag">${a.flag}</span>${a.name}</span>
        </div>
        <div class="rc-conf">
          <div class="rc-conf-bar" style="width:${p.confidence}%"></div>
          <span>${p.confidence}% confidence</span>
        </div>
      </div>`;
  }).join('');
  document.getElementById('recent-list').innerHTML = recentHtml;

  // Accuracy ring + SVG text + season stat rows
  const pct = stats.accuracy;
  const ring = document.getElementById('acc-ring');
  if (ring) {
    const c = 2 * Math.PI * 54;
    ring.style.strokeDasharray = `${(pct / 100) * c} ${c}`;
  }
  const svgText = document.getElementById('acc-pct-text');
  if (svgText) svgText.textContent = pct + '%';
  const elComp = document.getElementById('acc-completed');
  if (elComp) elComp.textContent = stats.completed;
  const elCorr = document.getElementById('acc-correct');
  if (elCorr) elCorr.textContent = stats.correct;
  const elStr = document.getElementById('acc-streak');
  if (elStr) elStr.textContent = stats.streak + ' 🔥';
}

// =====================
// RENDER PREDICTIONS
// =====================
function renderPredictions() {
  const all = [...PREDICTIONS, ...userPredictions];
  let filtered = all;
  if (predFilter === 'upcoming') filtered = all.filter(p => p.status === 'upcoming' || p.status === 'live');
  if (predFilter === 'completed') filtered = all.filter(p => p.status === 'completed');
  if (predFilter === 'correct') filtered = all.filter(p => p.correct);
  if (predFilter === 'wrong') filtered = all.filter(p => p.status === 'completed' && !p.correct);

  const html = filtered.map(p => {
    const h = TEAMS[p.home] || { name: p.home, flag: '🏳' };
    const a = TEAMS[p.away] || { name: p.away, flag: '🏳' };
    let statusClass = p.status;
    if (p.status === 'completed') statusClass = p.correct ? 'correct' : 'wrong';
    return `
      <div class="pred-card ${statusClass}">
        <div class="pred-top">
          <span class="pred-round">${p.round} · ${p.league.replace('FIFA ', '')}</span>
          <span class="pred-date">${formatDate(p.date)}</span>
        </div>
        <div class="pred-match">
          <div class="pred-team home">
            <div class="pred-flag">${h.flag}</div>
            <div class="pred-name">${h.name}</div>
          </div>
          <div class="pred-center">
            <div class="pred-scores">
              <div class="pred-pscores">${p.predictedScore.h} — ${p.predictedScore.a}</div>
              <div class="pred-slabel">Prediction</div>
              ${p.actualScore
                ? `<div class="pred-ascores ${p.correct ? 'ac-correct' : 'ac-wrong'}">${p.actualScore.h} — ${p.actualScore.a}</div><div class="pred-slabel">Result</div>`
                : p.status === 'live'
                  ? `<div class="pred-live-score">LIVE</div>`
                  : `<div class="pred-upcoming-time">${p.time || 'TBD'}</div>`}
            </div>
            <div class="pred-venue">📍 ${p.venue}</div>
          </div>
          <div class="pred-team away">
            <div class="pred-flag">${a.flag}</div>
            <div class="pred-name">${a.name}</div>
          </div>
        </div>
        <div class="pred-analysis">${p.analysis}</div>
        <div class="pred-footer">
          <div class="pred-conf-bar-wrap">
            <div class="pred-conf-fill" style="width:${p.confidence}%"></div>
          </div>
          <span class="pred-conf-text">${p.confidence}% Confidence</span>
        </div>
      </div>`;
  }).join('');
  document.getElementById('pred-grid').innerHTML = html || '<p class="empty-msg">No predictions found.</p>';
}

function setPredFilter(f) {
  predFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.filter === f));
  renderPredictions();
}

// =====================
// RENDER CHARTS
// =====================
function renderCharts() {
  if (currentChartTab === 'groups') renderGroups();
  else renderBracket();
}

function setChartTab(tab) {
  currentChartTab = tab;
  document.querySelectorAll('.chart-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  document.getElementById('bracket-view').style.display = tab === 'bracket' ? 'block' : 'none';
  document.getElementById('groups-view').style.display = tab === 'groups' ? 'block' : 'none';
  renderCharts();
}

function renderGroups() {
  const html = GROUPS.map(g => {
    const rows = g.teams.map((t, i) => {
      const team = TEAMS[t.code] || { name: t.code, flag: '🏳' };
      const qualified = i < 2;
      return `<tr class="${qualified ? 'qualified' : ''}">
        <td>${i + 1}</td>
        <td class="team-cell"><span class="tbl-flag">${team.flag}</span> ${team.name}</td>
        <td>${t.p}</td><td>${t.w}</td><td>${t.d}</td><td>${t.l}</td>
        <td>${t.gf}</td><td>${t.ga}</td><td>${t.gf - t.ga > 0 ? '+' : ''}${t.gf - t.ga}</td>
        <td class="pts-cell"><strong>${t.pts}</strong></td>
      </tr>`;
    }).join('');
    return `
      <div class="group-table-card">
        <div class="group-header">Group ${g.id}</div>
        <table class="group-tbl">
          <thead><tr><th>#</th><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }).join('');
  document.getElementById('groups-view').innerHTML = '<div class="groups-grid">' + html + '</div>';
}

function renderBracketMatch(m) {
  const ht = TEAMS[m.h] || { name: m.h, flag: '⚽' };
  const at = TEAMS[m.a] || { name: m.a, flag: '⚽' };
  const isLive = m.status === 'live';
  const isDone = m.status === 'done' || m.status === 'completed';
  const dateLabel = m.date ? `<span class="bm-date">${m.date}</span>` : '';
  const timeLabel = m.time && !isLive && !isDone ? `<div class="bm-time">${m.time}</div>` : '';
  return `
  <div class="bracket-match ${isLive ? 'live' : ''} ${isDone ? 'done' : ''}">
    ${dateLabel}
    <div class="bm-team ${m.winner === m.h ? 'winner' : ''}">
      <span>${ht.flag}</span>
      <span class="bm-name">${m.h === 'TBD' ? 'TBD' : ht.name}</span>
      ${m.score ? `<span class="bm-s">${m.score.split('-')[0]}</span>` : ''}
    </div>
    <div class="bm-team ${m.winner === m.a ? 'winner' : ''}">
      <span>${at.flag}</span>
      <span class="bm-name">${m.a === 'TBD' ? 'TBD' : at.name}</span>
      ${m.score ? `<span class="bm-s">${m.score.split('-')[1]}</span>` : ''}
    </div>
    ${isLive ? `<div class="bm-live">LIVE ${m.time}</div>` : timeLabel}
  </div>`;
}

function renderBracket() {
  const rounds = [
    { label: 'Round of 32', matches: BRACKET.r32 },
    { label: 'Round of 16', matches: BRACKET.r16 },
    { label: 'Quarter Finals', matches: BRACKET.qf },
    { label: 'Semi Finals', matches: BRACKET.sf },
    { label: 'Final', matches: [BRACKET.final] },
  ];
  const html = rounds.map(r => `
    <div class="bracket-round">
      <div class="bracket-round-label">${r.label}</div>
      <div class="bracket-matches">
        ${r.matches.map(renderBracketMatch).join('')}
      </div>
    </div>
  `).join('');
  document.getElementById('bracket-view').innerHTML = '<div class="bracket-scroll"><div class="bracket-inner">' + html + '</div></div>';
}

// =====================
// LIVE WIDGET
// =====================
function toggleWidget() {
  widgetOpen = !widgetOpen;
  document.getElementById('widget-panel').classList.toggle('open', widgetOpen);
  document.getElementById('widget-btn').classList.toggle('open', widgetOpen);
}

function setWidgetTab(tab) {
  widgetTab = tab;
  document.querySelectorAll('.wtab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
  renderWidgetContent();
}

function renderWidgetContent() {
  const d = NEXT_MATCH;
  const h = TEAMS[d.match.h];
  const a = TEAMS[d.match.a];

  document.getElementById('w-score-h').textContent = `${h.flag} ${h.name}`;
  document.getElementById('w-score-a').textContent = `${a.name} ${a.flag}`;
  document.getElementById('w-score-mid').innerHTML =
    `<span class="w-s" style="font-size:20px;color:var(--yellow)">${d.match.label}</span>`;

  const minEl = document.getElementById('w-min');
  minEl.textContent = 'NEXT';
  minEl.classList.remove('live-color');
  minEl.style.color = 'var(--yellow)';

  if (widgetTab === 'events') {
    const icons = { goal: '⚽', yellow: '🟨', red: '🟥', sub: '↕️', corner: '🚩' };
    document.getElementById('w-content').innerHTML =
      `<div style="font-size:10px;color:var(--ghost);text-transform:uppercase;letter-spacing:1px;padding:6px 0 10px;font-weight:700;">Predicted Key Events</div>` +
      d.events.map(e => {
        const teamName = e.team === 'h' ? h.name : a.name;
        return `<div class="w-event">
          <span class="w-ev-min">${e.min}</span>
          <span class="w-ev-icon">${icons[e.type] || '•'}</span>
          <div class="w-ev-desc">
            <strong>${e.player || (e.pIn ? e.pIn + ' ↑' : '')}</strong>
            ${e.pOut ? `<span class="w-ev-sub"> / ${e.pOut} ↓</span>` : ''}
            ${e.desc ? `<span class="w-ev-assist"> — ${e.desc}</span>` : ''}
            <span class="w-ev-team"> · ${teamName}</span>
          </div>
        </div>`;
      }).join('');
  } else if (widgetTab === 'lineups') {
    const renderXI = (xi, teamColor) => xi.map(row =>
      `<div class="lineup-row">${row.map(p =>
        `<div class="lineup-player" style="border-color:${teamColor}">
          <span class="lp-no">${p.no}</span>
          <span class="lp-name">${p.n.split(' ').pop()}</span>
        </div>`
      ).join('')}</div>`
    ).join('');
    document.getElementById('w-content').innerHTML = `
      <div class="lineups-container">
        <div class="lineup-side">
          <div class="lineup-title" style="color:${h.color}">${h.flag} ${h.name}</div>
          <div class="pitch-half">${renderXI(d.homeXI, h.color)}</div>
        </div>
        <div class="lineup-divider"></div>
        <div class="lineup-side">
          <div class="lineup-title" style="color:${a.color}">${a.flag} ${a.name}</div>
          <div class="pitch-half reverse">${renderXI(d.awayXI, a.color)}</div>
        </div>
      </div>`;
  } else {
    document.getElementById('w-content').innerHTML =
      `<div style="font-size:10px;color:var(--ghost);text-transform:uppercase;letter-spacing:1px;padding:6px 0 10px;font-weight:700;">Pre-Match Analysis</div>` +
      d.commentary.map(c =>
        `<div class="w-comm">
          <span class="w-comm-min">${c.min}</span>
          <span class="w-comm-text">${c.text}</span>
        </div>`
      ).join('');
  }
}

// =====================
// ADD PREDICTION MODAL
// =====================
function openAddModal() {
  document.getElementById('add-modal').classList.add('open');
}
function closeAddModal() {
  document.getElementById('add-modal').classList.remove('open');
}
function submitPrediction(e) {
  e.preventDefault();
  const f = e.target;
  const newP = {
    id: Date.now(), date: f.date.value,
    home: f.home.value.toUpperCase(), away: f.away.value.toUpperCase(),
    predictedScore: { h: parseInt(f.ph.value), a: parseInt(f.pa.value) },
    actualScore: null, status: 'upcoming',
    league: f.league.value || 'Custom',
    round: f.round.value || 'Custom',
    venue: f.venue.value || 'TBD',
    confidence: parseInt(f.confidence.value),
    analysis: f.analysis.value || 'No analysis provided.',
    time: f.time.value || 'TBD',
    correct: false,
  };
  if (!TEAMS[newP.home]) TEAMS[newP.home] = { name: f.hname.value, flag: f.hflag.value || '🏳', color: '#888' };
  if (!TEAMS[newP.away]) TEAMS[newP.away] = { name: f.aname.value, flag: f.aflag.value || '🏳', color: '#888' };
  userPredictions.push(newP);
  localStorage.setItem('hx_predictions', JSON.stringify(userPredictions));
  closeAddModal();
  renderPredictions();
  renderHome();
}

// =====================
// HELPERS
// =====================
function formatDate(d) {
  const dt = new Date(d);
  return dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

// =====================
// INIT
// =====================
function init() {
  renderBanner();
  renderHome();
  navigate('home');
  renderWidgetContent();

  // Nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      navigate(link.dataset.page);
    });
  });

  // Add prediction form
  document.getElementById('add-pred-form').addEventListener('submit', submitPrediction);

  // Close modal on backdrop
  document.getElementById('add-modal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeAddModal();
  });

  // Animate stats counters
  animateCounters();
}

function animateCounters() {
  const stats = getStats();
  animateNum('stat-accuracy', 0, stats.accuracy, '%', 1200);
  animateNum('stat-total', 0, stats.total, '', 800);
  animateNum('stat-streak', 0, stats.streak, '', 600);
  animateNum('stat-upcoming', 0, stats.upcoming + stats.live, '', 700);
}

function animateNum(id, from, to, suffix, duration) {
  const el = document.getElementById(id);
  if (!el) return;
  const start = performance.now();
  function tick(now) {
    const p = Math.min((now - start) / duration, 1);
    const val = Math.round(from + (to - from) * easeOut(p));
    el.textContent = val + suffix;
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

document.addEventListener('DOMContentLoaded', init);
