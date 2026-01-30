# Ejemplo Dashboard con mapa de Valle del cauca y sus municipios
# Un punto amarillo en el municipio que no llueve y
# un punto azul en el municipio que llueve
# pip install dash pandas requests pydeck
# pip 25.3.1
# Python 3.13.1

import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import dash
from dash import html, dash_table
import pydeck as pdk

# ---------------- SESIÓN REQUEST ----------------
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

# ---------------- MUNICIPIOS VALLE ----------------
MUNICIPIOS_VALLE = {
    "Alcalá": (3.5013, -76.4976),
    "Andalucía": (3.0020, -76.5845),
    "Ansermanuevo": (4.0261, -76.2705),
    "Argelia": (3.8794, -76.0153),
    "Bolívar": (4.0913, -76.1362),
    "Buenaventura": (3.8975, -77.0733),
    "Bugalagrande": (4.0481, -76.1812),
    "Caicedonia": (4.2877, -76.1005),
    "Cali": (3.4516, -76.5320),
    "Calima": (4.5028, -76.0722),
    "Candelaria": (3.2933, -76.4621),
    "Cartago": (4.7533, -75.9365),
    "Dagua": (3.7940, -76.8412),
    "El Águila": (4.0470, -76.1064),
    "El Cairo": (4.4169, -76.2821),
    "El Cerrito": (3.6082, -76.3205),
    "Florida": (3.9227, -76.3950),
    "Ginebra": (4.1393, -76.2191),
    "Guacarí": (3.9727, -76.2850),
    "Jamundí": (3.2156, -76.5293),
    "La Cumbre": (3.5386, -76.5210),
    "La Unión": (4.0336, -76.1927),
    "La Victoria": (3.7819, -76.4502),
    "Obando": (3.6170, -76.3050),
    "Palmira": (3.5392, -76.3031),
    "Pradera": (3.5627, -76.2923),
    "Restrepo": (3.9634, -76.2142),
    "Riofrío": (3.9283, -76.2217),
    "Roldanillo": (4.4004, -76.0097),
    "San Pedro": (3.8477, -76.2919),
    "Sevilla": (4.2247, -75.9874),
    "Toro": (4.0904, -76.0925),
    "Trujillo": (4.1225, -76.1502),
    "Tuluá": (4.0845, -76.1968),
    "Ulloa": (3.8630, -76.1573),
    "Versalles": (4.0165, -76.1155),
    "Vijes": (3.7439, -76.2211),
    "Yotoco": (3.5215, -76.3433),
    "Yumbo": (3.5676, -76.5080),
    "Zarzal": (4.1237, -76.1165)
}

# ---------------- API OPEN-METEO ----------------
def obtener_datos_lluvia(municipios_dict):
    datos = []
    for municipio, (lat, lon) in municipios_dict.items():
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}"
            f"&longitude={lon}"
            f"&current_weather=true"
            f"&hourly=precipitation"
            f"&timezone=auto"
        )
        try:
            response = session.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            current = data.get("current", {})
            temperatura = current.get("temperature_2m")
            lluvia = current.get("precipitation", 0)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error consultando {municipio}: {e}")
            temperatura = None
            lluvia = 0

        datos.append({
            "Municipio": municipio,
            "Temperatura (°C)": temperatura,
            "Lluvia (mm)": lluvia,
            "Latitud": lat,
            "Longitud": lon,
            "Está lloviendo": "Sí" if lluvia > 0 else "No"
        })
    return pd.DataFrame(datos)

# ---------------- MAPA PYDECK (SIN CAMBIOS) ----------------
def crear_mapa_pydeck(df):
    min_size = 500
    max_size = 3000
    max_lluvia = df["Lluvia (mm)"].max() if df["Lluvia (mm)"].max() > 0 else 1

    df["size"] = df["Lluvia (mm)"].fillna(0).apply(
        lambda x: min_size + (x / max_lluvia) * (max_size - min_size)
    )

    def color_por_lluvia(lluvia):
        ratio = lluvia / max_lluvia
        r = int(255 * (1 - ratio))
        g = int(255 * (1 - ratio))
        b = int(139 * ratio)
        return [r, g, b]

    df["color"] = df["Lluvia (mm)"].apply(color_por_lluvia)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["Longitud", "Latitud"],
        get_fill_color="color",
        get_radius="size",
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=3.8,
        longitude=-76.5,
        zoom=8,
        pitch=45
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={"text": "{Municipio}\nTemp: {Temperatura (°C)} °C\nLluvia: {Lluvia (mm)} mm\nEstá lloviendo: {Está lloviendo}"}
    )

    archivo = "mapa_lluvias_valle_pydeck.html"
    deck.to_html(archivo, open_browser=False)
    return archivo

# ---------------- DASHBOARD ----------------
df_municipios = obtener_datos_lluvia(MUNICIPIOS_VALLE)
df_table = df_municipios.drop(columns=["color"], errors="ignore")
mapa_html = crear_mapa_pydeck(df_municipios)

app = dash.Dash(__name__)
fecha_hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

app.layout = html.Div(
    style={
        "backgroundColor": "black",
        "color": "red",
        "padding": "15px",
        "fontFamily": "Arial"
    },
    children=[
        html.H1("Dashboard con mapa de lluvias en municipios de Colombia"),
        html.H4(f"Fecha y hora actual: {fecha_hora_actual}"),

        html.H3("Tabla con datos de lluvia"),
        dash_table.DataTable(
            data=df_table.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df_table.columns],
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "center",
                "padding": "6px",
                "backgroundColor": "#e0e0e0",
                "color": "black"
            },
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold"
            },
            page_size=10
        ),

        html.H3("Mapa de lluvias (amarillo → azul según intensidad)"),
        html.Iframe(
            srcDoc=open(mapa_html, "r", encoding="utf-8").read(),
            width="100%",
            height="800"
        )
    ]
)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4321, debug=True)
