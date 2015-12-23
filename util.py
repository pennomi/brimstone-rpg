"""Some useful structs and other objects.
"""


class Color:
    # TODO: Maybe instead it takes in a string and forgivingly parses it
    #  * 0.5, 0.5, 0.5, 1.0  (floats)
    #  * 424242FF            (hex)
    #  * 255, 255, 255, 255  (ints)
    def __init__(self, r: float, g: float, b: float, a: float=1.0):
        self._attrs = (r, g, b, a)

    def __iter__(self):
        return iter(self._attrs)
BLACK = Color(0, 0, 0, 1)


# TODO: Also add a layout parser (x, y, w, h) and a font parser
