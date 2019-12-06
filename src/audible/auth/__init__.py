from .authenticate import (
    authenticate_as_device,
    authenticate_as_software_player
)
from .utils import (
    refresh_access_token,
    refresh_website_cookies,
    user_profile,
    deregister_device,
    register_device,
    sign_request
)
from .handler import (
    AccessTokenAuth,
    SignAuth,
    LoginAuthHandler,
    FileAuthHandler
)
from ..markets import AudibleMarket


class AuthManager:
    def __init__(self, market, auth=None):
        self.market = AudibleMarket(market) if isinstance(market, 'str') else market
        self.auth = None

    def authenticate(self, username, password, **kwargs):
        market = kwargs.pop('market', None) or self.market
        return authenticate_as_device(username, password, market, **kwargs)

    def authenticate_as_player(self, username, password, **kwargs):
        market = kwargs.pop('market', None) or self.market
        return authenticate_as_software_player(username, password, market, **kwargs)

    def register(self, access_token, **kwargs):
        tld = kwargs.pop('tld') or self.market.tld
        return register_device(access_token, tld, **kwargs)

    def deregister(self, access_token, deregister_all=False):
        return deregister_device(access_token, deregister_all)

    def refresh_access_token(self, refresh_token):
        return refresh_access_token(refresh_token)

    def refresh_website_cookies(self, refresh_token, tld=None):
        tld = tld or self.market.tld
        return refresh_website_cookies(refresh_token, tld)

    def user_profile(self, access_token):
        return user_profile(access_token)








class AuthenticationResponse:
    def __init__(self, access_token, expires, cookies=None):
        self.access_token = access_token
        self.expires = expires
        self.cookies = cookies

    @property
    def has_access_token(self):
        return self.access_token is not None

    @property
    def access_token_expires(self):
        if self.has_expires_timestamp:
            return datetime.fromtimestamp(self.expires) - datetime.utcnow()

    @property
    def access_token_expired(self):
        return datetime.fromtimestamp(self.expires) < datetime.utcnow()


class RegistrationResponse:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __call__(self, method, url, params=None, data=None, json=None):
        return sign_request(
            self.adp_token, self.private_key, method, url, params,
            data, json
        )
