import streamlit as st
import pandas as pd

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

# ─── Data ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=0)
def load_data():
    return pd.read_csv("cities.csv")

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
    if st.button("Reset all weights to 5", use_container_width=True):
        st.session_state["_reset_to_5"] = True
        st.rerun()
    if st.button("Reset all weights to 0", use_container_width=True):
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

# ─── Filter bar ───────────────────────────────────────────────────────────────

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

# ─── City cards ───────────────────────────────────────────────────────────────

if view.empty:
    st.markdown(
        "<p style='color:#555;text-align:center;padding:40px 0;'>No cities match your filters.</p>",
        unsafe_allow_html=True,
    )
else:
    for idx in range(len(view)):
        row     = view.iloc[idx]
        rank    = idx + 1
        flag    = FLAGS.get(row["Country"], "🌐")
        score   = row["Weighted Score"]
        sc      = score_cls(score)

        # Top-5 factors by weighted contribution (ignoring zero-weight factors)
        contrib = {
            f: row[f] * weights[f]
            for f in FACTORS
            if weights[f] > 0
        }
        top5 = sorted(contrib, key=contrib.get, reverse=True)[:5]

        # Short label: trim long names for pills
        SHORT = {
            "Female:Male Ratio":      "F:M Ratio",
            "Nightlife & Social Scene": "Nightlife",
            "Cultural Openness":      "Cult. Open.",
            "English Proficiency":    "English",
            "Healthcare Quality":     "Healthcare",
            "Flight Connectivity":    "Flights",
            "Political Stability":    "Pol. Stab.",
            "Expat Community":        "Expats",
            "Ease of Travel":         "Visa/Travel",
            "Dating App Activity":    "Dating Apps",
            "Internet Speed":         "Internet",
        }
        pills_html = " ".join(
            pill_html(SHORT.get(f, f), row[f]) for f in top5
        )

        # Card HTML (shown inside the expander when open)
        card_html = f"""
<div class="city-card">
  <div class="rank-num">#{rank}</div>
  <div class="city-main">
    <div class="city-name">{flag} {row['City']}</div>
    <div class="city-sub">{row['Country']} · {row['Region']}</div>
  </div>
  <div class="score-badge sc-{sc}">{score:.1f}</div>
  <div class="pills-row">{pills_html}</div>
</div>"""

        # Factor detail grid HTML
        # Raw value labels for three factors (only if columns exist in CSV)
        RAW_LABELS = {}
        if "Raw_USD"  in row.index: RAW_LABELS["Cost of Living"] = f"${int(row['Raw_USD']):,}/mo"
        if "Raw_Mbps" in row.index: RAW_LABELS["Internet Speed"] = f"{int(row['Raw_Mbps'])} Mbps"
        if "Raw_AQI"  in row.index: RAW_LABELS["Air Quality"]    = f"AQI {int(row['Raw_AQI'])}"

        grid_rows = ""
        for f in FACTORS:
            fs    = row[f]
            fc    = bar_color(fs)
            sc2   = score_cls(fs)
            raw_label = f" <span style='font-size:10px;color:#666;font-weight:400;'>· {RAW_LABELS[f]}</span>" if f in RAW_LABELS else ""
            grid_rows += f"""
<div class="factor-item">
  <div class="factor-lbl">{f}{raw_label}</div>
  <div class="bar-bg">
    <div class="bar-fill" style="width:{fs:.1f}%;background:{fc};"></div>
  </div>
  <div class="factor-val sc-{sc2}">{fs:.1f}</div>
</div>"""

        detail_html = f'<div class="factor-grid">{grid_rows}</div>'

        # Expander: label = plain text summary; content = styled card + grid
        label = f"#{rank}  {row['City']}  ·  {row['Country']}  —  {score:.1f}"
        with st.expander(label, expanded=False):
            st.markdown(card_html + detail_html, unsafe_allow_html=True)
