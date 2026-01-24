# Ejemplo Dashboard con mapa de cali y sus comunas con 
# Un punto amarillo en la comuna que no llueve y 
# un punto azul en la comuna que llueve
# pip install pandas requests dash
# pip 25.3.1
# Python 3.13.1


import requests 
import pandas as pd
import dash
from dash import html, dcc, dash_table
import dash_leaflet as dl
from datetime import datetime

# En la siguientes lineas se muestra
# Diccionario con 22 comunas y coordenadas aproximadas
comunas = {
    "Comuna 1": {"lat": 3.45, "lon": -76.53},
    "Comuna 2": {"lat": 3.46, "lon": -76.53},
    "Comuna 3": {"lat": 3.44, "lon": -76.53},
    "Comuna 4": {"lat": 3.46, "lon": -76.50},
    "Comuna 5": {"lat": 3.47, "lon": -76.51},
    "Comuna 6": {"lat": 3.43, "lon": -76.50},
    "Comuna 7": {"lat": 3.42, "lon": -76.50},
    "Comuna 8": {"lat": 3.45, "lon": -76.51},
    "Comuna 9": {"lat": 3.43, "lon": -76.52},
    "Comuna 10": {"lat": 3.41, "lon": -76.51},
    "Comuna 11": {"lat": 3.42, "lon": -76.53},
    "Comuna 12": {"lat": 3.43, "lon": -76.54},
    "Comuna 13": {"lat": 3.46, "lon": -76.54},
    "Comuna 14": {"lat": 3.44, "lon": -76.49},
    "Comuna 15": {"lat": 3.40, "lon": -76.50},
    "Comuna 16": {"lat": 3.41, "lon": -76.51},
    "Comuna 17": {"lat": 3.39, "lon": -76.52},
    "Comuna 18": {"lat": 3.42, "lon": -76.54},
    "Comuna 19": {"lat": 3.43, "lon": -76.55},
    "Comuna 20": {"lat": 3.41, "lon": -76.55},
    "Comuna 21": {"lat": 3.42, "lon": -76.51},
    "Comuna 22": {"lat": 3.3533, "lon": -76.5354},
}

# Se consulta una base de datos de una api y se guardan los datos en variables
def obtener_lluvia(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation"
    try:
        response = requests.get(url, timeout=5)  # timeout 5 segundos
        data = response.json()
        return data.get("current_weather", {}).get("precipitation", 0)
    except requests.exceptions.Timeout:
        print(f"Timeout al consultar {lat}, {lon}")
        return 0
    except requests.exceptions.RequestException as e:
        print(f"Error al consultar {lat}, {lon}: {e}")
        return 0

# De los datos que vienen de la api base de datos se extraen los relacionados a lluvia
resultados = []
for comuna, coord in comunas.items():
    lluvia = obtener_lluvia(coord["lat"], coord["lon"])
    resultados.append({
        "Comuna": comuna,
        "Lat": coord["lat"],
        "Lon": coord["lon"],
        "Lluvia (mm)": lluvia
    })

df = pd.DataFrame(resultados)

# En la siguiente Función se crea color degradado amarillo → azul
def color_degradado(mm, max_mm=10):
    ratio = min(mm / max_mm, 1)
    r = int(255 * (1 - ratio))
    g = int(255 * (1 - ratio))
    b = int(255 * ratio)
    return f"rgb({r},{g},{b})"

# Crear lista de marcadores para el mapa
markers = [
    dl.CircleMarker(
        center=(row["Lat"], row["Lon"]),
        radius=10,
        color=color_degradado(row["Lluvia (mm)"]),
        fill=True,
        fillColor=color_degradado(row["Lluvia (mm)"]),
        fillOpacity=0.7,
        children=dl.Tooltip(f"{row['Comuna']}: {row['Lluvia (mm)']} mm")
    )
    for _, row in df.iterrows()
]

# Se inicializa el dash
app = dash.Dash(__name__)

# Obtener fecha y hora actual
fecha_hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

app.layout = html.Div(
    style={'backgroundColor': 'black', 'color': 'red', 'padding': '20px', 'fontFamily': 'Arial'},
    children=[
        html.H1("Lluvia en Comunas de Santiago de Cali"),
        html.Div(f"Fecha y hora actual: {fecha_hora_actual}", style={'marginBottom': '20px', 'fontSize': 16}),
        
        html.H2("Tabla de lluvias por comuna"),
        dash_table.DataTable(
            id='tabla-lluvia',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'black',
                'color': 'red',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_cell={
                'textAlign': 'center',
                'backgroundColor': 'black',
                'color': 'red'
            }
        ),
        
        html.H2("Mapa de lluvias por comuna"),
        dl.Map(
            children=[
                dl.TileLayer(),
                dl.LayerGroup(markers)
            ],
            center=(3.43722, -76.5225),
            zoom=11,
            style={'width': '100%', 'height': '600px'}
        )
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
