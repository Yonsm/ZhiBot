from importlib import import_module
from homeassistant.util import slugify
from homeassistant.util.json import load_json, save_json
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.components.http import HomeAssistantView

from typing import Optional
from datetime import timedelta
import homeassistant.auth.models as models
from homeassistant.auth.const import ACCESS_TOKEN_EXPIRATION

import logging
_LOGGER = logging.getLogger(__package__)

DOMAIN = 'zhibot'


async def async_setup(hass, config):
    for conf in config.get(DOMAIN):
        platform = conf['platform']
        botname = platform + 'bot'
        module = import_module('.' + platform, __package__)
        Class = getattr(module, botname)
        hass.http.register_view(Class(botname, hass, conf))
    return True


class basebot(HomeAssistantView):
    """View to handle Configuration requests."""

    def __init__(self, botname, hass, conf):
        self.hass = hass
        self.name = slugify(conf['name']) if 'name' in conf else None

        self.url = '/' + (self.name or botname)
        self.requires_auth = False

        self.token = conf.get('token')
        info = "Serving on " + self.url
        if self.token:
            info += '?token=' + self.token
        else:
            self.init_auth(botname)
        _LOGGER.info(info)

    async def post(self, request):
        try:
            data = await request.json()
            _LOGGER.info(f"REQUEST: %s", data)
            if await self.async_check(request, data):
                result = await self.async_handle(data)
            else:
                result = "没有访问授权！"
            _LOGGER.debug("RESPONSE: %s", result)
        except Exception as e:
            result = repr(e)
            import traceback
            _LOGGER.error(traceback.format_exc())
        return self.json(self.response(result))

    def response(self, result):
        raise NotImplementedError()

    async def async_handle(self, data):
        raise NotImplementedError()

    async def async_check(self, request, data):
        if self.token:
            return self.token == '*' or self.token == request.query.get('token') or self.token == request.headers.get('token')
        return await self.async_check_auth(data)

    def init_auth(self, botname):
        self._auth_ui = None
        self._auth_path = self.hass.config.path(STORAGE_DIR, botname)
        self._auth_users = load_json(self._auth_path) or []

    async def async_check_auth(self, data):
        return self.check_auth(data)

    def check_auth(self, data):
        user = self.get_auth_user(data)
        if not user:
            return False
        if user in self._auth_users:
            return True

        configurator = self.hass.components.configurator
        if self._auth_ui:
            configurator.async_request_done(self._auth_ui)

        def config_callback(fields):
            configurator.request_done(self._auth_ui)
            self._auth_ui = None

            _LOGGER.debug(fields)
            if fields.get('agree') == 'ok':
                self.auth_users.append(user)
                save_json(self._auth_path, self.auth_users)

        self._auth_ui = configurator.async_request_config(
            '智加加', config_callback,
            description=self.get_auth_desc(data),
            submit_caption='完成',
            fields=[{'id': 'agree', 'name': '如果允许访问，请输入“ok”'}],
        )
        return False

    def get_auth_desc(self, data):
        raise NotImplementedError()

    def get_auth_user(self, data):
        raise NotImplementedError()


class oauthbot(basebot):

    def init_auth(self, botname):
        # TODO: 这TMD到底是不是 OAuth 的最佳姿势？严重怀疑，我也不知道哪里抄来的姿势
        store = self.hass.auth._store
        self._async_create_refresh_token = store.async_create_refresh_token
        store.async_create_refresh_token = self.async_create_refresh_token

    async def async_create_refresh_token(
        self,
        user: models.User,
        client_id: Optional[str] = None,
        client_name: Optional[str] = None,
        client_icon: Optional[str] = None,
        token_type: str = models.TOKEN_TYPE_NORMAL,
        access_token_expiration: timedelta = ACCESS_TOKEN_EXPIRATION,
    ) -> models.RefreshToken:
        if access_token_expiration == ACCESS_TOKEN_EXPIRATION:
            access_token_expiration = timedelta(days=365)
        return await self._async_create_refresh_token(user, client_id, client_name, client_icon, token_type, access_token_expiration)

    async def async_check_token(self, token):
        return await self.hass.auth.async_validate_access_token(token) is not None
