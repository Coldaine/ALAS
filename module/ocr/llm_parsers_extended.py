"""
Extended LLM parsers for additional OCR parsing scenarios in ALAS
"""
import re
from typing import Optional
from module.ocr.llm_bridge import LLMParser
from module.logger import logger


class GuildProgressParser(LLMParser):
    """Parse guild operations progress to XX/YY format"""
    
    def get_prompt(self) -> str:
        return """You are parsing guild operation progress from the Azur Lane guild screen.

Input: Raw OCR text showing current progress vs maximum.
Common OCR errors: Slash may be '|', '\\', '1', or have spaces. Numbers may be misread.

Required output format: CURRENT/MAXIMUM (no spaces)
- CURRENT: Integer 0-999
- MAXIMUM: Integer, typically 60, 80, 100, 120, 150, 200

Validation rules:
- Current cannot exceed maximum
- Maximum values are fixed mission targets
- Common maximums: 60, 80, 100, 120, 150, 200

Examples:
"75/100" → "75/100"
"45 | 60" → "45/60"
"120\\150" → "120/150"
"80 1 100" → "80/100"

Return ONLY the formatted progress string."""

    def validate_output(self, output: str) -> bool:
        pattern = r'^(\d+)/(\d+)$'
        match = re.match(pattern, output)
        
        if not match:
            return False
            
        current, maximum = map(int, match.groups())
        
        # Common maximum values
        valid_maximums = [60, 80, 100, 120, 150, 200]
        
        return current <= maximum and maximum in valid_maximums
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        text = raw_text.replace('|', '/').replace('\\', '/').replace(' ', '')
        text = text.replace('l', '1').replace('I', '1')
        
        pattern = r'(\d+)/(\d+)'
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
            
        return None
        
    def _get_default_value(self) -> Optional[str]:
        return None


class SOSChapterParser(LLMParser):
    """Parse SOS chapter numbers"""
    
    def get_prompt(self) -> str:
        return """You are parsing an SOS chapter number from the Azur Lane SOS signal list.

Input: Raw OCR text of a chapter number.
Common OCR errors: 'I' as '1', 'O' as '0', 'S' as '5', 'B' as '8', partial visibility.

Required output format: Integer 3-10 (as string)
- Range: 3 to 10 only

Validation rules:
- SOS chapters only exist for chapters 3-10
- No SOS for chapters 1, 2, 11+
- Single digit (3-9) or exactly 10

Examples:
"S" → "5"
"I0" → "10"
"B" → "8"
"3" → "3"

Return ONLY the chapter number as a string."""

    def validate_output(self, output: str) -> bool:
        if not output.isdigit():
            return False
            
        chapter = int(output)
        return 3 <= chapter <= 10
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        text = raw_text.strip().upper()
        
        # Common OCR substitutions
        text = text.replace('S', '5').replace('I', '1').replace('O', '0').replace('B', '8')
        
        # Extract first number
        match = re.search(r'(\d+)', text)
        if match:
            num = int(match.group(1))
            if 3 <= num <= 10:
                return str(num)
                
        return None
        
    def _get_default_value(self) -> Optional[str]:
        return None


class RaidCounterParser(LLMParser):
    """Parse raid attempt counter to X/3 format"""
    
    def get_prompt(self) -> str:
        return """You are parsing raid attempt counter from the Azur Lane raid interface.

Input: Raw OCR text showing remaining attempts vs maximum.
Common OCR errors: Slash variations, color-affected misreads.

Required output format: CURRENT/MAXIMUM
- CURRENT: Integer 0-3
- MAXIMUM: Always 3 for raids

Validation rules:
- Maximum is always 3 for raid attempts
- Current ranges from 0 to 3
- Format is always X/3

Examples:
"3/3" → "3/3"
"1|3" → "1/3"
"0 / 3" → "0/3"
"2\\3" → "2/3"

Return ONLY the formatted counter string."""

    def validate_output(self, output: str) -> bool:
        pattern = r'^([0-3])/3$'
        return bool(re.match(pattern, output))
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        text = raw_text.replace('|', '/').replace('\\', '/').replace(' ', '')
        
        # Look for X/3 pattern
        match = re.search(r'([0-3])/3', text)
        if match:
            return match.group(0)
            
        # Look for just a single digit with 3
        match = re.search(r'([0-3])\D*3', text)
        if match:
            return f"{match.group(1)}/3"
            
        return None
        
    def _get_default_value(self) -> Optional[str]:
        return "3/3"  # Safe default - assume full attempts


class ResearchDurationParser(LLMParser):
    """Parse research duration to HH:MM:SS format"""
    
    def get_prompt(self) -> str:
        return """You are parsing time remaining for active research in Azur Lane.

Input: Raw OCR text of time remaining.
Common OCR errors: Colons as dots/semicolons, may include "d" for days, "h" for hours.

Required output format: HH:MM:SS (even if days present)
- Convert any day values to hours
- HH: 00-99 (can exceed 24 for multi-day research)
- MM: 00-59
- SS: 00-59

Validation rules:
- Research can take 0:30:00 to 48:00:00
- If days present, convert to hours (1d = 24h)
- Common durations: 0:30, 1:00, 1:30, 2:00, 2:30, 3:00, 4:00, 5:00, 6:00, 8:00, 12:00

Examples:
"23:45:30" → "23:45:30"
"1d 2h" → "26:00:00"
"5.30.00" → "05:30:00"
"12;00;00" → "12:00:00"

Return ONLY the formatted time string."""

    def validate_output(self, output: str) -> bool:
        pattern = r'^(\d{1,2}):([0-5][0-9]):([0-5][0-9])$'
        match = re.match(pattern, output)
        
        if not match:
            return False
            
        hours = int(match.group(1))
        # Research can be up to 48 hours
        return hours <= 48
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        text = raw_text.lower()
        
        # Handle day/hour format
        day_match = re.search(r'(\d+)d', text)
        hour_match = re.search(r'(\d+)h', text)
        
        if day_match or hour_match:
            total_hours = 0
            if day_match:
                total_hours += int(day_match.group(1)) * 24
            if hour_match:
                total_hours += int(hour_match.group(1))
            return f"{total_hours:02d}:00:00"
            
        # Handle standard time format
        text = text.replace('.', ':').replace(';', ':').replace(' ', ':')
        pattern = r'(\d{1,2}):(\d{1,2}):(\d{1,2})'
        match = re.search(pattern, text)
        
        if match:
            h, m, s = map(int, match.groups())
            return f"{h:02d}:{m:02d}:{s:02d}"
            
        return None
        
    def _get_default_value(self) -> Optional[str]:
        return None


class BattleStatusEnemyParser(LLMParser):
    """Parse enemy fleet names with character removal"""
    
    def get_prompt(self) -> str:
        return """You are parsing an enemy fleet name from the Azur Lane battle status screen.

Input: Raw OCR text of enemy fleet type (may be in Chinese/Japanese).
Common OCR errors: Partial character recognition, extra symbols.

Required output: Clean fleet name with specific characters removed
Remove these characters: - 一 个 ― ~ (

Common fleet types:
- 小型偵察艦隊 (small reconnaissance fleet)
- 中型主力舰队 (medium main fleet)
- 大型主力艦隊 (large main fleet)
- 精锐舰队 (elite fleet)
- 輸送艦隊 (transport fleet)

Examples:
"中型-主力舰队" → "中型主力舰队"
"~小型偵察艦隊" → "小型偵察艦隊"
"精锐舰队一个" → "精锐舰队"

Return ONLY the cleaned fleet name."""

    def validate_output(self, output: str) -> bool:
        # Check that forbidden characters are removed
        forbidden = ['-', '一', '个', '―', '~', '(']
        return not any(char in output for char in forbidden)
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        # Remove specific characters
        text = raw_text
        for char in ['-', '一', '个', '―', '~', '(']:
            text = text.replace(char, '')
            
        return text.strip() if text.strip() else None
        
    def _get_default_value(self) -> Optional[str]:
        return None


class FurniturePriceParser(LLMParser):
    """Parse furniture prices to integer format"""
    
    def get_prompt(self) -> str:
        return """You are parsing furniture price from the Azur Lane dorm shop.

Input: Raw OCR text of furniture cost in coins.
Common OCR errors: Currency symbols, commas, decimals, partial digits.

Required output format: Pure integer (no symbols or formatting)
- Range: 20 to 5000 typically

Validation rules:
- Common prices: 40, 80, 100, 150, 200, 300, 500, 700, 1000, 1200, 1500
- Always whole numbers
- No furniture costs more than 5000
- Minimum price is 20

Examples:
"$500" → "500"
"1,200" → "1200"
"I50" → "150"
"3OO" → "300"

Return ONLY the integer price as a string."""

    def validate_output(self, output: str) -> bool:
        if not output.isdigit():
            return False
            
        price = int(output)
        return 20 <= price <= 5000
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        # Remove common formatting
        text = re.sub(r'[$,.]', '', raw_text)
        text = text.replace('O', '0').replace('I', '1').replace('l', '1')
        
        # Extract digits
        match = re.search(r'\d+', text)
        if match:
            price = int(match.group(0))
            if 20 <= price <= 5000:
                return str(price)
                
        return None
        
    def _get_default_value(self) -> Optional[str]:
        return None


class MinigameScoreParser(LLMParser):
    """Parse minigame scores to integer format"""
    
    def get_prompt(self) -> str:
        return """You are parsing a score from the Azur Lane New Year minigame.

Input: Raw OCR text of battle score.
Common OCR errors: Commas, special effects obscuring digits, decimals.

Required output format: Pure integer (no formatting)
- Range: 0 to 99999

Validation rules:
- Scores are always whole numbers
- Typical range: 5000-30000
- High scores may reach 50000+

Examples:
"12,500" → "12500"
"25.000" → "25000"
"I8750" → "18750"
"7,5OO" → "7500"

Return ONLY the integer score as a string."""

    def validate_output(self, output: str) -> bool:
        if not output.isdigit():
            return False
            
        score = int(output)
        return 0 <= score <= 99999
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        # Remove formatting
        text = re.sub(r'[,.]', '', raw_text)
        text = text.replace('O', '0').replace('I', '1').replace('l', '1')
        
        # Extract digits
        match = re.search(r'\d+', text)
        if match:
            return match.group(0)
            
        return None
        
    def _get_default_value(self) -> Optional[str]:
        return "0"


class DataKeyCounterParser(LLMParser):
    """Parse data key counter to X/5 format"""
    
    def get_prompt(self) -> str:
        return """You are parsing data key counter from the Azur Lane interface.

Input: Raw OCR text showing available data keys.
Common OCR errors: Missing maximum, slash variations, single number only.

Required output format: CURRENT/MAXIMUM
- CURRENT: Integer 0-5
- MAXIMUM: Always 5

Validation rules:
- Maximum is always 5 for data keys
- Current ranges from 0 to 5
- If only one number visible, assume it's current with max 5

Examples:
"3/5" → "3/5"
"2" → "2/5"
"0|5" → "0/5"
"4 / 5" → "4/5"

Return ONLY the formatted counter string."""

    def validate_output(self, output: str) -> bool:
        pattern = r'^([0-5])/5$'
        return bool(re.match(pattern, output))
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        text = raw_text.replace('|', '/').replace('\\', '/').replace(' ', '')
        
        # Look for X/5 pattern
        match = re.search(r'([0-5])/5', text)
        if match:
            return match.group(0)
            
        # Single digit - assume it's current count
        match = re.search(r'^([0-5])$', text.strip())
        if match:
            return f"{match.group(1)}/5"
            
        return None
        
    def _get_default_value(self) -> Optional[str]:
        return "0/5"


class ShipLevelParser(LLMParser):
    """Parse ship levels for awakening"""
    
    def get_prompt(self) -> str:
        return """You are parsing a ship level from the Azur Lane awakening interface.

Input: Raw OCR text of ship level.
Common OCR errors: 'I' as '1', 'O' as '0', 'l' as '1'.

Required output format: Integer level (as string)
- Range: 1 to 125

Validation rules:
- Maximum level is 125
- Awakening available at levels: 10, 30, 70, 100
- Common levels: 70, 80, 90, 100, 105, 110, 115, 120, 125

Examples:
"I00" → "100"
"12O" → "120"
"ll0" → "110"
"7O" → "70"

Return ONLY the level as a string."""

    def validate_output(self, output: str) -> bool:
        if not output.isdigit():
            return False
            
        level = int(output)
        return 1 <= level <= 125
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        # Fix common OCR errors
        text = raw_text.replace('I', '1').replace('O', '0').replace('l', '1')
        
        # Extract digits
        match = re.search(r'\d+', text)
        if match:
            level = int(match.group(0))
            if 1 <= level <= 125:
                return str(level)
                
        return None
        
    def _get_default_value(self) -> Optional[str]:
        return None


# Update factory function
def get_parser(parser_type: str, provider: str = "auto") -> Optional[LLMParser]:
    """Get appropriate parser instance for given type"""
    parsers = {
        # Original parsers
        "commission_duration": CommissionDurationParser,
        "dorm_food": DormFoodCounterParser,
        "research_code": ResearchProjectCodeParser,
        "stage_name": StageNameParser,
        "shop_price": ShopPriceParser,
        "fleet_power": FleetPowerParser,
        
        # Extended parsers
        "guild_progress": GuildProgressParser,
        "sos_chapter": SOSChapterParser,
        "raid_counter": RaidCounterParser,
        "research_duration": ResearchDurationParser,
        "battle_enemy": BattleStatusEnemyParser,
        "furniture_price": FurniturePriceParser,
        "minigame_score": MinigameScoreParser,
        "data_key": DataKeyCounterParser,
        "ship_level": ShipLevelParser,
    }
    
    parser_class = parsers.get(parser_type)
    if parser_class:
        return parser_class(provider=provider)
        
    logger.warning(f"Unknown parser type: {parser_type}")
    return None