# En el siguiente codigo se muestra un dashboarda con IA de
# Loteria colombia consultando una API web y con los datos crear
# Una tabla, una grafica y un  pronostico del siguiente numero

import pandas as pd
import requests
from datetime import datetime
from dash import Dash, html, dcc
from dash import dash_table
import plotly.express as px
from sklearn.linear_model import LinearRegression
import io
import base64
from fpdf import FPDF

# Se consulta y se guardan los datos en variable json_data
API_URL = "https://api-resultadosloterias.com/api/results/2025-01-01"  # Reemplaza con tu URL real
response = requests.get(API_URL)
json_data = response.json()

if json_data.get('status') != 'success' or 'data' not in json_data:
    raise ValueError("La API no devolvió datos válidos")

data = json_data['data']

# En el siguiente codigo se crea el dataframe que es darle variables a cada columna
df = pd.DataFrame(data)
df['result'] = df['result'].astype(int)
df['time'] = pd.to_datetime(df['date'])
df = df.sort_values('time')
df['timestamp'] = df['time'].apply(lambda x: x.timestamp())

# En el siguiente codigo se muestra el analisis y proceso de los datos
X = df['timestamp'].values.reshape(-1, 1)
y = df['result'].values
model = LinearRegression()
model.fit(X, y)
next_time = df['timestamp'].iloc[-1] + 1
next_pred = model.predict([[next_time]])[0]

# En el siguiente codigo se crea la grafica
fig = px.bar(df, x='slug', y='result', color='result', text='result',
             title='Resultados por Lotería (slug)')
fig.update_traces(texttemplate='%{text}', textposition='outside')
fig.update_layout(
    plot_bgcolor='black',
    paper_bgcolor='black',
    font_color='white',
    xaxis=dict(tickfont=dict(color='red')),
    yaxis=dict(tickfont=dict(color='white'))
)

# Con este codigo se genera el xlsx 
buffer_xlsx = io.BytesIO()
df_copy = df.drop(columns=['timestamp']).copy()
df_copy['Predicción siguiente'] = next_pred
df_copy['Fecha descarga'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
df_copy.to_excel(buffer_xlsx, index=False)
buffer_xlsx.seek(0)
xlsx_base64 = base64.b64encode(buffer_xlsx.read()).decode('utf-8')
xlsx_href = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{xlsx_base64}"

# Con el siguiente codigo se crea un pdf 
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", "B", 16)
pdf.set_text_color(255, 0, 0)
pdf.cell(0, 10, "Dashboard de Resultados", ln=True, align="C")
pdf.set_font("Arial", "", 12)
pdf.set_text_color(0, 0, 0)
pdf.cell(0, 10, f"Fecha y hora descarga: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
pdf.cell(0, 10, f"Predicción siguiente número: {next_pred:.2f}", ln=True)
pdf.ln(5)

# Tabla en PDF
pdf.set_font("Arial", "B", 12)
pdf.cell(60, 8, "Lotería", 1, 0, 'C')
pdf.cell(40, 8, "Resultado", 1, 0, 'C')
pdf.cell(40, 8, "Fecha", 1, 1, 'C')

pdf.set_font("Arial", "", 12)
for index, row in df.iterrows():
    pdf.cell(60, 8, row['slug'], 1, 0, 'C')
    pdf.cell(40, 8, str(row['result']), 1, 0, 'C')
    pdf.cell(40, 8, row['date'], 1, 1, 'C')

# Posteriormente exportamos PDF como bytes y codificar en base64
pdf_bytes = pdf.output(dest='S').encode('latin1')
pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
pdf_href = f"data:application/pdf;base64,{pdf_base64}"

# A continuacion se muestra codigo para crear dashboard
app = Dash(__name__)

app.layout = html.Div([
    html.H1('Dashboard de Resultados', style={'color': 'white', 'textAlign': 'center'}),
    html.H4(f'Fecha y hora actual: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            style={'color': 'white', 'textAlign': 'center'}),
    html.H3(f'Predicción del siguiente número: {next_pred:.2f}',
            style={'color': 'white', 'textAlign': 'center'}),
    
    # Botones de descarga
    html.Div([
        html.A("Descargar PDF", href=pdf_href, download=f"resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
               style={'marginRight': '10px', 'color': 'white', 'backgroundColor':'red', 'padding':'10px', 'textDecoration':'none', 'borderRadius':'5px'}),
        html.A("Descargar XLSX", href=xlsx_href, download=f"resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
               style={'color': 'white', 'backgroundColor':'green', 'padding':'10px', 'textDecoration':'none', 'borderRadius':'5px'})
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Tabla
    dash_table.DataTable(
        data=df.drop(columns=['timestamp']).to_dict('records'),
        columns=[{"name": i, "id": i} for i in df.columns if i != 'timestamp'],
        page_size=10,
        style_table={'overflowX': 'auto', 'width': '100%'},
        style_header={
            'backgroundColor': 'red',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_cell={
            'backgroundColor': 'lightgrey',
            'color': 'black',
            'textAlign': 'center',
            'padding': '5px'
        }
    ),
    
    # Gráfica
    dcc.Graph(
        id='slug-graph',
        figure=fig,
        style={'width': '100%', 'height': '600px'}
    )
], style={'backgroundColor': 'black', 'padding': '20px', 'minHeight': '100vh'})

if __name__ == '__main__':
    app.run(debug=True)
