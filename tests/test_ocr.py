import PIL

from mott.ocr import OCR


def test_ocr():
    input_path = "tests/data/bigmotradertest.jpeg"
    in_image = PIL.Image.open(input_path)
    auec = OCR.image_to_auec(in_image)
    assert auec == 820000
