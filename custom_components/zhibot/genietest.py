#!/usr/bin/env python3
import sys
import json
import asyncio
import requests
import logging
from genie import handleRequest, makeResponse, _LOGGER


class RemoteHass:

    def __init__(self, url, token):
        self.url = url + '/api/'
        self.token = token
        self.states = self
        self.services = self

    def rest(self, cmd, data=None):
        url = self.url + cmd
        method = 'POST' if data else 'GET'
        _LOGGER.debug('REST %s %s %s', method, url, data or '')
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Content-Type': 'application/json'} if self.token else None
        text = requests.request(method, url, json=data, headers=headers, verify=False).text
        try:
            return json.loads(text)
        except Exception as e:
            _LOGGER.error("%s: %s", e, text)
            return None

    def async_all(self):
        from collections import namedtuple
        entities = []
        for d in self.rest('states') or []:
            entities.append(namedtuple('EntityState', d.keys())(*d.values()))
        return entities

    def get(self, entity_id):
        from collections import namedtuple
        state = self.rest('states/' + entity_id) or {}
        return namedtuple('EntityState', state.keys())(*state.values())

    async def async_call(self, domain, service, data, blocking=False):
        return self.rest('services/' + domain + '/' + service, data) or []


async def main():
    argv = sys.argv
    if len(argv) < 3:
        print(f'Usage: {argv[0]} <https://192.168.1.x:8123> <token> [[-]<1|2|3|4>] [deviceId]')
        exit(0)

    headers = [
        {'namespace': 'AliGenie.Iot.Device.Discovery', 'name': 'DiscoveryDevices'},
        {'namespace': 'AliGenie.Iot.Device.Query', 'name': 'Query'},
        {'namespace': 'AliGenie.Iot.Device.Control', 'name': 'TurnOn'},
        {'namespace': 'AliGenie.Iot.Device.Control', 'name': 'TurnOff'},
    ]
    action = abs(int(argv[3])) - 1 if len(argv) > 3 else 0
    mode = argv[3][0] == '-' if len(argv) > 3 else 0
    deviceId = argv[4] if len(argv) > 4 else 'light.er_tong_fang_tai_deng'
    data = {
        'header': headers[action],
        'payload': {'accessToken': argv[2], 'deviceId': deviceId, 'deviceType': deviceId.split('.')[0]}
    }

    requests.packages.urllib3.disable_warnings()
    if mode:
        text = requests.request('POST', argv[1] + '/geniebot?token=' + argv[2], json=data, verify=False).text
        response = json.loads(text)
    else:
        response = await handleRequest(RemoteHass(argv[1], argv[2]), data)

    devices = response['payload'].get('devices')
    if devices:
        response = [i['deviceId'] + '|' + i['model'] + '=' + i['deviceType'] + '|' + i['zone'] + '/' + i['deviceName'] for i in devices]

    print(json.dumps(response, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    _LOGGER.setLevel(logging.DEBUG)
    _LOGGER.addHandler(logging.StreamHandler())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
