from mott.exceptions import MottException
from mott.ocr import OCR
import pytest


def test_ocr_local():
    input_uri = "tests/data/bigmotradertest.jpeg"
    auec = OCR(input_uri).image_to_auec()
    assert auec == 820000


def test_ocr_url():
    url = "https://en.wikipedia.org/wiki/Test_card#/media/File:SMPTE_Color_Bars.svg"
    with pytest.raises(MottException):
        auec = OCR(url).image_to_auec()
    url = "https://github.com/twsearle/mottbot/blob/main/tests/data/bigmotradertest.jpeg?raw=true"

    auec = OCR(url).image_to_auec()
    assert auec == 820000
