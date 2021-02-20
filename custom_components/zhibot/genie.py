import logging

_LOGGER = logging.getLogger(__name__)


def errorPayload(errorCode):
    """Generate error result"""
    messages = {
        'INVALIDATE_CONTROL_ORDER':    'invalidate control order',
        'SERVICE_ERROR': 'service error',
        'DEVICE_NOT_SUPPORT_FUNCTION': 'device not support',
        'INVALIDATE_PARAMS': 'invalidate params',
        'DEVICE_IS_NOT_EXIST': 'device is not exist',
        'IOT_DEVICE_OFFLINE': 'device is offline',
        'ACCESS_TOKEN_INVALIDATE': ' access_token is invalidate'
    }
    return {'errorCode': errorCode, 'message': messages[errorCode]}


def makeResponse(payload, header={}, properties=None):
    if isinstance(payload, str):
        payload = errorPayload(payload)
    error = 'errorCode' in payload or 'name' not in header
    header['name'] = ('Error' if error else header['name']) + 'Response'
    response = {'header': header, 'payload': payload}
    if properties:
        response['properties'] = properties
    return response


async def handleRequest(hass, request):
    """Handle request"""
    header = request['header']
    payload = request['payload']
    _LOGGER.debug("Handle Request: %s", request)

    properties = None
    name = header['name']
    namespace = header['namespace']
    if namespace == 'AliGenie.Iot.Device.Discovery':
        _payload = await discoveryDevice(hass)
    elif namespace == 'AliGenie.Iot.Device.Control':
        _payload = await controlDevice(hass, header, payload)
    elif namespace == 'AliGenie.Iot.Device.Query':
        properties = queryDevice(hass, payload)
        _payload = errorPayload('IOT_DEVICE_OFFLINE') if properties is None else {} 
    else:
        _payload = errorPayload('SERVICE_ERROR')

    if 'deviceId' in payload:
        _payload['deviceId'] = payload['deviceId']
    return makeResponse(_payload, header, properties)


async def discoveryDevice(hass):
    from aiohttp import ClientSession
    async with ClientSession() as session:
        async with session.get('https://open.bot.tmall.com/oauth/api/placelist') as resp:
            places = (await resp.json())['data']
        async with session.get('https://open.bot.tmall.com/oauth/api/aliaslist') as resp:
            aliases = (await resp.json())['data']
            aliases.append({'key': '电视', 'value': ['电视机']})

    states = hass.states.async_all()
    groups_ttributes = groupsAttributes(states)

    devices = []
    for state in states:
        attributes = state.attributes

        if attributes.get('hidden') or attributes.get('genie_hidden'):
            continue

        friendly_name = attributes.get('friendly_name')
        if not friendly_name:
            continue

        entity_id = state.entity_id
        deviceType = guessDeviceType(entity_id, attributes)
        if not deviceType:
            continue

        deviceName = guessDeviceName(friendly_name, attributes, places)
        if not checkAliasName(deviceName, entity_id, aliases):
            continue

        zone = guessZone(entity_id, attributes, groups_ttributes, places)
        if not zone:
            continue

        prop, action = guessPropertyAndAction(entity_id, attributes, state.state)
        if prop is None:
            continue

        # Merge all sensors into one for a zone
        # https://bbs.hassbian.com/thread-2982-1-1.html
        if deviceType == 'sensor':
            for sensor in devices:
                if sensor['deviceType'] == 'sensor' and zone == sensor['zone']:
                    deviceType = None
                    if not action in sensor['actions']:
                        sensor['properties'].append(prop)
                        sensor['actions'].append(action)
                        sensor['model'] += ' ' + friendly_name
                        # SHIT, length limition in deviceId: sensor['deviceId'] += '_' + entity_id
                    else:
                        _LOGGER.info('SKIP: ' + entity_id)
                    break
            if deviceType is None:
                continue
            deviceName = '传感器'
            entity_id = zone

        devices.append({
            'deviceId': entity_id,
            'deviceName': deviceName,
            'deviceType': deviceType,
            'zone': zone,
            'model': friendly_name,
            'brand': 'HomeAssistant',
            'icon': 'https://home-assistant.io/images/favicon-192x192.png',
            'properties': [prop],
            'actions': ['TurnOn', 'TurnOff', 'Query', action] if action == 'QueryPowerState' else ['Query', action],
            # 'extensions':{'extension1':'','extension2':''}
        })

        #_LOGGER.debug(str(len(devices)) + '. ' + deviceType + ':' + zone + '/' + deviceName + ((' <= ' + friendly_name) if friendly_name != deviceName else ''))

    # for sensor in devices:
        # if sensor['deviceType'] == 'sensor':
        # _LOGGER.info(json.dumps(sensor, indent=2, ensure_ascii=False))

    return {'devices': devices}


async def controlDevice(hass, header, payload):
    entity_id = payload['deviceId']
    service = getControlService(header['name'])
    domain = entity_id[:entity_id.find('.')]
    data = {"entity_id": entity_id}
    if domain == 'cover':
        service = 'close_cover' if service == 'turn_off' else 'open_cover'

    result = await hass.services.async_call(domain, service, data, True)
    return {} if result is not None else errorPayload('IOT_DEVICE_OFFLINE')


def queryDevice(hass, payload):
    deviceId = payload['deviceId']
    if payload['deviceType'] == 'sensor':
        states = hass.states.async_all()
        entity_ids = []
        for state in states:
            attributes = state.attributes
            if state.entity_id.startswith('group.') and (attributes['friendly_name'] == deviceId or attributes.get('genie_zone') == deviceId):
                entity_ids = attributes.get('entity_id')
                break

        properties = [{'name': 'powerstate', 'value': 'on'}]
        for state in states:
            entity_id = state.entity_id
            attributes = state.attributes
            if entity_id.startswith('sensor.') and (entity_id in entity_ids or attributes['friendly_name'].startswith(deviceId) or attributes.get('genie_zone') == deviceId):
                prop, action = guessPropertyAndAction(entity_id, attributes, state.state)
                if prop is None:
                    continue
                properties.append(prop)
        return properties

    state = hass.states.get(deviceId)
    if state is None or state.state == 'unavailable':
        return None
    return {'name': 'powerstate', 'value': 'off' if state.state == 'off' else 'on'}


def getControlService(action):
    i = 0
    service = ''
    for c in action:
        service += (('_' if i else '') + c.lower()) if c.isupper() else c
        i += 1
    return service


DEVICE_TYPES = [
    'television',  # : '电视',
    'light',  # : '灯',
    'aircondition',  # : '空调',
    'airpurifier',  # : '空气净化器',
    'outlet',  # : '插座',
    'switch',  # : '开关',
    'roboticvacuum',  # : '扫地机器人',
    'curtain',  # : '窗帘',
    'humidifier',  # : '加湿器',
    'fan',  # : '风扇',
    'bottlewarmer',  # : '暖奶器',
    'soymilkmaker',  # : '豆浆机',
    'kettle',  # : '电热水壶',
    'waterdispenser',  # : '饮水机',
    'camera',  # : '摄像头',
    'router',  # : '路由器',
    'cooker',  # : '电饭煲',
    'waterheater',  # : '热水器',
    'oven',  # : '烤箱',
    'waterpurifier',  # : '净水器',
    'fridge',  # : '冰箱',
    'STB',  # : '机顶盒',
    'sensor',  # : '传感器',
    'washmachine',  # : '洗衣机',
    'smartbed',  # : '智能床',
    'aromamachine',  # : '香薰机',
    'window',  # : '窗',
    'kitchenventilator',  # : '抽油烟机',
    'fingerprintlock',  # : '指纹锁',
    'telecontroller',  # : '万能遥控器',
    'dishwasher',  # : '洗碗机',
    'dehumidifier',  # : '除湿机',
    'dryer',  # : '干衣机',
    'wall-hung-boiler',  # : '壁挂炉',
    'microwaveoven',  # : '微波炉',
    'heater',  # : '取暖器',
    'mosquito-dispeller',  # : '驱蚊器',
    'treadmill',  # : '跑步机',
    'smart-gating',  # : '智能门控(门锁)',
    'smart-band',  # : '智能手环',
    'hanger',  # : '晾衣架',
]

INCLUDE_DOMAINS = {
    'climate': 'aircondition',
    'fan': 'fan',
    'sensor': 'sensor',
    'light': 'light',
    'media_player': 'television',
    # 'remote': 'telecontroller',
    'switch': 'switch',
    'vacuum': 'roboticvacuum',
    'cover': 'curtain',
}

EXCLUDE_DOMAINS = [
    'automation',
    'binary_sensor',
    'device_tracker',
    'group',
    'zone',
]


def guessDeviceType(entity_id, attributes):
    # http://doc-bot.tmall.com/docs/doc.htm?treeId=393&articleId=108271&docType=1
    if 'genie_deviceType' in attributes:
        return attributes['genie_deviceType']

    # Exclude with domain
    domain = entity_id[: entity_id.find('.')]
    if domain in EXCLUDE_DOMAINS:
        return None

    # Map from domain
    return INCLUDE_DOMAINS[domain] if domain in INCLUDE_DOMAINS else None


def guessDeviceName(friendly_name, attributes, places):
    if 'genie_deviceName' in attributes:
        return attributes['genie_deviceName']

    # Remove place prefix
    for place in places:
        if friendly_name.startswith(place):
            return friendly_name[len(place):]

    return friendly_name


def checkAliasName(deviceName, entity_id, aliases):
    if entity_id.startswith('sensor'):
        return True

    # Name validation
    for alias in aliases:
        if deviceName == alias['key'] or deviceName in alias['value']:
            return True

    _LOGGER.error('%s is not a valid name in https://open.bot.tmall.com/oauth/api/aliaslist', deviceName)
    return False


def groupsAttributes(states):
    groups_attributes = []
    for state in states:
        group_entity_id = state.entity_id
        # and not group_entity_id.startswith('group.all_')
        if group_entity_id != 'group.default_view' and group_entity_id.startswith('group.'):
            group_attributes = state.attributes
            if 'entity_id' in group_attributes:
                groups_attributes.append(group_attributes)
    return groups_attributes


def guessZone(entity_id, attributes, groups_attributes, places):
    # https://open.bot.tmall.com/oauth/api/placelist
    if 'genie_zone' in attributes:
        return attributes['genie_zone']

    # Guess with friendly_name prefix
    name = attributes['friendly_name']
    for place in places:
        if name.startswith(place):
            return place

    # Guess from HomeAssistant group
    for group_attributes in groups_attributes:
        for child_entity_id in group_attributes['entity_id']:
            if child_entity_id == entity_id:
                if 'genie_zone' in group_attributes:
                    return group_attributes['genie_zone']
                return group_attributes['friendly_name']

    return None


def guessPropertyAndAction(entity_id, attributes, state):
    # http://doc-bot.tmall.com/docs/doc.htm?treeId=393&articleId=108264&docType=1
    # http://doc-bot.tmall.com/docs/doc.htm?treeId=393&articleId=108268&docType=1
    # Support On/Off/Query only at this time
    if 'genie_propertyName' in attributes:
        name = attributes['genie_propertyName']

    elif entity_id.startswith('sensor.'):
        unit = attributes['unit_of_measurement'] if 'unit_of_measurement' in attributes else ''
        device_class = attributes['device_class'] if 'device_class' in attributes else ''
        if unit == u'°C' or unit == u'℃' or device_class == 'temperature':
            name = 'Temperature'
        elif unit == 'lx' or unit == 'lm' or device_class == 'illuminance':
            name = 'Brightness'
        elif ('hcho' in entity_id) or device_class == 'hcho':
            name = 'Fog'
        elif ('humidity' in entity_id) or device_class == 'humidity':
            name = 'Humidity'
        elif ('pm25' in entity_id) or device_class == 'pm25':
            name = 'PM2.5'
        elif ('co2' in entity_id) or device_class == 'co2':
            name = 'WindSpeed'
        else:
            return (None, None)
    else:
        name = 'PowerState'
        if state != 'off':
            state = 'on'
    return ({'name': name.lower(), 'value': state}, 'Query' + name)
