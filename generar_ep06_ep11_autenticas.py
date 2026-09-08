#!/usr/bin/env python3
import os
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont

W, H = 1080, 1920
BANCO_DIR = Path(r"D:\Dropbox\Ai\MoneyPrinter\storage\local_videos\ai_generated\banco_imagenes_serie15")
CURRENT_DIR = Path(r"D:\Dropbox\Ai\MoneyPrinter")
FONT_MSYH = r"C:\Windows\Fonts\msyh.ttc"

def make_ep06_res2():
    # Source: ep2_3_mente_guia_qi.png (Sphere of pure Qi held in palms in nature)
    src = Path(r"D:\Dropbox\Ai\MoneyPrinter\storage\local_videos\ai_generated\images\ep2_3_mente_guia_qi.png")
    img = Image.open(src).convert("RGB")
    
    # Target: 1080x1920 (9:16 vertical)
    # Background: blurred and zoomed
    bg_ratio = max(W / img.width, H / img.height)
    bg = img.resize((int(img.width * bg_ratio), int(img.height * bg_ratio)), Image.Resampling.LANCZOS)
    left = (bg.width - W) // 2
    top = (bg.height - H) // 2
    bg = bg.crop((left, top, left + W, top + H))
    bg = bg.filter(ImageFilter.GaussianBlur(32))
    dark_overlay = Image.new("RGBA", (W, H), (5, 12, 24, 150))
    canvas = Image.alpha_composite(bg.convert("RGBA"), dark_overlay)
    
    # Foreground image: beautifully framed in center
    fg_w = int(W * 0.90)
    fg_h = int(fg_w * (img.height / img.width))
    fg = img.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
    
    mask = Image.new("L", (fg_w, fg_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, fg_w, fg_h], radius=24, fill=255)
    
    fx = (W - fg_w) // 2
    fy = (H - fg_h) // 2
    canvas.paste(fg.convert("RGBA"), (fx, fy), mask)
    
    # Draw glowing golden border
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([fx, fy, fx + fg_w, fy + fg_h], radius=24, outline=(255, 215, 0, 220), width=3)
    
    # Top title badge with MSYH (no unsupported symbols)
    badge_text = "意到气到 • YÌ DÀO QÌ DÀO"
    sub_text = "La Mente Guía al Qì • Conciencia Pura & Enfoque"
    font_b = ImageFont.truetype(FONT_MSYH, 32)
    font_s = ImageFont.truetype(FONT_MSYH, 28)
    
    tb = draw.textbbox((0, 0), badge_text, font=font_b)
    bw, bh = tb[2] - tb[0], tb[3] - tb[1]
    bx, by = (W - bw) // 2, fy - 110
    draw.rounded_rectangle([bx - 26, by - 12, bx + bw + 26, by + bh + 14], radius=16, fill=(15, 22, 38, 235), outline=(255, 215, 0, 230), width=2)
    draw.text((bx, by), badge_text, font=font_b, fill=(255, 225, 120))
    
    # Subtitle bottom
    stb = draw.textbbox((0, 0), sub_text, font=font_s)
    sw = stb[2] - stb[0]
    sx, sy = (W - sw) // 2, fy + fg_h + 45
    draw.text((sx + 1, sy + 1), sub_text, font=font_s, fill=(0, 0, 0, 230))
    draw.text((sx, sy), sub_text, font=font_s, fill=(230, 240, 255))
    
    dest = BANCO_DIR / "ep06_la_mente_guia_al_qi_res2.jpg"
    canvas.convert("RGB").save(dest, "JPEG", quality=96)
    print(f"✅ ep06_res2 generado: {dest}")

def make_ep11_res2():
    # Authentic Dun Qiang Gong drawing from Deming Qiu's book
    fig49_src = Path(r"C:\Users\SteelHorse\.gemini\antigravity-ide\brain\03199a36-69ec-464d-9fae-22e273347f2e\scratch\fig49_crop.png")
    fig49 = Image.open(fig49_src).convert("RGBA")
    
    # Carefully crop only the practitioner (x from 30 to 230, y from 30 to 290)
    # Let's inspect practitioner boundaries:
    # Width is 316, Height is 330.
    # The figure is in the left/center, text 'Figura 49' is at bottom right, vertical line is at right.
    prac_crop = fig49.crop((28, 26, 240, 278))
    
    # Invert drawing to create luminous cyan lines on dark background
    gray = ImageOps.grayscale(prac_crop)
    inv_lines = ImageOps.invert(gray)
    inv_lines = inv_lines.point(lambda p: 255 if p > 140 else int(p * 1.8))
    
    colored_lines = Image.new("RGBA", prac_crop.size, (0, 225, 255, 0))
    colored_lines.putalpha(inv_lines)
    
    # Canvas
    canvas = Image.new("RGBA", (W, H), (10, 16, 28, 255))
    draw = ImageDraw.Draw(canvas)
    
    # Subtle ambient gradient
    for y in range(H):
        alpha = int(35 * (y / H))
        draw.line([(0, y), (W, y)], fill=(6, 28, 52, alpha))
        
    font_badge = ImageFont.truetype(FONT_MSYH, 28)
    font_title = ImageFont.truetype(FONT_MSYH, 46)
    font_pinyin = ImageFont.truetype(FONT_MSYH, 34)
    font_desc = ImageFont.truetype(FONT_MSYH, 27)
    font_caption = ImageFont.truetype(FONT_MSYH, 25)
    
    # Top badge
    b_text = "MÉTODO FUNDAMENTAL DE ZHÌNÉNG QÌGŌNG"
    btb = draw.textbbox((0, 0), b_text, font=font_badge)
    bw = btb[2] - btb[0]
    bx = (W - bw) // 2
    draw.rounded_rectangle([bx - 26, 130, bx + bw + 26, 195], radius=16, fill=(15, 25, 45, 230), outline=(0, 225, 255), width=2)
    draw.text((bx, 142), b_text, font=font_badge, fill=(0, 225, 255))
    
    # Main Title
    c_title = "DÙN QIÁNG GŌNG (蹲墙功)"
    ctb = draw.textbbox((0, 0), c_title, font=font_title)
    draw.text(((W - (ctb[2] - ctb[0])) // 2, 235), c_title, font=font_title, fill=(240, 248, 255))
    
    c_sub = "Sentadillas Frente a la Pared • Lección 3"
    cstb = draw.textbbox((0, 0), c_sub, font=font_pinyin)
    draw.text(((W - (cstb[2] - cstb[0])) // 2, 305), c_sub, font=font_pinyin, fill=(0, 210, 255))
    
    # Central technical frame
    dw_w = 440
    dw_h = int(dw_w * (colored_lines.height / colored_lines.width))
    dw_resized = colored_lines.resize((dw_w, dw_h), Image.Resampling.LANCZOS)
    
    frame_x = (W - 740) // 2
    frame_y = 380
    frame_w = 740
    frame_h = dw_h + 100
    
    draw.rounded_rectangle([frame_x, frame_y, frame_x + frame_w, frame_y + frame_h], radius=24, fill=(16, 25, 44, 240), outline=(0, 190, 240, 200), width=2)
    canvas.paste(dw_resized, ((W - dw_w) // 2, frame_y + 35), dw_resized)
    
    # Caption nicely separated below frame
    caption = "Alineación Central: Descenso con Mingmen Abierto y Columna Recta"
    cap_tb = draw.textbbox((0, 0), caption, font=font_caption)
    draw.text(((W - (cap_tb[2] - cap_tb[0])) // 2, frame_y + frame_h - 45), caption, font=font_caption, fill=(175, 215, 250))
    
    # Lower technical bullets from BaseConocimiento
    box_y = frame_y + frame_h + 40
    box_h = 560
    draw.rounded_rectangle([(W - 920) // 2, box_y, (W + 920) // 2, box_y + box_h], radius=20, fill=(14, 22, 38, 240), outline=(0, 170, 225, 140), width=2)
    
    bullets = [
        "1. Postura Inicial: Pies juntos, cuerpo erguido frente a la pared.",
        "2. Contacto Continuo: Nariz y rodillas rozando la pared.",
        "3. Descenso: Bajar sin inclinar hacia atrás y sin sacar glúteos.",
        "4. Mìngmén (命门): Relajar cintura lumbar abriéndola hacia atrás.",
        "5. Ascenso: Guiar suavemente desde Bǎihuì (百会) hacia el cielo.",
        "6. Beneficios: Desbloquea canal Dū Mài (督脉) y flexibiliza la espina."
    ]
    
    cur_y = box_y + 42
    for b in bullets:
        draw.text(((W - 840) // 2, cur_y), b, font=font_desc, fill=(230, 242, 255))
        cur_y += 82
        
    dest = BANCO_DIR / "ep11_dun_qiang_gong_res2.jpg"
    canvas.convert("RGB").save(dest, "JPEG", quality=96)
    print(f"✅ ep11_res2 generado con figura limpia: {dest}")

if __name__ == "__main__":
    make_ep06_res2()
    make_ep11_res2()
