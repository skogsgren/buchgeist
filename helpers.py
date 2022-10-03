import sqlite3
import re
import requests
from bs4 import BeautifulSoup as bs4
import json
import gutenbergpy.textget
import random
from collections import Counter


def generate_most_popular():
    """ Extracts titles from gutenbergs "most popular the last 30 days" """
    html = requests.get("https://www.gutenberg.org/browse/scores/top")
    soup = bs4(html.text, 'html.parser', from_encoding="utf-8")
    # Find beginning of list within soup
    header = soup.find(id="books-last30")
    # Extract links within id of 'books-last30'
    lines = [x.string for x in header.next_sibling.next_sibling.find_all('a')]
    # Remove author by regex search
    most_popular = {}
    for i in lines:
        # Extract title via regex
        try:
            title = re.search(r"(.+ )+(?=by)", i).group(0).rstrip(' ')
        except AttributeError:  # i.e. if a book has no author
            title = re.search(r"(.+ )+(?=\([0-9]+\))", i).group(0).rstrip(' ')
            most_popular[title] = "Unknown"
            continue

        # Extract author's last name via regex
        author = re.search(r"(?<=by )(.+ )+(?=\([0-9]+\))", i).group(0).split()[-1]

        most_popular[title] = author
    # Export titles to json file
    with open("most_popular.json", 'w') as export:
        json.dump(most_popular, export)


def generate_cards(most_popular):
    """ Generates 'cards.json' containing fields for cards at index """
    cards = {}
    # Open database, extract metadata for entries in books from top list
    conn = sqlite3.connect('metadata.db')
    cur = conn.cursor()
    for i in most_popular:
        if most_popular[i] == "Unknown":
            entry = cur.execute(
                    "SELECT * FROM metadata WHERE title LIKE ?", (i,)).fetchone()
        else:
            author = most_popular[i]
            entry = cur.execute(
                    "SELECT * FROM metadata WHERE title LIKE ? AND author LIKE ?",
                    (i, author+'%')).fetchone()
        if entry is not None:
            book_id = int(entry[0])
            cards[book_id] = {"title": entry[2],
                              "author": entry[1],
                              "img": f"/static/img/pg{book_id}.cover.medium.jpg"}
    conn.close()
    # Export titles to json file
    with open("cards.json", 'w') as export:
        json.dump(cards, export)


def cleanbook(book_id):
    # Download book from Gutenberg, strip gutenberg license headers
    raw_book = gutenbergpy.textget.get_text_by_id(book_id)
    clean_book = gutenbergpy.textget.strip_headers(raw_book).decode('utf-8')
    return clean_book


def generate_sentences(bm):
    """ Takes a bookmodel object and its weights as input """
    lines = []
    for i in range(10):
        sentence = []
        # Choose first word in sentence from weighted probability, where
        # the weights are calculated from occurance in book
        word = random.choices(bm.first_words.most_common(),
                              weights=tuple(bm.weights),
                              k=len(bm.first_words))[0][0]
        # Keep on adding words to sentence until the model cannot predict
        # any longer
        while word is not None:
            sentence.append(word)
            word = bm.predict(word)
        # Format sentence and add it to lines that will be printed
        sentence = ' '.join(sentence) + '.'
        lines.append(sentence)
    return lines
