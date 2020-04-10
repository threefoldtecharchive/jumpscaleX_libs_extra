from Jumpscale import j

import plotly.graph_objects as go


class SimulatorBase(j.baseclasses.object_config):
    """
    a set of nodes seen in 1 specific month
    """

    def _init_pre(self, **kwargs):
        self._model_ = False
        self._bcdb_ = None

    def _numeric_get(self, val):
        if isinstance(val, float) or isinstance(val, int):
            val = j.data.types.numeric.clean(val)
        return val

    def __str__(self):
        if hasattr(self, "month"):
            out = "{YELLOW}## %s: %s{RESET}\n\n" % (self._cat, self.month)
        else:
            out = "{YELLOW}## %s{RESET}\n\n" % (self._cat)

        for key, val in self._data._ddict_hr.items():
            val = self._numeric_get(val)
            out += " - {RED}%-30s{RESET} : %s\n" % (key, val)

        # walk over properties
        for key in [i for i in self._properties if not i.startswith("_") and i not in ["id", "name"]]:
            if key == "markdown":
                continue
            try:

                val = getattr(self, key)
                val = self._numeric_get(val)
                out += " - {RED}%-30s{RESET} : %s\n" % (key, val)
            except:
                pass

        out = j.core.tools.text_replace(out)
        return out

    __repr_ = __str__

    @property
    def markdown(self):
        out = """
        ```python
        %s
        ```
        """ % str(
            self
        )
        return out

    def graph(self, rownames, title=None):

        if isinstance(rownames, str):
            rownames = [rownames]

        fig = go.FigureWidget()
        for name in rownames:
            row = self.rows[name]
            xx, yy = row.values_xy
            fig.add_trace(go.Scatter(x=xx, y=yy, name=name, connectgaps=False))

        if len(rownames) > 0 or title:
            fig.update_layout(title=title, showlegend=True)

        return fig
