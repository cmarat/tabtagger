import xlrd
from bs4 import BeautifulSoup


class Table(object):
    def __init__(self, filename=None):
        super(Table, self).__init__()
        if filename:
            self.filename = filename
            self.open(filename)

    def open(self, filename):
        self.sheet = sheet = xlrd.open_workbook(filename).sheets()[0]
        self.properties = sheet.row_values(0)
        self.entities = sheet.col_values(0)[1:]


def strip_html_tags(literal):
    return ''.join(BeautifulSoup(literal).findAll(text=True))


def xls(filename):
    sheet = xlrd.open_workbook(filename).sheets()[0]
    origin = sheet.cell_value(0, 0)
    column_headers = [strip_html_tags(v) for v in sheet.row_values(0)]
    row_headers = [strip_html_tags(v) for v in sheet.col_values(0)[1:]]
    return origin, column_headers, row_headers
