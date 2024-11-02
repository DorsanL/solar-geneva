from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Load GIS data
girec_lin = pd.read_pickle("output/girec_lin.pickle")
girec_exp = pd.read_pickle("output/girec_exp.pickle")
communes_lin = pd.read_pickle("output/communes_lin.pickle")
communes_exp = pd.read_pickle("output/communes_exp.pickle")

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
                {'label': 'Sous-secteurs statistiques (GIREC)', 'value': "girec"},
                {'label': 'Communes', 'value': "communes"},
            ],
            value="communes",
            inline=True
        ),
        html.P("Carte à afficher :"),
        dcc.RadioItems(
            id='metric-input',
            options=[
                {'label': 'Capacité installée [MWc]', 'value': "power"},
                {'label': 'Potentiel installable [MWc]', 'value': "potential"},
                {'label': 'Ratio capacité installée / potentiel installable [%]', 'value': "ratio"},
            ],
            value="potential",
            inline=True
        ),
        html.P("Croissance :"),
        dcc.RadioItems(
            id='model-input',
            options=[
                {'label': 'Linéaire', 'value': "linear"},
                {'label': 'Exponentielle (objectif 1 MWc)', 'value': "exponential"},
            ],
            value="linear",
            inline=True
        ),
        html.P("Potentiel solaire total :"),
        dcc.RadioItems(
            id='potential-input',
            options=[
                {'label': "1 [GWh/an] (Plan directeur de l'énergie)", 'value': 3},  # divide by 3
                {'label': "3 [GWh/an] (Toit solaire)", 'value': 1},  # default value from QBuildings
            ],
            value=3,
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
    Input('metric-input', 'value'),
    Input('model-input', 'value'),
    Input('potential-input', 'value'),
    Input('min-value-input', 'value'),
    Input('max-value-input', 'value'),
)
def update_map(year, granularity, metric, model, potential, min_scale, max_scale):

    if granularity == "communes" and model == "linear":
        data = communes_lin
    elif granularity == "communes" and model == "exponential":
        data = communes_exp
    elif granularity == "girec" and model == "linear":
        data = girec_lin
    else:
        data = girec_exp

    if metric == "power":
        data_to_plot = data[year]
    elif metric == "potential":
        data_to_plot = data["pv_potential"] / potential
    else:
        data_to_plot = 100 * data[year] / (data["pv_potential"] / potential)

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
        labels={year: "MWc"}
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=1200)

    return fig


@app.callback(
    Output('plot-expansion', 'figure'),
    Output('plot-share', 'figure'),
    Input('year-input', 'value'),
    Input('granularity-input', 'value'),
    Input('model-input', 'value'),
)
def update_plots(year, granularity, model):

    if granularity == "communes" and model == "linear":
        data = communes_lin
    elif granularity == "communes" and model == "exponential":
        data = communes_exp
    elif granularity == "girec" and model == "linear":
        data = girec_lin
    else:
        data = girec_exp

    total_capacity_by_year = data.sum(numeric_only=True)

    fig_expansion = px.line(
        x=total_capacity_by_year.index,
        y=total_capacity_by_year.values,
        title="Capacité photovoltaïque installée à Genève (2005-2050)",
        labels={"x": "Année", "y": "[MWc]"},
        template="plotly_white"
    )
    fig_expansion.update_traces(line=dict(color="orange"), mode="lines+markers")

    fig_expansion.add_trace(
        go.Scatter(
            x=[2030, 2050],
            y=[350, 1000],
            mode="markers+text",
            marker=dict(color="red", size=10, symbol="circle"),
            text=["Objectif 2030<br>350 MWc", "Objectif 2050<br>1000 MWc"],
            textposition="middle left"
        )
    )
    fig_expansion.update_layout(
        xaxis=dict(range=[2005, 2055]),  # Ensure x-axis includes entire range
        yaxis=dict(range=[0, 1100]),  # Adjust y-axis range for better display
        showlegend=False
    )

    fig_share = px.bar(
        x=data.index,
        y=data[year].values / data[year].sum() * 100,
        labels={'x': 'Commune', 'y': '[%]'},
        title=f"Répartition de la capacité photovoltaïque déployée en {year}",
        template="plotly_white"
    )
    fig_share.update_traces(marker_color='orange')

    return fig_expansion, fig_share


if __name__ == '__main__':
    app.run_server(debug=True)
