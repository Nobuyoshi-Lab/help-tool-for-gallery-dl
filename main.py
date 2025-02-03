import os
import re
import json
import subprocess
import threading
import customtkinter as ctk
import tkinter as tk  # For certain icon handling
from pathlib import Path
from tkinter import messagebox, filedialog

# Attempt to fix icon behavior in Windows taskbar
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.gallerydl.helper")
except:
    pass

# If Pillow is available, it can be used for more reliable icon loading
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class GalleryDownloadHelper(ctk.CTk):
    """
    Gallery Download Helper: 
    A CustomTkinter-based GUI for gallery-dl, side-by-side URL and Terminal sections,
    with special handling for URL formatting and simpler status indication.
    """

    def __init__(self):
        super().__init__()

        # ---------------------------
        # Window / Appearance Setup
        # ---------------------------
        self.title("Gallery Download Helper")
        # Fixed window size large enough for side-by-side panels
        self.geometry("900x640")
        self.resizable(False, False)

        # Use dark mode with a dark-blue theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # Attempt to load an .ico for the taskbar/title bar icon
        icon_path = Path(__file__).parent / "images" / "app_icon.ico"
        if icon_path.is_file():
            if PIL_AVAILABLE:
                # Use Pillow for better reliability in setting the icon
                image = Image.open(icon_path)
                icon_img = ImageTk.PhotoImage(image)
                self.iconphoto(True, icon_img)
            else:
                # Fallback (sometimes doesn't show in taskbar)
                self.iconbitmap(icon_path)

        # ---------------------------
        # Internal State
        # ---------------------------
        self.stop_flag = False
        self.cmd_thread = None
        self.process_obj = None
        self.timeout_seconds = 3

        # Colors for label background
        self.color_idle = "#6c757d"       # Gray
        self.color_running = "#ffc107"    # Yellow
        self.color_finished = "#28a745"   # Green

        # Text colors for each state (for improved readability)
        self.text_color_idle = "white"
        self.text_color_running = "black"
        self.text_color_finished = "white"

        # File references
        self.urls_file = Path(__file__).parent / "urls.txt"
        self.config_file_path = self._detect_config_file()

        # Download folder (read from config if found)
        self.download_folder_var = ctk.StringVar()
        self._init_download_folder()

        # ---------------------------
        # Create & Place Widgets
        # ---------------------------
        self._create_widgets()
        self._place_widgets()

        # Load any existing URLs
        self._load_urls_on_start()

    # =========================================================================
    #  Detect gallery-dl config, read the base-directory
    # =========================================================================
    def _detect_config_file(self):
        possible_paths = [
            Path(os.environ.get('APPDATA', ''), 'gallery-dl', 'config.json'),
            Path(os.environ.get('USERPROFILE', ''), 'gallery-dl', 'config.json'),
            Path(os.environ.get('USERPROFILE', ''), 'gallery-dl.conf'),
            Path(__file__).parent / "gallery-dl.conf"
        ]
        for p in possible_paths:
            if p.is_file():
                return str(p)
        return ""

    def _init_download_folder(self):
        """If config found, retrieve base-directory; else blank."""
        if self.config_file_path:
            try:
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                base_dir = cfg_data.get("extractor", {}).get("base-directory", "")
                self.download_folder_var.set(base_dir)
            except (json.JSONDecodeError, OSError, KeyError):
                self.download_folder_var.set("")
        else:
            self.download_folder_var.set("")

    # =========================================================================
    #  Create Widgets
    # =========================================================================
    def _create_widgets(self):
        bold_font = ("Segoe UI", 12, "bold")

        # ~~~~ Top Frame (Theme + Config) ~~~~
        self.top_frame = ctk.CTkFrame(self)

        self.theme_label = ctk.CTkLabel(self.top_frame, text="Theme:", font=bold_font)
        self.btn_theme_system = ctk.CTkButton(
            self.top_frame, text="System", width=60,
            command=lambda: self._change_theme("System"),
            font=bold_font
        )
        self.btn_theme_light = ctk.CTkButton(
            self.top_frame, text="Light", width=60,
            command=lambda: self._change_theme("Light"),
            font=bold_font
        )
        self.btn_theme_dark = ctk.CTkButton(
            self.top_frame, text="Dark", width=60,
            command=lambda: self._change_theme("Dark"),
            font=bold_font
        )

        if self.config_file_path:
            cfg_text = f"Config Found: {self.config_file_path}"
            cfg_color = "green"
        else:
            cfg_text = "No gallery-dl config found"
            cfg_color = "red"
        self.config_label = ctk.CTkLabel(
            self.top_frame, text=cfg_text, text_color=cfg_color,
            font=bold_font
        )

        # ~~~~ Download Folder Frame ~~~~
        self.path_frame = ctk.CTkFrame(self)
        self.download_folder_label = ctk.CTkLabel(
            self.path_frame, text="Download Folder:", font=bold_font
        )
        self.download_folder_entry = ctk.CTkEntry(
            self.path_frame, textvariable=self.download_folder_var,
            width=400, font=bold_font
        )
        self.browse_button = ctk.CTkButton(
            self.path_frame, text="Browse", width=80,
            command=self._browse_folder, font=bold_font
        )

        # ~~~~ Main Frame (two panels: left = URLs, right = Terminal) ~~~~
        self.main_frame = ctk.CTkFrame(self)
        self.left_panel = ctk.CTkFrame(self.main_frame)
        self.right_panel = ctk.CTkFrame(self.main_frame)

        # Panel titles
        self.url_title_label = ctk.CTkLabel(
            self.left_panel,
            text="URLs",
            font=bold_font
        )
        self.terminal_title_label = ctk.CTkLabel(
            self.right_panel,
            text="Terminal Output",
            font=bold_font
        )

        # URL text box
        self.url_text = ctk.CTkTextbox(
            self.left_panel, width=400, height=380,
            activate_scrollbars=True, font=bold_font
        )

        # Terminal text box
        self.terminal_box = ctk.CTkTextbox(
            self.right_panel, width=400, height=380,
            activate_scrollbars=True, font=bold_font
        )
        self.terminal_box.configure(state="disabled")

        # ~~~~ Bottom Frame (Buttons + Status) ~~~~
        self.bottom_frame = ctk.CTkFrame(self)

        # Buttons container (centered)
        self.buttons_container = ctk.CTkFrame(self.bottom_frame)
        self.btn_get_image = ctk.CTkButton(
            self.buttons_container, text="Get Image",
            command=self._handle_execute, font=bold_font
        )
        self.btn_save = ctk.CTkButton(
            self.buttons_container, text="Save URLs",
            command=self._save_urls, font=bold_font
        )
        self.btn_clear = ctk.CTkButton(
            self.buttons_container, text="Clear URLs",
            command=self._clear_urls, font=bold_font
        )
        self.btn_restore = ctk.CTkButton(
            self.buttons_container, text="Restore URLs",
            command=self._restore_urls, font=bold_font
        )
        self.btn_stop = ctk.CTkButton(
            self.buttons_container, text="Stop Process",
            command=self._stop_command, font=bold_font
        )

        self.status_label_var = ctk.StringVar(value="Status: Idle")
        self.status_label = ctk.CTkLabel(
            self.bottom_frame,
            textvariable=self.status_label_var,
            fg_color=self.color_idle,
            corner_radius=6,
            font=bold_font,
            width=700,  # Make it a bit wider to appear like a 'bar'
            text_color=self.text_color_idle
        )

    # =========================================================================
    #  Place Widgets
    # =========================================================================
    def _place_widgets(self):
        # ~~~~ Top Frame ~~~~
        self.top_frame.pack(pady=10, fill="x")
        self.theme_label.pack(side="left", padx=5)
        self.btn_theme_system.pack(side="left", padx=5)
        self.btn_theme_light.pack(side="left", padx=5)
        self.btn_theme_dark.pack(side="left", padx=5)
        self.config_label.pack(side="right", padx=20)

        # ~~~~ Download Folder Frame ~~~~
        self.path_frame.pack(pady=5, fill="x")
        self.download_folder_label.pack(side="left", padx=5)
        self.download_folder_entry.pack(side="left", padx=5)
        self.browse_button.pack(side="left", padx=5)

        # ~~~~ Main Frame ~~~~
        self.main_frame.pack(fill="both", expand=True, pady=5)
        self.left_panel.pack(side="left", fill="both", expand=True, padx=(10, 5))
        self.right_panel.pack(side="left", fill="both", expand=True, padx=(5, 10))

        # Left panel: URLs
        self.url_title_label.pack(pady=(5, 0))
        self.url_text.pack(expand=True, fill="both", pady=5)

        # Right panel: Terminal
        self.terminal_title_label.pack(pady=(5, 0))
        self.terminal_box.pack(expand=True, fill="both", pady=5)

        # ~~~~ Bottom Frame ~~~~
        self.bottom_frame.pack(fill="x", pady=10)

        # Buttons container, centered
        self.buttons_container.pack(anchor="center", pady=(0, 10))
        self.btn_get_image.pack(side="left", padx=5)
        self.btn_save.pack(side="left", padx=5)
        self.btn_clear.pack(side="left", padx=5)
        self.btn_restore.pack(side="left", padx=5)
        self.btn_stop.pack(side="left", padx=5)

        # Status label (appears as a wide bar)
        self.status_label.pack(pady=5)

    # =========================================================================
    #  Theme Handling
    # =========================================================================
    def _change_theme(self, mode):
        ctk.set_appearance_mode(mode)

    # =========================================================================
    #  Browse & Update Download Folder
    # =========================================================================
    def _browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.download_folder_var.set(folder_selected)
            # Write to config if present
            if self.config_file_path:
                try:
                    with open(self.config_file_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    if "extractor" not in cfg_data:
                        cfg_data["extractor"] = {}
                    cfg_data["extractor"]["base-directory"] = folder_selected
                    with open(self.config_file_path, "w", encoding="utf-8") as f:
                        json.dump(cfg_data, f, indent=4)
                except (json.JSONDecodeError, OSError):
                    pass

    # =========================================================================
    #  URL File Handling
    # =========================================================================
    def _load_urls_on_start(self):
        """Load the contents of urls.txt into the text box on startup."""
        if self.urls_file.exists():
            self._restore_urls()

    def _restore_urls(self):
        self.url_text.delete("1.0", "end")
        try:
            with open(self.urls_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.url_text.insert("1.0", content)
        except OSError:
            pass

    def _save_urls(self):
        """
        Clean up and validate each URL, then save them line-by-line.
        No extra newline at the end.
        """
        raw_text = self.url_text.get("1.0", "end")
        cleaned = self._clean_urls(raw_text)

        # Update text widget with cleaned content
        self.url_text.delete("1.0", "end")
        self.url_text.insert("1.0", cleaned)

        # Write cleaned to file
        try:
            with open(self.urls_file, "w", encoding="utf-8") as f:
                f.write(cleaned)
            self._update_status_label("Status: URLs Saved", self.color_idle, self.text_color_idle)
        except OSError:
            self._update_status_label("Status: Save Failed", self.color_idle, self.text_color_idle)

    def _clear_urls(self):
        self.url_text.delete("1.0", "end")

    def _clean_urls(self, raw_text):
        """
        Split the text by whitespace, pick out valid URLs, and return
        each URL on its own line (no trailing newline).
        """
        tokens = raw_text.split()
        valid_tokens = [t for t in tokens if self._is_valid_url(t)]
        # Join them line-by-line
        return "\n".join(valid_tokens)

    @staticmethod
    def _is_valid_url(s):
        """
        Simple URL check: must start with http:// or https://, no spaces inside.
        (You can enhance this regex if needed.)
        """
        pattern = re.compile(r'^https?://\S+$', re.IGNORECASE)
        return bool(pattern.match(s))

    # =========================================================================
    #  Subprocess Execution
    # =========================================================================
    def _handle_execute(self):
        """
        Save and validate URLs, clear terminal, then run gallery-dl in a thread.
        """
        self._save_urls()
        self._clear_terminal()

        if self.cmd_thread and self.cmd_thread.is_alive():
            messagebox.showwarning("Running", "A process is already running.")
            return

        self._update_status_label("Status: Running...", self.color_running, self.text_color_running)
        self.stop_flag = False

        self.cmd_thread = threading.Thread(target=self._run_subprocess)
        self.cmd_thread.start()

    def _run_subprocess(self):
        cmd = ['cmd', '/k', 'gallery-dl', '-i', str(self.urls_file)]
        try:
            self.process_obj = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                universal_newlines=True, bufsize=1, shell=True
            )
        except OSError as e:
            self._append_to_terminal(f"Error running command: {e}\n")
            self._finish_subprocess("Process Failed.")
            return

        for line in self.process_obj.stdout:
            if self.stop_flag:
                self.process_obj.terminate()
                break
            self._append_to_terminal(line)
            self._parse_progress(line)

        try:
            self.process_obj.wait(timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired:
            self.process_obj.kill()

        self._finish_subprocess("Process Finished.")

    def _finish_subprocess(self, msg):
        self.stop_flag = False
        self.process_obj = None
        self._append_to_terminal(msg + "\n")

        if "Failed" in msg:
            # Something went wrong
            self._update_status_label("Status: Idle", self.color_idle, self.text_color_idle)
        else:
            self._update_status_label("Status: Done", self.color_finished, self.text_color_finished)

    def _stop_command(self):
        if self.process_obj:
            self.stop_flag = True

    def _parse_progress(self, line):
        if "Downloading" in line:
            self._update_status_label("Status: Downloading...", self.color_running, self.text_color_running)
        elif "Finished" in line or "Deleting" in line:
            self._update_status_label("Status: Processing...", self.color_running, self.text_color_running)

    # =========================================================================
    #  Terminal Box
    # =========================================================================
    def _clear_terminal(self):
        self.terminal_box.configure(state="normal")
        self.terminal_box.delete("1.0", "end")
        self.terminal_box.configure(state="disabled")

    def _append_to_terminal(self, text):
        def insert_line():
            self.terminal_box.configure(state="normal")
            self.terminal_box.insert("end", text)
            self.terminal_box.configure(state="disabled")
            self.terminal_box.see("end")
        self.terminal_box.after(0, insert_line)

    # =========================================================================
    #  Status Label Helper
    # =========================================================================
    def _update_status_label(self, text, bg_color, text_color):
        self.status_label_var.set(text)
        self.status_label.configure(fg_color=bg_color, text_color=text_color)


if __name__ == "__main__":
    app = GalleryDownloadHelper()
    app.mainloop()

'''
* prerequisites:
*   > pip install pyinstaller
*       + for pyinstaller
*   > python -m pip install --upgrade pywin32
*       + give the program os permissions
*
* packaging:
*   > pyinstaller main.py --onedir --windowed --name="gallery-dl-gui" --icon=images\app_icon.ico
'''
