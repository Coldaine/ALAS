"""
Integration examples showing how to use the LLM bridge system in ALAS modules

These examples demonstrate how to modify existing ALAS code to use the LLM parsers
for robust OCR output handling.
"""

# Example 1: Commission Duration Parsing
# Original code location: module/commission/project.py
def commission_parse_with_llm(self, string):
    """
    Enhanced commission parsing with LLM fallback
    
    Original implementation would fail on OCR errors like:
    - "8:3O:OO" (O instead of 0)
    - "I2.45.30" (I instead of 1, dots instead of colons)
    """
    from module.ocr.llm_bridge import parse_ocr_output
    
    # Try LLM parsing
    result = parse_ocr_output(
        raw_text=string,
        parser_type='commission_duration',
        context={'source': 'commission_timer'}
    )
    
    if result:
        # Convert to seconds for internal use
        h, m, s = map(int, result.split(':'))
        return h * 3600 + m * 60 + s
    else:
        # Fallback to original behavior or raise error
        self.logger.warning(f"Failed to parse commission duration: {string}")
        return None


# Example 2: Dorm Food Counter
# Original code location: module/dorm/dorm.py
class OcrDormFoodEnhanced:
    """Enhanced dorm food OCR with LLM parsing"""
    
    def ocr(self, image):
        """Read dorm food counter with LLM enhancement"""
        from module.ocr.llm_bridge import parse_ocr_output
        
        # Get raw OCR result
        raw_text = self._run_ocr(image)
        
        # Parse with LLM
        result = parse_ocr_output(
            raw_text=raw_text,
            parser_type='dorm_food',
            context={'source': 'dorm_food_counter'}
        )
        
        if result:
            # Split into current/total
            current, total = result.split('/')
            return int(current), int(total)
        else:
            self.logger.warning(f"Failed to parse dorm food: {raw_text}")
            return 0, 0


# Example 3: Research Project Name
# Original code location: module/research/project.py
def get_research_name_with_llm(self, image):
    """Get research project name with LLM parsing"""
    from module.ocr.llm_bridge import parse_ocr_output
    
    # Get raw OCR result
    raw_text = self.ocr.ocr(image)[0]
    
    # Parse with LLM
    result = parse_ocr_output(
        raw_text=raw_text,
        parser_type='research_code',
        context={'source': 'research_project'}
    )
    
    if result:
        return result
    else:
        # Fallback behavior
        self.logger.warning(f"Failed to parse research name: {raw_text}")
        return "UNKNOWN"


# Example 4: Stage Name Parsing
# Original code location: module/campaign/campaign_ocr.py
def _campaign_ocr_result_process_enhanced(self, result):
    """Process campaign stage name with LLM parsing"""
    from module.ocr.llm_bridge import parse_ocr_output
    
    if not result:
        return None
        
    # Parse with LLM
    parsed = parse_ocr_output(
        raw_text=result,
        parser_type='stage_name',
        context={'source': 'campaign_stage'}
    )
    
    if parsed:
        return parsed
    else:
        self.logger.warning(f"Failed to parse stage name: {result}")
        return None


# Example 5: Shop Price Parsing
# Original code location: module/shop/shop_medal.py
class ShopPriceOcrEnhanced:
    """Enhanced shop price OCR with LLM parsing"""
    
    def ocr(self, image):
        """Read shop price with LLM enhancement"""
        from module.ocr.llm_bridge import parse_ocr_output
        
        # Get raw OCR result
        raw_text = self._run_ocr(image)
        
        # Parse with LLM
        result = parse_ocr_output(
            raw_text=raw_text,
            parser_type='shop_price',
            context={'source': 'medal_shop_price'}
        )
        
        if result:
            return int(result)
        else:
            # Safe default
            self.logger.warning(f"Failed to parse shop price: {raw_text}")
            return 0


# Example 6: Batch Processing Multiple OCR Fields
def process_battle_stats_with_llm(self, screenshot):
    """Process multiple battle statistics with LLM parsing"""
    from module.ocr.llm_bridge import parse_ocr_output
    
    # Extract OCR regions
    fleet_power_raw = self.ocr_fleet_power(screenshot)
    enemy_name_raw = self.ocr_enemy_name(screenshot)
    
    # Parse all fields with appropriate parsers
    fleet_power = parse_ocr_output(
        raw_text=fleet_power_raw,
        parser_type='fleet_power',
        context={'source': 'exercise_opponent'}
    )
    
    enemy_name = parse_ocr_output(
        raw_text=enemy_name_raw,
        parser_type='battle_enemy',
        context={'source': 'battle_status'}
    )
    
    return {
        'fleet_power': int(fleet_power) if fleet_power else 0,
        'enemy_name': enemy_name or 'Unknown'
    }


# Example 7: Configurable LLM Provider
def parse_with_provider_selection(raw_text, parser_type):
    """Example of using specific LLM provider"""
    from module.ocr.llm_bridge import parse_ocr_output
    from module.config.config import AzurLaneConfig
    
    config = AzurLaneConfig()
    
    # Get provider preference from config
    provider = config.get('Llm.Provider', 'auto')
    
    # Parse with selected provider
    result = parse_ocr_output(
        raw_text=raw_text,
        parser_type=parser_type,
        provider=provider  # 'auto', 'gemini', or 'ollama'
    )
    
    return result


# Example 8: Error Handling and Monitoring
class OCRWithLLMMonitoring:
    """Example of OCR with comprehensive error handling"""
    
    def __init__(self):
        self.parse_failures = {}
        
    def parse_with_monitoring(self, raw_text, parser_type):
        """Parse with failure tracking for monitoring"""
        from module.ocr.llm_bridge import parse_ocr_output
        import time
        
        start_time = time.time()
        
        result = parse_ocr_output(
            raw_text=raw_text,
            parser_type=parser_type
        )
        
        parse_time = time.time() - start_time
        
        # Track failures for monitoring
        if result is None:
            self.parse_failures[parser_type] = self.parse_failures.get(parser_type, 0) + 1
            
            # Alert if too many failures
            if self.parse_failures[parser_type] > 10:
                self.logger.error(f"High failure rate for {parser_type} parser")
                
        # Log slow parses
        if parse_time > 1.0:
            self.logger.warning(f"Slow parse for {parser_type}: {parse_time:.2f}s")
            
        return result


# Example 9: Testing LLM Parsers
def test_llm_parser(parser_type, test_cases):
    """Test function for validating LLM parser behavior"""
    from module.ocr.llm_bridge import parse_ocr_output
    
    print(f"\nTesting {parser_type} parser:")
    print("-" * 50)
    
    for raw_text, expected in test_cases:
        result = parse_ocr_output(
            raw_text=raw_text,
            parser_type=parser_type
        )
        
        status = "✓" if result == expected else "✗"
        print(f"{status} '{raw_text}' -> '{result}' (expected: '{expected}')")


# Example test cases
if __name__ == "__main__":
    # Test commission duration parser
    test_llm_parser('commission_duration', [
        ("8:3O:OO", "08:30:00"),
        ("I2.45.30", "12:45:30"),
        ("2 15 00", "02:15:00"),
        ("23:45:30", "23:45:30"),  # This case now passes with relaxed validation
        ("00:14:59", None),  # Invalid, below 15min
    ])
    
    # Test shop price parser
    test_llm_parser('shop_price', [
        ("1,500", "1500"),
        ("00", "100"),
        ("2.000", "2000"),
        ("I00", "100"),
    ])
    
    # Test stage name parser
    test_llm_parser('stage_name', [
        ("7--2", "7-2"),
        ("sp3", "SP3"),
        ("D 3", "D3"),
        ("13—4", "13-4"),
    ])