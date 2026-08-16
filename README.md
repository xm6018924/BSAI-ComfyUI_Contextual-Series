# BSAI-ComfyUI_Contextual Series

Extract reference frames from a previously generated video to maintain **visual consistency** (characters, scenes, props, lighting, colors) across sequential video generations.

Designed for **MiniMax H3 Omni Reference** (全能参考) mode, which accepts up to 9 reference images to preserve visual continuity between clips.

## Problem Solved

When generating a series of video clips (e.g. a multi-scene short drama), each clip is generated independently. Without a reference bridge, characters, environments, and visual style can drift between clips. This node solves that by:

1. Taking the **last N frames** (or any custom range) from clip 1's output
2. Subsampling to a configurable maximum (default 9, matching H3's limit)
3. Outputting them as reference images for clip 2's generation
4. Optionally **saving to disk** so frames persist across separate ComfyUI sessions

## Nodes

### BSAI-ComfyUI_Contextual Series (Extract)

| Parameter | Type | Default | Description |
|---|---|---|---|
| `images` | IMAGE | — | Batch of frames from the previous video generation (e.g. output of `BSAI Video To Images` or `VideoHelperSuite LoadVideo`) |
| `selection_mode` | Enum | `last_n` | `last_n` / `first_n` / `middle_n` / `custom_range` |
| `frame_count` | INT | 15 | Number of frames to extract (used by last_n / first_n / middle_n) |
| `start_frame` | INT | 0 | Start frame index (0-based) for `custom_range` mode |
| `end_frame` | INT | 0 | End frame index (exclusive); 0 = up to last frame |
| `max_output_frames` | INT | 9 | Maximum frames after subsampling. H3 Omni Reference accepts ≤ 9 images |
| `sampling_method` | Enum | `even` | `even` (evenly distributed) or `sequential` (first N of selected range) |
| `save_frames` | BOOLEAN | False | Save extracted frames as PNG for cross-session reuse |
| `output_subdir` | STRING | `contextual_series` | Subdirectory under ComfyUI output folder |
| `filename_prefix` | STRING | `frame` | Prefix for saved files (e.g. `frame_00000.png`) |

**Outputs:** `images` (IMAGE), `frame_count` (INT)

### BSAI Contextual Series Load

| Parameter | Type | Default | Description |
|---|---|---|---|
| `directory` | STRING | — | Directory containing saved frames. Accepts absolute path or name relative to ComfyUI output/input folder |
| `filename_prefix` | STRING | `frame` | Only load files starting with this prefix |
| `max_frames` | INT | 9 | Maximum frames to load |
| `sampling_method` | Enum | `even` | `even` / `sequential` / `all` |

**Outputs:** `images` (IMAGE), `frame_count` (INT)

## Installation

### Method 1: ComfyUI-Manager (recommended)

1. Open ComfyUI-Manager → Custom Nodes Manager
2. Search for `BSAI-ComfyUI_Contextual-Series`
3. Click Install
4. Restart ComfyUI

### Method 2: Manual

1. Clone this repo into `ComfyUI/custom_nodes/`:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/xm6018924/BSAI-ComfyUI_Contextual-Series.git
   ```
2. Install dependencies:
   ```bash
   pip install -r BSAI-ComfyUI_Contextual-Series/requirements.txt
   ```
3. Restart ComfyUI

## Usage Examples

### Same-Session Workflow (Run 1 → Extract → Run 2)

```
[MiniMax H3 Text-to-Video]  →  [BSAI Video To Images]  →  [BSAI-ComfyUI_Contextual Series]
                                                              ↓ images
                                                    [MiniMax H3 Reference (全能参考)]
                                                              ↓
                                                    [Save Video]
```

1. **Run 1**: Generate clip 1 with MiniMax H3 Text-to-Video (or First/Last Frame)
2. Convert the video output to IMAGE frames (using `BSAI Video To Images` or `VHS LoadVideo`)
3. Connect to **BSAI-ComfyUI_Contextual Series** → set `selection_mode = last_n`, `frame_count = 15`
4. Connect the output `images` to **MiniMax H3 Reference** node's `reference_images` input
5. **Run 2**: Generate clip 2 with the reference frames maintaining visual consistency

### Cross-Session Workflow (Save → Load)

**Session 1:**
```
[Generate Video] → [Video To Images] → [BSAI-ComfyUI_Contextual Series]  (save_frames = True)
```

**Session 2:**
```
[BSAI Contextual Series Load] → images → [MiniMax H3 Reference (全能参考)] → [Save Video]
```

### Custom Frame Range

For referencing the middle 30-45 frames of a 120-frame video:
- `selection_mode` = `custom_range`
- `start_frame` = 30
- `end_frame` = 45
- `max_output_frames` = 9 (subsample evenly to 9 images)
- `sampling_method` = `even`

## MiniMax H3 Omni Reference Integration

The MiniMax H3 model supports an "Omni Reference" (全能参考) input mode that accepts:
- **Images**: ≤ 9 reference images
- **Videos**: ≤ 3 segments (2-15s each)
- **Audio**: ≤ 3 segments

This node outputs IMAGE batches sized to the 9-image limit. Connect the output to the H3 Reference node's `reference_images` input. The reference images will guide the model to preserve:
- Character appearance and clothing
- Scene composition and environment
- Lighting and color palette
- Props and object details

## Requirements

- ComfyUI (latest)
- Python ≥ 3.10
- PyTorch
- NumPy
- Pillow

## License

MIT
