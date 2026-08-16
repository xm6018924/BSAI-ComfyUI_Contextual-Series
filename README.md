# BSAI-ComfyUI_Contextual Series

> Extract reference frames from a previously generated video to maintain **visual consistency** (characters, scenes, props, lighting, colors) across sequential video generations.
>
> 从上一次生成的视频中提取参考帧，在连续视频生成中保持**视觉一致性**（人物、场景、道具、光线、色彩）。

Designed for **MiniMax H3 Omni Reference** (全能参考) mode, which accepts up to 9 reference images to preserve visual continuity between clips.

专为 **MiniMax H3 全能参考** 模式设计，该模式最多接受 9 张参考图片，用于在片段之间保持视觉连续性。

---

## Problem Solved | 解决的问题

When generating a series of video clips (e.g. a multi-scene short drama), each clip is generated independently. Without a reference bridge, characters, environments, and visual style can drift between clips. This node solves that by:

在连续生成一系列视频片段（如多场景短剧）时，每个片段都是独立生成的。如果没有参考桥接，人物、环境和视觉风格可能会在片段之间发生漂移。本节点通过以下方式解决这一问题：

1. Taking the **last N frames** (or any custom range) from clip 1's output
   — 从片段 1 的输出中提取**最后 N 帧**（或任意自定义范围）
2. Subsampling to a configurable maximum (default 9, matching H3's limit)
   — 子采样到可配置的最大数量（默认 9，匹配 H3 的限制）
3. Outputting them as reference images for clip 2's generation
   — 将其作为参考图片输出，用于片段 2 的生成
4. Optionally **saving to disk** so frames persist across separate ComfyUI sessions
   — 可选**保存到磁盘**，使帧在跨 ComfyUI 会话之间持久保留

---

## Nodes | 节点

### BSAI-ComfyUI_Contextual Series (Extract) | 上下文系列提取

| Parameter | Type | Default | Description | 说明 |
|---|---|---|---|---|
| `images` | IMAGE | — | Batch of frames from the previous video generation (e.g. output of `BSAI Video To Images` or `VideoHelperSuite LoadVideo`) | 上一次视频生成的帧批次（如 `BSAI Video To Images` 或 `VideoHelperSuite LoadVideo` 的输出） |
| `selection_mode` | Enum | `last_n` | `last_n` / `first_n` / `middle_n` / `custom_range` | `last_n`（最后N帧）/ `first_n`（最前N帧）/ `middle_n`（中间N帧）/ `custom_range`（自定义范围） |
| `frame_count` | INT | 15 | Number of frames to extract (used by last_n / first_n / middle_n) | 要提取的帧数（用于 last_n / first_n / middle_n 模式） |
| `start_frame` | INT | 0 | Start frame index (0-based) for `custom_range` mode | `custom_range` 模式的起始帧索引（从 0 开始） |
| `end_frame` | INT | 0 | End frame index (exclusive); 0 = up to last frame | 结束帧索引（不包含）；0 = 到最后一帧 |
| `max_output_frames` | INT | 9 | Maximum frames after subsampling. H3 Omni Reference accepts ≤ 9 images | 子采样后的最大输出帧数。H3 全能参考最多接受 9 张图片 |
| `sampling_method` | Enum | `even` | `even` (evenly distributed) or `sequential` (first N of selected range) | `even`（均匀分布）或 `sequential`（取选中范围的前 N 帧） |
| `save_frames` | BOOLEAN | False | Save extracted frames as PNG for cross-session reuse | 将提取的帧保存为 PNG，供跨会话复用 |
| `output_subdir` | STRING | `contextual_series` | Subdirectory under ComfyUI output folder | ComfyUI 输出目录下的子目录名 |
| `filename_prefix` | STRING | `frame` | Prefix for saved files (e.g. `frame_00000.png`) | 保存文件的前缀（如 `frame_00000.png`） |

**Outputs | 输出:** `images` (IMAGE), `frame_count` (INT)

---

### BSAI Contextual Series Load | 上下文系列加载

| Parameter | Type | Default | Description | 说明 |
|---|---|---|---|---|
| `directory` | STRING | — | Directory containing saved frames. Accepts absolute path or name relative to ComfyUI output/input folder | 包含已保存帧的目录。接受绝对路径或相对于 ComfyUI 输出/输入目录的名称 |
| `filename_prefix` | STRING | `frame` | Only load files starting with this prefix | 仅加载以此前缀开头的文件 |
| `max_frames` | INT | 9 | Maximum frames to load | 最大加载帧数 |
| `sampling_method` | Enum | `even` | `even` / `sequential` / `all` | `even`（均匀采样）/ `sequential`（顺序取前N个）/ `all`（全部加载） |

**Outputs | 输出:** `images` (IMAGE), `frame_count` (INT)

---

## Example Workflow | 示例工作流

A complete standard workflow is included in `example_workflows/contextual_series_demo.json`. Load it in ComfyUI via **Load** button to see a full two-stage demo:
> 完整的标准工作流示例位于 `example_workflows/contextual_series_demo.json`。在 ComfyUI 中通过 **Load** 按钮加载即可查看完整的两阶段演示：

```
Stage 1 (T2V)                    Contextual Series              Stage 2 (Ref2V)
┌─────────────────────┐          ┌──────────────────┐          ┌─────────────────────┐
│ MiniMaxH3ImageToVideo│ → IMAGE →│ BSAI_Contextual  │ → IMAGE →│ MiniMaxH3Reference  │
│ (Text-to-Video)      │          │ Series Extract    │          │ ToVideo (Ref2V)     │
│ ↓                    │          │ (last 15 frames   │          │ ↓                   │
│ VAEDecode → SaveVideo│          │  → 9 ref images)  │          │ VAEDecode → SaveVideo│
└─────────────────────┘          └──────────────────┘          └─────────────────────┘
```

- **31 nodes, 46 links** — includes model loaders, Turbo LoRA (4-step), resolution selector, two full generation pipelines, and the Contextual Series extraction node
- **31 个节点，46 条连线** — 包含模型加载器、Turbo LoRA（4步）、分辨率选择器、两条完整生成管线和 Contextual Series 提取节点

---

## Installation | 安装

### Method 1: ComfyUI-Manager (recommended) | 方式一：ComfyUI-Manager（推荐）

1. Open ComfyUI-Manager → Custom Nodes Manager
   — 打开 ComfyUI-Manager → 自定义节点管理器
2. Search for `BSAI-ComfyUI_Contextual-Series`
   — 搜索 `BSAI-ComfyUI_Contextual-Series`
3. Click Install
   — 点击安装
4. Restart ComfyUI
   — 重启 ComfyUI

### Method 2: Manual | 方式二：手动安装

1. Clone this repo into `ComfyUI/custom_nodes/`:
   — 将仓库克隆到 `ComfyUI/custom_nodes/` 目录：
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/xm6018924/BSAI-ComfyUI_Contextual-Series.git
   ```
2. Install dependencies:
   — 安装依赖：
   ```bash
   pip install -r BSAI-ComfyUI_Contextual-Series/requirements.txt
   ```
3. Restart ComfyUI
   — 重启 ComfyUI

---

## Usage Examples | 使用示例

### Same-Session Workflow (Run 1 → Extract → Run 2) | 同一会话工作流（第一次运行 → 提取 → 第二次运行）

```
[MiniMax H3 Text-to-Video]  →  [BSAI Video To Images]  →  [BSAI-ComfyUI_Contextual Series]
                                                              ↓ images
                                                    [MiniMax H3 Reference (全能参考)]
                                                              ↓
                                                    [Save Video]
```

1. **Run 1**: Generate clip 1 with MiniMax H3 Text-to-Video (or First/Last Frame)
   — **第一次运行**：用 MiniMax H3 文生视频（或首/尾帧）生成片段 1
2. Convert the video output to IMAGE frames (using `BSAI Video To Images` or `VHS LoadVideo`)
   — 将视频输出转换为 IMAGE 帧（使用 `BSAI Video To Images` 或 `VHS LoadVideo`）
3. Connect to **BSAI-ComfyUI_Contextual Series** → set `selection_mode = last_n`, `frame_count = 15`
   — 连接到 **BSAI-ComfyUI_Contextual Series** → 设置 `selection_mode = last_n`，`frame_count = 15`
4. Connect the output `images` to **MiniMax H3 Reference** node's `reference_images` input
   — 将输出的 `images` 连接到 **MiniMax H3 全能参考** 节点的 `reference_images` 输入
5. **Run 2**: Generate clip 2 with the reference frames maintaining visual consistency
   — **第二次运行**：使用参考帧生成片段 2，保持视觉一致性

### Cross-Session Workflow (Save → Load) | 跨会话工作流（保存 → 加载）

**Session 1 | 会话 1:**
```
[Generate Video] → [Video To Images] → [BSAI-ComfyUI_Contextual Series]  (save_frames = True)
```

**Session 2 | 会话 2:**
```
[BSAI Contextual Series Load] → images → [MiniMax H3 Reference (全能参考)] → [Save Video]
```

### Custom Frame Range | 自定义帧范围

For referencing the middle 30-45 frames of a 120-frame video:
— 引用 120 帧视频的中间 30-45 帧：

- `selection_mode` = `custom_range`
- `start_frame` = 30
- `end_frame` = 45
- `max_output_frames` = 9 (subsample evenly to 9 images | 均匀子采样为 9 张图片)
- `sampling_method` = `even`

> Users can freely specify any frame range, such as the last 10-15 frames, middle 30-45 frames, or frames 50-65, etc.
>
> 用户可以自由指定任意帧范围，如最后 10-15 帧、中间 30-45 帧、或第 50-65 帧等。

---

## MiniMax H3 Omni Reference Integration | MiniMax H3 全能参考集成

The MiniMax H3 model supports an "Omni Reference" (全能参考) input mode that accepts:
> MiniMax H3 模型支持"全能参考"输入模式，接受以下输入：

- **Images | 图片**: ≤ 9 reference images | ≤ 9 张参考图片
- **Videos | 视频**: ≤ 3 segments (2-15s each) | ≤ 3 段（每段 2-15 秒）
- **Audio | 音频**: ≤ 3 segments | ≤ 3 段

This node outputs IMAGE batches sized to the 9-image limit. Connect the output to the H3 Reference node's `reference_images` input. The reference images will guide the model to preserve:
> 本节点输出符合 9 张图片限制的 IMAGE 批次。将输出连接到 H3 全能参考节点的 `reference_images` 输入。参考图片将引导模型保持以下一致性：

- Character appearance and clothing | 人物外观与服装
- Scene composition and environment | 场景构图与环境
- Lighting and color palette | 光线与色彩风格
- Props and object details | 道具与物体细节

---

## Requirements | 环境要求

| Requirement | Version |
|---|---|
| ComfyUI | latest | 最新版 |
| Python | ≥ 3.10 |
| PyTorch | — |
| NumPy | — |
| Pillow | — |

---

## License | 许可证

MIT
