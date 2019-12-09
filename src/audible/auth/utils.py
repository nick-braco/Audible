import base64
import json as json_
import re
import string
from datetime import datetime, timedelta
from random import choices
from typing import Any, Dict
from urllib.parse import urlencode, urlparse

import rsa

from ..session import async_request


def refresh_access_token(refresh_token) -> Dict[str, Any]:
    """
    Refresh access token with refresh token.
    Access tokens are valid for 60 mins.
    """
    url = 'https://api.amazon.com/auth/token'
    body = {
        'app_name': 'Audible',
        'app_version': '3.7',
        'source_token': refresh_token,
        'requested_token_type': 'access_token',
        'source_token_type': 'refresh_token'
    }

    resp = async_request('POST', url, json=body, raise_for_status=True)

    expires_in_sec = int(resp['expires_in'])
    expires = (datetime.utcnow() + timedelta(seconds=expires_in_sec)).timestamp()

    return {
        'access_token': resp['access_token'],
        'expires': expires
    }


def user_profile(access_token: str):
    """Returns user profile."""

    url = 'https://api.amazon.com/user/profile'
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    return async_request('GET', url, headers=headers, raise_for_status=True)


def refresh_website_cookies(refresh_token: str, tld):
    """
    Refresh website token with refresh token.
    """

    url = 'https://www.amazon.com/ap/exchangetoken'
    body = {
        'app_name': 'Audible',
        'app_version': '3.7',
        'source_token': refresh_token,
        'requested_token_type': 'auth_cookies',
        'source_token_type': 'refresh_token',
        'domain': f'.amazon.{tld}'
    }

    return async_request('POST', url, data=body, raise_for_status=True)


def get_random_device_serial() -> str:
    """
    Generates a random text (str + int) with a length of 40 chars.
    
    Use of random serial prevents unregister device by other users
    with same `device_serial`.
    """
    return ''.join(choices(string.ascii_uppercase + string.digits, k=40))


class RegistrationResponse:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def register_device(access_token: str, tld: str, device_serial=None,
                    **kwargs) -> Dict[str, Any]:
    """
    Register a dummy audible device with access token and cookies
    from ``auth_login``.
    Returns important credentials needed for access audible api.
    """

    url = 'https://api.amazon.com/auth/register'

    default_token = [
        'bearer', 'mac_dms', 'website_cookies', 'store_authentication_cookie'
    ]
    default_extensions = ['device_info', 'customer_info']
    
    requested_token_type = kwargs.pop('requested_token_type', default_token)
    requested_extensions = kwargs.pop('requested_extensions', default_extensions)

    serial = device_serial or get_random_device_serial()

    body = {
        'requested_token_type': requested_token_type,
        'cookies': {
            'website_cookies': [],
            'domain': f'.amazon.{tld}'
        },
        'registration_data': {
            'domain': 'Device',
            'app_version': '3.7',
            'device_serial': serial,
            'device_type': 'A2CZJZGLK2JJVM',
            'device_name': ('%FIRST_NAME%%FIRST_NAME_POSSESSIVE_STRING%%DUPE_'
                            'STRATEGY_1ST%Audible for iPhone'),
            'os_version': '12.3.1',
            'device_model': 'iPhone',
            'app_name': 'Audible'
        },
        'auth_data': {
            'access_token': access_token
        },
        'requested_extensions': requested_extensions
    }

    resp = async_request('POST', url, json=body, raise_for_status=True)

    if 'error' in resp['response']:
        code = resp['response']['error']['code']
        msg = resp['response']['error']['message']
        raise Exception(f'{code}: {msg}')

    success_response = resp['response']['success']
    bearer = success_response['tokens']['bearer']
    expires_s = int(bearer.pop('expires_in'))
    bearer['expires'] = (datetime.utcnow() + timedelta(seconds=expires_s)).timestamp()

    return success_response
    # TODO: work here
    # return success_response

    '''tokens = success_response['tokens']
    adp_token = tokens['mac_dms']['adp_token']
    device_private_key = tokens['mac_dms']['device_private_key']
    store_authentication_cookie = tokens['store_authentication_cookie']
    access_token = tokens['bearer']['access_token']
    refresh_token = tokens['bearer']['refresh_token']
    expires_s = int(tokens['bearer']['expires_in'])
    expires = (datetime.utcnow() + timedelta(seconds=expires_s)).timestamp()

    extensions = success_response['extensions']
    device_info = extensions['device_info']
    customer_info = extensions['customer_info']

    login_cookies_new = dict()
    for cookie in tokens['website_cookies']:
        login_cookies_new[cookie['Name']] = cookie['Value'].replace(r'"', r'')

    return {
        'adp_token': adp_token,
        'device_private_key': device_private_key,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires': expires,
        'login_cookies': login_cookies_new,
        'store_authentication_cookie': store_authentication_cookie,
        'device_info': device_info,
        'customer_info': customer_info
    }'''


def deregister_device(access_token: str,
                      deregister_all: bool = False):
    """
    Deregister device which was previously registered with `access_token`.

    `access_token` is valid until expiration. All other credentials will
    be invalid immediately.
    
    If `deregister_all=True` all registered devices will be deregistered.
    """

    url = 'https://api.amazon.com/auth/deregister'
    body = {'deregister_all_existing_accounts': deregister_all}
    headers = {'Authorization': f'Bearer {access_token}'}

    return async_request('POST', url, json=body, headers=headers,
                         raise_for_status=True)


def verify_access_token(access_token: str):
    return access_token.startswith('Atna|')


def verify_refresh_token(refresh_token: str):
    return refresh_token.startswith('Atnr|')


def verify_adp_token(adp_token: str):
    parts = re.findall(r"{.*?}", adp_token)
    if len(parts) == 5:
        as_dict = {}
        for part in parts:
            key, value = re.search('{(.*?):(.*?)}', part).groups()
            print(re.search('{(.*?):(.*?)}', part).groups())
            as_dict[key] = value

        return list(as_dict.keys()) == ['enc', 'key', 'iv', 'name', 'serial']
    else:
        return False


def verify_device_private_key(device_key: str):
    return (device_key.startswith('-----BEGIN RSA PRIVATE KEY-----') and
            device_key.endswith('-----END RSA PRIVATE KEY-----\n'))


def verify_cookies(cookies: dict):
    return set(map(type, cookies.values())) == {str}


def sign_request(adp_token, device_private_key, method, url, params=None,
                 data=None, json=None):
    """
    This method creates signed header for request api.

    :param adp_token: the adp_token
    :param device_private_key: the device cert    
    :param method: the request method (GET, POST, DELETE, ...)
    :param url: the requested url
    :param params: the params of the request
    :param data: the data message body
    :param json: the json message body
    """

    path = urlparse(url).path
    if params:
        query = urlencode(params)
        path += f'?{query}'

    date = datetime.utcnow().isoformat('T') + 'Z'

    if data is None and json is None:
        body = ''
    elif json is not None and data is None:    
        body = json_.dumps(json)
    else:
        body = urlencode(data)

    data = f'{method}\n{path}\n{date}\n{body}\n{adp_token}'.encode()

    key = rsa.PrivateKey.load_pkcs1(device_private_key.encode())
    signed_data = rsa.pkcs1.sign(data, key, 'SHA-256')
    signed_encoded = base64.b64encode(signed_data)
    signed_decoded = signed_encoded.decode()

    signature = f'{signed_decoded}:{date}'

    return {
        'x-adp-token': adp_token,
        'x-adp-alg': 'SHA256withRSA:1.0',
        'x-adp-signature': signature
    }

