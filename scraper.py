#!/usr/bin/env python

import re
import argparse
import mechanize
from bs4 import BeautifulSoup

AMAZON_URL = 'http://www.amazon.com/gp/product/'
LIBRARY_URL = 'https://mdpl.ent.sirsi.net/client/catalog/search/advanced?'

class Scraper(object):
    def __init__(self):
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.addheaders = [('User-agent', 
                               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7')]

    def rank_by_reviews(self, books):
        ''' 
        Sort books by rating with highest rated books first
        '''
        newlist = sorted(books, key=lambda k: k['rating'], reverse=True) 
        return newlist

    def get_amazon_reviews(self, books):
        '''
        Get the Amazon review/rating for each book in books[]
        '''
        for b in books:
            url = AMAZON_URL + b['isbn10']

            self.br.open(url)

            s = BeautifulSoup(self.br.response().read())
            d = s.find('div', id='avgRating')
            m = re.search(r'\d+(\.\d+)?', d.text.strip())
            f = float(m.group(0))

            b['rating'] = f

    def isbn10_check_digit(self, isbn10):
        '''
        Given the first 9 digits of an ISBN10 number calculate
        the final (10th) check digit
        '''
        i = 0
        s = 0

        for n in xrange(10,1,-1):
            s += n * int(isbn10[i])
            i += 1

        s = s % 11
        s = 11 - s
        v = s % 11
        
        if v == 10:
            return 'x'
        else:
            return str(v)

    def isbn13to10(self, isbn13):
        '''
        Convert an ISBN13 number to ISBN10 by chomping off the
        first 3 digits, then calculating the ISBN10 check digit 
        for the next nine digits to come up with the ISBN10 #
        '''
        first9 = isbn13[3:][:9]
        isbn10 = first9 + self.isbn10_check_digit(first9)
        return isbn10

    def search_library_books(self, url, q):
        '''
        Scrape the first page of books for the given query.
        Calculate the ISBN10 value for each book so we can 
        look it up on Amazon
        '''
        books = []

        def select_form(form):
            return form.attrs.get('id', None) == 'advancedSearchForm'

        self.br.open(url)
        self.br.select_form(predicate=select_form)
        self.br.form['allWordsField'] = q
        self.br.form['formatTypeDropDown'] = ['BOOK']
        self.br.form['languageDropDown'] = ['ENG']
        self.br.submit()

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

    def scrape(self, url, q):
        books = self.search_library_books(url=url, q=q)
        self.get_amazon_reviews(books)
        books = self.rank_by_reviews(books)

        for b in books:
            print b['rating'], b['title']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Search Sirsi catalogue. Return results ranked by Amazon rating.")
    parser.add_argument("-u", "--url",   help="Sirsi url", required=True)
    parser.add_argument("-q", "--query", help="Query string", required=True)
    args = parser.parse_args()

    scraper = Scraper()
    scraper.scrape(args.url, args.query)
