"""
BSAI Asset Library System
- BSAI_AssetLibraryInput: Load images, videos, and audio from directories
- BSAI_AssetRefSelector: Select assets via @图N/@视频N/@音频N notation in prompt
- BSAI_ImageBatchSplitter: Split an IMAGE batch into individual images for H3 ref inputs
"""

import os
import re
import torch
import numpy as np
from PIL import Image
import folder_paths

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import comfy.utils
    _HAS_COMFY_UTILS = True
except Exception:
    _HAS_COMFY_UTILS = False

try:
    import torchaudio
    _HAS_TORCHAUDIO = True
except Exception:
    _HAS_TORCHAUDIO = False

try:
    import subprocess
    import tempfile
    _HAS_SUBPROCESS = True
except Exception:
    _HAS_SUBPROCESS = False


_IMG_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
_VID_EXTS = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv')
_AUD_EXTS = ('.wav', '.mp3', '.flac', '.ogg', '.aac', '.m4a')

MAX_REF_IMAGES = 9
MAX_REF_VIDEOS = 3
MAX_REF_AUDIOS = 3


def _resolve_directory(path):
    if not path:
        return None
    if os.path.isabs(path) and os.path.isdir(path):
        return path
    for base_func in [folder_paths.get_input_directory, folder_paths.get_output_directory]:
        full = os.path.join(base_func(), path)
        if os.path.isdir(full):
            return full
    return path if os.path.isdir(path) else None


def _load_image_tensor(path):
    img = Image.open(path).convert('RGB')
    arr = np.array(img, dtype=np.float32) / 255.0
    return torch.from_numpy(arr)


def _load_video_frames(path, max_frames=243):
    if cv2 is None:
        return torch.zeros(1, 64, 64, 3, dtype=torch.float32)
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return torch.zeros(1, 64, 64, 3, dtype=torch.float32)
    frames = []
    while len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame)
    cap.release()
    if not frames:
        return torch.zeros(1, 64, 64, 3, dtype=torch.float32)
    arr = np.stack(frames, dtype=np.float32) / 255.0
    return torch.from_numpy(arr)


def _load_audio_from_file(path):
    if _HAS_COMFY_UTILS:
        try:
            return comfy.utils.load_audio(path)
        except Exception:
            pass
    if _HAS_TORCHAUDIO:
        try:
            waveform, sr = torchaudio.load(path)
            if waveform.dim() == 2:
                waveform = waveform.unsqueeze(0)
            return {"waveform": waveform, "sample_rate": sr}
        except Exception:
            pass
    if _HAS_SUBPROCESS:
        try:
            tmp = tempfile.mktemp(suffix='.wav')
            subprocess.run(
                ['ffmpeg', '-y', '-i', path, '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', tmp],
                capture_output=True, timeout=60
            )
            if os.path.exists(tmp) and os.path.getsize(tmp) > 0:
                if _HAS_TORCHAUDIO:
                    waveform, sr = torchaudio.load(tmp)
                    if waveform.dim() == 2:
                        waveform = waveform.unsqueeze(0)
                    result = {"waveform": waveform, "sample_rate": sr}
                else:
                    import wave
                    with wave.open(tmp, 'rb') as wf:
                        n = wf.getnframes()
                        raw = wf.readframes(n)
                        sr = wf.getframerate()
                        ch = wf.getnchannels()
                        arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                        arr = arr.reshape(-1, ch).T
                        result = {"waveform": torch.from_numpy(arr).unsqueeze(0), "sample_rate": sr}
                os.unlink(tmp)
                return result
        except Exception:
            pass
    return {"waveform": torch.zeros(2, 1, 44100, dtype=torch.float32), "sample_rate": 44100}


def _empty_image():
    return torch.zeros(1, 64, 64, 3, dtype=torch.float32)


def _empty_audio():
    return {"waveform": torch.zeros(2, 1, 44100, dtype=torch.float32), "sample_rate": 44100}


class BSAI_AssetLibraryInput:
    """Upload images, videos, and audio files into a unified asset library.
    Files are uploaded via the node UI (batch or single), stored in input/bsai_assets/,
    and displayed as thumbnails. Each asset is indexed: 图1, 图2, ... / 视频1, ... / 音频1, ..."""

    CATEGORY = "BSAI"
    RETURN_TYPES = ("ASSET_LIBRARY",)
    RETURN_NAMES = ("asset_library",)
    FUNCTION = "load_assets"
    DESCRIPTION = "Upload images/videos/audio via node UI. Assets indexed: 图1,图2,... / 视频1,... / 音频1,..."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_files": ("STRING", {"default": "[]", "multiline": False, "tooltip": "JSON array of uploaded image filenames"}),
                "video_files": ("STRING", {"default": "[]", "multiline": False, "tooltip": "JSON array of uploaded video filenames"}),
                "audio_files": ("STRING", {"default": "[]", "multiline": False, "tooltip": "JSON array of uploaded audio filenames"}),
            }
        }

    def load_assets(self, image_files="[]", video_files="[]", audio_files="[]"):
        import json
        library = {"images": [], "videos": [], "audios": []}

        input_dir = folder_paths.get_input_directory()
        asset_base = os.path.join(input_dir, "bsai_assets")

        try:
            img_list = json.loads(image_files) if image_files else []
        except Exception:
            img_list = []
        try:
            vid_list = json.loads(video_files) if video_files else []
        except Exception:
            vid_list = []
        try:
            aud_list = json.loads(audio_files) if audio_files else []
        except Exception:
            aud_list = []

        img_dir = os.path.join(asset_base, "images")
        for fname in img_list:
            fpath = os.path.join(img_dir, fname)
            if os.path.exists(fpath):
                library["images"].append({
                    "path": fpath,
                    "name": fname,
                    "index": len(library["images"]) + 1,
                })

        vid_dir = os.path.join(asset_base, "videos")
        for fname in vid_list:
            fpath = os.path.join(vid_dir, fname)
            if os.path.exists(fpath):
                entry = {
                    "path": fpath,
                    "name": fname,
                    "index": len(library["videos"]) + 1,
                }
                if cv2 is not None:
                    cap = cv2.VideoCapture(fpath)
                    if cap.isOpened():
                        entry["frame_count"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        entry["fps"] = cap.get(cv2.CAP_PROP_FPS) or 24.0
                        entry["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        entry["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
                library["videos"].append(entry)

        aud_dir = os.path.join(asset_base, "audio")
        for fname in aud_list:
            fpath = os.path.join(aud_dir, fname)
            if os.path.exists(fpath):
                library["audios"].append({
                    "path": fpath,
                    "name": fname,
                    "index": len(library["audios"]) + 1,
                })

        total = len(library["images"]) + len(library["videos"]) + len(library["audios"])
        print(f"[BSAI AssetLibrary] Loaded {len(library['images'])} images, {len(library['videos'])} videos, {len(library['audios'])} audios (total {total})")
        return (library,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")


class BSAI_AssetRefSelector:
    """Select assets from the library using @图N / @视频N / @音频N notation in the prompt.
    Outputs individual images/videos/audios for MiniMaxH3ReferenceToVideo, plus a formatted prompt with H3 <Picture>/<Video>/<Audio> tags."""

    CATEGORY = "BSAI"
    RETURN_TYPES = (
        "IMAGE",
        "IMAGE", "IMAGE", "IMAGE",
        "AUDIO", "AUDIO", "AUDIO",
        "AUDIO", "AUDIO", "AUDIO",
        "STRING",
    )
    RETURN_NAMES = (
        "ref_images",
        "ref_video_0", "ref_video_1", "ref_video_2",
        "ref_video_audio_0", "ref_video_audio_1", "ref_video_audio_2",
        "ref_audio_0", "ref_audio_1", "ref_audio_2",
        "formatted_prompt",
    )
    FUNCTION = "select_assets"
    DESCRIPTION = "Parse @图N/@视频N/@音频N in prompt, load referenced assets, output for MiniMaxH3ReferenceToVideo."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "asset_library": ("ASSET_LIBRARY",),
                "prompt": ("STRING", {"default": "", "multiline": True, "tooltip": "Use @图1 @图3 for images, @视频1 for videos, @音频1 for audio"}),
            }
        }

    def select_assets(self, asset_library, prompt):
        images = asset_library.get("images", [])
        videos = asset_library.get("videos", [])
        audios = asset_library.get("audios", [])

        img_refs = [int(x) for x in re.findall(r'@图(\d+)', prompt)]
        vid_refs = [int(x) for x in re.findall(r'@视频(\d+)', prompt)]
        aud_refs = [int(x) for x in re.findall(r'@音频(\d+)', prompt)]

        img_refs = img_refs[:MAX_REF_IMAGES]
        vid_refs = vid_refs[:MAX_REF_VIDEOS]
        aud_refs = aud_refs[:MAX_REF_AUDIOS]

        formatted = prompt

        selected_images = []
        for i, ref_idx in enumerate(img_refs):
            found = next((a for a in images if a["index"] == ref_idx), None)
            if found:
                tensor = _load_image_tensor(found["path"])
                selected_images.append(tensor)
                formatted = formatted.replace(f'@图{ref_idx}', f'<Picture {i + 1}>')
            else:
                print(f"[BSAI AssetRefSelector] Warning: @图{ref_idx} not found in library (have {len(images)} images)")

        if selected_images:
            ref_images_batch = torch.stack(selected_images)
        else:
            ref_images_batch = _empty_image()

        ref_videos = [_empty_image()] * 3
        ref_video_audios = [_empty_audio()] * 3
        for i, ref_idx in enumerate(vid_refs):
            found = next((a for a in videos if a["index"] == ref_idx), None)
            if found:
                ref_videos[i] = _load_video_frames(found["path"])
                ref_video_audios[i] = _load_audio_from_file(found["path"])
                formatted = formatted.replace(f'@视频{ref_idx}', f'<Video {i + 1}>')
            else:
                print(f"[BSAI AssetRefSelector] Warning: @视频{ref_idx} not found in library (have {len(videos)} videos)")

        ref_audios = [_empty_audio()] * 3
        for i, ref_idx in enumerate(aud_refs):
            found = next((a for a in audios if a["index"] == ref_idx), None)
            if found:
                ref_audios[i] = _load_audio_from_file(found["path"])
                formatted = formatted.replace(f'@音频{ref_idx}', f'<Audio {i + 1}>')
            else:
                print(f"[BSAI AssetRefSelector] Warning: @音频{ref_idx} not found in library (have {len(audios)} audios)")

        print(f"[BSAI AssetRefSelector] Selected {len(selected_images)} images, {len(vid_refs)} videos, {len(aud_refs)} audios")
        return (
            ref_images_batch,
            ref_videos[0], ref_videos[1], ref_videos[2],
            ref_video_audios[0], ref_video_audios[1], ref_video_audios[2],
            ref_audios[0], ref_audios[1], ref_audios[2],
            formatted,
        )

    @classmethod
    def IS_CHANGED(cls):
        return float("nan")


class BSAI_ImageBatchSplitter:
    """Split an IMAGE batch into individual images (up to 9) for MiniMaxH3ReferenceToVideo ref_image_N inputs."""

    CATEGORY = "BSAI"
    RETURN_TYPES = ("IMAGE",) * MAX_REF_IMAGES
    RETURN_NAMES = tuple(f"image_{i}" for i in range(MAX_REF_IMAGES))
    FUNCTION = "split_batch"
    DESCRIPTION = "Split IMAGE batch into individual images for H3 ref_image_0..8 inputs."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            }
        }

    def split_batch(self, images):
        result = []
        for i in range(MAX_REF_IMAGES):
            if i < images.shape[0]:
                result.append(images[i:i + 1])
            else:
                result.append(images[0:1] if images.shape[0] > 0 else _empty_image())
        return tuple(result)


NODE_CLASS_MAPPINGS = {
    "BSAI_AssetLibraryInput": BSAI_AssetLibraryInput,
    "BSAI_AssetRefSelector": BSAI_AssetRefSelector,
    "BSAI_ImageBatchSplitter": BSAI_ImageBatchSplitter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_AssetLibraryInput": "BSAI Asset Library Input",
    "BSAI_AssetRefSelector": "BSAI Asset Reference Selector",
    "BSAI_ImageBatchSplitter": "BSAI Image Batch Splitter",
}
