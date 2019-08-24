import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_ui as dui
from datetime import datetime as dt
from Jumpscale import j

external_stylesheets = [
    "https://codepen.io/rmarren1/pen/mLqGRg.css",
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    "https://use.fontawesome.com/releases/v5.1.0/css/all.css",
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


grid_top = dui.Grid("grid_top", num_rows=1, num_cols=2, grid_padding=2)
grid = dui.Grid("grid", num_rows=12, num_cols=2, grid_padding=2)

controlpanel = dui.ControlPanel("controlpanel")
controlpanel.create_group(group="State", group_title="Select Simulation.")


state_select = dcc.Dropdown(id="state-dropdown", options=[{"label": "test", "value": "A"}], value="A")
controlpanel.add_element(state_select, "State")

markdown_text = """
# Exit Bonus Simulation

### Remuneration 

Goal is to have a fair remuneration schema for everyone who contributes to the ThreeFold cause.

Some fixed parameters

- average 15 people worked over last 48 months on this project (much more at end, but is avg out).  
- 200m tokens are available when 1Billion marketcap
- 20m tokens when 1m USD liquidity at Jan 2020
- all simulations in USD
- 10% of TFTech shares allocated for pool (at this point)
- nr of people avg working on project 40 (starting now) growing to 120 over 4 years 
- avg big mac index = 3.5
- 100% acceleration for anyone becoming 60 years old.

"""

grid.add_element(col=0, row=0, width=2, height=1, element=dcc.Markdown(markdown_text))


def sliders():

    l = html.Div(
        children=[
            html.Div("nr of months contribution (starting Jan 2019)"),
            html.Br(),
            dcc.Slider(
                id="nrmonths", min=0, max=60, step=1, value=36, marks={i * 6: "{}".format(i * 6) for i in range(0, 11)}
            ),
            html.Br(),
            html.Div("nr of months untill ThreeFold will hit marketcap of 1billion"),
            dcc.Slider(
                id="slider_marketcap_months",
                min=6,
                max=48,
                step=1,
                value=16,
                marks={i * 6: "{}".format(i * 6) for i in range(0, 9)},
            ),
            html.Br(),
            html.Div("price of tokens at that point (0.1-5 USD)"),
            dcc.Slider(
                id="token_price", min=0, max=5, step=0.1, value=1, marks={i: "{}".format(i) for i in range(0, 5)}
            ),
            html.Br(),
            html.Div("exit value for ThreeFoldTech (in million USD)"),
            dcc.Slider(
                id="exitvalue_tftech",
                min=0,
                max=2000,
                step=100,
                value=1000,
                marks={i * 200: "{}m".format(i * 200) for i in range(0, 11)},
            ),
            html.Br(),
        ]
    )

    r = html.Div(
        children=[
            html.Div("nr of months you will be working for ThreeFold or related at end 2018 (calculated in full time)"),
            dcc.Slider(
                id="nr_months_past",
                min=0,
                max=48,
                step=1,
                value=16,
                marks={i * 4: "{}".format(i * 4) for i in range(0, 12)},
            ),
            html.Br(),
            html.Div("average contribution level for the past (2.5 is std)"),
            dcc.Slider(
                id="contr_level_past", min=0, max=5, step=0.5, value=2.5, marks={i: "{}".format(i) for i in range(0, 5)}
            ),
            html.Br(),
            html.Div("average contribution level for future (2.5 is std)"),
            dcc.Slider(
                id="contr_level_future",
                min=0,
                max=5,
                step=0.5,
                value=2.5,
                marks={i: "{}".format(i) for i in range(0, 5)},
            ),
            html.Br(),
            html.Div("% working (50% is halftime, ...)"),
            dcc.Slider(
                id="workingtime",
                min=0,
                max=100,
                step=10,
                value=100,
                marks={i * 20: "{}".format(i * 20) for i in range(1, 5)},
            ),
            html.Br(),
        ]
    )

    return html.Div(children=[l, r], style={"columnCount": 2})


def experience():
    return html.Div(
        children=[
            html.Br(),
            html.Br(),
            html.Div("Location where you live (defines the big mac index)"),
            dcc.Dropdown(
                id="location",
                options=[
                    {"label": "Egypt", "value": 2.5},
                    {"label": "Europe", "value": 5.2},
                    {"label": "Dubai", "value": 5},
                ],
                value=5.2,
            ),
            html.Br(),
            html.Div("Do we achieve 1m EUR liquidity on market for TFT in Jan 2020"),
            dcc.RadioItems(
                id="liquidity_yes_no", options=[{"label": "Yes", "value": 1}, {"label": "No", "value": 0}], value=1
            ),
            html.Br(),
            html.Br(),
            html.Div("Expected dilution of shares in TFTech"),
            dcc.Slider(
                id="dilution", min=0, max=50, step=5, value=30, marks={i * 5: "{}".format(i * 5) for i in range(0, 10)}
            ),
            html.Br(),
            html.Br(),
            html.Div("Do we achieve the Billion $ valuation for TF Tokens?"),
            dcc.RadioItems(
                id="billion_y_n", options=[{"label": "Yes", "value": 1}, {"label": "No", "value": 0}], value=1
            ),
        ],
        style={"columnCount": 2, "width": "1000", "textAlign": "center"},
    )


def graphs():
    return html.Div(
        children=[html.Br(), html.Br(), dcc.Graph(id="graph-tftech"), dcc.Graph(id="graph-personal"), html.Br()],
        style={"columnCount": 2, "width": "1000", "textAlign": "center"},
    )


markdown_text2 = """
## details

- Valuation ThreeFold Tech: {{res["chart_total_y"][0]}} million USD
- Valuation Liquidity at 2020 Jan: {{res["chart_total_y"][1]}} million USD
- Valuation Tokens : {{res["chart_total_y"][2]}} million USD 
- Valuation Total: {{res["chart_total_y"][3]}} million USD 
- total nr of points you collected: {{res["points_past"]+res["points_future"]}}    
    - points from the past: {{res["points_past"]}}
    - points from the future: {{res["points_future"]}}
- total nr of points: {{res["points_total"]}}
- avg nr of people who contributed per month: {{res["nrpeople_month"]}} 



"""


def md():
    return html.Div(
        children=[html.Br(), dcc.Markdown(id="conclusion_md"), html.Br(), html.Br()], style={"textAlign": "left"}
    )


# app.layout = html.Div(children=[top(),sliders(),experience(),graphs(),md()],style={'width':'1000','textAlign': 'center','align': 'center'})


deps = [
    dash.dependencies.Input("nrmonths", "value"),
    dash.dependencies.Input("slider_marketcap_months", "value"),
    dash.dependencies.Input("token_price", "value"),
    dash.dependencies.Input("exitvalue_tftech", "value"),
    dash.dependencies.Input("nr_months_past", "value"),
    dash.dependencies.Input("contr_level_past", "value"),
    dash.dependencies.Input("contr_level_future", "value"),
    dash.dependencies.Input("workingtime", "value"),
    dash.dependencies.Input("location", "value"),
    dash.dependencies.Input("liquidity_yes_no", "value"),
    dash.dependencies.Input("dilution", "value"),
    dash.dependencies.Input("billion_y_n", "value"),
]

#
# def nrpeople_months(nrmonths):
#     def m(month):
#         return 40 + (120-40)/48*month
#     tot = 0
#     for i in range(0,nrmonths):
#         tot += m(i)
#     return tot
#
#
# def calc(nrmonths,slider_marketcap_months,token_price,exitvalue_tftech,
#                   nr_months_past,contr_level_past,contr_level_future,
#                   workingtime,location,liquidity_yes_no,dilution, billion_y_n):
#
#     res={}
#
#     tokens_liq = 20*token_price*liquidity_yes_no
#     tokens_exit = 200*token_price*billion_y_n
#     ev = exitvalue_tftech*(1-(dilution/100))/10
#     total = tokens_liq+tokens_exit+ev
#
#     res["chart_total_y"] = [ev,tokens_liq,tokens_exit,total]
#
#     big_mac_index = location
#
#
#
#     points_future = nrmonths*contr_level_future*big_mac_index * (workingtime/100)
#
#
#     points_past = nr_months_past * contr_level_past * big_mac_index
#
#     nrpeople_months_ = nrpeople_months(nrmonths)
#
#     avgbigmac = 3.5
#
#     points_total = 15 * 48 * 2.5 * avgbigmac + nrpeople_months_  * 2.5* avgbigmac
#
#     res["points_future"]=int(points_future)
#     res["points_past"]=int(points_past)
#     res["points_total"]=int(points_total)
#     res["perc_total"]=(points_future+points_past)/points_total
#     p = res["perc_total"]*1000000
#
#     res["chart_you_y"] = [ev*p,tokens_liq*p,tokens_exit*p,total*p]
#     res["nrpeople_month"] = int(nrpeople_months_/nrmonths)
#
#     print(res)
#
#     return res
#
#
# @app.callback(dash.dependencies.Output('graph-tftech', 'figure'),deps)
# def exit_output(*args):
#     x = ["Exit TFTech", "Tokens Liquid Valuation", "Tokens Exit Value","Total"]
#     res = calc(*args)
#
#     return {
#             'data': [
#                 {'x':x, 'y': res["chart_total_y"], 'type': 'bar', 'name': 'TFTechVal'},
#             ],
#             'layout': {
#                 'title': 'Exit Simulation (Total Value in USD)'
#             }
#     }
#
# @app.callback(dash.dependencies.Output('graph-personal', 'figure'),deps)
# def personal_bonus_output(*args):
#     x = ["Exit TFTech", "Tokens Liquid Valuation", "Tokens Exit Value","Total"]
#     res = calc(*args)
#
#     return {
#             'data': [
#                 {'x':x, 'y': res["chart_you_y"], 'type': 'bar', 'name': 'TFTechVal'},
#             ],
#             'layout': {
#                 'title': 'Exit Simulation (Total Value in USD)'
#             }
#     }
#
# @app.callback(dash.dependencies.Output('conclusion_md', 'children'),deps)
# def conclusion(*args):
#     res = calc(*args)
#     md = j.tools.jinja2.template_render(text=markdown_text2,res=res)
#     return md


def main():
    # app.layout = html.Div(
    #     [dui.Layout(grid=grid_top),
    #         dui.Layout(grid=grid,controlpanel=controlpanel)
    #     ],style={'height': '100vh','width': '100vw'})

    app.layout = html.Div(
        dui.Layout(grid=grid_top, controlpanel=controlpanel), style={"height": "100vh", "width": "100vw"}
    )

    app.run_server(debug=True)


main()
