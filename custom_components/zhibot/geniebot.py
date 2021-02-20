from . import oauthbot
from .genie import handleRequest, makeResponse

import logging
_LOGGER = logging.getLogger(__name__)


class geniebot(oauthbot):

    async def async_check_auth(self, data):
        return await self.async_check_token(data['payload']['accessToken'])

    async def async_handle(self, data):
        return await handleRequest(self.hass, data)

    def response(self, result):
        if isinstance(result, str):
            return makeResponse('ACCESS_TOKEN_INVALIDATE' if result == '没有访问授权！' else 'SERVICE_ERROR')
        return result
