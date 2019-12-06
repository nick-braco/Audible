import binascii
import pathlib

from ..session import AsyncAuthSession
from ..utils import asynchronous


def extract_activation_bytes(data):
    if (b'BAD_LOGIN' in data or b'Whoops' in data) or \
            b'group_id' not in data:
        print(data)
        print('\nActivation failed! ;(')
        raise ValueError('data wrong')
    a = data.rfind(b'group_id')
    b = data[a:].find(b')')
    keys = data[a + b + 1 + 1:]
    output = []
    output_keys = []
    # each key is of 70 bytes
    for i in range(0, 8):
        key = keys[i * 70 + i:(i + 1) * 70 + i]
        h = binascii.hexlify(bytes(key))
        h = [h[i:i+2] for i in range(0, len(h), 2)]
        h = b','.join(h)
        output_keys.append(h)
        output.append(h.decode('utf-8'))

    # only 4 bytes of output_keys[0] are necessary for decryption! ;)
    activation_bytes = output_keys[0].replace(b',', b'')[0:8]
    # get the endianness right (reverse string in pairs of 2)
    activation_bytes = b"".join(reversed([activation_bytes[i:i+2] for i in
                                         range(0, len(activation_bytes), 2)]))
    activation_bytes = activation_bytes.decode('ascii')

    return activation_bytes, output


@asynchronous
async def fetch_activation_bytes(player_token, filename=None):

    base_url_license = 'https://www.audible.com'
    rurl = base_url_license + '/license/licenseForCustomerToken'
    # register params
    params = {
        'customer_token': player_token
    }
    # deregister params
    dparams = {
        'customer_token': player_token,
        'action': 'de-register'
    }

    headers = {
        'User-Agent': 'Audible Download Manager'
    }

    async with AsyncAuthSession(headers=headers) as session:
        async with session.get(rurl, params=dparams) as resp:
            await resp.read()

        async with session.get(rurl, params=params) as resp:
            register_response_content = await resp.read()

        if filename:
            pathlib.Path(filename).write_bytes(register_response_content)
    
        activation_bytes, _ = extract_activation_bytes(register_response_content)
        print('activation_bytes: ' + activation_bytes)
    
        async with session.get(rurl, params=dparams) as resp:
            await resp.read()
    
        return activation_bytes

