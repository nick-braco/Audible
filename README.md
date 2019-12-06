
# AudibleAPI

[![image](https://img.shields.io/pypi/v/audible.svg)](https://pypi.org/project/audible/)
[![image](https://img.shields.io/pypi/l/audible.svg)](https://pypi.org/project/audible/)
[![image](https://img.shields.io/pypi/pyversions/audible.svg)](https://pypi.org/project/audible/)
[![image](https://img.shields.io/pypi/status/audible.svg)](https://pypi.org/project/audible/)
[![image](https://img.shields.io/pypi/wheel/audible.svg)](https://pypi.org/project/audible/)
[![Travis](https://img.shields.io/travis/mkb79/audible/master.svg?logo=travis)](https://travis-ci.org/mkb79/audible)
[![image](https://img.shields.io/pypi/implementation/audible.svg)](https://pypi.org/project/audible/)
[![image](https://img.shields.io/pypi/dm/audible.svg)](https://pypi.org/project/audible/)

**THIS BRANCH IS FOR INTERNAL USE ONLY. IT CONTAINS UNFINISHED CODE (V0.3.0 PRE-ALPHA)AND README IS NOT UP-TO-DATE**

**(A)Sync Interface for internal Audible API written in pure Python.**

Code and README based on omarroth‘s fantastic [audible.cr](https://github.com/omarroth/audible.cr) API written in crystal.
This package is wrote with Pythonista (iOS).

*With v0.3.0a0  I rewrote this package. The usage has changed completely. This README is for the new version only. Please take care of this.*

## Requirements

This package needs **Python 3.6 or above** and has the following dependencies:

- aiohttp
- beautifulsoup4
- pbkdf2
- Pillow
- pyaes
- requests
- rsa 

## Installation

For the latest version on PyPI (v0.2.1):

```bash
pip install audible
```

For the latest version on github (v0.3.0a0):

```bash
pip install git+https://github.com/mkb79/Audible#egg=audible
```

## Other Implementations

- [audible.cr](https://github.com/omarroth/audible.cr) (Crystal)
- [AudibleApi](https://github.com/rmcrackan/AudibleApi) (C#)


## Basic Usage

1. Import the audible package

	```python
	import audible
	```

2. Select a audible marketplace

	At this moment audible has 9 different marketplaces. To select the marketplace for _audible.com_:

	```python
	market = audible.AudibleMarket('us')
	```

3. Instantiate a auth handler

	For the first experiments you can use the very limited access  token auth handler. To use them you have to obtain a access token first.

	Obtain a access token currently requires answering a CAPTCHA. By default the captcha will be displayed on screen and a user prompt will be provided to enter the answer. Custom callbacks will be explained further below.

	**Access tokens expires after 60 minutes**

	```python
	access_token = market.getaccesstoken('USERNAME', 'PASSWORD')
	auth = audible.AccessTokenAuth(access_token)
	```

4. Get the api for the selected marketplace and make some api calls

	```python
	api = market.get_api(auth)
	library = api.library()
	library_book = api.library_book('ASIN')
	buy_book = api.buy_book('ASIN', use_credit=True)
	custom_request = api.request('GET', '/wishlist')
	```

5. Close the api connection

	```python
	api.close()
	```


## AudibleMarket

### Informations

At this moment audible has 9 different marketplaces. [Here](https://audible.custhelp.com/app/answers/detail/a_id/7267/~/what-is-an-audible-marketplace-and-which-is-best-for-me%3F "What is an Audible marketplace and which is best for me?") you can find some informations about them.

| Marketplace      | country\_code |
|----------------|----------------|
| Audible.com      |           us           |
| Audible.ca         |           ca           |
| Audible.co.uk    |           uk           |
| Audible.com.au |           au           |
| Audible.fr           |           fr            |
| Audible.de         |           de           |
| Audible.co.jp     |           jp             |
| Audible.it           |           it              |
| Audible.in          |           in             |

### Instantiate a AudibleMarket

You can instantiate a market of your choice with:

```python
market = audible.AudibleMarket('COUNTRY_CODE')
```

### Important methods and property‘s of AudibleMarket

The AudibleMarket instance has the following important methods and property’s:

- `market.market_url`

	Property returns website url for the selected marketplace

- `market.api_url`

	Property returns api url for the selected marketplace

- `market.amazon_url`

	Property returns the amazon url for the selected marketplace

- `market.market_infos`

	Property returns some informations about the selected marketplace

- `market.get_api(auth_handler, **options)`

	Gives a interface to make requests to the remote api for the selected marketplace.

- `market.get_async_api(auth_handler, **options)`

	Gives a interface to make async requests to the remote api for the selected marketplace.

- `market.get_access_token(username, password, **options)`

	Gives a access token to make api requests (via auth handler), retrieve the user profile or to register a device (this gives additional tokens like adp\_token & device\_cert, website cookies, refresh\_token, etc. for extended auth handling)!

- `market.get_player_token(username, password, **options)`

	Gives a player token to fetch activation bytes.


## AuthHandler
TODO: have to be filled out

### Saved data

If you save a session following data will be stored in file:

- login\_cookies
- access\_token
- refresh\_token
- adp\_token
- device\_private\_key
- locale\_code
- store\_authentication\_cookie (*new*)
- device\_info (*new*)
- customer\_info (*new*)
- expires

### Unencrypted Load/Save

Credentials can be saved any time to file like so:

```python
import audible

auth = audible.LoginAuthenticator(...)
auth.to_file("FILENAME", encryption=False)

# Sometime later...
auth = audible.FileAuthenticator("FILENAME")
```

Authenticator sets the filename as the default value when loading from or save to file simply run to overwrite old file
`auth.to_file()`. No filename is needed.

### Encrypted Load/Save

This Client supports file encryption now. The encryption
algorithm used is symmetric AES in cipher-block chaining (CBC) mode. Currently json and bytes style output are supported.
Credentials can be saved any time to encrypted file like so:

```python
import audible

auth = audible.LoginAuthenticator(...)

# save credentials in json style
auth.to_file(
    "FILENAME",
    "PASSWORD",
    encryption="json"
)

# in bytes style
auth.to_file(
    "FILENAME",
    "PASSWORD",
    encryption="bytes"
)

# Sometime later...
# load credentials
# encryption style are autodetected
auth = audible.FileAuthenticator(
    "FILENAME",
    "PASSWORD"
)
```

Authenticator sets the filename, password and encryption style as the default values when loading from or save to file simply run to overwrite old file with same password and encryption style
`auth.to_file()`. No filename is needed.

#### Advanced use of encryption/decryption:

`auth.to_file(..., **kwargs)`

`auth = audible.FileAuthenticator(..., **kwargs)`

Following arguments are possible:

- key\_size (default = 32)
- salt\_marker (default = b"$")
- kdf\_iterations (default = 1000)
- hashmod (default = Crypto.Hash.SHA256)
`key_size` may be 16, 24 or 32. The key is derived via the PBKDF2 key derivation function (KDF) from the password and a random salt of 16 bytes (the AES block size) minus the length of the salt header (see below).
The hash function used by PBKDF2 is SHA256 per default. You can pass a different hash function module via the `hashmod` argument. The module must adhere to the Python API for Cryptographic Hash Functions (PEP 247).
PBKDF2 uses a number of iterations of the hash function to derive the key, which can be set via the `kdf_iterations` keyword argumeent. The default number is 1000 and the maximum 65535.
The header and the salt are written to the first block of the encrypted output (bytes mode) or written as key/value pairs (dict mode). The header consist of the number of KDF iterations encoded as a big-endian word bytes wrapped by `salt_marker` on both sides. With the default value of `salt_marker = b'$'`, the header size is thus 4 and the salt 12 bytes.
The salt marker must be a byte string of 1-6 bytes length.
The last block of the encrypted output is padded with up to 16 bytes, all having the value of the length of the padding.
In json style all values are written as base64 encoded string.

### Remove encryption

To remove encryption from file (or save as new file):

```python
from audible.aescipher import remove_file_encryption

encrypted_file = "FILENAME"
decrypted_file = "FILENAME"
password = "PASSWORD"

remove_file_encryption(
    encrypted_file,
    decrypted_file,
    password
)
```


## AudibleAPI

### Instantiate a API

The AudibleAPI class can be instantiate in different ways.

1. The DIRECT way:

	```python
	api = audible.AudibleAPI(auth_handler, api_url, **options)
	```

2. The way over a AudibleMarket instance:

	```python
	market = audible.AudibleMarket(...)
	api = market.get_api(auth_handler, **options)
	# or async
	api = market.get_async_api(auth_handler, **options)
	```

Following arguments can be given at instantiate:

- `auth_handler` 

	Read the instructions about the auth handlers above.

- `api_url`

	The url for the api of the marketplace you want to request (eg. api.audible.com).

- `is_async`

	If `True` all requests to the api will be async (more informations about async requests see section Asynchron requests). Default is `False`. 

- `version`

	The requested api version. At this moment there are two version, `0.0` and `1.0`. Default is `1.0`. 

- `timeout`

	Set‘s the timeout for a api call. Default is `20`.

### Make requests

Please take a look to the API documentation further below this README for the api endpoints (path), params and body.

To make a request you can use this code:

`api.request(method, path, body=None, **params`

There are some api shortcuts build-in at this moment and more will be added with next releases.

- `api.buy_book(asin, use_credit, **params)`

	Shortcut for
	
	```python
	api.request(
			'POST',
			'/orders',
			body={
					'asin': asin,
					'audiblecreditapplied': use_credit
			},
			**params
	)
	```


- `api.library(**params)`
- `api.library_code(asin, **params)`

### Close the api connection

## CAPTCHA

Logging in currently requires answering a CAPTCHA. By default Pillow is used to show captcha and user prompt will be provided using `input`, which looks like:

```
Answer for CAPTCHA:
```

If Pillow can't display the captcha, the captcha url will be printed.

A custom callback can be provided (for example submitting the CAPTCHA to an external service), like so:

```
def custom_captcha_callback(captcha_url):
    
    # Do some things with the captcha_url ... 
    # maybe you can call webbrowser.open(captcha_url)

    return "My answer for CAPTCHA"

auth = audible.LoginAuthenticator(
    "EMAIL",
    "PASSWORD",
    locale="us",
    captcha_callback=custom_captcha_callback
)
```

## 2FA

If 2-factor-authentication by default is activated a user prompt will be provided using `input`, which looks like:

```
"OTP Code: "
```

A custom callback can be provided, like so:

```
def custom_otp_callback():
    
    # Do some things to insert otp code

    return "My answer for otp code"

auth = audible.LoginAuthenticator(
    "EMAIL",
    "PASSWORD",
    locale="us",
    otp_callback=custom_otp_callback
)
```


## Logging

In preparation of adding logging in near future I add following functions:

```python
import audible

# console logging
audible.set_console_logger("level")

# file logging
audible.set_file_logger("filename", "level")

```

Following levels will be accepted:

- debug
- info
- warn (or warning)
- error
- critical

You can use numeric levels too:

- 10 (debug)
- 20 (info)
- 30 (warn)
- 40 (error)
- 50 (critical)


## Asynchron requests

By default the AudibleAPI client requests are synchron using the requests module.

The client supports asynchronous request using the aiohttp module. You can instantiate a async client with:

```python
import audible
from audible.utils import asynchronous

@asynchronous
async def main():
	market = audible.AudibleMarket(country_code)
	auth = 'your_auth_handler'
	api = market.get_async_api(auth)
	library = await api.library()
	custom_requests = await api.request(...)
	await api.close()

main()
```

Please take attention to the `await`-Statements. If you don’t await the result the Client will give a coro instead of the result. 

The advantage of a async Client are making simultaneous requests. Instead of await a result before proceed to the next step you can schedule the requests and execute them at once. The `gather` method from asyncio delivers the results in a list. You can use `with`-Statement with api too, to avoid unclosed connections. 

For example:

```python
import asyncio

import audible
from audible.utils import asynchronous

@asynchronous
async def main():
	market = audible.AudibleMarket(country_code)
	auth = 'your_auth_handler'
	with market.get_async_api(auth) as api:
		tasks = []
		
		library = asyncio.ensure_future(
			api.library()
		)
		tasks.append(library)
		
		custom_requests = asyncio.ensure_future(
			api.request(...)
		)
		tasks.append(custom_requests)
		
		results = await asyncio.gather(*tasks)

main()
```

One more example without the `gather` method. If you make async requests without a `await`-Statement the requests will be executed in background but don’t block the system. We `await` the results of the requests when they are needed. In this moment it will block the system until the request is completed (if not already done in the background).

```python
import audible
from audible.utils import asynchronous

@asynchronous
async def main():
	market = audible.AudibleMarket(country_code)
	auth = 'your_auth_handler'
	with market.get_async_api(auth) as api:
		
		library = api.library()
		
		... do some other stuff ...
		
		custom_requests = api.request(...)
		
		library = await library
		custom_request = await custom_request

main()
```

## Authentication

### Informations

Clients are authenticated using OpenID. Once a client has successfully authenticated with Amazon, they are given an access token for authenticating with Audible.

### Register device

Clients can be register a device with the given `access_token` from authentication to `/auth/register`. Registration will be done for a specific device serial. After registration Clients obtaining an refresh token, RSA private key, adp\_token, website\_cookies and store\_authentication\_cookie depending on the requested token type. Multiple devices can be registered to a account.

### Signing requests

For requests to the Audible API, requests need to be signed using the provided RSA private key and adp\_token from registration. Request signing is fairly straight-forward and uses a signed SHA256 digest. Headers look like:

```
x-adp-alg: SHA256withRSA:1.0
x-adp-signature: AAAAAAAA...:2019-02-16T00:00:01.000000000Z,
x-adp-token: {enc:...}
```

Instead of signing a request the Client can use a `access_token` and `client-id` for request the Audible API. 

As reference for other implementations, a client **must** store a working `access_token` from a successful Amazon login in order to renew `refresh_token`, `adp_token`, etc from `/auth/register`.

### Refresh access token

An `access_token` can be renewed by making a request to `/auth/token` with a `refresh_token`. `access_token`s are valid for 1 hour.

### Refresh website cookies

Website cookies can be renewed by making a request to `/ap/exchangetoken` with a `refresh_token` for a specific amazon site.

### Deregister device

Refresh token, RSA private key and adp\_token are valid until deregister.

Clients deregister with a valid `access_token` to `/auth/deregister`. The `access_token` must be from the set of registration result for the registered device serial. If the `access_token` is expired in the meantime use a `refresh_token` to renew `access_token`. This deregister all devices with the same device serial such as registrations from other users.

A `access_token` from a fresh authentication can‘t be used for deregister. They are not bound to a specific registration (device serial).

To deregister all devices with Client use `deregister_all_existing_accounts=True` in the request body.
This function is necessary to prevent hanging slots if you registered a device earlier but don‘t store the given credentials.
This also deregister all other devices such as audible apps on mobile devices.


# API Documentation:

There is currently no publicly available documentation about the Audible API. There is a node client ([audible-api](https://github.com/willthefirst/audible/tree/master/node_modules/audible-api)) that has some endpoints documented, but does not provide information on authentication.

Luckily the Audible API is partially self-documenting, however the parameter names need to be known. Error responses will look like:

```json
{
  "message": "1 validation error detected: Value 'some_random_string123' at 'numResults' failed to satisfy constraint: Member must satisfy regular expression pattern: ^\\d+$"
}
```

Few endpoints have been fully documented, as a large amount of functionality is not testable from the app or functionality is unknown. Most calls need to be authenticated.

For `%s` substitutions the value is unknown or can be inferred from the endpoint. `/1.0/catalog/products/%s` for example requires an `asin`, as in `/1.0/catalog/products/B002V02KPU`.

Each bullet below refers to a parameter for the request with the specified method and URL.

Responses will often provide very little info without `response_groups` specified. Multiple response groups can be specified, for example: `/1.0/catalog/products/B002V02KPU?response_groups=product_plan_details,media,review_attrs`. When providing an invalid response group, the server will return an error response but will not provide information on available response groups.

## POST /1.0/orders

- B asin : String
- B audiblecreditapplied : String

Example request body:

```json
{
  "asin": "B002V1CB2Q",
  "audiblecreditapplied": "false"
}
```

- audiblecreditapplied: [true, false]

`audiblecreditapplied` will specify whether to use available credits or default payment method.

## GET /0.0/library/books

**Deprecated: Use `/1.0/library` instead**

params:

- purchaseAfterDate: mm/dd/yyyy
- sortByColumn: [SHORT\_TITLE, strTitle, DOWNLOAD\_STATUS, RUNNING\_TIME, sortPublishDate, SHORT\_AUTHOR, sortPurchDate, DATE\_AVAILABLE]
- sortInAscendingOrder: [true, false]

## GET /1.0/library

params:

- num\_results: \\d+ (max: 1000)
- page: \\d+
- purchased\_after: [RFC3339](https://tools.ietf.org/html/rfc3339) (e.g. `2000-01-01T00:00:00Z`)
- response\_groups: [contributors, media, price, product\_attrs, product\_desc, product\_extended\_attrs, product\_plan\_details, product\_plans, rating, sample, sku, series, reviews, ws4v, origin, relationships, review\_attrs, categories, badge\_types, category\_ladders, claim\_code\_url, is\_downloaded, is\_finished, is\_returnable, origin\_asin, pdf\_url, percent\_complete, provided\_review]
- sort\_by: [-Author, -Length, -Narrator, -PurchaseDate, -Title, Author, Length, Narrator, PurchaseDate, Title]

## GET /1.0/library/%asin

params:

- response\_groups: [contributors, media, price, product\_attrs, product\_desc, product\_extended\_attrs, product\_plan\_details, product\_plans, rating, sample, sku, series, reviews, ws4v, origin, relationships, review\_attrs, categories, badge\_types, category\_ladders, claim\_code\_url, is\_downloaded, is\_finished, is\_returnable, origin\_asin, pdf\_url, percent\_complete, provided\_review]

## POST(?) /1.0/library/item

- asin:

## POST(?) /1.0/library/item/%s/%s

## GET /1.0/wishlist

params:

- num\_results: \\d+ (max: 50)
- page: \\d+
- response\_groups: [contributors, media, price, product\_attrs, product\_desc, product\_extended\_attrs, product\_plan\_details, product\_plans, rating, sample, sku]
- sort\_by: [-Author, -DateAdded, -Price, -Rating, -Title, Author, DateAdded, Price, Rating, Title]

## POST /1.0/wishlist

body:

- asin : String

Example request body:

```json
{
  "asin": "B002V02KPU"
}
```

Returns 201 and a `Location` to the resource.

## DELETE /1.0/wishlist/%asin

Returns 204 and removes the item from the wishlist using the given `asin`.

## GET /1.0/badges/progress

params:

- locale: en\_US
- response\_groups: brag\_message
- store: Audible

## GET /1.0/badges/metadata

params:

- locale: en\_US
- response\_groups: all\_levels\_metadata

## GET /1.0/account/information

params:

- response\_groups: [delinquency\_status, customer\_benefits, subscription\_details\_payment\_instrument, plan\_summary, subscription\_details]
- source: [Enterprise, RodizioFreeBasic, AyceRomance, AllYouCanEat, AmazonEnglish, ComplimentaryOriginalMemberBenefit, Radio, SpecialBenefit, Rodizio]

## POST(?) /1.0/library/collections/%s/channels/%s

- customer\_id:
- marketplace:

## POST(?) /1.0/library/collections/%s/products/%s

- channel\_id:

## GET /1.0/catalog/categories

- categories\_num\_levels: \\d+ (greater than or equal to 1)
- ids: \\d+(,\\d+)\*
- root: [InstitutionsHpMarketing, ChannelsConfigurator, AEReadster, ShortsPrime, ExploreBy, RodizioBuckets, EditorsPicks, ClientContent, RodizioGenres, AmazonEnglishProducts, ShortsSandbox, Genres, Curated, ShortsIntroOutroRemoval, Shorts, RodizioEpisodesAndSeries, ShortsCurated]

## GET /1.0/catalog/categories/%category\_id

- image\_dpi: \\d+
- image\_sizes:
- image\_variants:
- products\_in\_plan\_timestamp:
- products\_not\_in\_plan\_timestamp:
- products\_num\_results: \\d+
- products\_plan: [Enterprise, RodizioFreeBasic, AyceRomance, AllYouCanEat, AmazonEnglish, ComplimentaryOriginalMemberBenefit, Radio, SpecialBenefit, Rodizio]
- products\_sort\_by: [-ReleaseDate, ContentLevel, -Title, AmazonEnglish, AvgRating, BestSellers, -RuntimeLength, ReleaseDate, ProductSiteLaunchDate, -ContentLevel, Title, Relevance, RuntimeLength]
- reviews\_num\_results: \\d+
- reviews\_sort\_by: [MostHelpful, MostRecent]

## POST /1.0/content/%asin/licenserequest

- B consumption\_type: [Streaming, Offline, Download]
- B drm\_type: [Hls, PlayReady, Hds, Adrm]
- B quality: [High, Normal, Extreme, Low]
- B num\_active\_offline\_licenses: \\d+ (max: 10)

Example request body:

```json
{
  "drm_type": "Adrm",
  "consumption_type": "Download",
  "quality": "Extreme"
}
```

For a succesful request, returns JSON body with `content_url`.

## GET /1.0/annotations/lastpositions

- asins: asin (comma-separated), e.g. ?asins=B01LWUJKQ7,B01LWUJKQ7,B01LWUJKQ7

## GET /1.0/content/%asin/metadata

- response\_groups: [chapter\_info]
- acr:

## GET /1.0/customer/information

- response\_groups: [migration\_details, subscription\_details\_rodizio, subscription\_details\_premium, customer\_segment, subscription\_details\_channels]

## GET /1.0/customer/status

- response\_groups: [benefits\_status, member\_giving\_status, prime\_benefits\_status, prospect\_benefits\_status]

## GET /1.0/customer/freetrial/eligibility

## GET /1.0/library/collections

- customer\_id:
- marketplace:

## POST(?) /1.0/library/collections

- collection\_type:

## GET /1.0/library/collections/%s

- customer\_id:
- marketplace:
- page\_size:
- continuation\_token:

## GET /1.0/library/collections/%s/products

- customer\_id:
- marketplace:
- page\_size:
- continuation\_token:
- image\_sizes:

## GET /1.0/stats/aggregates

- daily\_listening\_interval\_duration: ([012]?[0-9])|(30) (0 to 30, inclusive)
- daily\_listening\_interval\_start\_date: YYYY-MM-DD (e.g. `2019-06-16`)
- locale: en\_US
- monthly\_listening\_interval\_duration: 0?[0-9]|1[012] (0 to 12, inclusive)
- monthly\_listening\_interval\_start\_date: YYYY-MM (e.g. `2019-02`)
- response\_groups: [total\_listening\_stats]
- store: [AudibleForInstitutions, Audible, AmazonEnglish, Rodizio]

## GET /1.0/stats/status/finished

- asin: asin

## POST(?) /1.0/stats/status/finished

- start\_date:
- status:
- continuation\_token:

## GET /1.0/pages/%s

%s: ios-app-home

- locale: en-US
- reviews\_num\_results:
- reviews\_sort\_by:
- response\_groups: [media, product\_plans, view, product\_attrs, contributors, product\_desc, sample]

## GET /1.0/catalog/products/%asin

- image\_dpi:
- image\_sizes:
- response\_groups: [contributors, media, product\_attrs, product\_desc, product\_extended\_attrs, product\_plan\_details, product\_plans, rating, review\_attrs, reviews, sample, sku]
- reviews\_num\_results: \\d+ (max: 10)
- reviews\_sort\_by: [MostHelpful, MostRecent]

## GET /1.0/catalog/products/%asin/reviews

- sort\_by: [MostHelpful, MostRecent]
- num\_results: \\d+ (max: 50)
- page: \\d+

## GET /1.0/catalog/products

- author:
- browse\_type:
- category\_id: \\d+(,\\d+)\*
- disjunctive\_category\_ids:
- image\_dpi: \\d+
- image\_sizes:
- in\_plan\_timestamp:
- keywords:
- narrator:
- not\_in\_plan\_timestamp:
- num\_most\_recent:
- num\_results: \\d+ (max: 50)
- page: \\d+
- plan: [Enterprise, RodizioFreeBasic, AyceRomance, AllYouCanEat, AmazonEnglish, ComplimentaryOriginalMemberBenefit, Radio, SpecialBenefit, Rodizio]
- products\_since\_timestamp:
- products\_sort\_by: [-ReleaseDate, ContentLevel, -Title, AmazonEnglish, AvgRating, BestSellers, -RuntimeLength, ReleaseDate, ProductSiteLaunchDate, -ContentLevel, Title, Relevance, RuntimeLength]
- publisher:
- response\_groups: [contributors, media, price, product\_attrs, product\_desc, product\_extended\_attrs, product\_plan\_detail, product\_plans, rating, review\_attrs, reviews, sample, sku]
- reviews\_num\_results: \\d+ (max: 10)
- reviews\_sort\_by: [MostHelpful, MostRecent]
- title:

## GET /1.0/recommendations

- category\_image\_variants:
- image\_dpi:
- image\_sizes:
- in\_plan\_timestamp:
- language:
- not\_in\_plan\_timestamp:
- num\_results: \\d+ (max: 50)
- plan: [Enterprise, RodizioFreeBasic, AyceRomance, AllYouCanEat, AmazonEnglish, ComplimentaryOriginalMemberBenefit, Radio, SpecialBenefit, Rodizio]
- response\_groups: [contributors, media, price, product\_attrs, product\_desc, product\_extended\_attrs, product\_plan\_details, product\_plans, rating, sample, sku]
- reviews\_num\_results: \\d+ (max: 10)
- reviews\_sort\_by: [MostHelpful, MostRecent]

## GET /1.0/catalog/products/%asin/sims

- category\_image\_variants:
- image\_dpi:
- image\_sizes:
- in\_plan\_timestamp:
- language:
- not\_in\_plan\_timestamp:
- num\_results: \\d+ (max: 50)
- plan: [Enterprise, RodizioFreeBasic, AyceRomance, AllYouCanEat, AmazonEnglish, ComplimentaryOriginalMemberBenefit, Radio, SpecialBenefit, Rodizio]
- response\_groups: [contributors, media, price, product\_attrs, product\_desc, product\_extended\_attrs, product\_plans, rating, review\_attrs, reviews, sample, sku]
- reviews\_num\_results: \\d+ (max: 10)
- reviews\_sort\_by: [MostHelpful, MostRecent]
- similarity\_type: [InTheSameSeries, ByTheSameNarrator, RawSimilarities, ByTheSameAuthor, NextInSameSeries]


# Downloading

Downloading books with the 'licenserequest' endpoint of the api gives aaxc files instead of aax files. Aaxc protected files can’t be decoded at the moment. Please take a look at this [issue](https://github.com/mkb79/Audible/issues/3) for more informations. 

To get a download link of a aax protected files on alternate way, you need a **auth handler with adp_token and device_cert**. Here is the code:

```python
import audible
from audible.helpers import get_download_link

market = audible.AudibleMarket('country_code')
auth = your_favourite_auth_handler
link = get_download_link(market, auth, 'asin', optional: codec)
```

For downloading books take a look at this [example](https://github.com/mkb79/Audible/blob/master/examples/download_books_aax.py)

If you don’t have adp_token and device_cert you can use the official Audible Download Manager.

# Activation bytes

Since v0.3.0a0 you can fetch your activation bytes. To get them you need a player token first:

```python
import audible

market = audible.AudibleMarket(country_code)
player_token = market.get_player_token(
	username, password, **custom_callbacks
)
```

With the player token we can fetch the activation bytes

```python
from audible.helpers import fetch_activation_bytes

ab = fetch_activation_bytes(
	player_token,
	filename  # optional: saves activation blob
)
```

Assuming you have your activation bytes, you can convert .aax into another format with the following:

```
$ ffmpeg -activation_bytes 1CEB00DA -i test.aax -vn -c:a copy output.mp4
```
