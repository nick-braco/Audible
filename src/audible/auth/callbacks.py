import io

import requests
from PIL import Image


def default_captcha_callback(captcha_url: str) -> str:
    """Helper function for handling captcha."""
    # on error print captcha url instead of display captcha
    try:
        captcha = requests.get(captcha_url).content
        f = io.BytesIO(captcha)
        img = Image.open(f)
        img.show()
    except:
        print(captcha_url)

    guess = input('Answer for CAPTCHA: ')
    return str(guess).strip().lower()


def default_otp_callback() -> str:
    """Helper function for handling 2-factor authentication."""
    guess = input('OTP Code: ')
    return str(guess).strip().lower()
