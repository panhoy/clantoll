import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pyautogui
import keyboard
import threading
import time
import json
import hashlib
import webbrowser
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import io
import requests
import re
import os



try:
    import cv2
    import numpy as np
    import pytesseract
except ImportError:
    messagebox.showerror(
        "Missing Dependencies",
        "Some required libraries (OpenCV, NumPy, Pytesseract) are not installed.\n"
        "Please install them using: pip install opencv-python numpy pytesseract"
    )
    exit()


# --- Tesseract Configuration ---
try:
    if os.name == 'nt' and os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    pytesseract.get_tesseract_version()
except Exception:
    messagebox.showerror(
        "Tesseract Not Found",
        "Tesseract-OCR is not found or configured correctly.\n"
        "Please install it and ensure it's in your system's PATH, or modify the script with the correct location."
    )
    exit()

# --- Clash of Clans Color & Style Palette ---
COC_COLORS = {
    'bg_cream': '#FFF8DC',
    'bg_dark_cream': '#F5DEB3',
    'bg_brown': '#654321',
    'text_dark': '#2F1B14',
    'text_light': '#FFFFFF',
    'gold': '#FFD700',
    'orange': '#FF8C00',
    'blue': '#4682B4',
    'green': '#228B22',
    'red': '#DC143C',
    'dark_red': '#B22222',
}

# --- Main Application Class ---
class CoCAutoTool:
    """A class to encapsulate the entire Clash of Clans Auto-Tool application."""

    SESSION_FILE = "session.json"

    def __init__(self, root):
        self.root = root
        self.setup_positions = []
        self.positions = []
        self.clicking = False
        self.visual_overlays = []
        self.dots_visible = False
        self.logo_image = None
        self.ocr_region = None
        self.next_button_pos = None

        # --- License Key & UI State Variables ---
        self.SECRET_SALT = "your_very_secret_key_here_12345" # Change this for security
        self.login_frame = None
        self.create_key_frame = None
        self.main_app_frame = None
        self.generated_key_display_frame = None
        self.generated_key_var = tk.StringVar()
        self.newly_generated_key = ""

        # --- NEW: Variables to track link clicks ---
        self.telegram_clicked = False
        self.youtube_clicked = False
        self.key_generation_triggered = False # Prevents multiple triggers

        # --- Start the application ---
        self.setup_styles()
        self.check_for_session()

    def open_telegram_link(self):
        """Opens the support Telegram link, tracks the click, and checks if a key can be generated."""
        webbrowser.open_new("https://t.me/nhoy200")
        self.telegram_clicked = True
        self.telegram_button.config(state="disabled", text="✅ Telegram Visited")
        self._check_and_trigger_key_generation()

    def open_youtube_link(self):
        """Opens the YouTube link, tracks the click, and checks if a key can be generated."""
        webbrowser.open_new("https://www.youtube.com/@Xai-qq") # Replace with your YouTube channel
        self.youtube_clicked = True
        self.youtube_button.config(state="disabled", text="✅ YouTube Visited")
        self._check_and_trigger_key_generation()

    # --- MODIFIED: This function now triggers the key generation after a delay ---
    def _check_and_trigger_key_generation(self):
        """Checks if both links have been clicked. If so, starts a 3-second timer to generate the key."""
        # Check if both are clicked and that the process hasn't started already
        if self.telegram_clicked and self.youtube_clicked and not self.key_generation_triggered:
            self.key_generation_triggered = True # Mark that the process has started
            
            # Give user feedback immediately
            self.telegram_button.pack_forget()
            self.youtube_button.pack_forget()
            
            # Schedule the key display to appear after 3000ms (3 seconds)
            self.root.after(5000, self._display_generated_key)

    # --- NEW: This function contains the logic to show the key, and is called after the delay ---
    def _display_generated_key(self):
        """Generates the key and displays it in the UI. This is called by the timer."""
        # --- Generate the key automatically ---
        username = "default_user"
        duration_days = 3
        expiration_date = datetime.now() + timedelta(days=duration_days)
        expiration_timestamp = int(expiration_date.timestamp())
        hash_string = f"{username}-{expiration_timestamp}-{self.SECRET_SALT}"
        key_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        final_key = f"{username}-{expiration_timestamp}-{key_hash}"
        self.newly_generated_key = final_key
        self.generated_key_var.set(final_key)

        # --- Show the key and copy button ---
        if self.generated_key_display_frame and not self.generated_key_display_frame.winfo_viewable() and self.create_key_frame:
            last_widget = self.create_key_frame.winfo_children()[-1] # The "Back to Login" frame
            self.generated_key_display_frame.pack(pady=20, padx=10, fill='x', before=last_widget)


    # --- Authentication & UI Flow ---
    def check_for_session(self):
        """Checks for a valid, saved session file on startup."""
        try:
            with open(self.SESSION_FILE, 'r') as f:
                session_data = json.load(f)
            
            entered_key = session_data.get("license_key")
            if not entered_key:
                self.show_login_screen()
                return

            if self.validate_key(entered_key, silent=True):
                self.status_var_for_login = tk.StringVar(value="Logged in from saved session.")
                self.proceed_to_main_app()
            else:
                if os.path.exists(self.SESSION_FILE): os.remove(self.SESSION_FILE)
                self.show_login_screen()

        except (FileNotFoundError, json.JSONDecodeError):
            self.show_login_screen()

    def show_login_screen(self):
        """Displays the initial login screen."""
        self.root.title("Login - Clas of Clan ")

        if self.main_app_frame and self.main_app_frame.winfo_exists():
            self.main_app_frame.destroy()
        
        if self.create_key_frame and self.create_key_frame.winfo_exists():
            self.create_key_frame.pack_forget()

        # Reset flags when returning to login screen
        self.telegram_clicked = False
        self.youtube_clicked = False
        self.key_generation_triggered = False

        self.login_frame = ttk.Frame(self.root, padding="20")
        self.login_frame.place(relx=0.5, rely=0.5, anchor='center', relwidth=1.0, relheight=1.0)
        self.login_frame.lift() 

        if not self.main_app_frame or not self.main_app_frame.winfo_exists():
            self.root.geometry("350x450")

        ttk.Label(self.login_frame, text="License Key", font=('Arial', 14, 'bold'), foreground=COC_COLORS['text_dark']).pack(pady=(10, 10))
        
        key_entry_frame = ttk.Frame(self.login_frame)
        key_entry_frame.pack(pady=10)

        self.key_entry_var = tk.StringVar()
        key_entry = ttk.Entry(key_entry_frame, textvariable=self.key_entry_var, font=('Arial', 11), width=30)
        key_entry.pack(side='left', ipady=4)
        key_entry.focus()
        
        paste_button = ttk.Button(key_entry_frame, text="Paste", command=self.paste_key)
        paste_button.pack(side='left', padx=(5,0), ipady=1)

        ttk.Button(self.login_frame, text="Log In", command=self.handle_login_action, style='Start.TButton').pack(pady=10, fill='x', padx=50)
        ttk.Button(self.login_frame, text="Create Key", command=self.show_key_creation_screen, style='Link.TButton').pack(pady=5, fill='x', padx=50)

    def paste_key(self):
        """Pastes text from the clipboard into the key entry field."""
        try:
            clipboard_content = self.root.clipboard_get()
            self.key_entry_var.set(clipboard_content)
        except tk.TclError:
            messagebox.showwarning("Paste Error", "Could not get content from clipboard.", parent=self.login_frame)

    def show_key_creation_screen(self):
        """Displays the screen for creating a new license key."""
        if self.login_frame and self.login_frame.winfo_exists():
            self.login_frame.place_forget()

        self.create_key_frame = ttk.Frame(self.root, padding="20")
        self.create_key_frame.place(relx=0.5, rely=0.5, anchor='center', relwidth=1.0, relheight=1.0)
        self.create_key_frame.lift()

        ttk.Label(self.create_key_frame, text="Create New Key", font=('Arial', 14, 'bold'), foreground=COC_COLORS['text_dark']).pack(pady=(20, 10))
        ttk.Label(self.create_key_frame, text="Please visit both links to generate your key.", font=('Arial', 10), foreground=COC_COLORS['text_dark']).pack(pady=(0, 15))

        # This frame will be displayed later, automatically
        self.generated_key_display_frame = ttk.LabelFrame(self.create_key_frame, text="✅ Key Generated Successfully")
        key_label = ttk.Label(self.generated_key_display_frame, textvariable=self.generated_key_var, font=('Courier', 10), wraplength=300, justify='center')
        key_label.pack(pady=10, padx=10)
        copy_button = ttk.Button(self.generated_key_display_frame, text="📋 Copy Key", command=self.copy_key_to_clipboard)
        copy_button.pack(pady=(0, 10))
        
        # Add Telegram and YouTube buttons
        self.telegram_button = ttk.Button(self.create_key_frame, text="1. Join Telegram", command=self.open_telegram_link, style='Link.TButton')
        self.telegram_button.pack(pady=5, fill='x', padx=50)
        
        self.youtube_button = ttk.Button(self.create_key_frame, text="2. Subscribe to YouTube", command=self.open_youtube_link, style='Link.TButton')
        self.youtube_button.pack(pady=5, fill='x', padx=50)

        # Action frame with only "Back to Login"
        action_frame = ttk.Frame(self.create_key_frame)
        action_frame.pack(pady=20, side='bottom')
        ttk.Button(action_frame, text="Back to Login", command=self.show_login_screen).pack(side='left', padx=10)

    def copy_key_to_clipboard(self):
        """Copies the newly generated key to the system clipboard."""
        if not self.newly_generated_key:
            return 
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.newly_generated_key)
            messagebox.showinfo("Copied", "The key for 3 days has been copied to your clipboard.", parent=self.create_key_frame)
        except tk.TclError:
            messagebox.showwarning("Copy Error", "Could not access the clipboard.", parent=self.create_key_frame)

    def validate_key(self, key, silent=False):
        """Validates a license key. Returns True if valid, False otherwise."""
        parts = key.strip().split('-')
        
        if len(parts) != 3:
            if not silent: messagebox.showerror("Login Failed", "Invalid key format.", parent=self.login_frame)
            return False

        username, expiration_timestamp_str, provided_hash = parts
        try:
            expiration_timestamp = int(expiration_timestamp_str)
        except ValueError:
            if not silent: messagebox.showerror("Login Failed", "Invalid key data.", parent=self.login_frame)
            return False

        if datetime.now().timestamp() > expiration_timestamp:
            if not silent: messagebox.showerror("Login Failed", "This key has expired.", parent=self.login_frame)
            return False

        expected_hash_string = f"{username}-{expiration_timestamp}-{self.SECRET_SALT}"
        expected_hash = hashlib.sha256(expected_hash_string.encode()).hexdigest()

        if provided_hash == expected_hash:
            return True
        else:
            if not silent: messagebox.showerror("Login Failed", "The provided key is invalid.", parent=self.login_frame)
            return False

    def handle_login_action(self):
        """Validates the entered license key and saves the session."""
        entered_key = self.key_entry_var.get()
        if self.validate_key(entered_key):
            try:
                with open(self.SESSION_FILE, 'w') as f:
                    json.dump({"license_key": entered_key}, f)
            except IOError as e:
                messagebox.showerror("Login Error", f"Could not save session: {e}", parent=self.login_frame)
                return
            
            self.proceed_to_main_app()

    def proceed_to_main_app(self):
        """Clears auth frames and builds or reveals the main application UI."""
        if self.login_frame and self.login_frame.winfo_exists():
            self.login_frame.destroy()
        if self.create_key_frame and self.create_key_frame.winfo_exists():
            self.create_key_frame.destroy()
            
        if not self.main_app_frame or not self.main_app_frame.winfo_exists():
            self.setup_main_ui()
            self.load_from_file(silent=True)

    def handle_logout(self):
        """Logs out, destroys the main UI, deletes the session, and shows the login screen."""
        if messagebox.askyesno("Log Out", "Are you sure you want to log out?"):
            self.stop_clicking()
            self.hide_all_dots()

            try:
                if os.path.exists(self.SESSION_FILE):
                    os.remove(self.SESSION_FILE)
            except OSError as e:
                messagebox.showwarning("Logout Error", f"Could not clear session file: {e}")

            if self.main_app_frame and self.main_app_frame.winfo_exists():
                self.main_app_frame.destroy()

            self._reset_application_state()
            self.show_login_screen()

    def _reset_application_state(self):
        """
        Resets the application's internal data state. 
        IMPORTANT: This function does NOT touch the UI, as it is assumed to be destroyed.
        """
        self.setup_positions = []
        self.positions = []
        self.clicking = False
        self.dots_visible = False
        self.ocr_region = None
        self.next_button_pos = None
        self.main_app_frame = None # Nullify the reference to the destroyed frame
        
    # --- UI Setup ---
    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TNotebook', background=COC_COLORS['bg_cream'], borderwidth=0)
        style.configure('TNotebook.Tab', background=COC_COLORS['bg_dark_cream'], foreground=COC_COLORS['text_dark'], font=('Arial', 10, 'bold'), padding=[10, 5], borderwidth=1)
        style.map('TNotebook.Tab', background=[('selected', COC_COLORS['bg_brown']), ('active', COC_COLORS['orange'])], foreground=[('selected', COC_COLORS['gold']), ('active', COC_COLORS['text_light'])])
        style.configure('TFrame', background=COC_COLORS['bg_cream'])
        style.configure('TLabelframe', background=COC_COLORS['bg_cream'], borderwidth=1, relief="solid")
        style.configure('TLabelframe.Label', background=COC_COLORS['bg_brown'], foreground=COC_COLORS['gold'], font=('Arial', 11, 'bold'), padding=5)
        style.configure('TButton', font=('Arial', 10, 'bold'), padding=5, borderwidth=2, relief='raised')
        style.map('TButton', background=[('active', COC_COLORS['orange']), ('!disabled', COC_COLORS['bg_dark_cream'])], foreground=[('!disabled', COC_COLORS['text_dark'])])
        style.configure('Start.TButton', foreground=COC_COLORS['green'], font=('Arial', 12, 'bold'))
        style.configure('Stop.TButton', foreground=COC_COLORS['red'], font=('Arial', 12, 'bold'))
        style.configure('Danger.TButton', font=('Arial', 10, 'bold'), foreground=COC_COLORS['dark_red'])
        style.map('Danger.TButton', background=[('active', '#ff8282')])
        style.configure('Link.TButton', foreground=COC_COLORS['blue'], font=('Arial', 10, 'bold'))
        style.map('Link.TButton', background=[('active', COC_COLORS['bg_dark_cream'])])
        style.configure("Treeview", background=COC_COLORS['bg_dark_cream'], foreground=COC_COLORS['text_dark'], rowheight=25, fieldbackground=COC_COLORS['bg_dark_cream'], font=('Arial', 10))
        style.map('Treeview', background=[('selected', COC_COLORS['blue'])])
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background=COC_COLORS['bg_brown'], foreground=COC_COLORS['text_light'])

    def setup_main_ui(self):
        self.main_app_frame = tk.Frame(self.root, bg=COC_COLORS['bg_cream'])
        self.main_app_frame.pack(expand=True, fill='both')

        self.root.title("Clas of Clan ")
        self.root.geometry("370x630")
        
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        screen_width = self.root.winfo_screenwidth()
        x_position = screen_width - window_width - 140  
        self.root.geometry(f'+{x_position}+50')

        header = tk.Frame(self.main_app_frame, bg=COC_COLORS['bg_brown'], relief='raised', borderwidth=2)
        header.pack(fill='x')
        header.columnconfigure((0, 2), weight=1)
        header.columnconfigure(1, weight=0)
        content_frame = tk.Frame(header, bg=COC_COLORS['bg_brown'])
        content_frame.grid(row=0, column=1, pady=5, sticky='ew')
        try:
            logo_url = "https://i.pinimg.com/736x/01/06/17/010617204339b7b96e3adb9b80ed4f2b.jpg"
            response = requests.get(logo_url)
            img_data = response.content
            img = Image.open(io.BytesIO(img_data))
            img_resized = img.resize((50, 50), Image.Resampling.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(img_resized)
            logo_label = tk.Label(content_frame, image=self.logo_image, bg=COC_COLORS['bg_brown'])
            logo_label.pack(side='left', padx=(10, 15))
        except Exception as e:
            print(f"Error loading logo: {e}")
            tk.Frame(content_frame, width=65, bg=COC_COLORS['bg_brown']).pack(side='left')
        
        text_frame = tk.Frame(content_frame, bg=COC_COLORS['bg_brown'])
        text_frame.pack(side='left', anchor='center')
        
        title = tk.Label(text_frame, text="Clas of Clan ", font=('Arial', 18, 'bold'), bg=COC_COLORS['bg_brown'], fg=COC_COLORS['gold'])
        title.pack(anchor='w')
        
        notebook = ttk.Notebook(self.main_app_frame, style='TNotebook')
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        self.tab_main = ttk.Frame(notebook, style='TFrame')
        self.tab_attack = ttk.Frame(notebook, style='TFrame')
        self.tab_scanner = ttk.Frame(notebook, style='TFrame')
        self.tab_settings = ttk.Frame(notebook, style='TFrame')
        notebook.add(self.tab_main, text='🔹 Main')
        notebook.add(self.tab_attack, text='🎯 Attack')
        notebook.add(self.tab_scanner, text='🔎 Scanner')
        notebook.add(self.tab_settings, text='⚙️ Settings')
        self.create_main_tab()
        self.create_attack_tab()
        self.create_scanner_tab()
        self.create_settings_tab()

        initial_status = getattr(self, 'status_var_for_login', tk.StringVar(value="Ready. Set up your attack and scanner settings.")).get()
        self.status_var = tk.StringVar(value=initial_status)
        status_bar = tk.Label(self.main_app_frame, textvariable=self.status_var, font=('Arial', 9), bg=COC_COLORS['bg_brown'], fg=COC_COLORS['text_light'], relief='sunken', anchor='w', padx=10)
        status_bar.pack(side='bottom', fill='x')
        
        self.key_listener_thread = threading.Thread(target=self.listen_for_keys, daemon=True)
        self.key_listener_thread.start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_main_tab(self):
        frame = self.tab_main
        ttk.Label(frame, text="Main Controls", font=('Arial', 14, 'bold'), foreground=COC_COLORS['text_dark']).pack(pady=10)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20, fill='x', padx=50)
        self.start_btn = ttk.Button(btn_frame, text="▶ START (S)", style='Start.TButton', command=self.start_clicking)
        self.start_btn.pack(side='left', expand=True, fill='x', padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="■ STOP (D)", style='Stop.TButton', command=self.stop_clicking, state='disabled')
        self.stop_btn.pack(side='left', expand=True, fill='x', padx=5)
        info_frame = ttk.LabelFrame(frame, text="💡 Quick Guide (របៀបប្រើ)")
        info_frame.pack(pady=20, padx=10, fill='both', expand=True)
        guide_text = (
            "1. Go to 'Attack' tab to add Setup and Attack clicks.\n"
            "   (ទៅ Attack tab ដើម្បីបន្ថែមទីតាំងចុចដំបូង និងវាយប្រហារ)\n\n"
            "2. Go to 'Scanner' tab to set the loot scan area.\n"
            "   (ទៅ Scanner tab ដើម្បីកំណត់កន្លែងស្កេន)\n\n"
            "3. Return here and press START or the 'S' key.\n"
            "   (ត្រលប់មកវិញហើយចុច START ឬ 'S')\n\n"
            "4. Press 'D' at any time to stop the process.\n"
            "   (ចុច 'D' ដើម្បីបញ្ឈប់)"
        )
        tk.Label(info_frame, text=guide_text, font=('Arial', 10), wraplength=400, justify='left', bg=COC_COLORS['bg_cream'], fg=COC_COLORS['text_dark']).pack(pady=10, padx=10)

    def create_attack_tab(self):
        frame = self.tab_attack
        frame.pack_propagate(False)
        setup_frame = ttk.LabelFrame(frame, text="Setup Clicks (ចុចដំបូង)")
        setup_frame.pack(fill='x', padx=5, pady=(5,10))
        setup_btn_frame = ttk.Frame(setup_frame)
        setup_btn_frame.pack(fill='x', pady=5)
        ttk.Button(setup_btn_frame, text="➕ Add Setup Click (Q)", command=self.add_setup_position).pack(side='left', padx=5, expand=True)
        ttk.Button(setup_btn_frame, text="Clear Setup", command=self.clear_all_setup_positions, style='Danger.TButton').pack(side='left', padx=5, expand=True)
        setup_tree_frame = ttk.Frame(setup_frame)
        setup_tree_frame.pack(fill='both', expand=True, pady=5, padx=5)
        columns = ('#', 'X', 'Y', 'Delay (s)')
        self.setup_tree = ttk.Treeview(setup_tree_frame, columns=columns, show='headings', height=3)
        for col in columns: self.setup_tree.heading(col, text=col); self.setup_tree.column(col, width=60, anchor='center')
        self.setup_tree.column('#', width=30)
        self.setup_tree.pack(side='left', fill='both', expand=True)
        setup_scrollbar = ttk.Scrollbar(setup_tree_frame, orient='vertical', command=self.setup_tree.yview)
        self.setup_tree.configure(yscrollcommand=setup_scrollbar.set)
        setup_scrollbar.pack(side='right', fill='y')
        attack_frame = ttk.LabelFrame(frame, text="Attack Positions (ទីតាំងវាយប្រហារ)")
        attack_frame.pack(fill='both', expand=True, padx=5, pady=5)
        top_frame = ttk.Frame(attack_frame)
        top_frame.pack(fill='x', pady=5, padx=5)
        ttk.Button(top_frame, text="➕ Add Attack Position (A)", command=self.add_attack_position).pack(side='left', padx=5)
        self.toggle_dots_btn = ttk.Button(top_frame, text="👁️ Show Positions", command=self.toggle_dots)
        self.toggle_dots_btn.pack(side='left', padx=5)
        tree_frame = ttk.Frame(attack_frame)
        tree_frame.pack(fill='both', expand=True, pady=5, padx=5)
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=5)
        for col in columns: self.tree.heading(col, text=col); self.tree.column(col, width=60, anchor='center')
        self.tree.column('#', width=30)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        edit_frame = ttk.Frame(attack_frame)
        edit_frame.pack(pady=5)
        ttk.Button(edit_frame, text="Edit Delay", command=self.edit_delay).pack(side='left', padx=5)
        ttk.Button(edit_frame, text="Delete", command=self.delete_position).pack(side='left', padx=5)
        ttk.Button(edit_frame, text="Clear All", command=self.clear_all_positions, style='Danger.TButton').pack(side='left', padx=5)

    def create_scanner_tab(self):
        frame = self.tab_scanner
        frame.columnconfigure(1, weight=1)
        settings_frame = ttk.LabelFrame(frame, text="Scanner Configuration")
        settings_frame.pack(fill='x', padx=5, pady=10)
        settings_frame.columnconfigure(1, weight=1)
        ttk.Label(settings_frame, text="Min. Loot Required:", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.min_loot_var = tk.StringVar(value="100000")
        ttk.Entry(settings_frame, textvariable=self.min_loot_var, width=15).grid(row=0, column=1, padx=10, pady=10, sticky='w')
        self.scan_before_click_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Enable loot scanning before attack", variable=self.scan_before_click_var).grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
        btn_frame = ttk.LabelFrame(frame, text="Setup Areas")
        btn_frame.pack(fill='x', padx=5, pady=10)
        ttk.Button(btn_frame, text="1. Set Scan Region", command=lambda: self.capture_region_ui("ocr")).pack(fill='x', padx=10, pady=5)
        self.ocr_region_label = tk.Label(btn_frame, text="Scan Region: Not set", font=('Arial', 9), bg=COC_COLORS['bg_cream'])
        self.ocr_region_label.pack(pady=(0, 5))
        ttk.Button(btn_frame, text="2. Set 'Next' Button", command=lambda: self.capture_region_ui("next")).pack(fill='x', padx=10, pady=5)
        self.next_btn_label = tk.Label(btn_frame, text="Next Button: Not set", font=('Arial', 9), bg=COC_COLORS['bg_cream'])
        self.next_btn_label.pack(pady=(0, 10))
        ttk.Button(btn_frame, text="🔬 Test Scanner", command=self.test_scanner).pack(fill='x', padx=10, pady=5)

    def create_settings_tab(self):
        frame = self.tab_settings
        frame.columnconfigure(0, weight=1)
        file_frame = ttk.LabelFrame(frame, text="Configuration")
        file_frame.pack(fill='x', padx=5, pady=10)
        file_frame.columnconfigure(0, weight=1)
        file_frame.columnconfigure(1, weight=1)
        ttk.Button(file_frame, text="💾 Save Settings", command=self.save_to_file).grid(row=0, column=0, padx=5, pady=10, sticky='ew')
        ttk.Button(file_frame, text="📁 Load Settings", command=lambda: self.load_from_file(silent=False)).grid(row=0, column=1, padx=5, pady=10, sticky='ew')
        auth_frame = ttk.LabelFrame(frame, text="Authentication")
        auth_frame.pack(fill='x', padx=5, pady=10, anchor='n')
        ttk.Button(auth_frame, text="Log Out", command=self.handle_logout, style='Danger.TButton').pack(fill='x', padx=10, pady=10)
        support_frame = ttk.LabelFrame(frame, text="Support & About")
        support_frame.pack(fill='x', padx=5, pady=10, anchor='n')
        ttk.Button(support_frame, text="📨 Contact Support on Telegram", command=self.open_telegram_link, style='Link.TButton').pack(fill='x', padx=10, pady=10)

    # --- Core Logic ---
    def capture_region_ui(self, mode):
        self.root.withdraw()
        time.sleep(0.2)
        capture_win = tk.Toplevel()
        capture_win.attributes("-fullscreen", True, "-alpha", 0.3)
        capture_win.configure(bg="black")
        capture_win.overrideredirect(True)
        canvas = tk.Canvas(capture_win, cursor="cross", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        if mode == "ocr":
            rect = None
            start_x, start_y = 0, 0
            def on_press(event):
                nonlocal start_x, start_y, rect
                start_x, start_y = event.x, event.y
                rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='red', width=2)
            def on_drag(event):
                if rect is not None: canvas.coords(rect, start_x, start_y, event.x, event.y)
            def on_release(event):
                x1, y1 = min(start_x, event.x), min(start_y, event.y)
                x2, y2 = max(start_x, event.x), max(start_y, event.y)
                self.ocr_region = {'x': x1, 'y': y1, 'width': x2 - x1, 'height': y2 - y1}
                self.update_scanner_labels()
                capture_win.destroy()
                self.root.deiconify()
            canvas.bind("<ButtonPress-1>", on_press)
            canvas.bind("<B1-Motion>", on_drag)
            canvas.bind("<ButtonRelease-1>", on_release)
        elif mode == "next":
            def on_click(event):
                self.next_button_pos = {'x': event.x, 'y': event.y}
                self.update_scanner_labels()
                capture_win.destroy()
                self.root.deiconify()
                threading.Thread(target=self.flash_dot, args=(event.x, event.y, 1.5, 'green'), daemon=True).start()
            canvas.bind("<ButtonRelease-1>", on_click)

    def test_scanner(self):
        if not self.ocr_region:
            messagebox.showwarning("Scanner Not Ready", "Please set the scanner region first before testing.", parent=self.root)
            return
        self.status_var.set("Running scanner test...")
        self.root.update_idletasks()
        loot_amount = self.perform_ocr()
        self.status_var.set("Scanner test complete.")
        messagebox.showinfo("Scanner Test Result", f"Detected Loot: {loot_amount:,}", parent=self.root)

    def perform_ocr(self):
        if not self.ocr_region: return 0
        try:
            screenshot = pyautogui.screenshot(region=(self.ocr_region['x'], self.ocr_region['y'], self.ocr_region['width'], self.ocr_region['height']))
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            config = '--psm 7 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(thresh, config=config)
            numbers = re.findall(r'\d+', text)
            return int("".join(numbers)) if numbers else 0
        except Exception as e:
            print(f"Error during OCR: {e}")
            if hasattr(self, 'status_var'): self.status_var.set(f"OCR Error: {e}")
            return 0
    
    def execute_start_sequence(self):
        """Runs setup clicks and then starts the main click_loop."""
        try:
            if self.setup_positions:
                self.status_var.set("▶️ Executing setup clicks...")
                for i, pos in enumerate(self.setup_positions):
                    if not self.clicking: return 
                    self.status_var.set(f"▶️ Setup click {i+1}/{len(self.setup_positions)}...")
                    pyautogui.click(pos["x"], pos["y"])
                    time.sleep(pos.get("delay", 1.5))
            
            if self.clicking:
                self.status_var.set("🟢 Starting main search loop...")
                self.click_loop()
        except Exception as e:
            print(f"Error during start sequence: {e}")
            self.stop_clicking()

    def click_loop(self):
        try:
            min_loot = int(self.min_loot_var.get())
        except ValueError:
            self.status_var.set("❌ Invalid loot amount! Must be a number.")
            self.stop_clicking()
            return

        while self.clicking:
            if self.scan_before_click_var.get():
                found_target = False
                search_count = 0
                while self.clicking and not found_target:
                    search_count += 1
                    self.status_var.set(f"🔎 Searching... (Attempt #{search_count})")
                    loot_amount = self.perform_ocr()
                    if loot_amount >= min_loot:
                        found_target = True
                        self.status_var.set(f"🎯 Target found! Loot: {loot_amount:,}")
                        time.sleep(1)
                    else:
                        if not self.clicking: break
                        self.status_var.set(f"✖️ Loot low ({loot_amount:,}). Clicking next...")
                        if self.next_button_pos:
                            pyautogui.click(self.next_button_pos['x'], self.next_button_pos['y'])
                        time.sleep(2.5)
            
            if not self.clicking: break
            self.status_var.set("⚔️ Attacking target!")
            for i, pos in enumerate(self.positions):
                if not self.clicking: break
                pyautogui.click(pos["x"], pos["y"])
                self.status_var.set(f"⚔️ Deploying troop {i+1}/{len(self.positions)}")
                time.sleep(pos.get("delay", 0.5))
            if self.clicking:
                self.status_var.set("✅ Attack finished. Pausing...")
                time.sleep(10)
        self.stop_clicking()

    def start_clicking(self):
        if not self.clicking:
            if self.scan_before_click_var.get() and not self.ocr_region:
                self.status_var.set("❌ Set scanner region before starting!"); return
            if self.scan_before_click_var.get() and not self.next_button_pos:
                self.status_var.set("❌ Set 'Next' button position before starting!"); return
            if not self.positions:
                self.status_var.set("❌ Add at least one attack position!"); return

            self.clicking = True
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            threading.Thread(target=self.execute_start_sequence, daemon=True).start()

    def stop_clicking(self):
        if self.clicking:
            self.clicking = False
            if hasattr(self, 'status_var') and self.status_var:
                try:
                    self.status_var.set("🛑 Stopped by user.")
                except tk.TclError:
                    pass # Occurs if the widget is already destroyed, safe to ignore.
            if hasattr(self, 'start_btn') and self.start_btn.winfo_exists():
                self.start_btn.config(state="normal")
            if hasattr(self, 'stop_btn') and self.stop_btn.winfo_exists():
                self.stop_btn.config(state="disabled")

    def add_setup_position(self):
        x, y = pyautogui.position()
        self.setup_positions.append({"x": x, "y": y, "delay": 1.5})
        self.update_setup_position_display()
        threading.Thread(target=self.flash_dot, args=(x, y, 0.8, COC_COLORS['gold']), daemon=True).start()
        self.status_var.set(f"Added setup position ({x}, {y})")

    def add_attack_position(self):
        x, y = pyautogui.position()
        self.positions.append({"x": x, "y": y, "delay": 1.0})
        self.update_attack_position_display()
        threading.Thread(target=self.flash_dot, args=(x, y, 0.8, COC_COLORS['blue']), daemon=True).start()
        self.status_var.set(f"Added attack position ({x}, {y})")

    def listen_for_keys(self):
        try:
            keyboard.add_hotkey('s', self.start_clicking)
            keyboard.add_hotkey('d', self.stop_clicking)
            keyboard.add_hotkey('q', self.add_setup_position)
            keyboard.add_hotkey('a', self.add_attack_position)
            keyboard.wait()
        except Exception as e:
            print(f"Could not set up hotkeys (might need admin rights): {e}")

    def update_setup_position_display(self):
        if not hasattr(self, 'setup_tree') or not self.setup_tree.winfo_exists(): return
        for item in self.setup_tree.get_children(): self.setup_tree.delete(item)
        for i, pos in enumerate(self.setup_positions):
            self.setup_tree.insert("", "end", values=(i + 1, pos['x'], pos['y'], pos.get('delay', 1.5)))

    def update_attack_position_display(self):
        if not hasattr(self, 'tree') or not self.tree.winfo_exists(): return
        for item in self.tree.get_children(): self.tree.delete(item)
        for i, pos in enumerate(self.positions):
            self.tree.insert("", "end", values=(i + 1, pos['x'], pos['y'], pos.get('delay', 1.0)))

    def update_scanner_labels(self):
        if hasattr(self, 'ocr_region_label') and self.ocr_region_label.winfo_exists():
            if self.ocr_region:
                r = self.ocr_region
                self.ocr_region_label.config(text=f"Scan Region: ({r['x']}, {r['y']}) - {r['width']}x{r['height']}")
            else:
                self.ocr_region_label.config(text="Scan Region: Not set")
        if hasattr(self, 'next_btn_label') and self.next_btn_label.winfo_exists():
            if self.next_button_pos:
                n = self.next_button_pos
                self.next_btn_label.config(text=f"Next Button: ({n['x']}, {n['y']})")
            else:
                self.next_btn_label.config(text="Next Button: Not set")
    
    def flash_dot(self, x, y, duration=1.0, color='red'):
        try:
            dot = tk.Toplevel()
            dot.overrideredirect(True)
            dot.attributes("-topmost", True, "-alpha", 0.8)
            dot.geometry(f"16x16+{x-8}+{y-8}")
            canvas = tk.Canvas(dot, width=16, height=16, bg='black', highlightthickness=0)
            canvas.pack()
            canvas.create_oval(2, 2, 14, 14, fill=color)
            dot.after(int(duration * 1000), dot.destroy)
        except tk.TclError:
            pass # Main window might be closing

    def show_all_dots(self):
        self.hide_all_dots()
        try:
            for pos in self.setup_positions:
                dot = tk.Toplevel()
                dot.overrideredirect(True); dot.attributes("-topmost", True, "-alpha", 0.7); dot.geometry(f"12x12+{pos['x']-6}+{pos['y']-6}")
                canvas = tk.Canvas(dot, width=12, height=12, highlightthickness=0); canvas.pack()
                canvas.create_oval(1, 1, 11, 11, fill=COC_COLORS['gold']); self.visual_overlays.append(dot)
            for pos in self.positions:
                dot = tk.Toplevel()
                dot.overrideredirect(True); dot.attributes("-topmost", True, "-alpha", 0.7); dot.geometry(f"12x12+{pos['x']-6}+{pos['y']-6}")
                canvas = tk.Canvas(dot, width=12, height=12, highlightthickness=0); canvas.pack()
                canvas.create_oval(1, 1, 11, 11, fill=COC_COLORS['blue']); self.visual_overlays.append(dot)
            if self.ocr_region:
                r = self.ocr_region
                win = tk.Toplevel(self.root)
                win.overrideredirect(True); win.attributes("-topmost", True, "-transparentcolor", "white"); win.geometry(f"{r['width']}x{r['height']}+{r['x']}+{r['y']}")
                canvas = tk.Canvas(win, bg="white", highlightthickness=0); canvas.pack(fill='both', expand=True)
                canvas.create_rectangle(0, 0, r['width']-1, r['height']-1, outline='red', width=3); self.visual_overlays.append(win)
        except tk.TclError:
            self.visual_overlays = [] # Clear list if main window is gone

    def hide_all_dots(self):
        for item in self.visual_overlays:
            if item.winfo_exists(): item.destroy()
        self.visual_overlays = []

    def toggle_dots(self):
        self.dots_visible = not self.dots_visible
        if self.dots_visible:
            self.show_all_dots(); self.toggle_dots_btn.config(text="🙈 Hide Positions")
        else:
            self.hide_all_dots(); self.toggle_dots_btn.config(text="👁️ Show Positions")

    def edit_delay(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an attack position to edit."); return
        item = selection[0]
        index = int(self.tree.item(item, "values")[0]) - 1
        new_delay_str = simpledialog.askstring("Edit Delay", "Enter new delay (seconds):", initialvalue=str(self.positions[index]["delay"]), parent=self.root)
        if new_delay_str:
            try:
                new_delay = float(new_delay_str)
                if new_delay < 0: raise ValueError
                self.positions[index]["delay"] = new_delay
                self.update_attack_position_display()
            except ValueError: messagebox.showerror("Invalid Input", "Please enter a valid positive number.")

    def delete_position(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Select an attack position to delete."); return
        index = int(self.tree.item(selection[0], "values")[0]) - 1
        self.positions.pop(index)
        self.update_attack_position_display()
        if self.dots_visible: self.show_all_dots()

    def clear_all_setup_positions(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all setup positions?"):
            self.setup_positions.clear()
            self.update_setup_position_display()
            if self.dots_visible: self.show_all_dots()

    def clear_all_positions(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all attack positions?"):
            self.positions.clear()
            self.update_attack_position_display()
            if self.dots_visible: self.show_all_dots()

    def save_to_file(self):
        data_to_save = {
            "setup_positions": self.setup_positions, "positions": self.positions, "ocr_region": self.ocr_region,
            "next_button_pos": self.next_button_pos, "min_loot": self.min_loot_var.get(), "scan_enabled": self.scan_before_click_var.get(),
        }
        try:
            with open("coc_config.json", "w") as f: json.dump(data_to_save, f, indent=4)
            self.status_var.set("💾 Configuration saved successfully.")
        except Exception as e: messagebox.showerror("Save Error", f"Failed to save settings: {e}")

    def load_from_file(self, silent=False):
        try:
            with open("coc_config.json", "r") as f: data = json.load(f)
            self.setup_positions = data.get("setup_positions", [])
            self.positions = data.get("positions", [])
            self.ocr_region = data.get("ocr_region")
            self.next_button_pos = data.get("next_button_pos")
            self.min_loot_var.set(data.get("min_loot", "100000"))
            self.scan_before_click_var.set(data.get("scan_enabled", True))
            self.update_setup_position_display()
            self.update_attack_position_display()
            self.update_scanner_labels()
            if not silent: self.status_var.set("📁 Configuration loaded.")
        except FileNotFoundError:
            if not silent: self.status_var.set("No configuration file found.")
        except Exception as e:
            if not silent: messagebox.showerror("Load Error", f"Failed to load settings: {e}")

    def on_closing(self):
        self.stop_clicking()
        self.hide_all_dots()
        keyboard.unhook_all()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CoCAutoTool(root)
    root.mainloop()