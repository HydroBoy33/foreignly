import streamlit as st  # Foreignly v2: grid / list / map views
import pandas as pd
import requests
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

# ─── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Foreignly — International City Rankings",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ────────────────────────────────────────────────────────────────

FACTORS = [
    "Cost of Living",
    "Female:Male Ratio",
    "English Proficiency",
    "Ease of Travel",
    "Safety",
    "Weather",
    "Dating App Activity",
    "Cultural Openness",
    "Internet Speed",
    "Expat Community",
    "Healthcare Quality",
    "Flight Connectivity",
    "Air Quality",
    "Political Stability",
    "Nightlife & Social Scene",
]

FACTOR_EMOJI = {
    "Cost of Living":          "💰",
    "Female:Male Ratio":       "👩",
    "English Proficiency":     "🗣️",
    "Ease of Travel":          "✈️",
    "Safety":                  "🛡️",
    "Weather":                 "☀️",
    "Dating App Activity":     "📱",
    "Cultural Openness":       "🤝",
    "Internet Speed":          "⚡",
    "Expat Community":         "🌍",
    "Healthcare Quality":      "🏥",
    "Flight Connectivity":     "🛫",
    "Air Quality":             "🍃",
    "Political Stability":     "🏛️",
    "Nightlife & Social Scene":"🎉",
}

FLAGS = {
    "Argentina":      "🇦🇷",
    "Brazil":         "🇧🇷",
    "Bulgaria":       "🇧🇬",
    "Chile":          "🇨🇱",
    "Colombia":       "🇨🇴",
    "Costa Rica":     "🇨🇷",
    "Czech Republic": "🇨🇿",
    "Egypt":          "🇪🇬",
    "Estonia":        "🇪🇪",
    "Georgia":        "🇬🇪",
    "Germany":        "🇩🇪",
    "Hong Kong":      "🇭🇰",
    "Hungary":        "🇭🇺",
    "Indonesia":      "🇮🇩",
    "Japan":          "🇯🇵",
    "Malaysia":       "🇲🇾",
    "Mexico":         "🇲🇽",
    "Morocco":        "🇲🇦",
    "Panama":         "🇵🇦",
    "Peru":           "🇵🇪",
    "Philippines":    "🇵🇭",
    "Poland":         "🇵🇱",
    "Portugal":       "🇵🇹",
    "Serbia":         "🇷🇸",
    "Singapore":      "🇸🇬",
    "South Africa":   "🇿🇦",
    "South Korea":    "🇰🇷",
    "Spain":          "🇪🇸",
    "Taiwan":         "🇹🇼",
    "Thailand":       "🇹🇭",
    "Turkey":         "🇹🇷",
    "UAE":            "🇦🇪",
    "Vietnam":        "🇻🇳",
    # New countries
    "Croatia":        "🇭🇷",
    "Ecuador":        "🇪🇨",
    "Finland":        "🇫🇮",
    "Greece":         "🇬🇷",
    "Jordan":         "🇯🇴",
    "Lithuania":      "🇱🇹",
    "Nigeria":        "🇳🇬",
    "Paraguay":       "🇵🇾",
    "Romania":        "🇷🇴",
    "Slovenia":       "🇸🇮",
    "Sri Lanka":      "🇱🇰",
    "Tunisia":        "🇹🇳",
    "Uzbekistan":     "🇺🇿",
}

REGION_ORDER = [
    "All Regions",
    "Southeast Asia",
    "East Asia",
    "South Asia",
    "Latin America",
    "Europe",
    "EE/Caucasus",
    "MEA",
]

SHORT = {
    "Female:Male Ratio":        "F:M Ratio",
    "Nightlife & Social Scene": "Nightlife",
    "Cultural Openness":        "Cult. Open.",
    "English Proficiency":      "English",
    "Healthcare Quality":       "Healthcare",
    "Flight Connectivity":      "Flights",
    "Political Stability":      "Pol. Stab.",
    "Expat Community":          "Expats",
    "Ease of Travel":           "Visa/Travel",
    "Dating App Activity":      "Dating Apps",
    "Internet Speed":           "Internet",
}

# ─── City coordinates (lat, lon) for the map view ─────────────────────────────

CITY_COORDS = {
    "Chiang Mai":            (18.7883,  98.9853),
    "Bangkok":               (13.7563, 100.5018),
    "Phuket":                ( 7.8804,  98.3923),
    "Bali (Canggu/Ubud)":    (-8.6478, 115.1385),
    "Ho Chi Minh City":      (10.8231, 106.6297),
    "Hanoi":                 (21.0285, 105.8542),
    "Da Nang":               (16.0544, 108.2022),
    "Kuala Lumpur":          ( 3.1390, 101.6869),
    "Penang":                ( 5.4164, 100.3327),
    "Singapore":             ( 1.3521, 103.8198),
    "Manila":                (14.5995, 120.9842),
    "Krabi":                 ( 8.0863,  98.9063),
    "Ko Pha Ngan":           ( 9.7311, 100.0136),
    "Ko Lanta":              ( 7.6244,  99.0782),
    "Nakhon Ratchasima":     (14.9799, 102.0977),
    "Kota Kinabalu":         ( 5.9804, 116.0735),
    "Tokyo":                 (35.6762, 139.6503),
    "Osaka":                 (34.6937, 135.5023),
    "Fukuoka":               (33.5902, 130.4017),
    "Seoul":                 (37.5665, 126.9780),
    "Taipei":                (25.0330, 121.5654),
    "Hong Kong":             (22.3193, 114.1694),
    "Kyoto":                 (35.0116, 135.7681),
    "Kobe":                  (34.6901, 135.1956),
    "Naha (Okinawa)":        (26.2124, 127.6809),
    "Busan":                 (35.1796, 129.0756),
    "Mexico City":           (19.4326, -99.1332),
    "Playa del Carmen":      (20.6296, -87.0739),
    "Oaxaca":                (17.0732, -96.7266),
    "Medellín":              ( 6.2476, -75.5658),
    "Bogotá":                ( 4.7110, -74.0721),
    "Buenos Aires":          (-34.6037, -58.3816),
    "Santiago":              (-33.4489, -70.6693),
    "Lima":                  (-12.0464, -77.0428),
    "Cusco":                 (-13.5320, -71.9675),
    "San José":              ( 9.9281, -84.0907),
    "Panama City":           ( 8.9824, -79.5199),
    "Rio de Janeiro":        (-22.9068, -43.1729),
    "Florianópolis":         (-27.5954, -48.5480),
    "Cordoba":               (-31.4201, -64.1888),
    "Cuenca":                ( -2.9001, -79.0059),
    "Curitiba":              (-25.4284, -49.2733),
    "Recife":                ( -8.0476, -34.8770),
    "Asuncion":              (-25.2637, -57.5759),
    "Lisbon":                (38.7223,  -9.1393),
    "Porto":                 (41.1579,  -8.6291),
    "Funchal (Madeira)":     (32.6669, -16.9241),
    "Barcelona":             (41.3851,   2.1734),
    "Madrid":                (40.4168,  -3.7038),
    "Valencia":              (39.4699,  -0.3763),
    "Las Palmas (Canary Is.)": (28.1235, -15.4363),
    "Berlin":                (52.5200,  13.4050),
    "Prague":                (50.0755,  14.4378),
    "Budapest":              (47.4979,  19.0402),
    "Kraków":                (50.0647,  19.9450),
    "Warsaw":                (52.2297,  21.0122),
    "Tallinn":               (59.4370,  24.7536),
    "Athens":                (37.9838,  23.7275),
    "Split":                 (43.5081,  16.4402),
    "Dubrovnik":             (42.6507,  18.0944),
    "Ljubljana":             (46.0569,  14.5058),
    "Vilnius":               (54.6872,  25.2797),
    "Wrocław":               (51.1079,  17.0385),
    "Portimão":              (37.1366,  -8.5377),
    "Alicante":              (38.3452,  -0.4810),
    "Munich":                (48.1351,  11.5820),
    "Faro":                  (37.0194,  -7.9304),
    "Helsinki":              (60.1699,  24.9384),
    "Belgrade":              (44.7866,  20.4489),
    "Tbilisi":               (41.7151,  44.8271),
    "Sofia":                 (42.6977,  23.3219),
    "Tashkent":              (41.2995,  69.2401),
    "Timisoara":             (45.7489,  21.2087),
    "Novi Sad":              (45.2671,  19.8335),
    "Varna":                 (43.2141,  27.9147),
    "Dubai":                 (25.2048,  55.2708),
    "Istanbul":              (41.0082,  28.9784),
    "Cape Town":             (-33.9249, 18.4241),
    "Marrakech":             (31.6295,  -7.9811),
    "Cairo":                 (30.0444,  31.2357),
    "Tunis":                 (36.8065,  10.1815),
    "Amman":                 (31.9454,  35.9284),
    "Lagos":                 ( 6.5244,   3.3792),
    "Weligama":              ( 5.9667,  80.4297),
}

# ─── Wikipedia title overrides for city photos ────────────────────────────────
# Default: use the City name as the Wikipedia article title.

WIKI_TITLES = {
    "Bali (Canggu/Ubud)":      "Canggu",
    "Naha (Okinawa)":          "Naha",
    "Funchal (Madeira)":       "Funchal",
    "Las Palmas (Canary Is.)": "Las Palmas",
    "Ko Pha Ngan":             "Ko Pha-ngan",
    "Cordoba":                 "Córdoba, Argentina",
    "Asuncion":                "Asunción",
    "San José":                "San José, Costa Rica",
    "Cuenca":                  "Cuenca, Ecuador",
    "Santiago":                "Santiago, Chile",
    "Split":                   "Split, Croatia",
    "Valencia":                "Valencia, Spain",
    "Oaxaca":                  "Oaxaca City",
    "Timisoara":               "Timișoara",
    "Varna":                   "Varna, Bulgaria",
    "Faro":                    "Faro, Portugal",
    "Panama City":             "Panama City",
}

# ─── Data ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=0)
def load_data():
    return pd.read_csv("cities.csv")

# ─── City images (Wikipedia page thumbnails, fetched once & cached) ──────────

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_city_images(cities: tuple) -> dict:
    """Return {city: image_url}. Empty string when no image is available."""
    headers = {"User-Agent": "Foreignly/1.0 (city-rankings app; contact via GitHub)"}

    def fetch(city):
        title = WIKI_TITLES.get(city, city)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}"
        for _ in range(2):  # one retry on transient failures
            try:
                r = requests.get(url, headers=headers, timeout=5)
                if r.ok:
                    thumb = (r.json().get("thumbnail") or {}).get("source", "")
                    if thumb:
                        return city, thumb.replace("/320px-", "/640px-")
                    break  # page exists but has no image — don't retry
            except Exception:
                continue
        return city, ""

    try:
        with ThreadPoolExecutor(max_workers=12) as ex:
            return dict(ex.map(fetch, cities))
    except Exception:
        return {c: "" for c in cities}

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown(
    """
<style>
/* === Dark mode base === */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
.main .block-container {
    background-color: #0d0d0d !important;
    color: #e8e8e8 !important;
}

[data-testid="stSidebar"] {
    background-color: #101010 !important;
    border-right: 1px solid #1e1e1e !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* === Typography === */
* { font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif; }

/* === App header === */
.app-header { padding-bottom: 20px; margin-bottom: 4px; }
.app-title  { font-size: 30px; font-weight: 900; color: #f97316;
               letter-spacing: -0.04em; line-height: 1; }
.app-sub    { font-size: 12px; color: #555; margin-top: 4px; }

/* === Showing count === */
.showing-count { font-size: 12px; color: #555; margin: 6px 0 14px 0; }

/* === City card === */
.city-card {
    background: #131313;
    border: 1px solid #1e1e1e;
    border-radius: 10px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
    cursor: pointer;
    transition: border-color 0.15s;
}
.city-card:hover { border-color: #f97316; }

.rank-num {
    font-size: 13px; font-weight: 700; color: #444;
    min-width: 26px; flex-shrink: 0;
}
.city-flag  { font-size: 24px; flex-shrink: 0; }
.city-main  { flex: 1; min-width: 120px; }
.city-name  { font-size: 15px; font-weight: 700; color: #f0f0f0; }
.city-sub   { font-size: 11px; color: #555; margin-top: 2px; }

/* === Score badge === */
.score-badge {
    font-size: 24px; font-weight: 800;
    min-width: 56px; text-align: right; flex-shrink: 0;
}
.sc-green  { color: #22c55e; }
.sc-yellow { color: #f59e0b; }
.sc-red    { color: #ef4444; }

/* === Mini pills === */
.pills-row { display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
.pill {
    padding: 3px 9px; border-radius: 999px;
    font-size: 10px; font-weight: 600; white-space: nowrap;
}
.p-green  { background: #14532d44; color: #22c55e; border: 1px solid #14532d; }
.p-yellow { background: #42200644; color: #f59e0b; border: 1px solid #422006; }
.p-red    { background: #450a0a44; color: #ef4444; border: 1px solid #450a0a; }

/* === Factor detail grid === */
.factor-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    padding: 4px 0 8px 0;
}
.factor-item { display: flex; flex-direction: column; gap: 4px; }
.factor-lbl  { font-size: 10px; color: #555; text-transform: uppercase;
                letter-spacing: 0.06em; }
.bar-bg { background: #1e1e1e; border-radius: 3px; height: 5px; }
.bar-fill { height: 5px; border-radius: 3px; }
.factor-val { font-size: 12px; font-weight: 700; }

/* === Photo banner inside expanded cards === */
.photo-banner {
    width: 100%; height: 180px; object-fit: cover;
    border-radius: 10px; margin-bottom: 12px; display: block;
}

/* === Photo grid tiles (Nomad List style) === */
.tile-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 14px;
}
.tile {
    position: relative;
    height: 240px;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid #1e1e1e;
    background-color: #131313;
    background-size: cover;
    background-position: center;
    transition: border-color 0.15s, transform 0.15s;
}
.tile:hover { border-color: #f97316; transform: translateY(-2px); }
.tile-shade {
    position: absolute; inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.25) 0%,
                rgba(0,0,0,0.05) 35%, rgba(13,13,13,0.92) 100%);
}
.tile-fallback-flag {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 72px; opacity: 0.5;
}
.tile-rank {
    position: absolute; top: 12px; left: 14px;
    font-size: 12px; font-weight: 800; color: #fff;
    background: rgba(0,0,0,0.55); padding: 3px 9px; border-radius: 8px;
    backdrop-filter: blur(4px);
}
.tile-score {
    position: absolute; top: 12px; right: 14px;
    font-size: 17px; font-weight: 800;
    background: rgba(0,0,0,0.55); padding: 3px 11px; border-radius: 8px;
    backdrop-filter: blur(4px);
}
.tile-bottom { position: absolute; left: 14px; right: 14px; bottom: 12px; }
.tile-city    { font-size: 18px; font-weight: 800; color: #fff;
                text-shadow: 0 1px 4px rgba(0,0,0,0.8); }
.tile-country { font-size: 11px; color: #ccc; margin-top: 1px;
                text-shadow: 0 1px 3px rgba(0,0,0,0.8); }
.tile-pills {
    display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px;
    opacity: 0; max-height: 0; overflow: hidden;
    transition: opacity 0.2s, max-height 0.2s;
}
.tile:hover .tile-pills { opacity: 1; max-height: 80px; }

/* === Map detail panel === */
.map-hint { font-size: 12px; color: #555; margin: 8px 0; }

/* === Expander card styling === */
[data-testid="stExpander"] {
    background: #131313 !important;
    border: 1px solid #1e1e1e !important;
    border-radius: 10px !important;
    margin-bottom: 8px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"]:hover {
    border-color: #2a2a2a !important;
}
[data-testid="stExpander"] summary {
    padding: 0 !important;
    background: transparent !important;
}
[data-testid="stExpander"] summary:hover {
    color: inherit !important;
}

/* Expander arrow color */
[data-testid="stExpander"] svg { color: #444 !important; }

/* Override Streamlit input backgrounds */
[data-testid="stTextInput"] input {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    color: #e8e8e8 !important;
    border-radius: 8px !important;
}
[data-testid="stTextInput"] input::placeholder { color: #555 !important; }

[data-baseweb="select"] {
    background: #1a1a1a !important;
}
[data-baseweb="select"] > div {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    color: #e8e8e8 !important;
    border-radius: 8px !important;
}

/* View toggle radio — horizontal pills */
[data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] {
    flex-direction: row; gap: 6px;
}
[data-testid="stMain"] [data-testid="stRadio"] label {
    background: #1a1a1a; border: 1px solid #2a2a2a;
    border-radius: 8px; padding: 6px 14px;
    color: #ccc !important;
}
[data-testid="stMain"] [data-testid="stRadio"] label:has(input:checked) {
    border-color: #f97316;
}
[data-testid="stMain"] [data-testid="stRadio"] label p { color: #ddd !important; }
[data-testid="stMain"] [data-testid="stRadio"] [data-testid="stWidgetLabel"] { display: none; }

/* Sidebar slider labels */
[data-testid="stSidebar"] label { color: #ccc !important; font-size: 14px !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #666 !important; font-size: 10px !important;
    text-transform: uppercase; letter-spacing: 0.08em;
}

/* Slider label text — target the actual rendered paragraph inside each slider */
[data-testid="stSidebar"] [data-testid="stSlider"] label p {
    font-size: 15px !important;
    color: #ddd !important;
    font-weight: 500 !important;
    line-height: 1.4 !important;
}
[data-testid="stSidebar"] [data-testid="stSlider"] label div {
    font-size: 15px !important;
    color: #ddd !important;
}

/* Slider accent */
[data-baseweb="slider"] [role="slider"] { background: #f97316 !important; }
[data-baseweb="slider"] [data-testid="stThumbValue"] { color: #f97316 !important; }

/* Custom factor labels */
[data-testid="stSidebar"] .factor-label,
[data-testid="stSidebar"] .factor-label * {
    font-size: 18px !important;
    color: #ccc !important;
    font-weight: 600 !important;
    margin: 12px 0 6px 0 !important;
    display: block !important;
    line-height: 1.4 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ─── Score color helpers ───────────────────────────────────────────────────────

def score_cls(s: float) -> str:
    """Return CSS class suffix for a score 0-100."""
    if s >= 70:
        return "green"
    if s >= 40:
        return "yellow"
    return "red"

def bar_color(s: float) -> str:
    m = {"green": "#22c55e", "yellow": "#f59e0b", "red": "#ef4444"}
    return m[score_cls(s)]

def pill_html(label: str, score: float) -> str:
    c = score_cls(score)
    return f'<span class="pill p-{c}">{label}&nbsp;{score:.0f}</span>'

# ─── HTML builders (shared by list / grid / map views) ───────────────────────

def top5_factors(row, weights) -> list:
    contrib = {f: row[f] * weights[f] for f in FACTORS if weights[f] > 0}
    return sorted(contrib, key=contrib.get, reverse=True)[:5]

def pills_for(row, weights) -> str:
    return " ".join(pill_html(SHORT.get(f, f), row[f]) for f in top5_factors(row, weights))

def card_html(rank: int, row, weights) -> str:
    flag  = FLAGS.get(row["Country"], "🌐")
    score = row["Weighted Score"]
    sc    = score_cls(score)
    return f"""
<div class="city-card">
  <div class="rank-num">#{rank}</div>
  <div class="city-main">
    <div class="city-name">{flag} {row['City']}</div>
    <div class="city-sub">{row['Country']} · {row['Region']}</div>
  </div>
  <div class="score-badge sc-{sc}">{score:.1f}</div>
  <div class="pills-row">{pills_for(row, weights)}</div>
</div>"""

def detail_grid_html(row) -> str:
    raw_labels = {}
    if "Raw_USD"  in row.index: raw_labels["Cost of Living"] = f"${int(row['Raw_USD']):,}/mo"
    if "Raw_Mbps" in row.index: raw_labels["Internet Speed"] = f"{int(row['Raw_Mbps'])} Mbps"
    if "Raw_AQI"  in row.index: raw_labels["Air Quality"]    = f"AQI {int(row['Raw_AQI'])}"

    grid_rows = ""
    for f in FACTORS:
        fs  = row[f]
        fc  = bar_color(fs)
        sc2 = score_cls(fs)
        raw = (f" <span style='font-size:10px;color:#666;font-weight:400;'>· {raw_labels[f]}</span>"
               if f in raw_labels else "")
        grid_rows += f"""
<div class="factor-item">
  <div class="factor-lbl">{f}{raw}</div>
  <div class="bar-bg">
    <div class="bar-fill" style="width:{fs:.1f}%;background:{fc};"></div>
  </div>
  <div class="factor-val sc-{sc2}">{fs:.1f}</div>
</div>"""
    return f'<div class="factor-grid">{grid_rows}</div>'

def tile_html(rank: int, row, weights, img_url: str) -> str:
    flag  = FLAGS.get(row["Country"], "🌐")
    score = row["Weighted Score"]
    sc    = score_cls(score)
    if img_url:
        bg       = f"background-image:url('{img_url}');"
        fallback = ""
    else:
        bg       = "background:linear-gradient(135deg,#1a1a1a 0%,#26160a 100%);"
        fallback = f'<div class="tile-fallback-flag">{flag}</div>'
    return f"""
<div class="tile" style="{bg}">
  {fallback}
  <div class="tile-shade"></div>
  <div class="tile-rank">#{rank}</div>
  <div class="tile-score sc-{sc}">{score:.1f}</div>
  <div class="tile-bottom">
    <div class="tile-city">{flag} {row['City']}</div>
    <div class="tile-country">{row['Country']} · {row['Region']}</div>
    <div class="tile-pills">{pills_for(row, weights)}</div>
  </div>
</div>"""

# ─── Load data ────────────────────────────────────────────────────────────────

df = load_data()

# ─── Reset flags (must run BEFORE sliders are created) ───────────────────────

if st.session_state.pop("_reset_to_5", False):
    for factor in FACTORS:
        st.session_state[f"w_{factor}"] = 5

if st.session_state.pop("_reset_to_0", False):
    for factor in FACTORS:
        st.session_state[f"w_{factor}"] = 0

# ─── Sidebar: weight sliders ──────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        "<p style='font-size:10px;color:#555;text-transform:uppercase;"
        "letter-spacing:.08em;margin-bottom:12px;'>⚖ Factor Weights (0–10)</p>",
        unsafe_allow_html=True,
    )
    weights: dict[str, int] = {}
    for factor in FACTORS:
        st.markdown(
            f"<span class='factor-label'><span style='font-size:22px;'>{FACTOR_EMOJI[factor]}</span> {factor}</span>",
            unsafe_allow_html=True,
        )
        weights[factor] = st.slider("", 0, 10, 5, key=f"w_{factor}", label_visibility="collapsed")

    st.markdown("<hr style='border-color:#1e1e1e;margin:16px 0;'>", unsafe_allow_html=True)
    if st.button("Reset all weights to 5", width="stretch"):
        st.session_state["_reset_to_5"] = True
        st.rerun()
    if st.button("Reset all weights to 0", width="stretch"):
        st.session_state["_reset_to_0"] = True
        st.rerun()

# ─── Compute weighted scores ──────────────────────────────────────────────────

total_weight = sum(weights.values()) or 1

def weighted_score(row) -> float:
    return sum(row[f] * weights[f] for f in FACTORS) / total_weight

df["Weighted Score"] = df.apply(weighted_score, axis=1).round(1)

# ─── App header ───────────────────────────────────────────────────────────────

st.markdown(
    """
<div class="app-header">
  <div class="app-title">🌍 Foreignly</div>
  <div class="app-sub">International city rankings for dating &amp; relocation · adjust weights to personalize</div>
</div>
""",
    unsafe_allow_html=True,
)

# ─── Filter bar + view toggle ─────────────────────────────────────────────────

c1, c2, c3 = st.columns([3, 2, 2])
with c1:
    search = st.text_input(
        "search", placeholder="🔍  Search city or country...",
        label_visibility="collapsed",
    )
with c2:
    region = st.selectbox(
        "region", REGION_ORDER, label_visibility="collapsed"
    )
with c3:
    sort_by = st.selectbox(
        "sort", ["Weighted Score"] + FACTORS,
        label_visibility="collapsed",
    )

view_mode = st.radio(
    "view", ["🖼 Grid", "📋 List", "🗺 Map"],
    horizontal=True, label_visibility="collapsed", key="view_mode",
)

# ─── Apply filters ────────────────────────────────────────────────────────────

view = df.copy()

if search.strip():
    q = search.strip().lower()
    view = view[
        view["City"].str.lower().str.contains(q, na=False)
        | view["Country"].str.lower().str.contains(q, na=False)
    ]

if region != "All Regions":
    view = view[view["Region"] == region]

view = view.sort_values(sort_by, ascending=False).reset_index(drop=True)

# ─── City count ───────────────────────────────────────────────────────────────

st.markdown(
    f'<div class="showing-count">Showing <strong>{len(view)}</strong> cities</div>',
    unsafe_allow_html=True,
)

if view.empty:
    st.markdown(
        "<p style='color:#555;text-align:center;padding:40px 0;'>No cities match your filters.</p>",
        unsafe_allow_html=True,
    )
    st.stop()

# ─── Fetch city photos (needed by grid + list + map detail) ───────────────────

images = fetch_city_images(tuple(df["City"]))

# ═══ GRID VIEW (Nomad List-style photo tiles) ═════════════════════════════════

if view_mode == "🖼 Grid":
    tiles = "".join(
        tile_html(i + 1, view.iloc[i], weights, images.get(view.iloc[i]["City"], ""))
        for i in range(len(view))
    )
    st.markdown(f'<div class="tile-grid">{tiles}</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:11px;color:#444;margin-top:14px;'>Hover a city to "
        "see its top factors · switch to 📋 List for the full breakdown · photos "
        "via Wikipedia</p>",
        unsafe_allow_html=True,
    )

# ═══ LIST VIEW (expandable cards) ═════════════════════════════════════════════

elif view_mode == "📋 List":
    for idx in range(len(view)):
        row   = view.iloc[idx]
        rank  = idx + 1
        score = row["Weighted Score"]
        img   = images.get(row["City"], "")
        banner = f'<img class="photo-banner" src="{img}" alt="{row["City"]}">' if img else ""

        label = f"#{rank}  {row['City']}  ·  {row['Country']}  —  {score:.1f}"
        with st.expander(label, expanded=False):
            st.markdown(
                banner + card_html(rank, row, weights) + detail_grid_html(row),
                unsafe_allow_html=True,
            )

# ═══ MAP VIEW (interactive world map) ═════════════════════════════════════════

else:
    plot = view[view["City"].isin(CITY_COORDS)].copy()
    plot["lat"] = plot["City"].map(lambda c: CITY_COORDS[c][0])
    plot["lon"] = plot["City"].map(lambda c: CITY_COORDS[c][1])
    plot["rank"] = range(1, len(plot) + 1)

    fig = go.Figure(
        go.Scattermap(
            lat=plot["lat"],
            lon=plot["lon"],
            mode="markers",
            marker=dict(
                size=(8 + plot["Weighted Score"] / 7).tolist(),
                color=[bar_color(s) for s in plot["Weighted Score"]],
                opacity=0.92,
            ),
            customdata=plot[["City", "Country", "Weighted Score", "rank"]].values,
            hovertemplate=(
                "<b>#%{customdata[3]} %{customdata[0]}</b><br>"
                "%{customdata[1]}<br>"
                "Score: %{customdata[2]:.1f}"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        map=dict(style="carto-darkmatter", center=dict(lat=22, lon=40), zoom=1.4),
        margin=dict(l=0, r=0, t=0, b=0),
        height=540,
        paper_bgcolor="#0d0d0d",
        hoverlabel=dict(bgcolor="#1a1a1a", font_color="#e8e8e8", bordercolor="#f97316"),
        showlegend=False,
    )

    event = st.plotly_chart(
        fig, width="stretch",
        on_select="rerun", selection_mode="points", key="city_map",
    )

    # ── Detail panel for the clicked city ──
    selected_city = None
    try:
        pts = event.selection.points if event and event.selection else []
        if pts:
            selected_city = pts[0]["customdata"][0]
    except Exception:
        selected_city = None

    if selected_city is not None and (plot["City"] == selected_city).any():
        row  = plot[plot["City"] == selected_city].iloc[0]
        rank = int(row["rank"])
        img  = images.get(selected_city, "")
        banner = f'<img class="photo-banner" src="{img}" alt="{selected_city}">' if img else ""
        st.markdown(
            banner + card_html(rank, row, weights) + detail_grid_html(row),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="map-hint">🖱 Click a city marker to see its full factor '
            "breakdown · marker size &amp; color = weighted score</div>",
            unsafe_allow_html=True,
        )
