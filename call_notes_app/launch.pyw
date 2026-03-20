"""Launcher wrapper that logs errors to a file for debugging."""
import sys
import os
import traceback

# Ensure working directory is the call_notes_app folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launch_error.log")

try:
    # Remove old log
    if os.path.exists(log_path):
        os.remove(log_path)
    
    # Import and run the app
    from app import main
    main()
except Exception as e:
    with open(log_path, "w") as f:
        f.write(f"Launch failed:\n{traceback.format_exc()}\n")
    # Also show a message box so the user sees it
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, f"App failed to start. See:\n{log_path}\n\nError: {e}", "Call Notes Error", 0x10)
