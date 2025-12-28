# En el siguiente codigo se muestra una forma sencilla de crear
# Un dashboard con los datos de los partidos de ligas europeas
# pip install flask pandas requests lxml beautifulsoup4
import requests    
import pandas as pd
import numpy as np
from dash import Dash, html, dcc, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from sklearn.neural_network import MLPRegressor
from datetime import datetime

# Se guarda informacion en variables estaticas
fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

LIGAS = {
    "Premier League (ING)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/en.1.json",
    "La Liga (ESP)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/es.1.json",
    "Serie A (ITA)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/it.1.json",
    "Bundesliga (GER)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/de.1.json",
    "Ligue 1 (FRA)": "https://raw.githubusercontent.com/openfootball/football.json/master/2024-25/fr.1.json"
}

# Se descargan los datos de la API de resultados
def cargar_liga(url):
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data.get("matches", []))

    df["Team1"] = df["team1"].apply(lambda x: x.get("name") if isinstance(x, dict) else x)
    df["Team2"] = df["team2"].apply(lambda x: x.get("name") if isinstance(x, dict) else x)
    df[["Goals1", "Goals2"]] = df["score"].apply(
        lambda s: s["ft"] if s and s.get("ft") else [None, None]
    ).apply(pd.Series)
    df["Date"] = pd.to_datetime(df["date"], errors="coerce")
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

# Codigo de creacion del dashboard
app = Dash(__name__)

app.layout = html.Div(
    style={'backgroundColor': 'black', 'color': 'red', 'padding': '20px'},
    children=[

        html.H2("Análisis Equipo vs Equipo (IA)", style={'textAlign': 'center'}),
        html.Div(f"Fecha actual: {fecha_actual}", style={'textAlign': 'center'}),
        html.Div(id="rango-fechas", style={'textAlign': 'center', 'fontWeight': 'bold'}),

        html.Br(),

        dcc.Dropdown(
            id='liga',
            options=[{'label': k, 'value': k} for k in LIGAS],
            value=list(LIGAS.keys())[0],
            style={'color': 'black'}
        ),

        html.Br(),
        dcc.Dropdown(id='equipoA', placeholder="Equipo A", style={'color': 'black'}),
        html.Br(),
        dcc.Dropdown(id='equipoB', placeholder="Equipo B", style={'color': 'black'}),

        html.Hr(style={'borderColor': 'red'}),

        html.Div(id='pronostico-ia', style={'textAlign': 'center', 'fontWeight': 'bold'}),
        html.Br(),
        html.Div(id='probabilidades-ia', style={'textAlign': 'center'}),

        html.Hr(style={'borderColor': 'red'}),

        html.H3(id="tituloA", style={'backgroundColor': 'red', 'color': 'black', 'fontWeight': 'bold', 'padding': '5px'}),
        dash_table.DataTable(
            id='tablaA',
            page_size=8,
            style_header={'backgroundColor': 'red', 'fontWeight': 'bold', 'color': 'black'},
            style_data={'backgroundColor': 'lightgrey', 'color': 'black'}
        ),

        html.Hr(style={'borderColor': 'red'}),

        html.H3(id="tituloB", style={'backgroundColor': 'red', 'color': 'black', 'fontWeight': 'bold', 'padding': '5px'}),
        dash_table.DataTable(
            id='tablaB',
            page_size=8,
            style_header={'backgroundColor': 'red', 'fontWeight': 'bold', 'color': 'black'},
            style_data={'backgroundColor': 'lightgrey', 'color': 'black'}
        ),

        html.Hr(style={'borderColor': 'red'}),

        html.H3(id="tituloBarA", style={'backgroundColor': 'red', 'color': 'black', 'fontWeight': 'bold', 'padding': '5px'}),
        dcc.Graph(id='barA'),

        html.Hr(style={'borderColor': 'red'}),

        html.H3(id="tituloBarB", style={'backgroundColor': 'red', 'color': 'black', 'fontWeight': 'bold', 'padding': '5px'}),
        dcc.Graph(id='barB'),

        html.Hr(style={'borderColor': 'red'}),

        html.Div([
            html.Div(dcc.Graph(id='pieA_GF'), style={'width': '48%'}),
            html.Div(dcc.Graph(id='pieA_GC'), style={'width': '48%'})
        ], style={'display': 'flex', 'justifyContent': 'space-between'}),

        html.Br(),

        html.Div([
            html.Div(dcc.Graph(id='pieB_GF'), style={'width': '48%'}),
            html.Div(dcc.Graph(id='pieB_GC'), style={'width': '48%'})
        ], style={'display': 'flex', 'justifyContent': 'space-between'})
    ]
)

# Creacion de callback entre la base de datos y la interface
@app.callback(
    Output('equipoA', 'options'),
    Output('equipoA', 'value'),
    Input('liga', 'value')
)
def equiposA(liga):
    df = cargar_liga(LIGAS[liga])
    equipos = sorted(set(df.Team1) | set(df.Team2))
    return [{'label': e, 'value': e} for e in equipos], equipos[0]

@app.callback(
    Output('equipoB', 'options'),
    Output('equipoB', 'value'),
    Input('liga', 'value'),
    Input('equipoA', 'value')
)
def equiposB(liga, A):
    df = cargar_liga(LIGAS[liga])
    equipos = [e for e in sorted(set(df.Team1) | set(df.Team2)) if e != A]
    return [{'label': e, 'value': e} for e in equipos], equipos[0]

@app.callback(
    Output('pronostico-ia', 'children'),
    Output('probabilidades-ia', 'children'),
    Output('tablaA', 'data'),
    Output('tablaB', 'data'),
    Output('barA', 'figure'),
    Output('barB', 'figure'),
    Output('pieA_GF', 'figure'),
    Output('pieA_GC', 'figure'),
    Output('pieB_GF', 'figure'),
    Output('pieB_GC', 'figure'),
    Output('tituloA', 'children'),
    Output('tituloB', 'children'),
    Output('tituloBarA', 'children'),
    Output('tituloBarB', 'children'),
    Output('rango-fechas', 'children'),
    Input('liga', 'value'),
    Input('equipoA', 'value'),
    Input('equipoB', 'value')
)

# Funcion de actualizar la pagina
def actualizar(liga, A, B):

    df = cargar_liga(LIGAS[liga])

    fecha_min = df["Date"].min().strftime("%Y-%m-%d")
    fecha_max = df["Date"].max().strftime("%Y-%m-%d")

    def datos(eq):
        df_e = df[(df.Team1 == eq) | (df.Team2 == eq)]
        gf = df_e.apply(lambda r: r.Goals1 if r.Team1 == eq else r.Goals2, axis=1)
        gc = df_e.apply(lambda r: r.Goals2 if r.Team1 == eq else r.Goals1, axis=1)
        riv = df_e.apply(lambda r: r.Team2 if r.Team1 == eq else r.Team1, axis=1)

        resultado = df_e.apply(lambda r: 'G' if (r.Team1==eq and r.Goals1>r.Goals2) or (r.Team2==eq and r.Goals2>r.Goals1)
                               else ('E' if r.Goals1==r.Goals2 else 'P'), axis=1)

        tabla = pd.DataFrame({
            'Fecha': df_e['Date'].dt.strftime('%Y-%m-%d'),
            'Equipo 1': df_e['Team1'],
            'Goles Equipo 1': df_e['Goals1'],
            'Goles': gf,
            'Equipo 2': df_e['Team2'],
            'Goles Equipo 2': df_e['Goals2'],
            'Resultado': resultado
        })

        return df_e, gf, gc, riv, tabla

    dfA, gfA, gcA, rivA, tablaA = datos(A)
    dfB, gfB, gcB, rivB, tablaB = datos(B)

    X_A = np.arange(len(gfA)).reshape(-1, 1)
    X_B = np.arange(len(gfB)).reshape(-1, 1)

    modelA = MLPRegressor(max_iter=1000, random_state=42)
    modelB = MLPRegressor(max_iter=1000, random_state=42)

    modelA.fit(X_A, gfA)
    modelB.fit(X_B, gfB)

    predA = round(modelA.predict([[len(gfA)]])[0], 1)
    predB = round(modelB.predict([[len(gfB)]])[0], 1)

    pronostico = f"Pronóstico IA próximo partido: {A} {predA} - {predB} {B}"

    fuerzaA = gfA.mean() - gcA.mean()
    fuerzaB = gfB.mean() - gcB.mean()

    scores = np.exp([fuerzaA, 0.3, fuerzaB])
    probs = scores / scores.sum()

    prob_text = html.Div([
        html.Div(f"{A} gana: {probs[0]*100:.1f}%"),
        html.Div(f"Empate: {probs[1]*100:.1f}%"),
        html.Div(f"{B} gana: {probs[2]*100:.1f}%")
    ])

    # El siguiente codigo sirve para carcula un resultado H2H entre los equipos de futbol
    df_h2h = df[((df.Team1 == A) & (df.Team2 == B)) | ((df.Team1 == B) & (df.Team2 == A))]
    if not df_h2h.empty:
        gf_h2h_A = df_h2h.apply(lambda r: r.Goals1 if r.Team1 == A else r.Goals2, axis=1)
        gf_h2h_B = df_h2h.apply(lambda r: r.Goals2 if r.Team1 == A else r.Goals1, axis=1)
        X_h2h = np.arange(len(df_h2h)).reshape(-1,1)

        model_h2h_A = MLPRegressor(max_iter=1000, random_state=42)
        model_h2h_B = MLPRegressor(max_iter=1000, random_state=42)
        model_h2h_A.fit(X_h2h, gf_h2h_A)
        model_h2h_B.fit(X_h2h, gf_h2h_B)

        pred_h2h_A = round(model_h2h_A.predict([[len(df_h2h)]])[0],1)
        pred_h2h_B = round(model_h2h_B.predict([[len(df_h2h)]])[0],1)

        h2h_text = html.H2(f"H2H IA: {A} {pred_h2h_A} - {pred_h2h_B} {B}")
    else:
        h2h_text = html.H2("H2H IA: No hay partidos anteriores entre estos equipos")

    # Las siguientes funciones relacionadas con las graficas
    def pie(names, values, title):
        fig = px.pie(names=names, values=values, hole=0.3, title=title)
        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='red')
        return fig

    def barras(riv, gf, gc):
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=riv,
            y=gf,
            name='GF',
            marker_color='green',
            text=gf,
            textposition='inside',
            textfont_color='black'
        ))
        fig.add_trace(go.Bar(
            x=riv,
            y=gc,
            name='GC',
            marker_color='red',
            text=gc,
            textposition='inside',
            textfont_color='black'
        ))
        fig.update_layout(
            barmode='group',
            plot_bgcolor='black',
            paper_bgcolor='black',
            font_color='red'
        )
        return fig

    return (
        pronostico,
        html.Div([prob_text, h2h_text]),  # <- Aquí se muestra H2H debajo de probabilidades
        tablaA.to_dict("records"),
        tablaB.to_dict("records"),
        barras(rivA, gfA, gcA),
        barras(rivB, gfB, gcB),
        pie(rivA, gfA, f"{A} - Goles a Favor"),
        pie(rivA, gcA, f"{A} - Goles en Contra"),
        pie(rivB, gfB, f"{B} - Goles a Favor"),
        pie(rivB, gcB, f"{B} - Goles en Contra"),
        f"Histórico Completo - {A}",
        f"Histórico Completo - {B}",
        f"Goles por Rival - {A}",
        f"Goles por Rival - {B}",
        f"Datos desde {fecha_min} hasta {fecha_max}"
    )

# Main de ejecucion
if __name__ == "__main__":
    app.run(debug=True)
