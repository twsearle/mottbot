import itertools
import logging
from PIL import Image, ImageOps
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


def convert_image_format(image, output_format=None):
    new_image = image
    if output_format and (image.format != output_format):
        image_bytes = io.BytesIO()
        image.save(image_bytes, output_format)
        new_image = Image.open(image_bytes)
    return new_image


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
            self.image = Image.open(io.BytesIO(r.content))
        else:
            self.image = Image.open(URI)

    def contains_auec(self, contents) -> int:
        auec_variants = []
        for auec in [" auec", " avec", " auvec", " avuec"]:
            auec_variants += map(
                "".join, itertools.product(*zip(auec.upper(), auec.lower()))
            )

        number_end = -1
        for auec_str in auec_variants:
            number_end = contents.find(auec_str)
            if number_end >= 0:
                break
        if number_end < 0:
            logger_discord.debug(
                f"Failed to detect aUEC in image contents: '{contents}'"
            )
            raise MottException(f"OCR failure: aUEC not found in image contents")
        return number_end

    def auec_value(self, contents):
        number_end = self.contains_auec(contents)

        number_string = ""
        for c in contents[number_end::-1].strip():
            if c.isspace() or c.isalpha() and c != ",":
                break
            elif c != ",":
                number_string += c
        try:
            value = int(number_string[::-1])
        except ValueError:
            logger_discord.debug(
                f"Failed to detect a number of aUEC in image contents: '{contents}'"
            )
            raise MottException(f"OCR failure: number not found in image contents")
        return value

    def image_to_auec(self) -> float:
        logger_discord.info(f' processing image URI: "{self.uri}"')
        self.image = convert_image_format(self.image, output_format="PNG")
        self.image = self.image.convert("RGB")
        self.image = ImageOps.invert(self.image)
        self.image = ImageOps.autocontrast(self.image, cutoff=(0, 95))
        contents = pytesseract.image_to_string(self.image)
        return self.auec_value(contents)
