import tkinter as tk
from config_dialog import ConfigDialog
from app import App
from chirpstack_client import ChirpStackClient

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
        # Create an instance of ChirpStackClient with the configuration
        chirpstack_client = ChirpStackClient(
            f"{config_dialog.server_address.get()}:{config_dialog.server_port.get()}",
            config_dialog.api_token.get()
        )

        root.deiconify()  # Show the main window
        app = App(
            root,
            config_dialog.devices,
            chirpstack_client,
            config_dialog.app_id.get(),  # Pass the App ID to the App class
            config_dialog.tenant_id.get()  # Pass the Tenant ID to the App class
        )
        root.mainloop()  # Start the Tkinter event loop
    else:
        root.quit()  # Exit the application if not continuing

if __name__ == "__main__":
    main()
