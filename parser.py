from pyparsing import Literal, Word, srange, Group, OneOrMore, Dict, \
    nestedExpr, restOfLine, stringEnd, ParseException

# TODO: Inline Comments SkipTo and remove \n from whitespace?
# TODO: Syntax errors are just failing silently for some reason
from util import Color


def _build():
    """Encapsulate so the variables don't leak out."""
    # Basic punctuation
    colon = Literal(':').suppress()
    hashmark = Literal('#').suppress()
    comment = (hashmark + restOfLine).suppress()

    # Enforce Python-style naming conventions
    command_name = Word(srange("[A-Z]"), srange("[a-zA-Z0-9]"))  # StudlyCaps
    field_name = Word(srange("[a-z_]"), srange("[a-z0-9_]"))  # lower_underscore

    # Put it all together
    fields = Dict(OneOrMore(Group(field_name + colon + restOfLine)))
    fields = nestedExpr(opener="{", closer="}", content=fields)
    command = Group(command_name + fields)

    # Configure the parser
    tml_parser = OneOrMore(command) + stringEnd
    tml_parser.ignore(comment)
    return tml_parser
TML_PARSER = _build()


def _parse_expression(key: str, exp: str):
    """Take in an expression and safely transform it into a python expression.
    """
    # Do some cleaning
    exp = exp.strip()

    # TODO: Use regex to validate first?
    # TODO: Maybe PyParsing could validate it
    # TODO: Support expressions
    if key in ["x", "y", "w", "h", "radius", "padding_x", "padding_y",
               "line_spacing"]:
        return float(exp)
    if key == "color":
        return Color(*tuple(float(e) for e in exp.split(',')))
    return exp


def parse(string: str) -> list:
    try:
        commands = []
        for c, attrs in TML_PARSER.parseString(string):
            attrs = attrs.asDict()
            attrs = {k: _parse_expression(k, v) for k, v in attrs.items()}
            commands.append((c, attrs))
        return commands
    except ParseException:
        print(string)
        return []
