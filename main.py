import tkinter as tk
from config_dialog import ConfigDialog
from app import App  # Assuming App is the main application class

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window initially

    # Show the configuration dialog
    config_dialog_window = tk.Toplevel(root)
    config_dialog = ConfigDialog(config_dialog_window)

    # Wait until the config dialog is closed
    root.wait_window(config_dialog_window)

    # Check if configuration was completed successfully
    if config_dialog.config_complete:
        root.deiconify()  # Show the main window
        app = App(root, config_dialog.devices)  # Pass the devices to the main app
        root.mainloop()  # Start the Tkinter event loop
    else:
        root.quit()  # Exit the application if not continuing

if __name__ == "__main__":
    main()
