# Method Analysis: AzurLaneAutoScript.run()

## **📍 Location**
- **File**: `alas.py`
- **Class**: `AzurLaneAutoScript`
- **Lines**: 71-150

## **📊 Classification**
- **Call Frequency**: HIGH
- **Criticality**: VITAL
- **Failure Risk**: 🔴 HIGH

## **🔍 Method Signature**
```python
def run(self, command: str, skip_first_screenshot: bool = False) -> bool:
```

## **📖 Purpose & Functionality**
Core task execution method that runs any game task by name. This is THE MOST IMPORTANT METHOD as it handles all task execution and error recovery for the entire bot.

## **🔄 Logic Flow**
1. **Take Screenshot**: Unless skip_first_screenshot is True
2. **Execute Command**: Call method by name using `__getattribute__(command)()`
3. **Return Success**: Return True if task completes
4. **Handle Exceptions**: Complex exception handling for various game/bot errors
5. **Error Recovery**: Different strategies based on error type

## **🔗 Dependencies**
### **Internal Dependencies**:
- `self.device.screenshot()` - Screenshot before task
- `self.__getattribute__(command)()` - Dynamic method call
- `self.config.task_call()` - Schedule task execution
- `self.save_error_log()` - Error logging
- `self.checker` - Server status checking
- `handle_notify()` - Send notifications

### **External Dependencies**:
- **Libraries**: None directly
- **System**: Depends on task being executed
- **Platform**: Task-specific dependencies

## **📈 Call Analysis**
### **Called By**:
- `loop()` method - Called for EVERY scheduled task
- `get_next_task()` → `loop()` → `run()`
- Can be called hundreds of times per hour

### **Calls To**:
- Task methods: `dorm()`, `commission()`, etc. (40+ methods)
- Error handling: `save_error_log()`, `handle_notify()`
- Recovery: `config.task_call('Restart')`

## **⚠️ Failure Modes**
### **Potential Failures**:
1. **TaskEnd**: Normal task completion (not a failure)
2. **GameNotRunningError**: Game closed unexpectedly
3. **GameStuckError**: UI frozen or unresponsive
4. **GameTooManyClickError**: Clicking same spot repeatedly
5. **GameBugError**: Known game client bugs
6. **GamePageUnknownError**: Cannot identify current game screen
7. **ScriptError**: Programming error in task
8. **RequestHumanTakeover**: Manual intervention needed
9. **OcrParseError**: OCR failed multiple times
10. **Generic Exception**: Any unexpected error

### **Error Handling**:
- **Exceptions Caught**: 9 specific exception types + generic
- **Recovery Strategy**: 
  - Game errors → Restart game
  - Script errors → Exit with notification
  - OCR errors → Exit (new addition)
- **Fallback Methods**: Task restart, game restart, human takeover

## **🌍 Environment Compatibility**
### **Windows**: ✅ All error handling works
### **Linux**: ✅ All error handling works
### **Cross-Platform Issues**: 
- Task-specific issues inherited from called methods
- Notification system may be platform-specific

## **🚨 Critical Analysis**
### **Performance Impact**: 
- Exception handling overhead minimal
- Screenshot before each task
- Error log saving can be slow

### **Reliability Concerns**: 
- **WHERE BUGS MANIFEST** - All task errors surface here
- Complex exception hierarchy
- Some errors force bot exit

### **Improvement Suggestions**: 
- Add task timeout handling
- Implement retry with backoff
- Better error categorization
- Task-specific error handlers

## **🔧 Testing Strategy**
### **Unit Test Approach**: 
- Test each exception path
- Mock task methods to raise exceptions
- Verify return values and side effects

### **Integration Test Needs**: 
- Test with real game scenarios
- Verify error recovery works
- Test notification system

### **Mock Requirements**: 
- Mock all task methods
- Mock device.screenshot()
- Mock config.task_call()
- Mock notification system