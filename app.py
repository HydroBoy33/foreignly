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

# ISO codes for flag images (emoji flags don't render on Windows browsers)
COUNTRY_ISO = {
    "Argentina": "ar", "Brazil": "br", "Bulgaria": "bg", "Chile": "cl",
    "Colombia": "co", "Costa Rica": "cr", "Czech Republic": "cz", "Egypt": "eg",
    "Estonia": "ee", "Georgia": "ge", "Germany": "de", "Hong Kong": "hk",
    "Hungary": "hu", "Indonesia": "id", "Japan": "jp", "Malaysia": "my",
    "Mexico": "mx", "Morocco": "ma", "Panama": "pa", "Peru": "pe",
    "Philippines": "ph", "Poland": "pl", "Portugal": "pt", "Serbia": "rs",
    "Singapore": "sg", "South Africa": "za", "South Korea": "kr", "Spain": "es",
    "Taiwan": "tw", "Thailand": "th", "Turkey": "tr", "UAE": "ae",
    "Vietnam": "vn", "Croatia": "hr", "Ecuador": "ec", "Finland": "fi",
    "Greece": "gr", "Jordan": "jo", "Lithuania": "lt", "Nigeria": "ng",
    "Paraguay": "py", "Romania": "ro", "Slovenia": "si", "Sri Lanka": "lk",
    "Tunisia": "tn", "Uzbekistan": "uz",
}

def flag_img(country: str, h: int = 15) -> str:
    """Flag as an image (renders everywhere, unlike emoji flags on Windows)."""
    iso = COUNTRY_ISO.get(country)
    if not iso:
        return "🌐"
    w = round(h * 4 / 3)
    return (f'<img src="https://flagcdn.com/w80/{iso}.png" alt="{country}" '
            f'style="width:{w}px;height:{h}px;object-fit:cover;'
            f'border-radius:3px;vertical-align:-2px;">')

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
    "Ko Lanta":                "Ko Lanta District",
    "Marrakech":               "Marrakesh",
}

# Curated single iconic image per city (Wikimedia Commons, landmark articles)
CITY_IMAGES = {
    "Alicante": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/Playa_del_Postiguet_2.jpg/960px-Playa_del_Postiguet_2.jpg",  # Santa Bárbara Castle
    "Amman": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Amman_Citadel.jpg/960px-Amman_Citadel.jpg",  # Amman Citadel
    "Asuncion": "https://upload.wikimedia.org/wikipedia/commons/3/35/Palacio_de_los_L%C3%B3pez.jpg",  # Palacio de los López
    "Athens": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/1029_Acropolis_of_Athens_in_Greece_at_night_Photo_by_Giles_Laurent.jpg/960px-1029_Acropolis_of_Athens_in_Greece_at_night_Photo_by_Giles_Laurent.jpg",  # Acropolis of Athens
    "Bali (Canggu/Ubud)": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/TanahLot_2014.JPG/960px-TanahLot_2014.JPG",  # Tanah Lot
    "Bangkok": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/%E0%B9%80%E0%B8%88%E0%B8%94%E0%B8%B5%E0%B8%A2%E0%B9%8C%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%98%E0%B8%B2%E0%B8%99%E0%B8%97%E0%B8%A3%E0%B8%87%E0%B8%9B%E0%B8%A3%E0%B8%B2%E0%B8%87%E0%B8%84%E0%B9%8C%E0%B8%A7%E0%B8%B1%E0%B8%94%E0%B8%AD%E0%B8%A3%E0%B8%B8%E0%B8%932.jpg/960px-%E0%B9%80%E0%B8%88%E0%B8%94%E0%B8%B5%E0%B8%A2%E0%B9%8C%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%98%E0%B8%B2%E0%B8%99%E0%B8%97%E0%B8%A3%E0%B8%87%E0%B8%9B%E0%B8%A3%E0%B8%B2%E0%B8%87%E0%B8%84%E0%B9%8C%E0%B8%A7%E0%B8%B1%E0%B8%94%E0%B8%AD%E0%B8%A3%E0%B8%B8%E0%B8%932.jpg",  # Wat Arun
    "Barcelona": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/SF_maig_2_cropped.jpg/960px-SF_maig_2_cropped.jpg",  # Sagrada Família
    "Belgrade": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Hram_svetog_save_beograd_0005_%28edited%29.jpg/960px-Hram_svetog_save_beograd_0005_%28edited%29.jpg",  # Church of Saint Sava
    "Berlin": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Brandenburger_Tor_abends.jpg/960px-Brandenburger_Tor_abends.jpg",  # Brandenburg Gate
    "Bogotá": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/2017_Bogot%C3%A1_Bas%C3%ADlica_del_Se%C3%B1or_Ca%C3%ADdo_de_Monserrate.jpg/960px-2017_Bogot%C3%A1_Bas%C3%ADlica_del_Se%C3%B1or_Ca%C3%ADdo_de_Monserrate.jpg",  # Monserrate
    "Budapest": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Hungarian_Parliament_Building_from_across_the_Danube%2C_2025-01-11.jpg/960px-Hungarian_Parliament_Building_from_across_the_Danube%2C_2025-01-11.jpg",  # Hungarian Parliament Building
    "Buenos Aires": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Buenos_Aires_%2820234294752%29.jpg/960px-Buenos_Aires_%2820234294752%29.jpg",  # Obelisco de Buenos Aires
    "Busan": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Gwangan_Bridge1.jpg/960px-Gwangan_Bridge1.jpg",  # Gwangan Bridge
    "Cairo": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Pyramids_of_the_Giza_Necropolis.jpg/960px-Pyramids_of_the_Giza_Necropolis.jpg",  # Giza pyramid complex
    "Cape Town": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/Table_Mountain_DanieVDM.jpg/960px-Table_Mountain_DanieVDM.jpg",  # Table Mountain
    "Chiang Mai": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Wat_Phra_That_Doi_Suthep_-_Chiang_Mai.jpg/960px-Wat_Phra_That_Doi_Suthep_-_Chiang_Mai.jpg",  # Wat Phra That Doi Suthep
    "Cordoba": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Catedral_de_C%C3%B3rdoba_%282010_01%29_-_panoramio.jpg/960px-Catedral_de_C%C3%B3rdoba_%282010_01%29_-_panoramio.jpg",  # Córdoba Cathedral
    "Cuenca": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Catedral_de_la_Inmaculada_Concepci%C3%B3n%2C_Cuenca.jpg/960px-Catedral_de_la_Inmaculada_Concepci%C3%B3n%2C_Cuenca.jpg",  # New Cathedral of Cuenca
    "Curitiba": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Curitiba_Botanic_Garden.jpg/960px-Curitiba_Botanic_Garden.jpg",  # Botanical Garden of Curitiba
    "Cusco": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Sacsayhuam%C3%A1n%2C_Cusco%2C_Per%C3%BA%2C_2015-07-31%2C_DD_27.JPG/960px-Sacsayhuam%C3%A1n%2C_Cusco%2C_Per%C3%BA%2C_2015-07-31%2C_DD_27.JPG",  # Sacsayhuamán
    "Da Nang": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/C%E1%BA%A7u_R%E1%BB%93ng.jpg/960px-C%E1%BA%A7u_R%E1%BB%93ng.jpg",  # Dragon Bridge (Da Nang)
    "Dubai": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Burj_Khalifa_%28worlds_tallest_building%29_and_the_Dubai_skyline_%2825781049892%29.jpg/960px-Burj_Khalifa_%28worlds_tallest_building%29_and_the_Dubai_skyline_%2825781049892%29.jpg",  # Burj Khalifa
    "Dubrovnik": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Dubrovnik_s_24.jpg/960px-Dubrovnik_s_24.jpg",  # Walls of Dubrovnik
    "Faro": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/FaroKesklinn.jpg/960px-FaroKesklinn.jpg",  # Faro Cathedral
    "Florianópolis": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Ponte_Hercilio_Luz_-_Florianopolis_-_Santa_Catarina.jpg/960px-Ponte_Hercilio_Luz_-_Florianopolis_-_Santa_Catarina.jpg",  # Hercílio Luz Bridge
    "Fukuoka": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Fukuoka_Tower_Before_Sunset.jpg/960px-Fukuoka_Tower_Before_Sunset.jpg",  # Fukuoka Tower
    "Funchal (Madeira)": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Catedral%2C_Funchal%2C_Madeira%2C_Portugal%2C_2019-05-29%2C_DD_34.jpg/960px-Catedral%2C_Funchal%2C_Madeira%2C_Portugal%2C_2019-05-29%2C_DD_34.jpg",  # Funchal Cathedral
    "Hanoi": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Th%C3%A1p_R%C3%B9a_5.jpg/960px-Th%C3%A1p_R%C3%B9a_5.jpg",  # Turtle Tower
    "Helsinki": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Kirkko3.png/960px-Kirkko3.png",  # Helsinki Cathedral
    "Ho Chi Minh City": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Bas%C3%ADlica_de_Nuestra_Se%C3%B1ora%2C_Ciudad_Ho_Chi_Minh%2C_Vietnam%2C_2013-08-14%2C_DD_03.JPG/960px-Bas%C3%ADlica_de_Nuestra_Se%C3%B1ora%2C_Ciudad_Ho_Chi_Minh%2C_Vietnam%2C_2013-08-14%2C_DD_03.JPG",  # Notre-Dame Cathedral Basilica of Saigon
    "Hong Kong": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/Hong_Kong_Skyline_viewed_from_Victoria_Peak.jpg/960px-Hong_Kong_Skyline_viewed_from_Victoria_Peak.jpg",  # Victoria Harbour
    "Istanbul": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Hagia_Sophia_%28228968325%29.jpeg/960px-Hagia_Sophia_%28228968325%29.jpeg",  # Hagia Sophia
    "Ko Lanta": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Ko_Lanta_Beach.jpg/960px-Ko_Lanta_Beach.jpg",  # Ko Lanta Yai
    "Ko Pha Ngan": "https://upload.wikimedia.org/wikipedia/commons/f/fd/Koh_Phangan01.jpg",  # Haad Rin
    "Kobe": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/20190901_Kobe_Port_Tower-1.jpg/960px-20190901_Kobe_Port_Tower-1.jpg",  # Kobe Port Tower
    "Kota Kinabalu": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/KotaKinabalu_Sabah_CityMosque-08.jpg/960px-KotaKinabalu_Sabah_CityMosque-08.jpg",  # Kota Kinabalu City Mosque
    "Krabi": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Railay_Beach_5.jpg/960px-Railay_Beach_5.jpg",  # Railay Beach
    "Kraków": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Wawel_%284%29.jpg/960px-Wawel_%284%29.jpg",  # Wawel Castle
    "Kuala Lumpur": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Kuala_Lumpur_Tower_20250822_%281%29.jpg/960px-Kuala_Lumpur_Tower_20250822_%281%29.jpg",  # Menara Kuala Lumpur
    "Kyoto": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Golden_Pavilion_Kinkaku-ji_water_mirror_2024.jpg/960px-Golden_Pavilion_Kinkaku-ji_water_mirror_2024.jpg",  # Kinkaku-ji
    "Lagos": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Lekki-link-bridge--full-view2.jpg/960px-Lekki-link-bridge--full-view2.jpg",  # Lekki-Ikoyi Link Bridge
    "Las Palmas (Canary Is.)": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Playa_de_las_canteras_24_Dec2006_palmas_gran_canaria.jpg/960px-Playa_de_las_canteras_24_Dec2006_palmas_gran_canaria.jpg",  # Playa de Las Canteras
    "Lima": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Lima%2C_Peru%E2%80%A6the_Plaza_de_Armas_de_Lima_by_day_%288444360764%29.jpg/960px-Lima%2C_Peru%E2%80%A6the_Plaza_de_Armas_de_Lima_by_day_%288444360764%29.jpg",  # Plaza Mayor, Lima
    "Lisbon": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Torre_Bel%C3%A9m_April_2009-4a.jpg/960px-Torre_Bel%C3%A9m_April_2009-4a.jpg",  # Belém Tower
    "Ljubljana": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Ljubljanski_grad_in_Grajski_gri%C4%8D.jpg/960px-Ljubljanski_grad_in_Grajski_gri%C4%8D.jpg",  # Ljubljana Castle
    "Madrid": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Palacio_Real_de_Madrid_Julio_2016_%28cropped%29.jpg/960px-Palacio_Real_de_Madrid_Julio_2016_%28cropped%29.jpg",  # Royal Palace of Madrid
    "Manila": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Baluartillo_de_San_Jos%C3%A9%2C_Manila%2C_Filipinas%2C_2023-08-26%2C_DD_41.jpg/960px-Baluartillo_de_San_Jos%C3%A9%2C_Manila%2C_Filipinas%2C_2023-08-26%2C_DD_41.jpg",  # Intramuros
    "Marrakech": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Marokko0112_%28retouched%29.jpg/960px-Marokko0112_%28retouched%29.jpg",  # Koutoubia Mosque
    "Medellín": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Edificio_Coltejer-Medellin.jpg/960px-Edificio_Coltejer-Medellin.jpg",  # Coltejer Building
    "Mexico City": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Bellas_Artes_01.jpg/960px-Bellas_Artes_01.jpg",  # Palacio de Bellas Artes
    "Munich": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg/960px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg",  # Marienplatz
    "Naha (Okinawa)": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Naha_Okinawa_Japan_Shuri-Castle-01.jpg/960px-Naha_Okinawa_Japan_Shuri-Castle-01.jpg",  # Shuri Castle
    "Nakhon Ratchasima": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Phimai_%28III%29.jpg/960px-Phimai_%28III%29.jpg",  # Phimai Historical Park
    "Novi Sad": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f5/Petrovaradin_Fortress_%28P%C3%A9terv%C3%A1radi_v%C3%A1r%2C_Peterwardein%29.JPG/960px-Petrovaradin_Fortress_%28P%C3%A9terv%C3%A1radi_v%C3%A1r%2C_Peterwardein%29.JPG",  # Petrovaradin Fortress
    "Oaxaca": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Monte_Alban_West_Side_Platform.jpg/960px-Monte_Alban_West_Side_Platform.jpg",  # Monte Albán
    "Osaka": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Osaka_Castle_03bs3200.jpg/960px-Osaka_Castle_03bs3200.jpg",  # Osaka Castle
    "Panama City": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Cinta_Costera_Panam%C3%A1.jpg/960px-Cinta_Costera_Panam%C3%A1.jpg",  # Cinta Costera skyline
    "Penang": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Kek_Lok_Si_at_dusk.jpg/960px-Kek_Lok_Si_at_dusk.jpg",  # Kek Lok Si
    "Phuket": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Dramatic_karst_landscape_of_Phang_Nga_Bay%2C_Thailand.jpg/960px-Dramatic_karst_landscape_of_Phang_Nga_Bay%2C_Thailand.jpg",  # Phang Nga Bay
    "Playa del Carmen": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/PlayadelCarmen3.png/960px-PlayadelCarmen3.png",  # Playa del Carmen
    "Portimão": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Praia_da_Rocha_2014-09-11.jpg/960px-Praia_da_Rocha_2014-09-11.jpg",  # Praia da Rocha
    "Porto": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Dom_Lu%C3%ADs_I_Bridge_%2836961760686%29.jpg/960px-Dom_Lu%C3%ADs_I_Bridge_%2836961760686%29.jpg",  # Dom Luís I Bridge
    "Prague": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Prague_07-2016_view_from_Lesser_Town_Tower_of_Charles_Bridge_img3.jpg/960px-Prague_07-2016_view_from_Lesser_Town_Tower_of_Charles_Bridge_img3.jpg",  # Charles Bridge
    "Recife": "https://upload.wikimedia.org/wikipedia/commons/a/a0/Recife_bom_jesus.jpg",  # Recife Antigo
    "Rio de Janeiro": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Christ_the_Redeemer_-_Cristo_Redentor.jpg/960px-Christ_the_Redeemer_-_Cristo_Redentor.jpg",  # Christ the Redeemer (statue)
    "San José": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Costa_Rica-Teatro_Nacional.JPG/960px-Costa_Rica-Teatro_Nacional.JPG",  # National Theatre of Costa Rica
    "Santiago": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Costanera_Center_at_evening_%28cropped%29.jpg/960px-Costanera_Center_at_evening_%28cropped%29.jpg",  # Gran Torre Santiago
    "Seoul": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/%EA%B4%91%ED%99%94%EB%AC%B8_%EC%9B%94%EB%8C%80.jpg/960px-%EA%B4%91%ED%99%94%EB%AC%B8_%EC%9B%94%EB%8C%80.jpg",  # Gyeongbokgung
    "Singapore": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Marina_Bay_Sands_%28I%29.jpg/960px-Marina_Bay_Sands_%28I%29.jpg",  # Marina Bay Sands
    "Sofia": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Catedral_de_Alejandro_Nevski_--_2019_--_Sof%C3%ADa%2C_Bulgaria.jpg/960px-Catedral_de_Alejandro_Nevski_--_2019_--_Sof%C3%ADa%2C_Bulgaria.jpg",  # Alexander Nevsky Cathedral, Sofia
    "Split": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Croatia-01239_-_The_Peristil_%289551533404%29.jpg/960px-Croatia-01239_-_The_Peristil_%289551533404%29.jpg",  # Diocletian's Palace
    "Taipei": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Taipei_101_from_Xiangshan_20250905.jpg/960px-Taipei_101_from_Xiangshan_20250905.jpg",  # Taipei 101
    "Tallinn": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Catedral_de_Alejandro_Nevsky%2C_Tallin%2C_Estonia%2C_2012-08-11%2C_DD_46.JPG/960px-Catedral_de_Alejandro_Nevsky%2C_Tallin%2C_Estonia%2C_2012-08-11%2C_DD_46.JPG",  # Alexander Nevsky Cathedral, Tallinn
    "Tashkent": "https://upload.wikimedia.org/wikipedia/en/thumb/5/5c/Toshkent_teleminorasi.jpg/960px-Toshkent_teleminorasi.jpg",  # Tashkent TV Tower
    "Tbilisi": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Tbilisi_IMG_8846_1920.jpg/960px-Tbilisi_IMG_8846_1920.jpg",  # Narikala
    "Timisoara": "https://upload.wikimedia.org/wikipedia/en/thumb/4/4e/Catedrala_Mitropolitana%2C_Timisoara.jpg/960px-Catedrala_Mitropolitana%2C_Timisoara.jpg",  # Timișoara Orthodox Cathedral
    "Tokyo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/58/Tokyo_Tower_2023.jpg/960px-Tokyo_Tower_2023.jpg",  # Tokyo Tower
    "Tunis": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Minaret_et_patio_de_la_mosqu%C3%A9e_Zitouna_au_centre_de_la_M%C3%A9dina_de_Tunis.jpg/960px-Minaret_et_patio_de_la_mosqu%C3%A9e_Zitouna_au_centre_de_la_M%C3%A9dina_de_Tunis.jpg",  # Al-Zaytuna Mosque
    "Valencia": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/2002_wurde_das_Ozeaneum_in_Valencia_er%C3%B6ffnet._14.jpg/960px-2002_wurde_das_Ozeaneum_in_Valencia_er%C3%B6ffnet._14.jpg",  # L'Oceanogràfic
    "Varna": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Varna_Cathedral_-_2.jpg/960px-Varna_Cathedral_-_2.jpg",  # Dormition Cathedral, Varna
    "Vilnius": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Vilnius_Cathedral_20.jpg/960px-Vilnius_Cathedral_20.jpg",  # Vilnius Cathedral
    "Warsaw": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Pa%C5%82ac_Kultury_i_Nauki_2019.jpg/960px-Pa%C5%82ac_Kultury_i_Nauki_2019.jpg",  # Palace of Culture and Science
    "Weligama": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/Weligama_Beach_in_Sri_Lanka.jpg/960px-Weligama_Beach_in_Sri_Lanka.jpg",  # Weligama Beach
    "Wrocław": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Old_Town_Hall_in_Wroc%C5%82aw%2C_September_2022_07.jpg/960px-Old_Town_Hall_in_Wroc%C5%82aw%2C_September_2022_07.jpg",  # Wrocław Town Hall
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
                    j = r.json()
                    thumb = (j.get("thumbnail") or {}).get("source", "")
                    if thumb:
                        # only upscale if the original is big enough (else 404)
                        orig_w = (j.get("originalimage") or {}).get("width", 0)
                        if orig_w >= 640:
                            thumb = thumb.replace("/320px-", "/640px-")
                        return city, thumb
                    break  # page exists but has no image — don't retry
            except Exception:
                continue
        return city, ""

    try:
        with ThreadPoolExecutor(max_workers=8) as ex:
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
    font-size: 72px; opacity: 0.45;
}
.tile-fallback-flag img { border-radius: 6px; }
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
    flag  = flag_img(row["Country"], h=14)
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
    flag  = flag_img(row["Country"], h=15)
    score = row["Weighted Score"]
    sc    = score_cls(score)
    if img_url:
        bg       = f"background-image:url('{img_url}');"
        fallback = ""
    else:
        bg       = "background:linear-gradient(135deg,#1a1a1a 0%,#26160a 100%);"
        fallback = f'<div class="tile-fallback-flag">{flag_img(row["Country"], h=54)}</div>'
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

images = {c: CITY_IMAGES.get(c, "") for c in df["City"]}
_missing = tuple(c for c in df["City"] if not images[c])
if _missing:  # fallback to Wikipedia API for any city not in the curated dict
    images.update(fetch_city_images(_missing))

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
