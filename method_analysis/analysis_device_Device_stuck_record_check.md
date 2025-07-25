# Method Analysis: Device.stuck_record_check()

## **📍 Location**
- **File**: `module/device/device.py`
- **Class**: `Device`
- **Lines**: 238-262

## **📊 Classification**
- **Call Frequency**: EXTREME
- **Criticality**: VITAL
- **Failure Risk**: 🟡 MEDIUM

## **🔍 Method Signature**
```python
def stuck_record_check(self):
```

## **📖 Purpose & Functionality**
Detects when the bot is stuck waiting for UI elements too long and raises appropriate errors. Critical for preventing infinite loops and detecting game crashes.

## **🔄 Logic Flow**
1. **Check Timers**: Check if 60s timer reached (180s for long waits)
2. **Short Timer Check**: If under 60s, return False
3. **Long Timer Check**: If under 180s, check if waiting for special buttons
4. **Log Warning**: Show function call stack and what we're waiting for
5. **Clear Records**: Reset timers and detection records
6. **Raise Error**: GameStuckError if app running, GameNotRunningError if not

## **🔗 Dependencies**
### **Internal Dependencies**:
- `self.stuck_timer` - 60 second timer
- `self.stuck_timer_long` - 180 second timer
- `self.stuck_long_wait_list` - Buttons that can take longer
- `self.detect_record` - Set of buttons being waited for
- `show_function_call()` - Debug stack trace
- `self.app_is_running()` - Check if game is alive

### **External Dependencies**:
- **Libraries**: None directly
- **System**: App process checking
- **Platform**: None

## **📈 Call Analysis**
### **Called By**:
- `screenshot()` - EVERY screenshot call
- `dump_hierarchy()` - UI hierarchy dumps
- Called thousands of times per hour

### **Calls To**:
- Timer methods: reached(), reset()
- show_function_call() for debugging
- stuck_record_clear()
- app_is_running()

## **⚠️ Failure Modes**
### **Potential Failures**:
1. **False Positives**: Detecting stuck when just slow
2. **False Negatives**: Not detecting actual stuck state
3. **Timer Issues**: Timer not properly reset between tasks

### **Error Handling**:
- **Exceptions Caught**: None
- **Recovery Strategy**: Raises exceptions for caller to handle
- **Fallback Methods**: None

## **🌍 Environment Compatibility**
### **Windows**: ✅ Fully compatible
### **Linux**: ✅ Fully compatible  
### **Cross-Platform Issues**: None

## **🚨 Critical Analysis**
### **Performance Impact**: 
- Minimal - just timer checks
- Called very frequently but lightweight

### **Reliability Concerns**: 
- Hard-coded timeout values
- Special case list maintenance
- Stack trace logging overhead

### **Improvement Suggestions**: 
- Configurable timeout values
- Dynamic timeout based on operation
- Better stuck detection heuristics
- Separate timers for different operations

## **🔧 Testing Strategy**
### **Unit Test Approach**: 
- Test timer expiration scenarios
- Test special button detection
- Verify proper error raising

### **Integration Test Needs**: 
- Test actual stuck scenarios
- Verify game crash detection
- Test timer reset behavior

### **Mock Requirements**: 
- Mock timers
- Mock app_is_running()
- Mock detect_record