from ..utils import asynchronous
from ..session import AsyncAuthSession


@asynchronous
async def get_download_link(market, auth_handler, asin,
                            codec="LC_128_44100_stereo"):
    content_url = (
        "https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/FSDownloadContent"
    )

    params = {
        'type': 'AUDI',
        'currentTransportMethod': 'WIFI',
        'key': asin,
        'codec': codec
    }

    async with AsyncAuthSession(auth=auth_handler) as session:
        async with session.get(
                url=content_url,
                params=params,
                allow_redirects=False
                ) as resp:
            link = resp.headers['Location']

    prep_link = link.replace("cds.audible.com", f"cds.audible.{market.tld}")

    return prep_link

