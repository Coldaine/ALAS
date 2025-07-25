# Three-Strike OCR Error System in ALAS

## How It Works

**Yes, the bot will still stop after 3 consecutive OCR failures**, but only for specific tracked parsing operations.

### Key Points:

1. **The three-strike system operates at the parsing level, not the raw OCR level**
   - It tracks specific error types like "ocr_duration", "ocr_commission", etc.
   - General OCR failures (like network errors) don't trigger this system

2. **Error Categories Are Independent**
   - 3 duration parsing errors won't affect commission parsing
   - Each error type has its own counter

3. **Success Resets the Counter**
   - Any successful parse of that type resets the count to 0
   - This prevents temporary issues from permanently stopping the bot

4. **When It Triggers**
   - After exactly 3 consecutive failures of the same type
   - Raises `OcrParseError` exception
   - The bot stops to prevent infinite loops on persistent issues

### Example Scenario:

```
1. OCR reads "6h 30m" but expects "6:30:00" format -> Error #1
2. OCR reads "invalid" for duration -> Error #2  
3. OCR reads garbled text -> Error #3
4. OcrParseError raised! Bot stops.
```

### Where It's Used:

The three-strike system is implemented for specific parsing operations:
- Duration parsing (timers, countdowns)
- Commission status parsing
- Other structured data that requires specific formats

### Important: 

**Our improved PaddleOCR wrapper doesn't change this behavior.** The three-strike system remains intact because:
- It operates at a higher level (parsing layer)
- It's not affected by the OCR backend implementation
- The error counting happens after OCR results are returned

So yes, ALAS will still stop after 3 consecutive parsing failures to prevent infinite loops and alert you to persistent issues that need investigation.