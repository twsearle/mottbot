import logging
from logging import StreamHandler

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)

from mott.exceptions import MottException
from mott.ocr import (
    OCR,
    OCRInvalidURLError,
    OCRaUECNotFoundError,
    OCRNumberNotFoundError,
    uri_validator,
)
import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def test_ocr():
    return await OCR.create("tests/data/bigmotradertest.jpeg")


class TestOCR:
    @pytest.mark.asyncio
    async def test_ocr_local(self, test_ocr):
        auec = await test_ocr.image_to_auec()
        assert auec == 820000

    @pytest.mark.asyncio
    async def test_ocr_url(self):
        url = "https://en.wikipedia.org/wiki/Test_card#/media/File:SMPTE_Color_Bars.svg"
        assert uri_validator(url)
        with pytest.raises(OCRInvalidURLError):
            _ = await OCR.create(url)

        url = "https://robertsspaceindustries.com/media/fupjr98kisd1fr/store_slideshow_large/BatCave_4k_v02.jpg"
        with pytest.raises(OCRaUECNotFoundError):
            ocr_obj = await OCR.create(url)
            auec = await ocr_obj.image_to_auec()

        url = "https://github.com/twsearle/mottbot/blob/main/tests/data/bigmotradertest.jpeg?raw=true"
        ocr_obj = await OCR.create(url)
        auec = await ocr_obj.image_to_auec()
        assert auec == 820000

    @pytest.mark.asyncio
    async def test_contains_auec(self, test_ocr):
        contents_throw = [" pounds", " notauec", "654jauec"]
        for c in contents_throw:
            with pytest.raises(OCRaUECNotFoundError):
                test_ocr.contains_auec(c)

        contents_and_number_end = {
            "9,999 aUEC": 5,
            "9,999  aUEC": 6,
            "9,999 aVEC": 5,
            "9,999 auec": 5,
            "9,999 avec": 5,
        }
        for k, v in contents_and_number_end.items():
            assert test_ocr.contains_auec(k) == v

    @pytest.mark.asyncio
    async def test_auec_value(self, test_ocr):
        contents_throw = ["  aUEC", "abv avec"]
        for c in contents_throw:
            with pytest.raises(OCRNumberNotFoundError):
                test_ocr.auec_value(c)

        contents_and_value = {
            "999 aUEC": 999,
            "9,999 aUEC": 9999,
            "junk9,999,999 aUECjunk": 9999999,
            " 1,999,999 aUEC": 1999999,
            "\t9,199,999 aUEC": 9199999,
            "\n9,919,999 aUEC": 9919999,
        }
        for k, v in contents_and_value.items():
            assert test_ocr.auec_value(k) == v
