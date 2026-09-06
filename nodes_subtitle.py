"""
BSAI Subtitle System
- BSAI_SubtitleConfig: Configure subtitle font/color/size/position from C:\\Windows\\Fonts
- BSAI_SubtitleRenderer: Render narration (旁白) and dialogue (对白) subtitles on video frames
"""

import os
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _list_fonts():
    fonts_dir = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
    fonts = []
    if os.path.isdir(fonts_dir):
        for fname in sorted(os.listdir(fonts_dir)):
            lower = fname.lower()
            if lower.endswith(('.ttf', '.otf', '.ttc')):
                fonts.append(fname)
    if not fonts:
        fonts = ["arial.ttf"]
    return fonts


_AVAILABLE_FONTS = _list_fonts()
_DEFAULT_FONT = "msyh.ttc" if "msyh.ttc" in _AVAILABLE_FONTS else (_AVAILABLE_FONTS[0] if _AVAILABLE_FONTS else "arial.ttf")


def _get_font_path(font_name):
    fonts_dir = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
    path = os.path.join(fonts_dir, font_name)
    if os.path.exists(path):
        return path
    for fb in ['msyh.ttc', 'simhei.ttf', 'simsun.ttc', 'arial.ttf']:
        fb_path = os.path.join(fonts_dir, fb)
        if os.path.exists(fb_path):
            return fb_path
    return None


def _parse_color(color_str):
    s = color_str.strip().lstrip('#')
    try:
        if len(s) == 6:
            return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
        if len(s) == 3:
            return tuple(int(c * 2, 16) for c in s)
    except Exception:
        pass
    return (255, 255, 255)


def _wrap_text(text, font, max_width, draw):
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            lines.append('')
            continue
        is_cjk = any('\u4e00' <= c <= '\u9fff' for c in paragraph)
        if is_cjk and ' ' not in paragraph:
            current = ""
            for char in paragraph:
                test = current + char
                bbox = draw.textbbox((0, 0), test, font=font)
                if (bbox[2] - bbox[0]) > max_width and current:
                    lines.append(current)
                    current = char
                else:
                    current = test
            if current:
                lines.append(current)
        else:
            words = paragraph.split(' ')
            current = ""
            for word in words:
                test = f"{current} {word}".strip() if current else word
                bbox = draw.textbbox((0, 0), test, font=font)
                if (bbox[2] - bbox[0]) > max_width and current:
                    lines.append(current)
                    current = word
                else:
                    current = test
            if current:
                lines.append(current)
    return [l for l in lines if l is not None]


def _draw_text_block(draw, img_w, img_h, lines, font, color_rgba, position, margin, bg_box, line_spacing=4):
    if not lines:
        return 0
    line_heights = []
    line_widths = []
    for line in lines:
        if line:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_heights.append(max(bbox[3] - bbox[1], font.size // 2) + 6)
            line_widths.append(bbox[2] - bbox[0])
        else:
            line_heights.append(font.size // 2)
            line_widths.append(0)
    total_h = sum(line_heights) + line_spacing * max(len(lines) - 1, 0)
    if position == 'top':
        y = margin
    elif position == 'center':
        y = max(margin, (img_h - total_h) // 2)
    else:
        y = max(margin, img_h - total_h - margin)
    for i, line in enumerate(lines):
        if line:
            x = max(0, (img_w - line_widths[i]) // 2)
            if bg_box:
                pad = 8
                draw.rectangle(
                    [x - pad, y - 2, x + line_widths[i] + pad, y + line_heights[i]],
                    fill=(0, 0, 0, 170)
                )
            draw.text((x, y), line, fill=color_rgba, font=font)
        y += line_heights[i] + line_spacing
    return total_h


class BSAI_SubtitleConfig:
    """Configure subtitle font, color, size, and position.
    Font selection from C:\\Windows\\Fonts. Supports two subtitle types: narration (旁白) and dialogue (对白)."""

    CATEGORY = "BSAI"
    RETURN_TYPES = ("SUBTITLE_CONFIG",)
    RETURN_NAMES = ("subtitle_config",)
    FUNCTION = "configure"
    DESCRIPTION = "Configure subtitle styling: font from C:\\Windows\\Fonts, color, size, position for 旁白 and 对白."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "font_name": (_AVAILABLE_FONTS, {"default": _DEFAULT_FONT, "tooltip": "Font file from C:\\Windows\\Fonts"}),
                "font_size": ("INT", {"default": 36, "min": 8, "max": 200, "step": 1, "tooltip": "Font size in pixels"}),
                "narration_color": ("STRING", {"default": "#FFFFFF", "tooltip": "旁白 subtitle color (hex, e.g. #FFFFFF for white)"}),
                "dialogue_color": ("STRING", {"default": "#FFEE88", "tooltip": "对白 subtitle color (hex, e.g. #FFEE88 for yellow)"}),
                "narration_position": (["top", "center", "bottom"], {"default": "top", "tooltip": "旁白 subtitle vertical position"}),
                "dialogue_position": (["top", "center", "bottom"], {"default": "bottom", "tooltip": "对白 subtitle vertical position"}),
                "background_box": ("BOOLEAN", {"default": True, "tooltip": "Draw semi-transparent background behind text for readability"}),
                "margin": ("INT", {"default": 30, "min": 0, "max": 500, "step": 1, "tooltip": "Margin from screen edge in pixels"}),
            }
        }

    def configure(self, font_name, font_size, narration_color, dialogue_color,
                  narration_position, dialogue_position, background_box, margin):
        config = {
            "font_name": font_name,
            "font_size": font_size,
            "narration_color": narration_color,
            "dialogue_color": dialogue_color,
            "narration_position": narration_position,
            "dialogue_position": dialogue_position,
            "background_box": background_box,
            "margin": margin,
        }
        return (config,)


class BSAI_SubtitleRenderer:
    """Render narration (旁白) and dialogue (对白) subtitles on video frames.
    Can extract subtitle text from CLIP_INFO or accept direct text input."""

    CATEGORY = "BSAI"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "render"
    DESCRIPTION = "Burn-in 旁白/对白 subtitles onto video frames using configured font and style."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "Video frames to render subtitles on"}),
                "subtitle_config": ("SUBTITLE_CONFIG", {"tooltip": "Subtitle styling configuration"}),
            },
            "optional": {
                "clip_info": ("CLIP_INFO", {"tooltip": "Clip info containing narration/dialogue text. Overrides manual text."}),
                "narration": ("STRING", {"default": "", "multiline": True, "tooltip": "旁白 subtitle text (used if clip_info not connected)"}),
                "dialogue": ("STRING", {"default": "", "multiline": True, "tooltip": "对白 subtitle text (used if clip_info not connected)"}),
            }
        }

    def render(self, images, subtitle_config, **kwargs):
        clip_info = kwargs.get("clip_info")
        narr_text = kwargs.get("narration", "")
        dial_text = kwargs.get("dialogue", "")
        if clip_info:
            if clip_info.get("narration"):
                narr_text = clip_info["narration"]
            if clip_info.get("dialogue"):
                dial_text = clip_info["dialogue"]

        if not narr_text and not dial_text:
            return (images,)

        font_path = _get_font_path(subtitle_config["font_name"])
        if font_path is None:
            print("[BSAI SubtitleRenderer] Warning: font not found, skipping subtitle render")
            return (images,)

        font = ImageFont.truetype(font_path, subtitle_config["font_size"])
        h, w = images.shape[1], images.shape[2]
        margin = subtitle_config["margin"]
        max_width = w - 2 * margin

        overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, 'RGBA')

        if narr_text:
            narr_color = _parse_color(subtitle_config["narration_color"]) + (255,)
            narr_lines = _wrap_text(narr_text, font, max_width, draw)
            _draw_text_block(draw, w, h, narr_lines, font, narr_color,
                             subtitle_config["narration_position"], margin,
                             subtitle_config["background_box"])

        if dial_text:
            dial_color = _parse_color(subtitle_config["dialogue_color"]) + (255,)
            dial_lines = _wrap_text(dial_text, font, max_width, draw)
            _draw_text_block(draw, w, h, dial_lines, font, dial_color,
                             subtitle_config["dialogue_position"], margin,
                             subtitle_config["background_box"])

        result = []
        for i in range(images.shape[0]):
            frame = images[i].cpu().numpy()
            frame = (frame * 255).astype(np.uint8)
            img = Image.fromarray(frame).convert('RGBA')
            img = Image.alpha_composite(img, overlay)
            img = img.convert('RGB')
            result.append(torch.from_numpy(np.array(img, dtype=np.float32) / 255.0))

        print(f"[BSAI SubtitleRenderer] Rendered subtitles on {images.shape[0]} frames (narration={bool(narr_text)}, dialogue={bool(dial_text)})")
        return (torch.stack(result),)


NODE_CLASS_MAPPINGS = {
    "BSAI_SubtitleConfig": BSAI_SubtitleConfig,
    "BSAI_SubtitleRenderer": BSAI_SubtitleRenderer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_SubtitleConfig": "BSAI Subtitle Config",
    "BSAI_SubtitleRenderer": "BSAI Subtitle Renderer",
}
