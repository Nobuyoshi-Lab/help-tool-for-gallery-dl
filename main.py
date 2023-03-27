import os
import json
import subprocess
import tkinter as tk

from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox


# Update the background color of the label
def update_label_bg(label, bg_color):
    label.config(bg=bg_color)


# Insert the command line output into the terminal window
def insert_cmd_line_output(line, terminal, color='white'):
    def update_terminal():
        terminal.configure(state="normal")
        terminal.insert(tk.END, line, color)
        terminal.configure(state="disabled")
        terminal.see(tk.END)

    terminal.after(0, update_terminal)


# Define color map for stages
color_map = {
    'running': 'yellow',
    'finished': 'green',
}

stop_process = False
process = None

# Execute command in a separate thread and update the stage color
def execute_command(cmd, terminal):
    global stop_process
    global process

    p = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
        shell=True
    )
    p.poll()

    update_label_bg(stage_color_label, color_map['running'])

    while True:
        line = p.stdout.readline()
        insert_cmd_line_output(line, terminal)
        if not line.strip() and p.poll() is not None:
            break
        if stop_process:
            p.terminate()
            break

    try:
        p.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        p.kill()

    update_label_bg(stage_color_label, color_map['finished'])
    window.title(window_title + " - " + "Done")
    stop_process = False


def on_close():
    global process, stop_process
    if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
        if process and process.is_alive():
            stop_process = True
            process.join()  # Wait for the thread to finish
        window.destroy()


# Create a file if it doesn't exist and return the file path
def create_file_if_not_exists(path):
    filepath = Path(path)
    filepath.touch(exist_ok=True)
    return filepath


# Open a file and load its content into the text window
def open_file(path):
    filepath = create_file_if_not_exists(path)
    with open(filepath, mode="r", encoding="utf-8") as input_file:
        text = input_file.read()
        text_window.insert(tk.END, text)


# Save the content of the text window to the specified file
def save_file(path):
    filepath = create_file_if_not_exists(path)
    with open(filepath, mode="w", encoding="utf-8") as output_file:
        text = text_window.get("1.0", tk.END)
        output_file.write(text)
    window.title(window_title + " - " + "File Saved")


# Execute the main command and update the UI accordingly
def execute_main_command(path):
    clear_terminal_output()
    save_file(path)
    window.title(window_title + " - " + "Running")
    cmd = ['cmd', '/k', 'gallery-dl', '-i', path]
    process = Thread(target=lambda: execute_command(cmd, terminal_output_window))
    process.start()


# Clear the terminal output window
def clear_terminal_output():
    terminal_output_window.configure(state="normal")
    terminal_output_window.delete("1.0", "end")


# Clear the text window
def clear_text():
    text_window.delete("1.0", "end")


def stop_command():
    global stop_process
    stop_process = True

    
# Default parameters
nord_bg = "#2E3440"
nord_tc = "#D8DFE4"
absolute_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(absolute_path, 'urls.txt')
window_title = "Help Tool for Gallery-DL"
timeout_seconds = 3
font_setting = ("Consolas", 12)
window_size = "1000x1000"

# Create application window
window = tk.Tk()
window.title(window_title)
window.geometry(window_size)
window.resizable(False, False)

# Configure window grids
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=3)
window.columnconfigure(0, weight=1)

# Create text window and terminal output window
text_window = tk.Text(
    window,
    bg="antique white",
    fg="black",
    font=font_setting
)

terminal_output_window = tk.Text(
    window,
    bg=nord_bg,
    fg=nord_tc,
    font=font_setting
)

# Open existing file with URLs, else create one
open_file(file_path)

# Buttons initialization
buttons_frame = tk.Frame(window, relief=tk.RAISED, bd=5)

# Buttons configuration
execute_button = tk.Button(
    buttons_frame,
    text="Get Image",
    command=lambda: execute_main_command(file_path)
)
execute_button.pack(side="left")

save_button = tk.Button(
    buttons_frame,
    text="Save URLs",
    command=lambda: save_file(file_path)
)
save_button.pack(side="left")

clear_button = tk.Button(
    buttons_frame,
    text="Clear All URLs",
    command=clear_text
)
clear_button.pack(side="left")

restore_button = tk.Button(
    buttons_frame,
    text="Restore URLs",
    command=lambda: open_file(file_path)
)
restore_button.pack(side="left")

stop_button = tk.Button(
    buttons_frame,
    text="Stop Process",
    command=stop_command
)
stop_button.pack(side="left")
# ============================================================
config_locations = [
    os.path.join(os.environ['APPDATA'], 'gallery-dl', 'config.json'),
    os.path.join(os.environ['USERPROFILE'], 'gallery-dl', 'config.json'),
    os.path.join(os.environ['USERPROFILE'], 'gallery-dl.conf')
]

config_file_path = "Config Not Found"
config_status = config_file_path
config_status_color = "red"

for location in config_locations:
    if os.path.isfile(location):
        config_file_path = location
        config_status = "Config Found"
        config_status_color = "green"
        break

# Function for reading the config file
def read_config_file(file_path):
    with open(file_path, "r") as file:
        config_data = json.load(file)
    return config_data

# Function for writing the config file
def write_config_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

download_folder_path = tk.StringVar()

# Function for updating the label_file_explorer textvariable
def update_label_file_explorer(new_text):
    download_folder_path.set(new_text)

# Function for opening the file explorer window
def get_folder_path():
    folder_selected = filedialog.askdirectory()
    download_folder_path.set(folder_selected)

    if config_file_path != "Config Not Found":
        config_data = read_config_file(config_file_path)
        new_directory = download_folder_path.get()
        config_data["extractor"]["base-directory"] = new_directory
        write_config_file(config_file_path, config_data)
        update_label_file_explorer(new_directory)

# If the config file is found, update the label_file_explorer with the base-directory value
if config_file_path != "Config Not Found":
    config_data = read_config_file(config_file_path)
    update_label_file_explorer(config_data["extractor"]["base-directory"])

# Create a File Explorer label
explorer_interface = tk.Frame(window, relief=tk.RAISED, bd=3)

config_status_label = tk.Label(
    explorer_interface,
    text=config_status,
    width=20,
    height=4,
    fg=config_status_color,
    anchor="w"
)
config_status_label.pack(side="left")

download_location_label = tk.Label(
    explorer_interface,
    textvariable=download_folder_path,
    width=100,
    height=4,
    fg="black",
    anchor="w"
)
download_location_label.pack(side="left")

browse_files_button = tk.Button(
    explorer_interface,
    text="Browse Files",
    command=get_folder_path
)
browse_files_button.pack(side="left")

# ============================================================
stage_indicator = tk.Frame(window, relief=tk.RAISED, bd=1)

bg_color = "gray"

stage_color_label = tk.Label(
    stage_indicator,
    width=1000,
    height=1,
    bg=bg_color,
)
stage_color_label.pack(side="left")

# ============================================================
# Assign widgets to grids
explorer_interface.grid(
    row=0,
    column=0,
    sticky="nsew"
)

terminal_output_window.grid(
    row=1,
    column=0,
    sticky="nsew"
)

stage_indicator.grid(
    row=2,
    column=0,
    sticky="nsew"
)

text_window.grid(
    row=3,
    column=0,
    sticky="nsew"
)

buttons_frame.grid(
    row=4,
    column=0,
    sticky="ns"
)

# Bind the custom close function to the window's close button
window.protocol("WM_DELETE_WINDOW", on_close)

# Hold application window
window.mainloop()

'''
* prerequisites:
*   > pip install pyinstaller
*       + for pyinstaller
*   > python -m pip install --upgrade pywin32
*       + give the program os permissions
*
* packaging:
*   > pyinstaller main.py --onedir --windowed --name="gallery-dl-gui.exe"
'''
