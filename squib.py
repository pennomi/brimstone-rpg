"""A squib-inspired python library that does card generation "the Python way"
"""
import cairo
from gi.repository import Rsvg
from gi.repository import Pango
from gi.repository import PangoCairo
from gi.repository.GLib import GError
import tqdm as tqdm
from google_sheets import get_worksheet_data
from util import Color, BLACK
from parser import parse
from jinja2 import Template


class RenderInstance:
    def __init__(self, index, width, height):
        self.index = index
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx = cairo.Context(self.surface)
        self.pctx = PangoCairo.create_context(self.ctx)
        # TODO: Antialias the font

    def draw_rect(self,
                  id: str="",
                  x: float=0,
                  y: float=0,
                  w: float=100,
                  h: float=100,
                  color: Color=BLACK,
                  stroke: bool=False,
                  radius: float=0,  # TODO radius
                  dash: float=None):  # TODO: Dash
        self.ctx.set_source_rgba(*color)
        self.ctx.rectangle(x, y, w, h)
        if stroke:
            self.ctx.stroke()
        else:
            self.ctx.fill()
        # TODO: Allow stroke instead of fill... or both?

    def draw_svg(self,
                 id: str=None,
                 x: float=0,
                 y: float=0,
                 w: float=100,
                 h: float=100,
                 file: str=None):
        if not file:
            return

        # TODO: Fail with a warning nicer
        try:
            handle = Rsvg.Handle.new_from_file(file)
        except GError as e:
            print("Could not load svg file:", file)
            return
        d = handle.get_dimensions()
        svg_width, svg_height = d.width, d.height

        # Position/Scale the svg to fit the specified position
        self.ctx.translate(x, y)
        self.ctx.scale(w / svg_width, h / svg_height)

        # Draw the SVG
        Rsvg.Handle.render_cairo(handle, self.ctx)

        # Undo the transform
        self.ctx.scale(svg_width / w, svg_height / h)
        self.ctx.translate(-x, -y)

    def draw_text(self,
                  id: str=None,
                  x: float=0,
                  y: float=0,
                  w: float=100,
                  h: float=100,
                  text: str="undefined",
                  color: Color=BLACK,
                  font_name: str="Ubuntu",
                  font_size: int=16,
                  # TODO: Align
                  ):
        # make the font
        font = Pango.FontDescription("{} {}".format(font_name, font_size))

        # Convert to Pango units
        width = int(w * Pango.SCALE)
        height = int(h * Pango.SCALE)

        # Generate the text
        pango_layout = PangoCairo.create_layout(self.ctx)
        pango_layout.set_markup(text, -1)
        # TODO: pango_layout.set_alignment(Pango.Alignment.CENTER)
        pango_layout.set_font_description(font)
        pango_layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        pango_layout.set_width(width)

        # Ellipsize if there's too much content
        text_width, text_height = pango_layout.get_pixel_size()
        if text_height > h:
            pango_layout.set_ellipsize(Pango.EllipsizeMode.END)
            pango_layout.set_height(height)
            # text_width, text_height = pango_layout.get_pixel_size()

        # draw a debug box
        self.draw_rect(x=x, y=y, w=w, h=h, color=Color(0.0, 1.0, 1.0, 1.0), stroke=True)

        # draw the text
        self.ctx.set_source_rgba(*color)
        self.ctx.move_to(x, y)
        PangoCairo.show_layout(self.ctx, pango_layout)

    def draw_table(self, data):
        # TODO: We need tables!
        pass

    def save(self):
        self.surface.write_to_png("_output/card{}.png".format(self.index))


def main():
    print("Test commencing.")
    # Load the data from Google Sheets
    wks = get_worksheet_data("Brimstone RPG Powers")
    keys = wks[0]
    card_data = [dict(zip(keys, line)) for line in wks[1:]]

    # Do some context processing
    for card in card_data:
        # Use images directory
        for k in ['background', 'icon']:
            card[k] = 'images/' + card[k]

        # Tags
        card['tags'] = [s.strip().upper() for s in card['tags'].split(',')]

        # Parse Markup
        card['description'] = card['description'].replace(
            '[', '<span font="UbuntuCondensed Normal 16" rise="3000" '
                 'background="#212121" foreground="#FFFFFF"'
                 'gravity="south"> '
        ).replace(
            ']', ' </span>'
        )

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
                "Svg": blorp.draw_svg,
                "Rect": blorp.draw_rect,
                "Text": blorp.draw_text,
            }[cmd]
            func(**attrs)

        # Save the card to file
        blorp.save()

        # TODO: Hand and showcase renders

if __name__ == "__main__":
    main()
