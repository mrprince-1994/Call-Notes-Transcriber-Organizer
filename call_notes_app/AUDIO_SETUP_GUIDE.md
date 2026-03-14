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
Call audio → CABLE Input (system default speaker) → CABLE Output → App captures it
                                                                 ↓
                                                    Listen-through → Your speakers/headset (you hear it)
```

---

## Scenario 1: Using a Headset (Plantronics Blackwire 5220 or similar)

### Windows Sound Settings (right-click speaker icon → Sound settings)

- Set **Output device** to: `CABLE Input (VB-Audio Virtual Cable)`

### mmsys.cpl (Win + R → mmsys.cpl → Enter)

Playback tab:
- Verify **CABLE Input (VB-Audio Virtual Cable)** is the Default Device

Recording tab:
1. Right-click **CABLE Output (VB-Audio Virtual Cable)** → Properties
2. Go to the **Listen** tab
3. Check **"Listen to this device"**
4. Set **"Playback through this device"** to: `Headset Earphone (Plantronics Blackwire 5220 Series)`
5. Click Apply, then OK

### Zoom / Teams Audio Settings

- Speaker: **Same as System** (this routes audio through CABLE Input)
- Microphone: **Headset Microphone (Plantronics Blackwire 5220 Series)**

### In the App

- **System Audio (CABLE Output):** Select the device labeled `CABLE Output (VB-Audio Virtual Cable)` (device number will vary by machine)
- **Microphone:** Select your headset microphone from the dropdown

### Summary

| Setting | Value |
|---|---|
| Windows output device | CABLE Input (VB-Audio Virtual Cable) |
| mmsys.cpl listen-through | Your headset earphone (e.g. Plantronics, Jabra, etc.) |
| Zoom/Teams speaker | Same as System |
| Zoom/Teams microphone | Your headset microphone |
| App — System Audio | CABLE Output (VB-Audio Virtual Cable) |
| App — Microphone | Your headset microphone |

---

## Scenario 2: Using Built-in Laptop Speakers & Microphone (No Headset)

### Windows Sound Settings

- Set **Output device** to: `CABLE Input (VB-Audio Virtual Cable)` (same as headset setup)

### mmsys.cpl (Win + R → mmsys.cpl → Enter)

Recording tab:
1. Right-click **CABLE Output (VB-Audio Virtual Cable)** → Properties
2. Go to the **Listen** tab
3. Check **"Listen to this device"**
4. Set **"Playback through this device"** to: `Speakers (Realtek(R) Audio)`
5. Click Apply, then OK

### Zoom / Teams Audio Settings

- Speaker: **Same as System**
- Microphone: **Microphone (Realtek(R) Audio)**

### In the App

- **System Audio (CABLE Output):** Select the device labeled `CABLE Output (VB-Audio Virtual Cable)` (device number will vary by machine)
- **Microphone:** Select your built-in microphone from the dropdown

### Summary

| Setting | Value |
|---|---|
| Windows output device | CABLE Input (VB-Audio Virtual Cable) |
| mmsys.cpl listen-through | Your laptop speakers (e.g. Speakers (Realtek(R) Audio)) |
| Zoom/Teams speaker | Same as System |
| Zoom/Teams microphone | Your built-in microphone (e.g. Microphone (Realtek(R) Audio)) |
| App — System Audio | CABLE Output (VB-Audio Virtual Cable) |
| App — Microphone | Your built-in microphone |

---

## Switching Between Headset and Laptop Speakers

When you plug in or unplug your headset, only TWO things need to change:

### Plugging in headset

1. `mmsys.cpl` → Recording tab → right-click **CABLE Output** → Properties → **Listen** tab
2. Make sure **"Listen to this device"** is checked
3. Set **"Playback through this device"** dropdown to your headset earphone
4. Click Apply, then OK
5. In the app, change Microphone to your headset microphone

### Unplugging headset

1. `mmsys.cpl` → Recording tab → right-click **CABLE Output** → Properties → **Listen** tab
2. Make sure **"Listen to this device"** is checked
3. Set **"Playback through this device"** dropdown to your laptop speakers
4. Click Apply, then OK
5. In the app, change Microphone to your built-in microphone

Everything else stays the same:
- Windows output stays on CABLE Input
- System Audio in the app stays on CABLE Output
- Zoom/Teams speaker stays on "Same as System"

---

## Important: Zoom / Teams Speaker Setting

The call app (Zoom, Teams, etc.) must have its speaker set to **"Same as System"** — not directly to your headset or speakers. If you set it directly to your headset, the audio bypasses VB-CABLE and the app won't capture it.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| App not capturing call audio | Check that Zoom/Teams speaker is "Same as System", not your headset directly |
| Can't hear anything | Open mmsys.cpl → Recording → CABLE Output → Listen tab → make sure "Listen to this device" is checked and playback device is correct |
| Audio stopped after plugging in headset | Windows may have switched output — set it back to CABLE Input in Sound Settings, and update listen-through to your headset |
| App not capturing your voice | Change the Microphone dropdown in the app to match your current mic (headset or built-in) |
| Multiple CABLE Output entries in app | Select the one labeled `CABLE Output (VB-Audio Virtual Cable)` |
| Zoom audio goes to headset but app doesn't capture | Zoom speaker is set directly to headset — change it to "Same as System" |

---

## Quick Reference: mmsys.cpl

The classic Sound Control Panel is hidden in Windows 11. To open it:

```
Win + R → mmsys.cpl → Enter
```

This gives you access to the Recording tab and Listen-through settings that aren't available in the modern Windows Sound Settings.
