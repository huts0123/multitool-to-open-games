import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import os
import subprocess
import json
from PIL import Image, ImageTk  # For handling images
import ctypes  # For extracting .exe icons on Windows

SHORTCUTS_FILE = "shortcuts.json"

class MultiToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Tool GUI")
        self.root.geometry("600x700")  # Adjusted for better layout

        # Create a frame to hold the buttons
        self.tool_frame = tk.Frame(self.root)
        self.tool_frame.pack(pady=10)

        # Create the label
        self.label = tk.Label(self.root, text="Multi-Tool with Game/Application Shortcuts with Icons")
        self.label.pack(pady=10)

        # Search bar
        self.search_var = tk.StringVar()
        self.search_bar = tk.Entry(self.root, textvariable=self.search_var)
        self.search_bar.pack(pady=5)
        self.search_bar.bind("<KeyRelease>", self.search_suggestions)
        self.search_bar.bind("<Return>", self.launch_suggested_game)

        # Suggestions listbox
        self.suggestions_listbox = tk.Listbox(self.root)
        self.suggestions_listbox.pack(pady=5)
        self.suggestions_listbox.bind("<Double-Button-1>", self.launch_selected_game)

        # Button to add new game/app shortcuts via file picker
        self.add_game_btn = tk.Button(self.root, text="Add Game/Application Shortcut", command=self.add_game_shortcut)
        self.add_game_btn.pack(pady=5)

        # Button to scan for Steam and Epic Games
        self.scan_games_btn = tk.Button(self.root, text="Scan for Steam and Epic Games", command=self.scan_for_games)
        self.scan_games_btn.pack(pady=5)

        # Button to remove shortcuts
        self.remove_shortcut_btn = tk.Button(self.root, text="Remove Selected Shortcut", command=self.remove_shortcut)
        self.remove_shortcut_btn.pack(pady=5)

        # Initialize checkbox variables
        self.checkbox_vars = {}

        # Load existing shortcuts from file
        self.shortcuts = self.load_shortcuts_from_file()
        self.load_shortcuts()

        # Configure grid column weights for responsiveness
        for i in range(5):  # Assuming you want to display up to 5 buttons in a row
            self.tool_frame.grid_columnconfigure(i, weight=1)

    def add_tool_button(self, name, command, icon_image=None, game_image=None, row=None, col=None):
        """Function to add a new button dynamically with an optional icon and game image."""
        # Create a frame for the icon, button, and checkbox
        button_frame = tk.Frame(self.tool_frame)

        # Create a checkbox for this game
        var = tk.IntVar(value=0)  # 0 = unchecked, 1 = checked
        checkbox = tk.Checkbutton(button_frame, variable=var)
        checkbox.pack(side='left', padx=5)

        self.checkbox_vars[name] = var  # Store the variable associated with the game name

        # Add the button with image above text
        tool_button = tk.Button(
            button_frame,
            text=name,
            command=command,
            width=30,
            height=2,
            compound=tk.TOP,  # Set the image above the text
            image=icon_image  # The image to be displayed
        )
        tool_button.pack(side='left', padx=5, pady=5)

        # Keep a reference to the image to prevent garbage collection
        if icon_image:
            tool_button.image = icon_image  

        # Place the button frame in the grid with sticky options for responsiveness
        button_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')

    def search_suggestions(self, event):
        """Filter suggestions based on the search bar input."""
        search_term = self.search_var.get().lower()
        self.suggestions_listbox.delete(0, tk.END)  # Clear previous suggestions

        if search_term:
            for name in self.shortcuts.keys():
                if search_term in name.lower():
                    self.suggestions_listbox.insert(tk.END, name)  # Add matching game names

        # Show or hide suggestions based on input
        if self.suggestions_listbox.size() > 0:
            self.suggestions_listbox.pack(pady=5)
        else:
            self.suggestions_listbox.pack_forget()  # Hide the listbox if no suggestions

    def launch_suggested_game(self, event):
        """Launch the game based on the selected suggestion.""" 
        selected_game = self.suggestions_listbox.get(tk.ACTIVE)
        if selected_game and selected_game in self.shortcuts:
            self.launch_game(self.shortcuts[selected_game]['path'])
            self.suggestions_listbox.pack_forget()  # Hide suggestions after launching

    def launch_selected_game(self, event):
        """Launch the game when a suggestion is double-clicked.""" 
        selected_game = self.suggestions_listbox.get(tk.ACTIVE)
        if selected_game:
            self.launch_game(self.shortcuts[selected_game]['path'])
            self.suggestions_listbox.pack_forget()  # Hide suggestions after launching

    def add_game_shortcut(self):
        """Function to add a game/application shortcut by picking a file.""" 
        game_path = filedialog.askopenfilename(title="Select Game/Application Executable or URL",
                                               filetypes=(("Executable files", "*.exe"), ("URL files", "*.url"), ("All files", "*.*")))
        if game_path:
            # Check if the file is a .url file
            if game_path.endswith('.url'):
                # Load the URL content
                with open(game_path, 'r') as file:
                    url_content = file.readlines()
                    url = url_content[1].strip().split('=')[1]  # Get the URL from the .url file
                    game_name = os.path.basename(game_path).replace('.url', '')  # Remove .url extension
            else:
                # Regular executable file handling
                game_name = simpledialog.askstring("Input", "Enter a name for the shortcut:", initialvalue=os.path.basename(game_path))

            # Check if the game name already exists
            if game_name in self.shortcuts:
                messagebox.showwarning("Duplicate Shortcut", f"The shortcut for {game_name} already exists.")
                return

            # Extract the icon from the executable or URL if possible
            icon_image = self.extract_exe_icon(game_path) if not game_path.endswith('.url') else None

            # Manually ask for the game image
            game_image_path = filedialog.askopenfilename(title="Select Game Image",
                                                         filetypes=(("Image files", "*.png;*.jpg;*.jpeg"), ("All files", "*.*")))

            game_image = self.load_game_image(game_image_path) if game_image_path else None

            # Add the shortcut with the customized name, extracted icon, and game image
            self.add_tool_button(game_name, lambda: self.launch_game(url if game_path.endswith('.url') else game_path), icon_image, game_image, 0, 0)

            # Save the shortcut
            self.save_shortcut(game_name, url if game_path.endswith('.url') else game_path, "url" if game_path.endswith('.url') else "game")

            # Refresh shortcuts to update layout
            self.refresh_shortcuts()

    def load_game_image(self, image_path):
        """Load a game image if it exists, else return None.""" 
        try:
            if os.path.exists(image_path):
                image = Image.open(image_path)
                image.thumbnail((64, 64))  # Resize the image to 64x64 for display
                return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Error loading game image: {e}")
        return None

    def launch_game(self, game_path):
        """Function to launch the selected game/application or URL.""" 
        try:
            if os.path.exists(game_path) or game_path.startswith('http'):
                if game_path.startswith('http'):  # Check if it's a URL
                    subprocess.Popen(['start', game_path], shell=True)  # Open URL in default browser
                else:
                    subprocess.Popen([game_path], shell=True)
                messagebox.showinfo("Launching Game", f"Launching {os.path.basename(game_path)}")
            else:
                messagebox.showerror("Error", "Game path not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch game: {str(e)}")

    def save_shortcut(self, name, path, shortcut_type):
        """Save the new game/application shortcut to the JSON file.""" 
        self.shortcuts[name] = {"path": path, "type": shortcut_type}
        with open(SHORTCUTS_FILE, 'w') as file:
            json.dump(self.shortcuts, file)
        messagebox.showinfo("Shortcut Saved", f"Shortcut for {name} saved!")

    def load_shortcuts(self):
        """Load the game/application shortcuts from the JSON file and add them to the GUI.""" 
        for idx, (name, data) in enumerate(self.shortcuts.items()):
            if data["type"] == "game":
                icon_image = self.extract_exe_icon(data["path"])
                # Load the corresponding game image
                game_image_path = os.path.join(os.path.dirname(data["path"]), f"{name}.png")
                game_image = self.load_game_image(game_image_path)
                self.add_tool_button(name, lambda path=data["path"]: self.launch_game(path), icon_image, game_image, idx // 5, idx % 5)
            elif data["type"] == "url":
                # URL shortcut handling, no executable icon needed
                self.add_tool_button(name, lambda url=data["path"]: self.launch_game(url), None, None, idx // 5, idx % 5)

    def load_shortcuts_from_file(self):
        """Load shortcuts from JSON file if it exists.""" 
        if os.path.exists(SHORTCUTS_FILE):
            with open(SHORTCUTS_FILE, 'r') as file:
                return json.load(file)
        return {}

    def extract_exe_icon(self, exe_path):
        """Extract the icon from the specified executable file."""
        try:
            large, small = ctypes.windll.shell32.ExtractIconEx(exe_path, 0, 1, 1, 0)
            if large:
                ico_x = ctypes.windll.user32.GetSystemMetrics(11)
                hdc = ctypes.windll.user32.GetDC(0)
                hicon = ctypes.windll.user32.CreateIconIndirect(large[0])
                return ImageTk.PhotoImage(Image.frombytes("RGBA", (ico_x, ico_x), hicon))
        except Exception as e:
            print(f"Error extracting icon: {e}")
        return None

    def refresh_shortcuts(self):
        """Refresh the displayed shortcuts after adding/removing a shortcut."""
        for widget in self.tool_frame.winfo_children():
            widget.destroy()  # Clear existing buttons

        self.load_shortcuts()

    def scan_for_games(self):
        """Placeholder for scanning games from Steam and Epic Games."""
        messagebox.showinfo("Scanning...", "Scanning for Steam and Epic Games (this feature is under development).")

    def remove_shortcut(self):
        """Remove the selected shortcuts."""
        shortcuts_to_remove = [name for name, var in self.checkbox_vars.items() if var.get() == 1]
        if not shortcuts_to_remove:
            messagebox.showwarning("No Selection", "Please select at least one shortcut to remove.")
            return

        for name in shortcuts_to_remove:
            if name in self.shortcuts:
                del self.shortcuts[name]  # Remove from the shortcuts dictionary
                del self.checkbox_vars[name]  # Remove the associated checkbox variable

        # Save the updated shortcuts
        with open(SHORTCUTS_FILE, 'w') as file:
            json.dump(self.shortcuts, file)

        messagebox.showinfo("Shortcut Removed", f"Removed shortcut(s): {', '.join(shortcuts_to_remove)}")

        self.refresh_shortcuts()

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiToolApp(root)
    root.mainloop()
