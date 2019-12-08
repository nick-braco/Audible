import asyncio
import logging
import json
from urllib.parse import urlencode

import aiohttp
import requests
import yarl

from .errors import (
    BadRequest,
    NotFoundError,
    NotResponding,
    NetworkError,
    ServerError,
    Unauthorized,
    UnexpectedError,
    RatelimitError)
from .utils import asynchronous


REQUEST_LOG = '{method} {url} has received {text}, has returned {status}'


class PrepareRequestMixin:
    def _prepare_auth_request(self, method, url, auth_handler,
                              allowed_auth_modes, **kwargs):

        supported_auth_modes = auth_handler.supported_auth_modes

        if isinstance(allowed_auth_modes, str):
            allowed_auth_modes = list(allowed_auth_modes)
        if not allowed_auth_modes:
            allowed_auth_modes = supported_auth_modes

        auth_mode = set(supported_auth_modes).intersection(allowed_auth_modes)
        auth_mode = list(auth_mode)

        if not auth_mode:
            msg = (f'Auth mode(s) `{", ".join(allowed_auth_modes)}` '
                   'not supported by this auth handler.')
            raise PermissionError(msg)

        auth_headers = auth_handler(
            method=method,
            url=url,
            auth_mode=auth_mode,
            **kwargs)

        return auth_headers


class AsyncAuthSession(PrepareRequestMixin, aiohttp.ClientSession):
    def __init__(self, auth_handler=None, allowed_auth_modes=[], **kwargs):

        self._auth_handler = auth_handler
        self._allowed_auth_modes = allowed_auth_modes
        super().__init__(**kwargs)

    def _request(self, method, url, auth_handler=None, allowed_auth_modes=[],
                 params=None, headers={}, **kwargs):

        auth_handler = auth_handler or self._auth_handler

        if auth_handler:
            allowed_auth_modes = allowed_auth_modes or self._allowed_auth_modes
            auth_headers = self._prepare_auth_request(
                method=method,
                url=url,
                params=params,
                auth_handler=auth_handler,
                allowed_auth_modes=allowed_auth_modes,
                json=kwargs.get('json'),
                data=kwargs.get('data')
            )
            headers.update(auth_headers)

        if params:
            url += '?' + urlencode(params)
            url = yarl.URL(url, encoded=True)

        return super()._request(method, url, headers=headers, **kwargs)


class SyncAuthSession(PrepareRequestMixin, requests.Session):
    def __init__(self, auth_handler=None, allowed_auth_modes=[], **kwargs):
        self._auth_handler = auth_handler
        self._allowed_auth_modes = allowed_auth_modes
        super().__init__(**kwargs)

    def request(self, method, url, auth_handler=None, allowed_auth_modes=[],
                params=None, headers={}, **kwargs):

        auth_handler = auth_handler or self._auth_handler

        if auth_handler:
            allowed_auth_modes = allowed_auth_modes or self._allowed_auth_modes
            auth_headers = self._prepare_auth_request(
                method=method,
                url=url,
                params=params,
                auth_handler=auth_handler,
                allowed_auth_modes=allowed_auth_modes,
                json=kwargs.get('json'),
                data=kwargs.get('data')
            )
            headers.update(auth_headers)

        return super().request(
            method, url, headers=headers, params=params, **kwargs)


@asynchronous
async def async_request(method, url, **kwargs):
    logger = logging.getLogger(__name__)
    try:
        async with AsyncAuthSession(raise_for_status=True) as session:
            async with session.request(method, url, **kwargs) as resp:
                text = await resp.text()

                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text

    except aiohttp.ClientError as e:
        logger.warning(e.args)
        raise


class AsyncAPISession:
    def __init__(self, **options):
        default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.session = AsyncAuthSession(headers=default_headers)

        self.logger = logging.getLogger(__name__)

    @asynchronous
    async def close(self):
        await self.session.close()

    def _raise_for_status(self, resp, text, *, method=None):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = text
        code = getattr(resp, 'status', None)

        self.logger.debug(
            REQUEST_LOG.format(method=method or resp.request_info.method,
                               url=resp.url, text=text, status=code)
        )
    
        if 300 > code >= 200:  # Request was successful
            # return data, resp  # value, response
            return data
        elif code == 400:
            raise BadRequest(resp, data)
        elif code in (401, 403):  # Unauthorized request - Invalid credentials
            raise Unauthorized(resp, data)
        elif code == 404:  # not found
            raise NotFoundError(resp, data)
        elif code == 429:
            raise RatelimitError(resp, data)
        elif code == 503:  # Maintainence
            raise ServerError(resp, data)
        else:
            raise UnexpectedError(resp, data)

    @asynchronous
    async def request(self, api, method, path, **kwargs):
        url = 'https://{0.api_url}/{0.version}{1}'.format(api, path)
        auth_handler = api.auth

        try:
            async with self.session.request(
                    method, url, auth_handler=auth_handler, **kwargs
            ) as resp:
                return self._raise_for_status(resp, await resp.text())
        except asyncio.TimeoutError:
            raise NotResponding
        except aiohttp.ServerDisconnectedError:
            raise NetworkError
        except PermissionError as e:
            self.logger.warning(e)
            return {'error': e}

