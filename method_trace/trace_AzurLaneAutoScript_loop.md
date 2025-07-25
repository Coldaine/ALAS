# Method Trace: AzurLaneAutoScript.loop()

## **📍 Location**
- **File**: `alas.py`
- **Class**: `AzurLaneAutoScript`
- **Lines**: 533-603

## **📖 Purpose & Functionality**
Main scheduler loop that runs forever, executing tasks according to schedule. This is the heart of ALAS that keeps the bot running continuously.

## **🔄 Execution Path**

### Step 1: Setup Logging
- **Code**: `logger.set_file_logger(self.config_name)`
- **Purpose**: Configure file logging for this config instance
- **Inputs**: Config name string
- **Outputs**: None
- **Side Effects**: Creates/opens log file, sets up file handler

### Step 2: Infinite Loop Initialization
- **Code**: `while True:`
- **Purpose**: Create continuous operation loop
- **Inputs**: None
- **Outputs**: Loop iteration
- **Side Effects**: Begins infinite execution cycle

### Step 3: Check Stop Event
- **Code**: `if self.stop_event.is_set():`
- **Purpose**: Check if GUI requested shutdown
- **Inputs**: Threading event state
- **Outputs**: Boolean result
- **Side Effects**: None

### Step 4: Stop Event Handling
- **Code**: `logger.info('Stop event detected')` and `break`
- **Purpose**: Gracefully exit loop on stop request
- **Inputs**: None
- **Outputs**: None
- **Side Effects**: Logs stop event, exits infinite loop

### Step 5: Server Status Check
- **Code**: `self.checker.wait_until_available()`
- **Purpose**: Wait for game server maintenance to end
- **Inputs**: Server status
- **Outputs**: None
- **Side Effects**: May block execution during maintenance

### Step 6: Get Next Task
- **Code**: `task = self.get_next_task()`
- **Purpose**: Retrieve next scheduled task from scheduler
- **Inputs**: Current time, task schedule
- **Outputs**: Task name string
- **Side Effects**: Updates scheduler state

### Step 7: Device Initialization
- **Code**: `self.device`
- **Purpose**: Ensure device connection is established
- **Inputs**: Device configuration
- **Outputs**: Device object
- **Side Effects**: May initialize device connection

### Step 8: Skip First Restart Logic
- **Code**: `skip_first_restart` handling
- **Purpose**: Avoid unnecessary restart on first run
- **Inputs**: First run flag
- **Outputs**: Boolean flag
- **Side Effects**: Updates first run state

### Step 9: Task Execution
- **Code**: `self.run(task)`
- **Purpose**: Execute the scheduled task
- **Inputs**: Task name
- **Outputs**: Task result
- **Side Effects**: Performs game actions, changes game state

### Step 10: Success Handling
- **Code**: Reset failure counters, continue loop
- **Purpose**: Track successful task completion
- **Inputs**: Task result
- **Outputs**: None
- **Side Effects**: Resets failure tracking

### Step 11: Exception Handling
- **Code**: Multiple except blocks for different error types
- **Purpose**: Handle task failures with appropriate recovery
- **Inputs**: Exception objects
- **Outputs**: None
- **Side Effects**: Logging, recovery actions, failure counting

### Step 12: Failure Counting
- **Code**: Increment consecutive failure counter
- **Purpose**: Track repeated failures for escalation
- **Inputs**: Current failure count
- **Outputs**: Updated failure count
- **Side Effects**: Updates failure tracking state

### Step 13: Config Refresh
- **Code**: `del_cached_property(self, 'config')`
- **Purpose**: Reload configuration on changes
- **Inputs**: Config object
- **Outputs**: None
- **Side Effects**: Clears cached config, forces reload

### Step 14: Critical Failure Handling
- **Code**: Check failure count, call `handle_notify()`
- **Purpose**: Escalate to human on repeated failures
- **Inputs**: Failure count threshold
- **Outputs**: None
- **Side Effects**: Sends notifications, may exit

## **🌿 Branch Analysis**

### Stop Event Branch
- **If stop_event.is_set()**: Log and break from loop
- **Else**: Continue with task execution

### Task Execution Branch
- **If task execution succeeds**: Reset failure counters, continue
- **If task execution fails**: Handle exception, increment failures

### Failure Count Branch
- **If failures < threshold**: Continue with next iteration
- **If failures >= threshold**: Call handle_notify(), potentially exit

### Config Reload Branch
- **If config changes detected**: Reload configuration
- **Else**: Use cached configuration

## **⚠️ Exception Paths**

### Task Execution Exceptions
- **Source**: self.run(task) method
- **Handling**: Specific exception handlers for different error types
- **Recovery**: Varies by exception type (restart, retry, escalate)

### Device Connection Exceptions
- **Source**: Device initialization or operations
- **Handling**: Device restart or reconnection attempts
- **Recovery**: Re-establish device connection

### Configuration Exceptions
- **Source**: Config loading or validation
- **Handling**: Use default values or previous config
- **Recovery**: Reload configuration from file

## **🔗 External Calls**

### Scheduler Operations
- **get_next_task()**: Retrieve next scheduled task
- **Expected Behavior**: Return task name based on schedule

### Task Execution
- **run(task)**: Execute specific game task
- **Expected Behavior**: Perform task actions, may raise exceptions

### Device Operations
- **Device initialization and operations**: Establish and maintain device connection
- **Expected Behavior**: Provide stable device interface

### Notification System
- **handle_notify()**: Send notifications on critical failures
- **Expected Behavior**: Alert user to critical issues

## **🚨 Critical Analysis**

### Performance Impact
- **Minimal**: Mostly waiting and delegation
- **Config Reload**: May cause brief pauses
- **Task Execution**: Varies by task complexity

### Reliability Concerns
- **Infinite Loop**: Could hang if task blocks indefinitely
- **No Global Timeout**: No protection against hung tasks
- **Memory Accumulation**: Potential memory leaks over time

### Improvement Suggestions
- **Watchdog Timer**: Add timeout protection for hung tasks
- **Memory Monitoring**: Track and limit memory usage
- **Loop Statistics**: Add iteration counter and performance metrics
- **Better Failure Categorization**: Distinguish between different failure types
- **Graceful Degradation**: Implement fallback modes for critical failures
