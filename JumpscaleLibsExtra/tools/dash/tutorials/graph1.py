import dash
import dash_core_components as dcc
import dash_html_components as html

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

markdown_text = """
### Dash and Markdown

Dash apps can be written in Markdown.
Dash uses the [CommonMark](http://commonmark.org/)
specification of Markdown.

Check out their [60 Second Markdown Tutorial](http://commonmark.org/help/)
if this is your first introduction to Markdown!
"""


app.layout = html.Div(
    children=[
        html.H1(children="Hello Dash"),
        html.Div(
            children="""
        Dash: A web application framework for Python.
    """
        ),
        dcc.Graph(id="graph"),
        dcc.Slider(id="slider", min=0, max=10, step=0.5, value=3),
        dcc.Slider(id="slider2", min=0, max=10, step=0.5, value=3),
    ]
)


@app.callback(
    dash.dependencies.Output("graph", "figure"),
    [dash.dependencies.Input("slider", "value"), dash.dependencies.Input("slider2", "value")],
)
def update_output(value, value2):
    return {
        "data": [
            {"x": [1, 2, 3], "y": [1, 1, value2], "type": "bar", "name": "SF"},
            {"x": [1, 2, 3], "y": [2, 4, value], "type": "bar", "name": "Montréal"},
        ],
        "layout": {"title": "..."},
    }


def main():
    app.run_server(debug=True)
