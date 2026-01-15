# DASHBOARD DE HOMICIDIOS COLOMBIA POR DEPARTAMENTO
# CON INTELIGENCIA ARTIFICIAL, MACHINE LEARNING Y REGRESION LINEAL
# TAMBIEN HAY GRAFICAS DEL DASHBOARD FILTRADA POR AÑO, MES Y DEPARTAMENTO
# TAMBIEN HAY UN MAPA QUE MUESTRAN LOS DATOS POR DIA

import requests
import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

# A continuacion se guardan las variables relacionadas con la consulta a la api
URL = "https://www.datos.gov.co/resource/m8fd-ahd9.json"
params = {"$limit": 1000000}

response = requests.get(URL, params=params)
response.raise_for_status()
data = response.json()
df = pd.DataFrame(data)

# Se hace limpieza de datos 
posibles_fechas = ["fecha_hecho", "fecha", "fecha_del_hecho"]
col_fecha = next((c for c in posibles_fechas if c in df.columns), None)

if col_fecha is None:
    raise Exception("(-) No se encontró columna de fecha en el dataset")

df.rename(columns={col_fecha: "fecha_hecho"}, inplace=True)
df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")

df["anio"] = df["fecha_hecho"].dt.year
df["mes"] = df["fecha_hecho"].dt.month
df["dia"] = df["fecha_hecho"].dt.day

df["departamento"] = df["departamento"].str.upper()
df = df.dropna(subset=["anio", "mes", "dia", "departamento"])

df[["anio", "mes", "dia"]] = df[["anio", "mes", "dia"]].astype(int)
anios_disponibles = sorted(df["anio"].unique())

# Se indica las coordenadas en el mapa de los departamentos colombia
centroides_departamentos = {
    "AMAZONAS": [-69.9333, -1.4433],
    "ANTIOQUIA": [-75.5636, 6.2518],
    "ARAUCA": [-70.7333, 7.0833],
    "ATLANTICO": [-75.5247, 10.4230],
    "BOLIVAR": [-75.5000, 10.4000],
    "BOYACA": [-73.3500, 5.5500],
    "CALDAS": [-75.5138, 5.0703],
    "CAQUETA": [-75.6667, 1.5833],
    "CASANARE": [-71.7333, 5.3667],
    "CAUCA": [-76.0000, 2.5000],
    "CESAR": [-73.2500, 10.9833],
    "CHOCO": [-76.6413, 5.6936],
    "CORDOBA": [-75.8800, 8.7700],
    "CUNDINAMARCA": [-74.0758, 4.5981],
    "GUAINIA": [-69.7500, 2.5667],
    "GUAVIARE": [-72.6333, 2.5667],
    "HUILA": [-75.2800, 2.9300],
    "LA GUAJIRA": [-72.9000, 11.5400],
    "MAGDALENA": [-74.2500, 10.5000],
    "META": [-73.6140, 4.1560],
    "NARIÑO": [-77.2719, 1.2141],
    "NORTE DE SANTANDER": [-72.4967, 7.8891],
    "PUTUMAYO": [-76.5417, 0.1521],
    "QUINDIO": [-75.7688, 4.5617],
    "RISARALDA": [-75.6946, 4.8517],
    "SAN ANDRES Y PROVIDENCIA": [-81.7000, 12.5847],
    "SANTANDER": [-73.1198, 7.1254],
    "SUCRE": [-75.3977, 9.3070],
    "TOLIMA": [-75.2322, 4.4359],
    "VALLE DEL CAUCA": [-76.5225, 3.4372],
    "VAUPES": [-70.2500, 1.5833],
    "VICHADA": [-69.1000, 4.6000],
}

# Se procede a crear el dashboard
app = dash.Dash(__name__)
fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# ESTILOS TABLAS
estilo_header = {
    "backgroundColor": "red",
    "color": "black",
    "fontWeight": "bold",
    "textAlign": "center"
}

estilo_celda = {
    "backgroundColor": "lightgray",
    "color": "black",
    "textAlign": "left",
    "fontSize": "12px"
}

app.layout = html.Div(
    style={"width": "95%", "margin": "auto", "backgroundColor": "black", "color": "red"},
    children=[
        html.H1("Homicidios en Colombia", style={"textAlign": "center"}),
        html.H4(f"Fecha actual: {fecha_actual}", style={"textAlign": "center"}),

        html.Label("Año"),
        dcc.Dropdown(id="select-anio",
                     options=[{"label": a, "value": a} for a in anios_disponibles],
                     value=anios_disponibles[0]),

        html.Label("Mes"),
        dcc.Dropdown(id="select-mes"),

        html.Label("Día"),
        dcc.Dropdown(id="select-dia"),

        html.H3("Registros de homicidios para la fecha seleccionada"),
        dash_table.DataTable(
            id="tabla-homicidios",
            page_size=10,
            style_header=estilo_header,
            style_cell=estilo_celda,
            style_table={"overflowX": "auto"}
        ),

        dcc.Graph(id="grafica-barras"),
        dcc.Graph(id="mapa-colombia"),

        html.H3(id="titulo-pronostico"),

        dash_table.DataTable(
            id="tabla-pronostico",
            page_action="none",
            style_header=estilo_header,
            style_cell=estilo_celda,
            style_table={"overflowX": "auto", "maxHeight": "600px", "overflowY": "auto"}
        )
    ]
)

# Se continua con la creacion de los callback
@app.callback(
    Output("select-mes", "options"),
    Output("select-mes", "value"),
    Input("select-anio", "value")
)
def actualizar_meses(anio):
    meses = sorted(df[df.anio == anio].mes.unique())
    return [{"label": m, "value": m} for m in meses], meses[0]

@app.callback(
    Output("select-dia", "options"),
    Output("select-dia", "value"),
    Input("select-anio", "value"),
    Input("select-mes", "value")
)
def actualizar_dias(anio, mes):
    dias = sorted(df[(df.anio == anio) & (df.mes == mes)].dia.unique())
    return [{"label": d, "value": d} for d in dias], dias[0]

# Callback main o principal
@app.callback(
    Output("tabla-homicidios", "data"),
    Output("tabla-homicidios", "columns"),
    Output("grafica-barras", "figure"),
    Output("mapa-colombia", "figure"),
    Output("tabla-pronostico", "data"),
    Output("tabla-pronostico", "columns"),
    Output("titulo-pronostico", "children"),
    Input("select-anio", "value"),
    Input("select-mes", "value"),
    Input("select-dia", "value")
)
def actualizar_dashboard(anio, mes, dia):

    df_f = df[(df.anio == anio) & (df.mes == mes) & (df.dia == dia)]

    columnas = [{"name": c, "id": c} for c in df_f.columns]
    data_tabla = df_f.to_dict("records")

    conteo = df_f.groupby("departamento").size().reset_index(name="cantidad")

    # GRÁFICA DE BARRAS CON COLORES Y VALORES DENTRO
    fig_barras = px.bar(
        conteo,
        x="departamento",
        y="cantidad",
        color="departamento",
        text="cantidad",
        title="Cantidad de homicidios por departamento",
        template="plotly_dark"
    )

    fig_barras.update_traces(
        textposition="inside",
        textfont_color="white"
    )

    fig_barras.update_layout(showlegend=False)

    # MAPA
    lons, lats, texts, sizes = [], [], [], []
    max_val = conteo["cantidad"].max() if not conteo.empty else 1

    for _, r in conteo.iterrows():
        if r.departamento in centroides_departamentos:
            lon, lat = centroides_departamentos[r.departamento]
            lons.append(lon)
            lats.append(lat)
            texts.append(f"{r.departamento}: {r.cantidad}")
            sizes.append(10 + (r.cantidad / max_val) * 30)

    fig_mapa = go.Figure(go.Scattermapbox(
        lon=lons,
        lat=lats,
        text=texts,
        mode="markers",
        marker=dict(size=sizes, color="red")
    ))

    fig_mapa.update_layout(
        title="Distribución geográfica de homicidios en Colombia",
        mapbox_style="open-street-map",
        mapbox_zoom=4.5,
        mapbox_center={"lat": 4.5, "lon": -74},
        template="plotly_dark"
    )

    # PRONÓSTICO
    pronostico = []
    for dep in df.departamento.unique():
        df_dep = df[(df.departamento == dep) & (df.mes == mes) & (df.dia == dia)]

        if len(df_dep) < 2:
            pred = 0
        else:
            df_agg = df_dep.groupby("anio").size().reset_index(name="cantidad")
            X = df_agg["anio"].values.reshape(-1, 1)
            y = df_agg["cantidad"].values
            model = LinearRegression()
            model.fit(X, y)
            pred = max(0, int(round(model.predict([[2026]])[0])))

        pronostico.append({"departamento": dep, "pronostico": pred})

    columnas_p = [
        {"name": "Departamento", "id": "departamento"},
        {"name": "Pronóstico de homicidios", "id": "pronostico"}
    ]

    titulo = f"Pronóstico de homicidios para el {dia}/{mes}/2026"

    return data_tabla, columnas, fig_barras, fig_mapa, pronostico, columnas_p, titulo

# El siguiente codigo es el main de ejecucion
if __name__ == "__main__":
    app.run(debug=True)
