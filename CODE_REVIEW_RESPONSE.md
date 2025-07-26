# Code Review: Action Screenshot Archiving and Logging System

## 1. Executive Summary

This is a solid implementation that successfully addresses the core requirements of improving debuggability through session-based logging and action-based screenshot archiving.

-   **Logging**: The move to unique, timestamped log files per session is well-executed and a significant improvement. It correctly modifies `logger.py`, `alas.py`, and `process_manager.py` to create a clean, robust logging system that eliminates the previous issue of commingled logs.
-   **Screenshot Archiving**: The concept is excellent for debugging. It provides invaluable context for understanding the bot's state before each action. However, the current implementation has **critical performance and storage implications** that must be addressed. It is always on, writes files synchronously, and lacks any storage management.
-   **Overall**: The changes are highly beneficial, but the archiving feature requires refinement to be suitable for general use. The logging fix is production-ready.

---

## 2. Review Criteria Analysis

### 2.1. Correctness

-   **Screenshot Archiving**: It works, but the use of the last cached image (`self.image`) could be stale if an action is performed long after a screenshot. This is a minor issue for debugging but worth noting. The filename sanitization is insufficient and could lead to errors on certain button names.
-   **Logging System**: **Excellent.** The use of a timestamp in `logger.py` (`%Y%m%d_%H%M%S`) effectively creates unique log files. The removal of the `clear_on_start` parameter simplifies the logic correctly.
-   **Regex Pattern**: The pattern `[A-Z]-\d{3}-[A-Z]{2}` in `project.py` is **correct** for the described format and is a good, robust way to handle verbose LLM output.

### 2.2. Performance Impact

-   **CRITICAL**: Saving a screenshot on every action (`click`, `swipe`, etc.) is a synchronous I/O operation. This will add significant latency (50-500ms+) to every action, noticeably slowing down the bot, especially on machines with slower HDDs or SD cards.
-   **Recommendation**: File I/O should be offloaded to a non-blocking background thread. The main thread should only add the image to a queue. For a debugging feature, consider using JPEG instead of PNG to reduce file size and write time.

### 2.3. Error Handling

-   **Disk Full**: There is no error handling for a "disk full" scenario. An `OSError` would likely be raised and, if unhandled, would crash the bot.
-   **I/O Errors**: The `save_image` call is not wrapped in a `try...except` block. Any file permission errors, invalid path characters, or other `IOError` exceptions will be unhandled.
-   **Recommendation**: Wrap the file-saving logic in a `try...except` block to catch potential I/O errors and log them as warnings without crashing the bot.

### 2.4. Code Quality

-   **DRY Violation**: The call to `self.archive_action_screenshot(...)` is repeated in `click()`, `long_click()`, `swipe()`, and `drag()` in `module/device/control.py`. This could be refactored into a decorator or a single helper method.
-   **Redundant Code**: `module/device/screenshot.py` contains **two different implementations** of `archive_action_screenshot()`. Python's Method Resolution Order will use the second one, but the first one (which includes a disabled config check) is confusing and should be removed or merged.

### 2.5. Thread Safety

-   The file I/O itself is not explicitly thread-safe. While ALAS's main loop is largely single-threaded, `os.makedirs(..., exist_ok=True)` helps prevent race conditions on directory creation. If multiple actions were ever threaded, there could be issues. Using a single-consumer background thread for writing would solve this.

### 2.6. Storage Management

-   **Unbounded Growth**: The system will accumulate screenshots indefinitely. For a bot running hundreds of actions per session, this will consume a large amount of disk space very quickly (potentially gigabytes per week).
-   **Recommendation**: Implement an automatic cleanup strategy. This is essential for a feature like this.
    1.  **Cleanup by Age**: Delete archives older than a configurable number of days (e.g., 3-7 days).
    2.  **Cleanup by Size**: Limit the total size of the archive folder and delete the oldest files when the limit is exceeded.

### 2.7. Integration Issues

-   The feature will work correctly with all screenshot methods because it operates on the cached `self.image`.
-   The duplicate method definition in `screenshot.py` is a self-inflicted integration conflict that needs to be resolved.

---

## 3. Answers to Specific Questions

1.  **Stale `self.image`?**
    > Yes, this is a valid concern. The screenshot may not be "fresh." The ideal solution is to take a new screenshot right before archiving, but this would double the performance cost. The current trade-off is acceptable for a debugging tool, but the behavior should be documented.

2.  **Timestamp with milliseconds?**
    > Yes, this is good practice. The action archive already does this correctly. For the main log file in `logger.py`, adding `%f` to the timestamp format would provide more granularity and prevent rare collisions.

3.  **Button name sanitization sufficient?**
    > No. It only handles `\`, `/`, and space. It will fail on other invalid filename characters like `:`, `*`, `?`, `"`, `<`, `>`, `|`. A more robust sanitization function is needed.

4.  **Config option to disable?**
    > **Absolutely essential.** This is the most critical missing piece. This feature should be **disabled by default** and only enabled by users for debugging purposes.

5.  **Regex pattern `[A-Z]-\d{3}-[A-Z]{2}` coverage?**
    > Yes, this pattern appears to be correct and robust for all research codes that follow the specified format.

---

## 4. High-Priority Recommendations & Proposed Changes

The following changes are recommended to make the feature production-ready.

### 1. Make Archiving Optional and Configurable

The feature must be disabled by default.

### 2. Merge Duplicate Methods and Improve Implementation

Combine the two `archive_action_screenshot` methods in `module/device/screenshot.py` into one, and add robust sanitization and error handling.

**Proposed Change (`module/device/screenshot.py`)**

```python
-    def archive_action_screenshot(self, action_name="unknown"):
-        """
-        Archives the current screenshot before an action is taken, if enabled in config.
-        This is useful for debugging and understanding the bot's behavior.
-        Saves to 'action_archive/<action_name>/<timestamp>.png'.
-
-        Args:
-            action_name (str): Name of the action being taken, e.g. 'click', 'swipe'.
-        """
-        if not self.config.get('Debug.ArchiveActionScreenshot', False):
-            return
-        if not self.has_cached_image:
-            logger.warning("archive_action_screenshot: No cached image to save.")
-            return
-
-        now = time.time()
-        file = f"{int(now * 1000)}.png"
-
-        folder = os.path.join(self.config.DropRecord_SaveFolder, "action_archive", action_name)
-        os.makedirs(folder, exist_ok=True)
-
-        file_path = os.path.join(folder, file)
-        self.image_save(file_path)
-        logger.debug(f"Archived action screenshot to: {file_path}")
-
-    def archive_action_screenshot(self, action_name="unknown", button_name=""):
+    def archive_action_screenshot(self, action_name="unknown", button_name=""):
         """
         Archives the current screenshot before an action is taken.
         This is useful for debugging and understanding the bot's behavior.
         Saves to 'log/action_archive/<date>/<action_name>/<timestamp>_<button>.png'.
 
         Args:
             action_name (str): Name of the action being taken, e.g. 'click', 'swipe'.
             button_name (str): Name of the button or element being interacted with.
         """
-        # Always archive - no config check needed
-        
-        # Ensure we have an image to save
-        if not hasattr(self, 'image') or self.image is None:
+        # This feature is for debugging and is disabled by default.
+        if not self.config.get('Debug.EnableActionArchiving', False):
+            return
+
+        if not self.has_cached_image:
             logger.warning("archive_action_screenshot: No image to save.")
             return
 
         now = time.time()
         timestamp = datetime.fromtimestamp(now).strftime("%Y%m%d_%H%M%S_%f")[:-3]
         date_folder = datetime.fromtimestamp(now).strftime("%Y-%m-%d")
         
-        # Clean button name for filename
-        button_clean = str(button_name).replace('/', '_').replace('\\', '_').replace(' ', '_')
+        # Sanitize button name for use in a filename.
+        # Removes invalid characters and limits length.
+        import re
+        button_clean = re.sub(r'[\\/*?:"<>|]',"", str(button_name))
+        button_clean = button_clean.replace(' ', '_')
+        button_clean = button_clean[:50] # Limit length to avoid issues
+
         if button_clean:
             file = f"{timestamp}_{button_clean}.png"
         else:
             file = f"{timestamp}.png"
 
-        # Create folder structure
-        folder = os.path.join("./log/action_archive", date_folder, action_name)
-        os.makedirs(folder, exist_ok=True)
-
-        file_path = os.path.join(folder, file)
-        save_image(self.image, file_path)
-        logger.debug(f"Archived action screenshot: {action_name} @ {button_name} -> {file_path}")
+        try:
+            # Create folder structure
+            folder = os.path.join("./log/action_archive", date_folder, action_name)
+            os.makedirs(folder, exist_ok=True)
+
+            file_path = os.path.join(folder, file)
+            save_image(self.image, file_path)
+            logger.debug(f"Archived action screenshot: {action_name} @ {button_name} -> {file_path}")
+        except Exception as e:
+            logger.warning(f"Failed to archive action screenshot: {e}")

```
This updated method is now configurable, has robust filename sanitization, includes error handling, and removes the confusing duplicate code. The next step would be to ensure the configuration default is set to `false`.
