# -*- coding: utf-8 -*-
"""
视频生成 - 使用 Kling API 将脚本生成营销/电商短视频
流程：创意中心 → 内容分析 → 传输至此 → Kling 文生视频 → 保存到本地
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
import streamlit as st

from config import VIDEO_SAVE_DIR
from src.video.kling_client import KlingClient, script_to_prompt, KLING_MAX_DURATION, WANXIANG_MAX_DURATION
from src.video.wanxiang_client import WanxiangClient
from src.video.wanxiang_prompts import (
    wanxiang_script_to_prompt,
    VIDEO_STYLES,
    FONT_STYLES,
    VOICE_STYLES,
    VOICE_GENDERS,
    WANXIANG_NEGATIVE_PROMPT,
)
from src.video.task_store import load_video_tasks, save_video_tasks
from src.video.post_production import process_video as run_post_production
from src.video.safety_precheck import precheck_and_sanitize_script


def _download_video(video_url: str, filepath: Path) -> bool:
    """下载视频到指定路径"""
    try:
        r = requests.get(video_url, timeout=60, stream=True)
        r.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception:
        return False


def _concatenate_videos(paths: list[str], out_path: Path) -> bool:
    """拼接多个视频为一条"""
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        clips = [VideoFileClip(p) for p in paths]
        final = concatenate_videoclips(clips)
        final.write_videofile(str(out_path), codec="libx264", audio_codec="aac", verbose=False, logger=None)
        for c in clips:
            c.close()
        final.close()
        return True
    except Exception:
        return False


def _download_and_save(video_url: str, title: str, task_id: str, segment_paths: list[str] | None = None) -> str | None:
    """下载视频并保存，支持多段拼接。返回本地路径或 None"""
    save_dir = Path(VIDEO_SAVE_DIR)
    save_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", (title or "video")[:80])
    if segment_paths and len(segment_paths) > 1:
        out_path = save_dir / f"{safe_name}_{task_id[:12]}_merged.mp4"
        if _concatenate_videos(segment_paths, out_path):
            for p in segment_paths:
                try:
                    Path(p).unlink(missing_ok=True)
                except Exception:
                    pass
            return str(out_path)
        return None
    filename = f"{safe_name}_{task_id[:12]}.mp4"
    filepath = save_dir / filename
    if _download_video(video_url, filepath):
        return str(filepath)
    return None

st.set_page_config(page_title="视频生成", page_icon="🎬", layout="wide")
st.title("🎬 视频生成")
st.caption("将脚本转为营销/电商短视频（竖屏 9:16），支持 Kling / 万象2.6")

# 初始化（F5 刷新时从磁盘恢复任务，不丢失进度）
if "pending_video" not in st.session_state:
    st.session_state["pending_video"] = []
if "kling_tasks" not in st.session_state:
    st.session_state["kling_tasks"] = load_video_tasks()

# 视频模型选择
VIDEO_MODELS = [
    ("万象 2.6（阿里百炼）", "wanxiang"),
    ("Kling（可灵）", "kling"),
]
kling_client = KlingClient()
wanxiang_client = WanxiangClient()
selected_label = st.selectbox(
    "视频生成模型",
    [m[0] for m in VIDEO_MODELS],
    key="video_model_select",
)
video_provider = next((m[1] for m in VIDEO_MODELS if m[0] == selected_label), "wanxiang")
client = wanxiang_client if video_provider == "wanxiang" else kling_client

if video_provider == "wanxiang" and not wanxiang_client.is_available():
    st.warning("请配置 `.env` 中的 `DASHSCOPE_API_KEY` 以使用万象 2.6")
elif video_provider == "kling" and not kling_client.is_available():
    st.warning("请配置 `.env`：`KLING_ACCESS_KEY` + `KLING_SECRET_KEY`。注册：https://klingapi.com")

st.subheader("待制作脚本")
pending = st.session_state.get("pending_video", [])

if not pending:
    st.info("暂无待制作脚本。请先在「创意中心」生成 → 「内容分析」分析编辑 → 点击「传输给视频生成」。")
else:
    for i, p in enumerate(pending):
        title = p.get("title", "(无标题)")[:50]
        with st.expander(f"📄 {title} | 行业: {p.get('industry', '-')}", expanded=True):
            st.write("**标题**", p.get("title", ""))
            st.write("**钩子**", p.get("hook", ""))
            script_full = p.get("script", "")
            st.caption(f"脚本全文（{len(script_full)} 字）— 完整用于 20-30 秒两段拼接，含 0-15s + 15-30s 全部内容")
            st.text_area("脚本", script_full, height=380, disabled=True, key=f"script_display_{i}", label_visibility="collapsed")
            col1, col2 = st.columns([1, 3])
            with col1:
                use_long = (video_provider == "wanxiang")
                if video_provider == "wanxiang":
                    st.caption("✅ 万象已强制启用 20-30 秒两段拼接（2×15秒）")
                video_style, font_style, voice_style, voice_gender = "modern_business", "songti", "professional", "female"
                if video_provider == "wanxiang":
                    video_style = st.selectbox(
                        "视频风格",
                        options=[row[1] for row in VIDEO_STYLES],
                        format_func=lambda x: next(r[0] for r in VIDEO_STYLES if r[1] == x),
                        key=f"vs_{i}",
                    )
                    font_style = st.selectbox(
                        "字体风格",
                        options=[row[1] for row in FONT_STYLES],
                        format_func=lambda x: next(r[0] for r in FONT_STYLES if r[1] == x),
                        key=f"fs_{i}",
                    )
                    voice_style = st.selectbox(
                        "配音风格",
                        options=[row[1] for row in VOICE_STYLES],
                        format_func=lambda x: next(r[0] for r in VOICE_STYLES if r[1] == x),
                        key=f"vo_{i}",
                    )
                    voice_gender = st.selectbox(
                        "配音性别",
                        options=[row[1] for row in VOICE_GENDERS],
                        format_func=lambda x: next(r[0] for r in VOICE_GENDERS if r[1] == x),
                        key=f"vg_{i}",
                    )
                    use_post = st.checkbox("后制：TTS + 字幕叠加", value=True, key=f"post_{i}", help="【推荐】生成后自动叠加：① 中文女声 TTS 配音 ② 宋体白字黑边字幕。解决无字幕、乱码、配音不对问题。")
                else:
                    use_post = False
                if st.button("🎬 生成视频", key=f"gen_{i}"):
                    script = p.get("script", "")
                    precheck = precheck_and_sanitize_script(script)
                    script_for_gen = precheck["clean_text"]
                    if precheck["changed"]:
                        st.warning(f"检测到 {len(precheck['hits'])} 处潜在敏感表达，已自动改写为合规表述后再生成。")
                    title = p.get("title", "")
                    hook = p.get("hook", "")
                    industry = p.get("industry", "营销")
                    if video_provider == "wanxiang" and use_long:
                        # 两段生成：0-15s + 15-30s（万象专用 prompt）
                        prompt1 = wanxiang_script_to_prompt(title, hook, script_for_gen, industry, video_style=video_style, font_style=font_style, voice_style=voice_style, voice_gender=voice_gender, segment=1, segment_seconds=(0, 15))
                        prompt2 = wanxiang_script_to_prompt(title, hook, script_for_gen, industry, video_style=video_style, font_style=font_style, voice_style=voice_style, voice_gender=voice_gender, segment=2, segment_seconds=(15, 30))
                        res1 = client.text2video(prompt1, size="720*1280", duration=WANXIANG_MAX_DURATION, negative_prompt=WANXIANG_NEGATIVE_PROMPT)
                        res2 = client.text2video(prompt2, size="720*1280", duration=WANXIANG_MAX_DURATION, negative_prompt=WANXIANG_NEGATIVE_PROMPT)
                        if "error" in res1:
                            st.error(res1["error"])
                        elif "error" in res2:
                            st.error(res2["error"])
                        else:
                            st.session_state["kling_tasks"].append({
                                "task_id": f"{res1['task_id']}_{res2['task_id']}",
                                "task_ids": [res1["task_id"], res2["task_id"]],
                                "video_provider": video_provider,
                                "title": title,
                                "hook": hook,
                                "script": script_for_gen,
                                "industry": industry,
                                "status": "processing",
                                "video_url": "",
                                "segment_urls": [],
                                "segment_count": 2,
                                "use_post_production": use_post,
                                "voice_gender": voice_gender,
                            })
                            save_video_tasks(st.session_state["kling_tasks"])
                            st.success("已提交 2 段任务（约 30 秒），请查看下方进度")
                            st.rerun()
                    else:
                        if video_provider == "wanxiang":
                            prompt = wanxiang_script_to_prompt(title, hook, script_for_gen, industry, video_style=video_style, font_style=font_style, voice_style=voice_style, voice_gender=voice_gender)
                            res = client.text2video(prompt, size="720*1280", duration=WANXIANG_MAX_DURATION, negative_prompt=WANXIANG_NEGATIVE_PROMPT)
                        else:
                            prompt = script_to_prompt(title, hook, script_for_gen, industry)
                            res = client.text2video(
                                prompt,
                                model="kling-v2.5-turbo",
                                duration=KLING_MAX_DURATION,
                                aspect_ratio="9:16",
                                mode="std",
                            )
                        if "error" in res:
                            st.error(res["error"])
                        else:
                            st.session_state["kling_tasks"].append({
                                "task_id": res["task_id"],
                                "video_provider": video_provider,
                                "title": title,
                                "hook": hook,
                                "script": script_for_gen,
                                "industry": industry,
                                "status": "processing",
                                "video_url": "",
                                "prompt_used": prompt,
                                "use_post_production": use_post if video_provider == "wanxiang" else False,
                                "voice_gender": voice_gender if video_provider == "wanxiang" else "female",
                            })
                            save_video_tasks(st.session_state["kling_tasks"])
                            st.success("任务已提交，请在下方查看进度（F5 刷新不会丢失）")
                            st.rerun()

st.divider()
st.subheader("生成任务")
if st.button("🔄 刷新进度"):
    st.rerun()


@st.fragment(run_every=15)
def _task_list():
    """任务列表：每 15 秒自动轮询进度"""
    tasks = st.session_state.get("kling_tasks", [])
    if not tasks:
        st.caption("点击上方「生成视频」后，任务将在此展示")
        return
    for idx, t in enumerate(tasks):
        task_id = t.get("task_id", "")
        task_ids = t.get("task_ids")  # 多段任务
        status = t.get("status", "processing")
        video_url = t.get("video_url", "")
        prov = t.get("video_provider", "wanxiang")
        task_client = wanxiang_client if prov == "wanxiang" else kling_client

        # 多段任务轮询
        if task_ids and status in ("processing", "pending", "running"):
            segment_urls = t.get("segment_urls") or []
            for i, tid in enumerate(task_ids):
                if i < len(segment_urls):
                    continue
                polled = task_client.get_task_status(tid)
                if polled.get("status") == "completed" and polled.get("video_url"):
                    segment_urls.append(polled["video_url"])
                    t["segment_urls"] = segment_urls
                    if len(segment_urls) == len(task_ids):
                        # 全部完成，下载并拼接
                        save_dir = Path(VIDEO_SAVE_DIR)
                        save_dir.mkdir(parents=True, exist_ok=True)
                        seg_paths = []
                        for j, url in enumerate(segment_urls):
                            fp = save_dir / f"_seg_{task_id[:8]}_{j}.mp4"
                            if _download_video(url, fp):
                                seg_paths.append(str(fp))
                        if len(seg_paths) == len(task_ids):
                            local_path = _download_and_save("", t.get("title", ""), task_id, segment_paths=seg_paths)
                            if local_path and t.get("use_post_production") and t.get("script"):
                                post_path = Path(local_path).with_stem(Path(local_path).stem + "_post")
                                result = run_post_production(
                                    local_path, t["script"], str(post_path),
                                    voice_gender=t.get("voice_gender", "female"),
                                )
                                if result:
                                    Path(local_path).unlink(missing_ok=True)
                                    local_path = result
                            t["local_path"] = local_path
                            t["video_url"] = local_path or segment_urls[0]
                        t["status"] = "completed"
                        save_video_tasks(st.session_state["kling_tasks"])
                    else:
                        save_video_tasks(st.session_state["kling_tasks"])
                elif polled.get("status") == "failed":
                    t["status"] = "failed"
                    t["error"] = polled.get("error", "生成失败")
                    save_video_tasks(st.session_state["kling_tasks"])
                    break

        # 单段任务轮询
        elif status in ("processing", "pending", "running") and task_id and not task_ids:
            polled = task_client.get_task_status(task_id)
            new_status = polled.get("status", status)
            if new_status == "completed" and polled.get("video_url"):
                t["status"] = "completed"
                t["video_url"] = polled["video_url"]
                local_path = _download_and_save(
                    polled["video_url"], t.get("title", ""), task_id
                )
                if local_path and t.get("use_post_production") and t.get("script"):
                    post_path = Path(local_path).with_stem(Path(local_path).stem + "_post")
                    result = run_post_production(
                        local_path, t["script"], str(post_path),
                        voice_gender=t.get("voice_gender", "female"),
                    )
                    if result:
                        Path(local_path).unlink(missing_ok=True)
                        local_path = result
                t["local_path"] = local_path
                save_video_tasks(st.session_state["kling_tasks"])
            elif new_status == "failed":
                t["status"] = "failed"
                t["error"] = polled.get("error", "生成失败")
                save_video_tasks(st.session_state["kling_tasks"])
            else:
                t["status"] = new_status or "processing"

        with st.expander(f"{'✅' if t.get('status') == 'completed' else '⏳'} {t.get('title', '')[:40]} | {t.get('status', '')}", expanded=t.get("status") != "completed"):
            st.caption(f"Task ID: {task_id}")
            if t.get("status") == "completed" and (t.get("video_url") or t.get("local_path")):
                vid = t.get("local_path") or t.get("video_url")
                st.video(vid)
                if t.get("video_url") and t["video_url"].startswith("http"):
                    st.markdown(f"[📎 在线链接]({t['video_url']})")
                if t.get("local_path"):
                    st.success(f"已保存到: `{t['local_path']}`")
            elif t.get("status") == "failed":
                err = t.get("error", "生成失败")
                if "balance" in str(err).lower() or "余额" in str(err):
                    err = "账户余额不足，请前往可灵平台充值后再试"
                elif "no message" in str(err).lower() or "任务失败" in str(err):
                    pass  # 已由 kling_client 返回更具体说明
                st.error(err)
            else:
                prov_hint = "万象 2.6 约 1–5 分钟" if prov == "wanxiang" else "Kling 约 30–60 秒"
                st.info(f"生成中（{prov_hint}），本页每 15 秒自动刷新，或点击「刷新进度」")
            if st.button("移除", key=f"rm_task_{idx}"):
                st.session_state["kling_tasks"] = [x for j, x in enumerate(tasks) if j != idx]
                save_video_tasks(st.session_state["kling_tasks"])
                st.rerun()


_task_list()

st.divider()
st.subheader("企业流程")
st.write("1. 输入产品 → 2. 选择行业 → 3. AI 生成脚本 → 4. 内容分析（评分、编辑）→ **5. AI 生成视频** → 6. 发布")
st.caption("万象 2.6 需 DASHSCOPE_API_KEY；Kling 需 KLING_ACCESS_KEY+SECRET_KEY。生成约 1–5 分钟。")
