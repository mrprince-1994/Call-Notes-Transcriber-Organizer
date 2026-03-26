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
    # Table tags
    text_widget.tag_configure("table_header", foreground="#eef0f2",
                              font=("Consolas", 10, "bold"), lmargin1=10, lmargin2=10)
    text_widget.tag_configure("table_cell", foreground="#c8ccd0",
                              font=("Consolas", 10), lmargin1=10, lmargin2=10)
    text_widget.tag_configure("table_border", foreground="#4b5563",
                              font=("Consolas", 10), lmargin1=10, lmargin2=10)
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

    def _flush_table(self):
        """Render accumulated table rows as a formatted table."""
        if not self._table_rows:
            return
        w = self._widget

        # Filter out separator rows (|---|---|)
        data_rows = []
        for row in self._table_rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            # Skip separator rows like |---|---|
            if all(re.match(r"^:?-+:?$", c) for c in cells if c):
                continue
            data_rows.append(cells)

        if not data_rows:
            self._table_rows = []
            return

        # Calculate column widths
        num_cols = max(len(r) for r in data_rows)
        col_widths = [0] * num_cols
        for row in data_rows:
            for i, cell in enumerate(row):
                if i < num_cols:
                    col_widths[i] = max(col_widths[i], len(_strip_md_inline(cell)))

        # Pad each column to at least a minimum width
        col_widths = [max(w, 6) for w in col_widths]

        # Render each row
        for row_idx, row in enumerate(data_rows):
            # Pad row to num_cols
            while len(row) < num_cols:
                row.append("")
            is_header = (row_idx == 0)
            for col_idx, cell in enumerate(row):
                cell_text = cell.strip()
                padded = cell_text.ljust(col_widths[col_idx])
                if col_idx == 0:
                    w.insert(tk.END, "  ", "table_cell")
                tag = "table_header" if is_header else "table_cell"
                _insert_inline(w, padded, tag)
                if col_idx < num_cols - 1:
                    w.insert(tk.END, " │ ", "table_border")
            w.insert(tk.END, "\n")
            # Draw separator after header
            if is_header:
                sep = "  "
                for ci, cw in enumerate(col_widths):
                    sep += "─" * cw
                    if ci < num_cols - 1:
                        sep += "─┼─"
                w.insert(tk.END, sep + "\n", "table_border")

        w.insert(tk.END, "\n")
        self._table_rows = []

    def _render_line(self, line: str):
        """Render a single line with markdown formatting."""
        w = self._widget
        stripped = line.strip()

        # DEBUG: uncomment to see what lines are being rendered
        # print(f"[md_render] LINE: {repr(stripped[:120])}")

        # Table row detection: lines that start with |
        if stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 3:
            self._table_rows.append(stripped)
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
