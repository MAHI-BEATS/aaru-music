import asyncio
import glob
import json
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Union, Optional
import string
import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ytSearch import VideosSearch, CustomSearch
import base64
from AnonXMusic import LOGGER
from AnonXMusic.utils.database import is_on_off
from AnonXMusic.utils.formatters import time_to_seconds
from config import YT_API_KEY, YTPROXY_URL as YTPROXY

logger = LOGGER(__name__)

def cookie_txt_file() -> Optional[str]:
    try:
        folder_path = f"{os.getcwd()}/cookies"
        filename = f"{os.getcwd()}/cookies/logs.csv"
        txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
        if not txt_files:
            raise FileNotFoundError("No .txt files found in the specified folder.")
        cookie_txt_file_path = random.choice(txt_files)
        with open(filename, 'a') as file:
            file.write(f'Chosen File : {cookie_txt_file_path}\n')
        return f"""cookies/{str(cookie_txt_file_path).split("/")[-1]}"""
    except Exception as e:
        logger.error(f"Error in cookie_txt_file: {str(e)}")
        return None

async def check_file_size(link: str) -> Optional[int]:
    async def get_format_info(link: str):
        cookie_file = cookie_txt_file()
        if not cookie_file:
            return None
            
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_file,
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

    def parse_size(formats: list) -> int:
        total_size = 0
        for format_info in formats:
            if 'filesize' in format_info and format_info['filesize']:
                total_size += format_info['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        logger.warning("No formats found.")
        return None
    
    total_size = parse_size(formats)
    return total_size

async def shell_cmd(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    error_str = errorz.decode("utf-8")
    if errorz:
        if "unavailable videos are hidden" in error_str.lower():
            return out.decode("utf-8")
        else:
            return error_str
    return out.decode("utf-8")

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\$[0-?]*[ -/]*[@-~])")
        self.dl_stats = {
            "total_requests": 0,
            "api_downloads": 0,
            "ytdlp_downloads": 0,
            "cookie_downloads": 0,
            "existing_files": 0
        }

    def _clean_link(self, link: str, videoid: Union[bool, str] = None) -> str:
        """Helper method to clean YouTube links"""
        if videoid:
            link = self.base + str(videoid)
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
        return link

    async def exists(self, link: str, videoid: Union[bool, str] = None) -> bool:
        if videoid:
            link = self.base + str(videoid)
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Optional[str]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        
        for message in messages:
            text = message.text or message.caption
            if not text:
                continue
                
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        offset, length = entity.offset, entity.length
                        return text[offset : offset + length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        clean_link = self._clean_link(link, videoid)
        results = VideosSearch(clean_link, limit=1)
        result_list = (await results.next())["result"]
        
        if not result_list:
            raise ValueError("No video found")
            
        result = result_list[0]
        title = result["title"]
        duration_min = result["duration"]
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        vidid = result["id"]
        duration_sec = 0 if str(duration_min) == "None" else int(time_to_seconds(duration_min))
        
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None) -> str:
        clean_link = self._clean_link(link, videoid)
        results = VideosSearch(clean_link, limit=1)
        result_list = (await results.next())["result"]
        return result_list[0]["title"] if result_list else "Unknown Title"

    async def duration(self, link: str, videoid: Union[bool, str] = None) -> str:
        clean_link = self._clean_link(link, videoid)
        results = VideosSearch(clean_link, limit=1)
        result_list = (await results.next())["result"]
        return result_list[0]["duration"] if result_list else "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None) -> str:
        clean_link = self._clean_link(link, videoid)
        results = VideosSearch(clean_link, limit=1)
        result_list = (await results.next())["result"]
        return result_list[0]["thumbnails"][0]["url"].split("?")[0] if result_list else ""

    async def video(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        clean_link = self._clean_link(link, videoid)
        cookie_file = cookie_txt_file()
        
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_file if cookie_file else "",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            clean_link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link: str, limit: int, user_id: int, videoid: Union[bool, str] = None) -> list:
        clean_link = self._clean_link(link, videoid)
        cookie_file = cookie_txt_file()
        cmd = f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_file if cookie_file else ''} --playlist-end {limit} --skip-download {clean_link}"
        playlist = await shell_cmd(cmd)
        
        result = [item for item in playlist.split("\n") if item.strip()]
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        clean_link = self._clean_link(link, videoid)
        results = VideosSearch(clean_link, limit=1)
        result_list = (await results.next())["result"]
        
        if not result_list:
            raise ValueError("No track found")
            
        result = result_list[0]
        track_details = {
            "title": result["title"],
            "link": result["link"],
            "vidid": result["id"],
            "duration_min": result["duration"],
            "thumb": result["thumbnails"][0]["url"].split("?")[0],
        }
        return track_details, result["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None) -> tuple:
        clean_link = self._clean_link(link, videoid)
        cookie_file = cookie_txt_file()
        ytdl_opts = {"quiet": True, "cookiefile": cookie_file} if cookie_file else {"quiet": True}
        
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(clean_link, download=False)
            for format_info in r["formats"]:
                try:
                    format_str = str(format_info["format"])
                    if "dash" in format_str.lower():
                        continue
                except:
                    continue
                
                try:
                    formats_available.append({
                        "format": format_info["format"],
                        "filesize": format_info.get("filesize", 0),
                        "format_id": format_info["format_id"],
                        "ext": format_info["ext"],
                        "format_note": format_info.get("format_note", ""),
                        "yturl": clean_link,
                    })
                except KeyError:
                    continue
        return formats_available, clean_link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None) -> tuple:
        clean_link = self._clean_link(link, videoid)
        try:
            search = VideosSearch(clean_link, limit=10)
            search_results = (await search.next()).get("result", [])

            results = []
            for result in search_results:
                duration_str = result.get("duration", "0:00")
                try:
                    parts = duration_str.split(":")
                    duration_secs = 0
                    if len(parts) == 3:
                        duration_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:
                        duration_secs = int(parts[0]) * 60 + int(parts[1])

                    if duration_secs <= 3600:
                        results.append(result)
                except (ValueError, IndexError):
                    continue

            if not results or query_type >= len(results):
                raise ValueError("No suitable videos found within duration limit")

            selected = results[query_type]
            return (
                selected["title"],
                selected["duration"],
                selected["thumbnails"][0]["url"].split("?")[0],
                selected["id"]
            )

        except Exception as e:
            logger.error(f"Error in slider: {str(e)}")
            raise ValueError("Failed to fetch video details")

    def create_session(self):
        """Create session with retries"""
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.1)
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    async def yt_dlp_download(self, vid_id: str, is_audio: bool = True, title: str = None) -> Optional[str]:
        """yt-dlp fallback downloader"""
        try:
            os.makedirs("downloads", exist_ok=True)
            
            safe_title = re.sub(r'[^\w\s-]', '', str(title or vid_id))[:100].strip() if title else vid_id
            ext = "mp3" if is_audio else "mp4"
            filepath = os.path.join("downloads", f"{safe_title}.{ext}")
            
            # Check if file exists
            if os.path.exists(filepath):
                self.dl_stats["existing_files"] += 1
                return filepath
            
            cookie_file = cookie_txt_file()
            ydl_opts = {
                'format': 'bestaudio/best' if is_audio else 'best[height<=720]',
                'outtmpl': os.path.join("downloads", f"%(title)s.%(ext)s"),
                'quiet': True,
                'no_warnings': True,
            }
            
            if cookie_file:
                ydl_opts['cookiefile'] = cookie_file
                
            if is_audio:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(f"https://youtube.com/watch?v={vid_id}", download=True)
                )
                
                # Find the actual downloaded file
                actual_file = ydl.prepare_filename(info)
                if is_audio and actual_file.endswith('.webm'):
                    # Convert webm to mp3 if needed
                    mp3_file = actual_file.rsplit('.', 1)[0] + '.mp3'
                    if os.path.exists(mp3_file):
                        actual_file = mp3_file
                
                if os.path.exists(actual_file):
                    self.dl_stats["ytdlp_downloads"] += 1
                    return actual_file
                    
            return None
            
        except Exception as e:
            logger.error(f"yt-dlp download failed: {str(e)}")
            return None

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> tuple:
        if videoid:
            vid_id = str(videoid)
            link = self.base + vid_id
        else:
            vid_id = link.split("v=")[1].split("&")[0] if "v=" in link else link

        self.dl_stats["total_requests"] += 1
        loop = asyncio.get_running_loop()

        def create_session():
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=0.1)
            session.mount('http://', HTTPAdapter(max_retries=retries))
            session.mount('https://', HTTPAdapter(max_retries=retries))
            return session

        async def download_with_requests(url: str, filepath: str, headers: dict = None) -> Optional[str]:
            try:
                session = create_session()
                response = session.get(
                    url, 
                    headers=headers, 
                    stream=True, 
                    timeout=60,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)
                
                return filepath
                
            except Exception as e:
                logger.error(f"Requests download failed: {str(e)}")
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
                return None
            finally:
                try:
                    session.close()
                except:
                    pass

        async def api_audio_dl(vid_id: str) -> Optional[str]:
            """Original API downloader with error handling"""
            try:
                if not YT_API_KEY or not YTPROXY:
                    logger.warning("API credentials missing, skipping API download")
                    return None
                
                headers = {
                    "x-api-key": YT_API_KEY,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                filepath = os.path.join("downloads", f"{vid_id}.mp3")
                if os.path.exists(filepath):
                    self.dl_stats["existing_files"] += 1
                    return filepath
                
                session = create_session()
                getAudio = session.get(f"{YTPROXY}/info/{vid_id}", headers=headers, timeout=30)
                
                if getAudio.status_code != 200:
                    logger.error(f"API returned {getAudio.status_code} for {vid_id}")
                    session.close()
                    return None
                
                songData = getAudio.json()
                session.close()
                
                status = songData.get('status')
                if status == 'success':
                    audio_url = songData['audio_url']
                    result = await download_with_requests(audio_url, filepath, headers)
                    if result:
                        self.dl_stats["api_downloads"] += 1
                        return result
                return None
                    
            except Exception as e:
                logger.error(f"API audio download failed: {str(e)}")
                return None

        async def api_video_dl(vid_id: str) -> Optional[str]:
            """Original API video downloader"""
            try:
                if not YT_API_KEY or not YTPROXY:
                    return None
                
                headers = {
                    "x-api-key": YT_API_KEY,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                filepath = os.path.join("downloads", f"{vid_id}.mp4")
                if os.path.exists(filepath):
                    self.dl_stats["existing_files"] += 1
                    return filepath
                
                session = create_session()
                getVideo = session.get(f"{YTPROXY}/info/{vid_id}", headers=headers, timeout=30)
                
                if getVideo.status_code != 200:
                    session.close()
                    return None
                
                videoData = getVideo.json()
                session.close()
                
                status = videoData.get('status')
                if status == 'success':
                    video_url = videoData['video_url']
                    result = await download_with_requests(video_url, filepath, headers)
                    if result:
                        self.dl_stats["api_downloads"] += 1
                        return result
                return None
                    
            except Exception as e:
                logger.error(f"API video download failed: {str(e)}")
                return None

        # Main download logic with fallback
        direct = True
        
        if songvideo and title:
            # Try API first, then yt-dlp
            fpath = await api_video_dl(vid_id)
            if not fpath:
                logger.info("API video failed, trying yt-dlp...")
                fpath = await self.yt_dlp_download(vid_id, is_audio=False, title=title)
            return fpath, True if fpath else False
            
        elif songaudio and title:
            # Try API first, then yt-dlp
            fpath = await api_audio_dl(vid_id)
            if not fpath:
                logger.info("API audio failed, trying yt-dlp...")
                fpath = await self.yt_dlp_download(vid_id, is_audio=True, title=title)
            return fpath, True if fpath else False
            
        elif video:
            fpath = await api_video_dl(vid_id)
            if not fpath:
                logger.info("API video failed, trying yt-dlp...")
                fpath = await self.yt_dlp_download(vid_id, is_audio=False)
        else:
            fpath = await api_audio_dl(vid_id)
            if not fpath:
                logger.info("API audio failed, trying yt-dlp...")
                fpath = await self.yt_dlp_download(vid_id, is_audio=True)
        
        return fpath, direct
