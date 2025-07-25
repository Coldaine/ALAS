# 🚀 ALAS Production Readiness Task - Deep Code Tracing & Verification

## Context
You are working on the ALAS (AzurLaneAutoScript) codebase which has undergone significant analysis. The previous work includes:
- Comprehensive method analysis in `ALAS_Method_Analysis_Matrix.md` 
- 11 detailed method analyses in the `method_analysis/` folder
- Identified critical bugs, particularly the screenshot retry issue (only 2 retries on black screen)
- New PaddleOCR v3 wrappers added but not integrated

## Your Mission
Make ALAS production-ready through exhaustive code tracing and verification, creating a test suite so comprehensive that live testing becomes unnecessary.

## Required Reading
1. **Start with**: `ALAS_Method_Analysis_Matrix.md` - Contains the systematic analysis framework and critical failure points
2. **Deep dive into**: All files in `method_analysis/` folder - Detailed breakdowns of each critical method
3. **Review**: `CLAUDE.md` - Project-specific instructions and current status
4. **Audit existing tests**: Review all test files and document which ones are "smoke tests" (only verify code runs) vs actual behavioral tests

## PRIMARY TASK: Deep Method Tracing

For each **VITAL** method identified in the analysis matrix, you must:

### 1. Create a Trace Document
Create `method_trace/trace_[class]_[method].md` with:
```markdown
# Method Trace: [ClassName].[method_name]()

## Execution Path
1. Entry point: [where this gets called]
2. Step 1: [what happens first]
   - Code: `specific line of code`
   - Purpose: [why this step exists]
   - Inputs: [what data comes in]
   - Outputs: [what data goes out]
   - Side effects: [what state changes]
3. Step 2: [continue for every line]
...

## Branch Analysis
- If condition X: [trace this path]
- Else: [trace alternate path]

## Exception Paths
- Exception Type 1: [full trace of error handling]
- Exception Type 2: [continue for each]

## External Calls
- Call to method_a(): [trace into this method too]
- Call to method_b(): [document expected behavior]
```

### 2. Create Step-by-Step Test Code
For EACH step in the trace, create a test that:
- Sets up the exact state before the step
- Executes just that step (may require refactoring)
- Verifies the output/state change
- Documents what the output actually was

Example:
```python
def test_screenshot_step_1_interval_wait():
    """Test that screenshot waits for interval before capturing"""
    # Setup
    mock_interval = Mock()
    mock_interval.wait.return_value = None
    
    # Execute single step
    screenshot_obj._screenshot_interval = mock_interval
    # ... execute just the wait step
    
    # Verify
    mock_interval.wait.assert_called_once()
    
    # Document actual behavior
    """
    ACTUAL OUTPUT: 
    - wait() called with no arguments
    - No return value
    - No state changes except internal timer
    """
```

### 3. Create Integration Tests Between Steps
Test how data flows between steps:
```python
def test_screenshot_flow_wait_to_capture():
    """Test data flow from interval wait to method selection"""
    # Document how state from step 1 affects step 2
    # Test with various states
```

## Critical Methods to Trace (Priority Order)

1. **Screenshot.screenshot()** - The most critical failure point
   - Trace all 9 steps in the retry loop
   - Trace into EVERY screenshot method (adb, adb_nc, etc.)
   - Document exact failure modes

2. **Device.__init__()** - Complex initialization
   - Trace all 4 retry attempts
   - Trace parent class initialization
   - Document platform-specific branches

3. **AzurLaneAutoScript.run()** - Task execution
   - Trace all 10 exception handlers
   - Document recovery strategies
   - Trace into actual task methods

4. **Device.stuck_record_check()** - Timeout detection
   - Trace timer logic
   - Document all branches
   - Test with various timer states

## Test Quality Requirements

### Replace Smoke Tests
Find tests that only verify "code doesn't crash" and replace with:
- Tests that verify actual behavior
- Tests that check state changes
- Tests that validate output correctness

### Document Test Gaps
Create `test_gaps.md` listing:
- Methods with no tests
- Methods with only smoke tests
- Edge cases not covered
- Platform-specific code not tested

## Fix Implementation with Verification

When implementing fixes (like the screenshot retry):

1. **Before Fix**: 
   - Create tests showing current broken behavior
   - Document exact failure mode
   
2. **After Fix**:
   - Create tests proving fix works
   - Test edge cases around the fix
   - Document performance impact

## Deliverables

1. **Method Trace Documents**: Complete traces for all VITAL methods
2. **Step Tests**: Individual tests for each step in critical methods  
3. **Integration Tests**: Tests showing how steps connect
4. **Test Gap Analysis**: Document showing test coverage reality
5. **Fix Verification**: Before/after tests for each fix
6. **Behavioral Test Suite**: Replace smoke tests with real behavioral tests

## Approach Guidelines

- **NO ASSUMPTIONS**: Trace what the code ACTUALLY does, not what you think it does
- **Document EVERYTHING**: Every return value, every state change
- **Test ISOLATION**: Each step should be testable in isolation
- **Mock MINIMALLY**: Only mock external dependencies, not internal methods
- **VERIFY OUTPUT**: Don't just check if methods were called, verify what they produced

## Success Criteria

The test suite should be so comprehensive that:
1. Any developer can understand exactly how each method works from the tests
2. Any change that breaks behavior will cause test failures
3. No emulator is needed to verify the code works correctly
4. Each critical path through the code has documented expected outputs

## Getting Started

1. Begin by reading all the method analysis documents
2. Create the `method_trace/` directory
3. Start with `Screenshot.screenshot()` as it's the most critical
4. For each line of code, write a test before moving to the next
5. Document surprises - where the code doesn't do what you expected
6. Build up a library of test utilities as you go

Remember: The goal is to understand the code so deeply through testing that live testing becomes redundant. Every edge case, every error path, every state change should be captured in tests.