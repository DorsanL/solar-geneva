from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# Load GIS data
girec = pd.read_pickle("girec_expansion.pickle")
communes = pd.read_pickle("communes_expansion.pickle")
communes_agg = pd.read_pickle("communes_expansion_agg.pickle")

# Post-process the data
total_capacity_by_year = communes.sum(numeric_only=True).div(1000)  # Convert to MWc

# Create the Dash app
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    html.H4('Expansion des capacités photovoltaïques dans le canton de Genève'),

    dcc.Tabs(id="tabs", value='tab-past', children=[
        dcc.Tab(label='Statistiques 2005-2024', value='tab-past'),
        dcc.Tab(label='Tendances 2025-2050', value='tab-future'),
    ]),

    html.Div(id='tabs-content')
])


# Callback to update content based on selected tab
@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs', 'value')]
)
def render_content(tab):
    if tab == 'tab-past':
        min_year = 2005
        max_year = 2024
    else:
        min_year = 2025
        max_year = 2050

    return html.Div([
        html.P("Année :"),
        dcc.Slider(
            id='year-input',
            min=min_year,
            max=max_year,
            step=1,
            value=2024,  # default value
            marks={year: str(year) for year in range(min_year, max_year + 1)},  # creating marks for each year
            tooltip={"placement": "bottom", "always_visible": True}  # optional, shows the current value
        ),
        html.P("Découpage :"),
        dcc.RadioItems(
            id='granularity-input',
            options=[
                {'label': 'Girec', 'value': "girec"},
                {'label': 'Communes', 'value': "communes"},
                {'label': 'Communes (agg)', 'value': "communes_agg"},
            ],
            value="communes",
            inline=True
        ),
        html.P("Carte à afficher :"),
        dcc.RadioItems(
            id='metric-input',
            options=[
                {'label': 'Capacité installée [kWc]', 'value': "power"},
                {'label': 'Potentiel installable [kWc]', 'value': "potential"},
                {'label': 'Ratio capacité installée / potentiel installable [%]', 'value': "ratio"},

            ],
            value="potential",
            inline=True
        ),
        html.P("Échelle :"),
        html.Div([
            dcc.Input(
                id='min-value-input',
                type='number',
                placeholder='Min',
                value=None,  # No default value
                style={'margin-right': '10px'}  # Adds some spacing
            ),
            dcc.Input(
                id='max-value-input',
                type='number',
                placeholder='Max',
                value=None  # No default value
            ),
        ]),

        # Main map at the top
        dcc.Graph(id='map'),

        # Performance plots side by side
        html.Div([
            html.Div(dcc.Graph(id='plot-expansion'), style={'width': '49%'}),
            html.Div(dcc.Graph(id='plot-share'), style={'width': '49%'})
        ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-bottom': '20px'}),
    ])


# Callback to update the map based on selected year and granularity
@app.callback(
    Output('map', 'figure'),
    Input('year-input', 'value'),
    Input('granularity-input', 'value'),
    Input('min-value-input', 'value'),
    Input('max-value-input', 'value'),
    Input('metric-input', 'value'),
)
def update_past_map(year, granularity, min_scale, max_scale, metric):

    if granularity == "communes":
        data = communes_agg
    elif granularity == "communes_agg":
        data = communes_agg
    else:
        data = girec

    if metric == "power":
        data_to_plot = data[year]
    elif metric == "potential":
        data_to_plot = data["pv_potential"] / 3
    else:
        data_to_plot = 100 * data[year] / (data["pv_potential"] / 3)

    try:
        range_for_plot = [min_scale, max_scale]
    except:
        range_for_plot = None

    fig = px.choropleth_mapbox(
        data_frame=data,
        geojson=data.geometry.__geo_interface__,
        locations=data.index,
        color=year if metric == "power" else data_to_plot,
        range_color=range_for_plot,
        color_continuous_scale="blues" if metric == "ratio" else "oranges",
        opacity=0.7,
        mapbox_style="open-street-map",
        center={"lat": 46.2244, "lon": 6.1432},
        zoom=10.7,
        labels={year: "kWc"}
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=1200)

    return fig


@app.callback(
    Output('plot-expansion', 'figure'),
    Output('plot-share', 'figure'),
    Input('year-input', 'value'),
)
def update_plots(year):
    
    fig_expansion = px.line(
        x=total_capacity_by_year.index,
        y=total_capacity_by_year.values,
        title="Capacité photovoltaïque installée à Genève (2005-2050)",
        labels={"x": "Année", "y": "[MWc]"},
        template="plotly_white"
    )
    fig_expansion.update_traces(line=dict(color="orange"), mode="lines+markers")

    fig_share = px.bar(
        x=communes.index,
        y=communes[year].values / communes[year].sum() * 100,
        labels={'x': 'Commune', 'y': '[%]'},
        title=f"Répartition de la capacité photovoltaïque déployée en {year}",
        template="plotly_white"
    )
    fig_share.update_traces(marker_color='orange')

    return fig_expansion, fig_share


if __name__ == '__main__':
    app.run_server(debug=True)
