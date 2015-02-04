#!/usr/bin/env python

import re
import mechanize
from bs4 import BeautifulSoup

AMAZON_URL = 'http://www.amazon.com/gp/product/'
LIBRARY_URL = 'https://mdpl.ent.sirsi.net/client/catalog/?'

class Scraper(object):
    def __init__(self):
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.addheaders = [('User-agent', 
                               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7')]

    def rank_by_reviews(self, books):
        newlist = sorted(books, key=lambda k: k['rating'], reverse=True) 
        return newlist

    def get_amazon_reviews(self, books):
        for b in books:
            url = AMAZON_URL + b['isbn10']

            self.br.open(url)

            s = BeautifulSoup(self.br.response().read())
            d = s.find('div', id='avgRating')
            m = re.search(r'\d+(\.\d+)?', d.text.strip())
            f = float(m.group(0))

            b['rating'] = f

    def isbn10_check_digit(self, isbn10):
        i = 0
        s = 0

        for n in xrange(10,1,-1):
            s += n * int(isbn10[i])
            i += 1

        s = s % 11
        s = s % 11
        v = 11 - s
        
        if v == 10:
            return 'x'
        else:
            return str(v)

    def isbn13to10(self, isbn13):
        first9 = isbn13[3:][:9]
        isbn10 = first9 + self.isbn10_check_digit(first9)
        return isbn10

    def search_library_books(self, q):
        books = []

        self.br.open(LIBRARY_URL)
        self.br.select_form('searchForm')
        self.br.form['q'] = q
        self.br.submit('searchButton')

        s = BeautifulSoup(self.br.response().read())
        x = {'class': 'isbnValue'}
        y = re.compile(r'^results_cell\d+$')
        z = re.compile(r'^results_bio\d+$')

        for i in s.findAll('input', attrs=x):
            d = i.findParent('div', id=y)
            d = d.find('div', id=z)

            if not i.get('value'):
                continue

            book = {}
            book['title'] = d.a['title']
            book['isbn13'] = i['value']
            book['isbn10'] = self.isbn13to10(book['isbn13'])
            books.append(book)

        return books

    def scrape(self, q='javascript'):
        books = self.search_library_books(q=q)
        self.get_amazon_reviews(books)
        books = self.rank_by_reviews(books)

        for b in books:
            print b['rating'], b['title']

if __name__ == '__main__':
    scraper = Scraper()
    scraper.scrape()
