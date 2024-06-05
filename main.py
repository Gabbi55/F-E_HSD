import serial
import struct
import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import time
import plotly
import random
import plotly.graph_objs as go
from collections import deque
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc

# Define data Deques to save data
pm1_values = deque()  # Limit data history to maintain performance
pm2_5_values = deque()
pm10_values = deque()
timestamps = deque()
lng_values = deque()
lat_values = deque()
hight_values = deque()
temp_values = deque()
hum_values = deque()

# Graphs x-axis limits to the last x minutes of data
lim_x_axis = 2

# open the serial port
ser = serial.Serial('COM7', 115200, timeout=1)

# Define the format of the struct
struct_format = '<9fH5B3d'

fig = go.Figure()

# Initialisation of the Dash application
app = dash.Dash(__name__)

colors = {
    "text": "#FFFFFF",  # white text
    "background": "#333333",  # dark gray background
    "plot_background": "#333333",  # medium gray plot background
    "paper_color": "#696969"  # very dark gray for graph paper background
}


# Create layout of Dash-app graphs of data and map
app.layout = html.Div(
    [
        # Headline of Dash-app
        html.H1(children = "Luftanalyse Daten",
                style = {
                    "textAlign" : "center",
                    "color" : colors["text"],
                    'backgroundColor': colors['background']
                }
        ),
        # Graphs of temp, hum, pm1, pm25, pm10
        html.Div([
                html.Div([dcc.Graph(id='live-graph-temp_hum',
                                            animate=True)],
                                            style={'display': 'inline-block', 'width': '25%'}),
                html.Div([dcc.Graph(id='live-graph-pm1',
                                            animate=True)],
                                            style={'display': 'inline-block', 'width': '25%'}),
                html.Div([dcc.Graph(id='live-graph-pm25',
                                            animate=True)],
                                            style={'display': 'inline-block', 'width': '25%'}),
                html.Div([dcc.Graph(id='live-graph-pm10',
                                            animate=True)],
                                            style={'display': 'inline-block', 'width': '25%'}),
        ],
            style={'backgroundColor': colors['background'], 'color': colors['text'], 'display': 'flex', 'flex-direction': 'row'}
        ),

        # Graph for hight and position on map
        html.Div([
            html.Div([
                dcc.Graph(id='live-map',
                          animate=True)],
                          style={'display': 'inline-block', 'width': '67%'}),
            html.Div([
                dcc.Graph(id='live-graph-hight',
                          animate=True)],
                          style={'display': 'inline-block', 'width': '33%'})
        ]),

        # Interval component to update the graphs every second
        dcc.Interval(
                id='graph-update',
                interval=1000,  # 1000 msec = 1 sec
                n_intervals=0
                )

    ]
)

# Callback function for updating the graphs
@app.callback([Output('live-graph-temp_hum', 'figure'),
               Output('live-graph-pm1', 'figure'),
               Output('live-graph-pm25', 'figure'),
               Output('live-graph-pm10', 'figure'),
               Output('live-map','figure'),
               Output('live-graph-hight', 'figure')],
              [Input('graph-update', 'n_intervals')])

def update_graph_scatter(n):
    min_time = None
    max_time = None

    # Check if data is available
    if ser.in_waiting > 0:
        # Read until we find a end marker
        while ser.read() != b'<':
            pass
        # Read the size of the struct
        struct_size = struct.calcsize(struct_format)
        # Read struct_size bytes from the serial port
        data = ser.read(struct_size)

        # Check for the start marker
        if ser.read() == b'>':
            if len(data) == struct_size:
                # If we received the correct amount of bytes, unpack them
                unpacked_data = struct.unpack(struct_format, data)
                # Now you can access the fields of the struct:
                pm1, pm25, pm10, sumBins, temp, altitude, hum, xtra, co2, year, month, day, hour, minute, second, lat, lng, heading = unpacked_data

                # Fill data lists with fields of the struct
                timestamp = datetime(year, month, day, hour, minute, second) #datetime -> structure of timestamp
                pm1_values.append(pm1) #append -> adds data tp list
                pm2_5_values.append(pm25)
                pm10_values.append(pm10)
                timestamps.append(timestamp)
                lng_values.append(lng)
                lat_values.append(lat)
                hight_values.append(altitude)
                temp_values.append(temp)
                hum_values.append(hum)



    # Figure of air_data
    # Setting the x-axis limits to the last 5 minutes of data
    if timestamps:
        min_time = timestamps[-1] - timedelta(minutes=lim_x_axis)
        max_time = timestamps[-1]

    # Define scatter plot for Temp and Humidity
    scatter_temp = go.Scatter(
        x=list(timestamps),
        y=list(temp_values),
        name='temp',
        mode='lines+markers',
        yaxis='y1'
    )
    scatter_hum = go.Scatter(
        x=list(timestamps),
        y=list(hum_values),
        name='hum',
        mode='lines+markers',
        yaxis='y2'
    )

    layout_temp_hum = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Temp [°C]', side='left'),
        yaxis2=dict(title='Hum [%]', overlaying='y', side='right'),
        title='Temp & Hum',
        paper_bgcolor=colors['paper_color'],  # Hintergrundfarbe des gesamten Graphbereichs
        plot_bgcolor=colors['plot_background'],  # Hintergrundfarbe des Plotbereichs
        font=dict(color=colors['text']),
        height=250,
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40}
    )


    # Define scatter plots for pm1, pm25 and pm10 values
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
    # Define layout of individual scatter diagrams graphs
    layout_pm1 = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Partikelkonzentration (µg/m³)'),
        title='PM1 Werte',
        paper_bgcolor=colors['paper_color'],  # Hintergrundfarbe des gesamten Graphbereichs
        plot_bgcolor=colors['plot_background'],  # Hintergrundfarbe des Plotbereichs
        font=dict(color=colors['text']),
        height = 250,
        margin = {'l': 40, 'r': 40, 't': 40, 'b': 40}
    )

    layout_pm25 = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Partikelkonzentration (µg/m³)'),
        title='PM2.5 Werte',
        paper_bgcolor=colors['paper_color'],  # Hintergrundfarbe des gesamten Graphbereichs
        plot_bgcolor=colors['plot_background'],  # Hintergrundfarbe des Plotbereichs
        font=dict(color=colors['text']),
        height=250,
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40}
    )

    layout_pm10 = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Partikelkonzentration (µg/m³)'),
        title='PM10 Werte',
        paper_bgcolor=colors['paper_color'],  # Hintergrundfarbe des gesamten Graphbereichs
        plot_bgcolor=colors['plot_background'],  # Hintergrundfarbe des Plotbereichs
        font=dict(color=colors['text']),
        height=250,
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40}
    )

    # Map with lat & lng values
    location = go.Scattermapbox(
        lon=list(lng_values),
        lat=list(lat_values),
        mode='lines+markers',
        marker=dict(size=10, color='red')
    )

    map_layout = go.Layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            #accesstoken='your_mapbox_access_token',  # optional, falls OpenStreetMap nicht ausreicht
            center=dict(lat=lat_values[-1], lon=lng_values[-1]),
            zoom=10
        ),
        height=500,
        margin={'r': 1, 't': 1, 'l': 1, 'b': 1}
    )

    # Figure of hight-data
    scatter_hight = go.Scatter(
        x=list(timestamps),
        y=list(hight_values),
        name='Hight',
        mode='lines+markers'
    )
    layout_hight = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Höhe [cm]'),
        title='Flughöhe',
        paper_bgcolor=colors['paper_color'],  # Hintergrundfarbe des gesamten Graphbereichs
        plot_bgcolor=colors['plot_background'],  # Hintergrundfarbe des Plotbereichs
        font=dict(color=colors['text']),
        height=500,
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40}
    )

    # Return of the updated graphs
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
    {
        'data': [location],
        'layout': map_layout
        },
    {
        'data': [scatter_hight],
        'layout': layout_hight
        }
    ]


# Start of the Dash server on port 4052
if __name__ == '__main__':
    app.run_server(port=4052)


