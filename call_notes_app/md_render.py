"""Lightweight markdown-to-Tkinter renderer for the AI Answers panel.

Converts streaming markdown chunks into styled Tkinter text widget inserts.
Handles: headers, bold, bullets, code spans, links, and horizontal rules.
"""
import re
import tkinter as tk
import webbrowser

# Regex patterns
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
_BARE_URL_RE = re.compile(r"(?<!\()(https?://[^\s\)\]>,]+)")

# Counter for unique link tag names
_link_counter = 0


def configure_tags(text_widget):
    """Set up all the text tags on a ScrolledText widget."""
    text_widget.tag_configure("h1", font=("Segoe UI Semibold", 15), foreground="#eef0f2",
                              spacing1=6, spacing3=1)
    text_widget.tag_configure("h2", font=("Segoe UI Semibold", 12), foreground="#10a37f",
                              spacing1=4, spacing3=1)
    text_widget.tag_configure("h3", font=("Segoe UI Semibold", 11), foreground="#6ee7b7",
                              spacing1=3, spacing3=1)
    text_widget.tag_configure("bold", font=("Segoe UI Semibold", 10), foreground="#eef0f2")
    text_widget.tag_configure("code", font=("Consolas", 10), foreground="#6ee7b7",
                              background="#0f1a26")
    text_widget.tag_configure("bullet", foreground="#c8ccd0", lmargin1=20, lmargin2=34,
                              font=("Segoe UI", 10), spacing1=1, spacing3=1)
    text_widget.tag_configure("body", foreground="#c8ccd0", font=("Segoe UI", 10),
                              spacing1=0, spacing3=0)
    text_widget.tag_configure("hr", foreground="#1f2937", font=("Segoe UI", 2),
                              spacing1=3, spacing3=3)
    text_widget.tag_configure("link", foreground="#60a5fa", font=("Segoe UI", 10),
                              underline=True)
    # Change cursor to hand when hovering over links
    text_widget.tag_bind("link", "<Enter>",
                         lambda e: text_widget.config(cursor="hand2"))
    text_widget.tag_bind("link", "<Leave>",
                         lambda e: text_widget.config(cursor=""))
    # Keep existing tags for question/status/separator
    text_widget.tag_configure("question", foreground="#fbbf24",
                              font=("Segoe UI Semibold", 11))
    text_widget.tag_configure("status", foreground="#9ca3af",
                              font=("Segoe UI Italic", 10))
    text_widget.tag_configure("separator", foreground="#374151")


class MarkdownStreamer:
    """Buffers streaming text and renders complete lines as rich text."""

    def __init__(self, text_widget):
        self._widget = text_widget
        self._buffer = ""
        self._table_rows = []  # accumulate table rows for batch rendering

    def feed(self, chunk: str):
        """Feed a streaming chunk. Renders complete lines immediately."""
        self._buffer += chunk

        # Pre-process buffer: force inline bullets onto separate lines
        self._buffer = re.sub(r'(?<!\n)\s+•\s+', '\n- ', self._buffer)
        self._buffer = re.sub(r'(?<!\n)\s{2,}-\s+', '\n- ', self._buffer)

        # Process all complete lines (ending with \n)
        while "\n" in self._buffer:
            idx = self._buffer.index("\n")
            line = self._buffer[:idx]
            self._buffer = self._buffer[idx + 1:]
            self._render_line(line)

    def flush(self):
        """Render any remaining buffered text."""
        if self._buffer:
            self._buffer = re.sub(r'\s+•\s+', '\n- ', self._buffer)
            self._buffer = re.sub(r'\s{2,}-\s+', '\n- ', self._buffer)
            while "\n" in self._buffer:
                idx = self._buffer.index("\n")
                line = self._buffer[:idx]
                self._buffer = self._buffer[idx + 1:]
                self._render_line(line)
            if self._buffer:
                self._render_line(self._buffer)
                self._buffer = ""
        # Flush any pending table rows
        if self._table_rows:
            self._flush_table()

    # Counter for unique table tag names
    _table_counter = 0

    def _flush_table(self):
        """Render table as a static PhotoImage — zero scroll overhead."""
        if not self._table_rows:
            return
        w = self._widget

        # Filter out separator rows (|---|---|)
        data_rows = []
        for row in self._table_rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            if all(re.match(r"^:?-+:?$", c) for c in cells if c):
                continue
            data_rows.append(cells)

        if not data_rows:
            self._table_rows = []
            return

        num_cols = max(len(r) for r in data_rows)
        for row in data_rows:
            while len(row) < num_cols:
                row.append("")

        from PIL import Image, ImageDraw, ImageFont, ImageTk

        # Style
        HDR_BG = (16, 163, 127)
        HDR_FG = (238, 240, 242)
        EVEN_BG = (17, 24, 39)
        ODD_BG = (13, 13, 20)
        CELL_FG = (200, 204, 208)
        GRID_CLR = (255, 255, 255)
        PAD_X, PAD_Y = 10, 7

        # Load fonts — fall back to default if Segoe UI not found
        try:
            f_hdr = ImageFont.truetype("segoeuib.ttf", 13)
            f_cell = ImageFont.truetype("segoeui.ttf", 13)
        except OSError:
            f_hdr = ImageFont.load_default()
            f_cell = ImageFont.load_default()

        # Measure columns and rows
        tmp = Image.new("RGB", (1, 1))
        draw_tmp = ImageDraw.Draw(tmp)

        col_widths = [0] * num_cols
        row_heights = []

        for row_idx, row in enumerate(data_rows):
            font = f_hdr if row_idx == 0 else f_cell
            max_h = 0
            for col_idx, cell in enumerate(row):
                text = _strip_md_inline(cell.strip())
                bbox = draw_tmp.textbbox((0, 0), text, font=font)
                tw = bbox[2] - bbox[0] + PAD_X * 2
                th = bbox[3] - bbox[1] + PAD_Y * 2
                col_widths[col_idx] = max(col_widths[col_idx], tw)
                max_h = max(max_h, th)
            row_heights.append(max_h)

        col_widths = [max(cw, 50) for cw in col_widths]

        total_w = sum(col_widths) + num_cols + 1
        total_h = sum(row_heights) + len(data_rows) + 1

        # Draw the table image
        img = Image.new("RGB", (total_w, total_h), (10, 10, 10))
        draw = ImageDraw.Draw(img)

        # Cell backgrounds and text
        y = 1
        for row_idx, row in enumerate(data_rows):
            is_header = (row_idx == 0)
            bg = HDR_BG if is_header else (EVEN_BG if row_idx % 2 == 1 else ODD_BG)
            fg = HDR_FG if is_header else CELL_FG
            font = f_hdr if is_header else f_cell
            rh = row_heights[row_idx]

            x = 1
            for col_idx, cell in enumerate(row):
                cw = col_widths[col_idx]
                draw.rectangle([x, y, x + cw - 1, y + rh - 1], fill=bg)
                text = _strip_md_inline(cell.strip())
                draw.text((x + PAD_X, y + PAD_Y), text, fill=fg, font=font)
                x += cw + 1
            y += rh + 1

        # Grid lines
        y = 0
        for row_idx in range(len(data_rows) + 1):
            draw.line([(0, y), (total_w, y)], fill=GRID_CLR, width=1)
            if row_idx < len(data_rows):
                y += row_heights[row_idx] + 1

        x = 0
        for col_idx in range(num_cols + 1):
            draw.line([(x, 0), (x, total_h)], fill=GRID_CLR, width=1)
            if col_idx < num_cols:
                x += col_widths[col_idx] + 1

        # Convert to PhotoImage and embed as an image in the Text widget
        photo = ImageTk.PhotoImage(img)

        # Keep a reference so it doesn't get garbage collected
        if not hasattr(w, "_table_images"):
            w._table_images = []
        w._table_images.append(photo)

        w.insert(tk.END, "\n")
        w.image_create(tk.END, image=photo, padx=10, pady=4)
        w.insert(tk.END, "\n\n")

        self._table_rows = []


    def _render_line(self, line: str):
        """Render a single line with markdown formatting."""
        w = self._widget
        stripped = line.strip()

        # DEBUG: uncomment to see what lines are being rendered
        # print(f"[md_render] LINE: {repr(stripped[:120])}")
        # with open("md_render_debug.log", "a") as dbg:
        #     dbg.write(f"LINE: {repr(stripped[:200])}\n")

        # Table row detection: lines that start with |
        if stripped.startswith("|") and stripped.count("|") >= 3:
            self._table_rows.append(stripped)
            return
        # Also catch separator rows like |---|---| or |:---|:---|
        elif re.match(r"^\|[\s:]*-+", stripped):
            self._table_rows.append(stripped)
            return
        elif self._table_rows and not stripped:
            # Tolerate a single blank line inside a table (streaming artifact)
            return
        else:
            # If we were accumulating table rows, flush them now
            if self._table_rows:
                self._flush_table()

        # Horizontal rule
        if stripped and all(c == "-" for c in stripped) and len(stripped) >= 3:
            w.insert(tk.END, "─" * 40 + "\n", "hr")
            return

        # Headers
        if stripped.startswith("### "):
            text = stripped[4:].strip()
            text = _strip_md_inline(text)
            w.insert(tk.END, text + "\n", "h3")
            return
        if stripped.startswith("## "):
            text = stripped[3:].strip()
            text = _strip_md_inline(text)
            w.insert(tk.END, text + "\n", "h2")
            return
        if stripped.startswith("# "):
            text = stripped[2:].strip()
            text = _strip_md_inline(text)
            w.insert(tk.END, text + "\n", "h1")
            return

        # Bullet points (- or *)
        if stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:]
            w.insert(tk.END, "  •  ", "bullet")
            _insert_inline(w, content, "bullet")
            w.insert(tk.END, "\n", "bullet")
            return

        # Numbered lists
        m = re.match(r"^(\d+)\.\s+", stripped)
        if m:
            num = m.group(1)
            content = stripped[m.end():]
            w.insert(tk.END, f"  {num}.  ", "bullet")
            _insert_inline(w, content, "bullet")
            w.insert(tk.END, "\n", "bullet")
            return

        # Empty line = small paragraph break (not a full blank line)
        if not stripped:
            return

        # Detect inline bullets: text containing " • " that should be separate lines
        # This handles cases where Claude outputs "• item1  • item2  • item3" inline
        if "•" in stripped or "  - " in stripped:
            # Split on bullet markers
            parts = re.split(r"\s*[•]\s*|\s{2,}-\s+", stripped)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) > 1:
                for part in parts:
                    w.insert(tk.END, "  •  ", "bullet")
                    _insert_inline(w, part, "bullet")
                    w.insert(tk.END, "\n", "bullet")
                return

        # Regular text with inline formatting
        _insert_inline(w, line, "body")
        w.insert(tk.END, "\n", "body")


def _strip_md_inline(text: str) -> str:
    """Remove markdown inline formatting for plain display (headers)."""
    text = _LINK_RE.sub(r"\1", text)
    text = _BOLD_RE.sub(r"\1", text)
    text = _CODE_RE.sub(r"\1", text)
    return text


def _insert_inline(widget, text: str, base_tag: str):
    """Insert text with inline bold, code, and link formatting."""
    global _link_counter
    pos = 0
    spans = []

    # Collect bold spans
    for m in _BOLD_RE.finditer(text):
        spans.append((m.start(), m.end(), "bold", m.group(1), None))
    # Collect code spans
    for m in _CODE_RE.finditer(text):
        spans.append((m.start(), m.end(), "code", m.group(1), None))
    # Collect markdown links [text](url)
    for m in _LINK_RE.finditer(text):
        spans.append((m.start(), m.end(), "link", m.group(1), m.group(2)))
    # Collect bare URLs (only if not already inside a markdown link)
    for m in _BARE_URL_RE.finditer(text):
        # Skip if this URL is part of a markdown link
        is_inside_md_link = False
        for s in spans:
            if s[2] == "link" and s[0] <= m.start() < s[1]:
                is_inside_md_link = True
                break
        if not is_inside_md_link:
            spans.append((m.start(), m.end(), "link", m.group(0), m.group(0)))

    # Sort by position
    spans.sort(key=lambda s: s[0])

    # Remove overlapping spans (keep first)
    filtered = []
    last_end = 0
    for start, end, tag, content, url in spans:
        if start >= last_end:
            filtered.append((start, end, tag, content, url))
            last_end = end

    for start, end, tag, content, url in filtered:
        if pos < start:
            widget.insert(tk.END, text[pos:start], base_tag)
        if tag == "link" and url:
            # Create a unique tag for this link so each has its own click handler
            _link_counter += 1
            link_tag = f"link_{_link_counter}"
            widget.tag_configure(link_tag, foreground="#60a5fa", font=("Segoe UI", 10),
                                 underline=True)
            link_url = url  # capture for closure
            widget.tag_bind(link_tag, "<Button-1>",
                            lambda e, u=link_url: webbrowser.open(u))
            widget.tag_bind(link_tag, "<Enter>",
                            lambda e: widget.config(cursor="hand2"))
            widget.tag_bind(link_tag, "<Leave>",
                            lambda e: widget.config(cursor=""))
            widget.insert(tk.END, content, ("link", link_tag))
        else:
            widget.insert(tk.END, content, tag)
        pos = end

    if pos < len(text):
        widget.insert(tk.END, text[pos:], base_tag)
