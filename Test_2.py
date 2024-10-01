import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import plotly.graph_objs as go
from collections import deque
import serial
import struct
from datetime import datetime

# Datenstrukturen zum Speichern der Sensorwerte
temp_values = deque(maxlen=1000)
hum_values = deque(maxlen=1000)
pm1_values = deque(maxlen=1000)
pm2_5_values = deque(maxlen=1000)
pm10_values = deque(maxlen=1000)
lat_values = deque(maxlen=1000)
lng_values = deque(maxlen=1000)
hight_values = deque(maxlen=1000)
timestamps = deque(maxlen=1000)

# Serielle Verbindung konfigurieren
ser = serial.Serial('COM7', 115200, timeout=1)
struct_format = '<9fH5B3d'  # Angenommenes Datenformat

# Erstellung der Dash-App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Definieren des App-Layouts
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Umweltüberwachungs-Dashboard"), width={'size': 6, 'offset': 3}),
        dbc.Col(dbc.Button("Umweltdaten anzeigen", id="show-env-data", n_clicks=0), width={'size': 2, 'offset': 1}),
        dbc.Col(dbc.Button("Kartenansicht", id="show-map", n_clicks=0), width=2)
    ], justify="end", no_gutters=True, className="mt-3"),
    html.Div(id="content", children=[])
], fluid=True)

# Callback zur Anzeige der Inhalte basierend auf der Auswahl
@app.callback(
    Output("content", "children"),
    [Input("show-env-data", "n_clicks"), Input("show-map", "n_clicks")],
    prevent_initial_call=True
)
def display_tab(env_click, map_click):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "show-env-data":
        return [
            dcc.Graph(id="temp-hum-graph"),
            dcc.Graph(id="pm-graph"),
            dcc.Interval(id="update-interval", interval=2000, n_intervals=0)
        ]
    elif button_id == "show-map":
        return [
            dl.Map(center=[50.1109, 8.6821], zoom=10, children=[
                dl.TileLayer(),
                dl.Marker(id="marker", position=[50.1109, 8.6821]),
                dl.Polyline(id="trail", positions=[], color="blue", weight=3)
            ], style={'width': '100%', 'height': '50vh'}, id="map"),
            dcc.Interval(id="map-update-interval", interval=5000, n_intervals=0)
        ]

# Callback zur Aktualisierung der Umweltdaten
@app.callback(
    [Output("temp-hum-graph", "figure"),
     Output("pm-graph", "figure")],
    [Input("update-interval", "n_intervals")]
)
def update_env_data(n):
    if ser.in_waiting > 0:
        data = ser.read(ser.in_waiting)
        temp, hum, pm1, pm2_5, pm10 = struct.unpack(struct_format, data)
        temp_values.append(temp)
        hum_values.append(hum)
        pm1_values.append(pm1)
        pm2_5_values.append(pm2_5)
        pm10_values.append(pm10)
        timestamps.append(datetime.now())

    temp_trace = go.Scatter(x=list(timestamps), y=list(temp_values), mode='lines+markers', name='Temperatur')
    hum_trace = go.Scatter(x=list(timestamps), y=list(hum_values), mode='lines+markers', name='Luftfeuchtigkeit')
    pm1_trace = go.Scatter(x=list(timestamps), y=list(pm1_values), mode='lines+markers', name='PM1')
    pm25_trace = go.Scatter(x=list(timestamps), y=list(pm2_5_values), mode='lines+markers', name='PM2.5')
    pm10_trace = go.Scatter(x=list(timestamps), y=list(pm10_values), mode='lines+markers', name='PM10')

    env_layout = go.Layout(title="Temperatur und Luftfeuchtigkeit", xaxis_title="Zeit", yaxis_title="Werte")
    pm_layout = go.Layout(title="Partikelmessung", xaxis_title="Zeit", yaxis_title="µg/m³")

    return {
        "data": [temp_trace, hum_trace],
        "layout": env_layout
    }, {
        "data": [pm1_trace, pm25_trace, pm10_trace],
        "layout": pm_layout
    }

# Callback zur Aktualisierung der Kartenansicht
@app.callback(
    [Output("marker", "position"),
     Output("trail", "positions")],
    [Input("map-update-interval", "n_intervals")]
)
def update_map(n):
    if ser.in_waiting > 0:
        data = ser.read(ser.in_waiting)
        lat, lng = struct.unpack(struct_format, data)[-2:]
        lat_values.append(lat)
        lng_values.append(lng)

    if lat_values and lng_values:
        current_position = [lat_values[-1], lng_values[-1]]
        trail = list(zip(lat_values, lng_values))
    else:
        current_position = [50.1109, 8.6821]
        trail = []

    return current_position, trail

# Starten der Dash-App
if __name__ == "__main__":
    app.run_server(debug=True)
