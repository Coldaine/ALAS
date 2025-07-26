# ALAS Bot Mechanics & Strategies

This document details the inner workings of ALAS (AzurLaneAutoScript) bot, including configuration options, strategies, and implementation details.

## Table of Contents
- [Configuration System](#configuration-system)
- [Dorm Module](#dorm-module)
- [Exercise (PvP) Module](#exercise-pvp-module)
- [Action Screenshot Archiving](#action-screenshot-archiving)
- [Logging System](#logging-system)

---

## Configuration System

### Architecture
The ALAS configuration system consists of three main components:

1. **`module/config/config.py`**: Core configuration manager
   - Handles loading, binding, and scheduling tasks
   - Implements task priority and scheduling logic
   - Dynamically binds configuration values to the active task

2. **`config/template.json`**: Master template
   - Contains all possible settings with defaults
   - Defines the structure for all modules

3. **`config/alas.json`**: Active configuration
   - User-specific settings
   - Overrides template defaults

### Task Scheduling
- Each task has `SuccessInterval` and `FailureInterval` (in minutes)
- Tasks can have specific `ServerUpdate` times (e.g., "00:00, 12:00, 18:00")
- The scheduler determines next task based on:
  - Enabled status
  - Next run time
  - Priority when multiple tasks are ready

### Key Features
- **Hot-reloading**: Config changes are detected automatically
- **Dynamic binding**: Config values are attached based on active task
- **Multi-task support**: Can schedule and manage dozens of different tasks

---

## Dorm Module

### Purpose
Automates dorm management for passive morale recovery and resource collection.

### Configuration Options

#### Dorm Settings
- **`Dorm_Collect`** (boolean): 
  - Automatically collect coins and hearts from the dorm
  - Default: `true`

- **`Dorm_Feed`** (boolean): 
  - Automatically feed ships to maintain morale
  - Default: `true`

- **`Dorm_FeedFilter`** (string): 
  - Priority order for food usage
  - Default: `"20000 > 10000 > 5000 > 3000 > 2000 > 1000"`
  - Uses highest value food first to minimize clicks

#### BuyFurniture Settings
- **`BuyFurniture_Enable`** (boolean): 
  - Auto-purchase furniture from shop
  - Default: `false`

- **`BuyFurniture_BuyOption`** (string):
  - `"all"`: Buy all available furniture
  - `"set"`: Buy only furniture sets
  - Default: `"all"`

### Important Notes
- **No Ship Rotation**: The dorm module does NOT rotate ships in/out
- **Morale Management**: Only feeds to maintain morale, doesn't optimize ship placement
- **Schedule**: Runs every 278 minutes (~4.6 hours) by default

### Implementation Details
- Uses long-tap for feeding (requires specific control methods)
- Falls back to multi-click if long-tap not supported
- Prioritizes expensive food to reduce interaction count

---

## Exercise (PvP) Module

### Purpose
Automates PvP battles with sophisticated timing strategies for rank optimization.

### Configuration Options

#### Exercise Settings

- **`Exercise_OpponentChooseMode`** (string):
  - `"max_exp"`: Choose opponent with highest average level
  - `"easiest"`: Choose weakest opponent (by level/power calculation)
  - `"leftmost"`: Always choose first opponent in list
  - `"easiest_else_exp"`: Try easiest first, if fails then max XP
  - Default: `"max_exp"`

- **`Exercise_OpponentTrial`** (integer):
  - Number of attempts per opponent before giving up
  - Default: `1`

- **`Exercise_ExerciseStrategy`** (string):
  - `"aggressive"`: Use all attempts immediately
  - `"fri18"`: Save 5 attempts for Friday 18:00
  - `"sat0"`: Save 5 attempts for Saturday 00:00
  - `"sat12"`: Save 5 attempts for Saturday 12:00
  - `"sat18"`: Save 5 attempts for Saturday 18:00
  - `"sun0"`: Save 5 attempts for Sunday 00:00
  - `"sun12"`: Save 5 attempts for Sunday 12:00
  - `"sun18"`: Save 5 attempts for Sunday 18:00
  - Default: `"aggressive"`

- **`Exercise_LowHpThreshold`** (float):
  - HP percentage to retreat (0.4 = 40%)
  - Default: `0.4`

- **`Exercise_LowHpConfirmWait`** (float):
  - Time to wait before confirming low HP retreat
  - Default: `0.1` seconds

### Admiral Trial Strategy

#### How Admiral Trials Work
- Exercise periods reset every 2 weeks
- Admiral trials occur at specific times before reset
- During trials, rank point gains/losses are increased
- Higher ranked opponents give more points

#### Strategy Implementation
```python
ADMIRAL_TRIAL_HOUR_INTERVAL = {
    "sun18": [6, 0],      # 6-0 hours before reset
    "sun12": [12, 6],     # 12-6 hours before reset
    "sun0": [24, 12],     # 24-12 hours before reset
    "sat18": [30, 24],    # 30-24 hours before reset
    "sat12": [36, 30],    # 36-30 hours before reset
    "sat0": [48, 36],     # 48-36 hours before reset
    "fri18": [56, 48],    # 56-48 hours before reset
}
```

#### Strategy Logic
1. **Aggressive Mode**:
   - Uses all exercise attempts immediately
   - No preservation for admiral trials

2. **Timed Strategies**:
   - Preserves 5 exercise attempts
   - Only uses them during specified admiral trial window
   - Always depletes if <6 hours remain (prevents waste)

### Opponent Selection Issues

#### Current Implementation Flaws
The "max_exp" mode uses a simplistic calculation:
```python
priority = np.sum(self.level) / 6  # Average level
```

**Problems**:
- Assumes XP correlates with level (incorrect for PvP)
- Doesn't consider actual rank differences
- Ignores that rank points depend on rank differential

#### Optimal Strategy (Not Implemented)
The best approach would be:
1. Always choose leftmost (highest ranked) opponents
2. Wait for opponents to climb in rank
3. Battle them when rank differential is maximized

### Schedule
- Runs at exercise reset times: 00:00, 12:00, 18:00
- With timed strategies, checks but preserves attempts

---

## Action Screenshot Archiving

### Purpose
Automatically saves screenshots before every bot action for debugging.

### Features
- **Location**: `log/action_archive/<date>/<action>/<timestamp>_<button>.png`
- **Always Enabled**: No configuration needed
- **Zero Performance Impact**: Uses async background thread
- **Auto-cleanup**: Removes archives older than 7 days on startup

### Technical Implementation
```python
# Async queue-based system
class Screenshot:
    _archive_queue = queue.Queue()
    _archive_thread = threading.Thread(target=_archive_worker, daemon=True)
    
    def archive_action_screenshot(self, action_name, button_name):
        # Queue screenshot for background save
        self._archive_queue.put((self.image.copy(), file_path))
```

### Benefits
- Debug bot decisions by seeing what it saw
- Understand stuck situations
- Verify OCR readings
- Track bot behavior over time

---

## Logging System

### Session-Based Logging
Each ALAS session creates a unique log file:
- **Format**: `log/YYYY-MM-DD_HHMMSS_<config_name>.txt`
- **Example**: `log/2025-07-26_143052_alas.txt`

### Features
- **No Overwrites**: Each session gets unique timestamped file
- **Clean Separation**: Easy to find logs for specific runs
- **Dual Systems**: 
  - `/log/` - Main operational logs (useful)
  - `/logs/` - Vision/LLM logs (less useful for debugging)

### Implementation
```python
# Create unique log file for each session
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"./log/{datetime.date.today()}_{timestamp}_{name}.txt"
```

---

## Common Strategies & Tips

### Resource Collection Setup
For passive resource collection:
1. Enable: Commission, Tactical, Research, Dorm, Guild, Reward
2. Disable: All combat tasks, Exercise, Gacha
3. Set appropriate intervals (30-60 min for most)

### PvP Optimization
1. Use "leftmost" opponent selection
2. Consider timed strategies for admiral trials
3. Monitor win rates - adjust strategy if losing too much

### Debugging
1. Check timestamped logs for each session
2. Review action archives to see bot decisions
3. Enable debug logging for detailed traces

---

## Future Improvements Needed

1. **Exercise Module**:
   - Implement proper rank-based opponent selection
   - Add waiting strategy for rank climbing
   - Consider win rate in selection

2. **Dorm Module**:
   - Add ship rotation for optimal morale management
   - Implement comfort optimization

3. **General**:
   - Better error recovery mechanisms
   - More sophisticated scheduling algorithms
   - Enhanced OCR with LLM fallbacks