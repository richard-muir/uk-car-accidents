import os
from random import randint

import dash
import flask

from dash.dependencies import Input, Output, State, Event
import dash_core_components as dcc
import dash_html_components as html

from pandas import read_csv, DataFrame

### GLOBALS, DATA & INTIALISE THE APP ###

# Mapbox key to display the map
MAPBOX = 'pk.eyJ1Ijoicm11aXIiLCJhIjoiY2o1MjBxcnkwMDdnZTJ3bHl5bXdxNW9uaCJ9.QR6f0fRLkHzmCgL70u5Hzw'

# Make the colours consistent for each type of accident
SEVERITY_LOOKUP = {'Fatal' : 'red',
                    'Serious' : 'orange',
                    'Slight' : 'yellow'}

# Need to downsample the number of Slight and Serious accidents to display them 
# on the map. These fractions reduce the number plotted to about 10k.
# There are only about 10k fatal accidents so don't need to downsample these
SLIGHT_FRAC = 0.1
SERIOUS_FRAC = 0.5

# This dict allows me to sort the weekdays in the right order
DAYSORT = dict(zip(['Friday', 'Monday', 'Saturday','Sunday', 'Thursday', 'Tuesday', 'Wednesday'],
                  [4, 0, 5, 6, 3, 1, 2]))

# Set the global font family
FONT_FAMILY =  "Arial" 


# Read in data from csv stored on github
#csvLoc = 'accidents2015_V.csv'  
csvLoc = 'https://raw.githubusercontent.com/richard-muir/uk-car-accidents/master/accidents2015_V.csv'
acc = read_csv(csvLoc, index_col = 0).dropna(how='any', axis = 0)
# Remove observations where speed limit is 0 or 10. There's only three and it adds a lot of 
#  complexity to the bar chart for no material benefit
acc = acc[~acc['Speed_limit'].isin([0, 10])]
# Create an hour column
acc['Hour'] = acc['Time'].apply(lambda x: int(x[:2]))


# Set up the Dash instance. Big thanks to @jimmybow for the boilerplate code
server = flask.Flask(__name__)
server.secret_key = os.environ.get('secret_key', 'secret')
app = dash.Dash(__name__, server=server)
app.config.supress_callback_exceptions = True

# Include the external CSS
cssURL = "https://rawgit.com/richard-muir/uk-car-accidents/master/road-safety.css"
app.css.append_css({
    "external_url": cssURL
})

## SETTING UP THE APP LAYOUT ##

# Main layout container
app.layout = html.Div([
    html.H1(
        'Traffic Accidents in the UK',
        style={
            'paddingLeft' : 50,
            'fontFamily' : FONT_FAMILY
            }
        ),
    html.Div([   # Holds the widgets & Descriptions

        html.Div([  

            html.H3(
                '''In 2015, the UK suffered {:,} traffic accidents, many of them fatal.'''.format(len(acc)),
                style={
                    'fontFamily' : FONT_FAMILY
                }
                ),
            html.Div(
                '''You can explore when and where the accidents happened using these filters.''',
                ),
            html.Div(
                '''Select the severity of the accident:''',
                style={
                    'paddingTop' : 20,
                    'paddingBottom' : 10
                }
            ),
            dcc.Checklist( # Checklist for the three different severity values
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
            html.Div(
                '''Select the day of the accident:''',
                style={
                    'paddingTop' : 20,
                    'paddingBottom' : 10
                }
            ),
            dcc.Checklist( # Checklist for the dats of week, sorted using the sorting dict created earlier
                options=[
                    {'label': day[:3], 'value': day} for day in sorted(acc['Day_of_Week'].unique(), key=lambda k: DAYSORT[k])
                ],
                values=[day for day in acc['Day_of_Week'].unique()],
                labelStyle={  # Different padding for the checklist elements
                    'display': 'inline-block',
                    'paddingRight' : 10,
                    'paddingLeft' : 10,
                    'paddingBottom' : 5,
                    },
                id="dayChecklist",
            ),
            html.Div(
                '''Select the hours in which the accident occurred (24h clock):''',
                style={
                    'paddingTop' : 20,
                    'paddingBottom' : 10
                }
            ),
            dcc.RangeSlider( # Slider to select the number of hours
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
            "width" : '60%', 
            'display' : 'inline-block', 
            'paddingLeft' : 50, 
            'paddingRight' : 10,
            'boxSizing' : 'border-box',
            }
        ),
        
        html.Div([  # Holds the map & the widgets

            dcc.Graph(id="map") # Holds the map in a div to apply styling to it
            
        ],
        style={
            "width" : '40%', 
            'float' : 'right', 
            'display' : 'inline-block', 
            'paddingRight' : 50, 
            'paddingLeft' : 10,
            'boxSizing' : 'border-box',
            'fontFamily' : FONT_FAMILY
            })

    ],
    style={'paddingBottom' : 20}),

    html.Div([  # Holds the heatmap & barchart (60:40 split) 
        html.Div([  # Holds the heatmap
            dcc.Graph(
                id="heatmap",
            ),
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
        html.Div([  # Holds the barchart
            dcc.Graph(
                id="bar",
            )
            #style={'height' : '50%'})
        ],
        style={
            "width" : '40%', 
            'float' : 'right', 
            'display' : 'inline-block', 
            'paddingRight' : 50, 
            'paddingLeft' : 5,
            'boxSizing' : 'border-box'
            })

    ]),
    html.Div([
        # Add a source annotation and a note for the downsampling
        html.Div(
            'Source: https://data.gov.uk/dataset/road-accidents-safety-data',
            style={
                'fontFamily' : FONT_FAMILY,
                'fontSize' : 8,
                'fontStyle' : 'italic'
            }),
        html.Div(
            'Note: Serious and slight accidents were downsampled to allow for speedier map plotting. Other charts are unaffected.',
            style={
                'fontFamily' : FONT_FAMILY,
                'fontSize' : 8,
                'fontStyle' : 'italic'
            }
        )])
])

## APP INTERACTIVITY THROUGH CALLBACK FUNCTIONS TO UPDATE THE CHARTS ##

# Callback function passes the current value of all three filters into the update functions.
# This on updates the bar.
@app.callback(
    Output(component_id='bar', component_property='figure'),
    [Input(component_id='severityChecklist', component_property='values'),
    Input(component_id='dayChecklist', component_property='values'),
    Input(component_id='hourSlider', component_property='value'),
    ]
)
def updateBarChart(severity, weekdays, time):
    # The rangeslider is selects inclusively, but a python list stops before the last number in a range
    hours = [i for i in range(time[0], time[1]+1)]
    
    # Create a copy of the dataframe by filtering according to the values passed in.
    # Important to create a copy rather than affect the global object.
    acc2 = DataFrame(acc[[
        'Accident_Severity','Speed_limit','Number_of_Casualties']][
            (acc['Accident_Severity'].isin(severity)) & 
            (acc['Day_of_Week'].isin(weekdays)) & 
            (acc['Hour'].isin(hours))
            ].groupby(['Accident_Severity','Speed_limit']).sum()).reset_index()

    # Create the field for the hovertext. Doing this after grouping, rather than
    #  immediately after loading the df. Should be quicker this way.
    def barText(row):
        return 'Speed Limit: {}mph<br>{:,} {} accidents'.format(row['Speed_limit'],
                                                                row['Number_of_Casualties'],
                                                                row['Accident_Severity'].lower())
    acc2['text'] = acc2.apply(barText, axis=1)

    # One trace for each accidents severity
    traces = []
    for sev in severity:
        traces.append({
            'type' : 'bar',
            'y' : acc2['Number_of_Casualties'][acc2['Accident_Severity'] == sev],
            'x' : acc2['Speed_limit'][acc2['Accident_Severity'] == sev],
            'text' : acc2['text'][acc2['Accident_Severity'] == sev],
            'hoverinfo' : 'text',
            'marker' : {
                'color' : SEVERITY_LOOKUP[sev], # Use the colur lookup for consistency
            'line' : {'width' : 2,
                      'color' : '#333'}},
            'name' : sev,
        })  
        
    fig = {'data' : traces,
          'layout' : {
              'paper_bgcolor' : 'rgb(26,25,25)',
              'plot_bgcolor' : 'rgb(26,25,25)',
              'font' : {
                  'color' : 'rgb(250,250,250'
              },
              'height' : 300,
              'title' : 'Accidents by speed limit',
              'margin' : { # Set margins to allow maximum space for the chart
                  'b' : 25,
                  'l' : 30,
                  't' : 70,
                  'r' : 0
              },
              'legend' : { # Horizontal legens, positioned at the bottom to allow maximum space for the chart
                  'orientation' : 'h',
                  'x' : 0,
                  'y' : 1.01,
                  'yanchor' : 'bottom',
                  },
            'xaxis' : {
                'tickvals' : sorted(acc2['Speed_limit'].unique()), # Force the tickvals & ticktext just in case
                'ticktext' : sorted(acc2['Speed_limit'].unique()),
                'tickmode' : 'array'
            }
          }}
    
    # Returns the figure into the 'figure' component property, update the bar chart
    return fig

# Pass in the values of the filters to the heatmap
@app.callback(
    Output(component_id='heatmap', component_property='figure'),
    [Input(component_id='severityChecklist', component_property='values'),
    Input(component_id='dayChecklist', component_property='values'),
    Input(component_id='hourSlider', component_property='value'),
    ]
)
def updateHeatmap(severity, weekdays, time):
    # The rangeslider is selects inclusively, but a python list stops before the last number in a range
    hours = [i for i in range(time[0], time[1] + 1)]
    # Take a copy of the dataframe, filtering it and grouping
    acc2 = DataFrame(acc[[
        'Day_of_Week', 'Hour','Number_of_Casualties']][
            (acc['Accident_Severity'].isin(severity)) & 
            (acc['Day_of_Week'].isin(weekdays)) & 
            (acc['Hour'].isin(hours))
            ].groupby(['Day_of_Week', 'Hour']).sum()).reset_index()

    # Apply text after grouping
    def heatmapText(row):
        return 'Day : {}<br>Time : {:02d}:00<br>Number of casualties: {}'.format(row['Day_of_Week'],
                                                                                row['Hour'], 
                                                                                row['Number_of_Casualties'])
    acc2['text'] = acc2.apply(heatmapText, axis=1)
    
    # Pre-sort a list of days to feed into the heatmap
    days = sorted(acc2['Day_of_Week'].unique(), key=lambda k: DAYSORT[k])

    # Create the z-values and text in a nested list format to match the shape of the heatmap
    z = []
    text = []
    for d in days:
        row = acc2['Number_of_Casualties'][acc2['Day_of_Week'] == d].values.tolist()
        t = acc2['text'][acc2['Day_of_Week'] == d].values.tolist()
        z.append(row)
        text.append(t)

    # Plotly standard 'Electric' colourscale is great, but the maximum value is white, as is the
    #  colour for missing values. I set the maximum to the penultimate maximum value, 
    #  then spread out the other. Plotly colourscales here: https://github.com/plotly/plotly.py/blob/master/plotly/colors.py

    Electric = [
        [0, 'rgb(0,0,0)'], [0.25, 'rgb(30,0,100)'],
        [0.55, 'rgb(120,0,100)'], [0.8, 'rgb(160,90,0)'],
        [1, 'rgb(230,200,0)']
        ]
    
    # Heatmap trace
    traces = [{
        'type' : 'heatmap',
        'x' : hours,
        'y' : days,
        'z' : z,
        'text' : text,
        'hoverinfo' : 'text',
        'colorscale' : Electric,
    }]
        
    fig = {'data' : traces,
          'layout' : {
              'paper_bgcolor' : 'rgb(26,25,25)',
              'font' : {
                  'color' : 'rgb(250,250,250'
              },
              'height' : 300,
              'title' : 'Accidents by time and day',
              'margin' : {
                  'b' : 50,
                  'l' : 70,
                  't' : 50,
                  'r' : 0,
              },
              'xaxis' : {
                  'ticktext' : hours, # for the tickvals and ticktext with one for each hour
                  'tickvals' : hours,
                  'tickmode' : 'array', 
              }
          }}
    return fig

# Feeds the filter outputs into the mapbox
@app.callback(
    Output(component_id='map', component_property='figure'),
    [Input(component_id='severityChecklist', component_property='values'),
    Input(component_id='dayChecklist', component_property='values'),
    Input(component_id='hourSlider', component_property='value'),
    ]
)
def updateMapBox(severity, weekdays, time):
    # List of hours again
    hours = [i for i in range(time[0], time[1]+1)]
    # Filter the dataframe
    acc2 = acc[
            (acc['Accident_Severity'].isin(severity)) &
            (acc['Day_of_Week'].isin(weekdays)) & 
            (acc['Hour'].isin(hours))
            ]

    # Once trace for each severity value
    traces = []
    for sev in sorted(severity, reverse=True):
        # Set the downsample fraction depending on the severity
        sample = 1
        if sev == 'Slight':
            sample = SLIGHT_FRAC
        elif sev == 'Serious':
            sample = SERIOUS_FRAC
        # Downsample the dataframe and filter to the current value of severity
        acc3 = acc2[acc2['Accident_Severity'] == sev].sample(frac=sample)
            
        # Scattermapbox trace for each severity
        traces.append({
            'type' : 'scattermapbox',
            'mode' : 'markers',
            'lat' : acc3['Latitude'],
            'lon' : acc3['Longitude'],
            'marker' : {
                'color' : SEVERITY_LOOKUP[sev], # Keep the colour consistent
                'size' : 2,
            },
            'hoverinfo' : 'text',
            'name' : sev,
            'legendgroup' : sev,
            'showlegend' : False,
            'text' : acc3['Local_Authority_(District)'] # Text will show location
        })
        
        # Append a separate marker trace to show bigger markers for the legend. 
        #  The ones we're plotting on the map are too small to be of use in the legend.
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
        'height' : 300,
        'paper_bgcolor' : 'rgb(26,25,25)',
              'font' : {
                  'color' : 'rgb(250,250,250'
              }, # Set this to match the colour of the sea in the mapbox colourscheme
        'autosize' : True,
        'hovermode' : 'closest',
        'mapbox' : {
            'accesstoken' : MAPBOX,
            'center' : {  # Set the geographic centre - trial and error
                'lat' : 54.5,
                'lon' : -2
            },
            'zoom' : 3.5,
            'style' : 'dark',   # Dark theme will make the colours stand out
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


