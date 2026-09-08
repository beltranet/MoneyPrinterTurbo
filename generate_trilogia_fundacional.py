#!/usr/bin/env python3
import os
import sys
import uuid
import shutil
from pathlib import Path
import subprocess
import imageio_ffmpeg

# Add MoneyPrinter project directory to sys.path
CURRENT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(CURRENT_DIR))

from loguru import logger
from app.models.schema import VideoParams, VideoAspect, VideoConcatMode, VideoTransitionMode
from app.services import voice, video as video_service, material as material_service, task as task_service

def add_audio_tail_padding(audio_path: str, padding_seconds: float = 1.0):
    """Agrega un silencio suave al final del audio mediante FFmpeg para evitar cortes abruptos."""
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
        logger.info(f"Agregado silencio final de {padding_seconds}s a {audio_path}")

def extract_and_normalize_subclip(raw_video_path: str, start_sec: int, duration_sec: int, output_path: str):
    """Extrae y normaliza un subclip vertical 1080x1920 desde un video en bruto."""
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
    logger.info(f"Subclip extraído: {os.path.basename(output_path)} ({start_sec}s -> {start_sec + duration_sec}s)")

def generate_trilogia_series():
    output_dir = CURRENT_DIR / "storage" / "trilogia_fundacional"
    output_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = CURRENT_DIR / "storage" / "cache_videos" / "trilogia_subclips"
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"=== INICIANDO GENERACIÓN BATCH DIVERSIFICADA: TRILOGÍA FUNDACIONAL ===")
    logger.info(f"Carpeta de Salida: {output_dir}")

    personales_dir = CURRENT_DIR / "storage" / "local_videos" / "personales"
    ai_clips_dir = CURRENT_DIR / "storage" / "local_videos" / "ai_generated" / "clips"

    # Definición de los 3 Episodios combinando Insumos IA y Video Real del Dojo VID_20260628_144710.mp4
    episodes = [
        {
            "id": "01_Que_es_el_Qi",
            "title": "¿Qué es el Qì?",
            "output_name": "01_Que_es_el_Qi.mp4",
            "phonetic_script": (
                "¿Qué es realmente el Chi? Lejos de conceptos místicos o esotéricos, en Chineng Chikung entendemos el Chi "
                "como la sustancia y la información fundamental que compone todo en el universo. Es la energía vital "
                "que nutre tus órganos, regula tu sistema nervioso y sostiene tu vitalidad diaria. Cuando el Chi fluye libremente "
                "y es abundante, el cuerpo se autorregula y la mente experimenta claridad y paz. En Sembradores de Chi, "
                "te enseñamos a cultivar y gestionar tu propia energía con autonomía y sin depender de nadie. "
                "Síguenos para aprender a sentir y transformar tu Chi día a día."
            ),
            "replacements": {
                "Chineng Chikung": "Zhìnéng Qìgōng",
                "Chi": "Qì",
                "Sembradores de Chi": "Sembradores de Qì"
            },
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
            "id": "02_Que_es_Zhineng_Qigong",
            "title": "¿Qué es Zhìnéng Qìgōng?",
            "output_name": "02_Que_es_Zhineng_Qigong.mp4",
            "phonetic_script": (
                "¿Qué hace diferente a Chineng Chikung de otras disciplinas? Creado por el Doctor Pang Ming, "
                "Chineng Chikung es un sistema científico de medicina energética y desarrollo de la conciencia. "
                "No se trata solo de movimientos físicos, sino de la integración pura entre mente, cuerpo y Chi. "
                "A través de métodos sencillos y profundos, entrenamos a la mente para guiar la energía a donde el cuerpo más lo necesita. "
                "Es una herramienta de transformación personal que te devuelve el control de tu salud y bienestar. "
                "Descubre el poder de cultivar tu vida con Chineng Chikung."
            ),
            "replacements": {
                "Chineng Chikung": "Zhìnéng Qìgōng",
                "Chi": "Qì",
                "Doctor Pang Ming": "Doctor Páng Míng"
            },
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
            "id": "03_El_Campo_de_Qi_Qi_Chang",
            "title": "El Campo de Qì (Qì Chǎng)",
            "output_name": "03_El_Campo_de_Qi_Qi_Chang.mp4",
            "phonetic_script": (
                "¿Has sentido alguna vez la fuerza de entrenar o meditar en grupo? En Chineng Chikung esto se conoce como Chi Chang, "
                "o el Campo de Chi. Un Chi Chang es un espacio donde la intención y la energía de muchas personas se sincronizan "
                "para crear una resonancia colectiva de sanación y armonía. Cuando te conectas al campo, tu práctica se vuelve "
                "diez veces más profunda y efectiva que al practicar en soledad. En Sembradores de Chi organizamos el campo en cada sesión "
                "para acompañarte en tu proceso. Únete a nuestra comunidad y siente la fuerza del campo de Chi."
            ),
            "replacements": {
                "Chineng Chikung": "Zhìnéng Qìgōng",
                "Chi Chang": "Qì Chǎng",
                "Chi": "Qì",
                "Sembradores de Chi": "Sembradores de Qì"
            },
            "clips_config": [
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 220, "dur": 6},
                {"stock": ai_clips_dir / "sample_qi_flow.mp4"},
                {"stock": ai_clips_dir / "ep2_3_mente_guia_qi.mp4"},
                {"raw": personales_dir / "VID_20260628_144710.mp4", "start": 260, "dur": 6},
                {"stock": ai_clips_dir / "ep1_5_transformacion_diaria.mp4"}
            ]
        }
    ]

    voice_name = "es-MX-JorgeNeural-Male"

    for ep_index, ep in enumerate(episodes, start=1):
        final_dest = output_dir / ep["output_name"]

        task_id = str(uuid.uuid4())
        task_dir = CURRENT_DIR / "storage" / "tasks" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"\n========================================================")
        logger.info(f"PROCESANDO VIDEO DIVERSIFICADO {ep_index}/3: {ep['title']}")
        logger.info(f"Task ID: {task_id}")
        logger.info(f"========================================================")

        # 1. Procesar y Preparar los Clips Visuales Únicos
        ep_materials = []
        for idx, item in enumerate(ep["clips_config"], start=1):
            if "raw" in item and os.path.exists(item["raw"]):
                clip_out = str(cache_dir / f"ep{ep_index}_clip{idx}.mp4")
                extract_and_normalize_subclip(str(item["raw"]), item["start"], item["dur"], clip_out)
                ep_materials.append(clip_out)
            elif "stock" in item and os.path.exists(item["stock"]):
                ep_materials.append(str(item["stock"]))

        logger.info(f"Materiales exclusivos preparados para Video {ep_index}: {len(ep_materials)} clips.")

        audio_path = str(task_dir / "audio.mp3")
        subtitle_path = str(task_dir / "subtitle.srt")

        # 2. Generar Audio TTS Fonético
        logger.info(f"Generando audio TTS fonético ({voice_name})...")
        sub_maker = voice.tts(
            text=ep["phonetic_script"],
            voice_name=voice_name,
            voice_rate=1.0,
            voice_file=audio_path,
            voice_volume=1.0,
        )
        if sub_maker:
            voice.create_subtitle(sub_maker=sub_maker, text=ep["phonetic_script"], subtitle_file=subtitle_path)

        # 3. Agregar Silencio de Cierre (Padding de 1.0s para evitar final abrupto)
        add_audio_tail_padding(audio_path, padding_seconds=1.0)

        # 4. Formatear Subtítulos .srt con Ortografía y Pinyin Formal
        if os.path.exists(subtitle_path):
            with open(subtitle_path, "r", encoding="utf-8") as f:
                srt_content = f.read()
            
            for orig, repl in ep["replacements"].items():
                srt_content = srt_content.replace(orig, repl)
            
            with open(subtitle_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            logger.info("Subtítulos actualizados con Pinyin formal y acentos.")

        # 5. Parámetros de Video (Transición Shuffle + Subtítulos de Alto Contraste con Fondo Oscuro Redondeado)
        video_params = VideoParams(
            video_subject=ep["title"],
            video_script=ep["phonetic_script"],
            video_source="local",
            video_materials=[{"url": m} for m in ep_materials],
            video_concat_mode=VideoConcatMode.sequential,
            video_transition_mode=VideoTransitionMode.shuffle, # Transiciones variadas
            video_clip_duration=7,
            video_aspect=VideoAspect.portrait,
            voice_name=voice_name,
            subtitle_enabled=True,
            subtitle_position="custom",
            custom_position=58.0,
            font_name="BeVietnamPro-Bold.ttf" if os.path.exists(CURRENT_DIR / "resource" / "fonts" / "BeVietnamPro-Bold.ttf") else "MicrosoftYaHeiBold.ttc",
            text_fore_color="#FFFFFF",
            stroke_color="#000000",
            stroke_width=3,
            text_background_color="#000000",
            rounded_subtitle_background=True
        )

        audio_duration = voice.get_audio_duration(audio_path)
        logger.info(f"Renderizando video final {ep_index}/3 (Duración audio: {audio_duration:.2f}s)...")

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
            logger.success(f"✅ Video {ep_index}/3 DIVERSIFICADO guardado en: {final_dest}")
        else:
            logger.error(f"❌ Falló el renderizado del video {ep['title']}")

    logger.success(f"\n🎉 ¡TRILOGÍA FUNDACIONAL DIVERSIFICADA GENERADA CON ÉXITO EN {output_dir}! 🎉")

if __name__ == "__main__":
    generate_trilogia_series()
