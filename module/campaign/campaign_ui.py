from module.base.timer import Timer
from module.campaign.assets import *
from module.campaign.campaign_event import CampaignEvent
from module.campaign.campaign_ocr import CampaignOcr
from module.exception import CampaignEnd, CampaignNameError, ScriptEnd
from module.logger import logger
from module.map.assets import WITHDRAW
from module.map.map_operation import MapOperation
from module.ui.assets import CAMPAIGN_CHECK
from module.ui.switch import Switch


class ModeSwitch(Switch):
    def handle_additional(self, main):
        if main.appear(WITHDRAW, offset=(30, 30)):
            logger.warning(f"ModeSwitch: WITHDRAW appears")
            raise CampaignNameError


MODE_SWITCH_1 = ModeSwitch("Mode_switch_1", offset=(30, 10))
MODE_SWITCH_1.add_state("normal", SWITCH_1_NORMAL)
MODE_SWITCH_1.add_state("hard", SWITCH_1_HARD)
MODE_SWITCH_2 = ModeSwitch("Mode_switch_2", offset=(30, 10))
MODE_SWITCH_2.add_state("hard", SWITCH_2_HARD)
MODE_SWITCH_2.add_state("ex", SWITCH_2_EX)

# Event mode switches changing from 20240725 to 20241219
# I think it stable at 20241219, so give them names with date 20241219
MODE_SWITCH_20241219 = ModeSwitch("Mode_switch_20241219", is_selector=True, offset=(30, 30))
MODE_SWITCH_20241219.add_state("combat", SWITCH_20241219_COMBAT)
MODE_SWITCH_20241219.add_state("story", SWITCH_20241219_STORY)
ASIDE_SWITCH_20241219 = ModeSwitch("Aside_switch_20241219", is_selector=True, offset=(30, 30))
ASIDE_SWITCH_20241219.add_state("part1", CHAPTER_20241219_PART1)
ASIDE_SWITCH_20241219.add_state("part2", CHAPTER_20241219_PART2)
ASIDE_SWITCH_20241219.add_state("sp", CHAPTER_20241219_SP)
ASIDE_SWITCH_20241219.add_state("ex", CHAPTER_20241219_EX)


def is_digit_chapter(chapter):
    """
    Args:
         chapter (int, str): Chapter. Such as 7, 'd', 'sp'.

    Returns:
        bool:
    """
    if isinstance(chapter, int):
        return True
    try:
        return chapter[0].isdigit()
    except IndexError:
        return False


class CampaignUI(MapOperation, CampaignEvent, CampaignOcr):
    ENTRANCE = Button(area=(), color=(), button=(), name="default_button")

    def campaign_ensure_chapter(self, chapter, skip_first_screenshot=True):
        """
        Args:
            chapter (int, str): Chapter. Such as 7, 'd', 'sp'.
            skip_first_screenshot:
        """
        index = self._campaign_get_chapter_index(chapter)
        isdigit = is_digit_chapter(chapter)

        # A copy of use ui_ensure_index.
        logger.hr("UI ensure index")
        retry = Timer(1, count=2)
        error_confirm = Timer(0.2, count=0)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_chapter_additional():
                continue

            current = self.get_chapter_index()
            current_isdigit = is_digit_chapter(self.campaign_chapter)

            logger.attr("Index", current)
            diff = index - current
            if diff == 0:
                break

            # Getting 3-7 when looking for D3
            if not (isdigit == current_isdigit):
                continue

            # 14-4 may be OCR as 4-1 due to slow animation, confirm if it is 4-1
            if index >= 11 and index % 10 == current:
                error_confirm.start()
                if not error_confirm.reached():
                    continue
            else:
                error_confirm.reset()

            # Switch
            if retry.reached():
                button = CHAPTER_NEXT if diff > 0 else CHAPTER_PREV
                self.device.multi_click(button, n=abs(diff), interval=(0.2, 0.3))
                retry.reset()

    def handle_chapter_additional(self):
        """
        Called in campaign_ensure_chapter()

        Returns:
            bool: True if handled
        """
        return False

    def campaign_ensure_mode(self, mode="normal"):
        """
        Args:
            mode (str): 'normal', 'hard', 'ex'
        """
        if mode == "hard":
            self.config.override(Campaign_Mode="hard")

        switch_2 = MODE_SWITCH_2.get(main=self)

        if switch_2 == "unknown":
            if mode == "ex":
                logger.warning("Trying to goto EX, but no EX mode switch")
            elif mode == "normal":
                MODE_SWITCH_1.set("hard", main=self)
            elif mode == "hard":
                MODE_SWITCH_1.set("normal", main=self)
            else:
                logger.warning(f"Unknown campaign mode: {mode}")
        else:
            if mode == "ex":
                MODE_SWITCH_2.set("hard", main=self)
            elif mode == "normal":
                MODE_SWITCH_2.set("ex", main=self)
                MODE_SWITCH_1.set("hard", main=self)
            elif mode == "hard":
                MODE_SWITCH_2.set("ex", main=self)
                MODE_SWITCH_1.set("normal", main=self)
            else:
                logger.warning(f"Unknown campaign mode: {mode}")

    def campaign_ensure_mode_20241219(self, mode="combat"):
        """
        Args:
            mode (str): 'combat' or 'story'
        """
        if mode in ["normal", "hard", "ex", "combat"]:
            MODE_SWITCH_20241219.set("combat", main=self)
        elif mode in ["story"]:
            MODE_SWITCH_20241219.set("story", main=self)
        else:
            logger.warning(f"Unknown campaign mode: {mode}")

    def campaign_ensure_aside_20241219(self, chapter):
        """
        Args:
            chapter: 'part1', 'part2', 'sp', 'ex'
        """
        if chapter in ["part1", "a", "c", "t"]:
            ASIDE_SWITCH_20241219.set("part1", main=self)
        elif chapter in ["part2", "b", "d"]:
            ASIDE_SWITCH_20241219.set("part2", main=self)
        elif chapter in ["sp", "ex_sp"]:
            ASIDE_SWITCH_20241219.set("sp", main=self)
        elif chapter in ["ex", "ex_ex"]:
            ASIDE_SWITCH_20241219.set("ex", main=self)
        else:
            logger.warning(f"Unknown campaign aside: {chapter}")

    def campaign_get_mode_names(self, name):
        """
        Get stage names in both 'normal' and 'hard'
        t1 -> [t1, ht1]
        ht1 -> [t1, ht1]
        a1 -> [a1, c1]

        Args:
            name (str):

        Returns:
            list[str]:
        """
        if name.startswith("t"):
            return [f"t{name[1:]}", f"ht{name[1:]}"]
        if name.startswith("ht"):
            return [f"t{name[2:]}", f"ht{name[2:]}"]
        if name.startswith("a") or name.startswith("c"):
            return [f"a{name[1:]}", f"c{name[1:]}"]
        if name.startswith("b") or name.startswith("d"):
            return [f"b{name[1:]}", f"d{name[1:]}"]
        return [name]

    def _campaign_name_is_hard(self, name):
        """
        Reuse manual defination in campaign_get_mode_names()

        Args:
            name: 'a1', 'ht1', 'sp1'

        Returns:
            bool: If stage is hard mode
        """
        mode_names = self.campaign_get_mode_names(name)
        if len(mode_names) == 2 and mode_names[1] == name:
            return True
        else:
            return False

    def campaign_get_entrance(self, name):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.

        Returns:
            Button:
        """
        entrance_name = name
        if self.config.MAP_HAS_MODE_SWITCH:
            for mode_name in self.campaign_get_mode_names(name):
                if mode_name in self.stage_entrance:
                    name = mode_name

        if name not in self.stage_entrance:
            logger.warning(f"Stage not found: {name}")
            raise CampaignNameError

        entrance = self.stage_entrance[name]
        entrance.name = entrance_name
        return entrance

    def campaign_set_chapter_main(self, chapter, mode="normal"):
        if chapter.isdigit():
            self.ui_goto_campaign()
            self.campaign_ensure_mode("normal")
            self.campaign_ensure_chapter(chapter)
            if mode == "hard":
                self.campaign_ensure_mode("hard")
                # info_bar shows: Hard mode for this map is not available yet.
                # There's also a game bug in EN, HM12 shows not available but it's actually available.
                self.handle_info_bar()
                self.campaign_ensure_chapter(chapter)
            return True
        else:
            return False

    def campaign_set_chapter_event(self, chapter, mode="normal"):
        if chapter in ["a", "b", "c", "d", "ex_sp", "as", "bs", "cs", "ds", "t", "ts", "tss", "ht", "hts"]:
            self.ui_goto_event()
            if chapter in ["a", "b", "as", "bs", "t", "ts", "tss"]:
                self.campaign_ensure_mode("normal")
            elif chapter in ["c", "d", "cs", "ds", "ht", "hts"]:
                self.campaign_ensure_mode("hard")
            elif chapter == "ex_sp":
                self.campaign_ensure_mode("ex")
            self.campaign_ensure_chapter(chapter)
            return True
        else:
            return False

    def campaign_set_chapter_sp(self, chapter, mode="normal"):
        if chapter == "sp":
            self.ui_goto_sp()
            self.campaign_ensure_chapter(chapter)
            return True
        else:
            return False

    def campaign_set_chapter_20241219(self, chapter, stage, mode="combat"):
        if self.config.MAP_CHAPTER_SWITCH_20241219:
            if self._campaign_name_is_hard(f"{chapter}{stage}"):
                self.config.override(Campaign_Mode="hard")
            # part1, part2, sp, ex
            if mode == "story":
                self.campaign_ensure_mode_20241219("story")
                return True
            if chapter in ["a", "c", "t"]:
                self.ui_goto_event()
                self.campaign_ensure_mode_20241219("combat")
                self.campaign_ensure_aside_20241219("part1")
                self.campaign_ensure_chapter(chapter)
                return True
            if chapter in ["b", "d", "ttl"]:
                self.ui_goto_event()
                self.campaign_ensure_mode_20241219("combat")
                self.campaign_ensure_aside_20241219("part2")
                self.campaign_ensure_chapter(chapter)
                return True
            if chapter in ["ex_sp"]:
                self.ui_goto_event()
                self.campaign_ensure_mode_20241219("combat")
                self.campaign_ensure_aside_20241219("sp")
                self.campaign_ensure_chapter(chapter)
                return True
            if chapter in ["ex_ex"]:
                self.ui_goto_event()
                self.campaign_ensure_mode_20241219("combat")
                self.campaign_ensure_aside_20241219("ex")
                self.campaign_ensure_chapter(chapter)
                return True
        if self.config.MAP_CHAPTER_SWITCH_20241219_SP:
            if self._campaign_name_is_hard(f"{chapter}{stage}"):
                self.config.override(Campaign_Mode="hard")
            # (empty), normal, sp, (empty)
            if chapter in ["sp", "t", "ht"]:
                self.ui_goto_event()
                self.campaign_ensure_mode_20241219("combat")
                # normal is on the position of part2
                self.campaign_ensure_aside_20241219("part2")
                self.campaign_ensure_chapter(chapter)
                return True
            if chapter in ["ex_sp"]:
                self.ui_goto_event()
                self.campaign_ensure_mode_20241219("combat")
                self.campaign_ensure_aside_20241219("sp")
                self.campaign_ensure_chapter(chapter)
                return True
        return False

    def campaign_set_chapter(self, name, mode="normal"):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, stage = self._campaign_separate_name(name)

        if self.campaign_set_chapter_main(chapter, mode):
            pass
        elif self.campaign_set_chapter_20241219(chapter, stage, mode):
            pass
        elif self.campaign_set_chapter_event(chapter, mode):
            pass
        elif self.campaign_set_chapter_sp(chapter, mode):
            pass
        else:
            logger.warning(f"Unknown campaign chapter: {name}")

    def handle_campaign_ui_additional(self):
        """
        Returns:
            bool: If handled
        """
        if self.appear(WITHDRAW, offset=(30, 30)):
            # logger.info("WITHDRAW button found, wait until map loaded to prevent bugs in game client")
            self.ensure_no_info_bar(timeout=2)
            try:
                self.withdraw()
            except CampaignEnd:
                pass
            return True
        return False

    def ensure_campaign_ui(self, name, mode="normal", skip_first_screenshot=True):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
            skip_first_screenshot:

        Raises:
            ScriptEnd: If failed to switch after retries
        """
        timeout = Timer(5, count=20).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                break
            try:
                self.campaign_set_chapter(name, mode)
                self.ENTRANCE = self.campaign_get_entrance(name=name)
                return True
            except CampaignNameError:
                pass

            if self.handle_campaign_ui_additional():
                continue

        logger.warning("Campaign name error")
        raise ScriptEnd("Campaign name error")

    def commission_notice_show_at_campaign(self):
        """
        Returns:
            bool: If any commission finished.
        """
        return self.appear(CAMPAIGN_CHECK, offset=(20, 20)) and self.appear(COMMISSION_NOTICE_AT_CAMPAIGN)
