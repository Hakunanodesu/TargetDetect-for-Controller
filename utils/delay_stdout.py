import tkinter as tk


class DelayedStdoutRedirector:
    def __init__(self, text_widget, interval_ms=50):
        self.text_widget = text_widget
        self.interval = interval_ms
        self.queue = []
        self.processing = False

    def write(self, s):
        # Split text into lines and enqueue
        lines = [line + '\n' for line in s.splitlines() if line.strip()]
        self.queue.extend(lines)
        if not self.processing:
            self.processing = True
            self._process_queue()

    def _process_queue(self):
        if self.queue:
            line = self.queue.pop(0)
            self.text_widget.config(state='normal')
            self.text_widget.insert(tk.END, line)
            self.text_widget.see(tk.END)
            self.text_widget.config(state='disabled')
            self.text_widget.after(self.interval, self._process_queue)
        else:
            self.processing = False

    def flush(self):
        pass