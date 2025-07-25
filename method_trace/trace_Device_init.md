# Method Trace: Device.__init__()

## **📍 Location**
- **File**: `module/device/device.py`
- **Class**: `Device`
- **Lines**: 80-96

## **📖 Purpose & Functionality**
Initialize device connection with retry logic for emulator startup. Critical for establishing communication with Android emulator.

## **🔄 Execution Path**

### Step 1: Parent Class Initialization
- **Code**: `super().__init__(config)`
- **Purpose**: Initialize Screenshot, Control, and AppControl base classes
- **Inputs**: Config object
- **Outputs**: None
- **Side Effects**: Sets up base class state, screenshot methods, control interfaces

### Step 2: Retry Loop Setup
- **Code**: `for _ in range(4):`
- **Purpose**: Allow up to 4 attempts to start emulator
- **Inputs**: None
- **Outputs**: Loop iteration
- **Side Effects**: Attempt counter increments

### Step 3: Device Initialization Attempt
- **Code**: `self.device_init()`
- **Purpose**: Attempt to connect to and initialize device
- **Inputs**: None
- **Outputs**: None
- **Side Effects**: Establishes device connection, may start emulator

### Step 4: Success Path
- **Code**: `break`
- **Purpose**: Exit retry loop on successful initialization
- **Inputs**: None
- **Outputs**: None
- **Side Effects**: Exits loop, proceeds to post-init

### Step 5: Exception Handling
- **Code**: `except EmulatorNotRunningError:`
- **Purpose**: Catch emulator startup failures
- **Inputs**: Exception object
- **Outputs**: None
- **Side Effects**: Continues to next retry attempt

### Step 6: Post-Initialization Setup
- **Code**: Various setup calls after retry loop
- **Purpose**: Configure device-specific settings
- **Inputs**: Device state
- **Outputs**: None
- **Side Effects**: Sets screenshot method, configures click recording

## **🌿 Branch Analysis**

### Retry Success Branch
- **If device_init() succeeds**: Break out of retry loop immediately
- **Continue to**: Post-initialization setup

### Retry Failure Branch
- **If EmulatorNotRunningError raised**: Continue to next retry attempt
- **If 4 attempts exhausted**: Exception propagates to caller

### Platform-Specific Branches
- **Different behavior**: Based on emulator type and platform
- **Handled in**: device_init() method implementation

## **⚠️ Exception Paths**

### EmulatorNotRunningError
- **Source**: device_init() method
- **Handling**: Retry up to 4 times
- **Recovery**: Wait for emulator startup, retry connection

### Other Exceptions
- **Source**: device_init() or parent class init
- **Handling**: Propagate to caller (no retry)
- **Recovery**: Caller must handle

## **🔗 External Calls**

### device_init()
- **Purpose**: Platform-specific device initialization
- **Expected Behavior**: Establish connection or raise EmulatorNotRunningError
- **Side Effects**: May start emulator process, configure ADB

### Parent Class Constructors
- **Screenshot.__init__()**: Initialize screenshot capabilities
- **Control.__init__()**: Initialize touch/input control
- **AppControl.__init__()**: Initialize app management
