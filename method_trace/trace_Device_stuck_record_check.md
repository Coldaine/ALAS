# Method Trace: Device.stuck_record_check()

## **📍 Location**
- **File**: `module/device/device.py`
- **Class**: `Device`
- **Lines**: 238-262

## **📖 Purpose & Functionality**
Detects when the bot is stuck waiting for UI elements too long and raises appropriate errors. Critical for preventing infinite loops.

## **🔄 Execution Path**

### Step 1: Short Timer Check
- **Code**: `if not self.stuck_timer.reached():`
- **Purpose**: Check if 60-second timer has elapsed
- **Inputs**: Timer state
- **Outputs**: Boolean result
- **Side Effects**: None

### Step 2: Early Return on Short Timer
- **Code**: `return False`
- **Purpose**: Exit early if not stuck yet (under 60s)
- **Inputs**: None
- **Outputs**: False
- **Side Effects**: None

### Step 3: Long Timer Check
- **Code**: `if not self.stuck_timer_long.reached():`
- **Purpose**: Check if 180-second timer has elapsed
- **Inputs**: Long timer state
- **Outputs**: Boolean result
- **Side Effects**: None

### Step 4: Special Button Check
- **Code**: `if len(self.detect_record) and list(self.detect_record)[0] in self.stuck_long_wait_list:`
- **Purpose**: Check if waiting for buttons that can take longer
- **Inputs**: detect_record set, stuck_long_wait_list
- **Outputs**: Boolean result
- **Side Effects**: None

### Step 5: Long Wait Early Return
- **Code**: `return False`
- **Purpose**: Allow longer wait for special buttons
- **Inputs**: None
- **Outputs**: False
- **Side Effects**: None

### Step 6: Debug Information Logging
- **Code**: `show_function_call()`
- **Purpose**: Log call stack for debugging stuck state
- **Inputs**: Current call stack
- **Outputs**: None
- **Side Effects**: Writes to log

### Step 7: Detect Record Logging
- **Code**: `logger.warning(f'Waiting for {self.detect_record}')`
- **Purpose**: Log what buttons/elements we're waiting for
- **Inputs**: detect_record set
- **Outputs**: None
- **Side Effects**: Writes warning to log

### Step 8: Clear Records
- **Code**: `self.stuck_record_clear()`
- **Purpose**: Reset timers and detection records
- **Inputs**: None
- **Outputs**: None
- **Side Effects**: Clears timers, resets detect_record

### Step 9: App Status Check
- **Code**: `if self.app_is_running():`
- **Purpose**: Determine if game is still running
- **Inputs**: App process state
- **Outputs**: Boolean result
- **Side Effects**: May check process list

### Step 10: Game Stuck Error
- **Code**: `raise GameStuckError('Wait too long')`
- **Purpose**: Indicate game is stuck but running
- **Inputs**: Error message
- **Outputs**: Exception
- **Side Effects**: Raises exception

### Step 11: Game Not Running Error
- **Code**: `raise GameNotRunningError('Wait too long')`
- **Purpose**: Indicate game has stopped/crashed
- **Inputs**: Error message
- **Outputs**: Exception
- **Side Effects**: Raises exception

## **🌿 Branch Analysis**

### Timer Branches
- **If stuck_timer not reached (< 60s)**: Return False, continue operation
- **If stuck_timer_long not reached (< 180s) AND waiting for special button**: Return False
- **Else**: Proceed to stuck detection logic

### App Status Branch
- **If app_is_running() returns True**: Raise GameStuckError
- **Else**: Raise GameNotRunningError

### Special Button Branch
- **If detect_record contains button in stuck_long_wait_list**: Allow 180s timeout
- **Else**: Use 60s timeout

## **⚠️ Exception Paths**

### GameStuckError
- **Condition**: Timer expired and app is running
- **Recovery**: Caller should restart current operation or task
- **Impact**: Current operation fails, may trigger task restart

### GameNotRunningError
- **Condition**: Timer expired and app is not running
- **Recovery**: Caller should restart app or exit
- **Impact**: Major failure, requires app restart

## **🔗 External Calls**

### Timer Methods
- **stuck_timer.reached()**: Check 60-second timer
- **stuck_timer_long.reached()**: Check 180-second timer
- **Expected Behavior**: Return boolean based on elapsed time

### Utility Methods
- **show_function_call()**: Debug stack trace logging
- **stuck_record_clear()**: Reset timers and records
- **app_is_running()**: Check if game process is active

### Data Structures
- **detect_record**: Set of buttons currently being waited for
- **stuck_long_wait_list**: List of buttons that can take longer
