#!/usr/bin/env python3
import os
import sys
import uuid
import shutil
from pathlib import Path
import subprocess
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
import re

CURRENT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(CURRENT_DIR))

from loguru import logger
from app.models.schema import VideoParams, VideoAspect, VideoConcatMode, VideoTransitionMode
from app.services import voice, video as video_service, material as material_service, task as task_service

FONT_BOLD = str(CURRENT_DIR / "resource" / "fonts" / "BeVietnamPro-Bold.ttf")
FONT_MEDIUM = str(CURRENT_DIR / "resource" / "fonts" / "BeVietnamPro-Medium.ttf")

def add_audio_tail_padding(audio_path: str, padding_seconds: float = 1.0):
    if os.path.exists(audio_path):
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        temp_path = audio_path + ".padded.mp3"
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", audio_path,
            "-af", f"apad=pad_dur={padding_seconds}",
            temp_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        os.replace(temp_path, audio_path)

def extract_and_normalize_subclip(raw_video_path: str, start_sec: int, duration_sec: int, output_path: str):
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = [
        ffmpeg_exe,
        "-y",
        "-ss", str(start_sec),
        "-i", raw_video_path,
        "-t", str(duration_sec),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264",
        "-preset", "fast",
        "-an",
        output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def generate_ig_covers(ep, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    W, H = 1080, 1920
    bg = Image.open(ep["src_img"]).convert("RGBA")
    bg = bg.resize((W, H), Image.Resampling.LANCZOS)
    
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    o_draw.rectangle([0, 0, W, H], fill=(0, 0, 0, 60))
    
    for y in range(350, 1570):
        dist_from_center = abs(y - 960) / 610.0
        alpha = int(210 * (1 - dist_from_center**1.8))
        alpha = max(0, min(220, alpha))
        o_draw.line([(0, y), (W, y)], fill=(5, 10, 20, alpha))
        
    combined = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(combined)
    
    font_badge = ImageFont.truetype(FONT_BOLD, 30)
    font_title_lg = ImageFont.truetype(FONT_BOLD, 58)
    font_title_sm = ImageFont.truetype(FONT_BOLD, 44)
    font_sub = ImageFont.truetype(FONT_BOLD, 32)
    font_foot = ImageFont.truetype(FONT_MEDIUM, 28)
    
    badge_text = ep["badge"]
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = badge_bbox[2] - badge_bbox[0]
    bh = badge_bbox[3] - badge_bbox[1]
    bx, by = (W - bw) // 2, 580
    
    draw.rounded_rectangle([bx - 24, by - 12, bx + bw + 24, by + bh + 12], radius=20, fill=(15, 25, 45, 230), outline=ep["theme_color"], width=2)
    draw.text((bx, by), badge_text, font=font_badge, fill=ep["theme_color"])
    
    curr_y = 690
    for line in ep["title_lines"]:
        is_pinyin = "(" in line or "气" in line
        f = font_title_sm if is_pinyin else font_title_lg
        col = (230, 240, 255) if not is_pinyin else ep["theme_color"]
        
        tb = draw.textbbox((0, 0), line, font=f)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        tx = (W - tw) // 2
        
        draw.text((tx + 2, curr_y + 2), line, font=f, fill=(0, 0, 0, 230))
        draw.text((tx, curr_y), line, font=f, fill=col)
        curr_y += th + 22
        
    curr_y += 15
    sub_text = ep["subtitle"]
    sb = draw.textbbox((0, 0), sub_text, font=font_sub)
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]
    sx = (W - sw) // 2
    
    draw.rounded_rectangle([sx - 28, curr_y - 10, sx + sw + 28, curr_y + sh + 12], radius=16, fill=(255, 255, 255, 230))
    draw.text((sx, curr_y), sub_text, font=font_sub, fill=(10, 15, 30))
    
    foot_text = "✦ ZHINENG QIGONG MÉXICO ✦"
    fb = draw.textbbox((0, 0), foot_text, font=font_foot)
    fw = fb[2] - fb[0]
    fx, fy = (W - fw) // 2, 1390
    draw.text((fx + 1, fy + 1), foot_text, font=font_foot, fill=(0, 0, 0, 200))
    draw.text((fx, fy), foot_text, font=font_foot, fill=(200, 220, 255, 240))

    reels_path = os.path.join(out_dir, f"reels_cover_{ep['base_name']}.jpg")
    combined.convert("RGB").save(reels_path, "JPEG", quality=95)
    
    img_4x5 = combined.crop((0, 285, 1080, 1635))
    path_4x5 = os.path.join(out_dir, f"post_4x5_{ep['base_name']}.jpg")
    img_4x5.convert("RGB").save(path_4x5, "JPEG", quality=95)
    
    img_1x1 = combined.crop((0, 420, 1080, 1500))
    path_1x1 = os.path.join(out_dir, f"post_1x1_{ep['base_name']}.jpg")
    img_1x1.convert("RGB").save(path_1x1, "JPEG", quality=95)

def generate_serie_15_full():
    output_dir = CURRENT_DIR / "storage" / "trilogia_fundacional"
    output_dir.mkdir(parents=True, exist_ok=True)

    ig_covers_dir = output_dir / "instagram_covers"
    ig_covers_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = CURRENT_DIR / "storage" / "cache_videos" / "serie15_subclips"
    cache_dir.mkdir(parents=True, exist_ok=True)

    personales_dir = CURRENT_DIR / "storage" / "local_videos" / "personales"
    ai_clips_dir = CURRENT_DIR / "storage" / "local_videos" / "ai_generated" / "clips"
    ai_img_dir = CURRENT_DIR / "storage" / "local_videos" / "ai_generated" / "images"

    logger.info("=== INICIANDO PRODUCCIÓN BATCH AUTÓNOMA: SERIE 15 VIDEOS FUNDAMENTALES ===")

    episodes = [
        # LUNES
        {
            "num": "01",
            "day": "LUNES",
            "title": "¿Qué es el Qì?",
            "output_name": "01_Que_es_el_Qi.mp4",
            "base_name": "ep01_que_es_el_qi",
            "badge": "SERIE FUNDAMENTOS • EP. 01",
            "title_lines": ["¿QUÉ ES EL QI?", "(气 - Qì)"],
            "subtitle": "La Ciencia de la Energía Vital",
            "src_img": str(ai_img_dir / "ep1_1_que_es_el_qi.png"),
            "theme_color": (0, 225, 255),
            "phonetic_script": (
                "¿Qué es realmente el Chi? Lejos de conceptos místicos o esotéricos, en Chineng Chikung entendemos el Chi "
                "como la sustancia y la información fundamental que compone todo en el universo. Es la energía vital "
                "que nutre tus órganos, regula tu sistema nervioso y sostiene tu vitalidad diaria. Cuando el Chi fluye libremente "
                "y es abundante, el cuerpo se autorregula y la mente experimenta claridad y paz. En Sembradores de Chi, "
                "te enseñamos a cultivar y gestionar tu propia energía con autonomía y sin depender de nadie. "
                "Síguenos para aprender a sentir y transformar tu Chi día a día."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì", "Sembradores de Chi": "Sembradores de Qì"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep1_1_que_es_el_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 20, "dur": 6},
                {"stock": ai_clips_dir / "ep1_2_organos_vitalidad.mp4"},
                {"stock": ai_clips_dir / "ep1_3_mente_claridad.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 80, "dur": 6},
                {"stock": ai_clips_dir / "ep1_4_cultivo_autonomo.mp4"},
                {"stock": ai_clips_dir / "ep1_5_transformacion_diaria.mp4"}
            ]
        },
        {
            "num": "02",
            "day": "LUNES",
            "title": "¿Qué es Zhīnéng Qígōng?",
            "output_name": "02_Que_es_Zhineng_Qigong.mp4",
            "base_name": "ep02_que_es_zhineng_qigong",
            "badge": "SERIE FUNDAMENTOS • EP. 02",
            "title_lines": ["¿QUÉ ES", "ZHĪNÉNG QÍGŌNG?", "(智能气功)"],
            "subtitle": "Ciencia y Conciencia Humana",
            "src_img": str(ai_img_dir / "ep2_1_sistema_cientifico.png"),
            "theme_color": (255, 200, 80),
            "phonetic_script": (
                "¿Qué hace diferente a Chineng Chikung de otras disciplinas? Creado por el Doctor Pang Ming, "
                "Chineng Chikung es un sistema científico de medicina energética y desarrollo de la conciencia. "
                "No se trata solo de movimientos físicos, sino de la integración pura entre mente, cuerpo y Chi. "
                "A través de métodos sencillos y profundos, entrenamos a la mente para guiar la energía a donde el cuerpo más lo necesita. "
                "Es una herramienta de transformación personal que te devuelve el control de tu salud y bienestar. "
                "Descubre el poder de cultivar tu vida con Chineng Chikung."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì", "Doctor Pang Ming": "Doctor Páng Míng"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep2_1_sistema_cientifico.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 110, "dur": 6},
                {"stock": ai_clips_dir / "ep2_2_integracion_mente_cuerpo.mp4"},
                {"stock": ai_clips_dir / "ep2_3_mente_guia_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 170, "dur": 6},
                {"stock": ai_clips_dir / "ep2_4_salud_bienestar.mp4"}
            ]
        },
        {
            "num": "03",
            "day": "LUNES",
            "title": "El Campo de Qì (Qì Chǎng)",
            "output_name": "03_El_Campo_de_Qi_Qi_Chang.mp4",
            "base_name": "ep03_el_campo_de_qi",
            "badge": "SERIE FUNDAMENTOS • EP. 03",
            "title_lines": ["EL CAMPO DE QI", "(Qì Chǎng - 气场)"],
            "subtitle": "Sincronización y Mente Colectiva",
            "src_img": str(ai_img_dir / "ep2_3_mente_guia_qi.png"),
            "theme_color": (160, 100, 255),
            "phonetic_script": (
                "¿Has sentido alguna vez la fuerza de entrenar o meditar en grupo? En Chineng Chikung esto se conoce como Chi Chang, "
                "o el Campo de Chi. Un Chi Chang es un espacio donde la intención y la energía de muchas personas se sincronizan "
                "para crear una resonancia colectiva de sanación y armonía. Cuando te conectas al campo, tu práctica se vuelve "
                "diez veces más profunda y efectiva que al practicar en soledad. En Sembradores de Chi organizamos el campo en cada sesión "
                "para acompañarte en tu proceso. Únete a nuestra comunidad y siente la fuerza del campo de Chi."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi Chang": "Qì Chǎng", "Chi": "Qì", "Sembradores de Chi": "Sembradores de Qì"},
            "clips_config": [
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 220, "dur": 6},
                {"stock": ai_clips_dir / "sample_qi_flow.mp4"},
                {"stock": ai_clips_dir / "ep2_3_mente_guia_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 260, "dur": 6},
                {"stock": ai_clips_dir / "ep1_5_transformacion_diaria.mp4"}
            ]
        },
        # MARTES
        {
            "num": "04",
            "day": "MARTES",
            "title": "El Qì Primordial (Hùnyuán Qì)",
            "output_name": "04_El_Qi_Primordial_Hunyuan_Qi.mp4",
            "base_name": "ep04_el_qi_primordial",
            "badge": "TEORÍA HUNYUAN • EP. 04",
            "title_lines": ["EL QI PRIMORDIAL", "(Hùnyuán Qì - 混元气)"],
            "subtitle": "La Fuente Inagotable de la Naturaleza",
            "src_img": str(ai_img_dir / "ep1_1_que_es_el_qi.png"),
            "theme_color": (0, 225, 255),
            "phonetic_script": (
                "Todo en el universo proviene de una sola fuente inagotable: el Hunyuan Chi. "
                "En la teoría de Chineng Chikung, el Hunyuan Chi es la sustancia primordial informe de donde nacen la materia, "
                "la energía y la información. A diferencia de otros sistemas de energía, el Hunyuan Chi no tiene límites. "
                "Al practicar Chineng Chikung, no gastas tu propia energía vital, sino que te conectas directamente "
                "con la abundancia infinita de la naturaleza. Aprende a nutrir tu vida desde la fuente pura."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Hunyuan Chi": "Hùnyuán Qì", "Chi": "Qì"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep1_1_que_es_el_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 15, "dur": 6},
                {"stock": ai_clips_dir / "ep1_4_cultivo_autonomo.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 95, "dur": 6},
                {"stock": ai_clips_dir / "sample_qi_flow.mp4"}
            ]
        },
        {
            "num": "05",
            "day": "MARTES",
            "title": "La Teoría de las Tres Capas",
            "output_name": "05_La_Teoria_de_las_Tres_Capas.mp4",
            "base_name": "ep05_las_tres_capas",
            "badge": "TEORÍA HUNYUAN • EP. 05",
            "title_lines": ["LAS TRES CAPAS", "Materia, Energía e Información"],
            "subtitle": "Sanación desde la Información Pura",
            "src_img": str(ai_img_dir / "ep2_1_sistema_cientifico.png"),
            "theme_color": (255, 200, 80),
            "phonetic_script": (
                "¿Sabías que la materia es solo la capa más externa de la realidad? El Doctor Pang Ming explicó que todo "
                "existe en tres capas: materia, energía e información. La medicina convencional trabaja principalmente en la materia. "
                "Chineng Chikung trabaja desde la capa de la información. Cuando cambias la información en tu mente y tu campo, "
                "el Chi se reorganiza y la materia en tus células se transforma naturalmente. Transforma tu información y transformarás tu cuerpo."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì", "Doctor Pang Ming": "Doctor Páng Míng"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep2_1_sistema_cientifico.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 40, "dur": 6},
                {"stock": ai_clips_dir / "ep2_3_mente_guia_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 140, "dur": 6},
                {"stock": ai_clips_dir / "ep2_4_salud_bienestar.mp4"}
            ]
        },
        {
            "num": "06",
            "day": "MARTES",
            "title": "La Mente Guía al Qì (Yì Niàn)",
            "output_name": "06_La_Mente_Guia_al_Qi.mp4",
            "base_name": "ep06_la_mente_guia_al_qi",
            "badge": "TEORÍA HUNYUAN • EP. 06",
            "title_lines": ["LA MENTE GUÍA AL QI", "(Yì Niàn - 意念)"],
            "subtitle": "Donde va la Atención, Fluye la Energía",
            "src_img": str(ai_img_dir / "ep2_3_mente_guia_qi.png"),
            "theme_color": (160, 100, 255),
            "phonetic_script": (
                "Donde va tu atención, va tu energía. En Chineng Chikung este principio se llama Yinian: la mente dirige al Chi. "
                "Si tu mente está dispersa en el estrés y la preocupación, tu energía vital se fuga. Pero cuando enfocas tu intencion "
                "con serenidad dentro del cuerpo, el Chi sigue a la mente y regenera cada tejido. Aprende a usar la fuerza de tu intención "
                "para sanar y revitalizar tu vida todos los días."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì", "Yinian": "Yìniàn"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep2_3_mente_guia_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 180, "dur": 6},
                {"stock": ai_clips_dir / "ep1_3_mente_claridad.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 230, "dur": 6},
                {"stock": ai_clips_dir / "ep2_2_integracion_mente_cuerpo.mp4"}
            ]
        },
        # MIÉRCOLES
        {
            "num": "07",
            "day": "MIÉRCOLES",
            "title": "El Hospital Sin Medicinas",
            "output_name": "07_El_Hospital_Sin_Medicinas.mp4",
            "base_name": "ep07_el_hospital_sin_medicinas",
            "badge": "EVIDENCIA HUAXIA • EP. 07",
            "title_lines": ["EL HOSPITAL", "SIN MEDICINAS", "(Centro Huaxia)"],
            "subtitle": "El Experimento Médico Más Grande",
            "src_img": str(ai_img_dir / "ep2_1_sistema_cientifico.png"),
            "theme_color": (255, 200, 80),
            "phonetic_script": (
                "¿Imaginas un hospital de cuatro mil personas sin farmacia ni medicamentos? En China existió el Centro Huaxia, "
                "fundado por el Doctor Pang Ming. Durante más de una década, médicos y practicantes demostraron que el cuerpo "
                "puede autorregularse sin fármacos mediante la práctica intensiva de Chineng Chikung. Con una tasa de efectividad médica "
                "del noventa y cinco por ciento en más de ciento ochenta enfermedades, Huaxia demostró el potencial ilimitado del ser humano."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì", "Doctor Pang Ming": "Doctor Páng Míng"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep2_1_sistema_cientifico.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 50, "dur": 6},
                {"stock": ai_clips_dir / "ep2_4_salud_bienestar.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 130, "dur": 6},
                {"stock": ai_clips_dir / "ep1_4_cultivo_autonomo.mp4"}
            ]
        },
        {
            "num": "08",
            "day": "MIÉRCOLES",
            "title": "Estudiante vs Paciente",
            "output_name": "08_Estudiante_vs_Paciente.mp4",
            "base_name": "ep08_estudiante_vs_paciente",
            "badge": "EVIDENCIA HUAXIA • EP. 08",
            "title_lines": ["ESTUDIANTE", "VS PACIENTE"],
            "subtitle": "De la Dependencia a la Autonomía",
            "src_img": str(ai_img_dir / "ep1_4_cultivo_autonomo.png"),
            "theme_color": (0, 225, 255),
            "phonetic_script": (
                "En el hospital de Huaxia no existían pacientes, solo estudiantes. ¿Por qué? Porque un paciente espera "
                "que alguien externo lo cure de forma pasiva. Un estudiante, en cambio, aprende un arte de vida para cultivar "
                "su propia salud. En Sembradores de Chi no buscamos que dependas de un maestro o de un terapeuta, "
                "sino que te conviertas en el maestro de tu propia salud y vitalidad."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì", "Sembradores de Chi": "Sembradores de Qì"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep1_4_cultivo_autonomo.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 70, "dur": 6},
                {"stock": ai_clips_dir / "ep1_5_transformacion_diaria.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 210, "dur": 6},
                {"stock": ai_clips_dir / "ep2_4_salud_bienestar.mp4"}
            ]
        },
        {
            "num": "09",
            "day": "MIÉRCOLES",
            "title": "Evidencia de Sanación (101 Milagros)",
            "output_name": "09_Evidencia_de_Sanacion_101_Milagros.mp4",
            "base_name": "ep09_evidencia_sanacion",
            "badge": "EVIDENCIA HUAXIA • EP. 09",
            "title_lines": ["EVIDENCIA DE SANACIÓN", "101 Milagros Naturales"],
            "subtitle": "Disolución de Tumores en Ultrasonido",
            "src_img": str(ai_img_dir / "ep1_2_organos_vitalidad.png"),
            "theme_color": (160, 100, 255),
            "phonetic_script": (
                "En el libro Ciento un Milagros de Sanación Natural, se documentan casos sorprendentes de personas recuperadas "
                "de cáncer, artritis, lupus y parálisis. Científicos y médicos occidentales filmaron la disolución de tumores "
                "en tiempo real en monitores de ultrasonido mientras los maestros organizaban el campo de Chi. "
                "La sanación no es magia; es la ciencia del Chi y la intención pura en acción."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì", "Ciento un Milagros": "101 Milagros"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep1_2_organos_vitalidad.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 100, "dur": 6},
                {"stock": ai_clips_dir / "sample_qi_flow.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 250, "dur": 6},
                {"stock": ai_clips_dir / "ep2_1_sistema_cientifico.mp4"}
            ]
        },
        # JUEVES
        {
            "num": "10",
            "day": "JUEVES",
            "title": "Levantar el Qì y Verterlo por la Cabeza",
            "output_name": "10_Levantar_el_Qi_Peng_Qi_Guan_Ding_Fa.mp4",
            "base_name": "ep10_peng_qi_guan_ding_fa",
            "badge": "MÉTODOS Y PRÁCTICA • EP. 10",
            "title_lines": ["PĚNG QÌ GUÀN DǏNG FǍ", "(捧气贯顶法)"],
            "subtitle": "Intercambio Directo con la Naturaleza",
            "src_img": str(ai_img_dir / "ep1_1_que_es_el_qi.png"),
            "theme_color": (0, 225, 255),
            "phonetic_script": (
                "Peng Chi Guan Ding Fa, o Levantar el Chi y Verterlo por la Cabeza, es el método fundamental del primer nivel "
                "de Chineng Chikung. A través de movimientos suaves y apertura mental, abrimos los poros y canales del cuerpo "
                "para liberar el Chi turbio e integrar el Hunyuan Chi puro de la naturaleza. Es el ejercicio practicado por millones "
                "de personas para restaurar la salud y la vitalidad diaria."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Peng Chi Guan Ding Fa": "Pěng Qì Guàn Dǐng Fǎ", "Chi": "Qì"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep1_1_que_es_el_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 30, "dur": 6},
                {"stock": ai_clips_dir / "ep1_5_transformacion_diaria.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 160, "dur": 6},
                {"stock": ai_clips_dir / "sample_qi_flow.mp4"}
            ]
        },
        {
            "num": "11",
            "day": "JUEVES",
            "title": "Sentadillas frente a la Pared (Dūn Qiáng Gōng)",
            "output_name": "11_Sentadillas_Pared_Dun_Qiang_Gong.mp4",
            "base_name": "ep11_dun_qiang_gong",
            "badge": "MÉTODOS Y PRÁCTICA • EP. 11",
            "title_lines": ["DŪN QIÁNG GŌNG", "(蹲墙功)"],
            "subtitle": "Flexibilidad de Columna y Desbloqueo",
            "src_img": str(ai_img_dir / "ep2_2_integracion_mente_cuerpo.png"),
            "theme_color": (255, 200, 80),
            "phonetic_script": (
                "Dun Qiang Gong, o las sentadillas frente a la pared, es conocido como el método atajo en Chineng Chikung. "
                "Al deslizar el cuerpo frente a una pared recta, se flexiona toda la columna vertebral, flexibilizando la cintura "
                "y abriendo la puerta de Mingmen. Este método desbloquea rápidamente la energía en la espalda, fortalece los riñones "
                "y revitaliza todo tu cuerpo en pocos minutos."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Dun Qiang Gong": "Dūn Qiáng Gōng", "Mingmen": "Mìngmén"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep2_2_integracion_mente_cuerpo.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 90, "dur": 6},
                {"stock": ai_clips_dir / "ep1_2_organos_vitalidad.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 190, "dur": 6},
                {"stock": ai_clips_dir / "ep2_4_salud_bienestar.mp4"}
            ]
        },
        {
            "num": "12",
            "day": "JUEVES",
            "title": "El Estado de Mingjue (Míngjué Gōngfu)",
            "output_name": "12_El_Estado_de_Mingjue.mp4",
            "base_name": "ep12_el_estado_de_mingjue",
            "badge": "MÉTODOS Y PRÁCTICA • EP. 12",
            "title_lines": ["EL ESTADO DE MINGJUE", "(Míngjué Gōngfu - 明觉)"],
            "subtitle": "Conciencia Pura y Observador Interno",
            "src_img": str(ai_img_dir / "ep2_3_mente_guia_qi.png"),
            "theme_color": (160, 100, 255),
            "phonetic_script": (
                "Mingjue es el estado de la conciencia que se observa a sí misma con absoluta pureza y serenidad. "
                "Cuando entras en el estado de Mingjue, la mente trasciende las emociones negativas y los apego del ego, "
                "convirtiéndose en un espejo claro. Desde este estado de conciencia pura, la sanación y la transformación "
                "ocurren de forma instantánea y sin esfuerzo."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Mingjue": "Míngjué"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep2_3_mente_guia_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 210, "dur": 6},
                {"stock": ai_clips_dir / "ep1_3_mente_claridad.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 270, "dur": 6},
                {"stock": ai_clips_dir / "ep2_1_sistema_cientifico.mp4"}
            ]
        },
        # VIERNES
        {
            "num": "13",
            "day": "VIERNES",
            "title": "Los 8 Versos del Campo de Qì",
            "output_name": "13_Los_8_Versos_del_Campo_de_Qi.mp4",
            "base_name": "ep13_los_8_versos",
            "badge": "TRASCENDENCIA • EP. 13",
            "title_lines": ["LOS 8 VERSOS", "Organización del Campo de Qì"],
            "subtitle": "Armonía Cósmica en 8 Frases",
            "src_img": str(ai_img_dir / "ep2_1_sistema_cientifico.png"),
            "theme_color": (255, 200, 80),
            "phonetic_script": (
                "La cabeza toca el cielo, los pies firmes en la tierra. El cuerpo se relaja y la mente se expande. "
                "Los ocho versos creados por el Doctor Pang Ming son la clave para organizar el campo de Chi perfecto "
                "antes de cada práctica. Al recitar o contemplar estos ocho versos, la mente entra en profunda serenidad "
                "y se conecta de inmediato con la inmensidad del universo."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì", "Doctor Pang Ming": "Doctor Páng Míng"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep2_1_sistema_cientifico.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 10, "dur": 6},
                {"stock": ai_clips_dir / "ep2_3_mente_guia_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 120, "dur": 6},
                {"stock": ai_clips_dir / "sample_qi_flow.mp4"}
            ]
        },
        {
            "num": "14",
            "day": "VIERNES",
            "title": "Cultivo de la Salud y Longevidad",
            "output_name": "14_Cultivo_Salud_Longevidad.mp4",
            "base_name": "ep14_salud_longevidad",
            "badge": "TRASCENDENCIA • EP. 14",
            "title_lines": ["CULTIVO DE LA SALUD", "Y LONGEVIDAD"],
            "subtitle": "Prevención, Vigor y Vitalidad Diaria",
            "src_img": str(ai_img_dir / "ep2_4_salud_bienestar.png"),
            "theme_color": (0, 225, 255),
            "phonetic_script": (
                "La verdadera medicina es la prevención. Chineng Chikung no solo sirve para recuperarse de enfermedades, "
                "sino para elevar la calidad de vida, fortalecer el sistema inmune y cultivar una longevidad plena y activa. "
                "Al integrar la práctica diaria en tu rutina, mantienes tus órganos nutridos y tu mente joven y serena "
                "sin importar tu edad."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep2_4_salud_bienestar.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 60, "dur": 6},
                {"stock": ai_clips_dir / "ep1_2_organos_vitalidad.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 150, "dur": 6},
                {"stock": ai_clips_dir / "ep1_5_transformacion_diaria.mp4"}
            ]
        },
        {
            "num": "15",
            "day": "VIERNES",
            "title": "Práctica Autónoma y Comunidad",
            "output_name": "15_Practica_Autonoma_Comunidad.mp4",
            "base_name": "ep15_practica_autonoma",
            "badge": "TRASCENDENCIA • EP. 15",
            "title_lines": ["PRÁCTICA AUTÓNOMA", "Sembradores de Qì"],
            "subtitle": "Transforma tu Vida Todos los Días",
            "src_img": str(ai_img_dir / "ep1_5_transformacion_diaria.png"),
            "theme_color": (160, 100, 255),
            "phonetic_script": (
                "El mayor regalo de Chineng Chikung es la libertad. Aprender a cultivar tu propio Chi te devuelve el poder "
                "de cuidar de ti y de tus seres queridos. En Sembradores de Chi te invitamos a formar parte de nuestra comunidad, "
                "compartiendo sesiones, el campo de Chi y el conocimiento para que juntos sembremos salud y conciencia en el mundo. "
                "Únete a nosotros y comienza tu práctica hoy mismo."
            ),
            "replacements": {"Chineng Chikung": "Zhìnéng Qìgōng", "Chi": "Qì", "Sembradores de Chi": "Sembradores de Qì"},
            "clips_config": [
                {"stock": ai_clips_dir / "ep1_5_transformacion_diaria.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 200, "dur": 6},
                {"stock": ai_clips_dir / "ep1_4_cultivo_autonomo.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 280, "dur": 6},
                {"stock": ai_clips_dir / "ep2_4_salud_bienestar.mp4"}
            ]
        }
    ]

    voice_name = "es-MX-JorgeNeural-Male"

    for idx_ep, ep in enumerate(episodes, start=1):
        final_dest = output_dir / ep["output_name"]
        
        logger.info(f"\n========================================================")
        logger.info(f"PROCESANDO VIDEO {idx_ep}/15 ({ep['day']}): {ep['title']}")
        logger.info(f"========================================================")

        ep_materials = []
        for c_idx, item in enumerate(ep["clips_config"], start=1):
            if "raw" in item and os.path.exists(item["raw"]):
                clip_out = str(cache_dir / f"ep{idx_ep}_subclip{c_idx}.mp4")
                extract_and_normalize_subclip(str(item["raw"]), item["start"], item["dur"], clip_out)
                ep_materials.append(clip_out)
            elif "stock" in item and os.path.exists(item["stock"]):
                ep_materials.append(str(item["stock"]))

        task_id = str(uuid.uuid4())
        task_dir = CURRENT_DIR / "storage" / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        audio_path = str(task_dir / "audio.mp3")
        subtitle_path = str(task_dir / "subtitle.srt")

        sub_maker = voice.tts(
            text=ep["phonetic_script"],
            voice_name=voice_name,
            voice_rate=1.0,
            voice_file=audio_path,
            voice_volume=1.0
        )
        if sub_maker:
            voice.create_subtitle(sub_maker=sub_maker, text=ep["phonetic_script"], subtitle_file=subtitle_path)

        add_audio_tail_padding(audio_path, padding_seconds=1.0)

        if os.path.exists(subtitle_path):
            with open(subtitle_path, "r", encoding="utf-8") as f:
                srt_content = f.read()

            sorted_replacements = sorted(ep.get("replacements", {}).items(), key=lambda x: len(x[0]), reverse=True)
            for orig, repl in sorted_replacements:
                pattern = r'\b' + re.escape(orig) + r'\b'
                srt_content = re.sub(pattern, repl, srt_content, flags=re.IGNORECASE)

            # Salvaguardas adicionales
            srt_content = re.sub(r'\bQì?neng\s+Qì?kung\b', 'ZhiNeng QiGong', srt_content, flags=re.IGNORECASE)
            srt_content = re.sub(r'\bQìna\b', 'China', srt_content)
            srt_content = re.sub(r'\bqìna\b', 'china', srt_content)

            with open(subtitle_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

        video_params = VideoParams(
            video_subject=ep["title"],
            video_script=ep["phonetic_script"],
            video_source="local",
            video_materials=[{"url": m} for m in ep_materials],
            video_concat_mode=VideoConcatMode.sequential,
            video_transition_mode=VideoTransitionMode.shuffle,
            video_clip_duration=7,
            video_aspect=VideoAspect.portrait,
            voice_name=voice_name,
            subtitle_enabled=True,
            subtitle_position="custom",
            custom_position=58.0,
            font_name="BeVietnamPro-Bold.ttf" if os.path.exists(FONT_BOLD) else "MicrosoftYaHeiBold.ttc",
            text_fore_color="#FFFFFF",
            stroke_color="#000000",
            stroke_width=3,
            text_background_color="#000000",
            rounded_subtitle_background=True
        )

        audio_duration = voice.get_audio_duration(audio_path)
        video_paths, combined_paths, warnings = task_service.generate_final_videos(
            task_id=task_id,
            params=video_params,
            downloaded_videos=ep_materials,
            audio_file=audio_path,
            subtitle_path=subtitle_path,
            audio_duration=audio_duration
        )

        if video_paths and os.path.exists(video_paths[0]):
            shutil.copy(video_paths[0], final_dest)
            logger.success(f"✅ Video {idx_ep}/15 ({ep['title']}) guardado en: {final_dest}")
        else:
            logger.error(f"❌ Falló el renderizado del video {ep['title']}")

        generate_ig_covers(ep, str(ig_covers_dir))
        logger.info(f"Portadas e imágenes de Instagram generadas para Ep. {ep['num']}")

    logger.success(f"\n🎉 ¡SERIE DE 15 VIDEOS Y PORTADAS GENERADA AUTÓNOMAMENTE CON ÉXITO EN {output_dir}! 🎉")

if __name__ == "__main__":
    generate_serie_15_full()

