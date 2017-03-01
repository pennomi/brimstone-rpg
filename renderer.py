import contextlib
import math
from ctypes import cdll, c_char_p, c_double, c_int, pointer
from enum import IntEnum
from functools import lru_cache


PC = cdll.LoadLibrary('libpangocairo-1.0.so.0')
PB = cdll.LoadLibrary('libgdk_pixbuf-2.0.so.0')
GDK = cdll.LoadLibrary('libgdk-3.so.0')
CAIRO_FORMAT_ARGB32 = 0
PANGO_SCALE = 1024


@lru_cache(maxsize=25)
def _load_font(description: str):
    return PC.pango_font_description_from_string(c_char_p(description.encode()))


@lru_cache(maxsize=100)
def _load_image(file: str=None) -> (object, int, int):
    buffer = PB.gdk_pixbuf_new_from_file(file.encode(), None)
    if not buffer:
        raise FileNotFoundError(file)
    width = PB.gdk_pixbuf_get_width(buffer)
    height = PB.gdk_pixbuf_get_height(buffer)
    return buffer, width, height


class TextAlignment(IntEnum):
    Left = 0
    Center = 1
    Right = 2


class WrapMode(IntEnum):
    Word = 0
    Char = 1
    WordChar = 2


class EllipsizeMode(IntEnum):
    None_ = 0
    Start = 1
    Middle = 2
    End = 3


class CairoRenderer:
    def __init__(self, width: int, height: int):
        """Initialize a text-enabled cairo surface we can draw on."""
        self.surface = PC.cairo_image_surface_create(
            CAIRO_FORMAT_ARGB32, width, height)
        self.context = PC.cairo_create(self.surface)
        self.layout = PC.pango_cairo_create_layout(self.context)
        self.buffer = None

    def set_font(self, font_name: str, font_size: int):
        description = "{} {}".format(font_name, font_size)
        font = _load_font(description)
        PC.pango_layout_set_font_description(self.layout, font)

    def set_text(self, text: str):
        PC.pango_layout_set_markup(self.layout, c_char_p(text.encode()), -1)

    def get_text_size(self) -> (int, int):
        w = pointer(c_int(0))
        h = pointer(c_int(0))
        PC.pango_layout_get_size(self.layout, w, h)
        return w[0]/PANGO_SCALE, h[0]/PANGO_SCALE

    def configure_text_layout(
            self,
            width: float=-1.0, height: float=-1.0,
            line_spacing: float=0.0,
            alignment: TextAlignment=TextAlignment.Left,
            wrap_mode: WrapMode=WrapMode.WordChar,
            ellipsize_mode: EllipsizeMode=EllipsizeMode.End,
            justify: bool=False) -> None:

        # Dimensions
        if width != -1:
            width *= PANGO_SCALE
        if height != -1:
            height *= PANGO_SCALE
        PC.pango_layout_set_width(self.layout, c_int(int(width)))
        PC.pango_layout_set_height(self.layout, c_int(int(height)))

        # Spacing
        line_spacing = int(line_spacing * PANGO_SCALE)
        PC.pango_layout_set_spacing(
            self.layout, c_int(line_spacing))

        # Alignment
        PC.pango_layout_set_alignment(self.layout, alignment)

        # Wrap Mode
        PC.pango_layout_set_wrap(self.layout, wrap_mode)

        # Ellipsize
        PC.pango_layout_set_ellipsize(self.layout, ellipsize_mode)

        # Justify
        PC.pango_layout_set_justify(self.layout, justify)

    @contextlib.contextmanager
    def translate(self, x: float, y: float):
        PC.cairo_translate(self.context, c_double(x), c_double(y))
        try:
            yield
        finally:
            PC.cairo_translate(self.context, c_double(-x), c_double(-y))

    @contextlib.contextmanager
    def scale(self, x: float, y: float):
        PC.cairo_scale(self.context, c_double(x), c_double(y))
        try:
            yield
        finally:
            PC.cairo_scale(self.context, c_double(1/x), c_double(1/y))

    # TODO: Parse several types of colors: 0-255, 0.0-1.0, #FFFFFF, 'black'
    # http://stackoverflow.com/questions/4296249/how-do-i-convert-a-hex-triplet-to-an-rgb-tuple-and-back
    def set_color(self, r: float, g: float, b: float, a: float):
        PC.cairo_set_source_rgba(
            self.context, c_double(r), c_double(g), c_double(b), c_double(a))

    def plot_rectangle(self, x: float, y: float, width: float, height: float,
                       radius: float):
        # Draw the geometry
        w = width
        h = height
        r = radius
        PC.cairo_move_to(self.context, c_double(x), c_double(y + r))

        def arc(a, b, c):
            c1 = (c + 1) % 4
            PC.cairo_arc(
                self.context,
                c_double(a), c_double(b), c_double(r),
                c_double(c*math.pi/2), c_double(c1*math.pi/2))

        arc(x + r, y + r, 2)
        arc(x + w - r, y + r, 3)
        arc(x + w - r, y + h - r, 0)
        arc(x + r, y + h - r, 1)

        PC.cairo_close_path(self.context)

    def stroke(self):
        PC.cairo_stroke(self.context)

    def fill(self):
        PC.cairo_fill(self.context)

    def set_image_buffer(self, filepath):
        self.buffer, width, height = _load_image(filepath)
        return width, height

    def paint_image(self):
        GDK.gdk_cairo_set_source_pixbuf(
            self.context, self.buffer, c_double(0), c_double(0))
        PC.cairo_paint(self.context)

    def paint_text(self):
        """Draw the text on the surface."""
        PC.pango_cairo_update_layout(self.context, self.layout)
        PC.pango_cairo_show_layout(self.context, self.layout)

    def save(self, filename):
        """Render this surface to PNG format."""
        PC.cairo_surface_write_to_png(self.surface, c_char_p(filename.encode()))

    def __del__(self):
        """Destroy all the objects we've created."""
        PC.g_object_unref(self.layout)
        PC.cairo_surface_destroy(self.surface)
        PC.cairo_destroy(self.context)
