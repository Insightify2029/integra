"""
Desktop Automation Engine
=========================
Desktop application automation using OS-native APIs.

Windows: Win32 API (pywin32), UI Automation
Linux: xdotool, wmctrl, D-Bus

Features:
- Window management (find, focus, minimize, maximize, close)
- Application launching and monitoring
- Keystroke and mouse simulation
- Clipboard operations
- Screenshot capture
- Process management
- Workflow automation (sequential actions)
"""

import os
import sys
import time
import json
import subprocess
import platform
from enum import Enum
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field

from core.logging import app_logger


# ═══════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════

class WindowState(Enum):
    """Window state."""
    NORMAL = "normal"
    MINIMIZED = "minimized"
    MAXIMIZED = "maximized"
    HIDDEN = "hidden"


class ActionType(Enum):
    """Automation action types."""
    LAUNCH_APP = "launch_app"
    FOCUS_WINDOW = "focus_window"
    CLOSE_WINDOW = "close_window"
    MINIMIZE_WINDOW = "minimize_window"
    MAXIMIZE_WINDOW = "maximize_window"
    KEYSTROKE = "keystroke"
    TYPE_TEXT = "type_text"
    CLICK = "click"
    WAIT = "wait"
    CLIPBOARD_COPY = "clipboard_copy"
    CLIPBOARD_PASTE = "clipboard_paste"
    SCREENSHOT = "screenshot"
    RUN_COMMAND = "run_command"


@dataclass
class WindowInfo:
    """Information about a desktop window."""
    handle: int = 0
    title: str = ""
    class_name: str = ""
    process_id: int = 0
    process_name: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    state: WindowState = WindowState.NORMAL
    is_visible: bool = True


@dataclass
class AutomationAction:
    """A single automation action."""
    action_type: ActionType
    params: dict = field(default_factory=dict)
    delay_after: float = 0.5  # seconds
    description: str = ""
    result: str = ""
    success: bool = False


@dataclass
class AutomationWorkflow:
    """A sequence of automation actions."""
    name: str
    description: str = ""
    actions: list = field(default_factory=list)
    created_at: str = ""
    last_run: str = ""
    run_count: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


# ═══════════════════════════════════════════════════════
# Platform Detection
# ═══════════════════════════════════════════════════════

IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform.startswith('linux')
IS_MAC = sys.platform == 'darwin'


# ═══════════════════════════════════════════════════════
# Desktop Automation Engine
# ═══════════════════════════════════════════════════════

class DesktopAutomation:
    """
    Cross-platform desktop automation engine.

    Provides:
    - Window management (find, focus, minimize, maximize, close)
    - Application launching and monitoring
    - Keyboard and mouse simulation
    - Clipboard operations
    - Screenshot capture
    - Workflow automation
    """

    def __init__(self, config_path: str = ""):
        self._config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))),
            "config", "automation_config.json"
        )
        self._workflows: list[AutomationWorkflow] = []
        self._app_paths: dict[str, str] = {}
        self._action_log: list[dict] = []
        self._is_windows = IS_WINDOWS
        self._is_linux = IS_LINUX

        self._load_config()

        app_logger.info(
            f"Desktop Automation initialized (platform: {platform.system()})"
        )

    # ─── Configuration ───────────────────────────────

    def _load_config(self):
        """Load configuration from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self._app_paths = config.get("app_paths", {})

                for wf in config.get("workflows", []):
                    actions = []
                    for a in wf.get("actions", []):
                        actions.append(AutomationAction(
                            action_type=ActionType(a["action_type"]),
                            params=a.get("params", {}),
                            delay_after=a.get("delay_after", 0.5),
                            description=a.get("description", ""),
                        ))
                    workflow = AutomationWorkflow(
                        name=wf["name"],
                        description=wf.get("description", ""),
                        actions=actions,
                    )
                    self._workflows.append(workflow)

                app_logger.debug("Automation config loaded")
            except Exception as e:
                app_logger.error(f"Error loading automation config: {e}")

    def save_config(self):
        """Save configuration to file."""
        workflows = []
        for wf in self._workflows:
            actions = []
            for a in wf.actions:
                actions.append({
                    "action_type": a.action_type.value,
                    "params": a.params,
                    "delay_after": a.delay_after,
                    "description": a.description,
                })
            workflows.append({
                "name": wf.name,
                "description": wf.description,
                "actions": actions,
            })

        config = {
            "app_paths": self._app_paths,
            "workflows": workflows,
        }
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            app_logger.debug("Automation config saved")
        except Exception as e:
            app_logger.error(f"Error saving automation config: {e}")

    # ─── App Path Management ─────────────────────────

    def register_app(self, name: str, path: str):
        """Register an application path."""
        self._app_paths[name] = path

    def get_app_path(self, name: str) -> str:
        """Get registered app path."""
        return self._app_paths.get(name, "")

    def get_registered_apps(self) -> dict[str, str]:
        """Get all registered apps."""
        return dict(self._app_paths)

    # ─── Window Management ───────────────────────────

    def find_windows(self, title_filter: str = "") -> list[WindowInfo]:
        """
        Find open windows, optionally filtering by title.
        """
        windows = []

        if self._is_windows:
            windows = self._find_windows_win32(title_filter)
        elif self._is_linux:
            windows = self._find_windows_linux(title_filter)

        return windows

    def _find_windows_win32(self, title_filter: str) -> list[WindowInfo]:
        """Find windows using Win32 API."""
        windows = []
        try:
            import win32gui
            import win32process

            def callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and (
                        not title_filter
                        or title_filter.lower() in title.lower()
                    ):
                        rect = win32gui.GetWindowRect(hwnd)
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        results.append(WindowInfo(
                            handle=hwnd,
                            title=title,
                            class_name=win32gui.GetClassName(hwnd),
                            process_id=pid,
                            x=rect[0],
                            y=rect[1],
                            width=rect[2] - rect[0],
                            height=rect[3] - rect[1],
                        ))

            win32gui.EnumWindows(callback, windows)
        except ImportError:
            app_logger.warning("win32gui not available")
        except Exception as e:
            app_logger.error(f"Error finding windows (Win32): {e}")

        return windows

    def _find_windows_linux(self, title_filter: str) -> list[WindowInfo]:
        """Find windows using wmctrl."""
        windows = []
        try:
            result = subprocess.run(
                ["wmctrl", "-l", "-p"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split(None, 4)
                    if len(parts) >= 5:
                        handle = int(parts[0], 16)
                        pid = int(parts[2]) if parts[2].isdigit() else 0
                        title = parts[4] if len(parts) > 4 else ""
                        if (
                            not title_filter
                            or title_filter.lower() in title.lower()
                        ):
                            windows.append(WindowInfo(
                                handle=handle,
                                title=title,
                                process_id=pid,
                            ))
        except FileNotFoundError:
            app_logger.warning("wmctrl not available on this system")
        except Exception as e:
            app_logger.error(f"Error finding windows (Linux): {e}")

        return windows

    def focus_window(self, title: str) -> bool:
        """Bring a window to the foreground."""
        if self._is_windows:
            return self._focus_window_win32(title)
        elif self._is_linux:
            return self._focus_window_linux(title)
        return False

    def _focus_window_win32(self, title: str) -> bool:
        """Focus window using Win32."""
        try:
            import win32gui
            import win32con

            windows = self._find_windows_win32(title)
            if windows:
                hwnd = windows[0].handle
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                app_logger.debug(f"Focused window: {title}")
                return True
        except Exception as e:
            app_logger.error(f"Error focusing window: {e}")
        return False

    def _focus_window_linux(self, title: str) -> bool:
        """Focus window using wmctrl."""
        try:
            result = subprocess.run(
                ["wmctrl", "-a", title],
                capture_output=True, timeout=5,
            )
            if result.returncode == 0:
                app_logger.debug(f"Focused window: {title}")
                return True
        except Exception as e:
            app_logger.error(f"Error focusing window: {e}")
        return False

    def minimize_window(self, title: str) -> bool:
        """Minimize a window."""
        if self._is_windows:
            try:
                import win32gui
                import win32con

                windows = self._find_windows_win32(title)
                if windows:
                    win32gui.ShowWindow(
                        windows[0].handle, win32con.SW_MINIMIZE
                    )
                    return True
            except Exception as e:
                app_logger.error(f"Error minimizing window: {e}")
        elif self._is_linux:
            try:
                subprocess.run(
                    ["xdotool", "search", "--name", title,
                     "windowminimize"],
                    capture_output=True, timeout=5,
                )
                return True
            except Exception as e:
                app_logger.error(f"Error minimizing window: {e}")
        return False

    def maximize_window(self, title: str) -> bool:
        """Maximize a window."""
        if self._is_windows:
            try:
                import win32gui
                import win32con

                windows = self._find_windows_win32(title)
                if windows:
                    win32gui.ShowWindow(
                        windows[0].handle, win32con.SW_MAXIMIZE
                    )
                    return True
            except Exception as e:
                app_logger.error(f"Error maximizing window: {e}")
        elif self._is_linux:
            try:
                subprocess.run(
                    ["wmctrl", "-r", title, "-b", "add,maximized_vert,maximized_horz"],
                    capture_output=True, timeout=5,
                )
                return True
            except Exception as e:
                app_logger.error(f"Error maximizing window: {e}")
        return False

    def close_window(self, title: str) -> bool:
        """Close a window."""
        if self._is_windows:
            try:
                import win32gui
                import win32con

                windows = self._find_windows_win32(title)
                if windows:
                    win32gui.PostMessage(
                        windows[0].handle, win32con.WM_CLOSE, 0, 0
                    )
                    return True
            except Exception as e:
                app_logger.error(f"Error closing window: {e}")
        elif self._is_linux:
            try:
                subprocess.run(
                    ["wmctrl", "-c", title],
                    capture_output=True, timeout=5,
                )
                return True
            except Exception as e:
                app_logger.error(f"Error closing window: {e}")
        return False

    # ─── Application Launching ───────────────────────

    def launch_app(self, name_or_path: str,
                   args: list[str] = None) -> Optional[int]:
        """
        Launch an application.

        Returns process ID if successful.
        """
        # Check registered apps first
        path = self._app_paths.get(name_or_path, name_or_path)

        if not os.path.exists(path) and not self._is_command_available(path):
            app_logger.error(f"Application not found: {path}")
            return None

        try:
            cmd = [path] + (args or [])
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            app_logger.info(f"Launched: {name_or_path} (PID: {process.pid})")
            return process.pid
        except Exception as e:
            app_logger.error(f"Failed to launch {name_or_path}: {e}")
            return None

    def _is_command_available(self, cmd: str) -> bool:
        """Check if a command is available in PATH."""
        try:
            if self._is_windows:
                result = subprocess.run(
                    ["where", cmd],
                    capture_output=True, timeout=5,
                )
            else:
                result = subprocess.run(
                    ["which", cmd],
                    capture_output=True, timeout=5,
                )
            return result.returncode == 0
        except Exception:
            return False

    def is_app_running(self, process_name: str) -> bool:
        """Check if an application is running."""
        try:
            if self._is_windows:
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {process_name}"],
                    capture_output=True, text=True, timeout=5,
                )
                return process_name.lower() in result.stdout.lower()
            else:
                result = subprocess.run(
                    ["pgrep", "-f", process_name],
                    capture_output=True, timeout=5,
                )
                return result.returncode == 0
        except Exception as e:
            app_logger.error(f"Error checking process: {e}")
            return False

    def get_running_processes(self) -> list[dict]:
        """Get list of running processes."""
        processes = []
        try:
            if self._is_windows:
                result = subprocess.run(
                    ["tasklist", "/FO", "CSV", "/NH"],
                    capture_output=True, text=True, timeout=10,
                )
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.strip('"').split('","')
                        if len(parts) >= 2:
                            processes.append({
                                "name": parts[0],
                                "pid": parts[1] if len(parts) > 1 else "",
                            })
            else:
                result = subprocess.run(
                    ["ps", "aux", "--no-headers"],
                    capture_output=True, text=True, timeout=10,
                )
                for line in result.stdout.strip().split('\n'):
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        processes.append({
                            "name": parts[10],
                            "pid": parts[1],
                        })
        except Exception as e:
            app_logger.error(f"Error listing processes: {e}")

        return processes

    # ─── Clipboard ───────────────────────────────────

    def clipboard_copy(self, text: str) -> bool:
        """Copy text to clipboard."""
        try:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
                return True
        except Exception as e:
            app_logger.error(f"Clipboard copy failed: {e}")
        return False

    def clipboard_paste(self) -> str:
        """Get text from clipboard."""
        try:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if clipboard:
                return clipboard.text()
        except Exception as e:
            app_logger.error(f"Clipboard paste failed: {e}")
        return ""

    # ─── Screenshot ──────────────────────────────────

    def take_screenshot(self, save_path: str = "",
                        region: tuple = None) -> str:
        """
        Take a screenshot.

        Args:
            save_path: Where to save (auto-generated if empty)
            region: Optional (x, y, width, height) tuple

        Returns:
            Path to saved screenshot
        """
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(
                os.path.expanduser("~"),
                "Desktop",
                f"screenshot_{timestamp}.png"
            )

        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QRect
            from PyQt5.QtGui import QScreen

            screen = QApplication.primaryScreen()
            if screen:
                if region:
                    x, y, w, h = region
                    pixmap = screen.grabWindow(0, x, y, w, h)
                else:
                    pixmap = screen.grabWindow(0)

                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                pixmap.save(save_path)
                app_logger.info(f"Screenshot saved: {save_path}")
                return save_path
        except Exception as e:
            app_logger.error(f"Screenshot failed: {e}")

        return ""

    # ─── Workflow Engine ─────────────────────────────

    def create_workflow(self, name: str,
                        description: str = "") -> AutomationWorkflow:
        """Create a new automation workflow."""
        workflow = AutomationWorkflow(
            name=name, description=description
        )
        self._workflows.append(workflow)
        return workflow

    def add_workflow_action(self, workflow: AutomationWorkflow,
                            action_type: ActionType,
                            params: dict = None,
                            delay_after: float = 0.5,
                            description: str = ""):
        """Add an action to a workflow."""
        action = AutomationAction(
            action_type=action_type,
            params=params or {},
            delay_after=delay_after,
            description=description,
        )
        workflow.actions.append(action)

    def run_workflow(self, workflow: AutomationWorkflow,
                     progress_callback: Callable = None) -> dict:
        """
        Execute a workflow sequentially.

        Returns results dict with success/failure counts.
        """
        results = {
            "total": len(workflow.actions),
            "success": 0,
            "failed": 0,
            "actions": [],
        }

        workflow.last_run = datetime.now().isoformat()
        workflow.run_count += 1

        for i, action in enumerate(workflow.actions):
            if progress_callback:
                pct = int((i + 1) / len(workflow.actions) * 100)
                progress_callback(pct, action.description or action.action_type.value)

            success = self._execute_action(action)
            action.success = success

            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

            results["actions"].append({
                "type": action.action_type.value,
                "description": action.description,
                "success": success,
                "result": action.result,
            })

            if action.delay_after > 0:
                time.sleep(action.delay_after)

        app_logger.info(
            f"Workflow '{workflow.name}' completed: "
            f"{results['success']}/{results['total']} actions succeeded"
        )

        return results

    def _execute_action(self, action: AutomationAction) -> bool:
        """Execute a single automation action."""
        try:
            if action.action_type == ActionType.LAUNCH_APP:
                pid = self.launch_app(
                    action.params.get("app", ""),
                    action.params.get("args", []),
                )
                action.result = f"PID: {pid}" if pid else "Failed"
                return pid is not None

            elif action.action_type == ActionType.FOCUS_WINDOW:
                return self.focus_window(
                    action.params.get("title", "")
                )

            elif action.action_type == ActionType.CLOSE_WINDOW:
                return self.close_window(
                    action.params.get("title", "")
                )

            elif action.action_type == ActionType.MINIMIZE_WINDOW:
                return self.minimize_window(
                    action.params.get("title", "")
                )

            elif action.action_type == ActionType.MAXIMIZE_WINDOW:
                return self.maximize_window(
                    action.params.get("title", "")
                )

            elif action.action_type == ActionType.CLIPBOARD_COPY:
                return self.clipboard_copy(
                    action.params.get("text", "")
                )

            elif action.action_type == ActionType.CLIPBOARD_PASTE:
                text = self.clipboard_paste()
                action.result = text
                return bool(text)

            elif action.action_type == ActionType.SCREENSHOT:
                path = self.take_screenshot(
                    action.params.get("path", ""),
                    action.params.get("region"),
                )
                action.result = path
                return bool(path)

            elif action.action_type == ActionType.WAIT:
                duration = action.params.get("seconds", 1.0)
                time.sleep(duration)
                return True

            elif action.action_type == ActionType.RUN_COMMAND:
                cmd = action.params.get("command", "")
                if not cmd:
                    return False
                result = subprocess.run(
                    cmd, shell=True,
                    capture_output=True, text=True,
                    timeout=action.params.get("timeout", 30),
                )
                action.result = result.stdout
                return result.returncode == 0

            else:
                app_logger.warning(
                    f"Unknown action type: {action.action_type}"
                )
                return False

        except Exception as e:
            action.result = str(e)
            app_logger.error(f"Action failed: {action.action_type}: {e}")
            return False

    # ─── Workflow Management ─────────────────────────

    def get_workflows(self) -> list[AutomationWorkflow]:
        """Get all workflows."""
        return list(self._workflows)

    def get_workflow(self, name: str) -> Optional[AutomationWorkflow]:
        """Get a workflow by name."""
        for wf in self._workflows:
            if wf.name == name:
                return wf
        return None

    def remove_workflow(self, name: str):
        """Remove a workflow by name."""
        self._workflows = [
            wf for wf in self._workflows if wf.name != name
        ]

    # ─── Pre-built Workflows ─────────────────────────

    def create_open_and_focus_workflow(self, app_name: str,
                                       app_path: str,
                                       window_title: str) -> AutomationWorkflow:
        """Create a workflow to open an app and focus its window."""
        wf = self.create_workflow(
            name=f"Open {app_name}",
            description=f"Launch {app_name} and bring to front",
        )
        self.add_workflow_action(
            wf, ActionType.LAUNCH_APP,
            {"app": app_path},
            delay_after=2.0,
            description=f"Launch {app_name}",
        )
        self.add_workflow_action(
            wf, ActionType.FOCUS_WINDOW,
            {"title": window_title},
            description=f"Focus {app_name} window",
        )
        return wf

    # ─── Status ──────────────────────────────────────

    @property
    def platform_name(self) -> str:
        """Get platform name."""
        return platform.system()

    @property
    def is_supported(self) -> bool:
        """Check if platform is supported."""
        return self._is_windows or self._is_linux

    def get_capabilities(self) -> dict:
        """Get available automation capabilities."""
        caps = {
            "platform": self.platform_name,
            "supported": self.is_supported,
            "window_management": False,
            "app_launching": True,
            "clipboard": True,
            "screenshot": True,
            "process_management": True,
        }

        if self._is_windows:
            try:
                import win32gui
                caps["window_management"] = True
            except ImportError:
                pass
        elif self._is_linux:
            caps["window_management"] = self._is_command_available("wmctrl")

        return caps

    def get_stats(self) -> dict:
        """Get automation statistics."""
        return {
            "platform": self.platform_name,
            "registered_apps": len(self._app_paths),
            "workflows": len(self._workflows),
            "capabilities": self.get_capabilities(),
        }
