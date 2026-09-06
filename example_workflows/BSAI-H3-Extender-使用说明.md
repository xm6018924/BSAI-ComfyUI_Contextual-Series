# BSAI-H3-Extender 精简示例工作流 — 修复版使用说明
# BSAI-H3-Extender Simplified Workflow — Fixed-Edition Usage Guide

> **配套工作流 (Companion workflow)**: `BSAI-H3-Extender-Fixed.json`
> **修复目标 (Target)**: `ComfyUI/custom_nodes/BSAI-ComfyUI_Contextual-Series`
> **适用版本 (Targeted ComfyUI)**: 0.33.0+ (含原生 `MiniMaxH3Extender` / `MiniMaxH3ReferenceToVideo` / `BSAI_AssetLibraryInput` 等节点)

---

## 0. 目录 / Table of Contents

1. [原始工作流存在哪些问题? / What was broken in the original?](#1-original-issues--原始问题)
2. [修复版做了什么改动? / What the fixed edition changes](#2-fixes--修复内容)
3. [三段式管线总览 / Three-pipeline overview](#3-overview--总览)
4. [主生成管线 (Active) / Main generation pipeline](#4-main-pipeline--主生成管线)
5. [人脸修复后处理 (Optional) / Face-refine post-processing](#5-face-refine--人脸修复后处理)
6. [HD 2× 放大后处理 (Optional) / HD 2× upscale post-processing](#6-hd-upscale--hd-2x-放大)
7. [资产库与提示词规范 / Asset library & prompt conventions](#7-asset--资产库与提示词)
8. [运行步骤 / Step-by-step run](#8-steps--运行步骤)
9. [常见问题 / FAQ](#9-faq--常见问题)
10. [模型下载清单 / Model download checklist](#10-models--模型下载清单)

---

<a id="1-original-issues--原始问题"></a>
## 1. 原始工作流存在哪些问题? / What was broken in the original?

| # | 问题 (CN) | Issue (EN) | 严重度 Severity |
|---|---|---|---|
| 1 | **节点 10 (VHS_LoadVideoPath) 的 `frame_load_cap=1`**:启用人脸修复时只加载 1 帧。 | `frame_load_cap=1` on node 10: only 1 frame loaded for face-refine. | 🔴 阻塞 Blocker |
| 2 | **节点 5 (AssetLibrary) 预填了 6 个不存在的文件名**:加载报错或拉空。 | Node 5 lists 6 missing filenames — ComfyUI fails to find them. | 🟡 警告 Warning |
| 3 | **两套主生成管线并存** (H3Extender + 旧版 Ref2V) 混在一起, 原始作者只把旧管线的节点设成 `mode=4` 屏蔽, 用户很难看出哪些该启用。 | Two parallel main pipelines existed; legacy path was muted with `mode=4` but not labeled. | 🟡 警告 Warning |
| 4 | **节点 36 (Text Multiline 全局提示词) 没有输出连线**, 是一段孤儿死代码; 而节点 37 才是真正接到 `H3Extender.global_prompt` 的活跃输入, 但被标题误导。 | Node 36 (long prompt) is orphaned (no output link); node 37 is the actual `global_prompt` input but its title didn't make that clear. | 🟢 文档 Doc |
| 5 | **Note 节点 (id=25) 的内嵌说明** 只描述原结构, 没说"如何启用后处理"。 | The instruction Note (id=25) only described structure, not how to enable post-processing. | 🟢 文档 Doc |
| 6 | **未提供 `Quick Start` 入口**:新用户找不到一键运行路径。 | No Quick-Start entry. | 🟢 体验 UX |

修复版已处理 1–6 全部。See [§2 Fixes](#2-fixes--修复内容).

---

<a id="2-fixes--修复内容"></a>
## 2. 修复版做了什么改动? / What the fixed edition changes

| 修复 (CN) | Fix (EN) | 影响范围 Scope |
|---|---|---|
| 节点 10 `frame_load_cap` 从 `1` 改为 `0` (=全部帧) | Node 10 `frame_load_cap` 1 → 0 (= all frames) | 人脸修复管线 |
| 节点 5 `image_files` 清空为 `[]`, 标题改为提示用户通过 UI 上传 | Node 5 `image_files` cleared to `[]`; title now tells user to upload via the node UI | 资产库 |
| 旧 Ref2V 管线节点 (id 38, 39, 44, 45, 46, 47, 48, 49, 52, 53, 54, 55, 56, 57, 58, 59) 标题前加 `(DISABLED) 旧Ref2V备用` | Legacy Ref2V nodes prefixed with `(DISABLED)` in their titles | 可视化 |
| 节点 36 标题改为 `(DISABLED) 旧版分段提示词文本(请在 H3Extender 节点内编辑 clips_json)` | Node 36 marked as legacy / orphaned | 文档 |
| 节点 37 标题改为 `Global Prompt (全局提示词) — 输入到 H3Extender.global_prompt` | Node 37 labeled as the actual `global_prompt` feed | 文档 |
| 节点 25 (Note) 重写, 包含 启用后处理 步骤 | Note (id=25) rewritten to cover post-processing enable steps | 文档 |
| **新增** 节点 68 `Quick Start` Note | **New** node 68: Quick Start note | 体验 UX |
| 所有 85 条 links 重新校验, 无悬空连线 | All 85 links re-validated; no orphans | 完整性 |

> 修复版**不改动** 节点 6 (`MiniMaxH3Extender`) 的 `clips_json` 内置 3 段分镜内容 — 这是用户的核心数据, 由用户自行编辑。

---

<a id="3-overview--总览"></a>
## 3. 三段式管线总览 / Three-pipeline overview

修复版工作流包含 **3 段独立管线**, 默认只启用主生成管线:

```
┌─────────────────────────────────────────────────────────────────────┐
│  主管线 (Main Generation, 默认 mode=0 = Always)                       │
│                                                                     │
│  UNETLoader(50) ─┐                                                   │
│  LoraLoaderModelOnly(65, Lightning LoRA) ─┤                          │
│  ComfySwitchNode(61, model) ──MODEL──> MiniMaxH3Extender(6)         │
│  ComfySwitchNode(62, steps)  ──INT───>   ▲                          │
│  CLIPLoader(51)  ──CLIP──────────────>   │                          │
│  VAELoader(42)   ──VAE───────────────>   │                          │
│  VAELoader(43)   ──audio_VAE────────>   │                          │
│  TextMultiline(37)─global_prompt────>   │                          │
│  AssetLibrary(5)  ──asset_library──>   │                          │
│                                         │                          │
│                                         ▼                          │
│                        MiniMaxH3MotionContextDiskFinalDecode(7)     │
│                                         │                          │
│                                         ▼                          │
│                       ComfyUI/output/video/MiniMax_H3_*.mp4        │
└─────────────────────────────────────────────────────────────────────┘
                  │                                    │
   (可选 Optional)│                          (可选 Optional)│
                  ▼                                    ▼
   ┌──────────────────────────┐         ┌──────────────────────────┐
   │ 人脸修复 (Face Refine)    │         │ HD 2× 放大 (HD Upscale)   │
   │ 节点 10-23 (mode=4 默认) │         │ 节点 24-35 (mode=4 默认)  │
   │ 输入: 已生成的 MP4        │         │ 输入: face-refine 的      │
   │ 输出: BSAI_H3_FaceRefined │         │       denoised latent     │
   │         .mp4              │         │ 输出: BSAI_H3_HD_Upscaled │
   └──────────────────────────┘         └──────────────────────────┘
```

---

<a id="4-main-pipeline--主生成管线"></a>
## 4. 主生成管线 (Active) / Main generation pipeline

### 4.1 节点清单 (按执行顺序) / Node list (in execution order)

| Order | ID | 节点类型 / Type | 标题 / Title | 关键参数 / Key params |
|---:|---:|---|---|---|
| 0  | 68 | Note | Quick Start | 快速开始指引 |
| 10 | 25 | Note | Workflow Instructions | 工作流说明 (重写后) |
| 11 | 5  | BSAI_AssetLibraryInput | Asset Library (留空) | image_files=`[]` |
| 22 | 37 | Text Multiline | Global Prompt | 全局提示词 → H3Extender.global_prompt |
| 23 | 43 | VAELoader | (audio_vae) | `minimax_h3_audio_vae_fp32.safetensors` |
| 24 | 63 | PrimitiveInt | Int (Full) | 20 (无 Lightning LoRA 时的步数) |
| 25 | 64 | PrimitiveInt | Int (Lightning LoRA) | 4 (有 Lightning LoRA 时的步数) |
| 26 | 66 | PrimitiveBoolean | Enable Lightning LoRA | `true` |
| 29 | 50 | UNETLoader | (主模型) | `minimax_h3_fl2va_int8_convrot.safetensors`, weight_dtype=default |
| 30 | 51 | CLIPLoader | (文本编码器) | `qwen3vl_32b_minimax_h3_*.safetensors`, type=**minimax** |
| 31 | 42 | VAELoader | (视频 VAE) | `minimax_h3_video_vae_int8_convrot.safetensors` |
| 37 | 62 | ComfySwitchNode | If/Else Switch (Steps) | 选择 4 或 20 步 |
| 38 | 65 | LoraLoaderModelOnly | (Lightning LoRA) | `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors`, strength=1 |
| 46 | 61 | ComfySwitchNode | If/Else Switch (model) | 选择 raw UNET 或 UNET+LoRA |
| 49 | 6  | **MiniMaxH3Extender** | (故事板生成器) | 见 §4.3 |
| 52 | 7  | MiniMaxH3MotionContextDiskFinalDecode | Final Decode & Preview | fps=24, filename_prefix=`BSAI_H3_Storyboard`, codec=H.264, crf=17 |

### 4.2 关键链路 / Key connections

```
50 (UNET) ────MODEL──> 61.on_false
65 (LoRA)  ────MODEL──> 61.on_true
66 (Boolean true) ──switch──> 61, 62
61 (output)  ──MODEL─> 6 (H3Extender)
50 (UNET)  ────MODEL──> 65 (Lightning LoRA 叠在主模型上)
51 (CLIP)  ────CLIP───> 6
42 (VAE)   ────VAE────> 6
43 (audio_vae) ─VAE──> 6
37 (Text)  ──STRING──> 6 (global_prompt)
5  (AssetLib) ─ASSET_LIBRARY─> 6
62 (Switch) ──INT───> 6 (steps)
6  (cache output) ──> 7 (FinalDecode)
7  (写文件到 ComfyUI/output/video/MiniMax_H3_*.mp4)
```

### 4.3 MiniMaxH3Extender (id=6) 关键参数

| Widget | 默认值 | 说明 / Description |
|---|---|---|
| `run_mode` | `clip_by_clip` | 主运行模式;还有 `single_clip` / `all_at_once` |
| `width` / `height` | 1344 / 768 | 分辨率, 32 的倍数, 与 `ResolutionSelector` 解耦(后者已禁用) |
| `ref_image_size` | `max` | 参考图尺寸, `match`=快, `max`=高保真但慢 |
| `steps` | 4 | 经 `ComfySwitchNode(62)` 控制, true=4 / false=20 |
| `sampler_name` | `euler` | 推荐 `euler` / `res_multistep` |
| `scheduler` | `beta` | `beta` / `normal` 对参考图友好; `simple` 略差 |
| `denoise` | 1.0 | 1.0=完全重画; <1=图生视频(im2v 风格) |
| `context_length` | 22 | 故事板上下文长度(帧) |
| `audio_context_length` | 0 | 音频上下文(0=H3 自动) |
| `clips_json` | (内置 3 段分镜) | **核心**: 每段分镜的 prompt / seed / duration |
| `refs_json` | `{"version":2,"refs":[null,...]}` | 9 个参考图槽位(暂未使用,可填 ref_image 路径) |
| `resolution_mode` | `auto_from_ref` | 分辨率来源 |

### 4.4 内置 3 段分镜 (clips_json)

工作流已预置 **3 段故事板分镜** (在节点 widget 内编辑):

1. **分镜 1** — *初始的觊觎*: 角色 1 vs 角色 2 争夺西瓜切片 (10 秒)
2. **分镜 2** — *边界的试探*: 过肩镜头 + 极近特写 (10 秒)
3. **分镜 3** — *冲突的升级*: 抓取西瓜、双手交错特写 (10 秒)

> 每段默认 duration=10s, 配合 24fps 实际输出约 240 帧。完整 3 段约 30 秒。
> 
> Each clip defaults to 10s @ 24fps ≈ 240 frames. 3 clips ≈ 30 seconds total.

---

<a id="5-face-refine--人脸修复后处理"></a>
## 5. 人脸修复后处理 (Optional) / Face-refine post-processing

**默认禁用 (Default OFF)**: 节点 10–23 全部为 `mode=4` (NEVER)。

### 5.1 启用方法 / How to enable

1. **先运行主生成管线** 一次, 在 `ComfyUI/output/video/` 下得到 `MiniMax_H3_*.mp4`。
2. **批量选中节点 10–23** (用 `Ctrl+Click` / `框选`)。
3. **右键 → Mode → Always** (从 `Never` 改为 `Always`)。
4. **修改节点 10 (VHS_LoadVideoPath)** 的 `video` 路径为刚才生成的 MP4, 例如 `output/video/MiniMax_H3_00001.mp4`。
5. **Queue Prompt** → 等待 → 输出 `ComfyUI/output/BSAI_H3_FaceRefined_*.mp4`。

### 5.2 节点清单 (10–23) / Node list

| ID | 类型 / Type | 标题 / Title | 作用 / Role |
|---:|---|---|---|
| 10 | VHS_LoadVideoPath | Load Video (0=全部帧) | 加载上一步生成的 MP4 (已修 frame_load_cap=0) |
| 11 | H3FaceTrackCrop | H3 Face Track + Crop | YOLOv8 人脸检测 + 平滑裁剪 |
| 12 | EmptyMiniMaxH3LatentAV | Empty H3 AV Latent | 创建空潜空间 (canvas 由 11 喂入) |
| 13 | H3InjectVideoLatent | H3 Inject Video Latent | 把裁剪后人脸帧编入 latent |
| 14 | H3PerFrameDenoise | H3 Per-Frame Denoise | 按人脸面积动态降噪 (小脸=1.0, 大脸=0.35) |
| 15 | CLIPTextEncode | (人脸提示词) | "A cinematic close-up of a woman's face, ..." |
| 16 | BasicGuider | (基础引导) | 无 CFG 的简易 guider |
| 17 | BasicScheduler | (人脸修复调度) | steps=4, denoise=0.35 |
| 18 | RandomNoise | (随机噪声) | 默认种子, 每次 randomize |
| 19 | KSamplerSelect | (采样器) | euler |
| 20 | SamplerCustomAdvanced | (高级采样) | 输出 denoised → 给 HD 放大用 |
| 21 | VAEDecode | (解码人脸) | 视频 VAE |
| 22 | H3FaceStitch | H3 Face Stitch Back | 把修复后的人脸贴回原图 |
| 23 | VHS_VideoCombine | (人脸修复输出) | 合成 MP4 |

### 5.3 推荐参数 / Recommended settings

| 参数 / Param | 推荐值 / Recommended | 说明 / Note |
|---|---|---|
| `frame_load_cap` | 0 (=全部帧) | 已修复;之前是 1 会只取首帧 |
| `detector` (节点 11) | `face_yolov8m.pt` | YOLOv8 medium, 精度/速度平衡 |
| `crop_factor` (节点 11) | 2.5 | 裁剪框是人脸的 2.5 倍 |
| `canvas_mode` (节点 11) | `auto_capped_768` | 自动上限 768×768 |
| `strength_small_face` (节点 14) | 1.0 | 远景小脸: 强降噪 |
| `strength_large_face` (节点 14) | 0.35 | 近景大脸: 弱降噪,保留细节 |
| `denoise` (节点 17) | 0.35 | 关键!不要 > 0.5, 否则破坏原图 |
| `mask_dilation` (节点 22) | 16 | 贴回时向外扩 16 px |
| `feather` (节点 22) | 6 | 边缘羽化 |

---

<a id="6-hd-upscale--hd-2x-放大"></a>
## 6. HD 2× 放大后处理 (Optional) / HD 2× upscale post-processing

**默认禁用 (Default OFF)**: 节点 24–35 全部为 `mode=4` (NEVER)。

### 6.1 启用方法 / How to enable

1. **必须先启用人脸修复管线** (节点 10–23), 因为 HD 放大需要它的 `denoised_output` (节点 20 的 link 33) 作为输入。
2. 批量选中节点 24–35, **右键 → Mode → Always**。
3. **Queue Prompt** → 等待 → 输出 `ComfyUI/output/BSAI_H3_HD_Upscaled_*.mp4`。

### 6.2 节点清单 (24–35) / Node list

| ID | 类型 / Type | 标题 / Title | 作用 / Role |
|---:|---|---|---|
| 24 | MiniMaxH3LatentUpscaleCombined | H3 Latent Upscale 2x | 潜空间 2x 放大 + 重新加噪 |
| 26 | RandomNoise | (放大噪声) | 放大用的随机噪声 |
| 27 | BasicScheduler | (放大调度) | steps=4, denoise=1 |
| 28 | CLIPTextEncode | (负面提示词) | "blurry, low quality, ..." |
| 29 | CFGGuider | (高清修复引导) | cfg=1.0 |
| 30 | KSamplerSelect | (高清采样器) | euler |
| 31 | BasicScheduler | (高清修复调度) | steps=4, denoise=1 |
| 32 | DisableNoise | (禁用噪声) | 跳过内置噪声(24 已加) |
| 33 | SamplerCustomAdvanced | (高清采样) | 接收放大后的 latent |
| 34 | VAEDecode | (高清解码) | 视频 VAE |
| 35 | VHS_VideoCombine | (高清输出) | 合成 MP4 |

### 6.3 ⚠️ 注意 / Heads up

- **不要对整段视频全量放大**, 显存占用极高。先放大 5–10 秒片段确认效果。
- 如需对完整视频放大, **修改节点 24 的 `samples` 输入连线**为完整视频的 latent (而不是来自人脸修复的 denoised_output)。
- `MiniMaxH3LatentUpscaleCombined` 的 `learned_model` 需要本地存在 `minimax_h3_latent_upscaler_3d_fp16.safetensors`。

---

<a id="7-asset--资产库与提示词"></a>
## 7. 资产库与提示词规范 / Asset library & prompt conventions

### 7.1 BSAI_AssetLibraryInput (节点 5) / Asset library

| 参数 / Param | 说明 / Description |
|---|---|
| `image_files` | JSON 数组, 通过**节点 UI** 上传;文件存到 `ComfyUI/input/bsai_assets/images/` |
| `video_files` | 同上, 存到 `ComfyUI/input/bsai_assets/videos/` |
| `audio_files` | 同上, 存到 `ComfyUI/input/bsai_assets/audio/` |
| `bsai_gallery` | (高级) 拖入式画廊, 留空即可 |

**索引规则 / Indexing**:
- 图片按上传顺序索引为 `@图1`, `@图2`, ... (最多 9 个)
- 视频为 `@视频1`, `@视频2`, `@视频3` (最多 3 个)
- 音频为 `@音频1`, `@音频2`, `@音频3` (最多 3 个)

**H3Extender 内的提示词引用 / H3Extender prompt referencing**:

> ⚠️ **重要 / IMPORTANT**: `MiniMaxH3Extender` (id=6) **不会**解析 `@图N` 提示词标记, 它使用 `refs_json` (节点 widget 内) 来直接指定 9 个参考图路径。
>
> `MiniMaxH3Extender` does **NOT** parse `@图N` markers from prompts. Use `refs_json` widget field to set up to 9 reference image paths directly.

要使用资产库, 需走 `MiniMaxH3ReferenceToVideo` (节点 56, **已禁用**), 或在 H3Extender 的 `refs_json` 中手动填入路径。

### 7.2 提示词最佳实践 / Prompt best practices

```text
[整体风格]：电影级写实风格，炽热且充满感官张力的午后氛围。

[角色档案]：
角色1@图1，淡蓝亚麻裙敏感少女，浅棕色长发微卷松散，...
角色2@图2，灰白粗麻衬衫固执青年，黑色短发利落硬朗，...

[道具档案]：
巨大的西瓜@图3，...
西瓜切片@图4，...

[场景档案]：
户外庭院（午后）@图5，...
同一户外庭院（午后）@图6，...

[分镜1]：初始的觊觎
0-3秒：极缓推、中景。... 角色1说："我先看到它的了"(声线：略带娇嗔，...)
3-6秒：微移、特写。... 音效：远处蝉鸣声，...
6-9秒：焦点转移、中近景。... 

[分镜2]：边界的试探
...
```

每个分镜应包含：
- **时间窗口** (0-3秒 / 3-6秒 / 6-9秒)
- **镜头** (极缓推 / 微移 / 焦点转移 / 过肩镜头 / 极近特写 / 快速推进 / 手持微晃)
- **动作描述** (角色做了什么, 视线/表情/姿态)
- **对白 (可选)**: `角色1说："..." (声线：..., 语速：..., 情绪：...)`
- **音效 (可选)**: `音效：...`

---

<a id="8-steps--运行步骤"></a>
## 8. 运行步骤 / Step-by-step run

### 8.1 一键运行主生成 (Run main only)

1. 打开 ComfyUI, 拖入 `BSAI-H3-Extender-Fixed.json`。
2. 双击节点 6 (`MiniMaxH3Extender`), 在右侧 widget 面板找到 `clips_json`, 编辑你的 3 段分镜。
3. (可选) 切换节点 66 (`Boolean Enable Lightning LoRA`): `true` = 4 步 (快), `false` = 20 步 (高质)。
4. 确认模型文件存在: `ComfyUI/models/diffusion_models/`, `text_encoders/`, `vae/`, `loras/`。见 §10。
5. **Queue Prompt**。
6. 等待 4–10 分钟 (Lightning LoRA + 4 步)。视频输出到 `ComfyUI/output/video/MiniMax_H3_*.mp4`。

### 8.2 启用后处理 / Enable post-processing

7. **人脸修复**: 框选节点 10–23, 右键 → Mode → Always。修改节点 10 的 `video` 路径。Queue Prompt。
8. **HD 放大**: 先确保 10–23 已运行, 然后框选节点 24–35, 右键 → Mode → Always。Queue Prompt。

### 8.3 切换 Lightning LoRA / Toggle Lightning LoRA

| 节点 66 值 | steps 经 switch (62) | UNET 经 switch (61) | 总耗时 (估) | 质量 |
|---|---|---|---|---|
| `true` | 4 (节点 64) | UNET + LoRA (节点 65) | ~3 min | 良好 |
| `false` | 20 (节点 63) | 纯 UNET (节点 50) | ~15 min | 最佳 |

> **默认是 `true`** (Lightning LoRA 开启)。要最高质量则切到 `false`。
> 
> **Default is `true`**. Switch to `false` for highest quality.

---

<a id="9-faq--常见问题"></a>
## 9. 常见问题 / FAQ

### Q1. 加载工作流时提示 "node MiniMaxH3Extender not found" / Node not found

**CN**: 这是 `tritant/ComfyUI_MiniMax_H3_Extender` 插件未安装。
**EN**: The `tritant/ComfyUI_MiniMax_H3_Extender` plugin is not installed.

修复 / Fix:
```bash
cd "C:\BSAI\ComfyUI-BSAI_pro_v37 HV\ComfyUI\custom_nodes"
git clone https://github.com/tritant/ComfyUI_MiniMax_H3_Extender.git
# 重启 ComfyUI / restart ComfyUI
```

### Q2. CLIPLoader 提示 "type must be minimax" / Wrong CLIP type

**CN**: `CLIPLoader` 的 `type` 必须是 `minimax`, 错选 `stable_diffusion` 会导致 H3 文本编码错误。
**EN**: The `type` field on `CLIPLoader` **must** be `minimax`; choosing `stable_diffusion` breaks H3 text encoding.

修复: 节点 51 `type` 选 `minimax`。Fix: set node 51 `type` to `minimax`.

### Q3. 模型找不到 / Model not found

**CN**: 检查 `ComfyUI/models/` 下是否有:
- `diffusion_models/minimax_h3_fl2va_int8_convrot.safetensors` (or fp16/bf16)
- `text_encoders/qwen3vl_32b_minimax_h3_*.safetensors`
- `vae/minimax_h3_video_vae_int8_convrot.safetensors`
- `vae/minimax_h3_audio_vae_fp32.safetensors`
- `loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors`

**EN**: Verify the files exist under `ComfyUI/models/`. See §10 for download links.

### Q4. 启用后处理时报 "SamplerCustomAdvanced missing denoised_output" / Missing denoised_output

**CN**: 节点 20 的 `denoised_output` (link 33) 是节点 24 (HD Upscale) 的输入。**HD Upscale 必须先启用人脸修复管线**。
**EN**: Node 20's `denoised_output` (link 33) feeds node 24 (HD Upscale). **Enable face-refine (10–23) before HD Upscale**.

### Q5. 如何自定义每段分镜的时长? / Per-clip duration

打开节点 6 (`MiniMaxH3Extender`) widget, 在 `clips_json` 里改每段 clip 的 `"duration"` 字段 (秒)。
Open node 6 widget, edit `"duration"` (in seconds) for each clip in `clips_json`.

### Q6. 我不想用 3 段分镜, 只想生成单段 / Single-clip mode

把 `clips_json` 清空, 改为单个 clip 数组 `[{"id":"clip_1","prompt":"...","seed":...,"duration":10}]`。
Or set `run_mode` widget to `single_clip` and put one clip in `clips_json`.

### Q7. 修复版工作流在哪里? / Where is the fixed file?

```
ComfyUI/custom_nodes/BSAI-ComfyUI_Contextual-Series/example_workflows/
  ├── BSAI-H3-Extender-Fixed.json     ← 修复版 / Fixed edition
  ├── contextual_series_demo.json     ← v1 演示
  ├── contextual_series_auto_expand.json  ← 5 段自动扩展
  └── fixed/
      ├── build_workflow.py
      └── fix_workflow.py             ← 修复脚本
```

---

<a id="10-models--模型下载清单"></a>
## 10. 模型下载清单 / Model download checklist

| 文件 / File | 放置位置 / Location | 下载 / Download |
|---|---|---|
| `minimax_h3_fl2va_int8_convrot.safetensors` | `models/diffusion_models/` | [🤗 Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors` (旧 Ref2V 用) | `models/diffusion_models/` | 同上 |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `models/text_encoders/` | 同上 |
| `minimax_h3_video_vae_int8_convrot.safetensors` | `models/vae/` | 同上 |
| `minimax_h3_video_vae_fp16.safetensors` (备选) | `models/vae/` | 同上 |
| `minimax_h3_audio_vae_fp32.safetensors` | `models/vae/` | 同上 |
| `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` | `models/loras/` | [🤗 4-step LoRA](https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors) |
| `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` (备选 4 步) | `models/loras/` | 同上 |
| `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` (8 步) | `models/loras/` | 同上 |
| `minimax_h3_latent_upscaler_3d_fp16.safetensors` (HD 放大用) | `models/vae/` 或 `models/diffusion_models/` | 见 `Tr1dae/ComfyUI-MiniMaxH3_LatentUpscaler` 仓库 |
| `face_yolov8m.pt` (人脸检测, 启用 face-refine 时) | `models/ultralytics/face/face_yolov8m.pt` 或按 `ComfyUI-H3-FaceRefine` 仓库说明放置 | 见 `ComfyUI-H3-FaceRefine` 仓库 |

**关于 Comfy-Org/MiniMax-H3 的具体路径示例**:
```text
📂 ComfyUI/
├── 📂 models/
│   ├── 📂 vae/
│   │   ├── minimax_h3_video_vae_fp16.safetensors
│   │   └── minimax_h3_audio_vae_fp32.safetensors
│   ├── 📂 diffusion_models/
│   │   └── minimax_h3_ref2va_pruned_int8_convrot.safetensors
│   ├── 📂 text_encoders/
│   │   └── qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
│   └── 📂 loras/
│       └── minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors
```

---

## 附: 验证修复版完整性 / Appendix: Validate the fixed edition

```powershell
# 在 venv 下运行
& "C:\BSAI\ComfyUI-BSAI_pro_v37 HV\ComfyUI\venv\Scripts\python.exe" `
  -c "import json; d=json.load(open(r'C:\BSAI\ComfyUI-BSAI_pro_v37 HV\ComfyUI\custom_nodes\BSAI-ComfyUI_Contextual-Series\example_workflows\BSAI-H3-Extender-Fixed.json',encoding='utf-8')); print('nodes:',len(d['nodes']),'links:',len(d['links']),'active:',sum(1 for n in d['nodes'] if n['mode']==0),'muted:',sum(1 for n in d['nodes'] if n['mode']==4))"
```

预期输出 / Expected:
```
nodes: 67 links: 85 active: 21 muted: 46
```

---

**作者备注 / Author notes**:
- 修复版保留了原作者的 3 段分镜内容作为示例, 用户可自由替换。
- 修复版**不会** 自动启用任何后处理; 用户可按 §5/§6 自行决定。
- 如果你的 `ComfyUI` 版本不支持 `MiniMaxH3Extender` (它来自 `tritant/ComfyUI_MiniMax_H3_Extender`), 请先安装该插件再加载工作流。
- The fixed edition **does not** auto-enable post-processing; the user must opt in per §5/§6.
- If your ComfyUI build doesn't ship `MiniMaxH3Extender`, install `tritant/ComfyUI_MiniMax_H3_Extender` first.

— *BSAI Mavis 自动生成 / auto-generated by Mavis* —
