# Gap Analysis Report for ALAS OCR Parsing Logic

## Key Implementation Questions for LLM Bridge System

1. **LLM Context Format**: How much context should the LLM receive? Just the OCR text and expected format, or should it also get the screen context (e.g., "this is from a commission duration field" vs "this is a shop price")?

2. **Fallback Strategy**: When the LLM fails to parse or returns an invalid format, what should happen? Return a default value, throw an error, or attempt a retry with more context?

3. **Performance Constraints**: Given that there might be multiple OCR fields per screenshot, are there latency requirements? Should the LLM process fields in batches or one at a time?

## Executive Summary

This report identifies critical parsing vulnerabilities in the ALAS codebase where OCR output mismatches could cause automation failures. Each gap represents a point where the bot expects rigid data formats but may receive slightly different text from OCR, leading to crashes or incorrect behavior.

This document serves as a specification for implementing an LLM-based bridge system that will transform raw OCR output into the exact formats expected by existing parsers.

---

## 1. Commission Duration Parsing

- **A. The Gap**: The function `module.commission.project.CommissionProject.commission_parse()` attempts to parse the remaining time for naval commissions. This logic is brittle and will fail if the OCR text includes variations in spacing, character misreads (I→1, D→0, S→5, B→8), or missing colons.

- **B. Exact Expected Format**: The parser strictly expects a time string in the format: `HH:MM:SS`. For example, `08:30:00`.

- **C. LLM Parsing Prompt**: 
```
You are parsing a commission duration from the Azur Lane game interface.

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

Return ONLY the formatted time string.
```

---

## 2. Dorm Food Counter Parsing

- **A. The Gap**: The logic in `module.dorm.dorm.OcrDormFood` reads the food supply counter in the dorm. The parsing expects a clean `current/total` format but will fail if the slash is misread, numbers are concatenated (10005800 instead of 1000/5800), or spacing issues occur.

- **B. Exact Expected Format**: A string in the format `XXXX/YYYY` where X and Y are integers. For example, `1000/5800`.

- **C. LLM Parsing Prompt**:
```
You are parsing a food counter from the Azur Lane dorm interface.

Input: Raw OCR text showing current food amount and maximum capacity.
Common OCR errors: Slash may be '|', '\', or missing entirely. Numbers may be concatenated without separator.

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
"3250\40000" → "3250/40000"

Return ONLY the formatted counter string.
```

---

## 3. Research Project Name Parsing

- **A. The Gap**: The `module.research.project.get_research_name()` function reads research project codes like "D-057-UL". The OCR can fail on the dash character (often read as double dash `--` or missing entirely), leading to incorrect project identification.

- **B. Exact Expected Format**: Research codes in format `X-NNN-XX` where X is letters and N is numbers. For example, `D-057-UL`.

- **C. LLM Parsing Prompt**:
```
You are parsing a research project code from the Azur Lane research lab.

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

Return ONLY the formatted project code.
```

---

## 4. Stage Name Parsing

- **A. The Gap**: The `module.campaign.campaign_ocr.CampaignOcr._campaign_ocr_result_process()` handles stage names like "7-2" or "SP3". The parser can fail if dashes are doubled (`7--2`), spaces are inserted, or the OCR reads the dash as an em-dash (–).

- **B. Exact Expected Format**: Stage names like `N-N` for normal stages or `XN` for special stages. Examples: `7-2`, `SP3`, `D3`.

- **C. LLM Parsing Prompt**:
```
You are parsing a stage name from the Azur Lane campaign map.

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

Return ONLY the formatted stage name.
```

---

## 5. Shop Price Parsing

- **A. The Gap**: The `module.shop.shop_medal.ShopPriceOcr` reads medal shop prices. The parser has a hardcoded fix for "00" → "100" but will fail on other misreads like commas in numbers (1,000), decimal points, or partial digits.

- **B. Exact Expected Format**: A clean integer string without commas or formatting. For example, `100`, `2000`.

- **C. LLM Parsing Prompt**:
```
You are parsing a price from the Azur Lane medal shop.

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

Return ONLY the integer price as a string.
```

---

## 6. Exercise Power Level Parsing

- **A. The Gap**: The `module.exercise.opponent.Opponent.get_power()` reads fleet power values. The parsing expects clean integers but will fail if the OCR includes commas (14,848), spaces, or misreads digits as letters.

- **B. Exact Expected Format**: A pure integer string with no thousand separators. For example, `14848`.

- **C. LLM Parsing Prompt**:
```
You are parsing a fleet power value from the Azur Lane exercise opponent screen.

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

Return ONLY the integer power value as a string.
```

---

## 7. Guild Operations Progress

- **A. The Gap**: The `module.guild.operations.GUILD_OPERATIONS_PROGRESS` uses DigitCounter to read progress like "75/100". The parser will fail if the slash is misread as a pipe (|), backslash (\), or if extra spaces are inserted.

- **B. Exact Expected Format**: Progress in `XX/YY` format where both are integers. For example, `75/100`.

- **C. LLM Parsing Prompt**:
```
You are parsing guild operation progress from the Azur Lane guild screen.

Input: Raw OCR text showing current progress vs maximum.
Common OCR errors: Slash may be '|', '\', '1', or have spaces. Numbers may be misread.

Required output format: CURRENT/MAXIMUM (no spaces)
- CURRENT: Integer 0-999
- MAXIMUM: Integer, typically 60, 80, 100, 120, 150, 200

Validation rules:
- Current cannot exceed maximum
- Maximum values are fixed mission targets
- Common maximums: 60, 80, 100, 120, 150, 200
- Current is always less than or equal to maximum

Examples:
"75/100" → "75/100"
"45 | 60" → "45/60"
"120\150" → "120/150"
"80 1 100" → "80/100"

Return ONLY the formatted progress string.
```

---

## 8. SOS Chapter Number Parsing

- **A. The Gap**: The `module.sos.sos.CampaignSos._find_target_chapter()` reads SOS chapter numbers. The Digit OCR can fail on colored text (green/yellow chapter numbers) or when numbers are partially obscured by UI elements.

- **B. Exact Expected Format**: A single or double-digit integer. For example, `3`, `10`.

- **C. LLM Parsing Prompt**:
```
You are parsing an SOS chapter number from the Azur Lane SOS signal list.

Input: Raw OCR text of a chapter number.
Common OCR errors: 'I' as '1', 'O' as '0', 'S' as '5', partial visibility.

Required output format: Integer 3-10 (as string)
- Range: 3 to 10 only

Validation rules:
- SOS chapters only exist for chapters 3-10
- No SOS for chapters 1, 2, 11+
- Single digit (3-9) or exactly 10
- If unclear between valid options, prefer lower chapter

Examples:
"S" → "5"
"I0" → "10"
"B" → "8"
"3" → "3"

Return ONLY the chapter number as a string.
```

---

## 9. Raid Counter Parsing

- **A. The Gap**: The `module.raid.raid.RaidCounter` reads attempt counts like "3/3". The parser uses different letter colors for different raid types, making it sensitive to UI theme changes or lighting variations in screenshots.

- **B. Exact Expected Format**: Format `X/Y` where X is current attempts and Y is maximum. For example, `3/3`.

- **C. LLM Parsing Prompt**:
```
You are parsing raid attempt counter from the Azur Lane raid interface.

Input: Raw OCR text showing remaining attempts vs maximum.
Common OCR errors: Slash variations, color-affected misreads.

Required output format: CURRENT/MAXIMUM
- CURRENT: Integer 0-3
- MAXIMUM: Always 3 for raids

Validation rules:
- Maximum is always 3 for raid attempts
- Current ranges from 0 to 3
- Current cannot exceed maximum
- Format is always X/3

Examples:
"3/3" → "3/3"
"1|3" → "1/3"
"0 / 3" → "0/3"
"2\\3" → "2/3"

Return ONLY the formatted counter string.
```

---

## 10. Research Duration Remaining

- **A. The Gap**: The `module.research.research.OCR_DURATION` reads time remaining on active research. The Duration parser can fail on formats like "1d 2h" or when colons are read as dots or semicolons.

- **B. Exact Expected Format**: Time in `HH:MM:SS` format. For example, `23:45:30`.

- **C. LLM Parsing Prompt**:
```
You are parsing time remaining for active research in Azur Lane.

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

Return ONLY the formatted time string.
```

---

## 11. Battle Status Enemy Name

- **A. The Gap**: The `module.statistics.battle_status.BattleStatusStatistics.stats_battle_status()` reads enemy fleet names like "中型主力舰队". The parser removes specific characters but will fail on partial matches or when Chinese characters are misread.

- **B. Exact Expected Format**: Clean enemy name string after removing characters `-一个―~(`. For example, `中型主力舰队`.

- **C. LLM Parsing Prompt**:
```
You are parsing an enemy fleet name from the Azur Lane battle status screen.

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

Return ONLY the cleaned fleet name.
```

---

## 12. Furniture Price Parsing

- **A. The Gap**: The `module.dorm.buy_furniture.OCR_FURNITURE_PRICE` reads furniture costs in the dorm shop. The Digit parser will fail if prices include currency symbols, decimal points, or thousand separators.

- **B. Exact Expected Format**: Pure integer string. For example, `500`, `1200`.

- **C. LLM Parsing Prompt**:
```
You are parsing furniture price from the Azur Lane dorm shop.

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

Return ONLY the integer price as a string.
```

---

## 13. New Year Event Score

- **A. The Gap**: The `module.minigame.new_year_challenge.OCR_NEW_YEAR_BATTLE_SCORE` reads minigame scores. The parser expects integers but can fail on scores with commas, decimals, or when special effects obscure digits.

- **B. Exact Expected Format**: Integer score value. For example, `12500`.

- **C. LLM Parsing Prompt**:
```
You are parsing a score from the Azur Lane New Year minigame.

Input: Raw OCR text of battle score.
Common OCR errors: Commas, special effects obscuring digits, decimals.

Required output format: Pure integer (no formatting)
- Range: 0 to 99999

Validation rules:
- Scores are always whole numbers
- Typical range: 5000-30000
- High scores may reach 50000+
- No decimals in scores

Examples:
"12,500" → "12500"
"25.000" → "25000"
"I8750" → "18750"
"7,5OO" → "7500"

Return ONLY the integer score as a string.
```

---

## 14. Data Key Counter

- **A. The Gap**: The `module.freebies.data_key.DATA_KEY` reads the available data key count using DigitCounter. The parser expects `X/Y` format but can fail if the UI shows only current count without maximum.

- **B. Exact Expected Format**: Format `current/max` like `3/5`.

- **C. LLM Parsing Prompt**:
```
You are parsing data key counter from the Azur Lane interface.

Input: Raw OCR text showing available data keys.
Common OCR errors: Missing maximum, slash variations, single number only.

Required output format: CURRENT/MAXIMUM
- CURRENT: Integer 0-5
- MAXIMUM: Always 5

Validation rules:
- Maximum is always 5 for data keys
- Current ranges from 0 to 5
- If only one number visible, assume it's current with max 5
- Format must include slash

Examples:
"3/5" → "3/5"
"2" → "2/5"
"0|5" → "0/5"
"4 / 5" → "4/5"

Return ONLY the formatted counter string.
```

---

## 15. Awaken Level Detection

- **A. The Gap**: The `module.awaken.awaken.Awaken` module needs to detect ship levels and awakening costs, but doesn't have explicit OCR parsing—it relies on indirect detection methods that can fail.

- **B. Exact Expected Format**: Integer level values like `100`, `120`.

- **C. LLM Parsing Prompt**:
```
You are parsing a ship level from the Azur Lane awakening interface.

Input: Raw OCR text of ship level.
Common OCR errors: 'I' as '1', 'O' as '0', 'l' as '1'.

Required output format: Integer level (as string)
- Range: 1 to 125

Validation rules:
- Maximum level is 125
- Awakening available at levels: 10, 30, 70, 100
- Common levels: 70, 80, 90, 100, 105, 110, 115, 120, 125
- Levels above 100 require awakening

Examples:
"I00" → "100"
"12O" → "120"
"ll0" → "110"
"7O" → "70"

Return ONLY the level as a string.
```

---

## Critical Findings Summary

1. **Time Formats**: Multiple modules expect `HH:MM:SS` but OCR often produces variations with dots, missing colons, or character substitutions.

2. **Counter Formats**: Many modules expect `X/Y` format but the slash character is frequently misread as other symbols.

3. **Number Formats**: Integer parsing fails when OCR includes commas, decimals, or spacing in numbers.

4. **Special Characters**: Dashes, slashes, and colons are common failure points across all modules.

5. **Language Mixing**: Some parsers expect specific alphabets but receive mixed language input.

## LLM Bridge Implementation Notes

The LLM bridge system should:
1. Accept raw OCR output and the target format specification
2. Apply context-aware transformations to match expected formats exactly
3. Handle validation to ensure outputs are semantically valid
4. Provide consistent error handling when transformation fails