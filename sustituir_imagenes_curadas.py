#!/usr/bin/env python3
"""
Sustitución de imágenes del banco para la Serie 15 Fundamentos
Alineación estricta con la Base de Conocimiento de ZhiNeng QiGong:
1. ep02_res1: Retrato oficial del Dr. Pang Ming (Fundador de ZNQG).
2. ep02_res2: Práctica de ZNQG en la naturaleza y conexión con el Campo de Qi.
3. ep06_res2: Rostro sereno en introspección pura (Yi Dao Qi Dao - La Mente Guía al Qi).
4. ep11_res2: Diagrama técnico auténtico de Dun Qiang Fa y columna vertebral (Mingmen).
"""

from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont

W, H = 1080, 1920
BANCO_DIR = Path(r"D:\Dropbox\Ai\MoneyPrinter\storage\local_videos\ai_generated\banco_imagenes_serie15")
BASE_CONOCIMIENTO = Path(r"D:\Dropbox\Ai\DisenoAgentico\BaseConocimiento")
SEMBRADORES = Path(r"D:\Dropbox\Ai\SembradoresDeQi")

def create_vertical_card(foreground_img, bg_color=(10, 16, 30), add_blur_bg=True, scale_fit=0.88):
    canvas = Image.new("RGB", (W, H), bg_color)
    
    if add_blur_bg:
        # Background: zoomed and heavily blurred version of the image
        bg = foreground_img.copy().convert("RGB")
        # Scale to fill canvas
        bg_ratio = max(W / bg.width, H / bg.height)
        bg = bg.resize((int(bg.width * bg_ratio), int(bg.height * bg_ratio)), Image.Resampling.LANCZOS)
        # Center crop
        left = (bg.width - W) // 2
        top = (bg.height - H) // 2
        bg = bg.crop((left, top, left + W, top + H))
        bg = bg.filter(ImageFilter.GaussianBlur(35))
        # Darken the background
        dark_overlay = Image.new("RGBA", (W, H), (5, 10, 20, 160))
        canvas = Image.alpha_composite(bg.convert("RGBA"), dark_overlay).convert("RGB")
    
    # Foreground image
    fg = foreground_img.copy().convert("RGBA")
    max_fg_w = int(W * scale_fit)
    max_fg_h = int(H * scale_fit)
    ratio = min(max_fg_w / fg.width, max_fg_h / fg.height)
    new_w = int(fg.width * ratio)
    new_h = int(fg.height * ratio)
    fg = fg.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Add subtle rounded corner mask & subtle border
    mask = Image.new("L", (new_w, new_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([0, 0, new_w, new_h], radius=24, fill=255)
    
    # Paste centered
    x = (W - new_w) // 2
    y = (H - new_h) // 2
    
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(fg, (x, y), mask)
    
    # Draw border
    draw = ImageDraw.Draw(canvas_rgba)
    draw.rounded_rectangle([x, y, x + new_w, y + new_h], radius=24, outline=(0, 200, 240, 180), width=3)
    
    return canvas_rgba.convert("RGB")

def process_ep02_res1():
    # Dr. Pang Ming
    src = SEMBRADORES / "Web" / "ImgWeb" / "QuesZNQG" / "dr-pang-ming-fundador-zhineng-qigong-retrato.jpg"
    img = Image.open(src)
    card = create_vertical_card(img, bg_color=(12, 18, 32), scale_fit=0.92)
    dest = BANCO_DIR / "ep02_que_es_zhineng_qigong_res1.jpg"
    card.save(dest, "JPEG", quality=96)
    print(f"✅ ep02_res1 generado con Dr. Pang Ming: {dest}")

def process_ep02_res2():
    # Práctica de meditación y sanación en el bosque (ZNQG)
    src = SEMBRADORES / "Web" / "ImgWeb" / "Cover" / "zhineng-qigong-practica-meditacion-sanacion-bosque.webp"
    img = Image.open(src)
    card = create_vertical_card(img, bg_color=(10, 22, 28), scale_fit=0.92)
    dest = BANCO_DIR / "ep02_que_es_zhineng_qigong_res2.jpg"
    card.save(dest, "JPEG", quality=96)
    print(f"✅ ep02_res2 generado con práctica ZNQG en la naturaleza: {dest}")

def process_ep06_res2():
    # Rostro sereno en introspección pura (La Mente Guía al Qi)
    src = SEMBRADORES / "Precampana" / "img" / "100226" / "5" / "close-up-portrait-of-serene-face-with-eyes-gently-2.jpeg"
    img = Image.open(src)
    # Crop to vertical 9:16 directly if ratio permits
    ratio = max(W / img.width, H / img.height)
    resized = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.Resampling.LANCZOS)
    left = (resized.width - W) // 2
    top = (resized.height - H) // 2
    cropped = resized.crop((left, top, left + W, top + H))
    
    # Add subtle zen vignette and Qi lighting
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([0, 0, W, H], fill=(0, 15, 30, 40))
    # Soft bottom gradient
    for y in range(H - 450, H):
        alpha = int(180 * ((y - (H - 450)) / 450.0))
        d.line([(0, y), (W, y)], fill=(5, 10, 20, alpha))
    final = Image.alpha_composite(cropped.convert("RGBA"), overlay).convert("RGB")
    dest = BANCO_DIR / "ep06_la_mente_guia_al_qi_res2.jpg"
    final.save(dest, "JPEG", quality=96)
    print(f"✅ ep06_res2 generado con introspección serena Yi Dao Qi Dao: {dest}")

def process_ep11_res2():
    # Dun Qiang Fa y columna vertebral
    columna_src = SEMBRADORES / "Web" / "ImgWeb" / "2ndLevel" / "MaterialesGrupoW" / "diagrama-flujo-energia-columna-zhineng-qigong.webp"
    columna_img = Image.open(columna_src).convert("RGB")
    
    # Create an exquisite vertical technical study card
    canvas = Image.new("RGB", (W, H), (12, 16, 26))
    
    # Background soft gradient
    draw = ImageDraw.Draw(canvas)
    for y in range(H):
        val = int(12 + (y / H) * 15)
        draw.line([(0, y), (W, y)], fill=(val, val + 4, val + 14))
        
    # Scale columna_img nicely
    c_ratio = min((W * 0.85) / columna_img.width, (H * 0.68) / columna_img.height)
    new_cw = int(columna_img.width * c_ratio)
    new_ch = int(columna_img.height * c_ratio)
    columna_resized = columna_img.resize((new_cw, new_ch), Image.Resampling.LANCZOS)
    
    # Rounded border on columna
    mask = Image.new("L", (new_cw, new_ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, new_cw, new_ch], radius=20, fill=255)
    
    cx = (W - new_cw) // 2
    cy = (H - new_ch) // 2 + 50
    
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(columna_resized, (cx, cy), mask)
    
    draw_rgba = ImageDraw.Draw(canvas_rgba)
    draw_rgba.rounded_rectangle([cx, cy, cx + new_cw, cy + new_ch], radius=20, outline=(0, 220, 255, 200), width=3)
    
    # Top badge for Dùn Qiáng Gōng
    badge_text = "✦ DÙN QIÁNG GŌNG (蹲墙功) ✦"
    draw_rgba.rounded_rectangle([(W - 550) // 2, 130, (W + 550) // 2, 210], radius=16, fill=(20, 30, 50, 230), outline=(0, 220, 255, 220), width=2)
    
    dest = BANCO_DIR / "ep11_dun_qiang_gong_res2.jpg"
    canvas_rgba.convert("RGB").save(dest, "JPEG", quality=96)
    print(f"✅ ep11_res2 generado con técnica y flujo de columna de ZNQG: {dest}")

if __name__ == "__main__":
    process_ep02_res1()
    process_ep02_res2()
    process_ep06_res2()
    process_ep11_res2()
    print("\n🎉 Todas las 4 imágenes han sido sustituidas exitosamente en el banco oficial.")
