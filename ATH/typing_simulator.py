import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
import pyautogui
import time
import threading
import random
import re

class TypingSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Typing Simulator")
        self.create_widgets()
        self.simulation_paused = False
        self.simulation_stopped = False

    def create_widgets(self):
        # Create Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Text Input Tab
        self.text_input_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_input_frame, text='Text Input')

        # Speed Settings Tab
        self.speed_settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.speed_settings_frame, text='Speed Settings')

        # About Tab
        self.about_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.about_frame, text='About')

        # --- Text Input Tab Widgets ---
        self.text_label = tk.Label(self.text_input_frame, text="Enter the text you want to type:")
        self.text_label.pack(anchor='w', padx=10, pady=5)

        self.text_input = scrolledtext.ScrolledText(self.text_input_frame, width=60, height=15)
        self.text_input.pack(padx=10, pady=5)

        # Start Button
        self.start_button = tk.Button(self.text_input_frame, text="Start Typing", command=self.start_typing_thread)
        self.start_button.pack(padx=10, pady=10)

        # Progress Bar and Time Remaining
        self.progress_label = tk.Label(self.text_input_frame, text="Progress:")
        self.progress_label.pack(anchor='w', padx=10, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.text_input_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=10, pady=5)

        self.time_remaining_label = tk.Label(self.text_input_frame, text="Estimated time remaining: N/A")
        self.time_remaining_label.pack(anchor='w', padx=10, pady=5)

        # Countdown Label
        self.countdown_label = tk.Label(self.text_input_frame, text="")
        self.countdown_label.pack(anchor='w', padx=10, pady=5)

        # --- Speed Settings Tab Widgets ---
        self.wpm_label = tk.Label(self.speed_settings_frame, text="Typing speed (words per minute):")
        self.wpm_label.pack(anchor='w', padx=10, pady=5)

        self.wpm_slider = tk.Scale(self.speed_settings_frame, from_=0, to=500, orient='horizontal')
        self.wpm_slider.set(60)  # Default WPM
        self.wpm_slider.pack(fill='x', padx=10, pady=5)

        # Include Pauses Checkbox
        self.include_pauses_var = tk.IntVar()
        self.include_pauses_check = tk.Checkbutton(self.speed_settings_frame, text="Include Pauses", variable=self.include_pauses_var, command=self.toggle_pauses)
        self.include_pauses_check.pack(anchor='w', padx=10, pady=5)

        # Pause Settings Frame
        self.pauses_frame = tk.Frame(self.speed_settings_frame)
        self.pauses_frame.pack(fill='x', padx=10, pady=5)

        # Pause after sentences
        self.pause_sentence_label = tk.Label(self.pauses_frame, text="Pause time after sentences (seconds):")
        self.pause_sentence_label.grid(row=0, column=0, sticky='w')
        self.pause_sentence_slider = tk.Scale(self.pauses_frame, from_=0, to=10, orient='horizontal', resolution=0.1)
        self.pause_sentence_slider.set(0)
        self.pause_sentence_slider.grid(row=0, column=1, sticky='we')

        # Pause after paragraphs
        self.pause_paragraph_label = tk.Label(self.pauses_frame, text="Pause time after paragraphs (seconds):")
        self.pause_paragraph_label.grid(row=1, column=0, sticky='w')
        self.pause_paragraph_slider = tk.Scale(self.pauses_frame, from_=0, to=10, orient='horizontal', resolution=0.1)
        self.pause_paragraph_slider.set(0)
        self.pause_paragraph_slider.grid(row=1, column=1, sticky='we')

        # Pause mid-sentence
        self.pause_mid_label = tk.Label(self.pauses_frame, text="Pause time mid-sentences (seconds):")
        self.pause_mid_label.grid(row=2, column=0, sticky='w')
        self.pause_mid_slider = tk.Scale(self.pauses_frame, from_=0, to=5, orient='horizontal', resolution=0.1)
        self.pause_mid_slider.set(0)
        self.pause_mid_slider.grid(row=2, column=1, sticky='we')

        # Pause time range
        self.pause_range_label = tk.Label(self.pauses_frame, text="Pause time range (min-max seconds):")
        self.pause_range_label.grid(row=3, column=0, sticky='w')
        self.pause_range_min_slider = tk.Scale(self.pauses_frame, from_=0, to=10, orient='horizontal', resolution=0.1, label="Min")
        self.pause_range_min_slider.set(1)
        self.pause_range_min_slider.grid(row=3, column=1, sticky='we')
        self.pause_range_max_slider = tk.Scale(self.pauses_frame, from_=0, to=10, orient='horizontal', resolution=0.1, label="Max")
        self.pause_range_max_slider.set(3)
        self.pause_range_max_slider.grid(row=3, column=2, sticky='we')

        # Initially hide pause settings if Include Pauses is not checked
        if not self.include_pauses_var.get():
            self.pauses_frame.pack_forget()

        # --- About Tab Widgets ---
        about_text = """
Typing Simulator

Developed by David Camick with the help of ChatGPT.

This application simulates typing text into any text field, making it appear as if it was typed manually. You can adjust the typing speed and include various pauses to simulate natural typing patterns.
"""
        self.about_label = tk.Label(self.about_frame, text=about_text, justify='left')
        self.about_label.pack(padx=10, pady=10, anchor='w')

        # Initialize pause settings
        self.pause_after_sentence = 0
        self.pause_after_paragraph = 0
        self.pause_mid_sentence = 0
        self.pause_time_range = (1, 3)  # Default pause time range in seconds

    def toggle_pauses(self):
        if self.include_pauses_var.get():
            self.pauses_frame.pack(fill='x', padx=10, pady=5)
        else:
            self.pauses_frame.pack_forget()

    def start_typing_thread(self):
        if hasattr(self, 'typing_thread') and self.typing_thread.is_alive():
            messagebox.showwarning("Typing in Progress", "Typing simulation is already running.")
            return
        self.simulation_paused = False
        self.simulation_stopped = False
        self.typing_thread = threading.Thread(target=self.start_typing)
        self.typing_thread.daemon = True
        self.typing_thread.start()

    def start_typing(self):
        text_input = self.text_input.get("1.0", tk.END)
        if not text_input.strip():
            messagebox.showerror("Input Error", "Please enter the text you want to type.")
            return

        wpm = self.wpm_slider.get()
        if wpm <= 0:
            messagebox.showerror("Input Error", "Please set a positive WPM.")
            return

        # Parse the text with formatting
        self.formatted_text = self.parse_formatted_text(text_input)

        # Get pause settings
        if self.include_pauses_var.get():
            self.pause_after_sentence = self.pause_sentence_slider.get()
            self.pause_after_paragraph = self.pause_paragraph_slider.get()
            self.pause_mid_sentence = self.pause_mid_slider.get()
            min_pause = self.pause_range_min_slider.get()
            max_pause = self.pause_range_max_slider.get()
            if min_pause > max_pause:
                messagebox.showerror("Input Error", "Minimum pause time cannot be greater than maximum pause time.")
                return
            self.pause_time_range = (min_pause, max_pause)
        else:
            self.pause_after_sentence = 0
            self.pause_after_paragraph = 0
            self.pause_mid_sentence = 0
            self.pause_time_range = (0, 0)

        # Estimate total time
        self.estimated_total_time = self.calculate_estimated_time(wpm)

        # Show estimated time popup
        self.show_estimated_time_popup()

    def calculate_estimated_time(self, wpm):
        total_words = sum(len(segment['text'].split()) for segment in self.formatted_text)
        time_per_word = 60 / wpm  # in seconds

        # Calculate total typing time
        total_typing_time = total_words * time_per_word

        # Calculate pauses
        sentence_pauses = self.count_sentences() * self.pause_after_sentence
        paragraph_pauses = self.count_paragraphs() * self.pause_after_paragraph
        mid_sentence_pauses = self.count_mid_sentence_pauses() * ((self.pause_time_range[0] + self.pause_time_range[1]) / 2)

        total_pause_time = sentence_pauses + paragraph_pauses + mid_sentence_pauses

        return total_typing_time + total_pause_time

    def count_sentences(self):
        text = ''.join(segment['text'] for segment in self.formatted_text)
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])

    def count_paragraphs(self):
        text = ''.join(segment['text'] for segment in self.formatted_text)
        paragraphs = text.split('\n\n')
        return len([p for p in paragraphs if p.strip()])

    def count_mid_sentence_pauses(self):
        text = ''.join(segment['text'] for segment in self.formatted_text)
        words = text.split()
        return len(words)  # Approximate mid-sentence pauses

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
        self.popup.destroy()
        self.countdown(5)

    def countdown(self, remaining):
        if remaining <= 0:
            self.countdown_label.config(text="")
            self.simulate_typing_thread()
        else:
            self.countdown_label.config(text=f"You have {remaining} seconds to focus on the target text field...")
            self.root.after(1000, self.countdown, remaining - 1)

    def simulate_typing_thread(self):
        self.typing_thread = threading.Thread(target=self.simulate_typing)
        self.typing_thread.daemon = True
        self.typing_thread.start()

    def simulate_typing(self):
        wpm = self.wpm_slider.get()
        time_per_word = 60 / wpm
        total_words = sum(len(segment['text'].split()) for segment in self.formatted_text)
        words_typed = 0
        start_time = time.time()
        estimated_total_time = self.estimated_total_time

        bold_on = False
        italic_on = False

        for segment in self.formatted_text:
            if self.simulation_stopped:
                break
            # Handle formatting
            if segment['bold'] != bold_on:
                pyautogui.hotkey('ctrl', 'b')
                bold_on = segment['bold']
            if segment['italic'] != italic_on:
                pyautogui.hotkey('ctrl', 'i')
                italic_on = segment['italic']

            # Split text into lines to handle line breaks
            lines = segment['text'].split('\n')
            for line_index, line in enumerate(lines):
                words = line.strip().split(' ')
                for word_index, word in enumerate(words):
                    if self.simulation_stopped:
                        break

                    pyautogui.typewrite(word)
                    words_typed += 1

                    if word_index < len(words) - 1:
                        # Mid-sentence pause
                        if self.pause_mid_sentence > 0:
                            time.sleep(self.pause_mid_sentence)
                        pyautogui.typewrite(' ')
                    time.sleep(time_per_word)

                    # Update progress bar and time remaining
                    elapsed_time = time.time() - start_time
                    progress = (elapsed_time / estimated_total_time) * 100
                    self.progress_var.set(min(progress, 100))
                    remaining_time = estimated_total_time - elapsed_time
                    self.time_remaining_label.config(text=f"Estimated time remaining: {max(0, remaining_time):.2f} seconds")
                    self.root.update_idletasks()

                # Pause after sentence
                if self.pause_after_sentence > 0 and re.search(r'[.!?]$', line.strip()):
                    time.sleep(self.pause_after_sentence)

                if line_index < len(lines) - 1:
                    pyautogui.press('enter')
                else:
                    pyautogui.typewrite(' ')

            # Pause after paragraph
            if self.pause_after_paragraph > 0 and line_index == len(lines) - 1:
                time.sleep(self.pause_after_paragraph)

        # Ensure formatting is reset
        if bold_on:
            pyautogui.hotkey('ctrl', 'b')
        if italic_on:
            pyautogui.hotkey('ctrl', 'i')

        self.progress_var.set(100)
        self.time_remaining_label.config(text=f"Estimated time remaining: 0.00 seconds")
        if not self.simulation_stopped:
            messagebox.showinfo("Done", "Typing simulation completed.")

    def parse_formatted_text(self, text):
        # Parse text for bold and italic formatting
        tokens = []
        # Pattern for bold, italic, and bold italic
        pattern = re.compile(r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*)', re.DOTALL)
        pos = 0
        for match in pattern.finditer(text):
            start, end = match.span()
            # Text before the match
            if start > pos:
                tokens.append({'text': text[pos:start], 'bold': False, 'italic': False})
            # Matched text
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
            tokens.append({'text': ' ', 'bold': False, 'italic': False})  # Add space after formatting
            pos = end
        # Text after the last match
        if pos < len(text):
            tokens.append({'text': text[pos:], 'bold': False, 'italic': False})
        return tokens

def main():
    root = tk.Tk()
    app = TypingSimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
