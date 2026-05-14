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
        
        # RAIN GLASS EFFECT BACKGROUND (same as before)
        background = youtube.resize((1280, 720)).convert("RGBA")
        layer1 = background.filter(ImageFilter.GaussianBlur(20))
        layer2 = background.filter(ImageFilter.GaussianBlur(35))
        layer3 = background.filter(ImageFilter.GaussianBlur(50))
        
        gradient = Image.new("RGBA", background.size, (0, 0, 0, 0))
        grad_draw = ImageDraw.Draw(gradient)
        for i in range(background.size[1]):
            alpha = int(40 + (i / background.size[1]) * 60)
            grad_draw.line([(0, i), (background.size[0], i)], fill=(0, 0, 0, alpha))
        
        import random
        rain = Image.new("RGBA", background.size, (0, 0, 0, 0))
        rain_draw = ImageDraw.Draw(rain)
        for _ in range(150):
            x = random.randint(0, 1280)
            y1 = random.randint(0, 200)
            y2 = random.randint(500, 720)
            thickness = random.randint(1, 3)
            alpha = random.randint(20, 60)
            rain_draw.line([(x, y1), (x + random.randint(-2, 2), y2)], 
                         fill=(200, 200, 255, alpha), width=thickness)
        rain = rain.filter(ImageFilter.GaussianBlur(2))
        
        background = Image.alpha_composite(layer3, layer2)
        background = Image.alpha_composite(background, layer1)
        background = Image.alpha_composite(background, gradient)
        background = Image.alpha_composite(background, rain)
        
        vignette_mask = Image.new("L", background.size, 255)
        vig_draw = ImageDraw.Draw(vignette_mask)
        for i in range(background.size[1]):
            for j in range(background.size[0]):
                dist = ((j - background.size[0]/2)**2 + (i - background.size[1]/2)**2)**0.5
                max_dist = (background.size[0]**2 + background.size[1]**2)**0.5 / 2
                vignette_mask.putpixel((j, i), int(150 + 100 * (1 - dist/max_dist)))
        vignette = Image.new("RGBA", background.size, (0, 0, 0, 0))
        vignette.putalpha(vignette_mask)
        background = Image.alpha_composite(background, vignette)

        # Glass panel
        panel_box = (70, 110, 1210, 620)
        glass_panel = create_glass_panel(background, panel_box, radius=40, blur=18, alpha=35)
        rain_reflection = rain.resize(glass_panel.size, Image.Resampling.LANCZOS)
        rain_reflection = ImageEnhance.Brightness(rain_reflection).enhance(0.3)
        glass_panel = Image.alpha_composite(glass_panel, rain_reflection)
        background.paste(glass_panel, (panel_box[0], panel_box[1]), glass_panel)

        draw = ImageDraw.Draw(background)

        # Glass border
        border_mask = rounded_rectangle_mask((panel_box[2] - panel_box[0], panel_box[3] - panel_box[1]), 40)
        border = Image.new("RGBA", (panel_box[2] - panel_box[0], panel_box[3] - panel_box[1]), (0, 0, 0, 0))
        bd = ImageDraw.Draw(border)
        for i in range(3, 0, -1):
            bd.rounded_rectangle((i, i, border.size[0] - i, border.size[1] - i), radius=40, outline=(100, 200, 255, 80), width=2)
        bd.rounded_rectangle((2, 2, border.size[0] - 3, border.size[1] - 3), radius=40, outline=(255, 255, 255, 120), width=2)
        background.paste(border, (panel_box[0], panel_box[1]), border_mask)

        # Fonts
        arial = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 30)
        font = ImageFont.truetype("AnonXMusic/assets/font.ttf", 34)
        small_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 24)
        branding_font = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 22)  # New smaller font for branding

        # YT & User Images
        yt_circle = circle(youtube)
        yt_circle = changeImageSize(210, 210, yt_circle)
        yt_glow = add_neon_glow(yt_circle, glow_color=(255, 50, 200), blur_radius=25, expand=28)
        background.paste(yt_glow, (115, 210), yt_glow)

        if user_photo_path and os.path.isfile(user_photo_path):
            user_img = Image.open(user_photo_path).convert("RGBA")
            user_circle = circle(user_img)
            user_circle = changeImageSize(210, 210, user_circle)
            user_glow = add_neon_glow(user_circle, glow_color=(0, 255, 200), blur_radius=25, expand=28)
            background.paste(user_glow, (930, 210), user_glow)

        # Top texts
        draw_text_with_glow(draw, (95, 135), f"{unidecode(app.name)}", arial, fill=(255, 255, 255), glow_fill=(0, 255, 255))
        draw_text_with_glow(draw, (560, 165), "NOW PLAYING", small_font, fill=(255, 255, 255), glow_fill=(255, 50, 200))

        # Title & info
        start_text_x = 370
        current_y = 250
        wrapped_title = textwrap.wrap(clear(title), width=32)
        for line in wrapped_title:
            draw_text_with_glow(draw, (start_text_x, current_y), line, font, fill=(255, 255, 255), glow_fill=(0, 255, 255))
            current_y += 45

        current_y += 10
        draw.text((start_text_x, current_y), f"{channel}", fill=(230, 230, 230), font=arial)
        draw.text((start_text_x, current_y + 45), f"Views : {views[:25]}", fill=(220, 220, 220), font=small_font)
        draw.text((start_text_x, current_y + 80), f"Duration : {duration[:20]}", fill=(220, 220, 220), font=small_font)

        # *** NEW: REMOVED "REQUESTED BY" from middle - now at bottom corners ***
        
        # Music bar (moved up slightly to make space)
        draw.rounded_rectangle((140, 530, 1140, 550), radius=10, fill=(255, 255, 255, 70))
        draw.rounded_rectangle((140, 530, 700, 550), radius=10, fill=(0, 255, 255, 180))
        draw.ellipse((690, 523, 718, 557), fill=(255, 255, 255))

        draw.text((135, 560), "00:00", fill="white", font=small_font)
        draw.text((1070, 560), f"{duration[:20]}", fill="white", font=small_font)

        # *** NEW BRANDING TEXTS AT BOTTOM CORNERS ***
        
        # Left Bottom: BETA BOT HUB (Cyan glow)
        draw_text_with_glow(
            draw, (85, 635), "BETA BOT HUB", branding_font,
            fill=(0, 255, 255), glow_fill=(0, 255, 255)
        )
        
        # Right Bottom: 👑 THE SHIV (Pink/Magenta glow) - Sub se neeche
        draw_text_with_glow(
            draw, (980, 650), "👑 THE SHIV", branding_font,
            fill=(255, 50, 200), glow_fill=(255, 50, 200)
        )

        # Neon lines
        draw.line((115, 195, 1165, 195), fill=(255, 255, 255, 100), width=3)
        draw.line((115, 520, 1165, 520), fill=(255, 255, 255, 80), width=2)

        try:
            os.remove(thumb_path)
        except:
            pass

        background.save(final_path)
        return final_path

    except Exception as e:
        print(f"Thumbnail Error: {e}")
        return YOUTUBE_IMG_URL
