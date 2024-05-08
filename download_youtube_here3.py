import os
import threading
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import pyperclip
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, PostProcessingError

from print_tricks import pt

class YouTubeDownloader:
    def __init__(self):
        self.last_handled_content = ""
        self.disable_clipboard_check = False
        self.failed_files = []
        self.downloaded_files = []
        self.setup_gui()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("YouTube Downloader")
        self.create_widgets()
        self.check_clipboard()
        self.root.mainloop()

    def create_widgets(self):
        self.url_entry = self.create_url_entry()
        self.format_var, self.format_menu = self.create_format_menu()
        self.download_path_var = self.create_download_path_entry()
        self.create_download_button()
        self.create_progress_bar()  # Ensure this is called here

    def create_url_entry(self):
        url_entry = tk.Entry(self.root, width=50, fg='grey')
        url_entry.insert(0, "Enter YouTube video URL here:")
        url_entry.bind('<Button-1>', self.on_entry_click)
        url_entry.bind("<FocusIn>", self.on_entry_click)
        url_entry.bind("<Control-v>", self.on_paste)
        url_entry.pack()
        return url_entry

    def create_format_menu(self):
        format_var = tk.StringVar(self.root)
        format_menu = ttk.Combobox(self.root, textvariable=format_var, width=60, state="readonly")
        format_menu['values'] = ["Select format..."]
        format_menu.set("Select format...")
        format_menu.pack()
        return format_var, format_menu

    def create_download_path_entry(self):
        download_path_var = tk.StringVar(self.root, value=os.path.dirname(__file__))
        tk.Label(self.root, text="Download Path:").pack()
        tk.Entry(self.root, textvariable=download_path_var, state='readonly', width=50).pack()
        change_path_button = tk.Button(self.root, text="Change Download Folder", command=self.change_download_path)
        change_path_button.pack()
        return download_path_var

    def create_download_button(self):
        self.download_button = tk.Button(self.root, text="Download", command=self.on_format_select, state='disabled')
        self.download_button.pack()

    def on_paste(self, event):
        self.root.after(2, lambda: self.update_last_handled_content_and_fetch_formats(self.url_entry.get()))

    def clear_entry(self, event=None):
        current_content = self.url_entry.get()
        if current_content:
            self.last_handled_content = current_content
        self.url_entry.delete(0, tk.END)

    def change_download_path(self):
        path = filedialog.askdirectory(initialdir=self.download_path_var.get())
        if path:
            self.download_path_var.set(path)

    def is_playlist_url(self, video_url):
        """
        Enhanced check to determine if a URL is likely a playlist. This method attempts to catch more edge cases
        by looking for common playlist indicators in YouTube URLs.
        """
        from urllib.parse import urlparse, parse_qs

        parsed_url = urlparse(video_url)
        query_params = parse_qs(parsed_url.query)

        # Common query parameters that indicate a playlist
        playlist_indicators = ['list', 'p']

        # Check for standard playlist URLs
        if any(indicator in query_params for indicator in playlist_indicators):
            return True

        # Check for other YouTube URL structures that might indicate a playlist or channel
        path_segments = parsed_url.path.split('/')
        if 'channel' in path_segments or 'c' in path_segments or 'user' in path_segments:
            return True

        return False

    def on_format_select(self):
        video_url = self.url_entry.get()
        format_id = self.format_var.get().split(' - ')[0]
        self.download_video(video_url, self.download_path_var.get(), format_id)

    def fetch_formats(self, event=None):
        def fetch_thread():
            video_url = self.url_entry.get()
            if video_url and (video_url.startswith("http://") or video_url.startswith("https://")):
                # Schedule setting the fetching message
                self.root.after(0, lambda: self.format_menu.set("Fetching..."))
                if self.is_playlist_url(video_url):
                    # Handle playlist differently without fetching all formats
                    playlist_formats = self.prepare_playlist_formats()
                    # Schedule updating the combobox values for playlist formats
                    self.root.after(0, lambda: self.update_combobox_values(playlist_formats))
                    self.root.after(0, lambda: self.format_var.set(playlist_formats[0]))
                    self.root.after(0, lambda: self.download_button.config(state='normal'))
                    self.root.after(0, lambda: self.update_queue_status(f'Playlist Ready. Choose a Preferred Format'))
                else:
                    # Schedule setting the combobox to "Fetching..."
                    self.root.after(0, lambda: self.update_combobox_values(["Fetching..."]))
                    self.root.after(0, lambda: self.update_queue_status(f'Fetching formats for {video_url[:25]}...'))
                    formats, info_dict = self.list_and_choose_format(video_url, gui=True)
                    self.root.after(0, lambda: self.update_queue_status(f'Video Ready. Choose a Format'))

                    if formats:
                        # Schedule updating the combobox with fetched formats
                        self.root.after(0, lambda: self.update_combobox_values(formats))
                        self.root.after(0, lambda: self.format_var.set(formats[0]))
                        self.root.after(0, lambda: self.download_button.config(state='normal'))
                    else:
                        # Schedule updating the combobox to show "No formats found"
                        self.root.after(0, lambda: self.update_combobox_values(["No formats found"]))
                        self.root.after(0, lambda: self.format_menu.set("No formats found"))

        threading.Thread(target=fetch_thread).start()

    def update_combobox_values(self, values):
        self.format_menu['values'] = values

    def list_and_choose_format(self, video_url, gui=False):
        """
        Fetches available formats for a given YouTube video URL and returns a list of format strings.
        If gui is True, it also prepares the format list for GUI display.
        Adjusts behavior based on whether the URL is for a single video or a playlist.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                pt.t(1)
                info_dict = ydl.extract_info(video_url, download=False)
                pt.t(1)
                # Check if the URL is for a playlist
                if 'entries' in info_dict:
                    # It's a playlist
                    if gui:
                        return self.prepare_playlist_formats(), info_dict
                    else:
                        # Handle non-GUI logic if necessary
                        pass
                else:
                    # It's a single video
                    formats = info_dict.get('formats', [{}])
                    format_list = [f"{f['format_id']} - {f['format_note']} - {f['ext']}" for f in formats if f.get('format_note')]
                    return format_list, info_dict
        except Exception as e:
            print(f"Error fetching formats: {e}")
            return [], {}

    def prepare_playlist_formats(self):
        """
        Prepares a list of target resolutions for playlist downloads.
        """
        return ["4k", "1440p", "1080p", "720p", "360p", "audio only"]

    def fetch_playlist_items(self, playlist_url):
        pt()
        ydl_opts = {
            # 'extract_flat': True,
            'quiet': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(playlist_url, download=False)
            pt(result)
            if 'entries' in result:
                return result['entries']
            else:
                return []

    def download_video(self, video_url, download_path, format_id):
        if self.is_playlist_url(video_url):
            playlist_items = self.fetch_playlist_items(video_url)
            for item in playlist_items:
                item_url = f"https://www.youtube.com/watch?v={item['id']}"
                threading.Thread(target=self.download_single_video, args=(item_url, download_path, format_id)).start()
        else:
            threading.Thread(target=self.download_single_video, args=(video_url, download_path, format_id)).start()

    def download_single_video(self, video_url, download_path, format_id):
        video_path = os.path.join(download_path, '%(title)s.%(ext)s')
        format_selection = f'{format_id}+bestaudio/bestvideo[height<=720]+bestaudio/bestvideo[height<=480]+bestaudio/bestvideo[height<=360]+bestaudio/best'
        ydl_opts = {
            'format': format_selection,
            'outtmpl': video_path,
            'progress_hooks': [self.progress_hook],
            # 'verbose': True,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e:
            print(f"An error occurred during download: {e}")
            self.failed_files.append(video_url)
        finally:
            print(f"Download completed or failed for: {video_url}")


    def finalize(self):
        # Method to print failed files at the end
        if self.failed_files:
            print("Failed files:")
            for file in self.failed_files:
                print(file)

    def map_resolution_to_format(self, resolution_choice):
        """
        Maps the user's resolution choice to yt-dlp's format selection syntax.
        This is a simplified example and needs to be adjusted based on actual requirements.
        """
        format_map = {
            "4k": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
            "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "audio only": "bestaudio",
        }
        return format_map.get(resolution_choice, "best")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                progress_percent = int(downloaded_bytes / total_bytes * 100)
                self.update_progress_bar(progress_percent)
                self.update_queue_status(f"Downloading... {progress_percent}%")
        elif d['status'] == 'finished':
            self.update_progress_bar(0)  # Reset progress bar for the next download
            self.update_queue_status("Processing downloaded video...")


    def create_progress_bar(self):
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack()
        self.queue_status_label = tk.Label(self.root, text="Status: Waiting")
        self.queue_status_label.pack()

    def update_progress_bar(self, progress):
        if hasattr(self, 'progress_bar'):  # Check if progress_bar exists
            self.progress_bar["value"] = progress
            self.root.update_idletasks()

    def update_queue_status(self, status):
        if hasattr(self, 'queue_status_label'):  # Check if queue_status_label exists
            self.queue_status_label.config(text=f"Status: {status}")

    def on_entry_click(self, event=None):
        # This method is called when the user clicks into the url_entry box.
        # It clears the entry box and prevents auto-refilling from the clipboard unless it's a new URL.
        current_content = self.url_entry.get()
        if current_content == "Enter YouTube video URL here:" or current_content == self.last_handled_content:
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg='black')
        # Disable clipboard check temporarily to prevent immediate refill
        self.disable_clipboard_check = True
        self.root.after(500, self.enable_clipboard_check)  # Re-enable after a short delay

    def enable_clipboard_check(self):
        # Re-enables clipboard checking after a delay
        self.disable_clipboard_check = False

    def check_clipboard(self):
        """
        Checks the clipboard for a YouTube URL and updates the URL entry if found.
        Only updates if the clipboard content is a new video URL different from the last handled content,
        and if clipboard checking is enabled.
        """
        if not self.disable_clipboard_check:
            clipboard_content = pyperclip.paste()
            if (clipboard_content.startswith("http://") or clipboard_content.startswith("https://")) and clipboard_content != self.last_handled_content:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clipboard_content)
                self.update_last_handled_content_and_fetch_formats(clipboard_content)
        self.root.after(1000, self.check_clipboard)

    def update_last_handled_content_and_fetch_formats(self, content):
        if content != self.last_handled_content:
            self.last_handled_content = content
            self.fetch_formats()


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.finalize()
'''
https://www.youtube.com/watch?v=s9duBO87kks

https://www.youtube.com/watch?v=EIYaD0ESD1o


https://www.youtube.com/watch?v=s9duBO87kks&list=PLMi-WtatoLo-tvukcAS8YlpQUkfxX-9W1


'''