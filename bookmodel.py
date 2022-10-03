from helpers import cleanbook
from nltk import word_tokenize
from nltk import sent_tokenize
from collections import Counter
import re
import random
import json
import sys
import os


class BookModel():
    def __init__(self, book_id, book=None):
        json_file = f"cache/{book_id}.json"

        # Error checking
        if not os.path.exists(json_file) and book is None:
            print("ERROR: If model does not exist book needs to be provided")
            sys.exit(1)

        # Import previous model if it exists
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
            self.book_raw = None
            self.bigrams = data["bigrams"]
            self.first_words = Counter(data["first_words"])
            self.weights = [x[1] for x in self.first_words.most_common()]
        else:
            # Create N-gram model of book
            self.book_raw = book
            self.bigrams = self.extract_bigrams(book)
            self.first_words = self.get_first_words()
            self.weights = [x[1] for x in self.first_words.most_common()]

            # Export file to JSON for persistency
            data = {"bigrams": self.bigrams,
                    "first_words": self.first_words}
            with open(json_file, 'w') as export:
                json.dump(data, export)

    def extract_bigrams(self, book: str) -> dict:
        """ Extracts bigrams from book using NLTK """
        bigrams = {}
        ws = ['.', ',', ';', '?', '!', '"', '’', '-', '(', ')', ':']
        tokens = word_tokenize(book)
        uniq = set(tokens)
        c = 1
        for word in uniq:
            print('', end=f'\rCREATING BIGRAM {c}/{len(uniq)}')
            c += 1
            if word not in ws:
                tmp = [x for i, x in enumerate(tokens)
                       if (tokens[i-1] == word
                           and x not in ws)]
                if tmp:
                    if word not in bigrams:
                        bigrams[word] = tmp
                    else:
                        bigrams[word] += tmp
        return bigrams

    def predict(self, word: str) -> str:
        """ Predicts next word using weighted probability """
        try:
            tmp = Counter(self.bigrams[word])
        except KeyError:
            return None
        weights = [x[1] for x in tmp.most_common()]
        return random.choices(tmp.most_common(), weights=tuple(weights),
                              k=len(tmp))[0][0]

    def get_first_words(self) -> Counter:
        """ Extracts first word from sentences in book with weights """
        tokens_raw = [x.split()[0] for x in sent_tokenize(self.book_raw)]
        first_words = [x for x in tokens_raw if not re.search(r'[^\w\s]', x)]
        return Counter(first_words)


def generate_bookmodel(book_id) -> BookModel:
    """ Generates bookmodel (for redis purposes) """
    return BookModel(book_id, cleanbook(book_id))
