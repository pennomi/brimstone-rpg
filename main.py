import json

import tqdm
from jinja2 import Template

from google_sheets import get_worksheet_data
from squib import render_string


def replace_markup(card, key):
    """Replaces [] with a background color tag and {} with fontawesome icons.
    """
    # [] Tags
    card[key] = card[key].replace(
        '[', '<span font="DroidSans Bold 20" rise="1000" '
             'background="#212121" foreground="#FFFFFF"'
             'gravity="south"> '
    ).replace(']', ' </span>')

    # {} Tags
    card[key] = card[key].replace(
        '{', '<span font="FontAwesome Normal">').replace('}', '</span>')


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

        # Stats
        stats = [_.split('|') for _ in card['stats'].split('\n') if _]
        card['stats'] = [
            {'icon': 'images/icons/{}.svg'.format(icon), 'text': text}
            for icon, text in stats
            ]

        # Ensure description uses \n notation
        card['description'] = card['description'].replace('\n', '\\n')

        # Parse Markup
        replace_markup(card, 'description')
        replace_markup(card, 'table_data')
        replace_markup(card, 'artist')

        # make the table data available as json
        table_data = [
            [_.strip() for _ in row.split('|')]
            for row in card['table_data'].split("\n")
            if row
            ]
        card['table_data'] = json.dumps(table_data) if table_data else ""

        # parse some keys as ints
        card['table_y'] = int(card['table_y']) if card['table_y'] else 0

    # Load the template
    with open('portrait.tml', 'r') as infile:
        template = Template(infile.read())

    # Iterate over each card and render it
    # TODO: Use asyncio to render everything in parallel
    for i, card in enumerate(tqdm.tqdm(card_data)):
        # Render the template using jinja
        layout = template.render(card=card)

        # Render the image using squib
        filename = "_output/card{}.png".format(card['id'])
        render_string(layout, 825, 1125, filename)

    # TODO: Hand and showcase renders


if __name__ == "__main__":
    main()
