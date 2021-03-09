#!/usr/bin/env python3

from html.parser import HTMLParser
from urllib.request import urlopen
import sys
import json


class AliGenieDeviceTypeParser(HTMLParser):

    def __init__(self, *, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.result = {}
        self._is_td = False
        self._is_key = False

    def handle_starttag(self, tag, attrs):
        self._is_td = tag == 'td'

    def handle_endtag(self, tag):
        self._is_td = False

    def handle_data(self, data):
        if self._is_td:
            if self._is_key:
                self.result[data.strip()] = self._value
            else:
                self._value = data.strip()
            self._is_key = not self._is_key


# Parse type name
parser = AliGenieDeviceTypeParser()
parser.feed(urlopen('https://doc-bot.tmall.com/docs/doc.htm?articleId=108271&docType=1').read().decode('utf-8'))

# Add hack type
parser.result['VMC'] = '新风机'
parser.result['projector'] = '投影仪'
parser.result['gateway'] = '网关'  # TEST

aliases = {i['key']: i['value'] for i in json.load(urlopen('https://open.bot.tmall.com/oauth/api/aliaslist'))['data']}

# Merge type names
type_names = {}
for k, v in parser.result.items():
    if v in aliases:
        alias = aliases[v]
        if v not in alias:
            alias.insert(0, v)
        type_names[k] = alias
        del aliases[v]
    else:
        type_names[k] = [v]

# Merge hack type
TYPE_ALIAS = {
    'heater': ['地暖'],  # TEST
    'STB': ['电视盒子'],  # TEST
    'airpurifier': ['净化器'],
}
for k, vs in TYPE_ALIAS.items():
    for v in vs:
        if v in aliases:
            alias = aliases[v]
            del aliases[v]
            if v not in alias:
                alias.insert(0, v)
        else:
            alias = [v]
        if k in type_names:
            type_names[k].extend(alias)
        else:
            type_names[k] = alias


# Merge void names
void_names = []
for k, v in aliases.items():
    if k not in v:
        v.append(k)
    void_names.append(v)

places = json.load(urlopen('https://open.bot.tmall.com/oauth/api/placelist'))['data']

# Generate
if len(sys.argv) > 1 and sys.argv[1] == 'md':
    print('区域名称：' + ','.join(places) + '\n')
    print('设备名称：' + ';'.join([','.join(v) for k, v in type_names.items()]) + '\n')
    print('未知类型：' + ';'.join([','.join(i) for i in void_names]) + '\n')
else:
    print('ZONE_PLACES = ' + str(places) + '\n')
    print('TYPE_NAMES = ' + str(type_names).replace('{', '{\n    ').replace('}', '\n}').replace('], ', '],\n    ') + '\n')
    #print('VOID_NAMES = ' + str(void_names).replace('[[', '[\n    [').replace(']]', ']\n]').replace('], ', '], \n    ') + '\n')
