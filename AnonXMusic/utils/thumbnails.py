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
    image.thumbnail((maxWidth, maxHeight), Image.Resampling.LANCZOS)
    return image

def circle(img):
    img = img.convert("RGBA")
    size = min(img.size)
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)
    return output

def clear(text):
    words = text.split()
    title = ""
    for word in words:
        if len(title) + len(word) < 55:  # Reduced for better fit
            title += " " + word
    return title.strip()

def rounded_rectangle_mask(size, radius):
    """Compatible rounded rectangle mask for older PIL versions"""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    
    w, h = size
    # Top-left corner
    draw.pieslice([0, 0, radius*2, radius*2], 180, 270, fill=255)
    draw.rectangle([radius, 0, w-radius, radius], fill=255)
    draw.pieslice([w-radius*2, 0, w, radius*2], 270, 360, fill=255)
    
    # Middle
    draw.rectangle([radius, radius, w-radius, h-radius], fill=255)
    
    # Bottom corners
    draw.pieslice([0, h-radius*2, radius*2, h], 90, 180, fill=255)
    draw.rectangle([radius, h-radius, w-radius, h], fill=255)
    draw.pieslice([w-radius*2, h-radius*2, w, h], 0, 90, fill=255)
    
    return mask

def add_raindrops(draw, box, count=100):
    """Adds a realistic raindrop effect within the glass panel."""
    x1, y1, x2, y2 = box
    for _ in range(count):
        rx = random.randint(x1, x2)
        ry = random.randint(y1, y2)
        r = random.randint(2, 6)
        draw.ellipse((rx, ry, rx + r, ry + r), fill=(255, 255, 255, 40))
        draw.ellipse((rx + 1, ry + 1, rx + r - 1, ry + r - 1), fill=(10, 10, 20, 30))

def create_glass_panel(base_img, box, radius=60, blur=15, alpha=85):
    x1, y1, x2, y2 = box
    crop = base_img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(blur))
    overlay = Image.new("RGBA", crop.size, (5, 10, 25, alpha))
    glass = Image.alpha_composite(crop.convert("RGBA"), overlay)
    
    glass_draw = ImageDraw.Draw(glass)
    add_raindrops(glass_draw, (0, 0, glass.size[0], glass.size[1]), count=150)
    
    mask = rounded_rectangle_mask(glass.size, radius)
    final = Image.new("RGBA", glass.size, (0, 0, 0, 0))
    final.paste(glass, (0, 0), mask)
    return final

def add_neon_glow(image, glow_color=(0, 255, 255), blur_radius=40, expand=60, intensity=200):  # Increased glow
    base = image.convert("RGBA")
    w, h = base.size
    alpha = base.split()[-1]
    glow = Image.new("RGBA", (w + expand * 2, h + expand * 2), (0, 0, 0, 0))
    glow_mask = Image.new("L", (w + expand * 2, h + expand * 2), 0)
    glow_mask.paste(alpha, (expand, expand))
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(blur_radius))
    color_layer = Image.new("RGBA", glow.size, glow_color + (intensity,))
    glow.paste(color_layer, (0, 0), glow_mask)
    glow.paste(base, (expand, expand), base)
    return glow

def draw_text_with_glow(draw, position, text, font, fill, glow_fill, glow_passes=3):  # Enhanced glow
    x, y = position
    # Multiple glow passes for stronger effect
    for pass_num in range(glow_passes):
        offset = pass_num + 1
        glow_alpha = 80 - (pass_num * 20)
        for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
            draw.text((x + dx, y + dy), text, font=font, fill=glow_fill + (glow_alpha,))
    
    draw.text((x, y), text, font=font, fill=fill)

def draw_rounded_rect(draw, box, radius, fill=None, outline=None, width=1):
    """Manual rounded rectangle for compatibility"""
    x1, y1, x2, y2 = box
    if fill:
        mask = rounded_rectangle_mask((x2-x1, y2-y1), radius)
        temp_img = Image.new("RGBA", (x2-x1, y2-y1), fill)
        temp_img.putalpha(mask)
        draw.bitmap((x1, y1), temp_img.split()[-1], fill=fill)
    
    if outline and width > 0:
        for i in range(width):
            draw.line([(x1+radius, y1+i), (x2-radius, y1+i)], fill=outline, width=1)
            draw.line([(x2-i, y1+radius), (x2-i, y2-radius)], fill=outline, width=1)
            draw.line([(x2-radius, y2-i), (x1+radius, y2-i)], fill=outline, width=1)
            draw.line([(x1+i, y2-radius), (x1+i, y1+radius)], fill=outline, width=1)

async def download_user_photo(user_id: int):
    try:
        async for photo in app.get_chat_photos(user_id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{user_id}.jpg")
    except:
        pass
    return None

# --- Main Thumbnail Function ---

async def get_thumb(videoid, user_id):
    os.makedirs("cache", exist_ok=True)
    final_path = f"cache/{videoid}_{user_id}.png"

    if os.path.isfile(final_path):
        return final_path

    url = f"https://www.youtube.com/watch?v={videoid}"

    try:
        results = VideosSearch(url, limit=1)
        data = await results.next()
        result = data["result"][0]

        title = re.sub(r"\W+", " ", result["title"]).title()
        duration = result.get("duration", "00:00")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown")
        channel = result.get("channel", {}).get("name", "Unknown Artist")

        thumb_path = f"cache/thumb_{videoid}.png"
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, mode="wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL

        # Canvas setup
        bg_image = Image.open(thumb_path).convert("RGBA")
        background = bg_image.resize((1920, 1080), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(30))
        background = ImageEnhance.Brightness(background).enhance(0.4)

        draw = ImageDraw.Draw(background)
        
        # 1. Glass Panel with Raindrops (slightly smaller for text safety)
        panel_box = (80, 80, 1840, 1000)  # Adjusted bounds
        glass = create_glass_panel(background, panel_box, radius=60)
        background.paste(glass, (panel_box[0], panel_box[1]), glass)
        draw_rounded_rect(draw, panel_box, 60, outline=(0, 255, 255, 140), width=8)  # Thicker glow outline

        # 2. Fonts with fallback
        try:
            font_path = "AnonXMusic/assets/font.ttf"
            font_path2 = "AnonXMusic/assets/font2.ttf"
            title_font = ImageFont.truetype(font_path, 60)  # Slightly smaller
            heading_font = ImageFont.truetype(font_path2, 45)
            small_font = ImageFont.truetype(font_path2, 36)
            branding_font = ImageFont.truetype(font_path2, 52)
        except:
            title_font = ImageFont.load_default()
            heading_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            branding_font = ImageFont.load_default()

        # 3. Dynamic Elements (Thumbnails) - Enhanced glow
        yt_circle = circle(bg_image)
        yt_circle = changeImageSize(520, 520, yt_circle)  # Slightly smaller
        yt_glow = add_neon_glow(yt_circle, glow_color=(255, 60, 160), blur_radius=45, expand=65, intensity=220)
        background.paste(yt_glow, (110, 250), yt_glow)

        # User Art - Enhanced glow
        user_photo_path = await download_user_photo(user_id)
        if user_photo_path and os.path.exists(user_photo_path):
            try:
                u_img = Image.open(user_photo_path).convert("RGBA")
                u_circle = circle(u_img)
                u_circle = changeImageSize(360, 360, u_circle)
                u_glow = add_neon_glow(u_circle, glow_color=(0, 255, 255), blur_radius=50, expand=70, intensity=240)
                background.paste(u_glow, (1420, 330), u_glow)
            except:
                pass

        # 4. Text & Info - All within glass panel bounds
        # Top headers (safer positioning)
        draw_text_with_glow(draw, (100, 110), f"{unidecode(app.name).upper()}", heading_font, (132, 224, 240), (132, 224, 240, 100), glow_passes=4)
        draw_text_with_glow(draw, (1520, 110), "NOW PLAYING", heading_font, (132, 224, 240), (132, 224, 240, 100), glow_passes=4)

        # Title and info (centered, safe bounds)
        title_y = 350
        draw.text((780, title_y), clear(title), fill="white", font=title_font, stroke_width=2, stroke_fill=(0, 255, 255, 100))
        draw.text((780, title_y + 70), f"Artist: {channel}", fill=(220, 220, 220), font=small_font)
        draw.text((780, title_y + 130), f"Views: {views}", fill=(180, 180, 180), font=small_font)
        draw.text((780, title_y + 190), f"Duration: {duration}", fill=(180, 180, 180), font=small_font)
        draw.text((1470, 720), "REQUESTED BY", fill="white", font=small_font, stroke_width=1, stroke_fill=(0, 255, 255, 80))

        # 5. Progress Bar (within bounds)
        bar_x1, bar_x2, bar_y = 780, 1770, 860  # Adjusted bounds
        draw_rounded_rect(draw, (bar_x1, bar_y, bar_x2, bar_y + 16), 8, fill=(255, 255, 255, 50))
        draw_rounded_rect(draw, (bar_x1, bar_y, bar_x1 + 480, bar_y + 16), 8, fill=(0, 255, 255, 200))
        draw.text((bar_x1, bar_y + 40), "00:00", fill="white", font=small_font)
        draw.text((bar_x2 - 120, bar_y + 40), duration, fill="white", font=small_font)

        # 6. BIG FOOTER BRANDING (within bounds)
        draw_text_with_glow(draw, (110, 960), "BETA BOT HUB", branding_font, (132, 224, 240), (0, 255, 255, 180), glow_passes=5)
        draw_text_with_glow(draw, (1500, 960), "👑 THE SHIV", branding_font, (255, 60, 160), (255, 0, 170, 180), glow_passes=5)

        # Cleanup
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
        
        background = background.convert("RGB")
        background.save(final_path, "PNG", quality=95)
        return final_path

    except Exception as e:
        print(f"Thumbnail Error: {e}")
        if 'thumb_path' in locals() and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except:
                pass
        return YOUTUBE_IMG_URL
