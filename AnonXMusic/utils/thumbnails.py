import os
import re
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
    img = img.convert("RGBA")
    size = min(img.size)
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
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
        if len(title) + len(word) < 60:
            title += " " + word
    return title.strip()

def rounded_rectangle_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask

def create_glass_panel(base_img, box, radius=60, blur=15, alpha=80):
    x1, y1, x2, y2 = box
    crop = base_img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(blur))
    overlay = Image.new("RGBA", crop.size, (10, 15, 30, alpha))
    glass = Image.alpha_composite(crop.convert("RGBA"), overlay)
    mask = rounded_rectangle_mask(glass.size, radius)
    final = Image.new("RGBA", glass.size, (0, 0, 0, 0))
    final.paste(glass, (0, 0), mask)
    return final

def add_neon_glow(image, glow_color=(0, 255, 255), blur_radius=25, expand=40):
    base = image.convert("RGBA")
    w, h = base.size
    alpha = base.split()[-1]
    glow = Image.new("RGBA", (w + expand * 2, h + expand * 2), (0, 0, 0, 0))
    glow_mask = Image.new("L", (w + expand * 2, h + expand * 2), 0)
    glow_mask.paste(alpha, (expand, expand))
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(blur_radius))
    color_layer = Image.new("RGBA", glow.size, glow_color + (180,))
    glow.paste(color_layer, (0, 0), glow_mask)
    glow.paste(base, (expand, expand), base)
    return glow

def draw_text_with_glow(draw, position, text, font, fill, glow_fill):
    x, y = position
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        draw.text((x + dx, y + dy), text, font=font, fill=glow_fill)
    draw.text((x, y), text, font=font, fill=fill)

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
        background = bg_image.resize((1920, 1080)).filter(ImageFilter.GaussianBlur(20))
        background = ImageEnhance.Brightness(background).enhance(0.4)

        # Draw Object
        draw = ImageDraw.Draw(background)
        
        # 1. Main Glass Panel
        panel_box = (50, 50, 1870, 1030)
        glass = create_glass_panel(background, panel_box, radius=60)
        background.paste(glass, (panel_box[0], panel_box[1]), glass)
        draw.rounded_rectangle(panel_box, radius=60, outline=(132, 224, 240, 150), width=5)

        # 2. Fonts
        font_path = "AnonXMusic/assets/font.ttf"
        font_path2 = "AnonXMusic/assets/font2.ttf"
        title_font = ImageFont.truetype(font_path, 65)
        heading_font = ImageFont.truetype(font_path2, 45)
        small_font = ImageFont.truetype(font_path2, 35)
        branding_font = ImageFont.truetype(font_path2, 30)

        # 3. Album Art (YouTube Thumb) - Left Circular
        yt_circle = circle(bg_image)
        yt_circle = changeImageSize(550, 550, yt_circle)
        yt_glow = add_neon_glow(yt_circle, glow_color=(255, 60, 160)) # Magenta
        background.paste(yt_glow, (100, 240), yt_glow)

        # 4. User Profile - Right Circular
        user_photo_path = await download_user_photo(user_id)
        if user_photo_path:
            u_img = Image.open(user_photo_path).convert("RGBA")
            u_circle = circle(u_img)
            u_circle = changeImageSize(350, 350, u_circle)
            u_glow = add_neon_glow(u_circle, glow_color=(132, 224, 240)) # Cyan
            background.paste(u_glow, (1420, 340), u_glow)

        # 5. Text Elements
        # Top Branding
        draw_text_with_glow(draw, (90, 80), f"{unidecode(app.name)}", heading_font, (132, 224, 240), (132, 224, 240, 100))
        draw_text_with_glow(draw, (1500, 80), "NOW PLAYING", heading_font, (132, 224, 240), (132, 224, 240, 100))

        # Song Details
        draw.text((750, 320), clear(title), fill="white", font=title_font)
        draw.text((750, 420), f"Artist: {channel}", fill=(200, 200, 200), font=small_font)
        draw.text((750, 480), f"Views: {views}", fill=(180, 180, 180), font=small_font)
        draw.text((750, 540), f"Duration: {duration}", fill=(180, 180, 180), font=small_font)
        
        draw.text((1450, 720), "REQUESTED BY", fill="white", font=branding_font)

        # 6. Progress Bar
        bar_x1, bar_x2, bar_y = 750, 1800, 850
        draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + 12), radius=6, fill=(255, 255, 255, 60))
        # Simulated Progress (40%)
        draw.rounded_rectangle((bar_x1, bar_y, bar_x1 + 400, bar_y + 12), radius=6, fill=(132, 224, 240))
        draw.text((bar_x1, bar_y + 30), "00:00", fill="white", font=small_font)
        draw.text((bar_x2 - 100, bar_y + 30), duration, fill="white", font=small_font)

        # 7. Footer Branding
        draw_text_with_glow(draw, (90, 960), "BETA BOT HUB", branding_font, (132, 224, 240), (0, 255, 255, 100))
        draw_text_with_glow(draw, (1600, 960), "👑 THE SHIV", branding_font, (255, 60, 160), (255, 0, 170, 100))

        # Final Cleanup & Save
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
            
        background = background.convert("RGB")
        background.save(final_path, "WEBP", quality=90)
        return final_path

    except Exception as e:
        print(f"Thumbnail Error: {e}")
        return YOUTUBE_IMG_URL
