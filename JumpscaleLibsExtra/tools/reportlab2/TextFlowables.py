from Jumpscale import j
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet


class BaseTextFlowable:
    base_style_name = "Normal"

    def __init__(self, text, custom_styles=None):
        self.text = text
        self.custom_styles = custom_styles or {}
        self.base_style = getSampleStyleSheet().get(self.base_style_name)

    def _apply_custom_styles(self):
        self.style = self.base_style
        for key, value in self.custom_styles.items():
            if hasattr(self.style, key):
                setattr(self.style, key, value)

    def get(self):

        self._apply_custom_styles()
        return Paragraph(self.text, self.base_style)


class Normal(BaseTextFlowable):
    base_style_name = "Normal"


class H1(BaseTextFlowable):
    base_style_name = "Heading1"


class H2(BaseTextFlowable):
    base_style_name = "Heading2"


class H3(BaseTextFlowable):
    base_style_name = "Heading3"


# TODO: implement the rest of the styles
