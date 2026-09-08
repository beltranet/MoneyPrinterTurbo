import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_BOLD = "/mnt/Archivos/Dropbox/Ai/MoneyPrinter/resource/fonts/BeVietnamPro-Bold.ttf"
FONT_MEDIUM = "/mnt/Archivos/Dropbox/Ai/MoneyPrinter/resource/fonts/BeVietnamPro-Medium.ttf"
OUT_DIR = "/mnt/Archivos/Dropbox/Ai/MoneyPrinter/storage/trilogia_fundacional/instagram_covers"

os.makedirs(OUT_DIR, exist_ok=True)

episodes = [
    {
        "num": "01",
        "badge": "TRILOGÍA FUNDACIONAL • PARTE 1",
        "title_lines": ["¿QUÉ ES EL QI?", "(气 - Qì)"],
        "subtitle": "La Ciencia de la Energía Vital",
        "src_img": "/mnt/Archivos/Dropbox/Ai/MoneyPrinter/storage/local_videos/ai_generated/images/ep1_1_que_es_el_qi.png",
        "base_name": "ep01_que_es_el_qi",
        "theme_color": (0, 225, 255) # Cyan glow
    },
    {
        "num": "02",
        "badge": "TRILOGÍA FUNDACIONAL • PARTE 2",
        "title_lines": ["¿QUÉ ES", "ZHĪNÉNG QÍGŌNG?", "(智能气功)"],
        "subtitle": "Ciencia y Conciencia Humana",
        "src_img": "/mnt/Archivos/Dropbox/Ai/MoneyPrinter/storage/local_videos/ai_generated/images/ep2_1_sistema_cientifico.png",
        "base_name": "ep02_que_es_zhineng_qigong",
        "theme_color": (255, 200, 80) # Gold glow
    },
    {
        "num": "03",
        "badge": "TRILOGÍA FUNDACIONAL • PARTE 3",
        "title_lines": ["EL CAMPO DE QI", "(Qì Chǎng - 气场)"],
        "subtitle": "Sincronización y Mente Colectiva",
        "src_img": "/mnt/Archivos/Dropbox/Ai/MoneyPrinter/storage/local_videos/ai_generated/images/ep2_3_mente_guia_qi.png",
        "base_name": "ep03_el_campo_de_qi",
        "theme_color": (160, 100, 255) # Purple/Indigo glow
    }
]

def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def make_instagram_reels_cover(ep):
    # 9:16 canvas (1080x1920)
    # Grid safe zone: y=420 to y=1500 (1080x1080)
    W, H = 1080, 1920
    bg = Image.open(ep["src_img"]).convert("RGBA")
    bg = bg.resize((W, H), Image.Resampling.LANCZOS)
    
    # Create dark gradient overlay in central grid area for contrast & text legibility
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    
    # Dark central vignette overlay (safe zone)
    # Rect from y=380 to y=1540 with semi-transparency
    o_draw.rectangle([0, 0, W, H], fill=(0, 0, 0, 60)) # general dimming
    
    # Gradient in middle safe area
    for y in range(350, 1570):
        # peak opacity in middle (y=960)
        dist_from_center = abs(y - 960) / 610.0
        alpha = int(210 * (1 - dist_from_center**1.8))
        alpha = max(0, min(220, alpha))
        o_draw.line([(0, y), (W, y)], fill=(5, 10, 20, alpha))
        
    # Top and bottom faint grid guide subtle lines (or smooth dark frames)
    combined = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(combined)
    
    font_badge = ImageFont.truetype(FONT_BOLD, 30)
    font_title_lg = ImageFont.truetype(FONT_BOLD, 62)
    font_title_sm = ImageFont.truetype(FONT_BOLD, 46)
    font_sub = ImageFont.truetype(FONT_BOLD, 34)
    font_foot = ImageFont.truetype(FONT_MEDIUM, 28)
    
    # Y-center of safe zone is 960. Let's arrange elements symmetrically inside y: 540..1380
    
    # 1. Badge at Y ~ 580
    badge_text = ep["badge"]
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = badge_bbox[2] - badge_bbox[0]
    bh = badge_bbox[3] - badge_bbox[1]
    
    bx = (W - bw) // 2
    by = 580
    pad_x, pad_y = 24, 12
    
    # Pill box background for badge
    draw.rounded_rectangle([bx - pad_x, by - pad_y, bx + bw + pad_x, by + bh + pad_y], radius=20, fill=(15, 25, 45, 230), outline=ep["theme_color"], width=2)
    draw.text((bx, by), badge_text, font=font_badge, fill=ep["theme_color"])
    
    # 2. Main Titles starting Y ~ 680
    curr_y = 690
    for line in ep["title_lines"]:
        is_pinyin = "(" in line or "气" in line
        f = font_title_sm if is_pinyin else font_title_lg
        col = (230, 240, 255) if not is_pinyin else ep["theme_color"]
        
        tb = draw.textbbox((0, 0), line, font=f)
        tw = tb[2] - tb[0]
        th = tb[3] - tb[1]
        tx = (W - tw) // 2
        
        # Shadow / Glow
        draw.text((tx + 2, curr_y + 2), line, font=f, fill=(0, 0, 0, 230))
        draw.text((tx, curr_y), line, font=f, fill=col)
        curr_y += th + 24
        
    # 3. Subtitle / Hook Badge at Y ~ curr_y + 20
    curr_y += 15
    sub_text = ep["subtitle"]
    sb = draw.textbbox((0, 0), sub_text, font=font_sub)
    sw = sb[2] - sb[0]
    sh = sb[3] - sb[1]
    sx = (W - sw) // 2
    
    # Rounded Pill Box for Subtitle
    draw.rounded_rectangle([sx - 30, curr_y - 10, sx + sw + 30, curr_y + sh + 14], radius=16, fill=(255, 255, 255, 230))
    draw.text((sx, curr_y), sub_text, font=font_sub, fill=(10, 15, 30))
    
    # 4. Instagram Footer branding at Y ~ 1380 (Safe Zone bottom)
    foot_text = "✦ ZHINENG QIGONG MÉXICO ✦"
    fb = draw.textbbox((0, 0), foot_text, font=font_foot)
    fw = fb[2] - fb[0]
    fx = (W - fw) // 2
    fy = 1390
    
    draw.text((fx + 1, fy + 1), foot_text, font=font_foot, fill=(0, 0, 0, 200))
    draw.text((fx, fy), foot_text, font=font_foot, fill=(200, 220, 255, 240))

    # Grid visual safe area check line (optional subtle frame or pure clean image)
    # Save 9:16 Reel Cover
    reels_path = os.path.join(OUT_DIR, f"reels_cover_{ep['base_name']}.jpg")
    combined.convert("RGB").save(reels_path, "JPEG", quality=95)
    
    # 5. Crop & Save 4:5 Feed Post (1080x1350) cropped centered from y=285 to y=1635
    img_4x5 = combined.crop((0, 285, 1080, 1635))
    path_4x5 = os.path.join(OUT_DIR, f"post_4x5_{ep['base_name']}.jpg")
    img_4x5.convert("RGB").save(path_4x5, "JPEG", quality=95)
    
    # 6. Crop & Save 1:1 Square Post (1080x1080) cropped centered from y=420 to y=1500
    img_1x1 = combined.crop((0, 420, 1080, 1500))
    path_1x1 = os.path.join(OUT_DIR, f"post_1x1_{ep['base_name']}.jpg")
    img_1x1.convert("RGB").save(path_1x1, "JPEG", quality=95)

    print(f"Generated covers for Episode {ep['num']}:")
    print(f"  - Reels 9:16: {reels_path}")
    print(f"  - Feed 4:5:   {path_4x5}")
    print(f"  - Square 1:1: {path_1x1}")

for ep in episodes:
    make_instagram_reels_cover(ep)

