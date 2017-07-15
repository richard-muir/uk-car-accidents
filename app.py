import os
from random import randint

import dash
import flask

from dash.dependencies import Input, Output
from dash_core_components import Graph, Checklist, RangeSlider
from dash_html_components import Div, H1, H3

from pandas import read_csv, DataFrame

MAPBOX = 'pk.eyJ1Ijoicm11aXIiLCJhIjoiY2o1MjBxcnkwMDdnZTJ3bHl5bXdxNW9uaCJ9.QR6f0fRLkHzmCgL70u5Hzw'
SEVERITY_LOOKUP = {'Fatal' : 'red',
                    'Serious' : 'orange',
                    'Slight' : 'yellow'}
SLIGHT_FRAC = 0.1
SERIOUS_FRAC = 0.5
DAYSORT = dict(zip(['Friday', 'Monday', 'Saturday','Sunday', 'Thursday', 'Tuesday', 'Wednesday'],
                  [4, 0, 5, 6, 3, 1, 2]))

FONT_FAMILY =  "Arial"

RIGHTBOX_CSS = {}



acc = read_csv('https://raw.githubusercontent.com/richard-muir/uk-car-accidents/master/accidents2015_V.csv', index_col = 0).dropna(how='any', axis = 0)
acc['Hour'] = acc['Time'].apply(lambda x: int(x[:2]))



server = flask.Flask(__name__)
server.secret_key = os.environ.get('secret_key', str(randint(0, 1000000)))
app = dash.Dash(__name__, server=server)


#app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

app.layout = Div([
    H1(
        'Traffic Accidents in the UK',
        style={
            'paddingLeft' : 50,
            'fontFamily' : FONT_FAMILY
            }
        ),
    #Div(id="my-div"),

    Div([   # Holds the map & the widgets
        Div([  # Holds the map
            Graph(id="map")
        ],
        style={
            "width" : '38%', 
            'display' : 'inline-block', 
            'paddingLeft' : 50, 
            'paddingRight' : 10,
            'boxSizing' : 
            'border-box'}
        ),
        Div([  # Holds the widgets & Descriptions
            H3(
                '''In 2015, the UK suffered {:,} traffic accidents, many of them fatal.'''.format(len(acc)),
                style={
                    'fontFamily' : FONT_FAMILY
                }
                ),
            Div(
                '''You can explore when and where the accidents happened using these filters.''',
                style={
                    }
                ),
            Div(
                '''Select the severity of the accident:''',
                style={
                    'paddingTop' : 20,
                    'paddingBottom' : 10
                }
            ),
            Checklist(
                options=[
                    {'label': sev, 'value': sev} for sev in acc['Accident_Severity'].unique()
                ],
                values=[sev for sev in acc['Accident_Severity'].unique()],
                labelStyle={
                    'display': 'inline-block',
                    'paddingRight' : 10,
                    'paddingLeft' : 10,
                    'paddingBottom' : 5,
                    },
                id="severityChecklist",
                
            ),
            Div(
                '''Select the day of the accident:''',
                style={
                    'paddingTop' : 20,
                    'paddingBottom' : 10
                }
            ),
            Checklist(
                options=[
                    {'label': day[:3], 'value': day} for day in sorted(acc['Day_of_Week'].unique(), key=lambda k: DAYSORT[k])
                ],
                values=[day for day in acc['Day_of_Week'].unique()],
                labelStyle={
                    'display': 'inline-block',
                    'paddingRight' : 10,
                    'paddingLeft' : 10,
                    'paddingBottom' : 5,
                    },
                id="dayChecklist",
            ),
            Div(
                '''Select the hours in which the accident occurred (24h clock):''',
                style={
                    'paddingTop' : 20,
                    'paddingBottom' : 10
                }
            ),
            RangeSlider(
                id="hourSlider",
                count=1,
                min=-acc['Hour'].min(),
                max=acc['Hour'].max(),
                step=1,
                value=[acc['Hour'].min(), acc['Hour'].max()],
                marks={str(h) : str(h) for h in range(acc['Hour'].min(), acc['Hour'].max() + 1)}
            )
        ],
        style={
            "width" : '58%', 
            'float' : 'right', 
            'display' : 'inline-block', 
            'paddingRight' : 50, 
            'paddingLeft' : 10,
            'boxSizing' : 'border-box',
            'fontFamily' : FONT_FAMILY
            })

    ],
    style={'paddingBottom' : 10}),

    Div([  # Holds the heatmap & barchart (60:40 split) 
        Div([  # Holds the heatmap
            Graph(id="heatmap",
            style={'height' : '50%'})
        ],
        style={
            "width" : '60%', 
            'float' : 'left', 
            'display' : 'inline-block', 
            'paddingRight' : 5, 
            'paddingLeft' : 50,
            'boxSizing' : 'border-box'
            }
        ),

        Div([  # Holds the barchart
            Graph(id="bar",
            style={'height' : '50%'})
        ],
        style={
            "width" : '40%', 
            'float' : 'right', 
            'display' : 'inline-block', 
            'paddingRight' : 50, 
            'paddingLeft' : 5,
            'boxSizing' : 'border-box'
            })

    ])
])

@app.callback(
    Output(component_id='bar', component_property='figure'),
    [Input(component_id='severityChecklist', component_property='values'),
    Input(component_id='dayChecklist', component_property='values'),
    Input(component_id='hourSlider', component_property='value'),
    ]
)
def updateBarChart(severity, weekdays, time):
    print(severity)

    hours = [i for i in range(time[0], time[1]+1)]
    
    acc2 = DataFrame(acc[[
        'Accident_Severity','Speed_limit','Number_of_Casualties']][
            (acc['Accident_Severity'].isin(severity)) & 
            (acc['Day_of_Week'].isin(weekdays)) & 
            (acc['Hour'].isin(hours))
            ].groupby(['Accident_Severity','Speed_limit']).sum()).reset_index()

    def barText(row):
        return 'Speed Limit: {}mph<br>{:,} {} accidents'.format(row['Speed_limit'],
                                                                row['Number_of_Casualties'],
                                                                row['Accident_Severity'].lower())
    acc2['text'] = acc2.apply(barText, axis=1)

    traces = []
    for sev in severity:
        traces.append({
            'type' : 'bar',
            'y' : acc2['Number_of_Casualties'][acc2['Accident_Severity'] == sev],
            'x' : acc2['Speed_limit'][acc2['Accident_Severity'] == sev],
            'text' : acc2['text'][acc2['Accident_Severity'] == sev],
            'hoverinfo' : 'text',
            'marker' : {
                'color' : SEVERITY_LOOKUP[sev],
            'line' : {'width' : 2,
                      'color' : '#333'}},
            'name' : sev,
        })
        
    fig = {'data' : traces,
          'layout' : {
              'height' : 300,
              'title' : 'Accidents by speed limit',
              'margin' : {
                  'b' : 25,
                  'l' : 30,
                  't' : 70,
                  'r' : 0
              },
              'legend' : {
                  'orientation' : 'h',
                  'x' : 0,
                  'y' : 1.01,
                  'yanchor' : 'bottom',
                  },
            'xaxis' : {
                'tickvals' : sorted(acc2['Speed_limit'].unique()),
                'ticktext' : sorted(acc2['Speed_limit'].unique()),
                'tickmode' : 'array'
            }
          }}
    
    return fig



@app.callback(
    Output(component_id='heatmap', component_property='figure'),
    [Input(component_id='severityChecklist', component_property='values'),
    Input(component_id='dayChecklist', component_property='values'),
    Input(component_id='hourSlider', component_property='value'),
    ]
)
def updateHeatmap(severity, weekdays, time):
    hours = [i for i in range(time[0], time[1] + 1)]
    acc2 = DataFrame(acc[[
        'Day_of_Week', 'Hour','Number_of_Casualties']][
            (acc['Accident_Severity'].isin(severity)) & 
            (acc['Day_of_Week'].isin(weekdays)) & 
            (acc['Hour'].isin(hours))
            ].groupby(['Day_of_Week', 'Hour']).sum()).reset_index()

    def heatmapText(row):
        return 'Day : {}<br>Time : {:02d}:00<br>Number of casualties: {}'.format(row['Day_of_Week'],
                                                                                row['Hour'], 
                                                                                row['Number_of_Casualties'])
    acc2['text'] = acc2.apply(heatmapText, axis=1)
    
    days = sorted(acc2['Day_of_Week'].unique(), key=lambda k: DAYSORT[k])

    z = []
    text = []
    for d in days:
        row = acc2['Number_of_Casualties'][acc2['Day_of_Week'] == d].values.tolist()
        t = acc2['text'][acc2['Day_of_Week'] == d].values.tolist()
        z.append(row)
        text.append(t)
    traces = [{
        'type' : 'heatmap',
        'x' : hours,
        'y' : days,
        'z' : z,
        'text' : text,
        'hoverinfo' : 'text',
        'colorscale' : 'Electric',
    }]
        
    fig = {'data' : traces,
          'layout' : {
              'height' : 300,
              'title' : 'Accidents by time and day',
              'margin' : {
                  'b' : 50,
                  'l' : 70,
                  't' : 50,
                  'r' : 0,
              },
              'xaxis' : {
                  'ticktext' : hours,
                  'tickvals' : hours,
                  'tickmode' : 'array', 
              }
          }}
    return fig




@app.callback(
    Output(component_id='map', component_property='figure'),
    [Input(component_id='severityChecklist', component_property='values'),
    Input(component_id='dayChecklist', component_property='values'),
    Input(component_id='hourSlider', component_property='value'),
    ]
)
def updateMapBox(severity, weekdays, time):
    hours = [i for i in range(time[0], time[1]+1)]
    acc2 = acc[
            (acc['Accident_Severity'].isin(severity)) &
            (acc['Day_of_Week'].isin(weekdays)) & 
            (acc['Hour'].isin(hours))
            ]

    traces = []

    for sev in sorted(severity, reverse=True):
        sample = 1
        if sev == 'Slight':
            sample = SLIGHT_FRAC
        elif sev == 'Serious':
            sample = SERIOUS_FRAC
            
        acc3 = acc2.sample(frac=sample)
            
        traces.append({
            'type' : 'scattermapbox',
            'mode' : 'markers',
            'lat' : acc3['Latitude'][acc3['Accident_Severity'] == sev],
            'lon' : acc3['Longitude'][acc3['Accident_Severity'] == sev],
            'marker' : {
                'color' : SEVERITY_LOOKUP[sev],
                'size' : 2,
            
            },
            'hoverinfo' : 'text',
            'name' : sev,
            'legendgroup' : sev,
            'showlegend' : False,
            'text' : acc3['Local_Authority_(District)'][acc3['Accident_Severity'] == sev]
        })
        
        traces.append({
            'type' : 'scattermapbox',
            'mode' : 'markers',
            'lat' : [0],
            'lon' : [0],
            'marker' : {
                'color' : SEVERITY_LOOKUP[sev],
                'size' : 10,
            
            },
            'name' : sev,
            'legendgroup' : sev,
            
        })
    layout = {
        #'width' : 300,
        'height' : 300,
        'paper_bgcolor' : 'rgb(26,25,25)',
        'autosize' : True,
        'hovermode' : 'closest',
        'mapbox' : {
            'accesstoken' : MAPBOX,
            'center' : {
                'lat' : 54.5,
                'lon' : -2
            },
            'zoom' : 3.5,
            'style' : 'dark',   
        },
        'margin' : {'t' : 0,
                   'b' : 0,
                   'l' : 0,
                   'r' : 0},
        'legend' : {
            'font' : {'color' : 'white'},
             'orientation' : 'h',
             'x' : 0,
             'y' : 1.01
        }
    }
    fig = dict(data=traces, layout=layout)
    return fig




# Run the Dash app
if __name__ == '__main__':
    app.server.run(debug=True, threaded=True)


