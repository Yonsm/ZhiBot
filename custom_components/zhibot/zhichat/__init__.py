import logging

_LOGGER = logging.getLogger(__name__)

INTENT_OPEN = ['打开', '开', '开启']
INTENT_CLOSE = ['关闭', '关', '关上', '关掉']
INTENT_QUERY = ['查询', '查']

INTENT_ACTION = ['全部动作', '帮助', '求助', '?', '？']
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
        return '\n'.join([i[0] + ';' + ('|'.join(i[1:]) if len(i) > 1 else '') for i in ALL_INTENTS]) + '\n'

    states = hass.states.async_all()
    if action and action.startswith('全部'):
        items = []

        async def name_callback(domain, entity_id, entity_name, state, attributes):
            items.append(entity_name)

        async def place_callback(domain, entity_id, entity_name, state, attributes):
            place, _ = zhiSplit(ALL_PLACES, entity_name)
            if place is not None and place not in items:
                items.append(place)

        async def device_callback(domain, entity_id, entity_name, state, attributes):
            _, device = zhiSplit(ALL_PLACES, entity_name)
            if device not in items:
                items.append(device)

        await zhiStates(states, device_callback if action == '全部设备' else (place_callback if action == '全部位置' else name_callback))

        if items:
            return '\n'.join(items) + '\n'
        elif action == '全部位置':
            return "未找到位置"

    else:
        answer = await zhiAction(hass, states, action, name) or await zhiAction(hass, states, action, name, False)
        if answer:
            return answer

    return "未找到设备"


async def zhiAction(hass, states, action, name, exact=True):
    answers = ''
    place, device = zhiSplit(ALL_PLACES, name)

    async def callback(domain, entity_id, entity_name, state, attributes):
        if (name == entity_name if exact else zhiMatch(entity_name, place, device)):
            answer = await zhiState(hass, domain, entity_id, state.state, attributes, action, exact)
            if exact:
                return entity_name + answer
            elif answer:
                nonlocal answers
                answers += entity_name + answer + '\n'

    return await zhiStates(states, callback) or answers


async def zhiStates(states, callback):
    for state in states:
        entity_id = state.entity_id
        domain = entity_id[:entity_id.find('.')]
        if domain not in ['zone', 'persistent_notification', 'device_tracker', 'remote']:
            attributes = state.attributes
            entity_name = attributes.get('friendly_name')
            if entity_name:
                answer = await callback(domain, entity_id, entity_name, state, attributes)
                if answer:
                    return answer


def zhiMatch(entity_name, place, device):
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


async def zhiState(hass, domain, entity_id, state, attributes, action, exact):
    service = None
    if domain in ['switch', 'light', 'fan', 'climate', 'cover', 'media_player', 'vacuum']:
        if action == '打开':
            service = 'open_cover' if domain == 'cover' else ('start' if domain == 'vacuum' else 'turn_on')
        elif action == '关闭':
            service = 'close_cover' if domain == 'cover' else ('return_to_base' if domain == 'vacuum' else 'turn_off')
    elif domain == 'automation':
        if not exact:
            return None
        if action == '打开':
            service = 'turn_on'
        elif action == '关闭':
            service = 'turn_off'
        elif action is None:
            service = 'trigger'
            action = '触发'
    elif not exact and (action == '打开' or action == '关闭'):
        return None

    if service:
        data = {'entity_id': entity_id}
        result = await hass.services.async_call(domain, service, data, True)
        #_LOGGER.warn("zhiState entity_id: %s, service: %s, result: %s", entity_id, service, result)
        return action + "成功"

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
    elif domain == 'weather':
        WEATHER_TEXTS = {
            'clear-night': '晴夜',
            'cloudy': '阴',
            'fog': '雾',
            'hail': '冰雹',
            'lightning': '雷电',
            'lightning-rainy': '雷阵雨',
            'partlycloudy': '白天多云',
            'partlycloudy': '夜间多云',
            'pouring': '暴雨',
            'rainy': '雨',
            'snowy': '雪',
            'snowy-rainy': '雨夹雪',
            'sunny': '晴天',
            'windy': '大风',
            'windy-variant': '雾霾有风',
        }
        if state in WEATHER_TEXTS:
            state = WEATHER_TEXTS[state]
        temp = attributes.get('temperature')
        if isinstance(temp, (int, float)):
            extra = '，温度' + str(temp)
        attr = attributes.get('attribution')
        if attr:
            extra = '，' + attr
    return '为' + (STATE_NAMES[state] if state in STATE_NAMES else state) + extra


def zhiSplit(items, text):
    for item in items:
        if text.startswith(item):
            return (item, text[len(item):])
    return (None, text)
