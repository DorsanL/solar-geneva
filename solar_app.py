from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# -------------- Data import -------------------------------------------

# Load GIS data
girec_lin = pd.read_pickle("output/girec_lin.pickle")
girec_exp = pd.read_pickle("output/girec_exp.pickle")
communes_lin = pd.read_pickle("output/communes_lin.pickle")
communes_exp = pd.read_pickle("output/communes_exp.pickle")

borders = communes_lin[['geometry']]

# -------------- Styling -------------------------------------------

app = Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP],  # 'https://codepen.io/chriddyp/pen/bWLwgP.css'
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

app.layout = dbc.Container([
    # Colors line
    dbc.Row(
        [
            dbc.Col(
                html.Hr(
                    style={
                        "borderWidth": "2vh",
                        "width": "100%",
                        "borderColor": "#CAE7B9",
                        "opacity": "unset",
                    }
                ),
                width={"size": 2},
            ),
            dbc.Col(
                html.Hr(
                    style={
                        "borderWidth": "2vh",
                        "width": "100%",
                        "borderColor": "#F3DE8A",
                        "opacity": "unset",
                    }
                ),
                width={"size": 2},
            ),
            dbc.Col(
                html.Hr(
                    style={
                        "borderWidth": "2vh",
                        "width": "100%",
                        "borderColor": "#EB9486",
                        "opacity": "unset",
                    }
                ),
                width={"size": 2},
            ),
            dbc.Col(
                html.Hr(
                    style={
                        "borderWidth": "2vh",
                        "width": "100%",
                        "borderColor": "#7E7F9A",
                        "opacity": "unset",
                    }
                ),
                width={"size": 2},
            ),
            dbc.Col(
                html.Hr(
                    style={
                        "borderWidth": "2vh",
                        "width": "100%",
                        "borderColor": "#97A7B3",
                        "opacity": "unset",
                    }
                ),
                width={"size": 2},
            ),
        ],
        className="g-0",
        style={"width": "120%"},
    ),
    # Title
    dbc.Row(
        [
            html.H3("Solar Geneva", style={"color": "#7E7F9A"}),
        ],
    ),
    # Subtitle
    dbc.Row(
        [
            html.H5("Expansion des capacités photovoltaïques dans le canton de Genève", style={"color": "#97A7B3"}),
        ],
    ),
    # Yellow line
    dbc.Row(
        dbc.Col(
            html.Hr(
                style={
                    "borderWidth": "0.5vh",
                    "width": "100%",
                    "borderColor": "#F3DE8A",
                    "opacity": "unset",
                }
            ),
            width={"size": 12, "offset": 0},
        ),
    ),
    # Potential input
    dcc.Markdown('''
            ##### Potentiel solaire total
            Le potentiel de production solaire du territoire genevois peut être calibré à :
        '''),
    dcc.RadioItems(
        id='potential-input',
        options=[
            {'label': html.Span([" 1000 [MWc], soit 1000 [GWh/an], selon le ",
                                 html.A("Plan directeur de l'énergie 2020-2030", href="https://www.ge.ch/document/plan-directeur-energie-2020-2030",
                                        target="_blank")]), 'value': 3},
            {'label': html.Span(
                [" 3000 [MWc], soit 3000 [GWh/an], selon ",
                 html.A("Toit solaire", href="https://www.uvek-gis.admin.ch/BFE/sonnendach/?lang=fr", target="_blank")]),
                'value': 1},
        ],
        value=3,
        labelStyle={'display': 'block'}  # To display each option on a new line
    ),
    # Yellow line
    dbc.Row(
        dbc.Col(
            html.Hr(
                style={
                    "borderWidth": "0.5vh",
                    "width": "100%",
                    "borderColor": "#F3DE8A",
                    "opacity": "unset",
                }
            ),
            width={"size": 12, "offset": 0},
        ),
    ),

    # Selection side by side
    dbc.Row([
        # Granularity input
        dbc.Col(
            [
                dcc.Markdown("##### Découpage du territoire"),
                dcc.RadioItems(
                    id='granularity-input',
                    options=[
                        {'label': ' Communes', 'value': "communes"},
                        {'label': ' Sous-secteurs statistiques (GIREC)', 'value': "girec"},
                    ],
                    value="communes",
                    inline=True,
                    labelStyle={'margin-right': '10px'}  # Add space between options
                ),
            ],
            width=5
        ),
        # Borders input
        dbc.Col(
            [
                dcc.Markdown("##### Frontières des communes"),
                dcc.RadioItems(
                    id='borders-input',
                    options=[
                        {'label': ' Afficher', 'value': True},
                        {'label': ' Masquer', 'value': False},
                    ],
                    value=False,
                    inline=True,
                    labelStyle={'margin-right': '10px'}  # Add space between options
                ),
            ],
            width={"size": 5, "offset": 2}  # Offset to start at the middle
        ),
    ], className="g-2"),
    # Yellow line
    dbc.Row(
        dbc.Col(
            html.Hr(
                style={
                    "borderWidth": "0.5vh",
                    "width": "100%",
                    "borderColor": "#F3DE8A",
                    "opacity": "unset",
                }
            ),
            width={"size": 12, "offset": 0},
        ),
    ),
    # Selection side by side
    dbc.Row([
        # Metric input
        dbc.Col(
            [
                dcc.Markdown("##### Carte à afficher"),
                dcc.RadioItems(
                    id='metric-input',
                    options=[
                        {'label': ' Potentiel installable [MWc]', 'value': "potential"},
                        {'label': ' Capacité installée [MWc]', 'value': "power"},
                        {'label': ' Ratio capacité installée / potentiel installable [%]', 'value': "ratio"},
                    ],
                    value="ratio",
                ),
            ],
            width=5
        ),
        # Range scale input
        dbc.Col(
            [
                dcc.Markdown("##### Échelle"),
                dcc.Input(
                    id='min-value-input',
                    type='number',
                    placeholder='Min',
                    value=None,
                    style={'margin-left': '0x', 'margin-right': '10px'}  # Adds some spacing
                ),
                dcc.Input(
                    id='max-value-input',
                    type='number',
                    placeholder='Max',
                    value=None
                ),
            ],
            width={"size": 5, "offset": 2}  # Offset to start at the middle
        ),
    ], className="g-2"),
    # Yellow line
    dbc.Row(
        dbc.Col(
            html.Hr(
                style={
                    "borderWidth": "0.5vh",
                    "width": "100%",
                    "borderColor": "#F3DE8A",
                    "opacity": "unset",
                }
            ),
            width={"size": 12, "offset": 0},
        ),
    ),
    # Tabs
    dbc.Tabs(
        [
            dbc.Tab(
                label="Statistiques 2005-2024",
                tab_id="tab-past",
                label_style={"color": "#080808"},
                tab_style={"background-color": "##a5cbe8"},
                active_label_style={"background-color": "#F3DE8A"},
            ),
            dbc.Tab(
                label="Tendances 2025-2050",
                tab_id="tab-future",
                label_style={"color": "#080808"},
                tab_style={"background-color": "##a5cbe8"},
                active_label_style={"background-color": "#F3DE8A"},
            ),
        ],
        id="tabs",
        active_tab="tab-future",
    ),

    html.Div(id="tabs-content", className="p-5"),

])


# Callback to update content based on selected tab
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'active_tab'),
    Input('metric-input', 'value'),
)
def render_content(tab, metric):
    if tab == 'tab-past':
        min_year = 2005
        max_year = 2024
    else:
        min_year = 2025
        max_year = 2050

    return html.Div([

        html.Div(
            [
                dcc.Markdown("##### Sélection de l'année"),
                dcc.Slider(
                    id='year-input',
                    min=min_year,
                    max=max_year,
                    step=1,
                    value=2025,
                    marks={year: str(year) for year in range(min_year, max_year + 1) if year % 5 == 0},  # marks for multiples of 5
                    tooltip={"placement": "bottom",
                             "always_visible": True,
                             "style": {"fontSize": "18px"},
                             },
                )],
            className='slider-container',
            style={'display': 'block' if metric != 'potential' else 'none'},
        ),

        # Main map at the top
        dcc.Graph(id='map'),

        # Model selection
        html.Div([
            dbc.Row(
                dbc.Col(
                    html.Hr(
                        style={
                            "borderWidth": "0.2vh",
                            "width": "100%",
                            "borderColor": "#97A7B3",
                            "opacity": "unset",
                        }
                    ),
                    width={"size": 12, "offset": 0},
                ),
            ),
            dcc.Markdown("##### Modèle de croissance"),
            dcc.RadioItems(
                id='model-input',
                options=[
                    {'label': ' Linéaire', 'value': "linear"},
                    {'label': ' Exponentiel (objectif 1 MWc)', 'value': "exponential"},
                ],
                value="linear")],
            style={'display': 'block' if tab == 'tab-future' else 'none'}
        ),

        dbc.Row(
            dbc.Col(
                html.Hr(
                    style={
                        "borderWidth": "0.2vh",
                        "width": "100%",
                        "borderColor": "#97A7B3",
                        "opacity": "unset",
                    }
                ),
                width={"size": 12, "offset": 0},
            ),
        ),

        # Plots on top and bottom
        dcc.Graph(id='plot-expansion'),
        dcc.Graph(id='plot-share'),

    ])


# Callback to update the map based on selected year and granularity
@app.callback(
    Output('map', 'figure'),
    Input('year-input', 'value'),
    Input('granularity-input', 'value'),
    Input('borders-input', 'value'),
    Input('metric-input', 'value'),
    Input('model-input', 'value'),
    Input('potential-input', 'value'),
    Input('min-value-input', 'value'),
    Input('max-value-input', 'value'),
)
def update_map(year, granularity, show_borders, metric, model, potential_scaling, min_scale, max_scale):
    if granularity == "communes" and model == "linear":
        data = communes_lin
    elif granularity == "communes" and model == "exponential":
        data = communes_exp
    elif granularity == "girec" and model == "linear":
        data = girec_lin
    else:
        data = girec_exp

    data["potential"] = data["pv_potential"] / potential_scaling

    if metric == "potential":
        data_to_plot = "potential"
        units = "MWc"
        color_scale = "oranges"
    elif metric == "power":
        data_to_plot = year
        units = "MWc"
        color_scale = "oranges"
    else:
        data["ratio"] = 100 * data[year] / data["potential"]
        data_to_plot = "ratio"
        units = "%"

        if year < 2025:
            color_scale = "blues"
        else:
            objective_2030 = 0.35
            objective_2050 = 0.95
            y_objective = objective_2030 + ((year - 2030) * (objective_2050 - objective_2030)) / (2050 - 2030)
            smoothing = 0.02 / y_objective
            color_scale = [
                (0.0, "darkred"),
                (y_objective - smoothing, "lightcoral"),
                (y_objective + smoothing, "lightgreen"),
                (1.0, "darkgreen"),
            ]

    try:
        range_for_plot = [min_scale, max_scale]
    except TypeError:
        range_for_plot = None

    fig = px.choropleth_mapbox(
        data_frame=data,
        geojson=data.geometry.__geo_interface__,
        locations=data.index,
        color=data_to_plot,
        range_color=range_for_plot,
        color_continuous_scale=color_scale,
        opacity=0.7,
        mapbox_style="open-street-map",
        center={"lat": 46.2250, "lon": 6.1432},
        zoom=10.9,
        labels={str(data_to_plot): units}
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=800, width=1200)

    if show_borders:
        for geom in borders.geometry:
            if geom.geom_type == 'Polygon':
                x, y = geom.exterior.xy
            elif geom.geom_type == 'MultiPolygon':
                # Commune Céligny has multiple polygons
                for polygon in geom.geoms:
                    x, y = polygon.exterior.xy

            fig.add_trace(
                go.Scattermapbox(
                    lon=list(x),
                    lat=list(y),
                    mode='lines',
                    line=dict(color='black', width=2),
                    hoverinfo='skip',
                    showlegend=False,
                )
            )

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
        title="Expansion des capacités photovoltaïques à Genève",
        labels={"x": "Année", "y": "[MWc]"},
        template="plotly_white"
    )
    fig_expansion.update_traces(line=dict(color="orange"), mode="lines+markers")

    fig_expansion.add_trace(
        go.Scatter(
            x=[2030, 2050],
            y=[350, 1000],
            mode="markers+text",
            marker=dict(color="green", size=10, symbol="circle"),
            text=["<b>Objectif 2030<br>350 MWc</b>", "<b>Objectif 2050<br>1000 MWc</b>"],
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
