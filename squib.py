"""A squib-inspired python library that does card generation "the Python way"
"""
import json
import warnings
from functools import lru_cache

import cairo
from gi.repository import Pango, PangoCairo, Gdk, GdkPixbuf
# noinspection PyUnresolvedReferences
from gi.repository.GLib import GError
import tqdm as tqdm
from google_sheets import get_worksheet_data
from util import Color, BLACK
from parser import parse
from jinja2 import Template


# TODO: Use asyncio to render everything in parallel


def scale_column_widths(columns, total_width):
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
    def __init__(self, index, width, height):
        self.index = index
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

        # Two different methods for rounded and normal rectangles
        if radius:
            r = radius
            self.ctx.move_to(x + r, y)
            self.ctx.line_to(x + w - r, y)
            self.ctx.curve_to(x + w, y, x + w, y, x + w, y + r)
            self.ctx.line_to(x + w, y + h - r)
            self.ctx.curve_to(x + w, y + h, x + w, y + h, x + w - r, y + h)
            self.ctx.line_to(x + r, y + h)
            self.ctx.curve_to(x, y + h, x, y + h, x, y + h - r)
            self.ctx.line_to(x, y + r)
            self.ctx.curve_to(x, y, x, y, x + r, y)
        else:
            self.ctx.rectangle(x, y, w, h)

        # TODO: Allow stroke instead of fill... or both?
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
                widths[i] = max(this_w, widths[i])

        # Make the widths smaller until it fits
        widths = scale_column_widths(widths, w)

        # Second pass to do rendering
        y_cursor = 0
        for i, row in enumerate(data):
            x_cursor = 0

            # calculate the height of this row
            height = 0
            for j, value in enumerate(row):
                _, h = self._get_text_size(value, font, w=widths[j])
                height = max(height, h)

            for j, value in enumerate(row):
                # render the table cell
                self.draw_rect(x=x + x_cursor, y=y + y_cursor, w=widths[j],
                               h=height, stroke=True, color=border_color)
                # then render the text inside it
                self.draw_text(text=value, x=x + x_cursor, y=y + y_cursor,
                               w=widths[j], h=height, color=color,
                               font_name=font_name, font_size=font_size)
                x_cursor += widths[j]

            y_cursor += height

    def save(self):
        self.surface.write_to_png("_output/card{}.png".format(self.index))


def replace_markup(card, key):
    """Replaces [] with a background color tag and {} with fontawesome icons.
    """
    # [] Tags
    card[key] = card[key].replace(
        '[', '<span font="UbuntuCondensed Normal 16" rise="3000" '
             'background="#212121" foreground="#FFFFFF"'
             'gravity="south"> '
    ).replace(']', ' </span>')

    # {} Tags
    card[key] = card[key].replace(
        '{', '<span font="FontAwesome Normal"> ').replace('}', ' </span>')


def main():
    # Load the data from Google Sheets
    wks = get_worksheet_data("Brimstone RPG Powers")
    keys = wks[0]
    card_data = [dict(zip(keys, line)) for line in wks[1:]]
    card_data = [c for c in card_data if any(c.values())]  # Remove empty lines

    print("Rendering card data...")
    # Do some context processing
    for i, card in enumerate(card_data):
        card['id'] = str(i).rjust(3, "0")

        # Use images directory
        card['background'] = 'images/frames/' + card['background']
        if card['image']:
            card['image'] = 'images/art/' + card['image']

        # Put the paintbrush on the artist
        card['artist'] = "{}" + card['artist']

        # Keywords
        card['keywords'] = [s.strip() for s in card['keywords'].split(',') if s]

        # Stats
        stats = [_.split('|') for _ in card['stats'].split('\n') if _]
        card['stats'] = [
            {'icon': 'images/icons/{}.svg'.format(icon), 'text': text}
            for icon, text in reversed(stats)
        ]

        # Ensure description uses \n notation
        card['description'] = card['description'].replace('\n', '\\n')

        # Parse Markup
        replace_markup(card, 'description')
        replace_markup(card, 'table_data')
        replace_markup(card, 'artist')

        # make the table data available as json
        table_data = [
            row.split('|') for row in card['table_data'].split("\n") if row
            ]
        card['table_data'] = json.dumps(table_data) if table_data else ""

        # parse some keys as ints
        card['table_y'] = int(card['table_y']) if card['table_y'] else 0

    # Load the template
    with open('portrait.tml', 'r') as infile:
        template = Template(infile.read())

    # Iterate over each card and render it
    for i, card in enumerate(tqdm.tqdm(card_data)):
        # Render the template using this card's data
        layout = template.render(card=card)

        # TODO: Everything below here probably becomes a core function call
        # Parse the template
        instructions = parse(layout)

        # Based on the template, run the operations specified
        blorp = RenderInstance(i, 825, 1125)
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

        # TODO: Hand and showcase renders


if __name__ == "__main__":
    main()
