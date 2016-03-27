"""Some useful structs and other objects.
"""


# TODO: Deprecate in favor of the renderer.py functionality
class Color:
    def __init__(self, r: float, g: float, b: float, a: float=1.0):
        self._attrs = (r, g, b, a)

    def __iter__(self):
        return iter(self._attrs)
BLACK = Color(0, 0, 0, 1)
