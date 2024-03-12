import os
from yt_dlp import YoutubeDL
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import pyperclip



def gui_main():
    global last_handled_content
    last_handled_content = ""  # Variable to track the last content that was manually handled

    def fetch_formats(event=None):
        video_url = url_entry.get()
        if video_url and (video_url.startswith("http://") or video_url.startswith("https://")):
            format_menu['values'] = ["Fetching"]
            format_menu.set("Fetching")
            formats, info_dict = list_and_choose_format(video_url, gui=True)
            if formats:
                # Directly use the formatted list without altering it
                format_choices = formats
                format_menu['values'] = format_choices
                format_var.set(format_choices[0])
                download_button['state'] = 'normal'
            else:
                format_menu['values'] = ["No formats found"]
                format_menu.set("No formats found")

    def on_format_select():
        video_url = url_entry.get()
        format_id = format_var.get().split(' - ')[0]
        download_video(video_url, download_path_var.get(), format_id)
        messagebox.showinfo("Download Completed", "Ready for the next download.")

    def change_download_path():
        path = filedialog.askdirectory(initialdir=download_path_var.get())
        if path:
            download_path_var.set(path)

    def clear_entry(event=None):
        global last_handled_content
        current_content = url_entry.get()
        if current_content:
            last_handled_content = current_content  # Update when the input box is cleared
        url_entry.delete(0, tk.END)

    def on_paste(event):
        print('--------')
        # Function to handle paste event
        global last_handled_content
        # Use after() to ensure the pasted content is fully processed
        root.after(2, lambda: update_last_handled_content_and_fetch_formats(url_entry.get()))

    def update_last_handled_content_and_fetch_formats(content):
        global last_handled_content
        if content != last_handled_content:  # Check if the content is new
            last_handled_content = content
            fetch_formats()  # Fetch formats

    def check_clipboard():
        global last_handled_content
        clipboard_content = pyperclip.paste()
        current_content = url_entry.get()
        # Check if the clipboard content is new and different from the last handled content
        if clipboard_content.startswith("http://") or clipboard_content.startswith("https://"):
            if clipboard_content != current_content and clipboard_content != last_handled_content:
                url_entry.delete(0, tk.END)
                url_entry.insert(0, clipboard_content)
                last_handled_content = clipboard_content  # Update the last handled content
                fetch_formats()
        root.after(1000, check_clipboard)

    def on_entry_click(event):
        clear_entry()
        
    root = tk.Tk()
    root.title("YouTube Downloader")

    url_entry = tk.Entry(root, width=50, fg='grey')
    url_entry.insert(0, "Enter YouTube video URL here:")
    url_entry.bind('<Button-1>', on_entry_click)
    url_entry.bind("<FocusIn>", on_entry_click)
    url_entry.bind("<Control-v>", on_paste)
    url_entry.pack()

    format_var = tk.StringVar(root)
    format_menu = ttk.Combobox(root, textvariable=format_var, width=60, state="readonly")
    format_menu['values'] = ["Select format..."]
    format_menu.set("Select format...")
    format_menu.pack()

    download_path_var = tk.StringVar(root, value=os.path.dirname(__file__))
    tk.Label(root, text="Download Path:").pack()
    tk.Entry(root, textvariable=download_path_var, state='readonly', width=50).pack()
    change_path_button = tk.Button(root, text="Change Download Folder", command=change_download_path)
    change_path_button.pack()

    download_button = tk.Button(root, text="Download", command=on_format_select, state='disabled')
    download_button.pack()

    check_clipboard()

    root.mainloop()
    
def cli_main():
    while True:
        video_url = input("Enter YouTube video URL for download options (or type 'exit' or 'quit'): ")
        if video_url.lower() == 'exit' or video_url == 'quit':
            break
        format_id = list_and_choose_format(video_url)
        download_path = os.path.dirname(__file__)
        user_input = input(f"Enter download path or press enter to use {download_path}: ")
        if user_input:
            download_path = user_input
        download_video(video_url, download_path, format_id)
        print("\nDownload completed. Ready for the next download.")

def list_and_choose_format(url, gui=False):
    ydl_opts = {}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict['formats']

        formats.sort(key=lambda f: (
            f.get('width', 0) or 0,
            f.get('fps', 0) or 0,
            f.get('tbr', 0) or 0
        ), reverse=True)

        # Generate a common formatted list of formats
        formatted_formats = []
        for i, f in enumerate(formats, start=1):
            resolution = f"{f.get('width', 'N/A')}x{f.get('height', 'N/A')}" if f.get('width') and f.get('height') else "(audio)"
            fps = f"{int(f.get('fps', '0'))}" if f.get('fps') else "0"
            ext = f['ext']
            duration = info_dict.get('duration', None)
            filesize = f.get('filesize', None)
            if not filesize:
                filesize = calculate_filesize(f.get('tbr', None), duration)
            else:
                filesize = f"~{filesize / 1024**2:.2f} MB"
            bitrate = f"{f.get('tbr', 0):.1f}" if f.get('tbr') else "N/A"
            format_note = f.get('format_note', '')
            formatted_format = f"{i} - {resolution}, {fps} fps, {ext}, {filesize}, {bitrate} kbps, {format_note}"
            formatted_formats.append(formatted_format)
        print('--------- \n ', formatted_format)

        if gui:
            # For GUI, return the list as is for display in the dropdown
            return formatted_formats, info_dict
        else:
            # For CLI, print the formatted list and let the user choose
            print("\nAvailable formats:")
            for formatted_format in formatted_formats:
                print(formatted_format)
            choice = int(input("\nEnter the number of the format to download: ")) - 1
            format_id = formats[choice]['format_id']
            return format_id
    except Exception as e:
        print(f"Error fetching video information: {e}")
        if gui:
            return [], None  # Return empty list and None for GUI mode
        else:
            return None  # Return None for CLI mode to indicate failure
        
        
        
def calculate_filesize(tbr, duration):
    if tbr and duration:
        # tbr is in kbit/s and duration is in seconds, so we convert tbr to bit/s, multiply by duration to get bits, then convert to MB
        filesize_bytes = (tbr * 1000) * duration / 8
        filesize_mb = filesize_bytes / (1024 ** 2)
        return f"{filesize_mb:.2f} MB"
    return "N/A"

def download_video(url, download_path='.', format_id='best'):
    ydl_opts = {
        'format': format_id,
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Error downloading video: {e}")

if __name__ == "__main__":
    USE_GUI = False

    if USE_GUI:
        gui_main()
    else:
        cli_main()
        
# if __name__ == "__main__":
#     while True:
#         video_url = input("Enter YouTube video URL for download options (or type 'exit' to quit): ")
#         if video_url.lower() == 'exit':
#             break
#         format_id = list_and_choose_format(video_url)
#         download_path = os.path.dirname(__file__)
#         user_input = input(f"Enter download path or press enter to use {download_path}: ")
#         if user_input:
#             download_path = user_input
#         download_video(video_url, download_path, format_id)
#         print("\nDownload completed. Ready for the next download.")






