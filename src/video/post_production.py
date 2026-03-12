# -*- coding: utf-8 -*-
"""
後製階段：TTS 配音 + 字幕疊加
- 從腳本解析【口播文案】與秒數
- 使用 edge-tts 生成配音
- 用 moviepy 疊加標準清晰字幕（白字黑邊，第二張截圖風格）
"""

import re
import asyncio
from pathlib import Path
from typing import Optional

# 標準字幕樣式：宋體 SimSun，白字黑邊、清晰易讀、用戶看得明白
# Windows: SimSun；Linux: Noto Serif CJK SC 或 simsun.ttf
SUBTITLE_FONT = "SimSun"
SUBTITLE_FONT_SIZE = 36
SUBTITLE_COLOR = "white"
SUBTITLE_STROKE_COLOR = "black"
SUBTITLE_STROKE_WIDTH = 2


def _parse_script_segments(script: str) -> list[tuple[float, float, str]]:
    """
    從腳本解析時段與口播文案。
    支持格式：**0-3秒** 【口播文案】"xxx" 或 **0:00–0:03** 【口播文案】xxx
    返回 [(start_sec, end_sec, text), ...]
    """
    segments = []
    # 按 **X-Y秒** 或 **X:XX–Y:YY** 分割區塊
    block_pattern = re.compile(r"\*\*(\d+)[-–:](\d+)(?:[-–:](\d+))?(?:[-–:](\d+))?\s*[秒s]?\*\*\s*(.*?)(?=\*\*\d|$)", re.DOTALL)
    for m in block_pattern.finditer(script):
        g = m.groups()
        if g[2] is None:
            start_sec = float(g[0])
            end_sec = float(g[1])
        else:
            start_sec = float(g[0]) * 60 + float(g[1])
            end_sec = float(g[2]) * 60 + float(g[3])
        block = g[4]

        voice_m = re.search(r"【口播文案?】\s*(?:[（(][^）)]*[）)])?\s*[""]?([^""\n]+?)[""]?\s*(?=【|\n\n|$)", block, re.DOTALL)
        if voice_m:
            text = voice_m.group(1).strip().strip('"\'')
            if text and len(text) > 2:
                segments.append((start_sec, end_sec, text))

    # 若解析失敗，按字數均分到 20–30 秒
    if not segments:
        clean = re.sub(r"\*\*[\d\-–:秒s]+\*\*|【[^】]+】", " ", script)
        clean = re.sub(r"\s+", " ", clean).strip()
        if clean and len(clean) > 10:
            total_chars = len(clean)
            duration = min(30, max(20, total_chars // 25))
            chunk = max(40, total_chars // 5)
            for i in range(0, total_chars, chunk):
                seg_text = clean[i : i + chunk]
                if seg_text.strip():
                    t0 = (i / total_chars) * duration
                    t1 = min(duration, ((i + chunk) / total_chars) * duration)
                    segments.append((t0, t1, seg_text.strip()))

    return segments


def _tts_generate(text: str, output_path: Path, voice: str = "zh-CN-XiaoxiaoNeural") -> bool:
    """使用 edge-tts 生成語音，保存為 mp3"""
    try:
        import edge_tts
    except ImportError:
        return False

    async def _run():
        com = edge_tts.Communicate(text, voice)
        await com.save(str(output_path))

    asyncio.run(_run())
    return output_path.exists()


def _add_subtitles_to_video(
    video_path: Path,
    output_path: Path,
    segments: list[tuple[float, float, str]],
) -> bool:
    """疊加字幕到視頻：白字黑邊，標準清晰"""
    try:
        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    except ImportError:
        return False

    clips = []
    try:
        video = VideoFileClip(str(video_path))
        for start, end, text in segments:
            if not text or end <= start:
                continue
            duration = min(end - start, 5.0)
            try:
                txt_clip = TextClip(
                    text,
                    font=SUBTITLE_FONT,
                    font_size=SUBTITLE_FONT_SIZE,
                    color=SUBTITLE_COLOR,
                    stroke_color=SUBTITLE_STROKE_COLOR,
                    stroke_width=SUBTITLE_STROKE_WIDTH,
                    method="caption",
                    size=(video.w - 80, None),
                )
                txt_clip = txt_clip.with_duration(duration).with_start(start)
                txt_clip = txt_clip.with_position(("center", "bottom"))
                clips.append(txt_clip)
            except Exception:
                pass
        if clips:
            result = CompositeVideoClip([video] + clips)
            result.write_videofile(str(output_path), codec="libx264", audio_codec="aac", verbose=False, logger=None)
            result.close()
        else:
            video.write_videofile(str(output_path), codec="libx264", audio_codec="aac", verbose=False, logger=None)
        video.close()
        for c in clips:
            try:
                c.close()
            except Exception:
                pass
        return True
    except Exception:
        return False


def process_video(
    video_path: str | Path,
    script: str,
    output_path: str | Path,
    voice: str = "zh-CN-XiaoxiaoNeural",
    voice_gender: str = "female",
) -> Optional[str]:
    """
    後製流程：TTS 配音 + 字幕疊加。
    video_path: 原始視頻路徑
    script: 腳本全文
    output_path: 輸出路徑
    voice: edge-tts 音色，female 時用 XiaoxiaoNeural，male 時用 YunxiNeural
    返回輸出路徑或 None
    """
    video_path = Path(video_path)
    output_path = Path(output_path)
    if not video_path.exists():
        return None

    segments = _parse_script_segments(script)
    if not segments:
        return None

    full_text = " ".join(t[2] for t in segments)
    if voice_gender == "male":
        voice = "zh-CN-YunxiNeural"
    else:
        voice = "zh-CN-XiaoxiaoNeural"

    save_dir = output_path.parent
    save_dir.mkdir(parents=True, exist_ok=True)
    audio_path = save_dir / "_tts_temp.mp3"

    if not _tts_generate(full_text, audio_path, voice):
        return None

    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
    except ImportError:
        audio_path.unlink(missing_ok=True)
        return None

    try:
        video = VideoFileClip(str(video_path))
        audio = AudioFileClip(str(audio_path))
        video_no_audio = video.without_audio()
        final = video_no_audio.with_audio(audio)
        temp_with_audio = save_dir / "_temp_with_audio.mp4"
        final.write_videofile(str(temp_with_audio), codec="libx264", audio_codec="aac", verbose=False, logger=None)
        final.close()
        video.close()
        audio.close()
        audio_path.unlink(missing_ok=True)

        if _add_subtitles_to_video(temp_with_audio, output_path, segments):
            temp_with_audio.unlink(missing_ok=True)
            return str(output_path)
        temp_with_audio.rename(output_path)
        return str(output_path)
    except Exception:
        audio_path.unlink(missing_ok=True)
        return None
