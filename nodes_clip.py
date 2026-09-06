"""
BSAI Clip Management System
- BSAI_ClipComposer: Define a single clip with prompt, subtitles, audio settings, asset refs
- BSAI_ClipSequencer: Self-contained storyboard with vertical CLIP cards, asset library @ notation

@ notation: @图N for images, @视频N for videos, @音频N for audio
Resolves against BSAI_AssetLibraryInput output (ASSET_LIBRARY type).
"""

import re
import json

FPS = 24
H3_FRAME_GRID = [5, 22, 39, 56, 73, 90, 107, 124, 141, 158, 175, 192, 209, 226, 243]

MAX_REF_IMAGES = 9
MAX_REF_VIDEOS = 3
MAX_REF_AUDIOS = 3


def _duration_to_frames(duration_seconds):
    target = int(duration_seconds * FPS)
    best = H3_FRAME_GRID[0]
    for v in H3_FRAME_GRID:
        if v <= target:
            best = v
    if target > H3_FRAME_GRID[-1] and abs(target - H3_FRAME_GRID[-1]) < abs(target - best):
        best = H3_FRAME_GRID[-1]
    return best


def _extract_subtitles_from_prompt(prompt):
    narration_lines = []
    dialogue_lines = []
    for line in prompt.split('\n'):
        line = line.strip()
        if not line:
            continue
        if re.match(r'^(?:【旁白】|旁白[：:]|\(旁白[:：])', line):
            text = re.sub(r'^(?:【旁白】|旁白[：:]|\(旁白[:：]\s*)', '', line).rstrip(')')
            narration_lines.append(text.strip())
        elif re.match(r'^(?:【对白】|对白[：:]|\(对白[:：])', line):
            text = re.sub(r'^(?:【对白】|对白[：:]|\(对白[:：]\s*)', '', line).rstrip(')')
            dialogue_lines.append(text.strip())
    return '\n'.join(narration_lines), '\n'.join(dialogue_lines)


def _resolve_asset_refs(asset_library, prompt, asset_refs_str):
    """Resolve @图N/@视频N/@音频N notation against the asset library.
    Returns (formatted_prompt, ref_image_paths, ref_video_paths, ref_audio_paths)."""
    if not asset_library:
        return prompt, [], [], []

    images = asset_library.get("images", [])
    videos = asset_library.get("videos", [])
    audios = asset_library.get("audios", [])

    combined = (prompt + " " + (asset_refs_str or "")).strip()

    img_refs = [int(x) for x in re.findall(r'@图(\d+)', combined)]
    vid_refs = [int(x) for x in re.findall(r'@视频(\d+)', combined)]
    aud_refs = [int(x) for x in re.findall(r'@音频(\d+)', combined)]

    img_refs = img_refs[:MAX_REF_IMAGES]
    vid_refs = vid_refs[:MAX_REF_VIDEOS]
    aud_refs = aud_refs[:MAX_REF_AUDIOS]

    formatted = prompt

    ref_image_paths = []
    for i, ref_idx in enumerate(img_refs):
        found = next((a for a in images if a["index"] == ref_idx), None)
        if found:
            ref_image_paths.append(found["path"])
            formatted = formatted.replace(f'@图{ref_idx}', f'<Picture {i + 1}>')
        else:
            print(f"[BSAI] Warning: @图{ref_idx} not found in library ({len(images)} images available)")

    ref_video_paths = []
    for i, ref_idx in enumerate(vid_refs):
        found = next((a for a in videos if a["index"] == ref_idx), None)
        if found:
            ref_video_paths.append(found["path"])
            formatted = formatted.replace(f'@视频{ref_idx}', f'<Video {i + 1}>')
        else:
            print(f"[BSAI] Warning: @视频{ref_idx} not found in library ({len(videos)} videos available)")

    ref_audio_paths = []
    for i, ref_idx in enumerate(aud_refs):
        found = next((a for a in audios if a["index"] == ref_idx), None)
        if found:
            ref_audio_paths.append(found["path"])
            formatted = formatted.replace(f'@音频{ref_idx}', f'<Audio {i + 1}>')
        else:
            print(f"[BSAI] Warning: @音频{ref_idx} not found in library ({len(audios)} audios available)")

    return formatted, ref_image_paths, ref_video_paths, ref_audio_paths


class BSAI_ClipComposer:
    """Compose a single clip with generation prompt, subtitle text, audio settings, and asset references.
    Supports @图N/@视频N/@音频N notation for referencing assets from BSAI_AssetLibraryInput.
    Connect asset_library input to enable @ notation resolution.
    Clips are arranged top-to-bottom in the workflow like a storyboard script."""

    CATEGORY = "BSAI"
    RETURN_TYPES = ("CLIP_INFO",)
    RETURN_NAMES = ("clip_info",)
    FUNCTION = "compose_clip"
    DESCRIPTION = "Define a clip: prompt, subtitle (旁白/对白), audio mode, duration, asset refs (@图N/@视频N/@音频N)."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True, "tooltip": "Generation prompt. Use 【旁白】/【对白】 for subtitles, @图N/@视频N/@音频N for assets."}),
                "asset_refs": ("STRING", {"default": "", "multiline": False, "tooltip": "Asset references: @图1 @图2 @视频1 @音频1"}),
                "narration": ("STRING", {"default": "", "multiline": True, "tooltip": "旁白字幕 (narration subtitle text). Used when subtitle_source='manual'."}),
                "dialogue": ("STRING", {"default": "", "multiline": True, "tooltip": "对白字幕 (dialogue subtitle text). Used when subtitle_source='manual'."}),
                "subtitle_source": (["manual", "extract_from_prompt"], {"default": "manual", "tooltip": "manual: use narration/dialogue fields. extract_from_prompt: parse 【旁白】/【对白】 from prompt."}),
                "audio_mode": (["H3_auto", "custom"], {"default": "H3_auto", "tooltip": "H3_auto: use H3 generated audio. custom: use user-provided audio."}),
                "duration": ("FLOAT", {"default": 5.0, "min": 0.25, "max": 150.0, "step": 0.25, "tooltip": "Clip duration in seconds. Snapped to H3 17n+5 frame grid."}),
                "width": ("INT", {"default": 1344, "min": 256, "max": 2048, "step": 32, "tooltip": "Video width (multiple of 32)"}),
                "height": ("INT", {"default": 768, "min": 256, "max": 2048, "step": 32, "tooltip": "Video height (multiple of 32)"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2**32 - 1, "tooltip": "Generation seed"}),
            },
            "optional": {
                "asset_library": ("ASSET_LIBRARY", {"tooltip": "Connect BSAI_AssetLibraryInput to enable @ notation resolution."}),
            },
        }

    def compose_clip(self, prompt, asset_refs, narration, dialogue, subtitle_source, audio_mode, duration, width, height, seed, asset_library=None):
        narr_text = narration
        dial_text = dialogue
        if subtitle_source == "extract_from_prompt":
            extracted_narr, extracted_dial = _extract_subtitles_from_prompt(prompt)
            if extracted_narr:
                narr_text = extracted_narr
            if extracted_dial:
                dial_text = extracted_dial

        formatted_prompt, ref_image_paths, ref_video_paths, ref_audio_paths = _resolve_asset_refs(
            asset_library, prompt, asset_refs
        )

        clip_info = {
            "prompt": prompt,
            "formatted_prompt": formatted_prompt,
            "asset_refs": asset_refs,
            "ref_image_paths": ref_image_paths,
            "ref_video_paths": ref_video_paths,
            "ref_audio_paths": ref_audio_paths,
            "narration": narr_text,
            "dialogue": dial_text,
            "subtitle_source": subtitle_source,
            "audio_mode": audio_mode,
            "duration": duration,
            "frame_count": _duration_to_frames(duration),
            "width": width,
            "height": height,
            "seed": seed,
        }
        print(f"[BSAI ClipComposer] Clip composed: {duration}s -> {clip_info['frame_count']} frames, refs: {len(ref_image_paths)}img/{len(ref_video_paths)}vid/{len(ref_audio_paths)}aud")
        return (clip_info,)

    @classmethod
    def IS_CHANGED(cls):
        return float("nan")


class BSAI_ClipSequencer:
    """Self-contained storyboard sequencer with vertical CLIP cards.

    Define clips directly in the node UI (top-to-bottom arrangement).
    Use @图N/@视频N/@音频N in each clip's asset_refs to reference assets from BSAI_AssetLibraryInput.
    Connect asset_library input to enable @ notation resolution.

    Also accepts external CLIP_INFO inputs (clip_1..clip_4) for backward compatibility
    with BSAI_ClipComposer. External clips are placed before internal clips in the sequence."""

    CATEGORY = "BSAI"
    RETURN_TYPES = ("CLIP_SEQUENCE",)
    RETURN_NAMES = ("clip_sequence",)
    FUNCTION = "sequence_clips"
    DESCRIPTION = "Storyboard sequencer: vertical CLIP cards, @资产库引用, manual add/remove clips."

    MAX_EXT_CLIPS = 4

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(1, cls.MAX_EXT_CLIPS + 1):
            optional[f"clip_{i}"] = ("CLIP_INFO", {"tooltip": f"External clip {i} (from BSAI_ClipComposer). Optional."})
        optional["asset_library"] = ("ASSET_LIBRARY", {"tooltip": "Connect BSAI_AssetLibraryInput for @ notation resolution."})
        return {
            "required": {
                "clips_json": ("STRING", {"default": "[]", "multiline": False, "tooltip": "JSON array of clip definitions (managed by UI)."}),
            },
            "optional": optional,
        }

    def sequence_clips(self, clips_json="[]", **kwargs):
        clips = []

        # External clips (from ClipComposer nodes)
        ext_count = 0
        for i in range(1, self.MAX_EXT_CLIPS + 1):
            key = f"clip_{i}"
            if key in kwargs and kwargs[key] is not None:
                clips.append(kwargs[key])
                ext_count += 1

        # Internal clips (from embedded UI cards)
        asset_library = kwargs.get("asset_library", None)
        try:
            internal_clips = json.loads(clips_json) if clips_json else []
        except Exception:
            internal_clips = []

        for clip_def in internal_clips:
            prompt = clip_def.get("prompt", "")
            asset_refs = clip_def.get("asset_refs", "")
            narration = clip_def.get("narration", "")
            dialogue = clip_def.get("dialogue", "")
            subtitle_source = clip_def.get("subtitle_source", "manual")
            audio_mode = clip_def.get("audio_mode", "H3_auto")
            duration = clip_def.get("duration", 5.0)
            width = clip_def.get("width", 1344)
            height = clip_def.get("height", 768)
            seed = clip_def.get("seed", 0)

            narr_text = narration
            dial_text = dialogue
            if subtitle_source == "extract_from_prompt":
                extracted_narr, extracted_dial = _extract_subtitles_from_prompt(prompt)
                if extracted_narr:
                    narr_text = extracted_narr
                if extracted_dial:
                    dial_text = extracted_dial

            formatted_prompt, ref_image_paths, ref_video_paths, ref_audio_paths = _resolve_asset_refs(
                asset_library, prompt, asset_refs
            )

            clip_info = {
                "prompt": prompt,
                "formatted_prompt": formatted_prompt,
                "asset_refs": asset_refs,
                "ref_image_paths": ref_image_paths,
                "ref_video_paths": ref_video_paths,
                "ref_audio_paths": ref_audio_paths,
                "narration": narr_text,
                "dialogue": dial_text,
                "subtitle_source": subtitle_source,
                "audio_mode": audio_mode,
                "duration": duration,
                "frame_count": _duration_to_frames(duration),
                "width": width,
                "height": height,
                "seed": seed,
            }
            clips.append(clip_info)

        total_dur = sum(c.get("duration", 0) for c in clips)
        print(f"[BSAI ClipSequencer] Sequenced {len(clips)} clips ({ext_count} external + {len(internal_clips)} internal), total {total_dur:.1f}s")
        return (clips,)

    @classmethod
    def IS_CHANGED(cls):
        return float("nan")


NODE_CLASS_MAPPINGS = {
    "BSAI_ClipComposer": BSAI_ClipComposer,
    "BSAI_ClipSequencer": BSAI_ClipSequencer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_ClipComposer": "BSAI Clip Composer",
    "BSAI_ClipSequencer": "BSAI Clip Sequencer",
}
