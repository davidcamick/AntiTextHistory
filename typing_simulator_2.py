import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
import pyautogui
import time
import threading
import random
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class TypingSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Typing Simulator")
        self.load_notification_settings()  # Load settings first
        self.create_widgets()  # Then create widgets that use those settings
        self.simulation_paused = False
        self.simulation_stopped = False
        
        # Bind text changes to update estimated time
        self.text_input.bind("<<Modified>>", self.on_text_modified)
        self.text_modified_flag = False

    def load_notification_settings(self):
        # Email settings with hardcoded credentials
        self.email_settings = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'davidpaulcamick@gmail.com',  # Hardcoded email
            'sender_password': 'algg ptxq yiek gism',  # Hardcoded app password
            'recipient_phone': '4047250528',  # Your phone number
            'carrier': 'att'  # Your carrier (att, verizon, tmobile, sprint)
        }
        
        # Carrier email domains
        self.carrier_domains = {
            'att': 'txt.att.net',
            'verizon': 'vtext.com',
            'tmobile': 'tmomail.net',
            'sprint': 'messaging.sprintpcs.com'
        }

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

        self.wpm_slider = tk.Scale(self.speed_settings_frame, from_=0, to=500, orient='horizontal', command=self.update_estimated_time)
        self.wpm_slider.set(60)  # Default WPM
        self.wpm_slider.pack(fill='x', padx=10, pady=5)

        # Real-time estimated time label
        self.estimated_time_frame = tk.Frame(self.speed_settings_frame, bd=2, relief=tk.GROOVE)
        self.estimated_time_frame.pack(fill='x', padx=10, pady=5)
        
        self.estimated_time_label = tk.Label(self.estimated_time_frame, 
                                           text="Estimated completion time: calculating...",
                                           font=("Arial", 10, "bold"))
        self.estimated_time_label.pack(pady=8, padx=5)

        # Include Pauses Checkbox
        self.include_pauses_var = tk.IntVar()
        self.include_pauses_check = tk.Checkbutton(self.speed_settings_frame, text="Include Pauses", variable=self.include_pauses_var, command=self.toggle_pauses)
        self.include_pauses_check.pack(anchor='w', padx=10, pady=5)

        # Pause Settings Frame
        self.pauses_frame = tk.Frame(self.speed_settings_frame)
        self.pauses_frame.pack(fill='x', padx=10, pady=5)

        # Pause chance after sentences
        self.pause_sentence_label = tk.Label(self.pauses_frame, text="Chance to pause after EACH sentence (%):")
        self.pause_sentence_label.grid(row=0, column=0, sticky='w')
        self.pause_sentence_slider = tk.Scale(self.pauses_frame, from_=0, to=100, orient='horizontal', resolution=1, command=self.update_estimated_time)
        self.pause_sentence_slider.set(50)  # Default 50% chance
        self.pause_sentence_slider.grid(row=0, column=1, sticky='we')

        # Pause chance after paragraphs
        self.pause_paragraph_label = tk.Label(self.pauses_frame, text="Chance to pause after EACH paragraph (%):")
        self.pause_paragraph_label.grid(row=1, column=0, sticky='w')
        self.pause_paragraph_slider = tk.Scale(self.pauses_frame, from_=0, to=100, orient='horizontal', resolution=1, command=self.update_estimated_time)
        self.pause_paragraph_slider.set(80)  # Default 80% chance
        self.pause_paragraph_slider.grid(row=1, column=1, sticky='we')

        # Pause chance mid-sentence
        self.pause_mid_label = tk.Label(self.pauses_frame, text="Chance to pause at punctuation (%):")
        self.pause_mid_label.grid(row=2, column=0, sticky='w')
        self.pause_mid_slider = tk.Scale(self.pauses_frame, from_=0, to=100, orient='horizontal', resolution=1, command=self.update_estimated_time)
        self.pause_mid_slider.set(10)  # Default 10% chance
        self.pause_mid_slider.grid(row=2, column=1, sticky='we')

        # Pause time range
        self.pause_range_label = tk.Label(self.pauses_frame, text="Pause duration range (seconds):")
        self.pause_range_label.grid(row=3, column=0, sticky='w')
        self.pause_range_min_slider = tk.Scale(self.pauses_frame, from_=0, to=10, orient='horizontal', resolution=0.1, label="Min", command=self.update_estimated_time)
        self.pause_range_min_slider.set(0.2)  # Small minimum
        self.pause_range_min_slider.grid(row=3, column=1, sticky='we')
        self.pause_range_max_slider = tk.Scale(self.pauses_frame, from_=0, to=10, orient='horizontal', resolution=0.1, label="Max", command=self.update_estimated_time)
        self.pause_range_max_slider.set(2.0)  # Reasonable maximum
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

        # Add Notifications Tab
        self.notifications_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.notifications_frame, text='Notifications')

        # Email Notification Settings
        self.email_frame = ttk.LabelFrame(self.notifications_frame, text="Email & SMS Notifications")
        self.email_frame.pack(fill='x', padx=10, pady=5)

        self.enable_notification_var = tk.BooleanVar(value=True)  # Enable by default
        self.enable_notification_check = tk.Checkbutton(self.email_frame, text="Enable Notifications", 
                                                       variable=self.enable_notification_var)
        self.enable_notification_check.pack(anchor='w', padx=5, pady=5)
        
        # Email Configuration - Pre-filled with hardcoded values
        tk.Label(self.email_frame, text="Gmail Address:").pack(anchor='w', padx=5, pady=2)
        self.email_entry = tk.Entry(self.email_frame, width=40)
        self.email_entry.insert(0, self.email_settings['sender_email'])  # Pre-fill with hardcoded email
        self.email_entry.pack(fill='x', padx=5, pady=2)
        
        tk.Label(self.email_frame, text="Gmail App Password:").pack(anchor='w', padx=5, pady=2)
        self.password_entry = tk.Entry(self.email_frame, width=40, show="*")
        self.password_entry.insert(0, self.email_settings['sender_password'])  # Pre-fill with hardcoded password
        self.password_entry.pack(fill='x', padx=5, pady=2)
        
        # Phone number is pre-filled based on your provided number
        tk.Label(self.email_frame, text="Phone Number:").pack(anchor='w', padx=5, pady=2)
        self.phone_entry = tk.Entry(self.email_frame, width=40)
        self.phone_entry.insert(0, self.email_settings['recipient_phone'])  # Pre-fill with your number
        self.phone_entry.pack(fill='x', padx=5, pady=2)
        
        # Carrier selection
        tk.Label(self.email_frame, text="Mobile Carrier:").pack(anchor='w', padx=5, pady=2)
        self.carrier_var = tk.StringVar(value=self.email_settings['carrier'])  # Set carrier from settings
        carrier_frame = tk.Frame(self.email_frame)
        carrier_frame.pack(fill='x', padx=5, pady=2)
        
        carriers = [("AT&T", "att"), ("Verizon", "verizon"), ("T-Mobile", "tmobile"), ("Sprint", "sprint")]
        for i, (carrier_name, carrier_value) in enumerate(carriers):
            tk.Radiobutton(carrier_frame, text=carrier_name, value=carrier_value, 
                          variable=self.carrier_var).grid(row=0, column=i, padx=5)
        
        # Status message
        self.status_label = tk.Label(self.email_frame, text="Status: Ready to send notifications", fg="green")
        self.status_label.pack(pady=5)
        
        # Help text - simplified since credentials are hardcoded
        help_text = "Credentials are pre-configured. You can test notifications below."
        tk.Label(self.email_frame, text=help_text).pack(pady=5)
        
        tk.Button(self.email_frame, text="Save Settings", command=self.save_notification_settings).pack(pady=5)
        tk.Button(self.email_frame, text="Test Notification", command=self.test_notification).pack(pady=5)

    def toggle_pauses(self):
        if self.include_pauses_var.get():
            self.pauses_frame.pack(fill='x', padx=10, pady=5)
        else:
            self.pauses_frame.pack_forget()
        # Update estimated time after toggling pauses
        self.update_estimated_time()

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
            self.pause_sentence_chance = self.pause_sentence_slider.get() / 100.0  # Convert to probability
            self.pause_paragraph_chance = self.pause_paragraph_slider.get() / 100.0
            self.pause_mid_chance = self.pause_mid_slider.get() / 100.0
            min_pause = self.pause_range_min_slider.get()
            max_pause = self.pause_range_max_slider.get()
            if min_pause > max_pause:
                messagebox.showerror("Input Error", "Minimum pause time cannot be greater than maximum pause time.")
                return
            self.pause_time_range = (min_pause, max_pause)
        else:
            self.pause_sentence_chance = 0
            self.pause_paragraph_chance = 0
            self.pause_mid_chance = 0
            self.pause_time_range = (0, 0)

        # Estimate total time
        self.estimated_total_time = self.calculate_estimated_time(wpm)

        # Show estimated time popup
        self.show_estimated_time_popup()

    def calculate_estimated_time(self, wpm):
        # More accurate word counting - consider actual word lengths
        total_chars = sum(len(segment['text']) for segment in self.formatted_text)
        # Average word length is ~5 characters (standard typing measurement)
        # Including space between words
        total_words = total_chars / 5
        time_per_word = 60 / wpm  # in seconds

        # Calculate total typing time
        total_typing_time = total_words * time_per_word

        # Calculate pauses based on probability
        text = ''.join(segment['text'] for segment in self.formatted_text)
        
        # Count sentence endings and apply probability
        sentence_endings = len(re.findall(r'[.!?][\s\n]', text))
        if re.search(r'[.!?]$', text):  # Add one if text ends with sentence terminator
            sentence_endings += 1
        if sentence_endings == 0:  # Ensure at least one sentence
            sentence_endings = 1
        
        # Count paragraph breaks and apply probability
        paragraphs = text.split('\n\n')
        paragraph_count = len([p for p in paragraphs if p.strip()]) or 1
        
        # Count mid-sentence pause points and apply probability
        mid_sentence_points = len(re.findall(r'[,;:]', text))
        
        # Calculate expected number of pauses based on probabilities
        expected_sentence_pauses = sentence_endings * self.pause_sentence_chance
        expected_paragraph_pauses = paragraph_count * self.pause_paragraph_chance
        expected_mid_pauses = mid_sentence_points * self.pause_mid_chance
        
        # Total expected pauses
        total_expected_pauses = expected_sentence_pauses + expected_paragraph_pauses + expected_mid_pauses
        
        # Average pause time from the range
        avg_pause_time = (self.pause_time_range[0] + self.pause_time_range[1]) / 2
        
        # Total pause time
        total_pause_time = total_expected_pauses * avg_pause_time
        
        return total_typing_time + total_pause_time

    def count_sentences(self):
        # More accurately count sentences by considering common sentence terminators
        text = ''.join(segment['text'] for segment in self.formatted_text)
        # Count sequences that end with period, exclamation mark, or question mark
        # followed by a space or newline
        sentences = re.findall(r'[.!?][\s\n]', text)
        # Add one more if the text ends with a sentence terminator without space after
        if re.search(r'[.!?]$', text):
            return len(sentences) + 1
        return len(sentences) or 1  # Ensure at least 1 sentence

    def count_paragraphs(self):
        # More accurately count paragraphs by looking for double newlines
        text = ''.join(segment['text'] for segment in self.formatted_text)
        paragraphs = text.split('\n\n')
        # Filter out empty paragraphs
        return len([p for p in paragraphs if p.strip()]) or 1  # Ensure at least 1 paragraph

    def count_mid_sentence_pauses(self):
        # More reasonable estimate of mid-sentence pauses
        # Typically these would occur at commas, semicolons, etc.
        text = ''.join(segment['text'] for segment in self.formatted_text)
        # Count potential pause points (commas, semicolons, colons, etc.)
        pause_points = re.findall(r'[,;:]', text)
        return len(pause_points)

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
        # Calculate time per character instead of per word for more accurate typing simulation
        # Standard: 1 word = 5 characters including spaces
        time_per_char = (60 / wpm) / 5
        
        # More accurate total time calculation
        total_chars = sum(len(segment['text']) for segment in self.formatted_text)
        estimated_total_time = self.estimated_total_time
        chars_typed = 0
        
        start_time = time.time()

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
                # Better sentence detection
                sentences = re.split(r'([.!?][\s])', line)
                current_sentence = ""
                
                for sentence_part in sentences:
                    if not sentence_part.strip():
                        continue
                        
                    words = sentence_part.split(' ')
                    for word_index, word in enumerate(words):
                        if self.simulation_stopped:
                            break

                        # Check for mid-sentence punctuation that should trigger pauses
                        for char in word:
                            pyautogui.typewrite(char)
                            chars_typed += 1
                            
                            # Apply pause after punctuation with probability
                            if char in ',;:' and random.random() < self.pause_mid_chance:
                                pause_time = random.uniform(self.pause_time_range[0], self.pause_time_range[1])
                                time.sleep(pause_time)
                                
                            time.sleep(time_per_char)
                            
                            # Update progress more accurately
                            elapsed_time = time.time() - start_time
                            progress = (chars_typed / total_chars) * 100
                            self.progress_var.set(min(progress, 100))
                            
                            # More accurate remaining time calculation
                            if chars_typed > 0:
                                time_per_char_actual = elapsed_time / chars_typed
                                remaining_chars = total_chars - chars_typed
                                remaining_typing_time = remaining_chars * time_per_char_actual
                                
                                # Add remaining pause times
                                remaining_sentences = (self.count_sentences() * (chars_typed / total_chars))
                                remaining_paragraphs = (self.count_paragraphs() * (chars_typed / total_chars))
                                remaining_sentence_pauses = (self.count_sentences() - remaining_sentences) * self.pause_after_sentence
                                remaining_paragraph_pauses = (self.count_paragraphs() - remaining_paragraphs) * self.pause_after_paragraph
                                
                                remaining_time = remaining_typing_time + remaining_sentence_pauses + remaining_paragraph_pauses
                                self.time_remaining_label.config(text=f"Estimated time remaining: {max(0, remaining_time):.2f} seconds")
                            
                            self.root.update_idletasks()

                        if word_index < len(words) - 1:
                            pyautogui.typewrite(' ')
                            chars_typed += 1
                            time.sleep(time_per_char)

                    # Check if this part ends a sentence - apply pause with probability
                    if re.search(r'[.!?]$', sentence_part) and random.random() < self.pause_sentence_chance:
                        pause_time = random.uniform(self.pause_time_range[0], self.pause_time_range[1])
                        time.sleep(pause_time)
                        current_sentence = ""
                    else:
                        current_sentence += sentence_part

                # At end of line, check if this is a paragraph break
                if line_index < len(lines) - 1:
                    pyautogui.press('enter')
                    # Apply paragraph pause with probability
                    if len(lines) > 1 and line_index < len(lines) - 2 and not lines[line_index + 1].strip():
                        if random.random() < self.pause_paragraph_chance:
                            pause_time = random.uniform(self.pause_time_range[0], self.pause_time_range[1])
                            time.sleep(pause_time)
                else:
                    pyautogui.typewrite(' ')

        # Ensure formatting is reset
        if bold_on:
            pyautogui.hotkey('ctrl', 'b')
        if italic_on:
            pyautogui.hotkey('ctrl', 'i')

        completion_time = time.time() - start_time
        self.progress_var.set(100)
        self.time_remaining_label.config(text=f"Estimated time remaining: 0.00 seconds")
        
        if not self.simulation_stopped:
            if self.enable_notification_var.get():
                # Use test_mode=False explicitly to ensure we're sending a completion notification
                notification_sent = self.send_notification(completion_time, test_mode=False)
                if notification_sent:
                    self.status_label.config(text=f"Notification sent successfully! ({time.strftime('%H:%M:%S')})", fg="green")
                else:
                    self.status_label.config(text=f"Failed to send notification. ({time.strftime('%H:%M:%S')})", fg="red")
            messagebox.showinfo("Done", f"Typing simulation completed in {completion_time:.2f} seconds.")

    def send_email_notification(self, completion_time):
        if not self.email_settings['sender_email'] or not self.email_settings['sender_password']:
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_settings['sender_email']
            msg['To'] = self.email_settings['recipient_email']
            msg['Subject'] = 'Typing Simulation Completed'

            body = f'Your typing simulation has completed in {completion_time:.2f} seconds.'
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.email_settings['smtp_server'], self.email_settings['smtp_port'])
            server.starttls()
            server.login(self.email_settings['sender_email'], self.email_settings['sender_password'])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

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
            if matched_text.startswith('***') and matched_text.endsWith('***'):  # Fixed: added missing dot
                content = matched_text[3:-3]
                tokens.append({'text': content, 'bold': True, 'italic': True})
            elif matched_text.startswith('**') and matched_text.endsWith('**'):  # Fixed: added missing dot
                content = matched_text[2:-2]
                tokens.append({'text': content, 'bold': True, 'italic': False})
            elif matched_text.startswith('*') and matched_text.endsWith('*'):  # Fixed: added missing dot
                content = matched_text[1:-1]
                tokens.append({'text': content, 'bold': False, 'italic': True})
            tokens.append({'text': ' ', 'bold': False, 'italic': False})  # Add space after formatting
            pos = end
        # Text after the last match
        if pos < len(text):
            tokens.append({'text': text[pos:], 'bold': False, 'italic': False})
        return tokens

    def save_notification_settings(self):
        self.email_settings['sender_email'] = self.email_entry.get().strip()
        self.email_settings['sender_password'] = self.password_entry.get().strip()
        self.email_settings['recipient_phone'] = self.phone_entry.get().strip()
        self.email_settings['carrier'] = self.carrier_var.get()
        messagebox.showinfo("Settings Saved", "Notification settings have been saved.")

    def test_notification(self):
        try:
            if self.send_notification(0, test_mode=True):
                self.status_label.config(text=f"Test notification sent successfully! ({time.strftime('%H:%M:%S')})", fg="green")
                messagebox.showinfo("Success", "Test notification sent successfully!")
            else:
                self.status_label.config(text=f"Failed to send test notification. ({time.strftime('%H:%M:%S')})", fg="red")
                messagebox.showerror("Error", "Failed to send notification. Check your settings and internet connection.")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)[:50]}...", fg="red")
            messagebox.showerror("Error", f"Failed to send notification: {str(e)}")

    def show_gmail_instructions(self):
        instructions = tk.Toplevel(self.root)
        instructions.title("Gmail App Password Setup Instructions")
        
        text = """How to Create a Gmail App Password:

1. Go to your Google Account settings by visiting: https://myaccount.google.com/

2. Select "Security" from the left navigation panel.

3. Under "Signing in to Google", select "2-Step Verification" and confirm your password.
   - If 2-Step Verification is not enabled, you'll need to enable it first.

4. Scroll down to "App passwords" and select it.

5. Select "Mail" from the app dropdown and "Other (Custom name)" from the device dropdown.

6. Enter "Typing Simulator" as the name and click "Generate".

7. Google will display a 16-character app password. Copy this password.

8. Paste this password into the "Gmail App Password" field in this application.

9. Click "Save Settings".

Important Notes:
- Never share your app password with anyone.
- An app password lets specific apps bypass 2-Step Verification.
- You can revoke access anytime by returning to the App passwords page.
"""
        
        scroll_text = scrolledtext.ScrolledText(instructions, width=70, height=20, wrap=tk.WORD)
        scroll_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        scroll_text.insert(tk.END, text)
        scroll_text.config(state=tk.DISABLED)  # Make it read-only
        
        tk.Button(instructions, text="Close", command=instructions.destroy).pack(pady=10)

    def send_notification(self, completion_time, test_mode=False):
        if not self.email_settings['sender_email'] or not self.email_settings['sender_password']:
            print("Error: Missing email credentials")
            return False

        try:
            # Get carrier domain
            carrier_domain = self.carrier_domains.get(self.email_settings['carrier'], 'txt.att.net')
            
            # Create recipient email from phone number and carrier
            recipient = f"{self.email_settings['recipient_phone']}@{carrier_domain}"
            print(f"Sending notification to: {recipient}")
            
            # Set up the MIME
            msg = MIMEMultipart()
            msg['From'] = self.email_settings['sender_email']
            msg['To'] = recipient
            msg['Subject'] = "Typing Simulator"  # Adding a subject line for better delivery
            
            # Keep the message short for SMS
            if test_mode:
                body = "Test: Typing Simulator"
            else:
                # Format with fewer decimals to keep the message shorter
                body = f"Typing completed in {completion_time:.1f}s"
                
            print(f"Message body: {body}")
            msg.attach(MIMEText(body, 'plain'))
            
            # Set up the SMTP server
            server = smtplib.SMTP(self.email_settings['smtp_server'], self.email_settings['smtp_port'])
            server.starttls()
            server.login(self.email_settings['sender_email'], self.email_settings['sender_password'])
            
            # Send email
            server.send_message(msg)
            server.quit()
            print("Notification sent successfully")
            return True
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
            return False

    # Add a new method for real-time estimated time updates
    def update_estimated_time(self, *args):
        """Update the estimated typing time based on current settings"""
        text_input = self.text_input.get("1.0", tk.END)
        
        if not text_input.strip():
            self.estimated_time_label.config(
                text="Estimated completion time: Enter text first",
                fg="gray"
            )
            return
            
        # Parse the text with formatting
        try:
            self.formatted_text = self.parse_formatted_text(text_input)
        except Exception:
            self.estimated_time_label.config(
                text="Estimated completion time: Error parsing text",
                fg="red"
            )
            return
            
        # Get WPM
        wpm = self.wpm_slider.get()
        if wpm <= 0:
            self.estimated_time_label.config(
                text="Estimated completion time: Set WPM above 0",
                fg="red"
            )
            return
            
        # Get pause settings
        if self.include_pauses_var.get():
            self.pause_sentence_chance = self.pause_sentence_slider.get() / 100.0
            self.pause_paragraph_chance = self.pause_paragraph_slider.get() / 100.0
            self.pause_mid_chance = self.pause_mid_slider.get() / 100.0
            min_pause = self.pause_range_min_slider.get()
            max_pause = self.pause_range_max_slider.get()
            if min_pause > max_pause:
                self.estimated_time_label.config(
                    text="Error: Min pause > Max pause",
                    fg="red"
                )
                return
            self.pause_time_range = (min_pause, max_pause)
        else:
            self.pause_sentence_chance = 0
            self.pause_paragraph_chance = 0
            self.pause_mid_chance = 0
            self.pause_time_range = (0, 0)

        # Calculate estimated time
        try:
            estimated_time = self.calculate_estimated_time(wpm)
            
            # Format time nicely
            if estimated_time < 60:
                time_str = f"{estimated_time:.1f} seconds"
            else:
                minutes = int(estimated_time // 60)
                seconds = estimated_time % 60
                time_str = f"{minutes} min {seconds:.1f} sec"
                
            # Show detail about pause contribution 
            text = ''.join(segment['text'] for segment in self.formatted_text)
            total_chars = sum(len(segment['text']) for segment in self.formatted_text)
            
            # Count expected pauses
            sentence_endings = max(1, len(re.findall(r'[.!?][\s\n]', text)) + (1 if re.search(r'[.!?]$', text) else 0))
            paragraph_count = max(1, len([p for p in text.split('\n\n') if p.strip()]))
            mid_sentence_points = len(re.findall(r'[,;:]', text))
            
            expected_pauses = (
                sentence_endings * self.pause_sentence_chance + 
                paragraph_count * self.pause_paragraph_chance + 
                mid_sentence_points * self.pause_mid_chance
            )
            
            avg_pause_time = (self.pause_time_range[0] + self.pause_time_range[1]) / 2
            
            typing_time = (total_chars / 5) * (60 / wpm)
            total_pause_time = expected_pauses * avg_pause_time
            
            # More detailed information about expected pauses
            pauses_str = f"Expected pauses: ~{expected_pauses:.1f} ({avg_pause_time:.1f}s avg)"
            detailed_str = f"({typing_time:.1f}s typing + {total_pause_time:.1f}s pauses)"
            
            # Update the label with detailed information
            self.estimated_time_label.config(
                text=f"Estimated completion time: {time_str}\n{detailed_str}\n{pauses_str}",
                fg="green"
            )
            
        except Exception as e:
            self.estimated_time_label.config(
                text=f"Error calculating time: {str(e)[:30]}",
                fg="red"
            )

    def on_text_modified(self, event):
        """Handle text modifications to update the time estimation"""
        # Avoid infinite recursion with flag
        if not self.text_modified_flag:
            self.text_modified_flag = True
            self.update_estimated_time()
            self.text_input.edit_modified(False)  # Reset the modified flag
            self.text_modified_flag = False

def main():
    root = tk.Tk()
    app = TypingSimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
