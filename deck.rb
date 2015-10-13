require 'squib'

Squib::Deck.new(cards: 5, layout: ['portrait.yml', 'layout.yml']) do
    # Load the spreadsheets
    items = xlsx file: 'items.xlsx'
    abilities = xlsx file: 'abilities.xlsx'
    bonuses = xlsx file: 'bonuses.xlsx'

    # TODO: Merge them all together or something
    deck = items

    # Set up the background and icon
    svg file: deck['Frame']
    svg file: deck['Icon'], layout: 'Icon'

    # Generate N tag fields by parsing the csv list in "Tags"
    deck['Tags'] = deck['Tags'].map{ |s| s.split(',').map{ |_| _.strip } }
    max_tags = deck['Tags'].map{ |s| s.length }.max
    (0..max_tags-1).each{|i|
        tag_name = 'Tag' + i.to_s
        tag_color = tag_name + 'Color'
        deck[tag_name] = deck['Tags'].map{ |t| t[i] ? t[i].strip.upcase : nil }
        deck[tag_color] = deck['Tags'].map{ |t|
            t[i] ? '#212121FF' : '#00000000'
        }
        rect x:0, y:85 + i * 40, width:195, height:30,
             fill_color: deck[tag_color], stroke_color: deck[tag_color]
        text x:75, y:88 + i * 40, width:120, height:24,
             str: deck[tag_name], color: "#FFFFFF",
             font: 'UbuntuCondensed Normal 16',
             align: 'left',
             markup: true,
             spacing: -5
    }

    ['Title', 'Subtitle', 'Target', 'Description'].each do |key|
        # Allow special markup for tags using Pango
        deck[key] = deck[key].map { |s|
            s = s.gsub(/\[/, '<span font="UbuntuCondensed Normal 16" rise="3000" background="#212121" foreground="#FFFFFF"> ')
            .gsub(/]/, ' </span>')
            '<span gravity="south">' + s + '</span>'
        }
        # Render the text
        text str: deck[key], layout: key
    end

    # Configure the bonuses
    ['Warmup', 'Cooldown', 'Damage'].each do |key|
        if key != 'Damage'
            deck[key] = deck[key].map { |s| s.to_i }
        end
        text str: deck[key], layout: key
    end

    # Configure the copyright/version text
    deck['CopyrightText'] = (0..deck['Author'].length-1).map { |i|
        "Author: " + deck['Author'][i] + "\n© " +
        deck['Creation Year'][i].to_i.to_s + " and licensed under cc-by-sa"
    }
    text str: deck['CopyrightText'], layout: 'Copyright'

    # Draw some debug bounding boxes
    #%w(cut safe).each do |key|
    #    rect layout: key, stroke_color: 'red'
    #end

    # Save all the cards to output
    save_png prefix: 'card'
    showcase file: 'showcase.png', fill_color: '#0000', trim: 37.5, trim_radius: 25
    hand file: 'hand.png', trim: 37.5, trim_radius: 25, fill_color: '#0000'
end


# TODO: Passives
#Squib::Deck.new(cards: 4, layout: ['landscape.yml', 'landscape.yml']) do
#end


# TODO: Card Back