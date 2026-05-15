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


def create_glass_panel(base_img, box, radius=35, blur=10, alpha=95):
    x1, y1, x2, y2 = box
    crop = base_img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(blur))
    overlay = Image.new("RGBA", crop.size, (255, 255, 255, alpha))
    glass = Image.alpha_composite(crop.convert("RGBA"), overlay)

    mask = rounded_rectangle_mask(glass.size, radius)
    final = Image.new("RGBA", glass.size, (0, 0, 0, 0))
    final.paste(glass, (0, 0), mask)
    return final


def add_neon_glow(image, glow_color=(0, 255, 255), blur_radius=18, expand=30):
    base = image.convert("RGBA")
    w, h = base.size

    alpha = base.split()[-1]
    glow = Image.new("RGBA", (w + expand * 2, h + expand * 2), (0, 0, 0, 0))

    glow_mask = Image.new("L", (w + expand * 2, h + expand * 2), 0)
    glow_mask.paste(alpha, (expand, expand))
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(blur_radius))

    color_layer = Image.new(
        "RGBA",
        (w + expand * 2, h + expand * 2),
        (glow_color[0], glow_color[1], glow_color[2], 180),
    )
    glow.paste(color_layer, (0, 0), glow_mask)
    glow.paste(base, (expand, expand), base)
    return glow


def draw_text_with_glow(draw, position, text, font, fill, glow_fill):
    x, y = position
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
        draw.text((x + dx, y + dy), text, font=font, fill=glow_fill)
    draw.text((x, y), text, font=font, fill=fill)


async def download_user_photo(user_id: int):
    try:
        async for photo in app.get_chat_photos(user_id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{user_id}.jpg")
    except:
        pass

    try:
        async for photo in app.get_chat_photos(app.id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{app.id}.jpg")
    except:
        pass

    return None


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

        try:
            title = re.sub(r"\W+", " ", result["title"]).title()
        except:
            title = "Unsupported Title"

        try:
            duration = result["duration"]
        except:
            duration = "Unknown Mins"

        try:
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        except:
            return YOUTUBE_IMG_URL

        try:
            views = result["viewCount"]["short"]
        except:
            views = "Unknown Views"

        try:
            channel = result["channel"]["name"]
        except:
            channel = "Unknown Channel"

        thumb_path = f"cache/thumb_{videoid}.png"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, mode="wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL

        user_photo_path = await download_user_photo(user_id)

        youtube = Image.open(thumb_path).convert("RGBA")
        background = youtube.resize((1280, 720)).convert("RGBA")
        background = background.filter(ImageFilter.GaussianBlur(14))
        background = ImageEnhance.Brightness(background).enhance(0.35)
        background = ImageEnhance.Contrast(background).enhance(1.15)

        dark_overlay = Image.new("RGBA", background.size, (0, 0, 0, 70))
        background = Image.alpha_composite(background, dark_overlay)

        # Glass panel
        panel_box = (70, 110, 1210, 620)
        glass_panel = create_glass_panel(background, panel_box, radius=40, blur=12, alpha=55)
        background.paste(glass_panel, (panel_box[0], panel_box[1]), glass_panel)

        draw = ImageDraw.Draw(background)

        # Border on glass
        border_mask = rounded_rectangle_mask((panel_box[2] - panel_box[0], panel_box[3] - panel_box[1]), 40)
        border = Image.new("RGBA", (panel_box[2] - panel_box[0], panel_box[3] - panel_box[1]), (255, 255, 255, 0))
        bd = ImageDraw.Draw(border)
        bd.rounded_rectangle(
            (2, 2, border.size[0] - 3, border.size[1] - 3),
            radius=40,
            outline=(255, 255, 255, 110),
            width=2,
        )
        background.paste(border, (panel_box[0], panel_box[1]), border_mask)

        # Fonts - Added branding font
        arial = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 30)
        font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 34)
        small_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 24)
        branding_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 22)  # Branding font

        # Left neon youtube thumb - FIXED IMAGE POSITIONING
        yt_circle = circle(youtube)
        yt_circle = changeImageSize(210, 210, yt_circle)
        yt_glow = add_neon_glow(yt_circle, glow_color=(255, 0, 170), blur_radius=22, expand=24)
        # Ensure proper positioning within bounds
        glow_w, glow_h = yt_glow.size
        paste_pos = (115, 210)
        if paste_pos[0] + glow_w <= 1280 and paste_pos[1] + glow_h <= 720:
            background.paste(yt_glow, paste_pos, yt_glow)
        else:
            # Fallback: paste without glow if too big
            background.paste(yt_circle, (115, 210), yt_circle)

        # Right neon user dp - FIXED IMAGE POSITIONING
        if user_photo_path and os.path.isfile(user_photo_path):
            user_img = Image.open(user_photo_path).convert("RGBA")
            user_circle = circle(user_img)
            user_circle = changeImageSize(210, 210, user_circle)
            user_glow = add_neon_glow(user_circle, glow_color=(0, 255, 255), blur_radius=22, expand=24)
            # Ensure proper positioning within bounds
            glow_w, glow_h = user_glow.size
            paste_pos = (930, 210)
            if paste_pos[0] + glow_w <= 1280 and paste_pos[1] + glow_h <= 720:
                background.paste(user_glow, paste_pos, user_glow)
            else:
                # Fallback: paste without glow if too big
                background.paste(user_circle, (930, 210), user_circle)

        # Top branding
        draw_text_with_glow(
            draw,
            (95, 135),
            f"{unidecode(app.name)}",
            arial,
            fill=(255, 255, 255),
            glow_fill=(0, 255, 255),
        )

        draw_text_with_glow(
            draw,
            (500, 165),
            "NOW PLAYING",
            small_font,
            fill=(255, 255, 255),
            glow_fill=(255, 0, 170),
        )

        # Song details
        draw_text_with_glow(
            draw,
            (330, 270),
            clear(title),
            font,
            fill=(255, 255, 255),
            glow_fill=(0, 255, 255),
        )

        draw.text(
            (330, 330),
            f"{channel}",
            fill=(230, 230, 230),
            font=arial,
        )

        draw.text(
            (330, 380),
            f"Views : {views[:25]}",
            fill=(220, 220, 220),
            font=small_font,
        )

        draw.text(
            (330, 420),
            f"Duration : {duration[:20]}",
            fill=(220, 220, 220),
            font=small_font,
        )

        draw.text(
            (935, 445),
            "REQUESTED BY",
            fill=(255, 255, 255),
            font=small_font,
        )
        
        # Music bar
        draw.rounded_rectangle(
            (140, 555, 1140, 575),
            radius=10,
            fill=(255, 255, 255, 70),
        )
        draw.rounded_rectangle(
            (140, 555, 700, 575),
            radius=10,
            fill=(0, 255, 255, 170),
        )
        draw.ellipse((690, 548, 718, 582), fill=(255, 255, 255))

        draw.text((135, 585), "00:00", fill="white", font=small_font)
        draw.text((1070, 585), f"{duration[:20]}", fill="white", font=small_font)

        # Soft neon lines
        draw.line((115, 195, 1165, 195), fill=(255, 255, 255, 90), width=2)
        draw.line((115, 520, 1165, 520), fill=(255, 255, 255, 70), width=2)

        # BRANDING TEXT - Added at bottom
        draw_text_with_glow(
            draw, 
            (85, 610),  # Bottom left
            "BETA BOT HUB", 
            branding_font,
            fill=(0, 255, 255), 
            glow_fill=(0, 255, 255, 120)
        )
        
        draw_text_with_glow(
            draw, 
            (980, 625),  # Bottom right
            "👑 THE SHIV", 
            branding_font,
            fill=(255, 50, 200), 
            glow_fill=(255, 50, 200, 120)
        )

        try:
            os.remove(thumb_path)
        except:
            pass

        background.save(final_path)
        return final_path

    except Exception as e:
        print(f"Thumbnail Error: {e}")
        return YOUTUBE_IMG_URL
