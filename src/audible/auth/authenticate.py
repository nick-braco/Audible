import base64
from datetime import datetime, timedelta
import hashlib
from typing import Dict

import aiohttp
from bs4 import BeautifulSoup

from .callbacks import default_captcha_callback, default_otp_callback
from .metadata import encrypt_metadata, meta_audible_app
from ..utils import asynchronous


USER_AGENT = ('Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) '
              'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148')


def get_soup(resp_text):
    return BeautifulSoup(resp_text, 'html.parser')


def get_inputs_from_soup(soup) -> Dict[str, str]:
    inputs = {}
    for node in soup.select('input[type=hidden]'):
        if node['name'] and node['value']:
            inputs[node['name']] = node['value']
    return inputs


def check_for_captcha(soup):
    captcha = soup.find('img', alt=lambda x: x and 'CAPTCHA' in x)
    return captcha is not None


def extract_captcha_url(soup):
    captcha = soup.find('img', alt=lambda x: x and 'CAPTCHA' in x)
    return captcha['src'] if captcha else None


def check_for_mfa(soup):
    mfa = soup.find('form', id=lambda x: x and 'auth-mfa-form' in x)
    return mfa is not None


def check_for_choice_mfa(soup):
    mfa_choice = soup.find('form', id='auth-select-device-form')
    return mfa_choice is not None


def check_for_cvf(soup):
    cvf = soup.find('div', id='cvf-page-content')
    return cvf is not None


def extract_cookies_from_session(session, base_url):
    cookies = session.cookie_jar.filter_cookies(base_url)
    cookies_dict = dict()

    for key, value in cookies.items():
        cookies_dict[key] = value.value

    return cookies_dict


class _BaseLogin:
    def __init__(self, **options):
        self._captcha_callback = (options.pop('captcha_callback', None) or
                                  default_captcha_callback)
        self._otp_callback = (options.pop('otp_callback', None) or
                              default_otp_callback)
        
        headers = options.pop('headers', {})
        if 'User-Agent' not in headers:
            headers['User-Agent'] = USER_AGENT
        self._session = aiohttp.ClientSession(headers=headers)

        self.last_response = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    @property
    def last_response(self):
        return self._last_response

    @last_response.setter
    def last_response(self, data):
        self._last_response = data

    async def close(self):
        await self._session.close()

    async def request(self, method, url, **kwargs):
        async with self._session.request(method, url, **kwargs) as resp:
            resp_soup = get_soup(await resp.text())
            self.last_response = resp, resp_soup

            return resp_soup

    async def login(self, username, password, base_url, oauth_params):
        base_url = base_url
        sign_in_url = base_url + '/ap/signin'
        cvf_url = base_url + '/ap/cvf/verify'

        while 'session-token' not in self._session.cookie_jar.\
                filter_cookies(base_url):
            await self.request('GET', base_url)

        oauth_soup = await self.request(
            'GET', sign_in_url, params=oauth_params)

        login_inputs = get_inputs_from_soup(oauth_soup)
        login_inputs['email'] = username
        login_inputs['password'] = password
        metadata = meta_audible_app(
            self._session._default_headers['User-Agent'],
            base_url)
        login_inputs['metadata1'] = encrypt_metadata(metadata)

        login_soup = await self.request('POST', sign_in_url, data=login_inputs)

        # check for captcha
        while check_for_captcha(login_soup):
            captcha_url = extract_captcha_url(login_soup)
            guess = self._captcha_callback(captcha_url)

            inputs = get_inputs_from_soup(login_soup)
            inputs['guess'] = guess
            inputs['use_image_captcha'] = 'true'
            inputs['use_audio_captcha'] = 'false'
            inputs['showPasswordChecked'] = 'false'
            inputs['email'] = username
            inputs['password'] = password
    
            login_soup = await self.request('POST', sign_in_url, data=inputs)

        # check for choice mfa
        # https://www.amazon.de/ap/mfa/new-otp
        while check_for_choice_mfa(login_soup):
            inputs = get_inputs_from_soup(login_soup)
            for node in login_soup.\
                    select('div[data-a-input-name=otpDeviceContext]'):
                # auth-TOTP, auth-SMS, auth-VOICE
                if 'auth-TOTP' in node['class']:
                    inp_node = node.find('input')
                    inputs[inp_node['name']] = inp_node['value']
    
            login_soup = await self.request(
                'POST', base_url + '/ap/mfa', data=inputs)
    
        # check for mfa (otp_code)
        while check_for_mfa(login_soup):
            otp_code = self._otp_callback()
            inputs = get_inputs_from_soup(login_soup)
            inputs['otpCode'] = otp_code
            inputs['mfaSubmit'] = 'Submit'
            inputs['rememberDevice'] = 'false'

            login_soup = await self.request('POST', sign_in_url, data=inputs)
    
        # check for cvf
        while check_for_cvf(login_soup):
            inputs = get_inputs_from_soup(login_soup)

            login_soup = await self.request('POST', cvf_url, data=inputs)

            inputs = get_inputs_from_soup(login_soup)
            inputs['action'] = 'code'
            inputs['code'] = input('Code: ')

            login_soup = await self.request('POST', cvf_url, data=inputs)


@asynchronous
async def authenticate_as_device(username, password, market: 'AudibleMarket',
                                 **options):

    def get_oauth_params(country_code, base_url, market_place_id):
        return {
            'openid.oa2.response_type': 'token',
            'openid.return_to': f'{base_url}/ap/maplanding',
            'openid.assoc_handle': f'amzn_audible_ios_{country_code}',
            'openid.identity': ('http://specs.openid.net/auth/2.0/'
                                'identifier_select'),
            'pageId': 'amzn_audible_ios',
            'accountStatusPolicy': 'P1',
            'openid.claimed_id': ('http://specs.openid.net/auth/2.0/'
                                  'identifier_select'),
            'openid.mode': 'checkid_setup',
            'openid.ns.oa2': 'http://www.amazon.com/ap/ext/oauth/2',
            'openid.oa2.client_id': ('device:6a52316c62706d53427a57355'
                                     '05a76477a45375959566674327959465'
                                     'a6374424a53497069546d45234132435'
                                     'a4a5a474c4b324a4a564d'),
            'openid.ns.pape': 'http://specs.openid.net/extensions/pape/1.0',
            'marketPlaceId': market_place_id,
            'openid.oa2.scope': 'device_auth_access',
            'forceMobileLayout': 'true',
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.pape.max_auth_age': '0'
        }

    def extract_token_from_url(url):
        parsed_url = url.query
        return parsed_url['openid.oa2.access_token']

    async with _BaseLogin(**options) as login:
        base_url = 'https://' + market.amazon_url
        oauth_params = get_oauth_params(
            country_code=market.country_code,
            base_url=base_url,
            market_place_id=market.market_place_id
        )
        
        await login.login(username, password, base_url, oauth_params)

        response_url = login.last_response[0].url
        access_token = extract_token_from_url(response_url)
        expires = (datetime.utcnow() + timedelta(seconds=3600)).timestamp()
        # login_cookies = extract_cookies_from_session(login._session, base_url)
        
    return {
        'access_token': access_token,
        'expires': expires,
        'cookies': login._session.cookie_jar
    }


@asynchronous
async def authenticate_as_software_player(username, password,
                                          market: 'AudibleMarket', **options):
    """
    Authenticate for player auth token (needed to retrieve activation bytes)
    """
    def get_oauth_params(country_code, audible_base_url, player_id):
        return {
            'openid.ns': 'http://specs.openid.net/auth/2.0',
            'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
            'openid.mode': 'logout',
            'openid.assoc_handle': 'amzn_audible_' + country_code,
            'openid.return_to': audible_base_url + ('/player-auth-token?playerType=software&playerId=%s=&bp_ua=y&'
                                                    'playerModel=Desktop&playerManufacturer=Audible' % player_id)
        }

    def extract_token_from_url(url):
        parsed_url = url.query
        return parsed_url['playerToken']

    def get_player_id():
        player_id = base64.encodebytes(hashlib.sha1(b'').digest()).rstrip()
        return player_id.decode('ascii')

    async with _BaseLogin(**options) as login:
        base_url = 'https://' + market.amazon_url
        audible_base_url = 'https://' + market.url
        player_id = get_player_id()

        oauth_params = get_oauth_params(
            country_code=market.country_code,
            audible_base_url=audible_base_url,
            player_id=player_id
        )

        await login.request(
            'GET',
            audible_base_url + '/',
            params={'ipRedirectOverride': 'true'}
        )
        
        await login.login(username, password, base_url, oauth_params)

        await login.request(
            'GET',
            audible_base_url + ('/player-auth-token?playerType=software&bp_ua=y&playerModel=Desktop&playerId=%s&'
                                'playerManufacturer=Audible&serial=' % player_id)
        )

        response_url = login.last_response[0].url
        player_token = extract_token_from_url(response_url)
        # login_cookies = extract_cookies_from_session(login._session, base_url)

    return player_token
