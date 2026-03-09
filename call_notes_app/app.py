import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from transcriber import LiveTranscriber
from summarizer import generate_notes
from storage import save_notes


class CallNotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Call Notes — Live Transcriber")
        self.root.geometry("850x700")
        self.root.minsize(700, 550)

        self.transcriber = None
        self._build_ui()
        self._load_devices()

    def _build_ui(self):
        # Top controls frame
        controls = ttk.Frame(self.root, padding=10)
        controls.pack(fill=tk.X)

        ttk.Label(controls, text="Customer Name:").grid(row=0, column=0, sticky=tk.W)
        self.customer_var = tk.StringVar()
        ttk.Entry(controls, textvariable=self.customer_var, width=30).grid(
            row=0, column=1, padx=5, columnspan=2
        )

        ttk.Label(controls, text="System Audio (CABLE Output):").grid(
            row=1, column=0, sticky=tk.W, pady=(5, 0)
        )
        self.system_device_var = tk.StringVar()
        self.system_device_combo = ttk.Combobox(
            controls, textvariable=self.system_device_var, width=45, state="readonly"
        )
        self.system_device_combo.grid(row=1, column=1, padx=5, pady=(5, 0), columnspan=2)

        ttk.Label(controls, text="Microphone:").grid(
            row=2, column=0, sticky=tk.W, pady=(5, 0)
        )
        self.mic_device_var = tk.StringVar()
        self.mic_device_combo = ttk.Combobox(
            controls, textvariable=self.mic_device_var, width=45, state="readonly"
        )
        self.mic_device_combo.grid(row=2, column=1, padx=5, pady=(5, 0), columnspan=2)

        # Buttons
        btn_frame = ttk.Frame(self.root, padding=(10, 5))
        btn_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(
            btn_frame, text="▶ Start Recording", command=self._start
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            btn_frame, text="⏹ Stop & Generate Notes", command=self._stop, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(btn_frame, textvariable=self.status_var).pack(side=tk.RIGHT, padx=10)

        # Live transcript area
        ttk.Label(self.root, text="Live Transcript:", padding=(10, 10, 10, 0)).pack(
            anchor=tk.W
        )
        self.transcript_text = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, height=12, state=tk.DISABLED
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        # Generated notes area
        ttk.Label(self.root, text="Generated Notes:", padding=(10, 5, 10, 0)).pack(
            anchor=tk.W
        )
        self.notes_text = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, height=12, state=tk.DISABLED
        )
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def _load_devices(self):
        temp = LiveTranscriber()
        devices = temp.get_audio_devices()
        self._devices = devices
        names = [f"{i}: {name}" for i, name in devices]

        # Add a "None" option so either can be optional
        system_names = ["(None)"] + names
        mic_names = ["(None)"] + names

        self.system_device_combo["values"] = system_names
        self.mic_device_combo["values"] = mic_names

        # Auto-select CABLE Output for system audio, first mic for mic
        cable_idx = None
        mic_idx = None
        for j, (i, name) in enumerate(devices):
            if "cable output" in name.lower() and "virtual cable" in name.lower() and cable_idx is None:
                cable_idx = j
            if "microphone" in name.lower() and mic_idx is None:
                mic_idx = j

        self.system_device_combo.current(cable_idx + 1 if cable_idx is not None else 0)
        self.mic_device_combo.current(mic_idx + 1 if mic_idx is not None else 0)

    def _on_partial(self, text):
        """Show partial (in-progress) transcript, replacing the current partial line."""
        self.root.after(0, self._safe_show_partial, text)

    def _on_final(self, text):
        """Finalize the current line and move to the next."""
        self.root.after(0, self._safe_show_final, text)

    def _safe_show_partial(self, text):
        self.transcript_text.config(state=tk.NORMAL)
        # Delete everything after the partial marker and replace with new partial
        self.transcript_text.delete("partial_start", "end-1c")
        self.transcript_text.insert("partial_start", text)
        self.transcript_text.see(tk.END)
        self.transcript_text.config(state=tk.DISABLED)

    def _safe_show_final(self, text):
        self.transcript_text.config(state=tk.NORMAL)
        # Replace partial text with final text + newline
        self.transcript_text.delete("partial_start", "end-1c")
        self.transcript_text.insert("partial_start", text + "\n")
        # Move the marker to the end for the next partial
        self.transcript_text.mark_set("partial_start", "end-1c")
        self.transcript_text.see(tk.END)
        self.transcript_text.config(state=tk.DISABLED)

    def _get_selected_device(self, combo):
        idx = combo.current()
        if idx <= 0:  # 0 is "(None)"
            return None
        return self._devices[idx - 1][0]

    def _start(self):
        customer = self.customer_var.get().strip()
        if not customer:
            messagebox.showwarning("Missing Info", "Please enter a customer name.")
            return

        system_dev = self._get_selected_device(self.system_device_combo)
        mic_dev = self._get_selected_device(self.mic_device_combo)

        if system_dev is None and mic_dev is None:
            messagebox.showwarning("No Device", "Please select at least one audio device.")
            return

        # Clear previous text
        for widget in (self.transcript_text, self.notes_text):
            widget.config(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.config(state=tk.DISABLED)

        self.transcriber = LiveTranscriber(
            system_device=system_dev,
            mic_device=mic_dev,
            on_partial=self._on_partial,
            on_final=self._on_final,
        )
        self.transcriber.start()

        # Set the initial mark for partial text replacement
        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.mark_set("partial_start", "end-1c")
        self.transcript_text.mark_gravity("partial_start", tk.LEFT)
        self.transcript_text.config(state=tk.DISABLED)

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("🔴 Recording...")

    def _stop(self):
        if not self.transcriber:
            return

        self.status_var.set("Stopping recording...")
        self.transcriber.stop()
        transcript = self.transcriber.get_full_transcript()

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

        if not transcript:
            self.status_var.set("No speech detected.")
            messagebox.showinfo("Empty", "No transcript was captured.")
            return

        self.status_var.set("Generating notes with Claude...")
        threading.Thread(
            target=self._generate_and_save, args=(transcript,), daemon=True
        ).start()

    def _generate_and_save(self, transcript):
        customer = self.customer_var.get().strip()
        try:
            notes = generate_notes(transcript, customer)
            filepath = save_notes(customer, notes)
            self.root.after(0, self._show_notes, notes, filepath)
        except Exception as e:
            self.root.after(
                0, lambda: messagebox.showerror("Error", f"Failed to generate notes:\n{e}")
            )
            self.root.after(0, lambda: self.status_var.set("Error generating notes."))

    def _show_notes(self, notes, filepath):
        self.notes_text.config(state=tk.NORMAL)
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert(tk.END, notes)
        self.notes_text.config(state=tk.DISABLED)
        self.status_var.set(f"Notes saved: {filepath}")


def main():
    root = tk.Tk()
    CallNotesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
