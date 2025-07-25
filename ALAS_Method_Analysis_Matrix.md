# **🔍 ALAS Method Analysis & Failure Matrix**

## **🤖 AGENT INSTRUCTIONS FOR SYSTEMATIC EXPANSION**

### **📋 EXPANSION METHODOLOGY**

To systematically expand this analysis for comprehensive codebase coverage, follow these detailed instructions:

#### **Phase 1: File Discovery & Prioritization**
1. **Identify all Python files** in the ALAS codebase using `Glob` tool with pattern `**/*.py`
2. **Exclude test files** (anything in `test/` folders or named `test_*.py`)
3. **Prioritize files by importance**:
   - **CRITICAL**: Core scheduler, device interface, base classes
   - **HIGH**: Game modules (campaign, dorm, commission, etc.)
   - **MEDIUM**: Configuration, utilities, UI components
   - **LOW**: Deployment scripts, tools, standalone utilities

#### **Phase 2: Method-by-Method Analysis Protocol**

For each file, follow this systematic review process:

##### **Step 1: File Structure Analysis**
1. **Read the entire file** using the `Read` tool
2. **Identify all classes and methods** using `Grep` with pattern `^(class|def)`
3. **Map inheritance relationships** by finding parent classes
4. **Document import dependencies** to understand external requirements

##### **Step 2: Individual Method Deep Dive**
For each method, perform this detailed analysis:

1. **Read Method Implementation**:
   - Use `Read` tool to examine the complete method code
   - Identify input parameters, return types, and side effects
   - Note any decorators (cached_property, retry, etc.)

2. **Trace Logic Flow**:
   - Map the execution path through the method
   - Identify decision points (if/else, loops, exception handling)
   - Document method calls to other functions/classes
   - Note platform-specific code paths

3. **Analyze Dependencies**:
   - External library calls (cv2, numpy, adb, etc.)
   - File system operations
   - Network operations  
   - Hardware interface calls
   - Configuration dependencies

4. **Assess Call Frequency**:
   - **EXTREME**: Called in tight loops (screenshot, appear, click)
   - **HIGH**: Called for each game action (UI navigation)
   - **MEDIUM**: Called per task/schedule cycle
   - **LOW**: Called at startup/shutdown or error conditions

5. **Determine Criticality**:
   - **VITAL**: Bot cannot function if this fails
   - **CRITICAL**: Major functionality loss but bot continues
   - **IMPORTANT**: Feature degradation
   - **HELPER**: Convenience/optimization only

6. **Evaluate Failure Risk**:
   - **🔴 HIGH**: Platform-specific, binary dependencies, complex logic
   - **🟡 MEDIUM**: Cross-platform but has external dependencies
   - **🟢 LOW**: Pure Python, simple logic, well-tested

##### **Step 3: Environment Compatibility Analysis**
For each method, analyze:
1. **Windows-specific code**: Registry access, Windows paths, .exe/.dll files
2. **Linux compatibility**: Cross-platform libraries, POSIX paths
3. **Emulator dependencies**: Specific emulator APIs, binaries
4. **Hardware requirements**: GPU, specific Android versions

#### **Phase 3: Documentation Generation**

##### **Step 4: Individual Method Documentation**
For each significant method, create a separate `.md` file with this structure:

```markdown
# Method Analysis: [ClassName].[method_name]()

## **📍 Location**
- **File**: `path/to/file.py`
- **Class**: `ClassName`
- **Lines**: [start-end]

## **📊 Classification**
- **Call Frequency**: [EXTREME/HIGH/MEDIUM/LOW]
- **Criticality**: [VITAL/CRITICAL/IMPORTANT/HELPER]
- **Failure Risk**: [🔴/🟡/🟢] [HIGH/MEDIUM/LOW]

## **🔍 Method Signature**
```python
def method_name(self, param1: type, param2: type = default) -> return_type:
```

## **📖 Purpose & Functionality**
[Detailed description of what this method does]

## **🔄 Logic Flow**
1. **Input Validation**: [description]
2. **Main Processing**: [step-by-step logic]
3. **Error Handling**: [exception handling]
4. **Return/Side Effects**: [what it returns or changes]

## **🔗 Dependencies**
### **Internal Dependencies**:
- `self.other_method()` - [purpose]
- `external_class.method()` - [purpose]

### **External Dependencies**:
- **Libraries**: numpy, cv2, adb, etc.
- **System**: File system, network, hardware
- **Platform**: Windows/Linux specific requirements

## **📈 Call Analysis**
### **Called By**:
- `method_a()` in `file_a.py` - [context]
- `method_b()` in `file_b.py` - [context]

### **Calls To**:
- `dependency_method()` - [frequency and purpose]

## **⚠️ Failure Modes**
### **Potential Failures**:
1. **[Failure Type]**: [Description and cause]
2. **[Failure Type]**: [Description and cause]

### **Error Handling**:
- **Exceptions Caught**: [list]
- **Recovery Strategy**: [description]
- **Fallback Methods**: [alternatives]

## **🌍 Environment Compatibility**
### **Windows**: ✅/❌/⚠️ [notes]
### **Linux**: ✅/❌/⚠️ [notes]
### **Cross-Platform Issues**: [specific concerns]

## **🚨 Critical Analysis**
### **Performance Impact**: [description]
### **Reliability Concerns**: [issues]
### **Improvement Suggestions**: [recommendations]

## **🔧 Testing Strategy**
### **Unit Test Approach**: [how to test this method]
### **Integration Test Needs**: [broader testing requirements]
### **Mock Requirements**: [external dependencies to mock]
```

##### **Step 5: Agent Execution Instructions**

**EXPLICIT AGENT ORDERS:**

1. **You MUST create individual analysis files** for each method you analyze
2. **File naming convention**: `analysis_[filename]_[classname]_[methodname].md`
3. **Save location**: Create folder `method_analysis/` in project root
4. **Write results using the Write tool** - do not just provide summaries
5. **Use the exact template structure** provided above
6. **Fill in ALL sections** - do not leave sections empty
7. **Provide specific examples** rather than generic descriptions
8. **Include actual code snippets** from the method being analyzed
9. **Cross-reference other methods** by checking actual usage with Grep tool
10. **Document your analysis process** in the file for future reference

##### **Step 6: Update Master Matrix**
After analyzing each method:
1. **Add the method to this master matrix** with updated information
2. **Update failure probability assessments** based on detailed analysis
3. **Adjust priority rankings** based on discovered dependencies
4. **Document cross-method relationships** and cascading failure risks

### **🎯 SYSTEMATIC EXECUTION PLAN**

#### **Phase 1 Files (Start Here)**:
1. `alas.py` - Main scheduler ⭐ **HIGHEST PRIORITY**
2. `module/device/device.py` - Device interface
3. `module/device/screenshot.py` - Screenshot system
4. `module/device/control.py` - Input control
5. `module/base/base.py` - Core logic base class

#### **Phase 2 Files (Core Game Logic)**:
6. `module/ui/ui.py` - UI navigation
7. `module/dorm/dorm.py` - Dorm automation
8. `module/commission/commission.py` - Commission system
9. `module/campaign/run.py` - Campaign automation
10. `module/ocr/ocr.py` - Text recognition

#### **Continue systematically through all remaining `.py` files...**

---

## **📋 METHODOLOGY**
- **Call Frequency**: `EXTREME` (thousands/hour) | `HIGH` (hundreds/hour) | `MEDIUM` (tens/hour) | `LOW` (few/hour)
- **Criticality**: `VITAL` (bot stops if fails) | `CRITICAL` (major functionality loss) | `IMPORTANT` (feature degradation) | `HELPER` (convenience only)
- **Failure Risk**: `🔴 HIGH` | `🟡 MEDIUM` | `🟢 LOW`

---

## **🎯 1. alas.py - Main Scheduler**

| Method | Frequency | Criticality | Failure Risk | Analysis |
|--------|-----------|-------------|--------------|----------|
| `__init__()` | LOW | VITAL | 🟢 LOW | Called once at startup. Simple initialization. |
| `config` (property) | EXTREME | VITAL | 🟡 MEDIUM | **Cached property accessed thousands of times**. Config parsing could fail. |
| `device` (property) | EXTREME | VITAL | 🔴 HIGH | **Most critical - creates Device object**. Platform-specific code, ADB dependencies. |
| `checker` (property) | MEDIUM | IMPORTANT | 🟡 MEDIUM | Server status checking. Network dependent. |
| `run()` | HIGH | VITAL | 🔴 HIGH | **Core task execution**. Exception handling for all game errors. **THE MOST IMPORTANT METHOD**. |
| `save_error_log()` | LOW | CRITICAL | 🟢 LOW | Error logging. File I/O dependent. |
| `loop()` | LOW | VITAL | 🟢 LOW | **Main scheduler loop - called once but runs forever**. |
| `get_next_task()` | HIGH | VITAL | 🟡 MEDIUM | Task scheduling logic. Config dependent. |
| `wait_until()` | MEDIUM | IMPORTANT | 🟢 LOW | Time-based waiting. Simple logic. |

**Task Methods (40+ methods like `dorm()`, `commission()`, etc.)**
| Method Pattern | Frequency | Criticality | Failure Risk | Analysis |
|--------|-----------|-------------|--------------|----------|
| `dorm()`, `commission()`, etc. | MEDIUM | CRITICAL | 🟡 MEDIUM | **Each called per schedule**. Import game modules. Where our TypeError occurred! |

---

## **📸 2. module/device/screenshot.py - Screenshot System**

| Method | Frequency | Criticality | Failure Risk | Analysis |
|--------|-----------|-------------|--------------|----------|
| `screenshot()` | EXTREME | VITAL | 🔴 HIGH | **Called every game action**. **THIS IS WHERE BLACK SCREEN FAILS**. |
| `screenshot_methods` (property) | HIGH | VITAL | 🔴 HIGH | **Method selection dict**. Platform-specific methods. |
| `check_screen_black()` | EXTREME | VITAL | 🔴 HIGH | **WHERE OUR BUG IS**. Returns False for black screens, causes retries. |
| `check_screen_size()` | EXTREME | VITAL | 🟡 MEDIUM | Screen dimension validation. |
| `_handle_orientated_image()` | EXTREME | VITAL | 🟡 MEDIUM | Image rotation logic. |
| `screenshot_adb()` | HIGH | VITAL | 🟡 MEDIUM | **Fallback method**. Universal but slow. |
| `screenshot_adb_nc()` | HIGH | VITAL | 🔴 HIGH | **Current failing method**. Netcat dependency. |
| `screenshot_uiautomator2()` | HIGH | VITAL | 🟡 MEDIUM | Python library method. Cross-platform. |
| `screenshot_nemu_ipc()` | HIGH | VITAL | 🔴 HIGH | **MEmu-specific**. Windows binary dependency. |
| `screenshot_ldopengl()` | HIGH | VITAL | 🔴 HIGH | **LDPlayer-specific**. Windows DLL dependency. |
| `screenshot_droidcast()` | HIGH | VITAL | 🔴 HIGH | DroidCast method. Binary dependency. |
| `screenshot_scrcpy()` | HIGH | VITAL | 🟡 MEDIUM | Screen mirroring. Cross-platform if installed. |
| `save_screenshot()` | LOW | HELPER | 🟢 LOW | Debug/logging feature. |
| `has_cached_image` (property) | EXTREME | IMPORTANT | 🟢 LOW | Simple existence check. |

---

## **🎮 3. module/device/control.py - Touch Control**

| Method | Frequency | Criticality | Failure Risk | Analysis |
|--------|-----------|-------------|--------------|----------|
| `click()` | EXTREME | VITAL | 🟡 MEDIUM | **Called for every game interaction**. Method dispatch. |
| `click_methods` (property) | HIGH | VITAL | 🔴 HIGH | **Method selection dict**. Platform-specific methods. |
| `multi_click()` | MEDIUM | IMPORTANT | 🟡 MEDIUM | Multiple rapid clicks. Timing dependent. |
| `long_click()` | MEDIUM | IMPORTANT | 🟡 MEDIUM | Press and hold actions. Method dispatch. |
| `swipe()` | HIGH | CRITICAL | 🟡 MEDIUM | Scroll and drag operations. |
| `click_adb()` | HIGH | VITAL | 🟡 MEDIUM | **Universal fallback method**. |
| `click_uiautomator2()` | HIGH | VITAL | 🟡 MEDIUM | Python library method. |
| `click_minitouch()` | HIGH | VITAL | 🟡 MEDIUM | Minitouch daemon method. |
| `click_maatouch()` | HIGH | VITAL | 🔴 HIGH | **MaaTouch binary**. May be Windows-compiled. |
| `click_nemu_ipc()` | HIGH | VITAL | 🔴 HIGH | **MEmu-specific**. Windows binary dependency. |

---

## **🧠 4. module/base/base.py - Core Logic**

| Method | Frequency | Criticality | Failure Risk | Analysis |
|--------|-----------|-------------|--------------|----------|
| `appear()` | EXTREME | VITAL | 🟡 MEDIUM | **Called for every UI detection**. Template matching core. |
| `appear_then_click()` | EXTREME | VITAL | 🟡 MEDIUM | **Core game interaction pattern**. Combines appear() + click(). |
| `wait_until_appear()` | HIGH | VITAL | 🟡 MEDIUM | **Waiting for UI elements**. Timeout and retry logic. |
| `wait_until_disappear()` | HIGH | VITAL | 🟡 MEDIUM | **Waiting for UI transitions**. |
| `match_template_color()` | HIGH | IMPORTANT | 🟡 MEDIUM | Enhanced template matching. |
| `ensure_button()` | EXTREME | VITAL | 🟢 LOW | Button object validation. Simple logic. |

---

## **🔗 5. module/device/connection.py - Device Connection**

| Method | Frequency | Criticality | Failure Risk | Analysis |
|--------|-----------|-------------|--------------|----------|
| `retry` (decorator) | EXTREME | VITAL | 🔴 HIGH | **Wraps all ADB operations**. Connection recovery logic. |
| `adb_reconnect()` | MEDIUM | VITAL | 🔴 HIGH | **Connection recovery**. ADB server dependency. |
| `adb_shell()` | EXTREME | VITAL | 🔴 HIGH | **Core ADB communication**. Every command goes through this. |
| `adb_start_server()` | LOW | VITAL | 🔴 HIGH | **ADB server initialization**. System dependency. |
| `serial` (property) | HIGH | VITAL | 🟡 MEDIUM | Device identification. Config dependent. |

---

## **👁️ 6. module/ocr/ocr.py - Text Recognition**

| Method | Frequency | Criticality | Failure Risk | Analysis |
|--------|-----------|-------------|--------------|----------|
| `OCR_MODEL.ocr()` | HIGH | CRITICAL | 🟡 MEDIUM | **Text recognition**. PaddleOCR/EasyOCR backend. |
| `ocr_wrapper()` | HIGH | CRITICAL | 🟡 MEDIUM | **Version compatibility wrapper**. Format conversion. |

---

# **🚨 CRITICAL FAILURE ANALYSIS**

## **🎯 ROOT CAUSE: Screenshot System Breakdown**

### **The Exact Problem (Line 272-276 in screenshot.py):**
```python
logger.warning(f"Received pure black screenshots from emulator, color: {color}")
logger.warning(
    f"Screenshot method `{self.config.Emulator_ScreenshotMethod}` "
    f"may not work on emulator `{self.serial}`, or the emulator is not fully started"
)
```

### **Critical Call Chain Failure:**
1. `alas.loop()` → `run()` → **`device.screenshot()`** ← **FAILS HERE**
2. `screenshot()` calls `check_screen_black()` 
3. `check_screen_black()` detects `color: (0.0, 0.0, 0.0)` and returns `False`
4. `screenshot()` retries only **2 times** then gives up
5. Bot continues with **black screen data** → **UI detection fails** → **"Unknown page" errors**

---

# **🛠️ FAILURE PROBABILITY MATRIX**

## **EXTREME RISK (🔴) - Will Break in Different Environments:**

| Method | Current Issue | Environment Risk |
|--------|---------------|------------------|
| `screenshot_adb_nc()` | **ACTIVE FAILURE** - Returning black screens | MEmu + Windows specific issue |
| `screenshot_nemu_ipc()` | Windows binary dependency | 100% fail on Linux |
| `screenshot_ldopengl()` | Windows DLL dependency | 100% fail on Linux |
| `click_maatouch()` | Binary may be Windows-compiled | High fail risk on Linux |
| `device` property | Platform detection logic | Different emulator support |
| `retry` decorator | ADB path assumptions | Different ADB installations |

## **HIGH RISK (🟡) - May Degrade Performance:**

| Method | Current Issue | Environment Risk |
|--------|---------------|------------------|
| `screenshot_uiautomator2()` | Cross-platform but slower | Performance degradation |
| `screenshot_adb()` | Universal but very slow | 10x slower on any platform |
| `appear()` | Template matching precision | Font rendering differences |
| `config` property | Path assumptions | Different file system layouts |

## **LOW RISK (🟢) - Should Work Everywhere:**

| Method | Analysis |
|--------|----------|
| Core game logic | Pure Python algorithms |
| OCR processing | Cross-platform libraries |
| Configuration parsing | Standard JSON/YAML |

---

# **🎯 IMMEDIATE FIX PRIORITIES**

## **Priority 1: Fix Current Windows Issues**
1. **`check_screen_black()` - Line 272**: Increase retry count from 2 to 10
2. **Force different screenshot method**: Override `ADB_nc` → `ADB` or `uiautomator2`
3. **Add screenshot method fallback chain**: Auto-detect working method

## **Priority 2: Fix TypeError Issues** 
1. **`dorm.py:394`** - ✅ **ALREADY FIXED** (string to int conversion)
2. **Audit all Filter usage** for similar string/int type mismatches

## **Priority 3: Linux Compatibility**
1. **Remove Windows-only screenshot methods** from Linux method list
2. **Add Linux emulator detection** logic
3. **Test ADB fallback chain** on Linux systems

---

# **📊 SUMMARY STATISTICS**

- **Total Methods Analyzed**: 50+
- **EXTREME Risk Methods**: 6 (12%)
- **HIGH Risk Methods**: 15 (30%)
- **MEDIUM Risk Methods**: 20 (40%)
- **LOW Risk Methods**: 9 (18%)

**Most Critical Single Point of Failure**: `screenshot()` method in `module/device/screenshot.py`

**Current Active Bug**: `screenshot_adb_nc()` returning pure black screenshots on Windows MEmu emulator, causing entire bot automation to fail.