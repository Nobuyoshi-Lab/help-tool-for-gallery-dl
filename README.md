# Gallery-DL GUI

This is a tool built based on [mikf/gallery-dl](https://github.com/mikf/gallery-dl) that provides a user-friendly interface for downloading image galleries from various websites. The GUI is built using the [Tkinter](https://docs.python.org/3/library/tkinter.html) library and simplifies the interaction with the Gallery-DL tool without requiring users to use command-line commands directly.

## Features

1. **Text window**: Enter and edit URLs of image galleries to download.
2. **Buttons**: Execute the main command, save URLs, clear URLs, and restore URLs from the file.
3. **Terminal output window**: Display the progress and results of the Gallery-DL execution.
4. **File explorer interface**: Browse and select a folder for downloading images.
5. **Status indicator**: Show whether the Gallery-DL configuration file is found or not, and display the path of the download folder.

The GUI reads and writes the Gallery-DL configuration file to update the download folder location. It also provides a convenient way for users to manage and save the URLs of image galleries for future use.

## Prerequisites

Before using the tool, you must first install `gallery-dl`, which is a command-line program for downloading image galleries from the internet. To do this, simply follow these steps:

1. Run the `install_gallery_dl.bat` script included in this repository.
    * This will automatically download and set up the latest version of `gallery-dl`.

## Usage

1. Download the latest release of Gallery-DL GUI from the [releases](https://github.com/s07091012/help-tool-for-gallery-dl/releases) page and setup with the `gallery-dl.conf` file __OR__ run the batch file.
2. Extract the contents of the zip file and run the `gallery-dl-gui/gallery-dl-gui.exe` file to start the GUI.
3. Enter and edit URLs in the text window.
4. Use the provided buttons to execute the main command, save URLs, clear URLs, and restore URLs.
5. Browse and select a download folder using the file explorer interface.
6. Monitor the progress and results in the terminal output window.

## Resources

- [gallery-dl GitHub repository](https://github.com/mikf/gallery-dl): This is the official GitHub repository for `gallery-dl`, where you can find documentation and the latest releases. **(Disclaimer: gallery-dl is not owned by me, it is originally developed by mikf)**
- [gallery-dl configuration example](https://github.com/mikf/gallery-dl/blob/master/docs/gallery-dl-example.conf): This is an example configuration file for `gallery-dl` that can be used to customize the tool's behavior. **(Disclaimer: gallery-dl-example.conf is not owned by me, it is originally developed by mikf)**
