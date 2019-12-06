import json as json_
import logging
from abc import ABCMeta, abstractmethod, abstractproperty
from collections.abc import MutableMapping
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

from .utils import (
    refresh_access_token,
    user_profile,
    deregister_device,
    register_device,
    sign_request
)
from . import authenticate_as_device
from ..helpers.aescipher import AESCipher, detect_file_encryption


logger = logging.getLogger('audible.auth.handler')


class BaseAuth(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, *args, auth_mode: Optional[str] = None, **kwargs):
        pass

    @abstractproperty
    def supported_auth_modes(self) -> List:
        pass

class AccessTokenAuth(BaseAuth):
    def __init__(self,
                 access_token: Optional[str] = None,
                 refresh_token: Optional[str] = None,
                 expires: Optional[Union[int, float]] = None,
                 client_id: str = '0',
                 auto_refresh: bool = False) -> None:

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires = expires
        self.client_id = client_id
        self.auto_refresh = auto_refresh

    def __call__(self, *args, auth_mode=['token'], **kwargs):
        if self.has_access_token:
            if not 'token' in auth_mode:
                logger.warning(f'Auth mode `{auth_mode}` not supported '
                               f'by this handler.')
                return {}

            return {
                'Authorization': 'Bearer ' + self.access_token,
                'client-id': self.client_id
            }
        else:
            logger.warning('No access token found. Can not apply auth.')
            return {}

    @property
    def supported_auth_modes(self):
        return ['token', None]

    @property
    def has_access_token(self):
        return self.access_token is not None

    @property
    def has_refresh_token(self):
        return self.refresh_token is not None

    @property
    def has_expires_timestamp(self):
        return self.expires is not None

    @property
    def access_token_expires(self):
        if self.has_expires_timestamp:
            return datetime.fromtimestamp(self.expires) - datetime.utcnow()

    @property
    def access_token_expired(self):
        if self.has_expires_timestamp:
            return datetime.fromtimestamp(self.expires) < datetime.utcnow()

    def refresh_access_token(self):
        if self.has_refresh_token:
            token = refresh_access_token(self.refresh_token)

            self.access_token = token["access_token"]
            self.expires = token['expires']
        else:
            logger.warning('No refresh token found. Can not refresh access token.')
            pass

    def user_profile(self) -> Dict[str, Any]:
        """Returns user profile."""
        if self.has_access_token:
            return user_profile(self.access_token)
        else:
            logger.warning('No access token found. Can not get user profile.')


class SignAuth(BaseAuth):
    def __init__(self, adp_token: str, private_key: str):
        self.adp_token = adp_token
        self.private_key = private_key

    def __call__(self, method, url, params=None, data=None, json=None,
                 auth_mode=['sign']):

        if not 'sign' in auth_mode:
            logger.warning(f'Auth mode `{auth_mode}` not supported '
                           f'by this handler.')
            return {}

        return sign_request(
            self.adp_token, self.private_key, method, url, params,
            data, json
        )

    @property
    def supported_auth_modes(self):
        return ['sign']

class BaseAuthHandler(BaseAuth, MutableMapping):
    """Base Class for retrieve and handle credentials."""

    def __init__(self):
        self.filename = None
        self.encryption = None
        self.crypter = None

    def __getitem__(self, key):
        return self.__dict__[key]

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            return None

    def __delitem__(self, key):
        del self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return f"{type(self).__name__}({self.__dict__})"

    def __call__(self, method, url, params=None, data=None, json=None, auth_mode=None):
        """
        This method creates signed header for request api.
    
        :param method: the request method (GET, POST, DELETE, ...)
        :param url: the requested url
        :param params: the params of the request
        :param data: the data message body
        :param json: the json message body
        """

        if 'sign' in auth_mode or auth_mode is None:
            if self.adp_token is not None and self.device_private_key is not None:
                return sign_request(
                    self.adp_token, self.device_private_key, method, url, params,
                    data, json
                )
            else:
                logger.warning(f'Auth type `{auth_mode}` not supported '
                           f'by this handler.')
                return {}
        elif 'token' in auth_mode:
            if self.access_token is not None:
                return {
                    'Authorization': 'Bearer ' + self.access_token,
                    'client-id': '0'
                }
            else:
                logger.warning(f'Auth mode `{auth_mode}` not supported '
                           f'by this handler.')
                return {}

    @property
    def supported_auth_modes(self):
        sign = self.adp_token is not None and self.device_private_key is not None
        token = self.access_token is not None

        filtered_list = [i for (i, v) in zip(['sign', 'token'], [sign, token]) if v]
        return filtered_list

    def to_file(self, filename=None, password=None, encryption="default",
                indent=4, set_default=True, **kwargs):

        if filename:
            filename = Path(filename)
        elif self.filename:
            filename = self.filename
        else:
            raise ValueError("No filename provided")

        if encryption != "default":
            pass
        elif self.encryption:
            encryption = self.encryption
        else:
            raise ValueError("No encryption provided")
        
        body = {
            "login_cookies": self.login_cookies,
            "adp_token": self.adp_token,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "device_private_key": self.device_private_key,
            "store_authentication_cookie": self.store_authentication_cookie,
            "device_info": self.device_info,
            "customer_info": self.customer_info,
            "expires": self.expires
        }
        json_body = json_.dumps(body, indent=indent)

        if encryption is False:
            filename.write_text(json_body)
            crypter = None
        else:
            if password:
                crypter = AESCipher(password, **kwargs)
            elif self.crypter:
                crypter = self.crypter
            else:
                raise ValueError("No password provided")

            crypter.to_file(json_body, filename=filename,
                            encryption=encryption, indent=indent)

        logger.info(f"saved data to file {filename}")

        if set_default:
            self.filename = filename
            self.encryption = encryption
            self.crypter = crypter

        logger.info(f"set filename {filename} as default")

    def re_login(self, username, password, market, **options):
        access_token = authenticate_as_device(username, password, market, **options)
        self.access_token = access_token

    def register_device(self, tld):
        register_data = register_device(access_token=self.access_token, tld=tld)

        self.update(**register_data)

    def deregister_device(self, deregister_all: bool = False):
        return deregister_device(access_token=self.access_token, deregister_all=deregister_all)

    def refresh_access_token(self, force=False):
        if force or self.access_token_expired:
            token = refresh_access_token(self.refresh_token)

            self.access_token = token["access_token"]
            self.expires = token['expires']
        else:
            print("Access Token not expired. No refresh necessary. "
                  "To force refresh please use force=True")

    def refresh_or_register(self, tld, force=False):
        try:
            self.refresh_access_token(force=force)
        except:
            try:
                self.deregister_device()
                self.register_device(tld)
            except:
                raise Exception("Could not refresh client.")

    def user_profile(self):
        return user_profile(access_token=self.access_token)

    @property
    def access_token_expires(self):
        return datetime.fromtimestamp(self.expires) - datetime.utcnow()

    @property
    def access_token_expired(self):
        return datetime.fromtimestamp(self.expires) < datetime.utcnow()


class LoginAuthHandler(BaseAuthHandler):
    """Authenticator class to retrieve credentials from login."""
    def __init__(self, access_token, tld, register=True, device_serial=None):
        super().__init__()
        if register:
            resp = register_device(access_token, tld, device_serial)
            logger.info("registered audible device")
            self.update(**resp)
        else:
            self.access_token = access_token


class FileAuthHandler(BaseAuthHandler):
    """Authenticator class to retrieve credentials from stored file."""
    def __init__(self, filename, password=None, **kwargs) -> None:
        super().__init__()
        self.filename = Path(filename)

        self.encryption = detect_file_encryption(self.filename)

        if self.encryption:
            self.crypter = AESCipher(password, **kwargs)
            file_data = self.crypter.from_file(self.filename, self.encryption)
        else:
            file_data = self.filename.read_text()

        json_data = json_.loads(file_data)

        # dont needed anymore
        json_data.pop("locale_code", None)

        self.update(**json_data)

        logger.info(f"load data from file {self.filename}")
