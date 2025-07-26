# Code Review Request: Action Screenshot Archiving and Logging System

Please perform a thorough code review of the recent implementation that adds automatic screenshot archiving before bot actions and fixes the logging system in the ALAS (AzurLaneAutoScript) project.

## Implementation Summary

The implementation adds two main features:
1. **Action Screenshot Archiving**: Automatically captures and saves screenshots before every bot action (click, swipe, drag)
2. **Session-based Logging**: Creates unique timestamped log files for each bot session

## Files Modified

1. `module/device/screenshot.py` - Added `archive_action_screenshot()` method
2. `module/device/control.py` - Integrated archiving into `click()`, `long_click()`, `swipe()`, and `drag()` methods
3. `module/logger.py` - Modified `set_file_logger()` to create timestamped log files
4. `alas.py` - Removed `clear_on_start` parameter
5. `module/webui/process_manager.py` - Updated logger initialization
6. `module/research/project.py` - Added regex parsing for LLM responses
7. `CLAUDE.md` - Updated documentation

## Review Criteria

Please evaluate the following aspects:

### 1. **Correctness**
- Does the screenshot archiving work correctly for all action types?
- Are there any edge cases where screenshots might not be captured?
- Does the logging system properly create unique files for each session?
- Is the regex pattern in `get_research_name()` correct for all research project codes?

### 2. **Performance Impact**
- What is the performance overhead of saving screenshots for every action?
- Should there be any throttling or limits on screenshot storage?
- Are there any potential memory leaks or resource issues?

### 3. **Error Handling**
- What happens if the disk is full?
- How does the system handle I/O errors during screenshot saving?
- Are there proper fallbacks if screenshot capture fails?

### 4. **Code Quality**
- Is the code well-structured and maintainable?
- Are there any violations of DRY (Don't Repeat Yourself)?
- Is the error logging appropriate?

### 5. **Thread Safety**
- Since ALAS uses threading, is the file I/O thread-safe?
- Could multiple actions cause race conditions in screenshot saving?

### 6. **Storage Management**
- How much disk space will this consume over time?
- Should there be automatic cleanup of old screenshots?
- Is the folder structure optimal for finding specific screenshots?

### 7. **Integration Issues**
- Does this work correctly with all screenshot methods (ADB, scrcpy, etc.)?
- Are there any conflicts with existing screenshot functionality?
- Does it properly inherit from the Screenshot class hierarchy?

## Specific Questions

1. In `archive_action_screenshot()`, should we check if `self.image` is stale or ensure a fresh screenshot?
2. Should the timestamp format include milliseconds for better granularity?
3. Is the button name sanitization sufficient for all possible button names?
4. Should there be a config option to disable this feature for production use?
5. The regex pattern `[A-Z]-\d{3}-[A-Z]{2}` - does this cover all possible research codes?

## Expected Deliverables

Please provide:
1. A list of any bugs or issues found
2. Suggestions for improvements
3. Performance analysis and recommendations
4. Code refactoring suggestions if applicable

## Context

This implementation is part of a game automation bot that performs hundreds of actions per session. The screenshot archiving is intended for debugging purposes to understand what the bot "saw" before taking each action. The logging fix addresses issues where multiple sessions would write to the same log file, making debugging difficult.