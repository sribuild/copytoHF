import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from huggingface_hub import HfApi

class ModernHFUploader:
    def __init__(self, root):
        self.root = root
        self.root.title("Hugging Face Uploader")
        self.root.geometry("450x620")
        self.root.configure(bg="#FFFFFF")
        self.root.resizable(False, False)

        # Apply modern "clam" theme as a clean base
        style = ttk.Style()
        style.theme_use("clam")

        # Color Palette
        bg_color = "#FFFFFF"
        text_primary = "#111827"
        text_secondary = "#6B7280"
        accent_blue = "#2563EB"
        accent_blue_hover = "#1D4ED8"
        input_bg = "#F9FAFB"
        border_color = "#D1D5DB"

        # General Styles
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=text_primary, font=("Segoe UI", 10))
        style.configure("Title.TLabel", foreground=text_primary, font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", foreground=text_secondary, font=("Segoe UI", 9))
        
        # Entry & Dropdown Styles
        style.configure("TEntry", fieldbackground=input_bg, foreground=text_primary, bordercolor=border_color, padding=5)
        style.configure("TCombobox", fieldbackground=input_bg, background=bg_color, foreground=text_primary, padding=5)

        # Button Styles
        style.configure("Secondary.TButton", font=("Segoe UI", 9), padding=6, background="#F3F4F6", foreground=text_primary, borderwidth=0)
        style.map("Secondary.TButton", background=[("active", "#E5E7EB")])

        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=10, background=accent_blue, foreground="#FFFFFF", borderwidth=0)
        style.map("Primary.TButton", background=[("active", accent_blue_hover)])

        # Main Layout Container
        main_frame = ttk.Frame(root, padding=35)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(main_frame, text="Upload to Hub", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(main_frame, text="Quickly sync local files to any Hugging Face repository.", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(2, 25))

        # Access Token Field
        ttk.Label(main_frame, text="Write Access Token").pack(anchor=tk.W, pady=(0, 4))
        self.token_entry = ttk.Entry(main_frame, show="*", width=50, font=("Segoe UI", 10))
        self.token_entry.pack(fill=tk.X, pady=(0, 15))

        # Target Repository Field
        ttk.Label(main_frame, text="Repository ID (e.g. username/repo)").pack(anchor=tk.W, pady=(0, 4))
        self.repo_entry = ttk.Entry(main_frame, width=50, font=("Segoe UI", 10))
        self.repo_entry.pack(fill=tk.X, pady=(0, 15))

        # Repository Type Dropdown
        ttk.Label(main_frame, text="Repository Type").pack(anchor=tk.W, pady=(0, 4))
        self.repo_type_var = tk.StringVar(value="model")
        self.repo_type_cb = ttk.Combobox(main_frame, textvariable=self.repo_type_var, values=["model", "dataset", "space"], state="readonly", font=("Segoe UI", 10))
        self.repo_type_cb.pack(fill=tk.X, pady=(0, 15))

        # Target Filename Field
        ttk.Label(main_frame, text="Path in Repository (e.g. folder/file.bin)").pack(anchor=tk.W, pady=(0, 4))
        self.path_entry = ttk.Entry(main_frame, width=50, font=("Segoe UI", 10))
        self.path_entry.pack(fill=tk.X, pady=(0, 20))

        # File Selection Section
        self.filepath = None
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=(0, 20))

        self.select_btn = ttk.Button(file_frame, text="Browse Files", style="Secondary.TButton", command=self.select_file)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.file_label = ttk.Label(file_frame, text="No file selected", foreground=text_secondary, font=("Segoe UI", 9))
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Progress Bar & Status
        self.progress = ttk.Progressbar(main_frame, mode="indeterminate", length=100)
        self.status_label = ttk.Label(main_frame, text="", font=("Segoe UI", 9, "bold"))

        # Upload Button
        self.upload_btn = ttk.Button(main_frame, text="Upload File", style="Primary.TButton", command=self.start_upload, state=tk.DISABLED)
        self.upload_btn.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

    def select_file(self):
        """Handle local file selection and autocomplete the destination path."""
        self.filepath = filedialog.askopenfilename(title="Select File to Upload")
        if self.filepath:
            filename = self.filepath.split('/')[-1]
            self.file_label.config(text=filename, foreground="#111827")
            self.upload_btn.config(state=tk.NORMAL)
            
            # Automatically populate the destination path if it's currently empty
            if not self.path_entry.get().strip():
                self.path_entry.insert(0, filename)

    def start_upload(self):
        """Validate inputs and spin up the background transfer thread."""
        token = self.token_entry.get().strip()
        repo = self.repo_entry.get().strip()
        repo_type = self.repo_type_var.get().strip()
        path_in_repo = self.path_entry.get().strip()

        if not all([token, repo, path_in_repo, self.filepath]):
            messagebox.showwarning("Incomplete Details", "Please fill out all text fields and select a file to continue.")
            return

        # Lock UI
        self.upload_btn.config(state=tk.DISABLED)
        self.select_btn.config(state=tk.DISABLED)
        
        # Show Progress UI
        self.progress.pack(fill=tk.X, pady=(10, 5))
        self.status_label.pack(anchor=tk.CENTER)
        self.status_label.config(text="Transfer in progress...", foreground="#2563EB")
        self.progress.start(15)

        # Execute the network request in a separate thread so the UI remains completely responsive
        threading.Thread(target=self.execute_upload, args=(token, repo, repo_type, path_in_repo), daemon=True).start()

    def execute_upload(self, token, repo, repo_type, path_in_repo):
        """Perform the file upload via the huggingface_hub API."""
        try:
            api = HfApi()
            api.upload_file(
                path_or_fileobj=self.filepath,
                path_in_repo=path_in_repo,
                repo_id=repo,
                repo_type=repo_type,
                token=token
            )
            # Route back to the main UI thread
            self.root.after(0, self.upload_success)
        except Exception as e:
            self.root.after(0, self.upload_failed, str(e))

    def upload_success(self):
        """Reset UI on successful transfer."""
        self.progress.stop()
        self.progress.pack_forget()
        self.status_label.config(text="Upload Complete", foreground="#10B981")
        
        messagebox.showinfo("Success", "Your file was successfully uploaded to the repository.")
        
        self.upload_btn.config(state=tk.NORMAL)
        self.select_btn.config(state=tk.NORMAL)

    def upload_failed(self, error):
        """Reset UI and show error details if the transfer fails."""
        self.progress.stop()
        self.progress.pack_forget()
        self.status_label.config(text="Upload Failed", foreground="#EF4444")
        
        messagebox.showerror("Error", f"An error occurred during upload:\n\n{error}")
        
        self.upload_btn.config(state=tk.NORMAL)
        self.select_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernHFUploader(root)
    root.mainloop()