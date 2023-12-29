import logging
import PIL
import rembg
import pytesseract
import validators
import requests
import io

logger_discord = logging.getLogger("discord")

from mott.exceptions import MottException
from urllib.parse import urlparse


def uri_validator(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])
    except:
        return False


class OCR:
    def __init__(self, URI):
        self.uri = URI
        if uri_validator(URI):
            validation = validators.url(URI)
            if not validation:
                raise MottException(f"Invalid image URL: {URI}")
            r = requests.get(URI, stream=True)
            if r.status_code != 200:
                raise MottException(
                    f"Failed to read: {URI} requests status_code: {r.status_code}"
                )
            self.image = PIL.Image.open(io.BytesIO(r.content))
        else:
            self.image = PIL.Image.open(URI)

    def image_to_auec(self) -> float:
        logger_discord.info(f' processing image URI: "{self.uri}"')
        out_image = rembg.remove(self.image)
        contents = pytesseract.image_to_string(out_image)
        number_end = contents.find("aUEC") - 1
        if number_end < 0:
            raise MottException(f"Failed to detect aUEC in '{contents}'")
        number_string = ""
        for c in contents[number_end::-1].strip():
            if c.isspace() or c.isalpha() and c != ",":
                break
            elif c != ",":
                number_string += c

        auec_value = float(number_string[::-1])
        return auec_value
