"""
LLM-based parsers for specific OCR parsing scenarios in ALAS
"""
import re
from typing import Optional, Dict, Any
from module.ocr.llm_bridge import LLMParser
from module.logger import logger


class CommissionDurationParser(LLMParser):
    """Parse commission duration from OCR text to HH:MM:SS format"""
    
    def get_prompt(self) -> str:
        return """You are parsing a commission duration from the Azur Lane game interface.

Input: Raw OCR text representing time remaining for a naval commission.
Common OCR errors: 'I' misread as '1', 'O' as '0', 'S' as '5', 'B' as '8', colons may appear as dots, semicolons, or spaces.

Required output format: HH:MM:SS (24-hour format with leading zeros)
- HH: 00-23 (hours)
- MM: 00-59 (minutes)  
- SS: 00-59 (seconds)

Validation rules:
- Commissions range from 0:15:00 to 12:00:00
- No commission exceeds 24 hours
- If ambiguous, prefer shorter durations

Examples:
"8:3O:OO" → "08:30:00"
"I2.45.30" → "12:45:30"
"2 15 00" → "02:15:00"

Return ONLY the formatted time string."""

    def validate_output(self, output: str) -> bool:
        """Validate HH:MM:SS format with reasonable ranges"""
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])$'
        if not re.match(pattern, output):
            return False
            
        hours, minutes, seconds = map(int, output.split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        
        # Commission time limits: 15 minutes (900s) to 24 hours (86400s)
        return 900 <= total_seconds <= 86400
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        """Try to parse time using common OCR error patterns"""
        # Replace common OCR errors
        text = raw_text.upper()
        text = text.replace('O', '0').replace('I', '1').replace('S', '5').replace('B', '8')
        text = text.replace('.', ':').replace(';', ':').replace(' ', ':')
        
        # Try to extract time pattern
        pattern = r'(\d{1,2}):(\d{1,2}):(\d{1,2})'
        match = re.search(pattern, text)
        
        if match:
            h, m, s = match.groups()
            return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            
        return None
        
    def _get_default_value(self) -> Optional[str]:
        """Return None to indicate parsing failure"""
        return None


class DormFoodCounterParser(LLMParser):
    """Parse dorm food counter from OCR text to XXXX/YYYY format"""
    
    def get_prompt(self) -> str:
        return """You are parsing a food counter from the Azur Lane dorm interface.

Input: Raw OCR text showing current food amount and maximum capacity.
Common OCR errors: Slash may be '|', '\\', or missing entirely. Numbers may be concatenated without separator.

Required output format: CURRENT/MAXIMUM (no spaces, no commas)
- CURRENT: Integer 0-99999
- MAXIMUM: Integer typically 5000-90000 in increments of 1000

Validation rules:
- Current cannot exceed maximum
- Maximum is usually a round number (5000, 10000, 20000, etc.)
- If numbers are concatenated, split at logical boundary

Examples:
"1000/5800" → "1000/5800"
"10005800" → "1000/5800" 
"1500 | 20000" → "1500/20000"
"3250\\40000" → "3250/40000"

Return ONLY the formatted counter string."""

    def validate_output(self, output: str) -> bool:
        """Validate current/maximum format"""
        pattern = r'^(\d+)/(\d+)$'
        match = re.match(pattern, output)
        
        if not match:
            return False
            
        current, maximum = map(int, match.groups())
        
        # Validation rules
        if current > maximum:
            return False
            
        # Maximum should be reasonable (5000-90000)
        if maximum < 5000 or maximum > 90000:
            return False
            
        return True
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        """Try to parse counter using common patterns"""
        text = raw_text.replace('|', '/').replace('\\', '/').replace(' ', '')
        
        # Try standard format
        pattern = r'(\d+)/(\d+)'
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
            
        # Try concatenated numbers (e.g., 10005800)
        if text.isdigit() and len(text) >= 8:
            # Find logical split point (round thousands)
            for i in range(len(text)-4, 3, -1):
                if text[i:] in ['5000', '10000', '20000', '30000', '40000', '50000']:
                    return f"{text[:i]}/{text[i:]}"
                    
        return None
        
    def _get_default_value(self) -> Optional[str]:
        """Return None to indicate parsing failure"""
        return None


class ResearchProjectCodeParser(LLMParser):
    """Parse research project codes to X-NNN-XX format"""
    
    def get_prompt(self) -> str:
        return """You are parsing a research project code from the Azur Lane research lab.

Input: Raw OCR text of a research project identifier.
Common OCR errors: Dashes may be doubled '--', em-dash '–', or missing. Letters/numbers may be misread.

Required output format: X-NNN-XX
- First segment: 1-2 uppercase letters (common: D, G, H, Q, C, E)
- Middle segment: 3-digit number with leading zeros
- Last segment: 2 uppercase letters (common: UL, UR, MI, FP, DR, RF)

Validation rules:
- Always use single hyphen '-' as separator
- Middle segment must be exactly 3 digits
- Known prefixes: D, G, H, Q, C, E
- Known suffixes: UL, UR, MI, FP, DR, RF

Examples:
"D--057--UL" → "D-057-UL"
"G031DR" → "G-031-DR"
"H 142 RF" → "H-142-RF"
"Q004Ml" → "Q-004-MI"

Return ONLY the formatted project code."""

    def validate_output(self, output: str) -> bool:
        """Validate research code format"""
        pattern = r'^[A-Z]{1,2}-\d{3}-[A-Z]{2}$'
        if not re.match(pattern, output):
            return False
            
        prefix, number, suffix = output.split('-')
        
        # Validate known prefixes and suffixes
        known_prefixes = ['D', 'G', 'H', 'Q', 'C', 'E']
        known_suffixes = ['UL', 'UR', 'MI', 'FP', 'DR', 'RF']
        
        return prefix in known_prefixes and suffix in known_suffixes
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        """Try to parse research code using patterns"""
        text = raw_text.upper().replace('--', '-').replace('–', '-').replace(' ', '')
        
        # Fix common OCR errors
        text = text.replace('I', '1').replace('O', '0').replace('ML', 'MI')
        
        # Try to match pattern
        pattern = r'([A-Z]{1,2})[-]?(\d{3})[-]?([A-Z]{2})'
        match = re.search(pattern, text)
        
        if match:
            prefix, number, suffix = match.groups()
            return f"{prefix}-{number}-{suffix}"
            
        return None
        
    def _get_default_value(self) -> Optional[str]:
        """Return None to indicate parsing failure"""
        return None


class StageNameParser(LLMParser):
    """Parse stage names to proper format (N-N, XN, SPN)"""
    
    def get_prompt(self) -> str:
        return """You are parsing a stage name from the Azur Lane campaign map.

Input: Raw OCR text of a stage identifier.
Common OCR errors: Dashes may be doubled, em-dash, or spaces. Letters may be lowercase.

Required output format varies by stage type:
- Normal stages: N-N (chapter-stage, like "7-2", "13-4")
- Hard mode: XN (letter + number, like "D3", "C2")
- Special stages: SPN (like "SP3")
- Event stages: XN or N-N format

Validation rules:
- Normal chapters: 1-14
- Normal stages per chapter: 1-4
- Hard mode uses A, B, C, D (not E+)
- SP stages: SP, SP1, SP2, SP3
- Always use hyphen for normal stages
- No hyphen for letter+number format

Examples:
"7--2" → "7-2"
"sp3" → "SP3"
"D 3" → "D3"
"13—4" → "13-4"

Return ONLY the formatted stage name."""

    def validate_output(self, output: str) -> bool:
        """Validate stage name format"""
        # Normal stage pattern (N-N)
        normal_pattern = r'^([1-9]|1[0-4])-[1-4]$'
        if re.match(normal_pattern, output):
            return True
            
        # Hard mode pattern (XN)
        hard_pattern = r'^[A-D][1-4]$'
        if re.match(hard_pattern, output):
            return True
            
        # Special stage pattern
        sp_pattern = r'^SP[1-3]?$'
        if re.match(sp_pattern, output):
            return True
            
        return False
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        """Try to parse stage name using patterns"""
        text = raw_text.upper().replace('--', '-').replace('—', '-').replace(' ', '')
        
        # Check for special stages first
        if 'SP' in text:
            match = re.search(r'SP(\d?)', text)
            if match:
                return f"SP{match.group(1)}"
                
        # Check for normal stages (N-N)
        normal_match = re.search(r'(\d{1,2})-?(\d)', text)
        if normal_match:
            chapter, stage = normal_match.groups()
            if 1 <= int(chapter) <= 14 and 1 <= int(stage) <= 4:
                return f"{chapter}-{stage}"
                
        # Check for hard mode (XN)
        hard_match = re.search(r'([A-D])(\d)', text)
        if hard_match:
            return f"{hard_match.group(1)}{hard_match.group(2)}"
            
        return None
        
    def _get_default_value(self) -> Optional[str]:
        """Return None to indicate parsing failure"""
        return None


class ShopPriceParser(LLMParser):
    """Parse shop prices to clean integer format"""
    
    def get_prompt(self) -> str:
        return """You are parsing a price from the Azur Lane medal shop.

Input: Raw OCR text of an item price in medals.
Common OCR errors: Commas in numbers, decimal points, 'O' as '0', partial digits.

Required output format: Pure integer (no commas, no decimals)
- Range: 20 to 20000

Validation rules:
- Common prices: 80, 100, 150, 200, 500, 1000, 1500, 2000, 5000, 10000, 15000
- "00" often means "100" (known OCR bug)
- Prices are always whole numbers
- No price below 20 or above 20000

Examples:
"1,500" → "1500"
"00" → "100"
"2.000" → "2000"
"I00" → "100"
"5O0" → "500"

Return ONLY the integer price as a string."""

    def validate_output(self, output: str) -> bool:
        """Validate price is reasonable integer"""
        if not output.isdigit():
            return False
            
        price = int(output)
        return 20 <= price <= 20000
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        """Try to parse price using common patterns"""
        # Handle special case: "00" → "100"
        if raw_text.strip() == "00":
            return "100"
            
        # Clean common OCR errors
        text = raw_text.replace(',', '').replace('.', '').replace('$', '')
        text = text.replace('O', '0').replace('I', '1').replace('l', '1')
        
        # Extract digits
        digits = re.findall(r'\d+', text)
        if digits:
            price = int(digits[0])
            if 20 <= price <= 20000:
                return str(price)
                
        return None
        
    def _get_default_value(self) -> Optional[str]:
        """Return None to indicate parsing failure"""
        return None


class FleetPowerParser(LLMParser):
    """Parse fleet power values to clean integer format"""
    
    def get_prompt(self) -> str:
        return """You are parsing a fleet power value from the Azur Lane exercise opponent screen.

Input: Raw OCR text of a fleet's total power rating.
Common OCR errors: Commas as thousand separators, spaces, 'O' as '0', 'I' as '1'.

Required output format: Pure integer (no commas, no spaces)
- Range: 1000 to 20000 typically

Validation rules:
- Fleet power is always 4-5 digits
- Typical range: 8000-15000
- Never below 1000 or above 20000
- Always a whole number

Examples:
"14,848" → "14848"
"13 477" → "13477"
"I2750" → "12750"
"9.521" → "9521"

Return ONLY the integer power value as a string."""

    def validate_output(self, output: str) -> bool:
        """Validate fleet power is reasonable"""
        if not output.isdigit():
            return False
            
        power = int(output)
        return 1000 <= power <= 20000
        
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        """Try to parse power using common patterns"""
        # Clean common formatting
        text = raw_text.replace(',', '').replace(' ', '').replace('.', '')
        text = text.replace('O', '0').replace('I', '1').replace('l', '1')
        
        # Extract digits
        digits = re.findall(r'\d+', text)
        if digits:
            power = int(digits[0])
            if 1000 <= power <= 20000:
                return str(power)
                
        return None
        
    def _get_default_value(self) -> Optional[str]:
        """Return None to indicate parsing failure"""
        return None


# Factory function to get appropriate parser
def get_parser(parser_type: str, provider: str = "auto") -> Optional[LLMParser]:
    """Get appropriate parser instance for given type"""
    parsers = {
        "commission_duration": CommissionDurationParser,
        "dorm_food": DormFoodCounterParser,
        "research_code": ResearchProjectCodeParser,
        "stage_name": StageNameParser,
        "shop_price": ShopPriceParser,
        "fleet_power": FleetPowerParser,
    }
    
    parser_class = parsers.get(parser_type)
    if parser_class:
        return parser_class(provider=provider)
        
    logger.warning(f"Unknown parser type: {parser_type}")
    return None