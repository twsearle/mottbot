import PIL
import rembg
import pytesseract

from mott.exceptions import MottException


class OCR:
    def image_to_auec(image) -> float:
        out_image = rembg.remove(image)
        contents = pytesseract.image_to_string(out_image)
        print(contents)
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
