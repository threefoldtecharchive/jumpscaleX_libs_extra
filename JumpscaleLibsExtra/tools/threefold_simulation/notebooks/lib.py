from IPython.display import Markdown as md
import numpy as np
# import bqplot.pyplot as plt
# from bqplot import *
# from ipywidgets import interact, HBox, Label, Layout
# import ipywidgets as widgets

import plotly.graph_objects as go

from Jumpscale import j


def clean_code(code):
    out = ""
    for line in code.split("\n"):
        if line.find("from Jumpscale import j") != -1:
            continue
        if line.find("j.tools.tfgrid_simulator.") != -1:
            continue
        if line.find("environment = simulation") != -1:
            continue
        if line.find("bom = simulation.bom") != -1:
            continue
        if line.strip().startswith("assert"):
            continue

        out += "%s\n" % line
    return out


def md_code(var):
    if j.sal.fs.exists(var):
        var = j.sal.fs.readFile(var)
        var = clean_code(var)
    return md("```python\n%s\n```" % var)
