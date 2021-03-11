#!/usr/bin/env python3
# https://www.yuque.com/qw5nze/ga14hc/bqd045

from html.parser import HTMLParser
from urllib.request import urlopen
import sys
import json


class TypeParser(HTMLParser):

    def __init__(self, url, begin_row=0, begin_col=0):
        super().__init__()
        self.result = {}
        self._begin_row = begin_row
        self._begin_col = begin_col
        self._row = -1
        self._col = -1
        self._in_td = False
        self.feed(urlopen(url).read().decode('utf-8'))

    def handle_starttag(self, tag, attrs):
        self._in_td = tag == 'td'
        if self._in_td:
            self._col += 1
        elif tag == 'tr':
            self._row += 1
            self._col = -1

    def handle_endtag(self, tag):
        self._in_td = False

    def handle_data(self, data):
        if self._in_td and self._row >= self._begin_row:
            if self._col == self._begin_col:
                self._value = data.strip()
            elif self._col == self._begin_col + 1:
                self.result[data.strip()] = self._value

    def merge_aliases(self, aliases):
        for k, v in self.result.items():
            if v in aliases:
                self.result[k] = aliases[v]
                del aliases[v]

    def hack_aliases(self, hack, aliases):
        for k, vs in hack.items():
            for v in vs:
                if v in aliases:
                    alias = aliases[v]
                    del aliases[v]
                else:
                    alias = v
                if k in self.result:
                    self.result[k] += ',' + alias
                else:
                    self.result[k] = alias


# Parse type name
#parser = TypeParser('https://doc-bot.tmall.com/docs/doc.htm?articleId=108271&docType=1')
#parser = TypeParser('https://www.aligenie.com/doc/357554/eq19cg', 1)
parser = TypeParser('https://www.aligenie.com/doc/357554/gxhx67', 1, 1)
aliases = json.load(urlopen('https://open.bot.tmall.com/oauth/api/aliaslist'))['data']
places = json.load(urlopen('https://open.bot.tmall.com/oauth/api/placelist'))['data']

aliases = {i['key']: ','.join(i['value'] if i['key'] in i['value'] else [i['key']] + i['value']) for i in aliases}
parser.merge_aliases(aliases)
# parser.hack_aliases({'airpurifier': ['净化器']}, aliases)

# Generate
if len(sys.argv) > 1 and sys.argv[1] == 'md':
    print('区域名称：' + ','.join(places) + '\n')
    print('设备名称：' + ';'.join([v for k, v in parser.result.items()]) + '\n')
    print('未知类型：' + ';'.join([v for k, v in aliases.items()]) + '\n')
else:
    print('ZONE_PLACES = ' + str(places) + '\n')
    print('TYPE_NAMES = ' + str(parser.result).replace('{', '{\n    ').replace('}', '\n}').replace(', ', ',\n    ') + '\n')
    #print('VOID_NAMES = ' + str([v for k, v in aliases.items()]).replace('[', '[\n    ').replace(']', '\n]').replace(', ', ', \n    ') + '\n')
