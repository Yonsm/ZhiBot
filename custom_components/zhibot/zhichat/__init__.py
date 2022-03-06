import logging

_LOGGER = logging.getLogger(__name__)

INTENT_OPEN = ['打开', '开', '开启']
INTENT_CLOSE = ['关闭', '关', '关上']
INTENT_QUERY = ['查询', '查']

INTENT_ACTION = ['全部动作', '帮助', '求助', '需要帮助', '?', '？']
INTENT_NAME = ['全部名称']
INTENT_PLACE = ['全部位置', '全部房间', '全部区域']
INTENT_DEVICE = ['全部设备']

ALL_INTENTS = [INTENT_OPEN, INTENT_CLOSE, INTENT_QUERY, INTENT_ACTION, INTENT_NAME, INTENT_PLACE, INTENT_DEVICE]
ALL_PLACES = ['门口', '客厅', '卧室', '客房', '主卧', '次卧', '书房', '餐厅', '厨房', '洗手间', '浴室', '阳台', '宠物房', '老人房', '儿童房', '婴儿房', '保姆房', '玄关', '一楼',
              '二楼', '三楼', '四楼', '楼梯', '走廊', '过道', '楼上', '楼下', '影音室', '娱乐室', '工作间', '杂物间', '衣帽间', '吧台', '花园', '温室', '车库', '休息室', '办公室', '起居室']


async def zhiChat(hass, query):
    #query = question.strip()
    _LOGGER.debug("QUERY: %s", query)
    if not query:
        return '空谈误国，实干兴邦！'

    action = None
    name = query
    for intent in ALL_INTENTS:
        verb, name = zhiSplit(intent, query)
        if verb is not None:
            action = intent[0]
            break

    if action == '全部动作':
        return '\n'.join([';'.join(i) for i in ALL_INTENTS])

    states = hass.states.async_all()
    if action == '全部名称':
        names = []
        for state in states:
            entity_id = state.entity_id
            domain = entity_id[:entity_id.find('.')]
            if domain not in ['zone', 'persistent_notification']:
                attributes = state.attributes
                friendly_name = attributes.get('friendly_name')
                if friendly_name:
                    names.append(friendly_name)
        if names:
            return '\n'.join(names)

    elif action == '全部位置':
        places = []
        all_places = [i for i in ALL_PLACES]
        for state in states:
            entity_id = state.entity_id
            domain = entity_id[:entity_id.find('.')]
            if domain not in ['zone', 'persistent_notification']:
                attributes = state.attributes
                friendly_name = attributes.get('friendly_name')
                if friendly_name:
                    place, device = zhiSplit(ALL_PLACES, friendly_name)
                    if place is not None and place not in places:
                        places.append(device)
        return '\n'.join(places) if places else "未找到位置"

    elif action == '全部设备':
        devices = []
        for state in states:
            entity_id = state.entity_id
            domain = entity_id[:entity_id.find('.')]
            if domain not in ['zone', 'persistent_notification']:
                attributes = state.attributes
                friendly_name = attributes.get('friendly_name')
                if friendly_name:
                    place, device = zhiSplit(ALL_PLACES, friendly_name)
                    if device not in devices:
                        devices.append(device)
        if devices:
            return '\n'.join(devices)

    else:
        answer = await zhiStates(hass, states, action, name) or await zhiStates(hass, states, action, name, False)
        if answer:
            return answer

    return "未找到设备"


async def zhiStates(hass, states, action, name, exact=True):
    answers = ''
    place, device = zhiSplit(ALL_PLACES, name)
    for state in states:
        entity_id = state.entity_id
        domain = entity_id[:entity_id.find('.')]
        if domain not in ['zone', 'persistent_notification']:
            attributes = state.attributes
            entity_name = attributes.get('friendly_name')
            if entity_name and zhiMatch(domain, entity_name, name, place, device, exact):
                answer = entity_name + await zhiState(hass, domain, entity_id, state.state, attributes, action)
                if exact:
                    return answer
                answers += answer + '\n'
    return answers


def zhiMatch(domain, entity_name, name, place, device, exact):
    if exact:
        return name == entity_name
    if domain == 'automation':
        return False
    entity_place, entity_device = zhiSplit(ALL_PLACES, entity_name)
    return entity_place is not None and ((place == entity_place and device == '') or (place is None and device == entity_device))


STATE_NAMES = {
    None: '无',
    'unknown': '未知',
    'unavailable': '不可用',

    'off': '关闭',
    'on': '开启',

    'idle': '空闲',
    'auto': '自动',
    'low': '低速',
    'medium': '中速',
    'middle': '中速',
    'high': '高速',
    'favorite': '最爱',

    'strong': '高速',
    'silent': '静音',
    'interval': '间歇',

    'cool': '制冷',
    'auto': '自动',
    'heat': '制热',
    'dry': '除湿',
    'fan': '送风',
    'fan_only': '送风',

    'Error': '错误',
    'Paused': '暂停',
    'Cleaning': '清扫中',
    'Charging': '充电中',
    'Charger disconnected': '充电断开',

    'home': '在家',
    'not_home': '离家',

    'open': '打开',
    'opening': '正在打开',
    'closed': '闭合',
    'closing': '正在闭合',
}


async def zhiState(hass, domain, entity_id, state, attributes, action):
    is_cover = domain == 'cover'  # or entity_id == 'group.all_covers'
    can_action = not domain in ['sensor', 'binary_sensor', 'device_tracker', 'person']
    if can_action and action == '打开':
        service = 'open_cover' if is_cover else 'turn_on'
    elif can_action and action == '关闭':
        service = 'close_cover' if is_cover else 'turn_off'
    elif domain == 'automation':
        service = 'trigger'
        action = '触发'
    else:
        extra = ''
        if domain == 'vacuum':
            status = attributes.get('status')
            if status:
                state = status
        elif domain == 'fan':
            mode = attributes.get('preset_mode')
            if mode:
                state = mode
        elif domain == 'climate':
            temp = attributes.get('current_temperature')
            if isinstance(temp, (int, float)):
                extra = '，温度' + str(temp)
        return '为' + (STATE_NAMES[state] if state in STATE_NAMES else state) + extra

    data = {'entity_id': entity_id}
    result = await hass.services.async_call(domain, service, data, True)
    return action + ("成功" if result else "不成功")


def zhiSplit(items, text):
    for item in items:
        if text.startswith(item):
            return (item, text[len(item):])
    return (None, text)
