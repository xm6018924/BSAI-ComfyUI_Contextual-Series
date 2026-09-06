import os
import torch
import numpy as np
from PIL import Image

import folder_paths


class BSAI_ContextualSeriesExtract:
    """
    Extract reference frames from a previously generated video to maintain
    visual consistency (characters, scenes, props, lighting, colors) across
    sequential video generations.

    Designed for MiniMax H3 Omni Reference mode, which accepts up to 9
    reference images to preserve visual continuity between clips.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "selection_mode": (
                    ["last_n", "first_n", "middle_n", "custom_range"],
                    {
                        "default": "last_n",
                        "tooltip": (
                            "last_n: take last N frames (recommended for continuity). "
                            "first_n: take first N frames. "
                            "middle_n: take N frames centered on the midpoint. "
                            "custom_range: use start_frame and end_frame indices."
                        ),
                    },
                ),
                "frame_count": (
                    "INT",
                    {
                        "default": 15,
                        "min": 1,
                        "max": 500,
                        "step": 1,
                        "tooltip": "Number of frames to extract (used by last_n / first_n / middle_n).",
                    },
                ),
                "start_frame": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 100000,
                        "step": 1,
                        "tooltip": "Start frame index (0-based) for custom_range mode.",
                    },
                ),
                "end_frame": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 100000,
                        "step": 1,
                        "tooltip": "End frame index (exclusive). 0 = up to last frame.",
                    },
                ),
                "max_output_frames": (
                    "INT",
                    {
                        "default": 9,
                        "min": 1,
                        "max": 50,
                        "step": 1,
                        "tooltip": (
                            "Maximum frames to output after subsampling. "
                            "MiniMax H3 Omni Reference supports up to 9 images."
                        ),
                    },
                ),
                "sampling_method": (
                    ["even", "sequential"],
                    {
                        "default": "even",
                        "tooltip": (
                            "even: evenly distributed sampling (preserves overall content). "
                            "sequential: take first N of the selected range."
                        ),
                    },
                ),
            },
            "optional": {
                "save_frames": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Save extracted frames as PNG files for cross-session reuse.",
                    },
                ),
                "output_subdir": (
                    "STRING",
                    {
                        "default": "contextual_series",
                        "tooltip": "Subdirectory under ComfyUI output folder for saved frames.",
                    },
                ),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "frame",
                        "tooltip": "Prefix for saved frame filenames (e.g. frame_00000.png).",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("images", "frame_count")
    FUNCTION = "extract_frames"
    CATEGORY = "BSAI"
    DESCRIPTION = (
        "Extract reference frames from a previously generated video to maintain "
        "visual consistency (characters, scenes, props, lighting, colors) across "
        "sequential video generations. Designed for MiniMax H3 Omni Reference mode."
    )

    def extract_frames(
        self,
        images,
        selection_mode,
        frame_count,
        start_frame,
        end_frame,
        max_output_frames,
        sampling_method,
        save_frames=False,
        output_subdir="contextual_series",
        filename_prefix="frame",
    ):
        total = images.shape[0]
        if total == 0:
            raise ValueError("Input IMAGE tensor is empty (0 frames).")

        if selection_mode == "last_n":
            n = min(frame_count, total)
            start = max(0, total - n)
            end = total
        elif selection_mode == "first_n":
            n = min(frame_count, total)
            start = 0
            end = n
        elif selection_mode == "middle_n":
            n = min(frame_count, total)
            mid = total // 2
            start = max(0, mid - n // 2)
            end = min(total, start + n)
        else:
            start = min(start_frame, total - 1)
            if end_frame <= 0 or end_frame > total:
                end = total
            else:
                end = min(end_frame, total)
            if end <= start:
                end = min(start + 1, total)

        selected = images[start:end]
        sel_count = selected.shape[0]

        if sel_count > max_output_frames:
            if sampling_method == "even":
                indices = torch.linspace(0, sel_count - 1, max_output_frames).long()
                selected = selected[indices]
            else:
                selected = selected[:max_output_frames]
            sel_count = max_output_frames

        if save_frames:
            self._save_frames(selected, output_subdir, filename_prefix)

        return (selected, sel_count)

    @staticmethod
    def _save_frames(images, output_subdir, filename_prefix):
        output_dir = folder_paths.get_output_directory()
        save_dir = os.path.join(output_dir, output_subdir)
        os.makedirs(save_dir, exist_ok=True)

        for i in range(images.shape[0]):
            img_np = (images[i].cpu().numpy() * 255.0).astype(np.uint8)
            Image.fromarray(img_np).save(
                os.path.join(save_dir, f"{filename_prefix}_{i:05d}.png")
            )

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")


class BSAI_ContextualSeriesLoad:
    """
    Load previously saved contextual reference frames from disk.
    Pairs with BSAI_ContextualSeriesExtract for cross-session workflows
    where run 1 and run 2 happen in separate ComfyUI sessions.
    """

    @staticmethod
    def _resolve_directory(directory):
        if os.path.isabs(directory) and os.path.isdir(directory):
            return directory
        candidates = [
            os.path.join(folder_paths.get_output_directory(), directory),
            os.path.join(folder_paths.get_input_directory(), directory),
            directory,
        ]
        for c in candidates:
            if os.path.isdir(c):
                return c
        return directory

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": (
                            "Directory containing saved frame PNG files. "
                            "Accepts absolute path or name relative to ComfyUI output/input folder."
                        ),
                    },
                ),
                "filename_prefix": (
                    "STRING",
                    {
                        "default": "frame",
                        "tooltip": "Only load files whose name starts with this prefix.",
                    },
                ),
                "max_frames": (
                    "INT",
                    {
                        "default": 9,
                        "min": 1,
                        "max": 50,
                        "step": 1,
                        "tooltip": "Maximum number of frames to load.",
                    },
                ),
                "sampling_method": (
                    ["even", "sequential", "all"],
                    {
                        "default": "even",
                        "tooltip": (
                            "even: evenly distributed across available files. "
                            "sequential: take first N files. "
                            "all: load every matching file (ignores max_frames)."
                        ),
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("images", "frame_count")
    FUNCTION = "load_frames"
    CATEGORY = "BSAI"
    DESCRIPTION = (
        "Load previously saved contextual reference frames from disk "
        "for cross-session visual consistency."
    )

    def load_frames(self, directory, filename_prefix, max_frames, sampling_method):
        if not directory:
            raise ValueError("Directory path is required.")

        resolved = self._resolve_directory(directory)
        if not os.path.isdir(resolved):
            raise ValueError(f"Directory not found: {directory}")

        exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
        files = sorted(
            os.path.join(resolved, f)
            for f in os.listdir(resolved)
            if f.startswith(filename_prefix) and f.lower().endswith(exts)
        )
        if not files:
            raise ValueError(
                f"No files with prefix '{filename_prefix}' found in {resolved}"
            )

        total = len(files)

        if sampling_method == "all" or total <= max_frames:
            chosen = files
        elif sampling_method == "even":
            idx = np.linspace(0, total - 1, max_frames).astype(int)
            chosen = [files[i] for i in idx]
        else:
            chosen = files[:max_frames]

        tensors = []
        ref_h, ref_w = None, None
        for fp in chosen:
            img = Image.open(fp).convert("RGB")
            if ref_h is None:
                ref_h, ref_w = img.height, img.width
            elif img.height != ref_h or img.width != ref_w:
                img = img.resize((ref_w, ref_h), Image.LANCZOS)
            arr = np.array(img, dtype=np.float32) / 255.0
            tensors.append(torch.from_numpy(arr))

        batch = torch.stack(tensors, dim=0)
        return (batch, batch.shape[0])

    @classmethod
    def IS_CHANGED(cls, directory, **kwargs):
        resolved = cls._resolve_directory(directory)
        if not os.path.isdir(resolved):
            return ""
        return str(os.path.getmtime(resolved))


NODE_CLASS_MAPPINGS = {
    "BSAI_ContextualSeriesExtract": BSAI_ContextualSeriesExtract,
    "BSAI_ContextualSeriesLoad": BSAI_ContextualSeriesLoad,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_ContextualSeriesExtract": "BSAI Contextual Series Extract",
    "BSAI_ContextualSeriesLoad": "BSAI Contextual Series Load",
}
