import os
import time
import threading
import queue
import re
from collections import deque
from datetime import datetime

import cv2
import numpy as np
from PIL import Image

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import get_color, image_size, limit_in, save_image
from module.device.method.adb import Adb
from module.device.method.ascreencap import AScreenCap
from module.device.method.droidcast import DroidCast
from module.device.method.ldopengl import LDOpenGL
from module.device.method.nemu_ipc import NemuIpc
from module.device.method.scrcpy import Scrcpy
from module.device.method.wsa import WSA
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger


class Screenshot(Adb, WSA, DroidCast, AScreenCap, Scrcpy, NemuIpc, LDOpenGL):
    _screen_size_checked = False
    _screen_black_checked = False
    _minicap_uninstalled = False
    _screenshot_interval = Timer(0.1)
    _last_save_time = {}
    image: np.ndarray
    
    # Async archiving
    _archive_queue = None
    _archive_thread = None
    _archive_thread_started = False

    @cached_property
    def screenshot_methods(self):
        return {
            "ADB": self.screenshot_adb,
            "ADB_nc": self.screenshot_adb_nc,
            "uiautomator2": self.screenshot_uiautomator2,
            "aScreenCap": self.screenshot_ascreencap,
            "aScreenCap_nc": self.screenshot_ascreencap_nc,
            "DroidCast": self.screenshot_droidcast,
            "DroidCast_raw": self.screenshot_droidcast_raw,
            "scrcpy": self.screenshot_scrcpy,
            "nemu_ipc": self.screenshot_nemu_ipc,
            "ldopengl": self.screenshot_ldopengl,
        }

    @cached_property
    def screenshot_method_override(self) -> str:
        return ""

    def screenshot(self):
        """
        Returns:
            np.ndarray:
        """
        self._screenshot_interval.wait()
        self._screenshot_interval.reset()

        for attempt in range(10):
            if self.screenshot_method_override:
                method = self.screenshot_method_override
            else:
                method = self.config.Emulator_ScreenshotMethod
            method = self.screenshot_methods.get(method, self.screenshot_adb)
            self.image = method()

            if self.config.Emulator_ScreenshotDedithering:
                if attempt == 0:
                    cv2.fastNlMeansDenoising(self.image, self.image, h=17, templateWindowSize=1, searchWindowSize=2)
            self.image = self._handle_orientated_image(self.image)

            if self.config.Error_SaveError:
                self.screenshot_deque.append({"time": datetime.now(), "image": self.image})

            if self.check_screen_size() and self.check_screen_black():
                break
            else:
                if attempt < 9:
                    wait_time = min(0.5 * (2 ** attempt), 5.0)
                    logger.warning(f"Screenshot retry {attempt + 1}/10, waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                continue

        return self.image

    @property
    def has_cached_image(self):
        return hasattr(self, "image") and self.image is not None

    def _handle_orientated_image(self, image):
        """
        Args:
            image (np.ndarray):

        Returns:
            np.ndarray:
        """
        width, height = image_size(self.image)
        if width == 1280 and height == 720:
            return image

        # Rotate screenshots only when they're not 1280x720
        if self.orientation == 0:
            pass
        elif self.orientation == 1:
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif self.orientation == 2:
            image = cv2.rotate(image, cv2.ROTATE_180)
        elif self.orientation == 3:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        else:
            raise ScriptError(f"Invalid device orientation: {self.orientation}")

        return image

    @cached_property
    def screenshot_deque(self):
        try:
            length = int(self.config.Error_ScreenshotLength)
        except ValueError:
            logger.error(f"Error_ScreenshotLength={self.config.Error_ScreenshotLength} is not an integer")
            raise RequestHumanTakeover
        # Limit in 1~300
        length = max(1, min(length, 300))
        return deque(maxlen=length)

    def _start_archive_thread(self):
        """Start the background thread for async screenshot archiving"""
        if not self._archive_thread_started:
            self._archive_queue = queue.Queue()
            self._archive_thread = threading.Thread(target=self._archive_worker, daemon=True)
            self._archive_thread.start()
            self._archive_thread_started = True
            logger.info("Started screenshot archive background thread")
    
    def _archive_worker(self):
        """Background thread that saves screenshots without blocking main thread"""
        while True:
            try:
                data = self._archive_queue.get(timeout=1)
                if data is None:  # Shutdown signal
                    break
                
                image, file_path = data
                save_image(image, file_path)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.warning(f"Archive worker error: {e}")
    
    def archive_action_screenshot(self, action_name="unknown", button_name=""):
        """
        Archives the current screenshot before an action is taken.
        This is useful for debugging and understanding the bot's behavior.
        Saves to 'log/action_archive/<date>/<action_name>/<timestamp>_<button>.png'.
        
        Uses async I/O to avoid blocking the main thread.

        Args:
            action_name (str): Name of the action being taken, e.g. 'click', 'swipe'.
            button_name (str): Name of the button or element being interacted with.
        """
        # Ensure we have an image to save
        if not hasattr(self, 'image') or self.image is None:
            return
        
        # Start archive thread if needed
        if not self._archive_thread_started:
            self._start_archive_thread()

        now = time.time()
        timestamp = datetime.fromtimestamp(now).strftime("%Y%m%d_%H%M%S_%f")[:-3]
        date_folder = datetime.fromtimestamp(now).strftime("%Y-%m-%d")
        
        # Robust filename sanitization - remove all invalid Windows filename characters
        button_clean = re.sub(r'[<>:"|?*\\/]', '_', str(button_name))
        button_clean = button_clean.replace(' ', '_')[:50]  # Limit length
        
        if button_clean:
            file = f"{timestamp}_{button_clean}.png"
        else:
            file = f"{timestamp}.png"

        try:
            # Create folder structure
            folder = os.path.join("./log/action_archive", date_folder, action_name)
            os.makedirs(folder, exist_ok=True)
            
            file_path = os.path.join(folder, file)
            
            # Queue for async save - returns immediately
            self._archive_queue.put((self.image.copy(), file_path))
            
        except Exception as e:
            logger.warning(f"Failed to queue screenshot for archiving: {e}")

    def save_screenshot(self, genre="items", interval=None, to_base_folder=False):
        """Save a screenshot. Use millisecond timestamp as file name.

        Args:
            genre (str, optional): Screenshot type.
            interval (int, float): Seconds between two save. Saves in the interval will be dropped.
            to_base_folder (bool): If save to base folder.

        Returns:
            bool: True if save succeed.
        """
        now = time.time()
        if interval is None:
            # Default interval of 2 seconds if not specified
            interval = 2

        if now - self._last_save_time.get(genre, 0) > interval:
            fmt = "png"
            file = f"{int(now * 1000)}.{fmt}"

            # Use DropRecord_SaveFolder as the base folder
            folder = self.config.DropRecord_SaveFolder
            if to_base_folder:
                # Create a 'base' subdirectory for base folder screenshots
                folder = os.path.join(folder, 'base')
            folder = os.path.join(folder, genre)
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)

            file = os.path.join(folder, file)
            self.image_save(file)
            self._last_save_time[genre] = now
            return True
        return False

    def screenshot_last_save_time_reset(self, genre):
        self._last_save_time[genre] = 0

    def screenshot_interval_set(self, interval=None):
        """
        Args:
            interval (int, float, str):
                Minimum interval between 2 screenshots in seconds.
                Or None for Optimization_ScreenshotInterval, 'combat' for Optimization_CombatScreenshotInterval
        """
        if interval is None:
            origin = self.config.Optimization_ScreenshotInterval
            interval = limit_in(origin, 0.1, 0.3)
            if interval != origin:
                logger.warning(f"Optimization.ScreenshotInterval {origin} is revised to {interval}")
                self.config.Optimization_ScreenshotInterval = interval
            # Allow nemu_ipc to have a lower default
            if self.config.Emulator_ScreenshotMethod in ["nemu_ipc", "ldopengl"]:
                interval = limit_in(origin, 0.1, 0.2)
        elif interval == "combat":
            origin = self.config.Optimization_CombatScreenshotInterval
            interval = limit_in(origin, 0.3, 1.0)
            if interval != origin:
                logger.warning(f"Optimization.CombatScreenshotInterval {origin} is revised to {interval}")
                self.config.Optimization_CombatScreenshotInterval = interval
        elif isinstance(interval, int | float):
            # No limitation for manual set in code
            pass
        else:
            logger.warning(f"Unknown screenshot interval: {interval}")
            raise ScriptError(f"Unknown screenshot interval: {interval}")
        # Screenshot interval in scrcpy is meaningless,
        # video stream is received continuously no matter you use it or not.
        if self.config.Emulator_ScreenshotMethod == "scrcpy":
            interval = 0.1

        if interval != self._screenshot_interval.limit:
            logger.info(f"Screenshot interval set to {interval}s")
            self._screenshot_interval.limit = interval

    def image_show(self, image=None):
        if image is None:
            image = self.image
        Image.fromarray(image).show()

    def image_save(self, file=None):
        if file is None:
            file = f"{int(time.time() * 1000)}.png"
        save_image(self.image, file)

    def check_screen_size(self):
        """
        Screen size must be 1280x720.
        Take a screenshot before call.
        """
        if self._screen_size_checked:
            return True

        orientated = False
        for _ in range(2):
            # Check screen size
            width, height = image_size(self.image)
            logger.attr("Screen_size", f"{width}x{height}")
            if width == 1280 and height == 720:
                self._screen_size_checked = True
                return True
            elif not orientated and (width == 720 and height == 1280):
                logger.info("Received orientated screenshot, handling")
                self.get_orientation()
                self.image = self._handle_orientated_image(self.image)
                orientated = True
                width, height = image_size(self.image)
                if width == 720 and height == 1280:
                    logger.info("Unable to handle orientated screenshot, continue for now")
                    return True
                else:
                    continue
            elif self.config.Emulator_Serial == "wsa-0":
                self.display_resize_wsa(0)
                return False
            elif hasattr(self, "app_is_running") and not self.app_is_running():
                logger.warning("Received orientated screenshot, game not running")
                return True
            else:
                logger.critical(f"Resolution not supported: {width}x{height}")
                logger.critical("Please set emulator resolution to 1280x720")
                raise RequestHumanTakeover

    def check_screen_black(self):
        if self._screen_black_checked:
            return True
        # Check screen color
        # May get a pure black screenshot on some emulators.
        color = get_color(self.image, area=(0, 0, 1280, 720))
        if sum(color) < 1:
            if self.config.Emulator_Serial == "wsa-0":
                for _ in range(2):
                    display = self.get_display_id()
                    if display == 0:
                        return True
                logger.info(f"Game running on display {display}")
                logger.warning("Game not running on display 0, will be restarted")
                self.app_stop_uiautomator2()
                return False
            elif self.config.Emulator_ScreenshotMethod == "uiautomator2":
                logger.warning(f"Received pure black screenshots from emulator, color: {color}")
                logger.warning("Uninstall minicap and retry")
                self.uninstall_minicap()
                self._screen_black_checked = False
                return False
            else:
                logger.warning(f"Received pure black screenshots from emulator, color: {color}")
                logger.warning(
                    f"Screenshot method `{self.config.Emulator_ScreenshotMethod}` "
                    f"may not work on emulator `{self.serial}`, or the emulator is not fully started"
                )
                logger.warning(f"Consider trying alternative screenshot methods: {list(self.screenshot_methods.keys())}")
                if self.is_mumu_family:
                    if self.config.Emulator_ScreenshotMethod == "DroidCast":
                        self.droidcast_stop()
                    else:
                        logger.warning("If you are using MuMu X, please upgrade to version >= 12.1.5.0")
                self._screen_black_checked = False
                return False
        else:
            self._screen_black_checked = True
            return True
