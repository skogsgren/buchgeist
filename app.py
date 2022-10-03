from flask import Flask, request, render_template, redirect, url_for

from bookmodel import BookModel
from bookmodel import generate_bookmodel
from helpers import generate_cards
from helpers import generate_most_popular
from helpers import generate_sentences

import json
import random
import os
import sqlite3
import rq
from rq import Queue
from rq.job import Job
from rq import get_current_job
from redis import Redis


app = Flask(__name__)

# Loading/queue system inspired by:
#     https://gist.github.com/vulcan25/23cae415aafec35abad21f150015a7ef
# Initialize task queue:
r = Redis(host='localhost', port=6379)
q = Queue(connection=r)
# This is an ugly solution to ensure that multiple requests aren't sent to
# redis for enqueing (although it doesn't affect runtime much anyway)
current_job_stack = []


# Initialize variables for homepage.
# NOTE: These are only necessary because I want to do a random sampling of the
# most popular books, otherwise (as I do for search) I can just check with the
# database, and pull directly from there).
if not os.path.exists("most_popular.json"):
    generate_most_popular()
with open("most_popular.json", 'r') as f:
    most_popular = json.load(f)

if not os.path.exists("cards.json"):
    generate_cards(most_popular)
with open("cards.json", 'r') as f:
    cards = json.load(f)


@app.route("/")
def index():
    """ lists randomly chosen books from (most popular books on) gutenberg """
    randomly_selected_cards = {}
    for i in random.sample(sorted(cards), k=20):
        randomly_selected_cards[i] = {"title": cards[i]["title"],
                                      "author": cards[i]["author"],
                                      "img": cards[i]["img"]}
    return render_template("index.html", cards=randomly_selected_cards)


@app.route("/search")
def search():
    query = request.args["query"]
    if query == "":
        return redirect(request.referrer)
    else:
        conn = sqlite3.connect('metadata.db')
        cur = conn.cursor()
        matches = cur.execute(
                    "SELECT * FROM metadata WHERE title LIKE ? OR author LIKE ?",
                    ("%"+query+"%", "%"+query+"%")).fetchall()
        conn.close()
        # To lazily avoid crashing server and/or browser
        if len(matches) > 150:
            matches = matches[:149]
        return render_template("search.html", query=query, matches=matches)


@app.route("/book")
def book():
    # Check if the value in the k/v pair is none
    book_id = request.args["id"]
    if book_id == "":
        return render_template("error.html")

    # Get the title of the book from database
    conn = sqlite3.connect('metadata.db')
    cur = conn.cursor()
    title = cur.execute("SELECT title FROM metadata WHERE book_id=?",
                          (book_id,)).fetchone()[0]
    conn.close()

    # Import model if it already exists
    if os.path.exists(f"cache/{book_id}.json"):
        bm = BookModel(book_id)
        lines = generate_sentences(bm)
        return render_template("book.html", lines=lines, book_id=book_id,
                               title=title)
    else:
        # If job is finished, render book page
        try:
            job = Job.fetch(book_id, connection=r)
            status = job.get_status()
            if status != 'finished':
                current_job_stack.pop(book_id)
                return render_template("loading.html", title=title)
            else:
                return redirect(url_for("/book", book_id=book_id))
        # If job is not running, queue bookmodel
        except rq.exceptions.NoSuchJobError:
            if book_id not in current_job_stack:
                job = q.enqueue(generate_bookmodel, args=(book_id,), timeout=1000)
                current_job_stack.append(book_id)
            # render loading page
            return render_template("loading.html", title=title)
