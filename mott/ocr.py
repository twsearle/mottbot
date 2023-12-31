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


class OCRInvalidURLError(MottException):
    def __init__(self, URI, message=""):
        if message == "":
            self.message = f"Invalid image URL: {URI}"
        else:
            self.message = message
        super().__init__(self.message)


class OCRaUECNotFoundError(MottException):
    def __init__(self, contents, message=""):
        if message == "":
            self.message = f"OCR: aUEC not found in image contents"
        else:
            self.message = message
        logger_discord.debug(f"Failed to detect aUEC in image contents: '{contents}'")
        super().__init__(self.message)


class OCRNumberNotFoundError(MottException):
    def __init__(self, number_string, message=""):
        if message == "":
            self.message = f"OCR: number not found in image contents"
        else:
            self.message = message
        logger_discord.debug(f"Failed to detect a number of aUEC in: '{number_string}'")
        super().__init__(self.message)


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
        self.setup()

    def setup(self):
        if uri_validator(self.uri):
            validation = True
            try:
                validation = validators.url(self.uri)
            except validators.utils.ValidationError:
                raise OCRInvalidURLError(self.uri)
            if not validation:
                raise OCRInvalidURLError(self.uri)

            r = requests.get(self.uri, stream=True)
            if r.status_code != 200:
                raise MottException(
                    f"Failed to read: {uri} requests status_code: {r.status_code}"
                )
            self.image = Image.open(io.BytesIO(r.content))

            # async with aiohttp.ClientSession() as session:
            #    async with session.get(self.uri) as r:
            #        if r.status != 200:
            #            raise MottException(
            #                f"Failed to read: {self.uri} status_code: {r.status_code}"
            #            )
            #        req_contents = await r.contents()
            #        self.image = Image.open(io.BytesIO(req_contents))
        else:
            self.image = Image.open(self.uri)

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
            raise OCRaUECNotFoundError(contents)
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
            raise OCRNumberNotFoundError(contents)
        return value

    def image_to_auec(self) -> float:
        logger_discord.info(f' processing image URI: "{self.uri}"')
        self.image = convert_image_format(self.image, output_format="PNG")
        self.image = self.image.convert("RGB")
        self.image = ImageOps.invert(self.image)
        self.image = ImageOps.autocontrast(self.image, cutoff=(0, 95))
        contents = pytesseract.image_to_string(self.image, config=r"--psm 4")
        return self.auec_value(contents)
