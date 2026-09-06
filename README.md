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

## v2.0 New Feature: Storyboard Clip Management System | v2.0 新功能：分镜片段管理系统

Version 2.0 adds a complete storyboard-style clip management system with asset library, subtitle rendering, and media combining:
> v2.0 新增完整的分镜式片段管理系统，包含资产库、字幕渲染和媒体合成：

- **Asset Library** — Load unlimited images/videos/audio from directories, reference by @图N notation
  — **资产库** — 从目录加载不限数量的图片/视频/音频，用 @图N 引用
- **Clip Composer** — Define clips with prompt, 旁白/对白 subtitles, audio mode; arrange top-to-bottom like a storyboard
  — **片段编排** — 定义片段的提示词、旁白/对白字幕、音频模式；从上到下排列如分镜脚本
- **Subtitle System** — Font from C:\Windows\Fonts, customizable color/size/position, two types: 旁白 and 对白
  — **字幕系统** — 从 C:\Windows\Fonts 选择字体，自定义颜色/大小/位置，支持旁白和对白两种类型
- **Media Combiner** — Concatenate all clips into one video with synchronized audio
  — **媒体合成** — 将所有片段合成为一个视频，同步音频

### BSAI Asset Library Input | 资产库输入

| Parameter | Type | Default | Description | 说明 |
|---|---|---|---|---|
| `image_directory` | STRING | — | Directory containing images (.png,.jpg,.jpeg,.webp,.bmp) | 图片目录 |
| `video_directory` | STRING | — | Directory containing videos (.mp4,.avi,.mov,.mkv,.webm) | 视频目录 |
| `audio_directory` | STRING | — | Directory containing audio (.wav,.mp3,.flac,.ogg,.aac) | 音频目录 |

**Outputs:** `asset_library` (ASSET_LIBRARY) — Assets indexed as 图1,图2,... / 视频1,... / 音频1,...

### BSAI Asset Reference Selector | 资产引用选择器

| Parameter | Type | Default | Description | 说明 |
|---|---|---|---|---|
| `asset_library` | ASSET_LIBRARY | — | Asset library from BSAI_AssetLibraryInput | 资产库 |
| `prompt` | STRING | — | Prompt with @图N / @视频N / @音频N references | 带 @图N / @视频N / @音频N 引用的提示词 |

**Outputs:** `ref_images` (IMAGE batch), `ref_video_0..2` (IMAGE), `ref_video_audio_0..2` (AUDIO), `ref_audio_0..2` (AUDIO), `formatted_prompt` (STRING with H3 `<Picture>`/`<Video>`/`<Audio>` tags)

The selector parses @图N/@视频N/@音频N notation, loads referenced assets, and converts the prompt to H3 native notation.
> 选择器解析 @图N/@视频N/@音频N 标记，加载引用的资产，并将提示词转换为 H3 原生标记。

### BSAI Image Batch Splitter | 图片批次分割器

Splits an IMAGE batch into individual images (up to 9) for MiniMaxH3ReferenceToVideo's ref_image_0..8 inputs.
> 将 IMAGE 批次分割为单独图片（最多9张），用于 MiniMaxH3ReferenceToVideo 的 ref_image_0..8 输入。

### BSAI Clip Composer | 片段编排器

| Parameter | Type | Default | Description | 说明 |
|---|---|---|---|---|
| `prompt` | STRING | — | Generation prompt. Use 【旁白】/【对白】 markers for subtitle extraction | 生成提示词。用【旁白】/【对白】标记提取字幕 |
| `narration` | STRING | — | 旁白字幕 (manual input) | 旁白字幕（手动输入） |
| `dialogue` | STRING | — | 对白字幕 (manual input) | 对白字幕（手动输入） |
| `subtitle_source` | Enum | `manual` | `manual` or `extract_from_prompt` | `manual`（手动）或 `extract_from_prompt`（从提示词提取） |
| `audio_mode` | Enum | `H3_auto` | `H3_auto` (H3 generated) or `custom` (user-provided) | `H3_auto`（H3生成）或 `custom`（自定义） |
| `duration` | FLOAT | 5.0 | Clip duration in seconds (snapped to H3 17n+5 grid) | 片段时长（秒，对齐到 H3 17n+5 帧格） |
| `width` | INT | 1344 | Video width (multiple of 32) | 视频宽度（32的倍数） |
| `height` | INT | 768 | Video height (multiple of 32) | 视频高度（32的倍数） |
| `seed` | INT | 0 | Generation seed | 生成种子 |

**Outputs:** `clip_info` (CLIP_INFO)

**Subtitle extraction markers | 字幕提取标记:**
- `【旁白】text` or `旁白：text` → narration | 旁白
- `【对白】text` or `对白：text` → dialogue | 对白

### BSAI Clip Sequencer | 片段序列器

Collects up to 16 clips (clip_1 through clip_16) into a CLIP_SEQUENCE. Arrange clips top-to-bottom in the workflow like a storyboard script.
> 收集最多16个片段（clip_1 到 clip_16）为 CLIP_SEQUENCE。在工作流中从上到下排列片段，如分镜脚本。

### BSAI Subtitle Config | 字幕配置

| Parameter | Type | Default | Description | 说明 |
|---|---|---|---|---|
| `font_name` | Enum | `msyh.ttc` | Font from C:\Windows\Fonts dropdown | 从 C:\Windows\Fonts 选择字体 |
| `font_size` | INT | 36 | Font size in pixels | 字体大小（像素） |
| `narration_color` | STRING | `#FFFFFF` | 旁白 color (hex) | 旁白颜色（十六进制） |
| `dialogue_color` | STRING | `#FFEE88` | 对白 color (hex) | 对白颜色（十六进制） |
| `narration_position` | Enum | `top` | 旁白 position: top/center/bottom | 旁白位置 |
| `dialogue_position` | Enum | `bottom` | 对白 position: top/center/bottom | 对白位置 |
| `background_box` | BOOLEAN | True | Semi-transparent background behind text | 文字后方的半透明背景 |
| `margin` | INT | 30 | Margin from screen edge (pixels) | 距屏幕边缘的边距（像素） |

**Outputs:** `subtitle_config` (SUBTITLE_CONFIG)

### BSAI Subtitle Renderer | 字幕渲染器

Renders 旁白/对白 subtitles on video frames. Accepts CLIP_INFO (for text) or direct text input.
> 在视频帧上渲染旁白/对白字幕。接受 CLIP_INFO（获取文本）或直接文本输入。

| Parameter | Type | Description | 说明 |
|---|---|---|---|
| `images` | IMAGE | Video frames to render subtitles on | 要渲染字幕的视频帧 |
| `subtitle_config` | SUBTITLE_CONFIG | Subtitle styling | 字幕样式 |
| `clip_info` (optional) | CLIP_INFO | Clip with narration/dialogue text | 含旁白/对白文本的片段信息 |
| `narration` (optional) | STRING | Direct narration text (if no clip_info) | 直接旁白文本（无 clip_info 时） |
| `dialogue` (optional) | STRING | Direct dialogue text (if no clip_info) | 直接对白文本（无 clip_info 时） |

**Outputs:** `images` (IMAGE with burned-in subtitles)

### BSAI Video Combiner | 视频合成器

Concatenates up to 16 video clips (clip_1..clip_16) into one continuous video. All clips resized to first clip's resolution.
> 将最多16个视频片段（clip_1..clip_16）拼接为一个连续视频。所有片段缩放到第一个片段的分辨率。

### BSAI Audio Combiner | 音频合成器

Concatenates up to 16 audio streams (audio_1..audio_16) into one continuous track. All streams resampled to first stream's sample rate.
> 将最多16个音频流（audio_1..audio_16）拼接为一个连续音轨。所有音频流重采样到第一个流的采样率。

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

### Auto-Expand Story Workflow (5-Stage) | 自动扩展剧情工作流（5段循环）

An advanced 5-stage auto-expanding workflow is included in `example_workflows/contextual_series_auto_expand.json`. It generates 5 consecutive video clips from a single story input, with each segment's prompt optimized by **BSAI MiniMAX H3 Prompt** node and visual consistency maintained by **BSAI-ComfyUI_Contextual Series**:
> 高级5段自动扩展工作流位于 `example_workflows/contextual_series_auto_expand.json`。它从单个故事输入生成5段连续视频片段，每段提示词由 **BSAI MiniMAX H3 Prompt** 节点优化，视觉一致性由 **BSAI-ComfyUI_Contextual Series** 保持：

```
首段提示词                    续写提示词2                   续写提示词3                   续写提示词4                   续写提示词5
    │                            │                            │                            │                            │
    ▼                            ▼                            ▼                            ▼                            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Stage 1  │→│ Stage 2  │→│ Stage 3  │→│ Stage 4  │→│ Stage 5  │
│   T2V    │  │  Ref2V   │  │  Ref2V   │  │  Ref2V   │  │  Ref2V   │
│ (8s)     │  │ (10s)    │  │ (10s)    │  │ (10s)    │  │ (10s)    │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘
     │ Extract      │ Extract      │ Extract      │ Extract
     │ (9 imgs)     │ (9 imgs)     │ (9 imgs)     │ (9 imgs)
     └──────────────┴──────────────┴──────────────┘
                    Reference frames chain
```

- **90 nodes, 148 links** — 1 T2V stage + 4 Ref2V stages, each with BSAI MiniMAX H3 Prompt optimization and Contextual Series extraction
- **90 个节点，148 条连线** — 1个T2V阶段 + 4个Ref2V阶段，每段都有 BSAI MiniMAX H3 Prompt 优化和 Contextual Series 提取

**How it works | 工作原理:**

1. User inputs a complete story, split into **first segment prompt** + **continuation prompts** (each ≤15s)
   — 用户输入完整故事，拆分为**首段提示词** + **续写提示词**（每段≤15秒）
2. Each segment goes through **BSAI MiniMAX H3 Prompt** for professional prompt optimization
   — 每段通过 **BSAI MiniMAX H3 Prompt** 优化为专业 MiniMax H3 提示词
3. Stage 1 generates clip 1 via **T2V**, then **Contextual Series Extract** extracts 9 reference frames
   — Stage 1 通过 **T2V** 生成片段1，然后提取9张参考帧
4. Stages 2-5 use **Ref2V** with reference frames from the previous stage to maintain visual consistency
   — Stage 2-5 使用前一阶段的参考帧通过 **Ref2V** 生成，保持视觉一致性

**To customize | 自定义:**
- Edit the TextBox/Text Multiline nodes to input your own story segments
  — 编辑 TextBox/Text Multiline 节点输入自定义故事片段
- Adjust Duration nodes (default: 8s for Stage 1, 10s for Stages 2-5)
  — 调整 Duration 节点（默认：Stage 1 为 8秒，Stage 2-5 为 10秒）
- To add more stages: duplicate a Stage 2-5 block and chain the extract output
  — 要增加更多段：复制 Stage 2-5 模块并链接提取输出

### Storyboard Demo Workflow (v2.0 All Nodes) | 分镜演示工作流（v2.0 全节点）

A complete v2.0 storyboard demo is included in `example_workflows/bsai_storyboard_demo.json`. It demonstrates all 11 plugin nodes with a two-clip storyboard:
> 完整的 v2.0 分镜演示位于 `example_workflows/bsai_storyboard_demo.json`。它用一个两片段分镜演示插件的全部 11 个节点：

- **16 nodes, 14 links, 6 groups** — Asset Library → Clip Composers → Asset Ref Selectors → Image Splitters → Subtitle Config → Subtitle Renderers → Clip Sequencer → Video/Audio Combiners
- **16 个节点，14 条连线，6 个分组** — 资产库 → 片段编排 → 资产引用 → 图片分割 → 字幕配置 → 字幕渲染 → 片段序列 → 视频/音频合成

```
Row 1 — Clip 1 (片段1):
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│ AssetLibrary│→│ ClipComposer│  │AssetRefSel. │→│ImgBatchSplit│  │  LoadImage  │
│             │  │  (prompt +  │  │ (@图1 parse)│  │→ image_0..8 │  │ (placeholder│
└────────────┘  │  旁白/对白)  │  └────────────┘  └────────────┘  │  for H3 vid) │
                → clip_info ─────────────────────────────────────→ └────────────┘
                  ↓                                                ↓
Row 2 — Clip 2 (片段2):                                              │
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│             │→│ ClipComposer│  │AssetRefSel. │→│ImgBatchSplit│  │  LoadImage  │
│             │  │  (prompt +  │  │ (@图1@图2)  │  │             │  │ (placeholder│
└────────────┘  │  旁白/对白)  │  └────────────┘  └────────────┘  │  for H3 vid) │
                → clip_info ─────────────────────────────────────→ └────────────┘
                  ↓                  ↓                                      ↓
Row 3 — Subtitles + Assembly:                                        ↓
┌────────────┐  ┌────────────┐               ┌────────────┐  ┌────────────┐
│SubtitleConfig│→│SubtitleRend.│←images──────│            │  │VideoCombiner│
│(font,color) │→│  Clip 1     │←clip_info───│  (from Row1)│  │ clip_1 ←───┘
└────────────┘  └──────┬─────┘               └────────────┘  │ clip_2 ←───┐
                ┌────────────┐               ┌────────────┐  └────────────┘
                │SubtitleRend.│←images──────│            │  ┌────────────┐
                │  Clip 2     │←clip_info───│  (from Row2)│  │AudioCombiner│
                └──────┬─────┘               └────────────┘  │ (no inputs  │
                       └──────────────────────────────────→   │  connected) │
                                                          └────────────┘
```

**Step-by-step setup | 逐步设置:**

1. **Prepare asset directory | 准备资产目录**
   - Create folder `ComfyUI/input/bsai_assets/images/` and place reference images there
   — 创建 `ComfyUI/input/bsai_assets/images/` 文件夹并放入参考图片

2. **Load the workflow | 加载工作流**
   - In ComfyUI, click **Load** → select `bsai_storyboard_demo.json`
   — 在 ComfyUI 中点击 **Load** → 选择 `bsai_storyboard_demo.json`

3. **Configure Asset Library (Node 1) | 配置资产库（节点1）**
   - Set `image_directory` to your asset folder path (e.g., `input/bsai_assets/images`)
   — 将 `image_directory` 设为你的资产目录路径（如 `input/bsai_assets/images`）
   - Optionally set `video_directory` and `audio_directory` for video/audio assets
   — 可选设置 `video_directory` 和 `audio_directory` 加载视频/音频资产

4. **Edit clip prompts (Nodes 2, 6) | 编辑片段提示词（节点2, 6）**
   - Write prompt text with `@图N` references and `【旁白】`/`【对白】` subtitle markers
   — 编写带 `@图N` 引用和 `【旁白】`/`【对白】` 字幕标记的提示词
   - Example: `@图1 A woman walking in neon city\n【旁白】The city never sleeps\n【对白】Where am I`
   — 示例：`@图1 一个女人走在霓虹城市\n【旁白】这座城市从不沉睡\n【对白】我在哪里`

5. **Configure subtitle style (Node 10) | 配置字幕样式（节点10）**
   - Select font from dropdown (auto-populated from `C:\Windows\Fonts`)
   — 从下拉菜单选择字体（从 `C:\Windows\Fonts` 自动填充）
   - Adjust colors: 旁白 white `#FFFFFF`, 对白 yellow `#FFEE88`
   — 调整颜色：旁白白色 `#FFFFFF`，对白黄色 `#FFEE88`

6. **Replace placeholders (Nodes 5, 9) | 替换占位符（节点5, 9）**
   - Replace `LoadImage` nodes with `VAEDecode` output from your H3 generation pipeline
   — 将 `LoadImage` 节点替换为 H3 生成管线的 `VAEDecode` 输出
   - Or keep `LoadImage` for testing subtitle rendering without H3 generation
   — 或保留 `LoadImage` 用于在不生成 H3 视频的情况下测试字幕渲染

7. **Connect to H3 generation | 连接到 H3 生成**
   - Connect `ImageBatchSplitter` outputs `image_0..8` → `MiniMaxH3ReferenceToVideo` `ref_image_0..8`
   — 将 `ImageBatchSplitter` 输出 `image_0..8` → `MiniMaxH3ReferenceToVideo` 的 `ref_image_0..8`
   - Connect `AssetRefSelector` `ref_video_0..2` → H3 `ref_video_0..2` (if using video references)
   — 将 `AssetRefSelector` 的 `ref_video_0..2` → H3 的 `ref_video_0..2`（如使用视频引用）
   - Use `AssetRefSelector` `formatted_prompt` output as H3 prompt input
   — 使用 `AssetRefSelector` 的 `formatted_prompt` 输出作为 H3 提示词输入

8. **Final assembly | 最终合成**
   - `BSAI_VideoCombiner` concatenates all clips → connect to `SaveVideo` or `CreateVideo`
   — `BSAI_VideoCombiner` 拼接所有片段 → 连接到 `SaveVideo` 或 `CreateVideo`
   - `BSAI_AudioCombiner` concatenates audio → connect H3 `VAEDecodeAudio` outputs here
   — `BSAI_AudioCombiner` 拼接音频 → 将 H3 `VAEDecodeAudio` 输出连接到此处

**Subtitle markers reference | 字幕标记参考:**

| Marker | Type | Default Color | Default Position | 标记 | 类型 | 默认颜色 | 默认位置 |
|---|---|---|---|---|---|---|---|
| `【旁白】text` | Narration | `#FFFFFF` (white) | top | `【旁白】文本` | 旁白 | `#FFFFFF`（白色） | 顶部 |
| `【对白】text` | Dialogue | `#FFEE88` (yellow) | bottom | `【对白】文本` | 对白 | `#FFEE88`（黄色） | 底部 |
| `旁白：text` | Narration | (same) | (same) | `旁白：文本` | 旁白 | （同上） | （同上） |
| `对白：text` | Dialogue | (same) | (same) | `对白：文本` | 对白 | （同上） | （同上） |

**Asset reference syntax | 资产引用语法:**

| Syntax | Meaning | Max | 语法 | 含义 | 上限 |
|---|---|---|---|---|---|
| `@图1` | Reference image 1 | 9 (`@图1`..`@图9`) | `@图1` | 引用图片1 | 9（`@图1`..`@图9`） |
| `@视频1` | Reference video 1 | 3 (`@视频1`..`@视频3`) | `@视频1` | 引用视频1 | 3（`@视频1`..`@视频3`） |
| `@音频1` | Reference audio 1 | 3 (`@音频1`..`@音频3`) | `@音频1` | 引用音频1 | 3（`@音频1`..`@音频3`） |

> The selector auto-converts `@图N` → `<Picture N>`, `@视频N` → `<Video N>`, `@音频N` → `<Audio N>` in the formatted prompt output for H3 Omni Reference.
>
> 选择器自动将 `@图N` → `<Picture N>`、`@视频N` → `<Video N>`、`@音频N` → `<Audio N>` 转换为 H3 全能参考的格式化提示词输出。

**Clip duration frame grid | 片段时长帧格:**

Duration in seconds is auto-snapped to the H3 `17n+5` frame grid (at 24fps):
> 时长（秒）自动对齐到 H3 `17n+5` 帧格（24fps）：

| Duration (s) | Frames | | 时长（秒） | 帧数 |
|---|---|---|---|---|
| 0.25 | 5 | | 0.25 | 5 |
| 1.0 | 22 | | 1.0 | 22 |
| 2.0 | 39 | | 2.0 | 39 |
| 3.0 | 56 | | 3.0 | 56 |
| 5.0 | 90 | | 5.0 | 90 |
| 10.0 | 175 | | 10.0 | 175 |

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

### Storyboard Clip Workflow (v2.0) | 分镜片段工作流 (v2.0)

A complete storyboard workflow using the new v2.0 nodes:
> 使用 v2.0 新节点的完整分镜工作流：

```
┌──────────────────────┐
│ BSAI_AssetLibraryInput│ → asset_library
│ (load images/videos/  │
│  audio from folders)  │
└──────────────────────┘
                          ↓
┌──────────────────────┐    ┌──────────────────────┐
│ BSAI_AssetRefSelector │    │ BSAI_ClipComposer #1  │
│ (parse @图N in prompt)│ ← │ (prompt, 旁白, 对白)   │
│ → ref_images, videos,  │    │ → clip_info            │
│   audios, fmt_prompt   │    └──────────────────────┘
└───────────┬───────────┘
            ↓
┌──────────────────────┐    ┌──────────────────────┐
│ BSAI_ImageBatchSplitter│   │ BSAI_SubtitleConfig    │
│ → ref_image_0..8       │   │ (font, color, position)│
└───────────┬───────────┘    └──────────┬─────────────┘
            ↓                            ↓
┌──────────────────────┐    ┌──────────────────────┐
│ MiniMaxH3Reference    │    │ BSAI_SubtitleRenderer  │
│ ToVideo               │    │ (render 旁白/对白)      │
│ → conditioning +      │    │ → IMAGE with subtitles  │
│   AV latent            │    └──────────┬─────────────┘
│ → Sampler → VAE Decode│               │
└───────────┬───────────┘               │
            → IMAGE ───────────────────→ ┘
                                          ↓
┌──────────────────────┐    ┌──────────────────────┐
│ BSAI_VideoCombiner    │    │ BSAI_AudioCombiner    │
│ (concat all clips)    │    │ (concat all audio)    │
│ → final IMAGE         │    │ → final AUDIO         │
└──────────────────────┘    └──────────────────────┘
```

**Per-clip flow | 每个片段的流程:**
1. Create a BSAI_ClipComposer for each clip (arrange top-to-bottom in workflow)
   — 为每个片段创建一个 BSAI_ClipComposer（在工作流中从上到下排列）
2. Write prompt with @图1 @图3 references and 【旁白】/【对白】 subtitle markers
   — 编写带 @图1 @图3 引用和【旁白】/【对白】字幕标记的提示词
3. BSAI_AssetRefSelector loads referenced assets → connect to MiniMaxH3ReferenceToVideo
   — BSAI_AssetRefSelector 加载引用的资产 → 连接到 MiniMaxH3ReferenceToVideo
4. Generate video with MiniMax H3 → VAE Decode → BSAI_SubtitleRenderer
   — 用 MiniMax H3 生成视频 → VAE Decode → BSAI_SubtitleRenderer
5. Connect all clip outputs to BSAI_VideoCombiner and BSAI_AudioCombiner
   — 将所有片段输出连接到 BSAI_VideoCombiner 和 BSAI_AudioCombiner

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
| Python | >= 3.10 |
| PyTorch | — |
| NumPy | — |
| Pillow | — |
| OpenCV (optional) | — | For video loading in asset library | 用于资产库视频加载 |
| torchaudio (optional) | — | For audio loading | 用于音频加载 |

---

## License | 许可证

MIT
