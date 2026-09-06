"""
BSAI Media Combiner System
- BSAI_VideoCombiner: Concatenate multiple video clips into one (up to 16 clips)
- BSAI_AudioCombiner: Concatenate multiple audio streams into one (up to 16 streams)
"""

import torch


class BSAI_VideoCombiner:
    """Combine multiple video clips (IMAGE batches) into a single continuous video.
    All clips are resized to match the first clip's resolution using bilinear interpolation.
    Connect clips top-to-bottom for storyboard-style sequencing."""

    CATEGORY = "BSAI"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "combine"
    DESCRIPTION = "Concatenate video clips sequentially. All clips resized to first clip's resolution."

    MAX_CLIPS = 16

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(1, cls.MAX_CLIPS + 1):
            optional[f"clip_{i}"] = ("IMAGE", {"tooltip": f"Video clip {i} (IMAGE batch)"})
        return {
            "required": {},
            "optional": optional,
        }

    def combine(self, **kwargs):
        clips = []
        for i in range(1, self.MAX_CLIPS + 1):
            key = f"clip_{i}"
            if key in kwargs and kwargs[key] is not None:
                clips.append(kwargs[key])

        if not clips:
            return (torch.zeros(1, 64, 64, 3, dtype=torch.float32),)

        if len(clips) == 1:
            return (clips[0],)

        target_h, target_w = clips[0].shape[1], clips[0].shape[2]
        result = []
        for clip in clips:
            if clip.shape[1] != target_h or clip.shape[2] != target_w:
                x = clip.permute(0, 3, 1, 2).float()
                x = torch.nn.functional.interpolate(
                    x, size=(target_h, target_w),
                    mode='bilinear', align_corners=False
                )
                clip = x.permute(0, 2, 3, 1)
            result.append(clip)

        combined = torch.cat(result, dim=0)
        total_frames = combined.shape[0]
        duration = total_frames / 24.0
        print(f"[BSAI VideoCombiner] Combined {len(clips)} clips -> {total_frames} frames ({duration:.1f}s @ 24fps)")
        return (combined,)

    @classmethod
    def IS_CHANGED(cls):
        return float("nan")


class BSAI_AudioCombiner:
    """Combine multiple audio streams into a single continuous audio track.
    All audio is resampled to match the first stream's sample rate."""

    CATEGORY = "BSAI"
    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "combine"
    DESCRIPTION = "Concatenate audio streams sequentially. All streams resampled to first stream's sample rate."

    MAX_INPUTS = 16

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(1, cls.MAX_INPUTS + 1):
            optional[f"audio_{i}"] = ("AUDIO", {"tooltip": f"Audio stream {i}"})
        return {
            "required": {},
            "optional": optional,
        }

    def combine(self, **kwargs):
        audios = []
        for i in range(1, cls.MAX_INPUTS + 1):
            key = f"audio_{i}"
            if key in kwargs and kwargs[key] is not None:
                audios.append(kwargs[key])

        if not audios:
            return ({"waveform": torch.zeros(2, 1, 44100, dtype=torch.float32), "sample_rate": 44100},)

        if len(audios) == 1:
            return (audios[0],)

        target_sr = audios[0]["sample_rate"]
        waveforms = []
        for audio in audios:
            wf = audio["waveform"]
            sr = audio["sample_rate"]
            if sr != target_sr:
                old_len = wf.shape[-1]
                new_len = int(old_len * target_sr / sr)
                wf = torch.nn.functional.interpolate(
                    wf.float(), size=new_len,
                    mode='linear', align_corners=False
                )
            waveforms.append(wf.float())

        min_channels = min(wf.shape[1] if wf.dim() >= 2 else 1 for wf in waveforms)
        normalized = []
        for wf in waveforms:
            if wf.dim() == 2:
                wf = wf.unsqueeze(0)
            if wf.shape[1] > min_channels:
                wf = wf[:, :min_channels, :]
            normalized.append(wf)

        combined = torch.cat(normalized, dim=-1)
        duration = combined.shape[-1] / target_sr
        print(f"[BSAI AudioCombiner] Combined {len(audios)} streams -> {combined.shape[-1]} samples ({duration:.1f}s @ {target_sr}Hz)")
        return ({"waveform": combined, "sample_rate": target_sr},)

    @classmethod
    def IS_CHANGED(cls):
        return float("nan")


NODE_CLASS_MAPPINGS = {
    "BSAI_VideoCombiner": BSAI_VideoCombiner,
    "BSAI_AudioCombiner": BSAI_AudioCombiner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BSAI_VideoCombiner": "BSAI Video Combiner",
    "BSAI_AudioCombiner": "BSAI Audio Combiner",
}
