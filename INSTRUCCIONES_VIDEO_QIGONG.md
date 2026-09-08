# Bitácora y Guía de Proyecto: Video ZhiNeng QiGong (Primer Verso)

**Fecha:** 2026-09-03  
**Proyecto:** MoneyPrinter Turbo - Creación de Video para Redes (Shorts / Reels / TikTok)  
**Estrategia de Lanzamiento:** 
- **Fase 1 (Inmediata):** Trilogía Fundacional Desmitificada (*Video 1: ¿Qué es el Qì?* | *Video 2: ¿Qué es ZNQG?* | *Video 3: El Campo de Qì*).
- **Fase 2:** La Saga de los 8 Versos de Organización del Campo (iniciando con *Dǐng tiān lì dì*).
**Referencia Bibliográfica:** *El Zhìnéng Qìgōng y la lengua china: El caso de los ocho versos que organizan el campo de Qì*, Fátima Fernández Christlieb (2019), pág. 39-42.
**Estrategia Operativa:** [`D:/Dropbox/Ai/SembradoresDeQi/Documentos/Marketing/ESTRATEGIA_OPERATIVA_SEMBRADORES_2026.md`](file:///D:/Dropbox/Ai/SembradoresDeQi/Documentos/Marketing/ESTRATEGIA_OPERATIVA_SEMBRADORES_2026.md)

---

## 1. Materiales de Video (Combinación Híbrida 9:16)

Los materiales ya están preparados, normalizados a resolución vertical (1080x1920) y organizados en:
📂 `storage/local_videos/`

1. `01_qigong_cielo.mp4` – Video propio del usuario en el dojo (apertura de brazos / postura erguida).
2. `02_pexels_cielo.mp4` – Stock Pexels: Timelapse de cielo abierto con nubes en movimiento.
3. `03_qigong_tierra.mp4` – Video propio del usuario: Flexión hacia la tierra (conectando canales).
4. `04_pexels_tierra.mp4` – Stock Pexels: Paisaje de montañas, niebla y naturaleza fértil.
5. `05_qigong_armonia.mp4` – Video propio del usuario: Palmas unidas en el pecho en meditación profunda (He Shi).
6. `06_pexels_cosmos.mp4` – Stock Pexels: Cosmos, nebulosa y polvo estelar en movimiento.

*Video fuente completo original:* `storage/local_videos/personales/VID_20260628_144710.mp4` (~5 minutos de práctica).

---

## 2. Textos: Locución vs. Subtítulos Visuales

Para que la voz en español de México (**es-MX-JorgeNeural**) pronuncie los términos chinos con exactitud para la comunidad practicante, se separa el texto de lectura del texto visual.

### A. Texto de Locución Fonética (Lo que lee el TTS)
> "El primer verso para organizar el campo de Chi en Chineng Chikung es Ding Tian Li Di. Literalmente significa: En Bai Jui sostengo el cielo y estoy de pie en la tierra. Al pronunciarlo, visualizamos que nos ponemos de pie sobre la tierra y sentimos que nuestra cabeza toca el inmenso cielo. Nos convertimos en un canal. Estamos entre el cielo y la tierra, somos como el cable infinito que los une en perfecta armonía. El Chi, la energía primordial del universo, fluye y está presente en los tres: en el cielo infinito, en la profundidad de la tierra y dentro de nosotros mismos. Así comenzamos a fusionarnos con el universo."

### B. Texto de Subtítulos en Pantalla (Ortografía editorial formal con caracteres Pinyin)
> "El primer verso para organizar el campo de Qì en Zhìnéng Qìgōng es 'Dǐng tiān lì dì'. Literalmente significa: 'En Bâi Huì sostengo el cielo y estoy de pie en la tierra'. Al pronunciarlo, visualizamos que nos ponemos de pie sobre la tierra y sentimos que nuestra cabeza toca el inmenso cielo. Nos convertimos en un canal. Estamos entre el cielo y la tierra, somos como el cable infinito que los une en perfecta armonía. El Qì, la energía primordial del universo, fluye y está presente en los tres: en el cielo infinito, en la profundidad de la tierra y dentro de nosotros mismos. Así comenzamos a fusionarnos con el universo."

---

## 3. Configuración Técnica

* **Fuente de video:** `local`
* **Lista de materiales ordenados:** `01_qigong_cielo.mp4,02_pexels_cielo.mp4,03_qigong_tierra.mp4,04_pexels_tierra.mp4,05_qigong_armonia.mp4,06_pexels_cosmos.mp4`
* **Modo de concatenación:** `sequential` (ensamblado cronológico)
* **Duración por clip:** `7` segundos
* **Voz:** `es-MX-JorgeNeural-Male` (o `es-MX-JorgeNeural`)
* **Tipografía:** `BeVietnamPro-Bold.ttf`
* **Música de fondo:** Suave ambiental (volumen 0.2)

---

## 4. Pasos para Retomar Mañana

1. Regenerar el audio (`audio.mp3`) con el guion fonético para corregir la pronunciación de:
   * *Zhineng Qigong* $\rightarrow$ *Chineng Chikung*
   * *Qì* $\rightarrow$ *Chi*
   * *Bâi Huì* $\rightarrow$ *Bai Jui*
2. Ajustar los subtítulos `.srt` para que visualmente mantengan la ortografía con pinyin tradicional (*Qì*, *Zhìnéng Qìgōng*, *Bâi Huì*).
3. Ensamblar la versión final con la combinación de video ya preparada.
