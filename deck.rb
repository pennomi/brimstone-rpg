require 'squib'

Squib::Deck.new(cards: 4, layout: ['hand.yml', 'layout.yml']) do
    # Load the spreadsheet
    deck = xlsx file: 'abilities.xlsx'

    # Set up the basic crap
    background color: '#230602'

    # Replace blocks surrounded by [] with Pango tags
    deck['Description'] = deck['Description'].map {
        |s| s.gsub(/\[/, '<span background="#424242" foreground="#FFFFFF"> ')
             .gsub(/]/, ' </span>')
    }

    # Configure the card's art
    svg file: deck['Art'], layout: 'Art'

    # Configure the Text
    ['Title', 'Description', 'Snark'].each do |key|
        text str: deck[key], layout: key
    end

    # Configure the bonuses
    %w(Attack Defend Health).each do |key|
        svg file: "#{key.downcase}.svg", layout: "#{key}Icon"
        text str: deck[key], layout: key
    end

    # TODO: Render the card background?    

    # Render all the cards to output
    save_png prefix: 'card'
    showcase file: 'showcase.png', fill_color: '#0000'
    hand file: 'hand.png', trim: 37.5, trim_radius: 25, fill_color: '#0000'
end


# TODO: Passives
#Squib::Deck.new(cards: 4, layout: ['hand.yml', 'landscape.yml']) do
#end
