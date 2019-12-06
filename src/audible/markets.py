import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from .api import AudibleAPI
from .session import async_request


logger = logging.getLogger(__name__)


AUDIBLE_MARKETS = {
    'germany': {
        'country_code': 'de',
        'tld': 'de',
        'market_place_id': 'AN7V1F1VY261K'
    },
    'united_states': {
        'country_code': 'us',
        'tld': 'com',
        'market_place_id': 'AF2M0KC94RCEA',
    },
    'united_kingdom': {
        'country_code': 'uk',
        'tld': 'co.uk',
        'market_place_id': 'A2I9A3Q2GNFNGQ'
    },
    'france': {
        'country_code': 'fr',
        'tld': 'fr',
        'market_place_id': 'A2728XDNODOQ8T'
    },
    'canada': {
        'country_code': 'ca',
        'tld': 'ca',
        'market_place_id': 'A2CQZ5RBY40XE'
    },
    'italy': {
        'country_code': 'it',
        'tld': 'it',
        'market_place_id': 'A2N7FU2W2BU2ZC'
    },
    'australia': {
        'country_code': 'au',
        'tld': 'com.au',
        'market_place_id': 'AN7EY7DTAW63G'
    },
    'india': {
        'country_code': 'in',
        'tld': 'in',
        'market_place_id': 'AJO3FBRUE6J4S'
    },
    'japan': {
        'country_code': 'jp',
        'tld': 'co.jp',
        'market_place_id': 'A1QAP3MOU4173J'
    }
}


def search_market_template(key: str, value: Any):
    for locale in AUDIBLE_MARKETS.values():
        if locale[key] == value:
            return locale
    msg = f'No template found for {key}: {value}'
    logger.warning(msg)
    raise Exception(msg)


def autodetect_market(tld: str) -> Dict[str, str]:
    """
    FOR INTERNAL USE ONLY
    Try to automatically detect correct settings for store.

    Needs the top level domain of the audible page to continue with
    (e.g. co.uk, it) and returns results found.

    """
    site = f'https://www.audible.{tld}/'
    params = {
        'ipRedirectOverride': 'true',
        'overrideBaseCountry': 'true'
    }

    site_text = async_request('GET', url=site, params=params)

    soup = BeautifulSoup(site_text, 'html.parser')
    login_link = soup.find('a', class_='ui-it-sign-in-link')['href']
    query_from_link = urlparse(login_link).query

    parsed_query = parse_qs(query_from_link)
    market_place_id = parsed_query['marketPlaceId'][0]
    country_code = parsed_query['pageId'][0].split('_')[-1]

    return {
        'country_code': country_code,
        'tld': tld,
        'market_place_id': market_place_id
    }


class AudibleMarket:
    """Represents a audible marketplace."""
    def __init__(self,
                 country_code: Optional[str] = None,
                 tld: Optional[str] = None
                 ) -> None:

        if (country_code and tld):
            raise Exception(
                'Only country_code or tld allowed not both.')

        if (country_code is None and tld is None):
            raise Exception(
                'You must provide a country_code or tld.')

        if country_code:
            market = search_market_template('country_code', country_code)
        else:
            market = search_market_template('tld', tld)

        self._country_code = market['country_code']
        self._tld = market['tld']
        self._market_place_id = market['market_place_id']

        self._website = None

    def __repr__(self):
        return f'Audible Market: {self.url}'

    @property
    def country_code(self) -> str:
        return self._country_code

    @property
    def tld(self) -> str:
        return self._tld

    @property
    def market_place_id(self) -> str:
        return self._market_place_id

    @property
    def website_content(self):
        if self._website is None:
            params = {
                'ipRedirectOverride': 'true',
                'overrideBaseCountry': 'true'
            }
            website = async_request(
                'GET', f'https://{self.url}/', params=params)
            self._website = BeautifulSoup(website, 'html.parser')

        return self._website

    @property
    def url(self):
        return f'www.audible.{self.tld}'

    @property
    def api_url(self):
        return f'api.audible.{self.tld}'

    @property
    def amazon_url(self):
        return f'www.amazon.{self.tld}'

    @property
    def title(self):
        return self.website_content.title.text

    @property
    def language(self):
        return self.website_content.html['lang']

    @property
    def infos(self):
        infos = self.website_content.find(
            'script', type='application/ld+json')
        return json.loads(infos.text)

    '''def get_api(self, auth, **kwargs):
        return AudibleAPI(auth, api_url=self.api_url, **kwargs)

    def authenticate(self, username, password, **options):
        return authenticate_as_device(username, password, self, **options)

    def authenticate_as_player(self, username, password, **options):
        return authenticate_as_software_player(username, password, self, **options)'''
