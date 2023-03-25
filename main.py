import os
import json
import subprocess
import tkinter as tk

from pathlib import Path
from threading import Thread
from tkinter import filedialog


def update_label_bg(label, bg_color):
    label.config(bg=bg_color)


def insert_function(line, terminal, color='white'):
    terminal.configure(state="normal")
    terminal.insert(tk.END, line, color)
    terminal.configure(state="disabled")
    terminal.see(tk.END)


color_map = {
    'running': 'yellow',
    'finished': 'green',
}


def command(cmd, terminal):
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

    # Blue color for the running stage
    update_label_bg(stage_color, color_map['running'])

    while True:
        line = p.stdout.readline()
        insert_function(line, terminal)
        if not line.strip() and p.poll is not None:
            break

    try:
        p.wait(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        p.kill()

    # Green color for the finished stage
    update_label_bg(stage_color, color_map['finished'])
    window.title(title_name + dash + "Done")


def path_function(path):
    filepath = Path(path)
    filepath.touch(exist_ok=True)
    return filepath


def open_file(path):
    filepath = path_function(path)
    with open(filepath, mode="r", encoding="utf-8") as input_file:
        text = input_file.read()
        text_window.insert(tk.END, text)


def save_file(path):
    filepath = path_function(path)
    with open(filepath, mode="w", encoding="utf-8") as output_file:
        text = text_window.get("1.0", tk.END)
        output_file.write(text)
    window.title(title_name + dash + "File Saved")


def execution(path):
    clear_stdout()
    save_file(path)
    window.title(title_name + dash + "Running")
    cmd = ['cmd', '/k', 'gallery-dl', '-i', path]
    process = Thread(target=lambda: command(cmd, cmd_window))
    process.start()


def clear_stdout():
    cmd_window.configure(state="normal")
    cmd_window.delete("1.0", "end")


def clear_text():
    text_window.delete("1.0", "end")


#  default parameters
nord_bg = "#2E3440"
nord_tc = "#D8DFE4"
absolute_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(absolute_path, 'urls.txt')
title_name = "Help Tool for Gallery-DL"
dash = " - "
timeout_sec = 3
font_setting = ("Consolas", 12)
window_size = "1000x1000"

#  create application window
window = tk.Tk()
window.title(title_name)
window.geometry(window_size)
window.resizable(False, False)

#  grids configuration
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=3)
window.columnconfigure(0, weight=1)

#  create text window
text_window = tk.Text(
    window,
    bg="antique white",
    fg="black",
    font=font_setting
)

cmd_window = tk.Text(
    window,
    bg=nord_bg,
    fg=nord_tc,
    font=font_setting
)

#  open exist file with URLs, else create one
open_file(file_path)

# buttons initialization
frm_buttons = tk.Frame(window, relief=tk.RAISED, bd=4)

#  ============================================================
#  buttons configuration
btn_execution = tk.Button(
    frm_buttons,
    text = "Get Image",
    command = lambda: execution(file_path)
)
btn_execution.pack(side="left")

btn_save = tk.Button(
    frm_buttons,
    text = "Save URLs",
    command = lambda: save_file(file_path)
)
btn_save.pack(side="left")

btn_clear = tk.Button(
    frm_buttons,
    text = "Clear All URLs",
    command = clear_text
)
btn_clear.pack(side="left")

btn_restore = tk.Button(
    frm_buttons,
    text = "Restore URLs",
    command=lambda: open_file(file_path)
)
btn_restore.pack(side="left")
#  ============================================================

#  ============================================================
config_locations = [
    os.path.join(os.environ['APPDATA'], 'gallery-dl', 'config.json'),
    os.path.join(os.environ['USERPROFILE'], 'gallery-dl', 'config.json'),
    os.path.join(os.environ['USERPROFILE'], 'gallery-dl.conf')
]

conf_file_path = "Config Not Found"
conf_found = conf_file_path
conf_found_indication = "red"

for location in config_locations:
    if os.path.isfile(location):
        conf_file_path = location
        conf_found = "Config Found"
        conf_found_indication = "green"
        break

# Function for reading the config file
def read_config_file(file_path):
    with open(file_path, "r") as file:
        conf_data = json.load(file)
    return conf_data

# Function for writing the config file
def write_config_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

download_folder_path = tk.StringVar()

# Function for updating the label_file_explorer textvariable
def update_label_file_explorer(new_text):
    download_folder_path.set(new_text)

# Function for opening the file explorer window
def getFolderPath():
    folder_selected = filedialog.askdirectory()
    download_folder_path.set(folder_selected)

    if conf_file_path != "Config Not Found":
        conf_data = read_config_file(conf_file_path)
        new_directory = download_folder_path.get()
        conf_data["extractor"]["base-directory"] = new_directory
        write_config_file(conf_file_path, conf_data)
        update_label_file_explorer(new_directory)

# If the config file is found, update the label_file_explorer with the base-directory value
if conf_file_path != "Config Not Found":
    conf_data = read_config_file(conf_file_path)
    update_label_file_explorer(conf_data["extractor"]["base-directory"])

# Create a File Explorer label
explorer_interface = tk.Frame(window, relief=tk.RAISED, bd=3)

label_found_conf = tk.Label(
    explorer_interface,
    text = conf_found,
    width = 20,
    height = 4,
    fg = conf_found_indication,
    anchor="w"
)
label_found_conf.pack(side="left")

label_file_explorer = tk.Label(
    explorer_interface,
    text = f"[Download Location] {download_folder_path.get()}",
    width = 100,
    height = 4,
    fg = "black",
    anchor="w"
)
label_file_explorer.pack(side="left")

button_explore = tk.Button(
    explorer_interface,
    text = "Browse Files",
    command = getFolderPath
)
button_explore.pack(side="left")
#  ============================================================

#  assign widget to grids
explorer_interface.grid(
    row = 0,
    column = 0,
    sticky = "nsew"
)

cmd_window.grid(
    row = 1,
    column = 0,
    sticky = "nsew"
)

color = tk.Frame(window, relief=tk.RAISED, bd=1)

bg_color = "gray"

stage_color = tk.Label(
    color,
    width = 1000,
    height = 1,
    bg = bg_color,
)
stage_color.pack(side="left")

color.grid(
    row = 2,
    column = 0,
    sticky = "nsew"
)

text_window.grid(
    row = 3,
    column = 0,
    sticky = "nsew"
)

frm_buttons.grid(
    row = 4,
    column = 0,
    sticky = "ns"
)

#  hold application window
window.mainloop()

'''
* prerequisites:
*   > pip install pyinstaller
*       + for pyinstaller
*   > python -m pip install --upgrade pywin32
*       + give the program os permissions
* 
* packaging:
*   > pyinstaller main.py --onefile --windowed --icon=images/app_icon.ico
'''
