import time
from datetime import timedelta
from typing import TYPE_CHECKING

import module.config.server as server
from module.base.button import Button
from module.base.decorator import cached_property
from module.base.utils import *
from module.logger import logger
from module.ocr.rpc import ModelProxyFactory
from module.webui.setting import State

if TYPE_CHECKING:
    from module.ocr.al_ocr import AlOcr

if not State.deploy_config.UseOcrServer:
    from module.ocr.models import OCR_MODEL
else:
    OCR_MODEL = ModelProxyFactory()


class Ocr:
    SHOW_LOG = True
    SHOW_REVISE_WARNING = False

    def __init__(self, buttons, letter=(255, 255, 255), threshold=128, alphabet=None, name=None):
        """
        Args:
            buttons (Button, tuple, list[Button], list[tuple]): OCR area.
            letter (tuple(int)): Letter RGB.
            threshold (int):
            alphabet: Alphabet white list.
            name (str):
        """
        self.name = str(buttons) if isinstance(buttons, Button) else name
        self._buttons = buttons
        self.letter = letter
        self.threshold = threshold
        self.alphabet = alphabet

    @property
    def buttons(self):
        buttons = self._buttons
        buttons = buttons if isinstance(buttons, list) else [buttons]
        buttons = [button.area if isinstance(button, Button) else button for button in buttons]
        return buttons

    @buttons.setter
    def buttons(self, value):
        self._buttons = value

    def pre_process(self, image):
        """
        Args:
            image (np.ndarray): Shape (height, width, channel)

        Returns:
            np.ndarray: Shape (width, height)
        """
        image = extract_letters(image, letter=self.letter, threshold=self.threshold)

        return image.astype(np.uint8)

    def after_process(self, result):
        """
        Args:
            result (str): '第二行'

        Returns:
            str:
        """
        return result

    def ocr(self, image, direct_ocr=False):
        """
        Args:
            image (np.ndarray, list[np.ndarray]):
            direct_ocr (bool): True to skip preprocess.

        Returns:
            str, list[str]:
        """
        if image is None:
            return '' if not isinstance(self._buttons, list) or len(self._buttons) <= 1 else []

        image_list = image if isinstance(image, list) else [image]
        if not image_list:
            return []

        result_list = []
        try:
            # Pre-process
            if not direct_ocr:
                image_list = [self.pre_process(img) for img in image_list]

            # OCR
            if self.alphabet:
                raw_results = OCR_MODEL.atomic_ocr_for_single_lines(image_list, alphabet=self.alphabet)
                result_list = ["".join(res) for res in raw_results]
            else:
                result_list = OCR_MODEL.ocr_for_single_lines(image_list)

            # Post-process
            result_list = [self.after_process(res) for res in result_list]

            if self.SHOW_LOG:
                for res, button in zip(result_list, self.buttons):
                    logger.info(f'OCR {self.name}@{button}: {res}')

        except Exception as e:
            logger.exception(e)
            # Return empty results matching the expected output shape
            result_list = ['' for _ in image_list]

        # Return single result if single image was passed
        if len(self.buttons) == 1 and isinstance(image, np.ndarray):
            return result_list[0]
        else:
            return result_list


class Digit(Ocr):
    pass


class DigitCounter(Digit):
    pass


class OcrYuv(Ocr):
    """Base class for YUV-based OCR (deprecated)"""

    pass


class DigitYuv(Digit, OcrYuv):
    pass


class DigitCounterYuv(DigitCounter, OcrYuv):
    pass


class Duration(Ocr):
    def __init__(self, buttons, letter=(255, 255, 255), threshold=128, alphabet="0123456789:IDSB", name=None):
        super().__init__(buttons, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace("I", "1").replace("D", "0").replace("S", "5")
        result = result.replace("B", "8")
        return result

    def ocr(self, image, direct_ocr=False):
        """
        Do OCR on a duration, such as `01:30:00`.

        Args:
            image:
            direct_ocr:

        Returns:
            list, datetime.timedelta: timedelta object, or a list of it.
        """
        result_list = super().ocr(image, direct_ocr=direct_ocr)
        if not isinstance(result_list, list):
            result_list = [result_list]
        result_list = [self.parse_time(result) for result in result_list]
        if len(self.buttons) == 1:
            result_list = result_list[0]
        return result_list

    @staticmethod
    def parse_time(string):
        """
        Args:
            string (str): `01:30:00`

        Returns:
            datetime.timedelta:
        """
        result = re.search(r"(\d{1,2}):?(\d{2}):?(\d{2})", string)
        if result:
            result = [int(s) for s in result.groups()]
            return timedelta(hours=result[0], minutes=result[1], seconds=result[2])
        else:
            logger.warning(f"Invalid duration: {string}")
            return timedelta(hours=0, minutes=0, seconds=0)


class DurationYuv(Duration, OcrYuv):
    pass
