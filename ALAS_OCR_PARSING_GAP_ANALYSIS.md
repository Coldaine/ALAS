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

- **C. Workflow**: The `commission_parse()` method captures a screenshot of the commission list, and the Duration OCR parser expects the time to be formatted as `HH:MM:SS` with colons as separators.

---

## 2. Dorm Food Counter Parsing

- **A. The Gap**: The logic in `module.dorm.dorm.OcrDormFood` reads the food supply counter in the dorm. The parsing expects a clean `current/total` format but will fail if the slash is misread, numbers are concatenated (10005800 instead of 1000/5800), or spacing issues occur.

- **B. Exact Expected Format**: A string in the format `XXXX/YYYY` where X and Y are integers. For example, `1000/5800`.

- **C. Workflow**: The `dorm_feed_scan()` function analyzes the dorm food interface, and the DigitCounter parser expects a forward slash separating current from total food supplies.

---

## 3. Research Project Name Parsing

- **A. The Gap**: The `module.research.project.get_research_name()` function reads research project codes like "D-057-UL". The OCR can fail on the dash character (often read as double dash `--` or missing entirely), leading to incorrect project identification.

- **B. Exact Expected Format**: Research codes in format `X-NNN-XX` where X is letters and N is numbers. For example, `D-057-UL`.

- **C. Workflow**: The `research_select()` method captures the research selection screen, and the OCR parser expects project codes with single dashes between segments.

---

## 4. Stage Name Parsing

- **A. The Gap**: The `module.campaign.campaign_ocr.CampaignOcr._campaign_ocr_result_process()` handles stage names like "7-2" or "SP3". The parser can fail if dashes are doubled (`7--2`), spaces are inserted, or the OCR reads the dash as an em-dash (–).

- **B. Exact Expected Format**: Stage names like `N-N` for normal stages or `XN` for special stages. Examples: `7-2`, `SP3`, `D3`.

- **C. Workflow**: The `get_chapter_index()` method scans the campaign selection screen, and the parser expects specific formats with hyphens or alphanumeric combinations.

---

## 5. Shop Price Parsing

- **A. The Gap**: The `module.shop.shop_medal.ShopPriceOcr` reads medal shop prices. The parser has a hardcoded fix for "00" → "100" but will fail on other misreads like commas in numbers (1,000), decimal points, or partial digits.

- **B. Exact Expected Format**: A clean integer string without commas or formatting. For example, `100`, `2000`.

- **C. Workflow**: The `_get_medals()` function scans shop item prices, and the Digit parser expects pure numeric strings that can be cast to integers.

---

## 6. Exercise Power Level Parsing

- **A. The Gap**: The `module.exercise.opponent.Opponent.get_power()` reads fleet power values. The parsing expects clean integers but will fail if the OCR includes commas (14,848), spaces, or misreads digits as letters.

- **B. Exact Expected Format**: A pure integer string with no thousand separators. For example, `14848`.

- **C. Workflow**: The `get_power()` method analyzes the exercise opponent selection screen, and the Digit parser needs comma-free integer strings representing fleet power.

---

## 7. Guild Operations Progress

- **A. The Gap**: The `module.guild.operations.GUILD_OPERATIONS_PROGRESS` uses DigitCounter to read progress like "75/100". The parser will fail if the slash is misread as a pipe (|), backslash (\), or if extra spaces are inserted.

- **B. Exact Expected Format**: Progress in `XX/YY` format where both are integers. For example, `75/100`.

- **C. Workflow**: The guild operations screen displays member contribution progress, and the DigitCounter expects a forward slash between current and maximum values.

---

## 8. SOS Chapter Number Parsing

- **A. The Gap**: The `module.sos.sos.CampaignSos._find_target_chapter()` reads SOS chapter numbers. The Digit OCR can fail on colored text (green/yellow chapter numbers) or when numbers are partially obscured by UI elements.

- **B. Exact Expected Format**: A single or double-digit integer. For example, `3`, `10`.

- **C. Workflow**: The `_sos_signal_select()` method scans available SOS signals, and the Digit parser expects clean numeric chapter identifiers.

---

## 9. Raid Counter Parsing

- **A. The Gap**: The `module.raid.raid.RaidCounter` reads attempt counts like "3/3". The parser uses different letter colors for different raid types, making it sensitive to UI theme changes or lighting variations in screenshots.

- **B. Exact Expected Format**: Format `X/Y` where X is current attempts and Y is maximum. For example, `3/3`.

- **C. Workflow**: The raid interface shows remaining attempts, and the DigitCounter needs to detect the slash separator with specific color thresholds.

---

## 10. Research Duration Remaining

- **A. The Gap**: The `module.research.research.OCR_DURATION` reads time remaining on active research. The Duration parser can fail on formats like "1d 2h" or when colons are read as dots or semicolons.

- **B. Exact Expected Format**: Time in `HH:MM:SS` format. For example, `23:45:30`.

- **C. Workflow**: The research lab screen shows time until completion, and the Duration OCR expects colon-separated time values.

---

## 11. Battle Status Enemy Name

- **A. The Gap**: The `module.statistics.battle_status.BattleStatusStatistics.stats_battle_status()` reads enemy fleet names like "中型主力舰队". The parser removes specific characters but will fail on partial matches or when Chinese characters are misread.

- **B. Exact Expected Format**: Clean enemy name string after removing characters `-一个―~(`. For example, `中型主力舰队`.

- **C. Workflow**: The battle preparation screen shows enemy fleet type, and the OCR needs to correctly identify Chinese/Japanese text after character filtering.

---

## 12. Furniture Price Parsing

- **A. The Gap**: The `module.dorm.buy_furniture.OCR_FURNITURE_PRICE` reads furniture costs in the dorm shop. The Digit parser will fail if prices include currency symbols, decimal points, or thousand separators.

- **B. Exact Expected Format**: Pure integer string. For example, `500`, `1200`.

- **C. Workflow**: The furniture shop displays prices, and the Digit OCR expects clean numeric values without any formatting.

---

## 13. New Year Event Score

- **A. The Gap**: The `module.minigame.new_year_challenge.OCR_NEW_YEAR_BATTLE_SCORE` reads minigame scores. The parser expects integers but can fail on scores with commas, decimals, or when special effects obscure digits.

- **B. Exact Expected Format**: Integer score value. For example, `12500`.

- **C. Workflow**: The New Year event battle results show scores, and the Digit parser needs pure numeric strings.

---

## 14. Data Key Counter

- **A. The Gap**: The `module.freebies.data_key.DATA_KEY` reads the available data key count using DigitCounter. The parser expects `X/Y` format but can fail if the UI shows only current count without maximum.

- **B. Exact Expected Format**: Format `current/max` like `3/5`.

- **C. Workflow**: The data key interface shows available keys, and the DigitCounter expects a slash-separated pair of values.

---

## 15. Awaken Level Detection

- **A. The Gap**: The `module.awaken.awaken.Awaken` module needs to detect ship levels and awakening costs, but doesn't have explicit OCR parsing—it relies on indirect detection methods that can fail.

- **B. Exact Expected Format**: Integer level values like `100`, `120`.

- **C. Workflow**: The awakening interface requires level detection to determine if ships can be awakened, but lacks robust OCR implementation.

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