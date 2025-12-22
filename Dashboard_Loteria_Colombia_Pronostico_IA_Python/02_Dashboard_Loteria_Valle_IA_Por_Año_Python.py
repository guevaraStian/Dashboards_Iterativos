# En el siguiente codigo se muestra un software que le pide
# a una API la informacion de las loterias mas recientes
# Luego filtra un año en especifico y crea un dashboar
# con IA para el pronostico del siguiente numero y dashboar
# Con los datos recogidos, primero se instalan librerias
# pip install pandas dash sklearn
import pandas as pd
import requests
from datetime import datetime, timedelta
from dash import Dash, html, dcc
from dash import dash_table
import plotly.express as px
from sklearn.linear_model import LinearRegression

# Se agregan las variables relacionadas a la api
BASE_URL = "https://api-resultadosloterias.com/api/results/"
start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 20)

all_data = []

# Se filtra la informacion por inicio de los datos hasta el fin de los datos
current_date = start_date
while current_date <= end_date:
    url = BASE_URL + current_date.strftime("%Y-%m-%d")
    response = requests.get(url)
    json_data = response.json()

    if json_data.get('status') == 'success' and 'data' in json_data:
        all_data.extend(json_data['data'])

    current_date += timedelta(days=1)

# Se crea el dataframe
df = pd.DataFrame(all_data)

# Filtrar solo loteria del valle
df = df[df['lottery'] == 'VALLE']

df['result'] = df['result'].astype(int)
df['time'] = pd.to_datetime(df['date'])
df = df.sort_values('time')

# Timestamp para predicción
df['timestamp'] = df['time'].apply(lambda x: x.timestamp())

# Se calcula el pronostico del siguiente dia
X = df['timestamp'].values.reshape(-1, 1)
y = df['result'].values

model = LinearRegression()
model.fit(X, y)

# Pronóstico siguiente día
next_time = df['timestamp'].iloc[-1] + 86400
next_pred = model.predict([[next_time]])[0]

# Se crea la grafica con la informacion
fig = px.line(
    df,
    x='time',
    y='result',
    markers=True,
    title='Resultados Valle - Año 2025'
)

fig.update_layout(
    plot_bgcolor='black',
    paper_bgcolor='black',
    font_color='white',
    xaxis_title='Fecha',
    yaxis_title='Número'
)

# El siguiente codigo es sore el dashboard
app = Dash(__name__)

app.layout = html.Div([

    html.H1(
        'Loteria del VALLE - año 2025',
        style={'color': 'white', 'textAlign': 'center'}
    ),

    html.H3(
        f'Pronóstico siguiente número: {next_pred:.2f}',
        style={'color': 'white', 'textAlign': 'center'}
    ),

    # ---------------- TABLA ----------------
    dash_table.DataTable(
        data=df.drop(columns=['timestamp']).to_dict('records'),
        columns=[{"name": i, "id": i} for i in df.columns if i != 'timestamp'],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': 'red',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_cell={
            'textAlign': 'center',
            'padding': '5px'
        }
    ),

    # ---------------- GRÁFICA ----------------
    dcc.Graph(
        figure=fig,
        style={'height': '600px'}
    )

], style={'backgroundColor': 'black', 'padding': '20px', 'minHeight': '100vh'})

# Main de ejecucion
if __name__ == '__main__':
    app.run(debug=True)
