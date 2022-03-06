from . import basebot
from .zhichat import zhiChat
from homeassistant.components.http import HomeAssistantView

from aiohttp import web

import logging
_LOGGER = logging.getLogger(__name__)


class genie2view(HomeAssistantView):
    """View to handle Configuration requests."""

    def __init__(self, conf):
        self.name = 'aligenie/' + conf['file'] + '.txt'
        self.url = '/' + self.name
        self.text = conf['text']
        self.requires_auth = False
        _LOGGER.info("Serving on " + self.url)

    async def get(self, request):
        _LOGGER.info("%s", request)
        return self.text


class genie2bot(basebot):

    def __init__(self, botname, hass, conf):
        super().__init__(botname, hass, conf)
        hass.http.register_view(genie2view(conf))

    def get_auth_user(self, data):
        return data['skillId']

    def get_auth_desc(self, data):
        return "天猫精灵正在试图访问“%s”。\n\技能名称: %s”\技能ID: %s" % (data['utterance'], data['skillName'], data['skillId'])

    async def async_handle(self, data):
        return await zhiChat(self.hass, data['utterance'])

    def response(self, result):
        return {
            "returnCode": "0",
            "returnValue": {
                "reply": result,
                "resultType": "RESULT",
                "executeCode": "SUCCESS"
            }
        }

    async def get(self, request):
        q = request.query.get('q')
        qt = {'action': '全部动作', 'name': '全部名称', 'place': '全部位置', 'device': '全部设备'}
        if q == 'corpus' or q in qt:
            if q == 'corpus':
                #body = 'dialog;action;name\n@{action}@{name};;\n@{action};;\n@{name};;\n'
                body = 'dialog;action;device\n@{action}@{place}@{device};;\n@{action}@{place};;\n@{action}@{device};;\n@{place}@{device};;\n@{action};;\n@{place};;\n@{device};;\n'
            else:
                body = await zhiChat(self.hass, qt[q])
                if q != 'action':
                    body = body.replace('\n', ';\n')
            headers = {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename="%s.csv"' % q}
        else:
            headers = {'Content-Type': 'text/plain'}
            body = await zhiChat(self.hass, q) if await self.async_check(request) else "没有访问授权！"
        return web.Response(body=body, headers=headers)
