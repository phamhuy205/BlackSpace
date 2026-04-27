import re

def get_embed_url(url):
    """
    Chuyển đổi các loại link (Drive, DoodStream, YouTube...) về dạng nhúng (Embed) 
    để có thể chạy được trong iframe mà không bị lỗi.
    """
    if not url:
        return ""

    # 1. Xử lý Google Drive
    drive_match = re.search(r'(?:drive\.google\.com/(?:file/d/|open\?id=)|docs\.google\.com/file/d/)([a-zA-Z0-9_-]+)', url)
    if drive_match:
        file_id = drive_match.group(1)
        return f"https://drive.google.com/file/d/{file_id}/preview"

    # 2. Xử lý DoodStream (Nếu bạn dùng server này)
    if "dood" in url:
        # Chuyển link xem sang link embed: dood.to/d/xxx -> dood.to/e/xxx
        return url.replace("/d/", "/e/")

    # 3. Xử lý OK.ru
    if "ok.ru" in url:
        video_id = url.split("/")[-1]
        return f"https://ok.ru/videoembed/{video_id}"

    # 4. Xử lý YouTube
    yt_match = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/))([a-zA-Z0-9_-]+)', url)
    if yt_match:
        return f"https://www.youtube.com/embed/{yt_match.group(1)}"

    return url
