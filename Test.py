import serial
import struct
import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import dash_leaflet as dl
from collections import deque
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc

# Define data Deques to save data
pm1_values = deque()
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

# Open the serial port (assuming serial data)
ser = serial.Serial('COM7', 115200, timeout=1)

# Define the format of the struct
struct_format = '<9fH5B3d'

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
        html.H1(
            children="Luftanalyse Daten",
            style={
                "textAlign": "center",
                "color": colors["text"],
                'backgroundColor': colors['background']
            }
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
            style={'backgroundColor': colors['background'], 'color': colors['text'], 'display': 'flex', 'flex-direction': 'row'}
        ),
        html.Div(
            [
                dcc.Input(),
                #dcc.Input(style={"margin-left": "15px"})
            ]
        ),

        # Graph for height and position on map (side by side)
        html.Div([
            html.Div([
                dl.Map([
                    dl.TileLayer(),  # Standardmäßig OpenStreetMap
                    dl.Marker(id="marker", position=[51.1887, 6.7939]),  # Initialize at a default position
                    dl.Polyline(id="trail", positions=[], color="blue", weight=3)  # Trail of positions
                ], center=[50.1109, 8.6821], zoom=10, id='live-map', style={'width': '100%', 'height': '500px'}),
            ], style={'display': 'inline-block', 'width': '65%'}),
            html.Div([
                dcc.Graph(id='live-graph-hight', animate=True)],
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

# Callback function for updating the graphs and the map
@app.callback([Output('live-graph-temp_hum', 'figure'),
               Output('live-graph-pm1', 'figure'),
               Output('live-graph-pm25', 'figure'),
               Output('live-graph-pm10', 'figure'),
               Output('marker', 'position'),  # Update marker position
               Output('live-map', 'center'),  # Update map center dynamically
               Output('trail', 'positions'),  # Update trail positions
               Output('live-graph-hight', 'figure')],
              [Input('graph-update', 'n_intervals')])
def update_graph_scatter(n):
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
                pm1, pm25, pm10, sumBins, temp, altitude, hum, xtra, co2, year, month, day, hour, minute, second, lat, lng, heading = unpacked_data

                # Append data to deque lists
                timestamp = datetime(year, month, day, hour, minute, second)
                pm1_values.append(pm1)
                pm2_5_values.append(pm25)
                pm10_values.append(pm10)
                timestamps.append(timestamp)
                lng_values.append(lng)
                lat_values.append(lat)
                hight_values.append(altitude)
                temp_values.append(temp)
                hum_values.append(hum)

    # Set the x-axis limits to the last 'lim_x_axis' minutes
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
        yaxis=dict(title='Temp (°C)', side='left'),
        yaxis2=dict(title='Humidity (%)', overlaying='y', side='right'),
        legend=dict(
            yanchor="bottom",
            xanchor="right"),
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

    # Define the trail  and marker position for the map
    if len(lat_values) > 0 and len(lng_values) > 0:
        new_position = [lat_values[-1], lng_values[-1]]  # Update position to the latest lat/lng
        trail_positions = list(zip(lat_values, lng_values))  # Update trail positions
    else:
        new_position = [51.1887, 6.7939]  # Default initial position (HSD)
        trail_positions = []

    # Define scatter plot for height data
    scatter_hight = go.Scatter(
        x=list(timestamps),
        y=list(hight_values),
        name='Hight',
        mode='lines+markers'
    )
    layout_hight = go.Layout(
        xaxis=dict(title='Zeit', type='date', range=[min_time, max_time]),
        yaxis=dict(title='Höhe [m]'),
        title='Flughöhe',
        paper_bgcolor=colors['paper_color'],
        plot_bgcolor=colors['plot_background'],
        font=dict(color=colors['text']),
        height=500,
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40}
    )

    # Return the updated figures and map components
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
        new_position, new_position, trail_positions,  # Update both marker and map center to the new position
        {
        'data': [scatter_hight],
        'layout': layout_hight
    }]


# Start of the Dash server
if __name__ == '__main__':
    app.run_server(port=4052)
