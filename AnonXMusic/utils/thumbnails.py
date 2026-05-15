import os
import re
import random
import aiofiles
import aiohttp
from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageOps,
)
from unidecode import unidecode
from ytSearch import VideosSearch
from AnonXMusic import app
from config import YOUTUBE_IMG_URL

# --- Helper Functions ---

def changeImageSize(maxWidth, maxHeight, image):
    image = image.copy()
    image.thumbnail((maxWidth, maxHeight))
    return image

def circle(img):
    try:
        img = img.convert("RGBA")
        size = min(img.size)
        img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        output.paste(img, (0, 0), mask)
        return output
    except Exception:
        return img.resize((500, 500))

def clear(text):
    if len(text) > 35:
        return text[:32] + "..."
    return text

def rounded_rectangle_mask(size, radius):
    try:
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
        return mask
    except AttributeError:
        # Fallback for older PIL versions
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle((0, 0, size[0], size[1]), fill=255)
        return mask

def add_raindrops(draw, box, count=150):
    x1, y1, x2, y2 = box
    for _ in range(count):
        rx, ry = random.randint(x1, x2), random.randint(y1, y2)
        r = random.randint(3, 8)
        draw.ellipse((rx, ry, rx + r, ry + r), fill=(255, 255, 255, 35))
        draw.ellipse((rx + 1, ry + 1, rx + 2, ry + 2), fill=(255, 255, 255, 80))

def create_glass_panel(base_img, box, radius=60, blur=20, alpha=70):
    try:
        x1, y1, x2, y2 = box
        crop = base_img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(blur))
        overlay = Image.new("RGBA", crop.size, (10, 15, 30, alpha))
        glass = Image.alpha_composite(crop.convert("RGBA"), overlay)
        
        glass_draw = ImageDraw.Draw(glass)
        add_raindrops(glass_draw, (0, 0, glass.size[0], glass.size[1]))
        
        mask = rounded_rectangle_mask(glass.size, radius)
        final = Image.new("RGBA", glass.size, (0, 0, 0, 0))
        final.paste(glass, (0, 0), mask)
        return final
    except Exception:
        # Fallback: simple blurred panel
        x1, y1, x2, y2 = box
        crop = base_img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(blur))
        return crop.convert("RGBA")

def add_neon_glow(image, glow_color=(0, 255, 255), blur_radius=25):
    try:
        base = image.convert("RGBA")
        w, h = base.size
        expand = 40
        glow = Image.new("RGBA", (w + expand * 2, h + expand * 2), (0, 0, 0, 0))
        alpha = base.split()[-1]
        glow_mask = Image.new("L", glow.size, 0)
        glow_mask.paste(alpha, (expand, expand))
        glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(blur_radius))
        
        color_layer = Image.new("RGBA", glow.size, glow_color + (180,))
        glow.paste(color_layer, (0, 0), glow_mask)
        glow.paste(base, (expand, expand), base)
        return glow
    except Exception:
        return image

def draw_text_with_glow(draw, position, text, font, fill, glow_fill):
    try:
        x, y = position
        for off in range(1, 4):
            draw.text((x-off, y), text, font=font, fill=glow_fill)
            draw.text((x+off, y), text, font=font, fill=glow_fill)
            draw.text((x, y-off), text, font=font, fill=glow_fill)
            draw.text((x, y+off), text, font=font, fill=glow_fill)
        draw.text((x, y), text, font=font, fill=fill)
    except Exception:
        # Fallback: simple text
        draw.text(position, text, font=font, fill=fill)

def ensure_dir(directory):
    """Ensure directory exists"""
    os.makedirs(directory, exist_ok=True)

# --- Main Thumbnail Function ---
async def get_thumb(videoid, user_id):
    # Ensure cache directory exists
    ensure_dir("cache")
    
    final_path = f"cache/{videoid}_{user_id}.png"
    
    # Return cached file if exists
    if os.path.isfile(final_path):
        return final_path

    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        data = await results.next()
        result = data["result"][0]

        title = result["title"]
        duration = result.get("duration", "00:00")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "N/A")
        channel = result.get("channel", {}).get("name", "Unknown Artist")

        thumb_path = f"cache/thumb_{videoid}.png"
        
        # Download thumbnail with proper error handling
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.get(thumbnail) as resp:
                    if resp.status == 200:
                        async with aiofiles.open(thumb_path, mode="wb") as f:
                            await f.write(await resp.read())
                    else:
                        return YOUTUBE_IMG_URL
        except Exception as download_err:
            print(f"Thumbnail download failed: {download_err}")
            return YOUTUBE_IMG_URL

        # Check if downloaded file exists and is valid
        if not os.path.isfile(thumb_path) or os.path.getsize(thumb_path) == 0:
            return YOUTUBE_IMG_URL

        # Background Processing
        bg_image = Image.open(thumb_path).convert("RGBA")
        background = bg_image.resize((1920, 1080)).filter(ImageFilter.GaussianBlur(40))
        background = ImageEnhance.Brightness(background).enhance(0.3)
        draw = ImageDraw.Draw(background)
        
        # Glass Panel
        panel_box = (80, 80, 1840, 1000)
        try:
            glass = create_glass_panel(background, panel_box)
            background.paste(glass, (panel_box[0], panel_box[1]), glass)
            draw.rounded_rectangle(panel_box, radius=60, outline=(0, 255, 255, 100), width=5)
        except Exception as panel_err:
            print(f"Glass panel error: {panel_err}")
            # Fallback: simple outline
            draw.rounded_rectangle(panel_box, radius=60, outline=(0, 255, 255, 100), width=5)

        # Load fonts with fallback
        font_path = "AnonXMusic/assets/font.ttf"
        try:
            title_font = ImageFont.truetype(font_path, 85)
            text_font = ImageFont.truetype(font_path, 50)
            brand_font = ImageFont.truetype(font_path, 65)
        except Exception:
            # Fallback fonts
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            brand_font = ImageFont.load_default()

        # Main Song Art (Circle with Pink Glow)
        yt_circle = circle(bg_image.resize((500, 500)))
        yt_glow = add_neon_glow(yt_circle, glow_color=(255, 20, 147))
        background.paste(yt_glow, (120, 240), yt_glow)

        # Text Info with error handling
        try:
            draw_text_with_glow(draw, (120, 120), "ANONXMUSIC", brand_font, (0, 255, 255), (0, 255, 255, 100))
            draw_text_with_glow(draw, (1400, 120), "NOW PLAYING", brand_font, (0, 255, 255), (0, 255, 255, 100))

            draw.text((700, 300), clear(title), fill="white", font=title_font)
            draw.text((700, 420), f"Artist: {channel}", fill=(200, 200, 200), font=text_font)
            draw.text((700, 500), f"Views: {views}", fill=(200, 200, 200), font=text_font)
            draw.text((700, 580), f"Duration: {duration}", fill=(200, 200, 200), font=text_font)

            # Progress Bar
            draw.rounded_rectangle((700, 800, 1750, 815), radius=8, fill=(255, 255, 255, 50))
            draw.rounded_rectangle((700, 800, 1300, 815), radius=8, fill=(0, 255, 255, 200))
            draw.text((700, 830), "00:00", fill="white", font=text_font)
            draw.text((1630, 830), duration, fill="white", font=text_font)

            # Footer
            draw_text_with_glow(draw, (120, 900), "BETA BOT HUB", brand_font, (0, 255, 255), (0, 255, 255, 100))
            draw_text_with_glow(draw, (1400, 900), "👑 THE SHIV", brand_font, (255, 20, 147), (255, 20, 147, 100))
        except Exception as text_err:
            print(f"Text rendering error: {text_err}")
            # Minimal fallback text
            draw.text((100, 100), "ANONXMUSIC", fill=(0, 255, 255), font=brand_font)
            draw.text((700, 400), clear(title), fill="white", font=title_font)

        # Save final image
        background.convert("RGB").save(final_path, "PNG", quality=95)
        return final_path

    except Exception as e:
        print(f"Thumbnail generation error for {videoid}: {e}")
        # Cleanup temp file
        if os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except:
                pass
        return YOUTUBE_IMG_URL

# Cleanup function (optional)
async def cleanup_cache():
    """Clean up old cache files"""
    cache_dir = "cache"
    if os.path.exists(cache_dir):
        for filename in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except:
                pass
