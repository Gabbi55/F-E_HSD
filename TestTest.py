import struct
from datetime import datetime, timedelta

import dash
import dash_core_components as dcc
import dash_leaflet as dl
import plotly.graph_objs as go
import serial
from dash import html
from dash.dependencies import Output, Input

# Define lists for data to save data
pm1_values = list()
pm2_5_values = list()
pm10_values = list()
timestamps = list()
lng_values = list()
lat_values = list()
altitude_values = list()
temp_values = list()
hum_values = list()
marker_positions = list()

# Open the serial port (assuming serial data)
ser = serial.Serial('COM7', 115200, timeout=1)

# Define the format of the struct
struct_format = '<9fH5B3d'

# Initialisation of the Dash application
app = dash.Dash(__name__)

colors = {
    "text": "#FFFFFF",  # white
    "background": "#333333",  # dark gray
    "plot_background": "#333333",  # medium gray
    "paper_color": "#696969"  # very dark gray
}

# Create layout of Dash-app graphs of data and map
app.layout = html.Div(style={'backgroundColor': colors['background']},
                      children=[
                          # Headline of Dash-app
                          html.H1(
                              children="Luftdaten-Analyse",
                              style={
                                  "textAlign": "center",
                                  "color": colors["text"],
                                  'backgroundColor': colors['background']
                              }
                          ),
                          # Slider for x-axis limit
                          html.Div([
                              html.Label('Zeitraum der Datendarstellung (in Minuten):'),
                              dcc.Slider(
                                  id='lim-x-axis-slider',
                                  min=1,
                                  max=60,
                                  step=1,
                                  value=20,
                                  marks={i: f'{i}' for i in range(0, 61, 10)},
                              ),
                          ],
                                style={'backgroundColor': colors['background'], 'color': colors['text']}
                          ),

                          # Graphs of temp, hum, pm1, pm25, pm10
                          html.Div([
                              html.Div([dcc.Graph(id='live-graph-temp_hum', animate=True)],
                                       style={'display': 'inline-block', 'width': '25%'}),
                              html.Div([dcc.Graph(id='live-graph-pm1', animate=True)],
                                       style={'display': 'inline-block', 'width': '25%'}),
                              html.Div([dcc.Graph(id='live-graph-pm25', animate=True)],
                                       style={'display': 'inline-block', 'width': '25%'}),
                              html.Div([dcc.Graph(id='live-graph-pm10', animate=True)],
                                       style={'display': 'inline-block', 'width': '25%'}),
                          ],
                              style={'backgroundColor': colors['background'], 'color': colors['text'],
                                     'display': 'flex', 'flex-direction': 'row'}
                          ),

                          # Graph for altitude of plane and position on map
                          html.Div([
                              html.Div([
                                  dl.Map([
                                      dl.TileLayer(),  # OpenStreetMap
                                      dl.LayerGroup(id="marker-layer"),  # LayerGroup to store all markers
                                  ], center=[51.4325, 6.8797], zoom=10, id='live-map',
                                      style={'width': '100%', 'height': '500px'}),
                              ], style={'display': 'inline-block', 'width': '65%'}),
                              html.Div([
                                  dcc.Graph(id='live-graph-altitude', animate=True)],
                                  style={'display': 'inline-block', 'width': '35%'}),
                          ], style={'display': 'flex', 'flex-direction': 'row'}),

                          # Interval component to update the graphs every second
                          dcc.Interval(
                              id='graph-update',
                              interval=1000,  # 1000 msec = 1 sec
                              n_intervals=0
                          )
                      ]
                      )


@app.callback([Output('live-graph-temp_hum', 'figure'),
               Output('live-graph-pm1', 'figure'),
               Output('live-graph-pm25', 'figure'),
               Output('live-graph-pm10', 'figure'),
               Output('marker-layer', 'children'),
               Output('live-graph-altitude', 'figure')],
              [Input('graph-update', 'n_intervals'),
               Input('lim-x-axis-slider', 'value')])
def update_graph_scatter(n, lim_x_axis):
    min_time = None
    max_time = None
    # Check if data is available from serial port
    if ser.in_waiting > 0:
        while ser.read() != b'<':
            pass
        struct_size = struct.calcsize(struct_format)
        data = ser.read(struct_size)

        if ser.read() == b'>':
            if len(data) == struct_size:
                unpacked_data = struct.unpack(struct_format, data)
                (pm1, pm25, pm10, sumBins, temp, altitude, hum, xtra, co2, year, month, day, hour, minute, second, lat,
                 lng, heading) = unpacked_data

                # Append data to lists
                timestamp = datetime(year, month, day, hour, minute, second)
                pm1_values.append(pm1)
                pm2_5_values.append(pm25)
                pm10_values.append(pm10)
                timestamps.append(timestamp)
                lng_values.append(lng)
                lat_values.append(lat)
                altitude_values.append(altitude)
                temp_values.append(temp)
                hum_values.append(hum)
                marker_positions.append(
                    {'position': [lat, lng], 'temperature': temp, 'humidity': hum, 'pm1': pm1, 'pm10': pm10,
                     'pm25': pm25})

    # Set the x-axis limits to the chosen 'lim_x_axis'-value
    if timestamps:
        min_time = timestamps[-1] - timedelta(minutes=lim_x_axis)
        max_time = timestamps[-1]

    # Define scatter plots for Temp and Humidity
    scatter_temp = go.Scatter(
        x=list(timestamps),
        y=list(temp_values),
        name='Temp',
        mode='lines+markers',
        yaxis='y1'
    )
    scatter_hum = go.Scatter(
        x=list(timestamps),
        y=list(hum_values),
        name='Humidity',
        mode='lines+markers',
        yaxis='y2'
    )

    layout_temp_hum = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Temperatur (°C)', side='left'),
        yaxis2=dict(title='Luftfeuchte (%)', overlaying='y', side='right'),
        legend=dict(yanchor="bottom", xanchor="right"),
        title='Temp & Humidity',
        paper_bgcolor=colors['paper_color'],
        plot_bgcolor=colors['plot_background'],
        font=dict(color=colors['text']),
        height=400,
        margin={'l': 40, 'r': 35, 't': 105, 'b': 80}
    )

    # Define scatter plots for PM1, PM2.5 and PM10 values
    scatter_pm1 = go.Scatter(
        x=list(timestamps),
        y=list(pm1_values),
        name='PM1',
        mode='lines+markers'
    )
    scatter_pm25 = go.Scatter(
        x=list(timestamps),
        y=list(pm2_5_values),
        name='PM2.5',
        mode='lines+markers'
    )
    scatter_pm10 = go.Scatter(
        x=list(timestamps),
        y=list(pm10_values),
        name='PM10',
        mode='lines+markers'
    )

    layout_pm1 = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Partikelkonzentration (µg/m³)'),
        title='PM1 Werte',
        paper_bgcolor=colors['paper_color'],
        plot_bgcolor=colors['plot_background'],
        font=dict(color=colors['text']),
        height=400,
        margin={'l': 40, 'r': 20, 't': 40, 'b': 80}
    )

    layout_pm25 = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Partikelkonzentration (µg/m³)'),
        title='PM2.5 Werte',
        paper_bgcolor=colors['paper_color'],
        plot_bgcolor=colors['plot_background'],
        font=dict(color=colors['text']),
        height=400,
        margin={'l': 40, 'r': 20, 't': 40, 'b': 80}
    )

    layout_pm10 = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Partikelkonzentration (µg/m³)'),
        title='PM10 Werte',
        paper_bgcolor=colors['paper_color'],
        plot_bgcolor=colors['plot_background'],
        font=dict(color=colors['text']),
        height=400,
        margin={'l': 40, 'r': 20, 't': 40, 'b': 80}
    )

    # List of marker on map with information
    markers = [
        dl.CircleMarker(center=pos['position'], radius=2, color="blue", fill=True, fillOpacity=0.6,
                        children=[
                            dl.Tooltip(html.Div([
                                html.Div(f"Lat: {pos['position'][0]:.6f}"),
                                html.Div(f"Lng: {pos['position'][1]:.6f}"),
                                html.Div(f"Temp: {pos['temperature']:.2f}°C"),
                                html.Div(f"Hum: {pos['humidity']:.2f}%"),
                                html.Div(f"pm1: {pos['pm1']:.2f}µg/m³"),
                                html.Div(f"pm10: {pos['pm10']:.2f}µg/m³"),
                                html.Div(f"pm25: {pos['pm25']:.2f}µg/m³"),
                            ]))
                        ])
        for pos in marker_positions
    ]

    # Define scatter plot for altitude data
    scatter_altitude = go.Scatter(
        x=list(timestamps),
        y=list(altitude_values),
        name='Altitude',
        mode='lines+markers'
    )
    layout_altitude = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Höhe (m)'),
        title='Flughöhe',
        paper_bgcolor=colors['paper_color'],
        plot_bgcolor=colors['plot_background'],
        font=dict(color=colors['text']),
        height=500,
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40}
    )

    return [{
        'data': [scatter_temp, scatter_hum],
        'layout': layout_temp_hum
    },
        {
            'data': [scatter_pm1],
            'layout': layout_pm1
        },
        {
            'data': [scatter_pm25],
            'layout': layout_pm25
        },
        {
            'data': [scatter_pm10],
            'layout': layout_pm10
        },
        markers,
        {
            'data': [scatter_altitude],
            'layout': layout_altitude
        }]


# Start of the Dash server
if __name__ == '__main__':
    app.run_server(port=4052)
