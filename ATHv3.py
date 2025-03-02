import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import pyautogui
import time
import threading
import re

def format_time(seconds):
    """Return a string formatted as 'X hours, Y minutes' for a given number of seconds."""
    minutes = seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    return f"{int(hours)} hours, {int(minutes)} minutes"

class TypingSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Typing Simulator - ATHv3")
        self.simulation_paused = False
        self.simulation_stopped = False
        self.create_widgets()

    def create_widgets(self):
        # Create Notebook with tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # ----------------------------
        # Text Input Tab (Rich–Text Editor)
        # ----------------------------
        self.text_input_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_input_frame, text="Text Input")

        # Toolbar with Bold and Italic buttons
        toolbar_frame = tk.Frame(self.text_input_frame)
        toolbar_frame.pack(fill="x", padx=10, pady=(10, 0))
        bold_button = tk.Button(toolbar_frame, text="Bold", command=self.apply_bold)
        bold_button.pack(side="left", padx=5)
        italic_button = tk.Button(toolbar_frame, text="Italic", command=self.apply_italic)
        italic_button.pack(side="left", padx=5)

        # Rich–text editor
        self.text_input = scrolledtext.ScrolledText(
            self.text_input_frame, width=60, height=15, font=("TkDefaultFont", 12)
        )
        self.text_input.pack(fill="both", expand=True, padx=10, pady=5)
        self.text_input.bind("<KeyRelease>", self.on_text_change)
        # Bind CTRL+B and CTRL+I for formatting keybinds in the editor
        self.text_input.bind("<Control-b>", self.handle_ctrl_b)
        self.text_input.bind("<Control-B>", self.handle_ctrl_b)
        self.text_input.bind("<Control-i>", self.handle_ctrl_i)
        self.text_input.bind("<Control-I>", self.handle_ctrl_i)
        # Bind paste event to process markdown markers
        self.text_input.bind("<<Paste>>", self.handle_paste)
        # Configure tags for visual formatting
        self.text_input.tag_configure("bold", font=("TkDefaultFont", 12, "bold"))
        self.text_input.tag_configure("italic", font=("TkDefaultFont", 12, "italic"))
        self.text_input.tag_configure("bolditalic", font=("TkDefaultFont", 12, "bold italic"))

        self.start_button = tk.Button(self.text_input_frame, text="Start Typing", command=self.start_typing_thread)
        self.start_button.pack(padx=10, pady=10)

        self.progress_label = tk.Label(self.text_input_frame, text="Progress:")
        self.progress_label.pack(anchor="w", padx=10, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.text_input_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=5)

        self.time_remaining_label = tk.Label(self.text_input_frame, text="Estimated time remaining: N/A")
        self.time_remaining_label.pack(anchor="w", padx=10, pady=5)

        self.countdown_label = tk.Label(self.text_input_frame, text="")
        self.countdown_label.pack(anchor="w", padx=10, pady=5)

        # ----------------------------
        # Settings Tab
        # ----------------------------
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")

        # Basic Settings: Manual WPM or Auto‑Adjust mode
        self.basic_settings_frame = ttk.LabelFrame(self.settings_frame, text="Basic Settings")
        self.basic_settings_frame.pack(fill="x", padx=10, pady=5)

        self.auto_adjust_var = tk.IntVar()
        self.auto_adjust_check = tk.Checkbutton(
            self.basic_settings_frame,
            text="Auto Adjust Target Duration",
            variable=self.auto_adjust_var,
            command=self.on_auto_adjust_change
        )
        self.auto_adjust_check.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.wpm_label = tk.Label(self.basic_settings_frame, text="Typing speed (words per minute):")
        self.wpm_slider = tk.Scale(self.basic_settings_frame, from_=10, to=500, orient="horizontal",
                                   command=self.on_settings_change)
        self.wpm_slider.set(60)
        self.wpm_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.wpm_slider.grid(row=1, column=1, sticky="we", padx=5, pady=5)

        # Auto‑adjust mode controls (hidden by default)
        self.target_duration_label = tk.Label(self.basic_settings_frame, text="Target Duration (HH:MM):")
        self.target_duration_entry = tk.Entry(self.basic_settings_frame)
        self.target_duration_entry.insert(0, "00:10")  # Default: 10 minutes
        self.target_duration_entry.bind("<KeyRelease>", self.on_settings_change)
        self.computed_wpm_label = tk.Label(self.basic_settings_frame, text="Computed WPM: N/A")
        self.target_duration_label.grid_forget()
        self.target_duration_entry.grid_forget()
        self.computed_wpm_label.grid_forget()
        self.basic_settings_frame.columnconfigure(1, weight=1)

        # Pause Settings
        self.pause_settings_frame = ttk.LabelFrame(self.settings_frame, text="Pause Settings")
        self.pause_settings_frame.pack(fill="x", padx=10, pady=5)

        self.include_pauses_var = tk.IntVar()
        self.include_pauses_check = tk.Checkbutton(
            self.pause_settings_frame,
            text="Include Pauses",
            variable=self.include_pauses_var,
            command=self.on_settings_change
        )
        self.include_pauses_check.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.pause_controls_frame = tk.Frame(self.pause_settings_frame)
        self.pause_controls_frame.grid(row=1, column=0, columnspan=2, sticky="we")

        self.pause_sentence_label = tk.Label(self.pause_controls_frame, text="Pause after sentence (sec):")
        self.pause_sentence_slider = tk.Scale(self.pause_controls_frame, from_=0, to=10, orient="horizontal",
                                              resolution=0.1, command=self.on_settings_change)
        self.pause_sentence_slider.set(0.5)
        self.pause_sentence_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.pause_sentence_slider.grid(row=0, column=1, sticky="we", padx=5, pady=5)

        self.pause_paragraph_label = tk.Label(self.pause_controls_frame, text="Pause after paragraph (sec):")
        self.pause_paragraph_slider = tk.Scale(self.pause_controls_frame, from_=0, to=10, orient="horizontal",
                                               resolution=0.1, command=self.on_settings_change)
        self.pause_paragraph_slider.set(1.0)
        self.pause_paragraph_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.pause_paragraph_slider.grid(row=1, column=1, sticky="we", padx=5, pady=5)

        self.pause_mid_label = tk.Label(self.pause_controls_frame, text="Pause mid-sentence (sec):")
        self.pause_mid_slider = tk.Scale(self.pause_controls_frame, from_=0, to=5, orient="horizontal",
                                         resolution=0.1, command=self.on_settings_change)
        self.pause_mid_slider.set(0.1)
        self.pause_mid_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.pause_mid_slider.grid(row=2, column=1, sticky="we", padx=5, pady=5)

        self.pause_controls_frame.columnconfigure(1, weight=1)

        self.estimated_time_label = tk.Label(self.settings_frame, text="Estimated Typing Time: N/A")
        self.estimated_time_label.pack(padx=10, pady=10, anchor="w")

        # ----------------------------
        # About Tab
        # ----------------------------
        self.about_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.about_frame, text="About")
        about_text = (
            "Typing Simulator - ATHv3\n\n"
            "Developed by David Camick with the help of ChatGPT.\n\n"
            "This application simulates typing text into any text field, making it appear as if it was typed manually.\n"
            "It supports rich–text editing: you can copy/paste text into the editor, select text, and use the Bold and Italic buttons\n"
            "or press CTRL+B and CTRL+I to apply formatting. When the simulation runs, the program sends CTRL+B and CTRL+I keybinds\n"
            "at the appropriate times so that the formatted text is reproduced exactly as shown.\n\n"
            "You can adjust the typing speed manually (WPM) or enable auto‑adjust mode by specifying a target duration (HH:MM).\n"
            "You can also set pauses after sentences, paragraphs, or mid‑sentence.\n"
            "All times are shown in hours and minutes."
        )
        self.about_label = tk.Label(self.about_frame, text=about_text, justify="left")
        self.about_label.pack(padx=10, pady=10, anchor="w")

        self.update_estimated_time()

    # ---------- Keybind Handlers for Bold/Italic in Editor ----------
    def handle_ctrl_b(self, event):
        self.apply_bold()
        return "break"

    def handle_ctrl_i(self, event):
        self.apply_italic()
        return "break"

    # ---------- Pasting Handler: Convert Markdown Markers for Bold/Italic ----------
    def handle_paste(self, event):
        try:
            pasted = self.root.clipboard_get()
        except tk.TclError:
            return
        # Detect markdown markers for italic (*), bold (**), and bolditalic (***)
        if re.search(r"\*{1,3}.+?\*{1,3}", pasted):
            plain_text, spans = self.convert_markdown_to_formatting(pasted)
        else:
            plain_text, spans = pasted, []
        insert_index = self.text_input.index("insert")
        self.text_input.insert(insert_index, plain_text)
        for span in spans:
            start_offset, end_offset, tag = span
            start_index = self.text_input.index(f"{insert_index}+{start_offset}c")
            end_index = self.text_input.index(f"{insert_index}+{end_offset}c")
            self.text_input.tag_add(tag, start_index, end_index)
        return "break"

    def convert_markdown_to_formatting(self, text):
        """
        Convert simple markdown markers in pasted text into plain text and formatting spans.
        Supports:
          - *text* for italic
          - **text** for bold
          - ***text*** for bold italic
        Returns (plain_text, spans) where spans is a list of tuples (start_offset, end_offset, tag)
        """
        spans = []
        plain_text = ""
        last_end = 0
        # Use regex to find groups with 1 to 3 asterisks
        pattern = re.compile(r"(\*{1,3})(.+?)\1", re.DOTALL)
        for match in pattern.finditer(text):
            # Append text before the match
            plain_text += text[last_end:match.start()]
            start_in_plain = len(plain_text)
            plain_text += match.group(2)
            end_in_plain = len(plain_text)
            marker = match.group(1)
            if len(marker) == 1:
                tag = "italic"
            elif len(marker) == 2:
                tag = "bold"
            elif len(marker) == 3:
                tag = "bolditalic"
            spans.append((start_in_plain, end_in_plain, tag))
            last_end = match.end()
        plain_text += text[last_end:]
        return plain_text, spans

    # ---------- Helper: Check if a given index is in a tag range ----------
    def in_tag(self, index, tag):
        ranges = self.text_input.tag_ranges(tag)
        for i in range(0, len(ranges), 2):
            start = ranges[i]
            end = ranges[i+1]
            if self.text_input.compare(index, ">=", start) and self.text_input.compare(index, "<", end):
                return True
        return False

    # ---------- Rich–Text Extraction Using Tag Ranges ----------
    def get_formatted_text(self):
        raw_text = self.text_input.get("1.0", "end-1c")
        tokens = []
        if not raw_text:
            return tokens
        current_format = None
        current_text = ""
        for i, ch in enumerate(raw_text):
            index = self.text_input.index(f"1.0+{i}c")
            bold = self.in_tag(index, "bold") or self.in_tag(index, "bolditalic")
            italic = self.in_tag(index, "italic") or self.in_tag(index, "bolditalic")
            fmt = (bold, italic)
            if current_format is None:
                current_format = fmt
                current_text = ch
            elif fmt == current_format:
                current_text += ch
            else:
                tokens.append({"text": current_text, "bold": current_format[0], "italic": current_format[1]})
                current_text = ch
                current_format = fmt
        tokens.append({"text": current_text, "bold": current_format[0], "italic": current_format[1]})
        return tokens

    # ---------- Toolbar Formatting Methods ----------
    def apply_bold(self):
        try:
            start = self.text_input.index("sel.first")
            end = self.text_input.index("sel.last")
        except tk.TclError:
            return
        current_tags = set(self.text_input.tag_names("sel.first"))
        if "bold" in current_tags or "bolditalic" in current_tags:
            self.text_input.tag_remove("bold", start, end)
            self.text_input.tag_remove("bolditalic", start, end)
        else:
            if "italic" in current_tags:
                self.text_input.tag_remove("italic", start, end)
                self.text_input.tag_add("bolditalic", start, end)
            else:
                self.text_input.tag_add("bold", start, end)

    def apply_italic(self):
        try:
            start = self.text_input.index("sel.first")
            end = self.text_input.index("sel.last")
        except tk.TclError:
            return
        current_tags = set(self.text_input.tag_names("sel.first"))
        if "italic" in current_tags or "bolditalic" in current_tags:
            self.text_input.tag_remove("italic", start, end)
            self.text_input.tag_remove("bolditalic", start, end)
        else:
            if "bold" in current_tags:
                self.text_input.tag_remove("bold", start, end)
                self.text_input.tag_add("bolditalic", start, end)
            else:
                self.text_input.tag_add("italic", start, end)

    # ---------- Callbacks ----------
    def on_text_change(self, event=None):
        self.update_estimated_time()

    def on_settings_change(self, event=None):
        self.update_estimated_time()

    def on_auto_adjust_change(self, event=None):
        if self.auto_adjust_var.get():
            self.wpm_label.grid_remove()
            self.wpm_slider.grid_remove()
            self.target_duration_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
            self.target_duration_entry.grid(row=1, column=1, sticky="we", padx=5, pady=5)
            self.computed_wpm_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        else:
            self.target_duration_label.grid_remove()
            self.target_duration_entry.grid_remove()
            self.computed_wpm_label.grid_remove()
            self.wpm_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
            self.wpm_slider.grid(row=1, column=1, sticky="we", padx=5, pady=5)
        self.on_settings_change()

    def parse_target_duration(self):
        value = self.target_duration_entry.get().strip()
        parts = value.split(":")
        if len(parts) != 2:
            return None
        try:
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 3600 + minutes * 60
        except ValueError:
            return None

    def update_estimated_time(self):
        # For simulation, we use the raw text (ignoring visual formatting)
        text = self.text_input.get("1.0", "end-1c").rstrip("\n")
        if not text.strip():
            self.estimated_time_label.config(text="Estimated Typing Time: N/A")
            if self.auto_adjust_var.get():
                self.computed_wpm_label.config(text="Computed WPM: N/A")
            return
        total_chars = len(text)
        if self.auto_adjust_var.get():
            target_seconds = self.parse_target_duration()
            if target_seconds is None or target_seconds <= 0:
                self.estimated_time_label.config(text="Estimated Typing Time: Invalid target duration")
                self.computed_wpm_label.config(text="Computed WPM: N/A")
                return
            self.computed_wpm_label.config(text="Computed WPM: N/A")
            self.estimated_time_label.config(text=f"Target Duration: {format_time(target_seconds)}")
        else:
            wpm = self.wpm_slider.get()
            delay = 60 / (wpm * 5)  # Assume average word length of 5 characters.
            estimated_time = total_chars * delay
            self.estimated_time_label.config(text=f"Estimated Typing Time: {format_time(estimated_time)}")

    # ---------- Simulation Methods ----------
    def start_typing_thread(self):
        if hasattr(self, "typing_thread") and self.typing_thread.is_alive():
            messagebox.showwarning("Typing in Progress", "Typing simulation is already running.")
            return
        self.simulation_paused = False
        self.simulation_stopped = False
        self.typing_thread = threading.Thread(target=self.start_typing)
        self.typing_thread.daemon = True
        self.typing_thread.start()

    def start_typing(self):
        text = self.text_input.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showerror("Input Error", "Please enter the text you want to type.")
            return
        raw_text = text  # Use raw text as shown.
        total_chars = len(raw_text)
        if self.auto_adjust_var.get():
            target_seconds = self.parse_target_duration()
            if total_chars == 0:
                messagebox.showerror("Input Error", "No characters to type.")
                return
            if target_seconds is None or target_seconds <= 0:
                messagebox.showerror("Input Error", "Invalid target duration.")
                return
            delay = target_seconds / total_chars
        else:
            wpm = self.wpm_slider.get()
            delay = 60 / (wpm * 5)  # Average word = 5 characters.
        self.estimated_total_time = delay * total_chars
        self.show_estimated_time_popup(raw_text, delay)

    def show_estimated_time_popup(self, raw_text, delay):
        popup_text = f"Estimated time for completion is: {format_time(self.estimated_total_time)}."
        self.popup = tk.Toplevel(self.root)
        self.popup.title("Estimated Time")
        tk.Label(self.popup, text=popup_text).pack(padx=20, pady=10)
        button_frame = tk.Frame(self.popup)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Start Typing", command=lambda: self.begin_countdown(raw_text, delay)).pack(side="left", padx=5)
        tk.Button(button_frame, text="Go Back to Settings", command=self.popup.destroy).pack(side="right", padx=5)

    def begin_countdown(self, raw_text, delay):
        self.popup.destroy()
        self.countdown(5, raw_text, delay)

    def countdown(self, remaining, raw_text, delay):
        if remaining <= 0:
            self.countdown_label.config(text="")
            self.simulate_typing(raw_text, delay)
        else:
            self.countdown_label.config(text=f"You have {remaining} seconds to focus on the target text field...")
            self.root.after(1000, self.countdown, remaining - 1, raw_text, delay)

    def simulate_typing(self, raw_text, delay):
        tokens = self.get_formatted_text()
        start_time = time.time()
        prev_bold = False
        prev_italic = False
        for token in tokens:
            if self.simulation_stopped:
                break
            if token["bold"] != prev_bold:
                pyautogui.hotkey("ctrl", "b")
                prev_bold = token["bold"]
            if token["italic"] != prev_italic:
                pyautogui.hotkey("ctrl", "i")
                prev_italic = token["italic"]
            for ch in token["text"]:
                if self.simulation_stopped:
                    break
                if ch == "\n":
                    pyautogui.press("enter")
                elif ch == "\t":
                    pyautogui.press("tab")
                else:
                    pyautogui.typewrite(ch)
                time.sleep(delay)
                elapsed_time = time.time() - start_time
                progress = (elapsed_time / self.estimated_total_time) * 100
                self.progress_var.set(min(progress, 100))
                remaining_time = self.estimated_total_time - elapsed_time
                self.time_remaining_label.config(text=f"Estimated time remaining: {format_time(remaining_time)}")
                self.root.update_idletasks()
        if prev_bold:
            pyautogui.hotkey("ctrl", "b")
        if prev_italic:
            pyautogui.hotkey("ctrl", "i")
        self.progress_var.set(100)
        self.time_remaining_label.config(text="Estimated time remaining: 0 hours, 0 minutes")
        messagebox.showinfo("Done", "Typing simulation completed.")

def main():
    root = tk.Tk()
    app = TypingSimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
