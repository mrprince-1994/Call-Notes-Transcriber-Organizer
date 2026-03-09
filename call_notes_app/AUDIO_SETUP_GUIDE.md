# Audio & Device Setup Guide

This guide covers how to configure your audio routing so the Call Notes app can capture both sides of a conversation — the other person's voice (system audio) and your voice (microphone).

The app uses VB-CABLE, a virtual audio driver that acts as a bridge between your system audio and the app.

---

## How VB-CABLE Works

VB-CABLE creates two virtual devices:

- **CABLE Input** — a virtual speaker. When Windows sends audio here, it enters the cable.
- **CABLE Output** — a virtual microphone. The app reads audio from here.

Audio flows like this:

```
Call/YouTube audio → CABLE Input (speaker) → CABLE Output (mic) → App captures it
```

The trick is that you also need to hear the audio yourself, so we use the "Listen" feature to echo it back to your real speakers or headset.

---

## Scenario 1: Using a Headset (Plantronics, Jabra, etc.)

### Windows Sound Settings

1. Right-click the speaker icon in your taskbar → **Sound settings**
2. Set **Output device** to: `CABLE Input (VB-Audio Virtual Cable)`
   - This routes all system audio (Teams, Zoom, YouTube) into the virtual cable

### Listen-Through (so you can hear audio in your headset)

1. Press `Win + R`, type `mmsys.cpl`, press Enter
2. Go to the **Recording** tab
3. Right-click **CABLE Output (VB-Audio Virtual Cable)** → **Properties**
4. Go to the **Listen** tab
5. Check **"Listen to this device"**
6. Set **"Playback through this device"** to: `Your headset speakers (e.g., Plantronics)`
7. Click **OK**

### In the App

- **System Audio (CABLE Output):** Select `CABLE Output (VB-Audio Virtual Cable)`
- **Microphone:** Select `Headset Microphone (Plantronics)` (or your headset mic name)

### Summary

| Setting | Value |
|---|---|
| Windows output device | CABLE Input (VB-Audio Virtual Cable) |
| Listen-through playback | Your headset (Plantronics, Jabra, etc.) |
| App — System Audio | CABLE Output (VB-Audio Virtual Cable) |
| App — Microphone | Headset Microphone |

---

## Scenario 2: Using Built-in Laptop Speakers & Microphone (No Headset)

### Windows Sound Settings

1. Right-click the speaker icon in your taskbar → **Sound settings**
2. Set **Output device** to: `CABLE Input (VB-Audio Virtual Cable)`

### Listen-Through (so you can hear audio from your laptop speakers)

1. Press `Win + R`, type `mmsys.cpl`, press Enter
2. Go to the **Recording** tab
3. Right-click **CABLE Output (VB-Audio Virtual Cable)** → **Properties**
4. Go to the **Listen** tab
5. Check **"Listen to this device"**
6. Set **"Playback through this device"** to: `Speakers (Realtek Audio)` (or your built-in speakers)
7. Click **OK**

### In the App

- **System Audio (CABLE Output):** Select `CABLE Output (VB-Audio Virtual Cable)`
- **Microphone:** Select `Microphone (Realtek(R) Audio)` (or your built-in mic name)

### Summary

| Setting | Value |
|---|---|
| Windows output device | CABLE Input (VB-Audio Virtual Cable) |
| Listen-through playback | Speakers (Realtek Audio) |
| App — System Audio | CABLE Output (VB-Audio Virtual Cable) |
| App — Microphone | Microphone (Realtek(R) Audio) |

---

## Switching Between Headset and Laptop Speakers

When you plug in or unplug a headset, Windows often auto-switches the output device to the headset. This breaks the VB-CABLE routing because audio stops going through CABLE Input.

**Every time you plug in or unplug a headset:**

1. Go to Windows Sound Settings
2. Set the output device back to `CABLE Input (VB-Audio Virtual Cable)`
3. Open `mmsys.cpl` → Recording → CABLE Output → Listen tab
4. Change **"Playback through this device"** to match your current listening device:
   - Headset plugged in → select your headset
   - No headset → select your laptop speakers

**In the app**, just change the Microphone dropdown to match:
- Headset plugged in → select your headset mic
- No headset → select your built-in mic

The System Audio dropdown stays the same (`CABLE Output`) regardless of which device you're using.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| App not capturing system audio | Check that Windows output is set to CABLE Input, not your headset or speakers |
| Can't hear anything | Set up Listen-through in mmsys.cpl (Recording → CABLE Output → Listen tab) |
| App not capturing your voice | Make sure the correct mic is selected in the app's Microphone dropdown |
| Audio stopped after plugging in headset | Windows switched output — set it back to CABLE Input |
| Multiple CABLE Output entries in app | Select the one labeled `CABLE Output (VB-Audio Virtual Cable)` — avoid "VB-Audio Point" entries |

---

## Quick Reference: mmsys.cpl

The classic Sound Control Panel is hidden in Windows 11. To open it:

```
Win + R → mmsys.cpl → Enter
```

This gives you access to the Recording tab and Listen-through settings that aren't available in the modern Windows Sound Settings.
