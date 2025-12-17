import genanki
import random

def create_deck(cards_data: list[dict], deck_name: str = "YouTube Quiz", output_file: str = "output.apkg"):
    """Creates an Anki deck from a list of card data."""
    
    # Generate a random deck ID
    deck_id = random.randrange(1 << 30, 1 << 31)
    
    deck = genanki.Deck(
        deck_id,
        deck_name
    )

    model = genanki.Model(
        1607392319,
        'Simple Model',
        fields=[
            {'name': 'Question'},
            {'name': 'Answer'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Question}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
            },
        ])

    for card in cards_data:
        # Format the answer to include the correct option and maybe the others as context if needed
        # For now, just the answer text.
        # We could also format it as a multiple choice question in the front.
        
        question_text = f"{card['question']}<br><br>"
        for opt in card['options']:
            question_text += f"- {opt}<br>"
            
        note = genanki.Note(
            model=model,
            fields=[question_text, card['answer']]
        )
        deck.add_note(note)

    genanki.Package(deck).write_to_file(output_file)
    print(f"Deck '{deck_name}' created as {output_file}")
