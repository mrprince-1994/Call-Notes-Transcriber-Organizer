"""
Standalone test for the extract button flash-and-reset pattern.
Does NOT import app.py — tests the exact _flash_btn logic in isolation.

Proves that:
  1. Button transitions to flash state (correct text + color + disabled)
  2. Button resets to original state after 3 seconds (text + color + normal)
  3. All 4 scenarios work for both SIFT and Activity buttons
"""
import time
import tkinter as tk
import customtkinter as ctk

ctk.set_appearance_mode("dark")

RESULTS = []
DEFAULT_COLOR = "#1f2937"

# These match the exact values used in app.py _flash_btn calls
SCENARIOS = [
    ("✅ Queued",    "#065f46"),  # success
    ("⚠️ Duplicate", "#92400e"),  # duplicate
    ("❌ Failed",    "#7f1d1d"),  # failure (None return)
    ("❌ Error",     "#7f1d1d"),  # exception
]


def pump(root, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        root.update()
        time.sleep(0.02)


def test_one(root, btn, orig_text, flash_text, flash_color):
    """
    Replicate the exact _flash_btn pattern from app.py:
        btn.configure(text=text, fg_color=color, state=DISABLED)
        root.after(3000, lambda: btn.configure(
            state=NORMAL, text=orig_text, fg_color=DEFAULT_COLOR))
    """
    name = f"{orig_text} → {flash_text} → resets"
    print(f"  TEST: {name}")

    # Reset to starting state
    btn.configure(text=orig_text, fg_color=DEFAULT_COLOR, state=tk.NORMAL)
    root.update()

    # === This is the exact _flash_btn code from app.py ===
    btn.configure(text=flash_text, fg_color=flash_color, state=tk.DISABLED)
    root.after(3000, lambda: btn.configure(
        state=tk.NORMAL, text=orig_text, fg_color=DEFAULT_COLOR))
    # =====================================================

    root.update()

    # Check flash state
    f_text = btn.cget("text")
    f_color = btn.cget("fg_color")
    f_state = str(btn.cget("state"))
    flash_ok = (f_text == flash_text and f_color == flash_color
                and f_state == "disabled")
    if not flash_ok:
        print(f"    FLASH FAIL: text={f_text!r} color={f_color!r} "
              f"state={f_state!r}")

    # Wait for the 3s reset
    pump(root, 3.3)

    r_text = btn.cget("text")
    r_color = btn.cget("fg_color")
    r_state = str(btn.cget("state"))
    reset_ok = (r_text == orig_text and r_color == DEFAULT_COLOR
                and r_state == "normal")
    if not reset_ok:
        print(f"    RESET FAIL: text={r_text!r} color={r_color!r} "
              f"state={r_state!r}")

    passed = flash_ok and reset_ok
    print(f"    {'PASS ✅' if passed else 'FAIL ❌'}")
    RESULTS.append((name, passed))


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  EXTRACT BUTTON FLASH/RESET TESTS")
    print("=" * 60)

    root = ctk.CTk()
    root.withdraw()

    sift_btn = ctk.CTkButton(root, text="📊 SIFT", fg_color=DEFAULT_COLOR,
                             height=30, width=80)
    sift_btn.pack()

    act_btn = ctk.CTkButton(root, text="📝 Activity", fg_color=DEFAULT_COLOR,
                            height=30, width=80)
    act_btn.pack()
    root.update()

    print("\n  --- SIFT Button ---")
    for flash_text, flash_color in SCENARIOS:
        test_one(root, sift_btn, "📊 SIFT", flash_text, flash_color)

    print("\n  --- Activity Button ---")
    for flash_text, flash_color in SCENARIOS:
        test_one(root, act_btn, "📝 Activity", flash_text, flash_color)

    root.destroy()

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    total = len(RESULTS)
    ok = sum(1 for _, p in RESULTS if p)
    for n, p in RESULTS:
        print(f"  {'✅' if p else '❌'} {n}")
    print(f"\n  {ok}/{total} passed")
    print("=" * 60)

    import sys
    sys.exit(0 if ok == total else 1)
