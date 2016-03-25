# coding: utf8
import cairocffi as cairo

from ctypes import cdll, c_char_p


# surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
# ctx = cairo.Context(surface)

cairo = cdll.LoadLibrary('libcairo.so.2')
pangocairo = cdll.LoadLibrary('libpangocairo-1.0.so.0')
CAIRO_FORMAT_ARGB32 = 0
surface = cairo.cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 100, 100)
ctx = cairo.cairo_create(surface)
layout = pangocairo.pango_cairo_create_layout(ctx)

cairo.cairo_surface_write_to_png(surface, c_char_p(b"out.png"))

# Clean Up
cairo.cairo_surface_destroy(surface)
