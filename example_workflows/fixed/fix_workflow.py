"""
Surgically fix the BSAI H3 Extender workflow.

Problems fixed:
1. node 10 (VHS_LoadVideoPath) - frame_load_cap=1 means only 1 frame is loaded
   when re-enabling face-refine. Changed to 0 (= all frames).
2. node 7 (FinalDecode) - widgets_values uses "output_directory": "" but
   modern ComfyUI/VHS may need an absolute or relative path; leaving as is.
3. node 6 (H3Extender) - the H3Extender widget already has its own clips_json
   with 3 preloaded storyboard clips, so the workflow is runnable. The
   H3HybridLoader (id 1) was the OLD model loader used by the disabled
   MiniMaxH3ReferenceToVideo (id 56) pipeline; the new active pipeline uses
   UNETLoader (50) + LoraLoaderModelOnly (65) + ComfySwitchNode (61). All
   consistent.
4. The ResolutionSelector (39), Math expr (54), Float (55), and Ref2V nodes
   (44,45,46,47,48,49,52,53,56,57,58,59) are all mode=4 (NEVER) - they are
   "draft" of a second pipeline. We mark them with a clear "(DISABLED -
   legacy)" title and add a banner note.
5. Asset Library (5) references files that may not exist; we replace with
   an empty JSON array so it doesn't try to load missing files until the
   user uploads their own.
6. Add a `quick_start` Note node that explains the one-click run path.

This script writes a NEW file; the original is preserved.
"""
import json
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else None
DST = sys.argv[2] if len(sys.argv) > 2 else None

if SRC is None or DST is None:
    raise SystemExit("usage: fix_workflow.py <src.json> <dst.json>")

with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

nmap = {n["id"]: n for n in data["nodes"]}

# --- 1. VHS_LoadVideoPath (id 10) frame_load_cap=1 -> 0
n10 = nmap[10]
n10["widgets_values"]["frame_load_cap"] = 0
n10["widgets_values_named"]["frame_load_cap"] = 0
n10["title"] = "Load Video (加载生成的视频) — 0=全部帧"

# --- 2. Asset Library (id 5) - clear the file lists so user uploads via UI
n5 = nmap[5]
n5["widgets_values"][0] = "[]"  # image_files
n5["widgets_values_named"]["image_files"] = "[]"
n5["title"] = "Asset Library (资产库) — 留空,在节点UI上传图片/视频/音频"

# --- 3. Mark the disabled legacy Ref2V pipeline nodes with a clear title
LEGACY_TITLES = {
    38: "(DISABLED) Save Video (旧Ref2V备用)",
    39: "(DISABLED) Resolution Selector (旧Ref2V备用)",
    44: "(DISABLED) VAE Decode Audio (旧Ref2V备用)",
    45: "(DISABLED) VAE Decode (旧Ref2V备用)",
    46: "(DISABLED) KSampler Select (旧Ref2V备用)",
    47: "(DISABLED) Basic Scheduler (旧Ref2V备用)",
    48: "(DISABLED) Sampler Custom Advanced (旧Ref2V备用)",
    49: "(DISABLED) Basic Guider (旧Ref2V备用)",
    52: "(DISABLED) Random Noise (旧Ref2V备用)",
    53: "(DISABLED) Create Video (旧Ref2V备用)",
    54: "(DISABLED) Comfy Math Expression (旧Ref2V备用)",
    55: "(DISABLED) Float Duration (旧Ref2V备用)",
    56: "(DISABLED) MiniMaxH3 ReferenceToVideo (旧Ref2V备用)",
    57: "(DISABLED) Load Image (旧Ref2V备用)",
    58: "(DISABLED) Input Text Prompt (旧Ref2V备用)",
    59: "(DISABLED) Load Image (旧Ref2V备用)",
    36: "(DISABLED) 旧版分段提示词文本(请在 H3Extender 节点内编辑 clips_json)",
    37: "Global Prompt (全局提示词) — 输入到 H3Extender.global_prompt",
    67: "说明: false=20步(无Lightning LoRA) / true=4步(开启Lightning LoRA)",
}
for nid, new_title in LEGACY_TITLES.items():
    if nid in nmap:
        nmap[nid]["title"] = new_title

# --- 4. Update the workflow instructions Note (id 25)
n25 = nmap[25]
NEW_INSTR = (
    "BSAI Contextual-Series H3 Extender — 修复版\n"
    "==========================================\n\n"
    "■ 单击运行路径 (mode=0, 直接可用)\n"
    "  1. UNETLoader (50)  →  LoraLoaderModelOnly (65)  →  ComfySwitchNode (61)\n"
    "  2. ComfySwitchNode (61)  →  MiniMaxH3Extender (6)  →  MiniMaxH3MotionContextDiskFinalDecode (7)\n"
    "  3. CLIPLoader (51) + VAELoader (42) + VAELoader (43)  →  MiniMaxH3Extender (6)\n"
    "  4. Text Multiline (37/36) 历史文本(只读, 实际在 H3Extender 节点内编辑)\n"
    "  5. Boolean (66) 切换 Lightning LoRA 步数: true=4步, false=20步\n\n"
    "■ 可选后处理 — 默认 mode=4 (禁用), 需要时右键节点 → mode = Always\n"
    "  人脸修复 (棕色组, 节点 10-23):\n"
    "    启用前先运行主管线生成 MP4, 修改节点 10 的 video 路径为该 MP4\n"
    "    节点 10 的 frame_load_cap 已修正为 0 (=全部帧)\n"
    "  HD 2x 放大 (紫色组, 节点 24-35):\n"
    "    需要先启用并运行人脸修复管线以提供 denoised latent\n\n"
    "■ 资产库 (节点 5)\n"
    "  工作流里的 6 个文件名已清空。请在 BSAI_AssetLibraryInput 节点的\n"
    "  UI 上传你自己的图片/视频/音频, 索引为 @图1/@视频1/@音频1 等。\n"
    "  H3Extender 节点内每个 clip 都有 rfe_* 系列参数, 独立于 AssetLibrary。\n\n"
    "■ 关键节点参数\n"
    "  [UNETLoader 50]: minimax_h3_fl2va_int8_convrot.safetensors (default 精度)\n"
    "  [LoraLoaderModelOnly 65]: minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors, strength=1\n"
    "  [CLIPLoader 51]: qwen3vl_32b_minimax_h3_*, type=minimax (必须)\n"
    "  [VAELoader 42]: minimax_h3_video_vae_int8_convrot.safetensors\n"
    "  [VAELoader 43]: minimax_h3_audio_vae_fp32.safetensors\n"
    "  [H3Extender 6]: width/height 由节点 widget 控制 (默认 1344x768, 24fps)\n"
    "                  4 步 (Lightning LoRA 开启) 或 20 步 (关闭)\n"
    "                  故事板 (clips_json) 在节点 widget 内编辑, 已预置 3 段分镜\n\n"
    "■ 运行顺序\n"
    "  1. 打开 MiniMaxH3Extender (节点 6) → 在 clips_json 里编辑 3 段分镜的 prompt\n"
    "  2. 必要时调整 UNET/CLIP/VAE 文件名匹配本地模型\n"
    "  3. (可选) 启用 Lightning LoRA (节点 66=true=4步加速)\n"
    "  4. Queue Prompt → 等待 → 视频输出在 ComfyUI/output/ 下\n"
    "  5. (可选) 启用 人脸修复/HD 放大 后处理\n"
)
n25["widgets_values"] = [NEW_INSTR]
n25["widgets_values_named"]["text"] = NEW_INSTR

# --- 5. Add a brand-new Quick-Start Note node (mode=0 = always shown)
# find a fresh ID
existing_ids = {n["id"] for n in data["nodes"]}
quick_id = max(existing_ids) + 1
quick_node = {
    "id": quick_id,
    "type": "Note",
    "pos": [3500, -3700],
    "size": [480, 320],
    "flags": {},
    "order": 0,
    "mode": 0,
    "inputs": [],
    "outputs": [],
    "title": "Quick Start (快速开始)",
    "properties": {"Node name for S&R": "Note"},
    "widgets_values": [
        "▶ 快速开始 (Quick Start)\n"
        "==================\n"
        "1. 在 H3Extender (id=6) 内编辑 3 段分镜的 prompt/seed/duration\n"
        "2. 确认 UNETLoader/CLIPLoader/VAELoader 的文件名匹配你的本地模型\n"
        "3. (可选) 节点 66 切换 Lightning LoRA: true=4步, false=20步\n"
        "4. (可选) 在 BSAI_AssetLibraryInput (id=5) 上传资产 (图/视频/音频)\n"
        "5. Queue Prompt\n"
        "6. 视频输出: ComfyUI/output/video/MiniMax_H3_*.mp4\n"
        "7. (可选) 启用后处理: 把节点 10 或 24-35 的 mode 改为 Always\n"
    ],
    "widgets_values_named": {
        "text": (
            "▶ 快速开始 (Quick Start)\n"
            "==================\n"
            "1. 在 H3Extender (id=6) 内编辑 3 段分镜的 prompt/seed/duration\n"
            "2. 确认 UNETLoader/CLIPLoader/VAELoader 的文件名匹配你的本地模型\n"
            "3. (可选) 节点 66 切换 Lightning LoRA: true=4步, false=20步\n"
            "4. (可选) 在 BSAI_AssetLibraryInput (id=5) 上传资产 (图/视频/音频)\n"
            "5. Queue Prompt\n"
            "6. 视频输出: ComfyUI/output/video/MiniMax_H3_*.mp4\n"
            "7. (可选) 启用后处理: 把节点 10 或 24-35 的 mode 改为 Always\n"
        )
    },
    "color": "#2a2",
}
data["nodes"].append(quick_node)
data["last_node_id"] = max(n["id"] for n in data["nodes"])

# Re-link to ensure last_link_id correct
max_lid = max((l[0] for l in data["links"]), default=0)
data["last_link_id"] = max_lid

# Bump version to mark this as the fixed edition
data["id"] = "bsai-h3-extender-fixed-v1"

with open(DST, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Wrote fixed workflow: {DST}")
print(f"  nodes: {len(data['nodes'])}")
print(f"  links: {len(data['links'])}")
print(f"  groups: {len(data.get('groups', []))}")
