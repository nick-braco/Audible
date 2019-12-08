# -*- coding: utf-8 -*-

"""
audible.api
~~~~~~~~~~~

This module contains the api interface for AudibleAPI.
"""

from .session import AsyncAPISession


class AudibleAPI:
    """Provides a interface to the internal Audible API.
    
    :param auth_handler: A ˋˋauth_handlerˋˋ class derived from
        :class:ˋauth.handler.BaseAuthˋ
    :param api_url: URL of the api for selected marketplace in format
        ˋˋapi.audible.{tld}ˋˋ. Take a look at :data:ˋmarkets.AUDIBLE_MARKETSˋ
        for all available audible markets tlds.
    :param version: version of remote api to make requests to. Default ˋˋ1.0ˋˋ.
    :param session: Share a :class:ˋsession.AsyncAuthSessionˋ with multiple
        ˋAudibleAPIˋ instances for different marketplaces.
    :param timeout: when a request to :func:`APISession.request` will be timeout.

    :example:

    >>> access_token = 'Atna|...'
    >>> auth_handler = audible.auth.AccessTokenAuth(access_token)
    >>> api = AudibleAPI(auth_handler, 'api.audible.com')
    
    .. todo:: implement more api request templates
           
    """
    def __init__(self, auth_handler, api_url, version='1.0',
                 session=None, timeout=20):

        self.auth = auth_handler
        self.api_url = api_url
        self.version = version
        self.timeout = timeout
        
        self.session = session or AsyncAPISession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return await self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.close()

    def __repr__(self):
        return f'<AudibleAPI for {self.api_url}>'

    def close(self):
        return self.session.close()

    def request(self, method, path, body=None, allowed_auth_modes=[],
                **params):

        if not path.startswith('/'):
            path = '/' + path

        return self.session.request(
            api=self,
            method=method,
            path=path,
            json=body,
            params=params,
            allowed_auth_modes=allowed_auth_modes
        )

    def buy_book(self, asin, use_credit, **params):
        body = {
            'asin': asin,
            'audiblecreditapplied': use_credit
        }

        return self.request(
            method='POST',
            path='/orders',
            body=body,
            **params
        )

    def library(self, **params):
        return self.request(
            method='GET',
            path='/library',
            allowed_auth_modes=['token', 'sign'],
            **params
        )

    def library_book(self, asin, **params):
        return self.request(
            method='GET',
            path=f'/library/{asin}',
            allowed_auth_modes=['token', 'sign'],
            **params
        )
