import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
from transcriber import LiveTranscriber
from summarizer import generate_notes
from storage import save_notes, _md_to_docx
from history import save_session, list_sessions, get_all_customers
from question_detector import is_aws_aiml_question, extract_question
from agent_client import ask_agent, warmup as warmup_agent, shutdown as shutdown_agent
from md_render import configure_tags, MarkdownStreamer

# --- Color Palette ---
BG_DARK = "#1e1e2e"
BG_PANEL = "#282840"
BG_INPUT = "#313150"
BG_CARD = "#2a2a45"
FG_TEXT = "#cdd6f4"
FG_DIM = "#7f849c"
FG_BRIGHT = "#ffffff"
ACCENT = "#89b4fa"
ACCENT_HOVER = "#74c7ec"
GREEN = "#a6e3a1"
RED = "#f38ba8"
ORANGE = "#fab387"
YELLOW = "#f9e2af"
BORDER = "#45475a"


def _apply_theme(root):
    """Configure a modern dark ttk theme."""
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 10))
    style.configure("TFrame", background=BG_DARK)
    style.configure("TLabel", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 10))
    style.configure("TLabelframe", background=BG_PANEL, foreground=ACCENT,
                     font=("Segoe UI Semibold", 11), borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background=BG_PANEL, foreground=ACCENT,
                     font=("Segoe UI Semibold", 11))

    style.configure("TEntry", fieldbackground=BG_INPUT, foreground=FG_BRIGHT,
                     insertcolor=FG_BRIGHT, borderwidth=1, relief="solid")
    style.configure("TCombobox", fieldbackground=BG_INPUT, foreground=FG_BRIGHT,
                     selectbackground=ACCENT, selectforeground=BG_DARK, borderwidth=1)
    style.map("TCombobox", fieldbackground=[("readonly", BG_INPUT)],
              foreground=[("readonly", FG_BRIGHT)])

    # Buttons
    style.configure("Accent.TButton", background=ACCENT, foreground=BG_DARK,
                     font=("Segoe UI Semibold", 10), padding=(12, 6), borderwidth=0)
    style.map("Accent.TButton", background=[("active", ACCENT_HOVER), ("disabled", BORDER)],
              foreground=[("disabled", FG_DIM)])

    style.configure("Green.TButton", background=GREEN, foreground=BG_DARK,
                     font=("Segoe UI Semibold", 10), padding=(12, 6), borderwidth=0)
    style.map("Green.TButton", background=[("active", "#b5f0b0"), ("disabled", BORDER)],
              foreground=[("disabled", FG_DIM)])

    style.configure("Red.TButton", background=RED, foreground=BG_DARK,
                     font=("Segoe UI Semibold", 10), padding=(12, 6), borderwidth=0)
    style.map("Red.TButton", background=[("active", "#f5a0b8"), ("disabled", BORDER)],
              foreground=[("disabled", FG_DIM)])

    style.configure("Export.TButton", background=BG_INPUT, foreground=FG_TEXT,
                     font=("Segoe UI", 9), padding=(10, 5), borderwidth=1, relief="solid")
    style.map("Export.TButton", background=[("active", BG_CARD), ("disabled", BG_DARK)],
              foreground=[("disabled", FG_DIM)])

    style.configure("Small.TButton", background=BG_INPUT, foreground=ACCENT,
                     font=("Segoe UI", 10), padding=(6, 4), borderwidth=1)
    style.map("Small.TButton", background=[("active", BG_CARD)])

    style.configure("Yellow.TButton", background=YELLOW, foreground=BG_DARK,
                     font=("Segoe UI Semibold", 10), padding=(10, 5), borderwidth=0)
    style.map("Yellow.TButton", background=[("active", "#fce8b8"), ("disabled", BORDER)],
              foreground=[("disabled", FG_DIM)])

    style.configure("TPanedwindow", background=BG_DARK)

    # Section headers
    style.configure("Section.TLabel", background=BG_DARK, foreground=ACCENT,
                     font=("Segoe UI Semibold", 10))
    style.configure("Status.TLabel", background=BG_DARK, foreground=ORANGE,
                     font=("Segoe UI", 9))
    style.configure("Title.TLabel", background=BG_DARK, foreground=FG_BRIGHT,
                     font=("Segoe UI Semibold", 14))
    style.configure("Dim.TLabel", background=BG_DARK, foreground=FG_DIM,
                     font=("Segoe UI", 9))
    style.configure("AI.TLabel", background=BG_DARK, foreground=YELLOW,
                     font=("Segoe UI Semibold", 10))


class CallNotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Call Notes — Live Transcriber")
        self.root.geometry("1400x800")
        self.root.minsize(1100, 700)
        self.root.configure(bg=BG_DARK)

        _apply_theme(root)

        self.transcriber = None
        self._current_transcript = ""
        self._current_notes = ""
        self._ai_enabled = True
        self._pending_questions = set()  # avoid duplicate lookups
        self._build_ui()
        self._load_devices()

        # Pre-start MCP servers in background so first question is fast
        warmup_agent()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Title bar
        title_bar = ttk.Frame(self.root)
        title_bar.pack(fill=tk.X, padx=15, pady=(12, 0))
        ttk.Label(title_bar, text="🎙  Call Notes", style="Title.TLabel").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(title_bar, textvariable=self.status_var, style="Status.TLabel").pack(
            side=tk.RIGHT, padx=5
        )

        # Main paned window — 3 columns
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # --- Left: History Panel ---
        history_frame = ttk.LabelFrame(paned, text="  Session History  ", padding=8)
        paned.add(history_frame, weight=1)

        filter_frame = ttk.Frame(history_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(filter_frame, text="Filter:", style="Dim.TLabel").pack(side=tk.LEFT)
        self.history_filter_var = tk.StringVar(value="(All)")
        self.history_filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.history_filter_var, width=16, state="readonly"
        )
        self.history_filter_combo.pack(side=tk.LEFT, padx=(5, 4))
        self.history_filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_history())
        ttk.Button(filter_frame, text="⟳", width=3, style="Small.TButton",
                   command=self._refresh_history).pack(side=tk.LEFT)

        self.history_list = tk.Listbox(
            history_frame, width=28, exportselection=False,
            bg=BG_INPUT, fg=FG_TEXT, selectbackground=ACCENT, selectforeground=BG_DARK,
            font=("Segoe UI", 9), borderwidth=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT, activestyle="none",
        )
        self.history_list.pack(fill=tk.BOTH, expand=True)
        self.history_list.bind("<<ListboxSelect>>", self._on_history_select)
        self._history_items = []

        # --- Center: Main Content ---
        center_frame = ttk.Frame(paned)
        paned.add(center_frame, weight=3)

        # Controls card
        controls = ttk.Frame(center_frame)
        controls.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(controls, text="Customer Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.customer_var = tk.StringVar()
        cust_entry = ttk.Entry(controls, textvariable=self.customer_var, width=32,
                               font=("Segoe UI", 10))
        cust_entry.grid(row=0, column=1, padx=8, columnspan=2, sticky=tk.W, pady=2)

        ttk.Label(controls, text="System Audio:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.system_device_var = tk.StringVar()
        self.system_device_combo = ttk.Combobox(
            controls, textvariable=self.system_device_var, width=48, state="readonly",
            font=("Segoe UI", 9)
        )
        self.system_device_combo.grid(row=1, column=1, padx=8, columnspan=2, sticky=tk.W, pady=2)

        ttk.Label(controls, text="Microphone:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.mic_device_var = tk.StringVar()
        self.mic_device_combo = ttk.Combobox(
            controls, textvariable=self.mic_device_var, width=48, state="readonly",
            font=("Segoe UI", 9)
        )
        self.mic_device_combo.grid(row=2, column=1, padx=8, columnspan=2, sticky=tk.W, pady=2)

        # Buttons row
        btn_frame = ttk.Frame(center_frame)
        btn_frame.pack(fill=tk.X, pady=(4, 8))

        self.start_btn = ttk.Button(btn_frame, text="▶  Start Recording",
                                     style="Green.TButton", command=self._start)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.stop_btn = ttk.Button(btn_frame, text="⏹  Stop & Generate",
                                    style="Red.TButton", command=self._stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 12))

        sep = ttk.Frame(btn_frame, width=1)
        sep.pack(side=tk.LEFT, padx=(0, 12))

        self.export_docx_btn = ttk.Button(btn_frame, text="📄 Export DOCX",
                                           style="Export.TButton", command=self._export_docx,
                                           state=tk.DISABLED)
        self.export_docx_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.export_pdf_btn = ttk.Button(btn_frame, text="📑 Export PDF",
                                          style="Export.TButton", command=self._export_pdf,
                                          state=tk.DISABLED)
        self.export_pdf_btn.pack(side=tk.LEFT)

        # Transcript area
        ttk.Label(center_frame, text="Live Transcript", style="Section.TLabel").pack(
            anchor=tk.W, pady=(4, 3)
        )
        self.transcript_text = scrolledtext.ScrolledText(
            center_frame, wrap=tk.WORD, height=9, state=tk.DISABLED,
            bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_BRIGHT,
            font=("Consolas", 10), borderwidth=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT, padx=8, pady=6,
        )
        self.transcript_text.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # Notes area
        ttk.Label(center_frame, text="Generated Notes", style="Section.TLabel").pack(
            anchor=tk.W, pady=(2, 3)
        )
        self.notes_text = scrolledtext.ScrolledText(
            center_frame, wrap=tk.WORD, height=9, state=tk.DISABLED,
            bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_BRIGHT,
            font=("Segoe UI", 10), borderwidth=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT, padx=8, pady=6,
        )
        self.notes_text.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        # --- Right: AI Answers Panel ---
        ai_frame = ttk.LabelFrame(paned, text="  🤖 AI Answers  ", padding=8)
        paned.add(ai_frame, weight=2)

        ai_controls = ttk.Frame(ai_frame)
        ai_controls.pack(fill=tk.X, pady=(0, 6))

        self.ai_toggle_var = tk.BooleanVar(value=True)
        self.ai_toggle_btn = ttk.Checkbutton(
            ai_controls, text="Auto-detect questions",
            variable=self.ai_toggle_var, command=self._toggle_ai,
        )
        self.ai_toggle_btn.pack(side=tk.LEFT)

        ttk.Button(ai_controls, text="Clear", style="Small.TButton",
                   command=self._clear_ai_answers).pack(side=tk.RIGHT)

        # Manual question entry
        ask_frame = ttk.Frame(ai_frame)
        ask_frame.pack(fill=tk.X, pady=(0, 6))

        self.manual_question_var = tk.StringVar()
        self.manual_question_entry = ttk.Entry(
            ask_frame, textvariable=self.manual_question_var,
            font=("Segoe UI", 9),
        )
        self.manual_question_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.manual_question_entry.bind("<Return>", lambda e: self._ask_manual_question())

        ttk.Button(ask_frame, text="Ask", style="Yellow.TButton",
                   command=self._ask_manual_question).pack(side=tk.RIGHT)

        # AI answers display
        self.ai_text = scrolledtext.ScrolledText(
            ai_frame, wrap=tk.WORD, state=tk.DISABLED,
            bg=BG_INPUT, fg=FG_TEXT, insertbackground=FG_BRIGHT,
            font=("Segoe UI", 9), borderwidth=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=YELLOW, padx=8, pady=6,
        )
        self.ai_text.pack(fill=tk.BOTH, expand=True)

        # Configure rich text tags for AI panel (markdown rendering)
        configure_tags(self.ai_text)

        # Load history on startup
        self.root.after(500, self._refresh_history)

    def _on_close(self):
        """Clean shutdown — stop MCP servers and close window."""
        try:
            shutdown_agent()
        except Exception:
            pass
        self.root.destroy()

    # --- AI Answers ---
    def _toggle_ai(self):
        self._ai_enabled = self.ai_toggle_var.get()

    def _clear_ai_answers(self):
        self.ai_text.config(state=tk.NORMAL)
        self.ai_text.delete("1.0", tk.END)
        self.ai_text.config(state=tk.DISABLED)
        self._pending_questions.clear()

    def _ask_manual_question(self):
        question = self.manual_question_var.get().strip()
        if not question:
            return
        self.manual_question_var.set("")
        self._submit_question(question)

    def _submit_question(self, question):
        """Send a question to the AI agent and stream the answer."""
        # Deduplicate — don't ask the same question twice
        q_key = question.lower().strip()
        if q_key in self._pending_questions:
            return
        self._pending_questions.add(q_key)

        # Show the question in the panel
        self.ai_text.config(state=tk.NORMAL)
        if self.ai_text.get("1.0", "end-1c").strip():
            self.ai_text.insert(tk.END, "\n" + "─" * 50 + "\n", "separator")
        self.ai_text.insert(tk.END, f"❓ {question}\n", "question")
        self.ai_text.insert(tk.END, "⏳ Searching AWS docs...\n", "status")
        self.ai_text.see(tk.END)
        self.ai_text.config(state=tk.DISABLED)

        self._ai_streaming_started = False
        self._ai_md_streamer = MarkdownStreamer(self.ai_text)

        def on_chunk(text):
            self.root.after(0, self._append_ai_chunk, text)

        def on_result(answer, error):
            self.root.after(0, self._finish_ai_answer, error)

        ask_agent(question, callback=on_result, on_chunk=on_chunk)

    def _append_ai_chunk(self, text):
        """Append a streaming chunk to the AI answers panel with markdown rendering."""
        self.ai_text.config(state=tk.NORMAL)

        # Remove the "Searching..." status on first chunk
        if not self._ai_streaming_started:
            self._ai_streaming_started = True
            pos = self.ai_text.search("⏳ Searching AWS docs...", "1.0", tk.END)
            if pos:
                line_end = self.ai_text.index(f"{pos} lineend+1c")
                self.ai_text.delete(pos, line_end)

        self._ai_md_streamer.feed(text)
        self.ai_text.see(tk.END)
        self.ai_text.config(state=tk.DISABLED)

    def _finish_ai_answer(self, error):
        """Called when the AI answer is complete (or errored)."""
        self.ai_text.config(state=tk.NORMAL)

        if error:
            # Remove the "Searching..." status if still there
            pos = self.ai_text.search("⏳ Searching AWS docs...", "1.0", tk.END)
            if pos:
                line_end = self.ai_text.index(f"{pos} lineend+1c")
                self.ai_text.delete(pos, line_end)
            self.ai_text.insert(tk.END, f"⚠️ {error}\n", "status")
        else:
            # Flush any remaining buffered markdown
            if hasattr(self, "_ai_md_streamer"):
                self._ai_md_streamer.flush()
            # Add a trailing newline if needed
            content = self.ai_text.get("end-2c", "end-1c")
            if content != "\n":
                self.ai_text.insert(tk.END, "\n")

        self.ai_text.see(tk.END)
        self.ai_text.config(state=tk.DISABLED)

    def _check_transcript_for_questions(self, text):
        """Called on each final transcript line to check for AWS AI/ML questions."""
        if not self._ai_enabled:
            return
        if is_aws_aiml_question(text):
            question = extract_question(text)
            if question:
                self._submit_question(question)

    # --- History ---
    def _refresh_history(self):
        threading.Thread(target=self._load_history_bg, daemon=True).start()

    def _load_history_bg(self):
        try:
            customers = ["(All)"] + get_all_customers()
            selected = self.history_filter_var.get()
            customer = None if selected == "(All)" else selected
            items = list_sessions(customer)
            self.root.after(0, self._update_history_ui, customers, items)
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"History load error: {e}"))

    def _update_history_ui(self, customers, items):
        self.history_filter_combo["values"] = customers
        self._history_items = items
        self.history_list.delete(0, tk.END)
        for item in items:
            ts = item["timestamp"][:16].replace("T", " ")
            label = f"{item['customer_name']}  ·  {ts}"
            self.history_list.insert(tk.END, label)

    def _on_history_select(self, event):
        sel = self.history_list.curselection()
        if not sel:
            return
        item = self._history_items[sel[0]]
        self._current_transcript = item.get("transcript", "")
        self._current_notes = item.get("notes", "")

        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.delete("1.0", tk.END)
        self.transcript_text.insert(tk.END, self._current_transcript)
        self.transcript_text.config(state=tk.DISABLED)

        self.notes_text.config(state=tk.NORMAL)
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert(tk.END, self._current_notes)
        self.notes_text.config(state=tk.DISABLED)

        self.customer_var.set(item["customer_name"])
        self.export_docx_btn.config(state=tk.NORMAL)
        self.export_pdf_btn.config(state=tk.NORMAL)
        self.status_var.set(f"Loaded session from {item['timestamp'][:16]}")

    # --- Export ---
    def _export_docx(self):
        if not self._current_notes:
            messagebox.showinfo("Nothing to export", "No notes to export.")
            return
        customer = self.customer_var.get().strip() or "Notes"
        path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")],
            initialfile=f"{customer}_notes.docx",
        )
        if path:
            _md_to_docx(customer, self._current_notes, path)
            self.status_var.set(f"Exported: {path}")

    def _export_pdf(self):
        if not self._current_notes:
            messagebox.showinfo("Nothing to export", "No notes to export.")
            return
        customer = self.customer_var.get().strip() or "Notes"
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=f"{customer}_notes.pdf",
        )
        if not path:
            return
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Helvetica", size=11)
            for line in self._current_notes.split("\n"):
                stripped = line.strip()
                if stripped.startswith("## "):
                    pdf.set_font("Helvetica", "B", 14)
                    pdf.cell(0, 10, stripped[3:], new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Helvetica", size=11)
                elif stripped.startswith("# "):
                    pdf.set_font("Helvetica", "B", 16)
                    pdf.cell(0, 10, stripped[2:], new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("Helvetica", size=11)
                elif stripped:
                    pdf.multi_cell(0, 6, stripped)
                else:
                    pdf.ln(4)
            pdf.output(path)
            self.status_var.set(f"Exported: {path}")
        except ImportError:
            messagebox.showerror("Missing Library", "Install fpdf2: python -m pip install fpdf2")

    # --- Device loading ---
    def _load_devices(self):
        temp = LiveTranscriber()
        devices = temp.get_audio_devices()
        self._devices = devices
        names = [f"{i}: {name}" for i, name in devices]

        system_names = ["(None)"] + names
        mic_names = ["(None)"] + names

        self.system_device_combo["values"] = system_names
        self.mic_device_combo["values"] = mic_names

        cable_idx = None
        mic_idx = None
        for j, (i, name) in enumerate(devices):
            if "cable output" in name.lower() and "virtual cable" in name.lower() and cable_idx is None:
                cable_idx = j
            if "microphone" in name.lower() and mic_idx is None:
                mic_idx = j

        self.system_device_combo.current(cable_idx + 1 if cable_idx is not None else 0)
        self.mic_device_combo.current(mic_idx + 1 if mic_idx is not None else 0)

    def _get_selected_device(self, combo):
        idx = combo.current()
        if idx <= 0:
            return None
        return self._devices[idx - 1][0]

    # --- Transcript callbacks ---
    def _on_partial(self, text):
        self.root.after(0, self._safe_show_partial, text)

    def _on_final(self, text):
        self.root.after(0, self._safe_show_final, text)
        # Check for AWS AI/ML questions in final transcript lines
        self._check_transcript_for_questions(text)

    def _safe_show_partial(self, text):
        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.delete("partial_start", "end-1c")
        self.transcript_text.insert("partial_start", text)
        self.transcript_text.see(tk.END)
        self.transcript_text.config(state=tk.DISABLED)

    def _safe_show_final(self, text):
        self.transcript_text.config(state=tk.NORMAL)
        self.transcript_text.delete("partial_start", "end-1c")
        self.transcript_text.insert("partial_start", text + "\n")
        self.transcript_text.mark_set("partial_start", "end-1c")
        self.transcript_text.see(tk.END)
        self.transcript_text.config(state=tk.DISABLED)

    # --- Recording ---
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

        for widget in (self.transcript_text, self.notes_text):
            widget.config(state=tk.NORMAL)
            widget.delete("1.0", tk.END)
            widget.config(state=tk.DISABLED)

        self._current_transcript = ""
        self._current_notes = ""
        self._pending_questions.clear()
        self.export_docx_btn.config(state=tk.DISABLED)
        self.export_pdf_btn.config(state=tk.DISABLED)

        self.transcriber = LiveTranscriber(
            system_device=system_dev,
            mic_device=mic_dev,
            on_partial=self._on_partial,
            on_final=self._on_final,
        )
        self.transcriber.start()

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
        self._current_transcript = transcript

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
        self.root.after(0, self._prepare_notes_for_streaming)

        def on_chunk(text):
            self.root.after(0, self._append_notes_chunk, text)

        try:
            notes = generate_notes(transcript, customer, on_chunk=on_chunk)
            self._current_notes = notes
            filepath = save_notes(customer, notes)

            try:
                save_session(customer, transcript, notes, filepath)
            except Exception:
                pass

            self.root.after(0, lambda: self.status_var.set(f"Notes saved: {filepath}"))
            self.root.after(0, lambda: self.export_docx_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.export_pdf_btn.config(state=tk.NORMAL))
            self.root.after(0, self._refresh_history)
        except Exception as e:
            self.root.after(
                0, lambda: messagebox.showerror("Error", f"Failed to generate notes:\n{e}")
            )
            self.root.after(0, lambda: self.status_var.set("Error generating notes."))

    def _prepare_notes_for_streaming(self):
        self.notes_text.config(state=tk.NORMAL)
        self.notes_text.delete("1.0", tk.END)

    def _append_notes_chunk(self, text):
        self.notes_text.config(state=tk.NORMAL)
        self.notes_text.insert(tk.END, text)
        self.notes_text.see(tk.END)


def main():
    root = tk.Tk()
    CallNotesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
