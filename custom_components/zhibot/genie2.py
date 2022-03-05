from . import basebot
from .zhichat import zhiChat
from homeassistant.components.http import HomeAssistantView

import logging
_LOGGER = logging.getLogger(__name__)


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

class genie2view(HomeAssistantView):
    """View to handle Configuration requests."""

    def __init__(self, conf):
        self.name = 'aligenie/' + conf['file'] + '.txt'
        self.url = '/' + self.name
        self.text = conf['text']
        self.requires_auth = False
        _LOGGER.info("Serving on " + self.url)

    async def get(self, request):
        _LOGGER.error("HTTP GET %s" % request)
        return self.text

