import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
import time
import threading
import re
import requests
import websocket
import json
import logging

# Configure logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class ChromeDebugger:
    def __init__(self, websocket_url):
        try:
            self.ws = websocket.create_connection(websocket_url, timeout=5)
        except Exception as e:
            logging.error(f"Failed to connect to WebSocket at {websocket_url}: {e}")
            raise
        self.message_id = 0

    def send_key_event(self, event_type, key, text=None):
        self.message_id += 1
        message = {
            "id": self.message_id,
            "method": "Input.dispatchKeyEvent",
            "params": {
                "type": event_type,
                "key": key
            }
        }
        if text is not None:
            message["params"]["text"] = text
        try:
            self.ws.send(json.dumps(message))
            # Removed waiting for a response (ws.recv()) as Chrome may not send one for every event.
        except Exception as e:
            logging.error(f"Error sending key event: {e}")

    def send_character(self, char):
        self.send_key_event("keyDown", char, text=char)
        self.send_key_event("keyUp", char)

    def send_enter(self):
        self.send_key_event("keyDown", "Enter", text="\n")
        self.send_key_event("keyUp", "Enter")

    def send_ctrl_hotkey(self, key):
        self.send_key_event("keyDown", "Control")
        self.send_key_event("keyDown", key, text=key)
        self.send_key_event("keyUp", key)
        self.send_key_event("keyUp", "Control")


class TypingSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Typing Simulator")
        self.simulation_stopped = False
        self.debugger = None  # Will hold our ChromeDebugger instance
        self.create_widgets()

    def create_widgets(self):
        # Main Notebook with three tabs: Text Input, Settings, About.
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Text Input Tab
        self.text_input_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_input_frame, text='Text Input')

        # Settings Tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text='Settings')

        # About Tab
        self.about_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.about_frame, text='About')

        # --- Text Input Tab Widgets ---
        self.text_label = tk.Label(self.text_input_frame, text="Enter the text you want to type:")
        self.text_label.pack(anchor='w', padx=10, pady=5)
        self.text_input = scrolledtext.ScrolledText(self.text_input_frame, width=60, height=15)
        self.text_input.pack(padx=10, pady=5)
        self.text_input.bind("<KeyRelease>", lambda event: self.update_estimated_time())

        self.start_button = tk.Button(self.text_input_frame, text="Start Typing", command=self.start_typing_thread)
        self.start_button.pack(padx=10, pady=10)

        self.progress_label = tk.Label(self.text_input_frame, text="Progress:")
        self.progress_label.pack(anchor='w', padx=10, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.text_input_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=10, pady=5)

        self.time_remaining_label = tk.Label(self.text_input_frame, text="Estimated time remaining: N/A")
        self.time_remaining_label.pack(anchor='w', padx=10, pady=5)
        self.countdown_label = tk.Label(self.text_input_frame, text="")
        self.countdown_label.pack(anchor='w', padx=10, pady=5)

        # --- Settings Tab Widgets ---
        self.wpm_label = tk.Label(self.settings_frame, text="Typing Speed (words per minute):")
        self.wpm_label.pack(anchor='w', padx=10, pady=5)
        self.wpm_slider = tk.Scale(self.settings_frame, from_=10, to=300, orient='horizontal',
                                   command=lambda val: self.update_estimated_time())
        self.wpm_slider.set(60)
        self.wpm_slider.pack(fill='x', padx=10, pady=5)

        self.punctuation_label = tk.Label(self.settings_frame, text="Extra Pause after Punctuation (seconds):")
        self.punctuation_label.pack(anchor='w', padx=10, pady=5)
        self.punctuation_slider = tk.Scale(self.settings_frame, from_=0, to=3, resolution=0.1, orient='horizontal',
                                           command=lambda val: self.update_estimated_time())
        self.punctuation_slider.set(0.5)
        self.punctuation_slider.pack(fill='x', padx=10, pady=5)

        self.newline_label = tk.Label(self.settings_frame, text="Extra Pause after Newline (seconds):")
        self.newline_label.pack(anchor='w', padx=10, pady=5)
        self.newline_slider = tk.Scale(self.settings_frame, from_=0, to=3, resolution=0.1, orient='horizontal',
                                       command=lambda val: self.update_estimated_time())
        self.newline_slider.set(0.5)
        self.newline_slider.pack(fill='x', padx=10, pady=5)

        self.estimated_time_label = tk.Label(self.settings_frame, text="Estimated Typing Duration: 0.00 seconds")
        self.estimated_time_label.pack(anchor='w', padx=10, pady=10)

        # --- About Tab Widgets ---
        about_text = (
            "Typing Simulator\n\n"
            "Developed by David Camick with the help of ChatGPT.\n\n"
            "This application types text into a Google Chrome tab in the background using "
            "Chrome's DevTools Protocol.\n\n"
            "IMPORTANT: Launch Chrome with remote debugging enabled. For example, run:\n"
            "\"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222 --remote-allow-origins=*"
        )
        self.about_label = tk.Label(self.about_frame, text=about_text, justify='left')
        self.about_label.pack(padx=10, pady=10, anchor='w')

    def update_estimated_time(self):
        try:
            raw_text = self.text_input.get("1.0", tk.END).strip()
            if not raw_text:
                self.estimated_time_label.config(text="Estimated Typing Duration: 0.00 seconds")
                return
            wpm = self.wpm_slider.get()
            base_delay = 60 / wpm
            punc_delay = self.punctuation_slider.get()
            newline_delay = self.newline_slider.get()
            words = raw_text.split()
            base_time = len(words) * base_delay
            punc_count = sum(raw_text.count(p) for p in ".!?")
            newline_count = raw_text.count("\n")
            total_estimated = base_time + punc_count * punc_delay + newline_count * newline_delay
            self.estimated_time_label.config(text=f"Estimated Typing Duration: {total_estimated:.2f} seconds")
        except Exception as e:
            self.estimated_time_label.config(text="Estimated Typing Duration: Error")

    def start_typing_thread(self):
        if hasattr(self, 'typing_thread') and self.typing_thread.is_alive():
            messagebox.showwarning("Typing in Progress", "Typing simulation is already running.")
            return
        self.simulation_stopped = False
        self.typing_thread = threading.Thread(target=self.start_typing)
        self.typing_thread.daemon = True
        self.typing_thread.start()

    def start_typing(self):
        raw_text = self.text_input.get("1.0", tk.END).strip()
        if not raw_text:
            messagebox.showerror("Input Error", "Please enter the text you want to type.")
            return
        self.formatted_text = self.parse_formatted_text(raw_text)
        self.estimated_total_time = self.compute_estimated_time(raw_text)
        self.show_estimated_time_popup()

    def compute_estimated_time(self, raw_text):
        try:
            wpm = self.wpm_slider.get()
            base_delay = 60 / wpm
            punc_delay = self.punctuation_slider.get()
            newline_delay = self.newline_slider.get()
            words = raw_text.split()
            base_time = len(words) * base_delay
            punc_count = sum(raw_text.count(p) for p in ".!?")
            newline_count = raw_text.count("\n")
            return base_time + punc_count * punc_delay + newline_count * newline_delay
        except Exception:
            return 0

    def show_estimated_time_popup(self):
        estimated_time_str = f"Estimated time for completion is: {self.estimated_total_time:.2f} seconds."
        self.popup = tk.Toplevel(self.root)
        self.popup.title("Estimated Time")
        tk.Label(self.popup, text=estimated_time_str).pack(padx=20, pady=10)
        button_frame = tk.Frame(self.popup)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Start Typing", command=self.begin_countdown).pack(side='left', padx=5)
        tk.Button(button_frame, text="Go Back to Settings", command=self.popup.destroy).pack(side='right', padx=5)

    def begin_countdown(self):
        self.debugger = self.connect_to_chrome()
        if not self.debugger:
            return
        self.popup.destroy()
        self.countdown(5)

    def countdown(self, remaining):
        if remaining <= 0:
            self.countdown_label.config(text="")
            self.simulate_typing_thread()
        else:
            self.countdown_label.config(text=f"Starting in {remaining} seconds... Ensure Chrome is ready.")
            self.root.after(1000, self.countdown, remaining - 1)

    def simulate_typing_thread(self):
        self.typing_thread = threading.Thread(target=self.simulate_typing)
        self.typing_thread.daemon = True
        self.typing_thread.start()

    def simulate_typing(self):
        wpm = self.wpm_slider.get()
        base_delay = 60 / wpm
        punc_delay = self.punctuation_slider.get()
        newline_delay = self.newline_slider.get()
        raw_text = self.text_input.get("1.0", tk.END).strip()
        if not raw_text:
            messagebox.showerror("Error", "No text to type.")
            return
        self.formatted_text = self.parse_formatted_text(raw_text)
        total_words = len(raw_text.split())
        words_typed = 0

        for segment in self.formatted_text:
            if self.simulation_stopped:
                break
            lines = segment['text'].split('\n')
            for li, line in enumerate(lines):
                words = line.split()
                for wi, word in enumerate(words):
                    if self.simulation_stopped:
                        break
                    self.send_text(word)
                    words_typed += 1
                    if wi < len(words) - 1:
                        self.send_text(" ")
                    time.sleep(base_delay)
                    if word and word[-1] in ".!?":
                        time.sleep(punc_delay)
                    progress = (words_typed / total_words) * 100
                    self.progress_var.set(min(progress, 100))
                if li < len(lines) - 1:
                    self.send_enter()
                    time.sleep(newline_delay)
        self.progress_var.set(100)
        self.time_remaining_label.config(text="Estimated time remaining: 0.00 seconds")
        messagebox.showinfo("Done", "Typing simulation completed.")

    def send_text(self, text, char_delay=0.01):
        for char in text:
            if char == "\n":
                self.send_enter()
            else:
                self.debugger.send_character(char)
            time.sleep(char_delay)

    def send_enter(self):
        self.debugger.send_enter()

    def connect_to_chrome(self):
        try:
            resp = requests.get("http://localhost:9222/json", timeout=5)
            tabs = resp.json()
            if not tabs:
                messagebox.showerror("Error", "No open Chrome tabs found with remote debugging enabled.")
                return None
            ws_url = tabs[0].get("webSocketDebuggerUrl")
            if not ws_url:
                messagebox.showerror("Error", "No WebSocket debugger URL found for the selected tab.")
                return None
            debugger = ChromeDebugger(ws_url)
            logging.info("Connected to Chrome via DevTools Protocol.")
            return debugger
        except Exception as e:
            logging.error(f"Failed to connect to Chrome: {e}")
            messagebox.showerror("Error", f"Failed to connect to Chrome: {e}")
            return None

    def parse_formatted_text(self, text):
        tokens = []
        pattern = re.compile(r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*)', re.DOTALL)
        pos = 0
        for match in pattern.finditer(text):
            start, end = match.span()
            if start > pos:
                tokens.append({'text': text[pos:start], 'bold': False, 'italic': False})
            matched_text = match.group()
            if matched_text.startswith('***') and matched_text.endswith('***'):
                content = matched_text[3:-3]
                tokens.append({'text': content, 'bold': True, 'italic': True})
            elif matched_text.startswith('**') and matched_text.endswith('**'):
                content = matched_text[2:-2]
                tokens.append({'text': content, 'bold': True, 'italic': False})
            elif matched_text.startswith('*') and matched_text.endswith('*'):
                content = matched_text[1:-1]
                tokens.append({'text': content, 'bold': False, 'italic': True})
            tokens.append({'text': ' ', 'bold': False, 'italic': False})
            pos = end
        if pos < len(text):
            tokens.append({'text': text[pos:], 'bold': False, 'italic': False})
        return tokens

def main():
    root = tk.Tk()
    app = TypingSimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
