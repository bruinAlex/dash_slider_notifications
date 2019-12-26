import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import pandas as pd 
import numpy as np 
import datetime
from datetime import timedelta, date, datetime
import time
import severity_processing

df = pd.read_csv("data/mock_single_server_error_data.csv")

epoch = datetime.utcfromtimestamp(0)

def unix_time_millis(dt):
	return (dt - epoch).total_seconds() #* 1000.0

daterange = pd.date_range(start='2020-01-01',end='2020-01-31',freq='D')

def unixTimeMillis(dt):
	''' Convert datetime to unix timestamp '''
	return int(time.mktime(dt.timetuple()))

def unixToDatetime(unix):
	''' Convert unix timestamp to datetime. '''
	return pd.to_datetime(unix,unit='s')

def getMarks(start, end, Nth=100):
	''' Returns the marks for labeling. 
		Every Nth value will be used.
	'''
	result = {}
	for i, date in enumerate(daterange):
		# Skip every other label due to space
		if i % 2 == 0:
			result[unixTimeMillis(date)] = {'label': str(date.strftime('%d')),
				'style': {
						'writing-mode': 'vertical-lr',
						'text-orientation': 'sideways'
					}
				}
		else:
			result[unixTimeMillis(date)] = {'label': ''}
	return result


navbar = dbc.NavbarSimple(
	children=[],
	brand="Site Name",
	brand_href="#",
	sticky="top",
	color="#F0F0F0"
)

body = dbc.Container(
	[
		dbc.Row(
			[
				dbc.Col(
					[
						html.H2("Header"),
						html.P(
							"""
							Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque 
							eleifend arcu eu massa pharetra venenatis. Quisque ac augue posuere sem pulvinar 
							sollicitudin nec auctor mi.
							"""
						),
						dbc.Row([
								dbc.Col([
										html.H4("Date Slider"),
									]),
								dbc.Col([
										html.H4(html.Div(id='date-display-div')),
									])
							]),
						html.Div(
							dcc.Slider(
								id = 'date_slider',
								min = unixTimeMillis(daterange.min()),
								max = unixTimeMillis(daterange.max()),
								value = unixTimeMillis(daterange.min()),
								marks = getMarks(daterange.min(),
											daterange.max()),
								step = None,
							),
							style = {
								'margin-bottom': '40px'
							}
						),
						# Data table
						html.Div(id='table'),
					],
					md=4,
				),
				dbc.Col(
					[
						html.Div(id='test-display'),
					]
				),
			]
		),
	],
	className="mt-4",
)


app = dash.Dash(__name__, external_stylesheets=["assets/bootstrap.min.css"]) 

app.layout = html.Div([navbar, body])

# Converts the unix date to human-readable
@app.callback(
	Output(component_id='date-display-div', component_property='children'),
	[Input(component_id='date_slider', component_property='value')]
)
def update_date_output_div(input_value):
	converted_utc_date = datetime.utcfromtimestamp(input_value).strftime('%b %d, %Y')
	return f"{converted_utc_date}"


def severity_key_sort(dict):
	"""
	Arbitrary sort of keys
	"""
	keys = dict.keys()
	sorted_keys = []
	if 'Critical' in keys:
		sorted_keys.append('Critical')
	if 'High' in keys:
		sorted_keys.append('High') 
	if 'Moderate' in keys:
		sorted_keys.append('Moderate') 
	if 'Low' in keys:
		sorted_keys.append('Low') 

	return sorted_keys

@app.callback(
	[Output(component_id='test-display', component_property='children'),
	Output('table', component_property='children')],
	[Input(component_id='date_slider', component_property='value')],
	)
# def dict2item(dict):
def dict2item(date, df=df):
	# Convert the date
	converted_utc_date = datetime.utcfromtimestamp(date).strftime('%Y-%m-%d')

	# Create a slice with recent trailing days
	sliced_df = severity_processing.trailing_days_df(df=df, date=converted_utc_date, trailing_days=3)

	# Create data table
	data_table = dash_table.DataTable(
		id='data-table',
		columns=[{'name': i, 'id': i} for i in sliced_df.columns],
		data=sliced_df.to_dict('records'),
		style_as_list_view=True,
		style_cell={'textAlign': 'center'},
	    style_cell_conditional=[
	        {
	            'if': {'column_id': 'date'},
	            'textAlign': 'left'
	        },
	        {
	        	'if': {'column_id': 'server'},
	        	'textAlign': 'right'
	        },
	    ],
	    style_data_conditional=[ # Highlight the selected day's data row in the table
	        {
	            'if': {'row_index': (sliced_df.shape[0] - 1)},  # Get the last row of the table
		        "backgroundColor": "#ababab",
		        'color': 'white'
	        }
	    ],
		)


	# Break if df is empty
	if not sliced_df.shape:
		return None, data_table

	# Calc severity for that slice
	severity = severity_processing.categorized_error_dict(sliced_df)

	# keys = dict.keys()
	# keys = severity.keys()
	keys = severity_key_sort(severity)
	cards = []

	if keys: # If there are warnings
		for key in keys:
			# Build the card for each key
			card = make_severity_item(key, severity)
			cards.append(card)
	else:
		cards.append(html.H3(
			"No problems found!",
			style = {
				'textAlign': 'center',
				'color': '#347834'
			}
			))

	return cards, data_table


def make_listgroupitem(item_list):
	"""
	Create a nicely formated list in the cardbody
	"""
	listgroupitem = []
	for el in item_list:
		listgroupitem.append(dbc.ListGroupItem(el,
			# Blocks the default white background color and sets bg to transparent
			style={
        		'backgroundColor': "rgba(255, 255, 255, 0)"
        	}))
	return listgroupitem


def severity_color(severity):
	color_mapping = {
		'Critical': "danger",
		'High': "warning",
		'Moderate': "info",
		'Low': 'light'
	}
	return color_mapping[severity]


def severity_text_inverse(severity):
	color_mapping = {
		'Critical': True,
		'High': True,
		'Moderate': True,
		'Low': False
	}
	return color_mapping[severity]

def severity_header_text_color(severity):
	color_mapping = {
		'Critical': "white",
		'High': "white",
		'Moderate': "white",
		'Low': "#383838"
	}
	return color_mapping[severity]

def make_severity_item(key, dict):
    """
 	Create the severity cards
    """

    # Get the list of items for each severity level
    rows = []
    for el in dict[key]:
    	rows.append(el)

    # Make the list of contents for dbc.ListGroup()
    dbc_listgroupitem = make_listgroupitem(rows)

    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4(
                	f"{key}",
                	style = {
                		'color': severity_header_text_color(key)
                	}
                ),
            ),
            dbc.CardBody(
                dbc.ListGroup(
                	dbc_listgroupitem,
        			flush=True,
    			),
            ),


        ],
        color = severity_color(key), 
        inverse = severity_text_inverse(key),
    ) 

if __name__ == "__main__":
	app.run_server(debug=True)