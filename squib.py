"""A squib-inspired python library that does card generation "the Python way"
"""
import json
import warnings

from parser import parse
from renderer import CairoRenderer, TextAlignment
from util import Color, BLACK


def _scale_column_widths(columns, total_width):
    # Until we're small enough...
    while sum(columns) > total_width:
        # find the biggest column(s)
        biggest = max(columns)
        # and shave off a tiny piece of them
        columns = [c - 1 if c >= biggest else c for c in columns]
    return columns


class RenderInstance:
    def __init__(self, filename, width, height):
        self.filename = filename
        self.renderer = CairoRenderer(width, height)

    def draw_rect(self,
                  id: str="",
                  x: float=0,
                  y: float=0,
                  w: float=100,
                  h: float=100,
                  color: Color=BLACK,
                  stroke: bool=False,
                  fill: bool=True,
                  radius: float=0) -> None:
        self.renderer.set_color(*color)
        self.renderer.plot_rectangle(x, y, w, h, radius)
        if stroke:
            self.renderer.stroke()
        if fill:
            self.renderer.fill()

    def draw_image(self,
                   id: str="",
                   x: float=0,
                   y: float=0,
                   w: float=100,
                   h: float=100,
                   file: str="") -> None:
        # TODO: Check the transforms
        try:
            width, height = self.renderer.set_image_buffer(file)
        except FileNotFoundError:
            warnings.warn("Could not load file: {}".format(file))
            return
        with self.renderer.translate(x, y):
            with self.renderer.scale(w/width, h/height):
                self.renderer.paint_image()

    def draw_text(self,
                  id: str=None,
                  x: float=0,
                  y: float=0,
                  w: float=-1.0,  # By default, DON'T restrict w/h
                  h: float=-1.0,
                  text: str="",
                  color: Color=BLACK,
                  font_name: str="Ubuntu",
                  font_size: int=16,
                  align: str="left",
                  line_spacing: int=0,
                  justify: bool=False,
                  debug: bool=False,
                  ):
        """Draw the configured text widget on the canvas.
        """
        # First, draw a debug box (if requested)
        if debug:
            self.draw_rect(x=x, y=y, w=w, h=h, color=Color(0.0, 1.0, 1.0, 1.0),
                           stroke=True, fill=False)

        # Process the inputs
        text = text.replace("\\n", "\n")
        alignment = {
            "left": TextAlignment.Left,
            "center": TextAlignment.Center,
            "right": TextAlignment.Right,
        }[align]  # TODO: Validate on the parser

        # Configure the text
        self.renderer.set_font(font_name, font_size)
        self.renderer.configure_text_layout(
            width=w, height=h,
            line_spacing=line_spacing,
            alignment=alignment,
            justify=justify,
        )
        self.renderer.set_color(*color)
        self.renderer.set_text(text)

        # Draw the text
        with self.renderer.translate(x, y):
            self.renderer.paint_text()

    def draw_table(self,
                   id: str=None,
                   data: []=None,
                   x: float=0,
                   y: float=0,
                   w: float=100,
                   # h: float=100,  # TODO: Is this even a thing?
                   padding_x: int=2,
                   padding_y: int=2,
                   color: Color=BLACK,
                   border_color: Color=BLACK,
                   font_name: str="Ubuntu",
                   font_size: int=16,
                   ):
        # Load the data
        if not data:
            return
        data = json.loads(data)
        # TODO: Assert the table data is rectangular

        # Set the font
        self.renderer.set_font(font_name, font_size)

        # First pass to generate the column widths
        widths = [0] * len(data[0])
        for row in data:
            for i, text in enumerate(row):
                text = text.replace("\\n", "\n")
                self.renderer.set_text(text)
                self.renderer.configure_text_layout(width=w, height=1000)
                this_w, _ = self.renderer.get_text_size()
                this_w += padding_x * 2
                widths[i] = max(this_w, widths[i])

        # Make the widths smaller until it fits
        widths = _scale_column_widths(widths, w)

        # Second pass to do rendering
        cursor_y = 0
        for i, row in enumerate(data):
            cursor_x = 0

            # calculate the height of this row
            height = 0
            for j, text in enumerate(row):
                self.renderer.set_text(text)
                self.renderer.configure_text_layout(width=widths[j], height=1000)
                _, h = self.renderer.get_text_size()
                height = max(height, h)
            height += padding_y * 2

            for j, text in enumerate(row):
                # render the table cell
                self.draw_rect(x=x + cursor_x, y=y + cursor_y, w=widths[j],
                               h=height, stroke=True, fill=False,
                               color=border_color)
                # then render the text inside it
                self.draw_text(text=text,
                               x=x + cursor_x + padding_x,
                               y=y + cursor_y + padding_y,
                               w=widths[j], h=height, color=color,
                               font_name=font_name, font_size=font_size)
                cursor_x += widths[j]
            cursor_y += height

    def save(self):
        self.renderer.save(self.filename)


def render_string(layout, w, h, filename):
    # Parse the template
    instructions = parse(layout)

    # Based on the template, run the operations specified
    blorp = RenderInstance(filename, w, h)
    for cmd, attrs in instructions:
        func = {
            "Image": blorp.draw_image,
            "Rect": blorp.draw_rect,
            "Text": blorp.draw_text,
            "Table": blorp.draw_table,
        }[cmd]
        func(**attrs)

    # Save the card to file
    blorp.save()
