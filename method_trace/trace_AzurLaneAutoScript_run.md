# Method Trace: AzurLaneAutoScript.run()

## **📍 Location**
- **File**: `alas.py`
- **Class**: `AzurLaneAutoScript`
- **Lines**: 71-150

## **📖 Purpose & Functionality**
Execute game tasks with comprehensive error handling and recovery strategies. Central method for all task execution.

## **🔄 Execution Path**

### Step 1: Parameter Processing
- **Code**: `command = command.strip()`
- **Purpose**: Clean command string
- **Inputs**: Command string
- **Outputs**: Cleaned command
- **Side Effects**: None

### Step 2: Skip Screenshot Check
- **Code**: `if skip_first_screenshot:`
- **Purpose**: Optionally skip initial screenshot for performance
- **Inputs**: Boolean flag
- **Outputs**: None
- **Side Effects**: May skip screenshot call

### Step 3: Initial Screenshot
- **Code**: `self.device.screenshot()`
- **Purpose**: Capture current game state
- **Inputs**: None
- **Outputs**: Screenshot array
- **Side Effects**: Updates device.image

### Step 4: Command Execution
- **Code**: `super().run(command)`
- **Purpose**: Execute the actual task/command
- **Inputs**: Command string
- **Outputs**: Task result
- **Side Effects**: Performs game actions, changes game state

### Step 5: Exception Handling Block
- **Code**: Multiple except clauses for different error types
- **Purpose**: Handle various failure modes with specific recovery
- **Inputs**: Exception objects
- **Outputs**: None or re-raised exception
- **Side Effects**: Logging, recovery actions, state changes

## **🌿 Branch Analysis**

### Skip Screenshot Branch
- **If skip_first_screenshot is True**: Skip initial screenshot
- **Else**: Take screenshot before command execution

### Success Path
- **If super().run(command) succeeds**: Return normally
- **No exceptions**: Task completed successfully

### Exception Handling Branches
- **9 specific exception types**: Each with tailored recovery strategy
- **Generic Exception**: Catch-all for unexpected errors

## **⚠️ Exception Paths**

### GameStuckError
- **Recovery**: Log error, may restart current operation
- **Handling**: Specific logging and recovery logic
- **Re-raise**: Depends on error severity

### GameNotRunningError
- **Recovery**: Attempt to restart game
- **Handling**: App restart logic
- **Re-raise**: If restart fails

### EmulatorNotRunningError
- **Recovery**: Attempt to restart emulator
- **Handling**: Emulator restart logic
- **Re-raise**: If emulator restart fails

### RequestHumanTakeover
- **Recovery**: Stop automation, wait for human
- **Handling**: Notification and pause logic
- **Re-raise**: Always (requires human intervention)

### GameTooManyClickError
- **Recovery**: Reduce click frequency
- **Handling**: Adjust timing parameters
- **Re-raise**: Rarely (usually recoverable)

### GameBugError
- **Recovery**: Restart current task
- **Handling**: Task restart logic
- **Re-raise**: If restart fails

### GameNotRunningError
- **Recovery**: Restart game application
- **Handling**: App management logic
- **Re-raise**: If app restart fails

### ScriptError
- **Recovery**: Log and continue or restart
- **Handling**: Script-specific recovery
- **Re-raise**: Depends on error type

### Exception (Generic)
- **Recovery**: Log and re-raise
- **Handling**: Generic error logging
- **Re-raise**: Always (unknown error)

## **🔗 External Calls**

### Device Operations
- **device.screenshot()**: Capture current screen
- **Expected Behavior**: Return screenshot array or raise exception

### Task Execution
- **super().run(command)**: Execute actual task logic
- **Expected Behavior**: Perform task actions, may raise various exceptions

### Recovery Operations
- **Various recovery methods**: Restart app, emulator, etc.
- **Expected Behavior**: Attempt to recover from error state

## **🚨 Critical Analysis**

### Error Handling Completeness
- **Covers**: 9 specific error types plus generic catch-all
- **Missing**: Some edge cases may not be covered
- **Improvement**: Add more specific error categorization

### Recovery Strategies
- **Restart-based**: Most errors trigger some form of restart
- **Human Intervention**: Some errors require human takeover
- **Graceful Degradation**: Limited fallback options

### Performance Impact
- **Screenshot Overhead**: Initial screenshot on every run
- **Exception Handling**: Minimal overhead unless exceptions occur
- **Recovery Cost**: Restart operations can be expensive
