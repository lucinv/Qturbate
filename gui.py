import tkinter as tk
from tkinter import ttk

# Constants
THUMBNAIL_SIZE = (200, 113)
PADDING = 10

class ThumbnailGridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grille de Vignettes Responsive et Scrollable")

        # Canvas + Scrollbars
        self.canvas = tk.Canvas(root)
        self.scrollbar_y = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(root, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Attach scrollable frame to canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        # Grid placement
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Bind resizing event
        self.root.bind("<Configure>", self.on_resize)

        # Store current number of rows and columns
        self.current_rows = 0
        self.current_cols = 0
        self.thumbnails = []

    def get_grid_size(self, width, height):
        cols = max(1, width // (THUMBNAIL_SIZE[0] + PADDING))
        rows = 100  # Arbitrary high number to allow scroll
        return rows, cols

    def create_thumbnails(self, rows, cols):
        # Clear existing thumbnails
        for thumb in self.thumbnails:
            thumb.destroy()
        self.thumbnails.clear()

        for row in range(rows):
            for col in range(cols):
                canvas = tk.Canvas(
                    self.scrollable_frame,
                    width=THUMBNAIL_SIZE[0],
                    height=THUMBNAIL_SIZE[1],
                    bg="white",
                    highlightthickness=1,
                    highlightbackground="gray"
                )
                canvas.create_rectangle(
                    10, 10,
                    THUMBNAIL_SIZE[0] - 10,
                    THUMBNAIL_SIZE[1] - 10,
                    fill="skyblue"
                )
                canvas.grid(row=row, column=col, padx=PADDING, pady=PADDING)
                self.thumbnails.append(canvas)

    def on_resize(self, event):
        if event.widget == self.root:
            frame_width = self.root.winfo_width()
            frame_height = self.root.winfo_height()
            _, cols = self.get_grid_size(frame_width, frame_height)

            if cols != self.current_cols:
                self.current_cols = cols
                self.create_thumbnails(5, cols)  # Fixed row count for demo

# Launch the application
root = tk.Tk()
app = ThumbnailGridApp(root)
root.mainloop()
