import logging

_LOGGER = logging.getLogger(__name__)


async def zhiChat(hass, query):
    #query = question.strip()
    _LOGGER.debug("QUERY: %s", query)
    if not query:
        return "空谈误国，实干兴邦！"

    if query == '全部动作' or query == '?' or query == '？':
        return '打开/关闭（设备或群组名）；查询（设备或群组名，可省略“查询”）；触发（自动化，可省略“触发”）'

    states = hass.states.async_all()
    names = [] if query == "全部设备" else None

    answer = await zhiStates(hass, query, states, False, names)  # 先尝试处理设备
    if answer is not None:
        return answer

    # if names is not None:
    #     import locale
    #     locale.setlocale(locale.LC_COLLATE, 'zh_CN.UTF8')
    #     names.sort(cmp=locale.strcoll)

    answer = await zhiStates(hass, query, states, True, names)  # 再尝试处理分组
    if answer is not None:
        return answer

    if names is not None:
        return ','.join(names)

    return "未找到设备"


async def zhiStates(hass, query, states, group, names):
    for state in states:
        entity_id = state.entity_id
        if entity_id.startswith('zone') or group != entity_id.startswith('group'):
            continue

        attributes = state.attributes
        friendly_name = attributes.get('friendly_name')
        if friendly_name is None:
            continue

        if names is not None:
            names.append(friendly_name)
        elif query.endswith(friendly_name):
            return friendly_name + await zhiState(hass, entity_id, state.state, query)
    return None

STATE_NAMES = {
    'on': '开启状态',
    'off': '关闭状态',

    'home': '在家',
    'not_home': '离家',

    'cool': '制冷模式',
    'heat': '制热模式',
    'auto': '自动模式',
    'dry': '除湿模式',
    'fan': '送风模式',

    'open': '打开状态',
    'opening': '正在打开',
    'closed': '闭合状态',
    'closing': '正在闭合',

    'unavailable': '不可用',
}


async def zhiState(hass, entity_id, state, query):
    domain = entity_id[:entity_id.find('.')]
    is_cover = domain == 'cover'  # or entity_id == 'group.all_covers'
    can_action = not domain in [
        'sensor', 'binary_sensor', 'device_tracker', 'person']
    if can_action and '开' in query:
        service = 'open_cover' if is_cover else 'turn_on'
        action = '打开'
    elif can_action and '关' in query:
        service = 'close_cover' if is_cover else 'turn_off'
        action = '关闭'
    elif domain == 'automation':  # and not '查' in query
        service = 'trigger'
        action = '触发'
    else:
        return '为' + (STATE_NAMES[state] if state in STATE_NAMES else state)

    data = {'entity_id': entity_id}
    result = await hass.services.async_call(domain, service, data, True)
    return action + ("成功" if result else "不成功")
