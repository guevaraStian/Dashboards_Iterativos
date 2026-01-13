import requests
import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.linear_model import LinearRegression

# =========================
# CONSULTA A LA API
# =========================
URL = "https://www.datos.gov.co/resource/m8fd-ahd9.json"
params = {"$limit": 10000000}

response = requests.get(URL, params=params)
response.raise_for_status()
df = pd.DataFrame(response.json())

# =========================
# LIMPIEZA DE DATOS
# =========================
df.rename(columns={"fecha_hecho": "fecha_hecho"}, inplace=True)
df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")
df["anio"] = df["fecha_hecho"].dt.year
df["departamento"] = df["departamento"].str.upper()
df = df.dropna(subset=["anio", "departamento"])
df["anio"] = df["anio"].astype(int)

anios_disponibles = sorted(df["anio"].unique())
departamentos_colombia = sorted(df["departamento"].unique())

# =========================
# CENTROIDES
# =========================
centroides_departamentos = {
    "ANTIOQUIA": [-75.56, 6.25],
    "CUNDINAMARCA": [-74.07, 4.59],
    "VALLE DEL CAUCA": [-76.52, 3.43],
    "ATLANTICO": [-75.52, 10.42],
    "SANTANDER": [-73.11, 7.12],
    "BOLIVAR": [-75.50, 10.40],
    "META": [-73.61, 4.15],
    "NARIÑO": [-77.27, 1.21],
    "CESAR": [-73.25, 10.98],
    "TOLIMA": [-75.23, 4.43],
    "BOGOTA D.C.": [-74.07, 4.71]
}

# =========================
# PRONÓSTICO ML
# =========================
def calcular_predicciones_2026():
    df_totales = df.groupby(["departamento", "anio"]).size().reset_index(name="homicidios")
    resultados = []

    for depto in departamentos_colombia:
        datos = df_totales[df_totales["departamento"] == depto]

        if len(datos) >= 2:
            X = datos[["anio"]]
            y = datos["homicidios"]
            modelo = LinearRegression()
            modelo.fit(X, y)
            pred = max(int(modelo.predict([[2026]])[0]), 0)
        else:
            pred = 0

        resultados.append({
            "departamento": depto,
            "homicidios_estimados_2026": pred
        })

    return pd.DataFrame(resultados).sort_values(
        "homicidios_estimados_2026", ascending=False
    )

df_predicciones = calcular_predicciones_2026()

# =========================
# DASHBOARD
# =========================
app = dash.Dash(__name__)
fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

app.layout = html.Div(
    style={
        "backgroundColor": "black",
        "color": "red",
        "minHeight": "100vh",
        "padding": "20px"
    },
    children=[
        html.H1("Homicidios en Colombia", style={"textAlign": "center"}),
        html.H4(f"Fecha y hora actual: {fecha_actual}", style={"textAlign": "center"}),

        dcc.Dropdown(
            id="select-anio",
            options=[{"label": str(a), "value": a} for a in anios_disponibles],
            value=anios_disponibles[0],
            style={"color": "black"}
        ),

        html.H3("Registros detallados del año seleccionado"),
        dash_table.DataTable(
            id="tabla-homicidios",
            page_size=10,
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold"
            },
            style_data={
                "backgroundColor": "gray",
                "color": "black"
            },
            style_cell={
                "border": "1px solid black"
            }
        ),

        html.H3("Total de homicidios por departamento"),
        dcc.Graph(id="grafica-barras"),

        html.H3("Distribución geográfica de homicidios por departamento"),
        dcc.Graph(id="mapa-colombia", style={"height": "700px"}),

        html.H2("Pronóstico total de homicidios por departamento para 2026"),
        dash_table.DataTable(
            data=df_predicciones.to_dict("records"),
            columns=[
                {"name": "Departamento", "id": "departamento"},
                {"name": "Homicidios estimados 2026", "id": "homicidios_estimados_2026"}
            ],
            page_action="none",
            style_table={"height": "600px", "overflowY": "auto"},
            style_header={
                "backgroundColor": "red",
                "color": "black",
                "fontWeight": "bold"
            },
            style_data={
                "backgroundColor": "gray",
                "color": "black"
            },
            style_cell={
                "border": "1px solid black"
            }
        )
    ]
)

# =========================
# CALLBACK
# =========================
@app.callback(
    [
        Output("tabla-homicidios", "data"),
        Output("tabla-homicidios", "columns"),
        Output("grafica-barras", "figure"),
        Output("mapa-colombia", "figure")
    ],
    Input("select-anio", "value")
)
def actualizar_dashboard(anio):
    df_anio = df[df["anio"] == anio]
    conteo = df_anio.groupby("departamento").size().reset_index(name="cantidad")

    fig_barras = px.bar(
        conteo,
        x="departamento",
        y="cantidad",
        color="departamento",
        text="cantidad",
        title=f"Homicidios por departamento en {anio}",
        template="plotly_dark"
    )
    fig_barras.update_traces(textposition="inside")
    fig_barras.update_layout(
        showlegend=False,
        font=dict(color="red"),
        plot_bgcolor="black",
        paper_bgcolor="black"
    )

    lons, lats, sizes, texts = [], [], [], []
    max_val = conteo["cantidad"].max() if not conteo.empty else 1

    for _, r in conteo.iterrows():
        if r["departamento"] in centroides_departamentos:
            lon, lat = centroides_departamentos[r["departamento"]]
            lons.append(lon)
            lats.append(lat)
            sizes.append(10 + (r["cantidad"] / max_val) * 30)
            texts.append(f"{r['departamento']}: {r['cantidad']}")

    fig_mapa = go.Figure(go.Scattermapbox(
        lon=lons,
        lat=lats,
        text=texts,
        mode="markers+text",
        marker=dict(size=sizes, color="red")
    ))

    fig_mapa.update_layout(
        title="Mapa de homicidios por departamento",
        mapbox_style="open-street-map",
        mapbox_zoom=4.5,
        mapbox_center={"lat": 4.5, "lon": -74},
        paper_bgcolor="black",
        font=dict(color="red")
    )

    return (
        df_anio.to_dict("records"),
        [{"name": c, "id": c} for c in df_anio.columns],
        fig_barras,
        fig_mapa
    )

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
