import xml.etree.cElementTree as ET
import os
import sqlite3
import wget
import urllib
import re
import requests
from bs4 import BeautifulSoup as bs4
import json


def build_database(rdf_dir="rdf-files/cache/epub"):
    """ Build metadata SQL database from catalog of RDF-files.
        Instructions:
            1. Download RDF-files from gutenberg
            2. Unzip them to a folder (I suggest the default above)
            3. Import build_db in python shell and run this function"""

    NS = dict(pg='http://www.gutenberg.org/2009/pgterms/',
              dc='http://purl.org/dc/terms/',
              dcam='http://purl.org/dc/dcam/',
              rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#')

    # connect to and/or create database
    conn = sqlite3.connect('metadata.db')
    cur = conn.cursor()
    if cur.execute("SELECT * FROM sqlite_master;").fetchall() == []:
        cur.execute("CREATE TABLE metadata("
                    "book_id INTEGER NOT NULL UNIQUE,"
                    "author TEXT NOT NULL,"
                    "title TEXT NOT NULL);")
    # create list of all book_ids in rdf catalog
    book_ids = [x for x in os.listdir(rdf_dir)]

    # iterate over each book_id and create SQL entry if missing
    count = 1
    length = len(book_ids)
    for book_id in book_ids:
        book_in_db = f"SELECT * FROM metadata WHERE book_id={book_id}"
        rdf = ET.parse(f"{rdf_dir}/{book_id}/pg{book_id}.rdf").getroot()
        if cur.execute(book_in_db).fetchone() is None:
            rdf = ET.parse(f"{rdf_dir}/{book_id}/pg{book_id}.rdf").getroot()
            # Xpath expressions thanks to
            #     https://gist.github.com/andreasvc/b3b4189120d84dec8857
            try:
                booktype = rdf.find('.//{%(dc)s}type//{%(rdf)s}value' % NS)
                if booktype is not None:  # no point adding audiobooks
                    count += 1
                    continue
                title = rdf.find('.//{%(dc)s}title' % NS).text
            except AttributeError:
                count += 1
                continue  # no point adding a book without discoverable title

            try:
                creator = rdf.find('.//{%(dc)s}creator' % NS)
                author = creator.find('.//{%(pg)s}name' % NS).text
            except AttributeError:
                author = "Unknown"

            book_data = (int(book_id),
                         author.replace('\n', '').replace('\r', ''),
                         title.replace('\n', '').replace('\r', ''))
            print(f"{count}/{length}\t{book_data}")
            count += 1
            cur.execute("INSERT INTO metadata VALUES (?, ?, ?)", book_data)
            conn.commit()

    # close connection to database
    conn.close()


def download_covers(db="metadata.db"):
    """ Download covers for books.
        Instruction:
            1. First create database using 'build_database'
            2. Import this function in python shell and run it,
               pointing it to the database generated in (1)"""
    URL = "https://dante.pglaf.org/cache/epub"

    # extract book_ids from SQL database
    conn = sqlite3.connect("metadata.db")
    cur = conn.cursor()
    book_ids = [x[0] for x in cur.execute("SELECT book_id FROM metadata")]
    conn.close()

    # download images from gutenberg mirror
    if not os.path.exists("static/img"):
        os.mkdir("static/img")
    for book_id in book_ids:
        # smaller cover is used to alleviate stress on server (avg 15kb/img)
        filename = f"pg{book_id}.cover.medium.jpg"
        if not os.path.exists(f"static/img/{filename}"):
            try:
                wget.download(f"{URL}/{book_id}/{filename}", "static/img")
            except urllib.error.HTTPError:
                print(f"Couldn't download {URL}/{book_id}/{filename}")
