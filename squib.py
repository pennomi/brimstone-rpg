"""A squib-inspired python library that does card generation "the Python way"
"""
import json
import warnings
from functools import lru_cache

import cairo
import math
from gi.repository import Pango, PangoCairo, Gdk, GdkPixbuf
# noinspection PyUnresolvedReferences
from gi.repository.GLib import GError

from parser import parse
from util import Color, BLACK


def _scale_column_widths(columns, total_width):
    # Until we're small enough...
    while sum(columns) > total_width:
        # find the biggest column(s)
        biggest = max(columns)
        # and shave off a tiny piece of them
        columns = [c - 1 if c >= biggest else c for c in columns]
    return columns


@lru_cache(maxsize=100)
def _load_image(file: str=None) -> (object, int, int):
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file(file)
    except GError:
        warnings.warn("Could not load file: {}".format(file))
        raise FileNotFoundError(file)
    return pb, pb.get_width(), pb.get_height()


class RenderInstance:
    def __init__(self, filename, width, height):
        self.filename = filename
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx = cairo.Context(self.surface)
        self.pctx = PangoCairo.create_context(self.ctx)

    def draw_rect(self,
                  id: str="",
                  x: float=0,
                  y: float=0,
                  w: float=100,
                  h: float=100,
                  color: Color=BLACK,
                  stroke: bool=False,
                  radius: float=0):
        self.ctx.set_source_rgba(*color)

        # Draw the geometry
        r = radius
        pi2 = math.pi/2
        self.ctx.move_to(x, y + r)
        self.ctx.arc(x + r, y + r, r, 2*pi2, 3*pi2)
        self.ctx.arc(x + w - r, y + r, r, 3*pi2, 0*pi2)
        self.ctx.arc(x + w - r, y + h - r, r, 0*pi2, 1*pi2)
        self.ctx.arc(x + r, y + h - r, r, 1*pi2, 2*pi2)
        self.ctx.close_path()

        # TODO: Allow stroke instead of fill... or both?
        # Stroke or fill it
        if stroke:
            self.ctx.stroke()
        else:
            self.ctx.fill()

    def draw_image(self,
                   id: str="",
                   x: float=0,
                   y: float=0,
                   w: float=100,
                   h: float=100,
                   file: str=""):
        try:
            buffer, width, height = _load_image(file)
        except FileNotFoundError:
            return

        # Position/Scale the svg to fit the specified position
        self.ctx.translate(x, y)
        self.ctx.scale(w / width, h / height)

        # Draw the image
        Gdk.cairo_set_source_pixbuf(self.ctx, buffer, 0, 0)
        self.ctx.paint()

        # Undo the transform
        self.ctx.scale(width / w, height / h)
        self.ctx.translate(-x, -y)

    def _get_text_size(self, text, font, w=None):
        text = text.replace("\\n", "\n")

        # Generate the text
        pango_layout = PangoCairo.create_layout(self.ctx)
        pango_layout.set_markup(text, -1)
        pango_layout.set_font_description(font)
        if w is not None:
            pango_layout.set_wrap(Pango.WrapMode.WORD_CHAR)
            pango_layout.set_width(int(w * Pango.SCALE))
        return pango_layout.get_pixel_size()

    def draw_text(self,
                  id: str=None,
                  x: float=0,
                  y: float=0,
                  w: float=100,  # TODO: These seem... arbitrary.
                  h: float=100,  # TODO: These seem... arbitrary.
                  text: str="undefined",
                  color: Color=BLACK,
                  font_name: str="Ubuntu",
                  font_size: int=16,
                  align: str="left",
                  line_spacing: int=0,
                  debug: bool=False,
                  ):
        text = text.replace("\\n", "\n")
        # make the font
        font = Pango.FontDescription("{} {}".format(font_name, font_size))

        # Convert to Pango units
        width = int(w * Pango.SCALE)
        height = int(h * Pango.SCALE)

        # Generate the text
        pango_layout = PangoCairo.create_layout(self.ctx)
        pango_layout.set_markup(text, -1)
        pango_layout.set_spacing(line_spacing * Pango.SCALE)
        pango_layout.set_alignment({
            "left": Pango.Alignment.LEFT,
            "center": Pango.Alignment.CENTER,
            "right": Pango.Alignment.RIGHT,
        }[align])  # TODO: Warnings for improper grammar
        pango_layout.set_font_description(font)
        # pango_layout.set_justify(True)
        pango_layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        pango_layout.set_width(width)

        # Ellipsize if there's too much content
        text_width, text_height = pango_layout.get_pixel_size()
        if text_height > h:
            pango_layout.set_ellipsize(Pango.EllipsizeMode.END)
            pango_layout.set_height(height)
            # text_width, text_height = pango_layout.get_pixel_size()

        # draw a debug box
        if debug:
            self.draw_rect(x=x, y=y, w=w, h=h, color=Color(0.0, 1.0, 1.0, 1.0),
                           stroke=True)

        # draw the text
        self.ctx.set_source_rgba(*color)
        self.ctx.move_to(x, y)
        PangoCairo.show_layout(self.ctx, pango_layout)

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
        if not data:
            return

        data = json.loads(data)

        # TODO: Assert the table data is rectangular

        # First pass to generate the values
        font = Pango.FontDescription("{} {}".format(font_name, font_size))
        widths = [0] * len(data[0])
        for row in data:
            for i, value in enumerate(row):
                this_w, _ = self._get_text_size(value, font)
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
            for j, value in enumerate(row):
                _, h = self._get_text_size(value, font, w=widths[j])
                height = max(height, h)
            height += padding_y * 2

            for j, value in enumerate(row):
                # render the table cell
                self.draw_rect(x=x + cursor_x, y=y + cursor_y, w=widths[j],
                               h=height, stroke=True, color=border_color)
                # then render the text inside it
                self.draw_text(text=value,
                               x=x + cursor_x + padding_x,
                               y=y + cursor_y + padding_y,
                               w=widths[j], h=height, color=color,
                               font_name=font_name, font_size=font_size)
                cursor_x += widths[j]

            cursor_y += height

    def save(self):
        self.surface.write_to_png(self.filename)


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
