# CS50 Final Project - Buchgeist

![](screenshot.png)

This is CS50, and this is my final project for that course. It is a very simple text
prediction website that generates text via bigrams using books from Gutenberg.
Because the books that are used as input are grabbed *from*
[Gutenberg](https://gutenberg.org) additional steps need to be taken since
they prohibit crawling:

1. A database needs to be constructed according to their
   [policy](https://www.gutenberg.org/policy/robot_access.html).
2. Images are downloaded using `wget` so that searches won't be painfully slow.
   The full download was about ~900mb, so not too bad.
3. Then books can be downloaded on a query to query basis.

The website is very simple, and is really only constitued by three locations:

1. **Homepage**: 20 randomly chosen books from Gutenbergs' most popular in the
   last 30 days.
2. **Search**: search in SQL database (which looks very similar to homepage)
3. **Book**: view of a random prediction for 10 sentences using bigram model.

Since the generation of bigram models is much simpler than say GPT-2 or any
transformer model, as long as you stick to the shorter books, the site actually
becomes quite responsive (< 10s per book). Now, the prediction results aren't
*great*, but they work for their intended purpose. Which is to say, just for
fun.


### Requirements

- `redis-server`
- `rqworker`

## Instructions

```
pip3 install -r requirements.txt
```

```python
import nltk
nltk.download('punkt')
```

For documentation regarding generating database from RDF-files, as well as
downloading the actual cover images, use `pydoc3 build_db`.
