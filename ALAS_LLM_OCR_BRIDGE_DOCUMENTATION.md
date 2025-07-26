# ALAS LLM OCR Bridge System - Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [How It Works](#how-it-works)
4. [Parser Types](#parser-types)
5. [Integration Guide](#integration-guide)
6. [Configuration](#configuration)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)

## Overview

The LLM OCR Bridge System is a robust parsing framework that uses Large Language Models (LLMs) to intelligently interpret OCR output, handling common recognition errors and format variations that would otherwise crash ALAS automation.

### Problem Statement
OCR engines often produce imperfect text with common errors:
- Character substitutions: `O` → `0`, `I` → `1`, `S` → `5`
- Separator variations: `:` → `.` or `;`, `/` → `|` or `\`
- Missing or extra characters: `7-2` → `7--2`
- Format inconsistencies: `1,500` vs `1500`

### Solution
The LLM Bridge provides intelligent parsing that understands context and can correct these errors automatically.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ALAS Module                                │
│  (e.g., Commission, Dorm, Research)                                │
└────────────────────────┬────────────────────────────────────────────┘
                         │ Raw OCR Text: "8:3O:OO"
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    parse_ocr_output()                               │
│  Main entry point with parser type selection                        │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LLMParser Instance                               │
│  (e.g., CommissionDurationParser)                                   │
├─────────────────────────────────────────────────────────────────────┤
│  1. Cache Check     │  Returns cached result if available           │
│  2. Rule-Based      │  Fast regex/pattern matching                  │
│  3. LLM Query       │  Intelligent parsing with context             │
│  4. Validation      │  Ensures output meets format requirements     │
│  5. Default/Error   │  Safe fallback value                         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM Provider Layer                               │
├─────────────────────┬───────────────────┬──────────────────────────┤
│   GeminiProvider    │   OllamaProvider   │   Future Providers      │
│  (Cloud-based)      │  (Local/Private)   │  (OpenAI, Claude, etc)  │
└─────────────────────┴───────────────────┴──────────────────────────┘
                         │
                         ▼
                 Parsed Result: "08:30:00"
```

## How It Works

### 1. Parser Selection
When `parse_ocr_output()` is called, it creates an instance of the appropriate parser based on the `parser_type`:

```python
result = parse_ocr_output(
    raw_text="8:3O:OO",              # OCR output with errors
    parser_type='commission_duration', # Selects CommissionDurationParser
    context={'source': 'timer'}       # Optional context
)
```

### 2. Multi-Stage Parsing Process

#### Stage 1: Cache Lookup (< 1ms)
```python
cache_key = "CommissionDurationParser:8:3O:OO"
if cache_key in self._cache:
    return self._cache[cache_key]  # Returns "08:30:00"
```

#### Stage 2: Rule-Based Parsing (< 10ms)
```python
def _rule_based_fallback(self, raw_text):
    # Apply common OCR corrections
    text = raw_text.replace('O', '0').replace('I', '1')
    text = text.replace('.', ':').replace(';', ':')
    
    # Try regex pattern
    pattern = r'(\d{1,2}):(\d{1,2}):(\d{1,2})'
    match = re.search(pattern, text)
    if match:
        h, m, s = match.groups()
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
```

#### Stage 3: LLM Parsing (100-500ms)
```python
def _llm_parse(self, raw_text, context):
    prompt = self.get_prompt()  # Parser-specific prompt
    full_prompt = f"{prompt}\n\nInput: {raw_text}"
    
    # Query LLM provider
    result = provider.query(full_prompt, max_tokens=50)
    return result
```

#### Stage 4: Validation
```python
def validate_output(self, output):
    # Parser-specific validation
    pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])$'
    if not re.match(pattern, output):
        return False
    
    # Additional semantic validation
    hours, minutes, seconds = map(int, output.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return 900 <= total_seconds <= 43200  # 15 min to 12 hours
```

### 3. LLM Prompt Engineering

Each parser has a carefully crafted prompt that includes:

1. **Context**: What the text represents
2. **Common Errors**: Known OCR mistakes
3. **Output Format**: Exact required format
4. **Validation Rules**: Constraints and ranges
5. **Examples**: Input → Output mappings

Example prompt structure:
```
You are parsing a commission duration from the Azur Lane game interface.

Input: Raw OCR text representing time remaining for a naval commission.
Common OCR errors: 'I' misread as '1', 'O' as '0', colons as dots...

Required output format: HH:MM:SS (24-hour format with leading zeros)

Validation rules:
- Commissions range from 0:15:00 to 12:00:00
- No commission exceeds 24 hours

Examples:
"8:3O:OO" → "08:30:00"
"I2.45.30" → "12:45:30"

Return ONLY the formatted time string.
```

## Parser Types

### Time/Duration Parsers
| Parser Type | Format | Example | Use Case |
|------------|---------|---------|----------|
| `commission_duration` | HH:MM:SS | "08:30:00" | Commission timers |
| `research_duration` | HH:MM:SS | "26:00:00" | Research timers (can exceed 24h) |

### Counter Parsers
| Parser Type | Format | Example | Use Case |
|------------|---------|---------|----------|
| `dorm_food` | XXXX/YYYY | "1000/5800" | Dorm food supply |
| `guild_progress` | XX/YY | "75/100" | Guild operations |
| `raid_counter` | X/3 | "2/3" | Raid attempts |
| `data_key` | X/5 | "3/5" | Data key availability |

### Identifier Parsers
| Parser Type | Format | Example | Use Case |
|------------|---------|---------|----------|
| `research_code` | X-NNN-XX | "D-057-UL" | Research projects |
| `stage_name` | N-N or XN | "7-2", "D3" | Campaign stages |
| `battle_enemy` | Text | "中型主力舰队" | Enemy fleet names |

### Numeric Parsers
| Parser Type | Format | Example | Use Case |
|------------|---------|---------|----------|
| `shop_price` | Integer | "1500" | Medal shop prices |
| `fleet_power` | Integer | "14848" | Fleet power rating |
| `furniture_price` | Integer | "500" | Furniture costs |
| `minigame_score` | Integer | "12500" | Event scores |
| `ship_level` | Integer | "120" | Ship levels |
| `sos_chapter` | Integer (3-10) | "7" | SOS chapter numbers |

## Integration Guide

### Basic Integration

1. **Import the parsing function**:
```python
from module.ocr.llm_bridge import parse_ocr_output
```

2. **Replace brittle parsing code**:
```python
# OLD CODE (crashes on OCR errors):
def parse_commission_time(self, ocr_text):
    parts = ocr_text.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    return hours * 3600 + minutes * 60 + seconds

# NEW CODE (handles OCR errors):
def parse_commission_time(self, ocr_text):
    parsed = parse_ocr_output(
        raw_text=ocr_text,
        parser_type='commission_duration'
    )
    
    if parsed:
        h, m, s = map(int, parsed.split(':'))
        return h * 3600 + m * 60 + s
    else:
        self.logger.warning(f"Failed to parse time: {ocr_text}")
        return None
```

### Advanced Integration

1. **With context information**:
```python
result = parse_ocr_output(
    raw_text=ocr_text,
    parser_type='shop_price',
    context={
        'source': 'medal_shop',
        'item_type': 'ship',
        'expected_range': (1000, 5000)
    }
)
```

2. **With specific provider**:
```python
# Force local processing
result = parse_ocr_output(
    raw_text=ocr_text,
    parser_type='fleet_power',
    provider='ollama'  # Use local LLM
)
```

3. **Batch processing**:
```python
from module.ocr.llm_parsers import get_parser

parser = get_parser('stage_name')
stages = ["7--2", "D 3", "sp3", "13—4"]
results = parser.batch_parse(stages)
# Results: ["7-2", "D3", "SP3", "13-4"]
```

### Creating Custom Parsers

To add a new parser type:

1. **Create parser class**:
```python
from module.ocr.llm_bridge import LLMParser

class MyCustomParser(LLMParser):
    def get_prompt(self) -> str:
        return """Your parsing prompt here..."""
    
    def validate_output(self, output: str) -> bool:
        # Validation logic
        return True
    
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        # Fast parsing rules
        return None
    
    def _get_default_value(self) -> Optional[str]:
        return "default_value"
```

2. **Register in factory**:
```python
# In llm_parsers.py
def get_parser(parser_type: str, provider: str = "auto"):
    parsers = {
        # ... existing parsers ...
        "my_custom": MyCustomParser,
    }
```

## Configuration

### In ALAS Configuration File
```yaml
Llm:
  # Provider selection: 'auto', 'gemini', 'ollama'
  Provider: auto
  
  # Gemini configuration
  GeminiApiKey: your-api-key-here
  GeminiModel: gemini-1.5-flash
  
  # Ollama configuration  
  OllamaUrl: http://localhost:11434
  OllamaModel: llama3.2:3b
  
  # Performance settings
  CacheSize: 1000
  MaxRetries: 2
  Timeout: 5.0
```

### Environment Variables
```bash
# Alternative to config file
export ALAS_LLM_PROVIDER=gemini
export ALAS_GEMINI_API_KEY=your-key
export ALAS_OLLAMA_URL=http://localhost:11434
```

## Performance Considerations

### Response Times
- **Cache Hit**: < 1ms
- **Rule-Based**: < 10ms
- **LLM (Gemini)**: 100-300ms
- **LLM (Ollama)**: 200-500ms

### Optimization Strategies

1. **Enable caching** (default):
   - Repeated OCR values return instantly
   - Cache persists during ALAS session

2. **Use rule-based first**:
   - Parser tries fast regex patterns before LLM
   - Handles 60-80% of cases without LLM

3. **Batch processing**:
   - Process multiple fields together
   - Reduces LLM round trips

4. **Provider selection**:
   - Use Ollama for privacy/offline
   - Use Gemini for accuracy/speed

### Memory Usage
- Base system: ~10MB
- Per parser instance: ~1MB
- Cache (1000 entries): ~5MB

## Troubleshooting

### Common Issues

1. **Parser returns None**
   - Check OCR text is not empty
   - Verify parser type is correct
   - Check logs for validation failures

2. **Slow parsing**
   - Ensure LLM provider is running
   - Check network connectivity (Gemini)
   - Consider using cache warming

3. **Inconsistent results**
   - Verify LLM temperature is low (0.1)
   - Check prompt examples match use case
   - Ensure validation rules are correct

### Debug Mode
```python
import logging
logging.getLogger('module.ocr.llm_bridge').setLevel(logging.DEBUG)

# Now parsing will show detailed logs:
# DEBUG: Cache miss for CommissionDurationParser:8:3O:OO
# DEBUG: Rule-based parsing failed
# DEBUG: LLM query: "You are parsing a commission duration..."
# DEBUG: LLM response: "08:30:00"
# INFO: CommissionDurationParser LLM parsed '8:3O:OO' -> '08:30:00'
```

### Monitoring
```python
# Track parsing performance
from module.ocr.llm_bridge import get_parsing_stats

stats = get_parsing_stats()
print(f"Cache hits: {stats['cache_hits']}")
print(f"Rule-based success: {stats['rule_based_success']}")
print(f"LLM queries: {stats['llm_queries']}")
print(f"Parse failures: {stats['failures']}")
```

## API Reference

### Main Function
```python
parse_ocr_output(
    raw_text: str,
    parser_type: str,
    context: Dict[str, Any] = None,
    provider: str = "auto"
) -> Optional[str]
```

**Parameters:**
- `raw_text`: OCR output to parse
- `parser_type`: Type of parser to use (see Parser Types)
- `context`: Optional context dictionary
- `provider`: LLM provider selection ('auto', 'gemini', 'ollama')

**Returns:**
- Parsed string in expected format, or None if parsing failed

### Parser Base Class
```python
class LLMParser(ABC):
    def parse(raw_text: str, context: Dict = None) -> Optional[str]
    def batch_parse(texts: List[str], context: Dict = None) -> List[Optional[str]]
    def validate_output(output: str) -> bool
```

### Provider Interface
```python
class LLMProvider(ABC):
    def query(prompt: str, max_tokens: int = 50) -> Optional[str]
```

## Best Practices

1. **Always handle None returns**:
```python
result = parse_ocr_output(text, 'shop_price')
price = int(result) if result else 0
```

2. **Use appropriate parser types**:
   - Don't use `commission_duration` for research timers
   - Don't use `shop_price` for fleet power

3. **Provide context when helpful**:
```python
context = {'item_rarity': 'SSR', 'shop_type': 'medal'}
```

4. **Monitor parsing failures**:
   - Log failures for analysis
   - Adjust prompts based on patterns
   - Add rule-based patterns for common cases

5. **Test with real OCR data**:
   - Collect failed OCR samples
   - Verify parser handles them correctly
   - Add to test suite

## Conclusion

The LLM OCR Bridge System provides a robust, extensible solution for handling OCR parsing in ALAS. By combining fast rule-based parsing with intelligent LLM interpretation, it ensures reliable automation even with imperfect OCR output.

For questions or contributions, please refer to the ALAS project documentation.