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
    states = hass.states.async_all()
    groups_attributes = groupsAttributes(states)

    devices = []
    for state in states:
        attributes = state.attributes

        if attributes.get('hidden') or attributes.get('genie_hidden'):
            continue

        friendly_name = attributes.get('friendly_name')
        if not friendly_name:
            continue

        entity_id = state.entity_id
        zone, deviceName = guessZoneName(entity_id, friendly_name, attributes, groups_attributes)
        deviceType = guessDeviceType(entity_id, deviceName, attributes)
        if deviceType is None:
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


ZONE_PLACES = ['门口', '客厅', '卧室', '客房', '主卧', '次卧', '书房', '餐厅', '厨房', '洗手间', '浴室', '阳台', '宠物房', '老人房', '儿童房', '婴儿房', '保姆房', '玄关', '一楼',
               '二楼', '三楼', '四楼', '楼梯', '走廊', '过道', '楼上', '楼下', '影音室', '娱乐室', '工作间', '杂物间', '衣帽间', '吧台', '花园', '温室', '车库', '休息室', '办公室', '起居室']

TYPE_NAMES = {
    'light': ['灯', '房灯', '吸顶灯', '床头灯', '床灯', '电灯', '吊灯', '台灯', '落地灯', '壁灯', '挂灯', '射灯', '筒灯', '灯带', '灯条', '暗藏灯', '背景灯', '阅读灯', '柜灯', '衣柜灯', '天花灯', '路灯', '彩灯'],
    'aircondition': ['空调', '空气调节器', '挂式空调'],
    'fan': ['风扇', '电风扇', '落地扇', '电扇', '台扇', '壁扇', '顶扇', '驱蚊风扇', '暖风扇', '净化暖风扇', '冷风扇', '塔扇'],
    'airpurifier': ['空气净化器', '空净', '空气清洁器'],
    'roboticvacuum': ['扫地机器人', '扫地机', '打扫机', '自动打扫机'],
    'curtain': ['窗帘', '窗纱', '布帘', '纱帘', '百叶帘', '卷帘'],
    'humidifier': ['加湿器', '空气加湿器', '加湿机', '空气加湿机'],
    'outlet': ['插座', '插头', '排插单孔单控'],
    'milkregulator': ['暖奶器', '热奶器', '牛奶', '调奶器', '温奶器', '冲奶机'],
    'kettle': ['电热水壶', '养生水壶', '水壶', '养生壶', '热水壶', '电水壶'],
    'soymilkmaker': ['豆浆机'],
    'oven': ['烤箱', '嵌入式烤箱'],
    'television': ['电视'],
    'waterpurifier': ['净水器', '净水器箱型'],
    'fridge': ['冰箱', '双开门冰箱', '冰柜'],
    'switch': ['开关'],
    'STB': ['机顶盒'],
    'sensor': ['传感器'],
    'waterheater': ['热水器', '电热水器', '燃气热水器'],
    'waterdispenser': ['饮水机'],
    'camera': ['摄像头', '摄像', '摄像机'],
    'router': ['路由器', '路由', '智能路由器'],
    'cooker': ['电饭煲', '电饭锅', '饭煲', '饭锅'],
    'aquarium': ['水族箱控制器', '智能鱼缸', '鱼缸'],
    'facesteam': ['蒸脸器'],
    'heater': ['取暖器', '加热器'],
    'foodprocesser': ['料理机'],
    'washmachine': ['洗衣机', '顶开式洗衣机', '滚筒洗衣机'],
    'microwaveoven': ['微波炉'],
    'airbox': ['空气检测仪'],
    'dehumidifier': ['除湿机', '除湿器'],
    'smartbed': ['智能床'],
    'telecontroller': ['万能遥控器'],
    'aromamachine': ['香薰机'],
    'window': ['窗'],
    'kitchenventilator': ['抽油烟机', '抽烟机', '烟机'],
    'fingerprintlock': ['指纹锁'],
    'dishwasher': ['洗碗机', '洗碗器'],
    'automobile': ['车'],
    'bathheater': ['浴霸'],
    'electricairer': ['晾衣机'],
    'VMC': ['新风机'],
    'wall-hung-boiler': ['壁挂炉'],
    'dryer': ['干衣机', '干衣器'],
    'mosquitoDispeller': ['驱蚊器'],
    'treadmill': ['跑步机'],
    'smart-gating': ['智能门控', '智能门锁', '门锁', '电子锁'],
    'Breaking': ['破壁机', '超跑'],
    'gateway': ['网关'],
    'scale': ['秤'],
    'smart-band': ['智能手环'],
    'electricpressurecooker': ['电压力锅', '压力锅', '高压锅'],
    'hanger': ['晾衣架', '衣架', '晒衣架'],
    'blanket': ['电热毯'],
    'instrument': ['按摩仪'],
    'armchair': ['按摩椅'],
    'button': ['无线按钮'],
    'smartbox': ['电视盒子', '盒子', '小米盒子', '荣耀盒子', '乐视盒子', '智能盒子'],
    'projector': ['投影仪', '投影机', '投影', '背投'],
    'fanLight': ['风扇灯'],
    'door_sensor': ['门磁传感器'],
    'IR_sensor': ['人体传感器'],
    'lightStrip': ['灯带'],
    'smartPeephole': ['智能猫眼'],
    'Gaswaterheater': ['燃气热水器'],
    'breadMachine': ['面包机'],
    'disinfectionCabine': ['消毒柜'],
    'inductionCooker': ['磁炉', '电磁炉'],
    'waterReplenishing': ['补水仪'],
    'ElectricToothbrush': ['电动牙刷'],
    'mosquitoKiller': ['灭蚊器'],
    'DoubleButtonSwitch': ['双键开关'],
    'ThreeButtonSwitch': ['三键开关'],
    'singleFireSwitch': ['单火开关'],
    'singleFireDoubleButtonSwitch': ['单火双键开关'],
    'singleFireThreeButtonSwitch': ['单火三键开关'],
    'Juicer': ['榨汁机'],
    'milkAdjuster': ['调奶器'],
    'wineCooler': ['酒柜'],
    'breastPump': ['吸奶器'],
    'sterilizerPot': ['消毒锅'],
    'windowCleanMachine': ['擦窗机'],
    'spinningBike': ['动感单车'],
    'walkingPad': ['走步机'],
    'cookingPot': ['多功能料理锅'],
    'vacuumCleaner': ['吸尘器'],
    'computer': ['电脑'],
    'THSensor': ['温湿度传感器'],
    'fourButtonSwitch': ['四键开关'],
    'garbageDisposer': ['垃圾处理器'],
    'bloodGlucoseMeter': ['血糖仪'],
    'bloodPressureMeter': ['血压仪'],
    'SmartTrashCan': ['智能垃圾桶'],
    'heatingTable': ['取暖桌'],
    'RowingMachine': ['划船机'],
    'ReadingPen': ['点读笔'],
    'CatLitter': ['猫砂盆'],
    'iceMachine': ['制冰机'],
    'deepFryer': ['电炸锅'],
    'Stimulator': ['按摩贴'],
    'Smokedetector': ['烟雾传感器'],
    'Gasdetector': ['燃气传感器'],
    'Waterdetector': ['水浸传感器'],
    'LightSensor': ['光线传感器'],
    'Warmboard': ['暖菜板'],
    'moxibustionApparatus': ['艾灸仪'],
    'foodMachine': ['辅食机'],
    'footTub': ['足浴盆'],
    'warmPalaceBelt': ['暖宫带']
}

DOMAIN_TYPES = {
    'climate': 'aircondition',
    'cover': 'curtain',
    'fan': 'fan',
    'light': 'light',
    'media_player': 'television',
    # 'remote': 'telecontroller',
    'switch': 'switch',
    'vacuum': 'roboticvacuum',
}


def guessDeviceType(entity_id, deviceName, attributes):
    if 'genie_deviceType' in attributes:
        return attributes['genie_deviceType']

    domain = entity_id[:entity_id.find('.')]
    if domain == 'sensor':
        return 'sensor'

    elif domain not in DOMAIN_TYPES:
        return None

    for k, v in TYPE_NAMES.items():
        for i in v:
            if deviceName in i:
                return k

    # for v in VOID_NAMES:
    #     for i in v:
    #         if deviceName in i:
    #             return DOMAIN_TYPES[domain]

    _LOGGER.warn('%s “%s”不是规范的名称，请参考 https://github.com/Yonsm/ZhiBot#4-名称规范', entity_id, deviceName)
    return DOMAIN_TYPES[domain]


def guessZoneName(entity_id, friendly_name, attributes, groups_attributes):
    zone = None
    name = attributes.get('genie_deviceName')
    for place in ZONE_PLACES:
        if name and name.startswith(place):
            zone = place
            name = name[len(place):]
            break
        elif friendly_name.startswith(place):
            zone = place
            if not name:
                name = friendly_name[len(place):]
            break
    return (attributes.get('genie_zone', zone) or guessGroupZone(entity_id, groups_attributes) or place, name or friendly_name)


def guessGroupZone(entity_id, groups_attributes):
    # Guess zone from group
    for group_attributes in groups_attributes:
        for child_entity_id in group_attributes['entity_id']:
            if child_entity_id == entity_id:
                group_zone = group_attributes.get('genie_zone', group_attributes['friendly_name'])
                if group_zone in ZONE_PLACES:
                    return group_zone
                break
    return None


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
