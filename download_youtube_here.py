import os
from yt_dlp import YoutubeDL

def list_and_choose_format(url):
    ydl_opts = {}
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict['formats']

    formats.sort(key=lambda f: (
        f.get('width', 0) or 0,
        f.get('fps', 0) or 0,
        f.get('tbr', 0) or 0
    ), reverse=True)

    # Column width variables
    index_width = 2
    resolution_width = 10
    fps_width = 3
    format_width = 6
    filesize_width = 13
    bitrate_width = 8
    note_width = 10

    print("Available formats:")
    # Adjust the total based on the sum of widths and separators
    print("-" * (index_width + resolution_width + fps_width + format_width + filesize_width + bitrate_width + note_width + 16))  
    print(f"{'#':<{index_width}} | {'Resolution':<{resolution_width}} | {'FPS':<{fps_width}} | {'Format':<{format_width}} | {'Filesize':<{filesize_width}} | {'(kbps)':<{bitrate_width}} | {'Note':<{note_width}}")
    print("-" * (index_width + resolution_width + fps_width + format_width + filesize_width + bitrate_width + note_width + 16))  
    
    for i, f in enumerate(formats, start=1):
        resolution = f"{f.get('width', 'N/A')}x{f.get('height', 'N/A')}" if f.get('width') and f.get('height') else "(audio)"
        fps = f"{int(f.get('fps', '0'))}" if f.get('fps') else "0"  # Capped to no decimal places
        ext = f['ext']
        # Inside your loop where you print format details:
        
        duration = info_dict.get('duration', None)  # Get duration from the info_dict
        filesize = f.get('filesize', None)
        if not filesize:  # If filesize is not directly available
            filesize = calculate_filesize(f.get('tbr', None), duration)  # Attempt to calculate
        else:
            filesize = f"~{filesize / 1024**2:.2f} MB"  # Convert to MB if available
    
        bitrate = f"{f.get('tbr', 0):.1f}" if f.get('tbr') else "N/A"
        format_note = f.get('format_note', '')
        
        # Adjusted row format with vertical lines for separation
        print(f"{i:<{index_width}} | {resolution:<{resolution_width}} | {fps:<{fps_width}} | {ext:<{format_width}} | {filesize:<{filesize_width}} | {bitrate:<{bitrate_width}} | {format_note:<{note_width}}")

    choice = int(input("\nEnter the number of the format to download: ")) - 1
    format_id = formats[choice]['format_id']
    return format_id

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
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == "__main__":
    while True:
        video_url = input("Enter YouTube video URL for download options (or type 'exit' to quit): ")
        if video_url.lower() == 'exit':
            break
        format_id = list_and_choose_format(video_url)
        download_path = os.path.dirname(__file__)
        user_input = input(f"Enter download path or press enter to use {download_path}: ")
        if user_input:
            download_path = user_input
        download_video(video_url, download_path, format_id)
        print("\nDownload completed. Ready for the next download.")



