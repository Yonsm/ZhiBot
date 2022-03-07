
from . import basebot
from .zhichat import zhiChat
from aiohttp import web

import logging
_LOGGER = logging.getLogger(__name__)


class miaibot(basebot):

    def get_auth_user(self, data):
        return data['session']['application']['app_id']

    def get_auth_desc(self, data):
        return "小爱同学正在试图访问“%s”。\n\napp_id: %s”\nuser_id: %s" % (data['query'], data['session']['application']['app_id'], data['session']['user']['user_id'])

    async def post(self, request):
        self._open_mic = False
        return await super().post(request)

    async def async_handle(self, data):

        request = data['request']

        #
        if 'no_response' in request:
            self._open_mic = True
            return "主人，您还在吗？"

        #
        request_type = request['type']
        if request_type == 2:
            return "再见主人，我在这里等你哦！"

        #
        slot_info = data['request'].get('slot_info')
        intent_name = slot_info.get(
            'intent_name') if slot_info is not None else None
        if intent_name == 'Mi_Welcome':
            self._open_mic = True
            return "您好主人，我能为你做什么呢？"

        answer = await zhiChat(self.hass, data['query'])
        self._open_mic = answer == "未找到设备"
        return answer

    def response(self, result):
        return {
            'version': '1.0',
            'is_session_end': not self._open_mic,
            'response': {
                'open_mic': self._open_mic,
                'to_speak': {'type': 0, 'text': result},
                # 'to_display': {'type': 0,'text': text}
            }
        }

    async def get(self, request):
        q = request.query.get('q')
        qt = {'action': '全部动作', 'name': '全部名称', 'place': '全部位置', 'device': '全部设备'}
        if q == 'corpus' or q in qt:
            if q == 'corpus':
                body = '{action}{place}{device}\n{action}{place}\n{action}{device}\n{place}{device}\n{action}\n{place}\n{device}\n让我家{action}{place}{device}\n让我家{action}{place}\n让我家{action}{device}\n把我家{action}{place}{device}\n把我家{action}{place}\n把我家{action}{device}\n问我家{place}{device}\n问我家{place}\n问我家{device}\n问我家{place}\n问我家{device}\n问我家{action}\n'
            else:
                text = await zhiChat(self.hass, qt[q])
                body = '词条名,同义词（多个同义词之间以英文逗号分隔）\n'
                if q == 'action':
                    body += text.replace('|', ',').replace(';', ',"').replace('\n', '"\n')
                else:
                    body += text.replace('\n', ',\n')
            headers = {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename="%s.csv"' % q}
        else:
            headers = {'Content-Type': 'text/plain'}
            body = await zhiChat(self.hass, q) if await self.async_check(request) else "没有访问授权！"
        return web.Response(body=body, headers=headers)
