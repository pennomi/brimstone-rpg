from ctypes import cdll, c_char_p

# Load Libs
cairo = cdll.LoadLibrary('libcairo.so.2')
pangocairo = cdll.LoadLibrary('libpangocairo-1.0.so.0')
CAIRO_FORMAT_ARGB32 = 0

# Draw Some Stuff
surface = cairo.cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 100, 100)
ctx = cairo.cairo_create(surface)
layout = pangocairo.pango_cairo_create_layout(ctx)
pangocairo.pango_layout_set_markup(layout, c_char_p(b"Cool"), -1)
pangocairo.pango_cairo_update_layout(ctx, layout)
pangocairo.pango_cairo_show_layout(ctx, layout)

# Render PNG
cairo.cairo_surface_write_to_png(surface, c_char_p(b"out.png"))

# Clean Up
pangocairo.g_object_unref(layout)
cairo.cairo_surface_destroy(surface)
