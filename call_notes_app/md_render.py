"""Lightweight markdown-to-Tkinter renderer for the AI Answers panel.

Converts streaming markdown chunks into styled Tkinter text widget inserts.
Handles: headers, bold, bullets, code spans, and horizontal rules.
"""
import re
import tkinter as tk

# Regex patterns
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_CODE_RE = re.compile(r"`([^`]+)`")


def configure_tags(text_widget):
    """Set up all the text tags on a ScrolledText widget."""
    text_widget.tag_configure("h1", font=("Segoe UI Semibold", 14), foreground="#f9e2af",
                              spacing1=8, spacing3=4)
    text_widget.tag_configure("h2", font=("Segoe UI Semibold", 12), foreground="#89b4fa",
                              spacing1=6, spacing3=3)
    text_widget.tag_configure("h3", font=("Segoe UI Semibold", 11), foreground="#74c7ec",
                              spacing1=4, spacing3=2)
    text_widget.tag_configure("bold", font=("Segoe UI Semibold", 9), foreground="#ffffff")
    text_widget.tag_configure("code", font=("Consolas", 9), foreground="#a6e3a1",
                              background="#313150")
    text_widget.tag_configure("bullet", foreground="#cdd6f4", lmargin1=16, lmargin2=28,
                              font=("Segoe UI", 9))
    text_widget.tag_configure("body", foreground="#cdd6f4", font=("Segoe UI", 9))
    text_widget.tag_configure("hr", foreground="#45475a", font=("Segoe UI", 6),
                              spacing1=4, spacing3=4)
    # Keep existing tags for question/status/separator
    text_widget.tag_configure("question", foreground="#f9e2af",
                              font=("Segoe UI Semibold", 10))
    text_widget.tag_configure("status", foreground="#7f849c",
                              font=("Segoe UI Italic", 9))
    text_widget.tag_configure("separator", foreground="#45475a")


class MarkdownStreamer:
    """Buffers streaming text and renders complete lines as rich text."""

    def __init__(self, text_widget):
        self._widget = text_widget
        self._buffer = ""

    def feed(self, chunk: str):
        """Feed a streaming chunk. Renders complete lines immediately."""
        self._buffer += chunk
        # Process all complete lines (ending with \n)
        while "\n" in self._buffer:
            idx = self._buffer.index("\n")
            line = self._buffer[:idx]
            self._buffer = self._buffer[idx + 1:]
            self._render_line(line)

    def flush(self):
        """Render any remaining buffered text."""
        if self._buffer:
            self._render_line(self._buffer)
            self._buffer = ""

    def _render_line(self, line: str):
        """Render a single line with markdown formatting."""
        w = self._widget
        stripped = line.strip()

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

        # Empty line = paragraph break
        if not stripped:
            w.insert(tk.END, "\n", "body")
            return

        # Regular text with inline formatting
        _insert_inline(w, line, "body")
        w.insert(tk.END, "\n", "body")


def _strip_md_inline(text: str) -> str:
    """Remove markdown inline formatting for plain display (headers)."""
    text = _BOLD_RE.sub(r"\1", text)
    text = _CODE_RE.sub(r"\1", text)
    return text


def _insert_inline(widget, text: str, base_tag: str):
    """Insert text with inline bold and code formatting."""
    # Split on bold and code patterns, inserting with appropriate tags
    pos = 0
    # Find all bold and code spans
    spans = []
    for m in _BOLD_RE.finditer(text):
        spans.append((m.start(), m.end(), "bold", m.group(1)))
    for m in _CODE_RE.finditer(text):
        spans.append((m.start(), m.end(), "code", m.group(1)))

    # Sort by position
    spans.sort(key=lambda s: s[0])

    # Remove overlapping spans (keep first)
    filtered = []
    last_end = 0
    for start, end, tag, content in spans:
        if start >= last_end:
            filtered.append((start, end, tag, content))
            last_end = end

    for start, end, tag, content in filtered:
        if pos < start:
            widget.insert(tk.END, text[pos:start], base_tag)
        widget.insert(tk.END, content, tag)
        pos = end

    if pos < len(text):
        widget.insert(tk.END, text[pos:], base_tag)
