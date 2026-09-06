/**
 * BSAI Clip Sequencer - Vertical CLIP Card Manager with Left Asset Panel
 *
 * Features:
 * - Vertical (top-to-bottom) CLIP card arrangement
 * - Each CLIP card has LEFT panel (asset references with thumbnails) + RIGHT panel (clip params)
 * - Left panel shows all assets from BSAI_AssetLibraryInput, click to toggle @ references
 * - Manual @ input also supported in left panel
 * - Collapsible advanced section: narration, dialogue, width, height, seed
 * - Serialized to hidden clips_json widget
 * - Connect BSAI_AssetLibraryInput to asset_library input for @ notation resolution
 */

import { app } from "../../../scripts/app.js";

var STYLE_ID = "bsai-clip-sequencer-css";
if (!document.getElementById(STYLE_ID)) {
    var st = document.createElement("style");
    st.id = STYLE_ID;
    st.textContent = `
.bsai-seq {
    display: flex; flex-direction: column; gap: 5px;
    padding: 6px; background: #1a1a1a; width: 100%; box-sizing: border-box;
    font-family: sans-serif;
}
.bsai-seq-cards {
    display: flex; flex-direction: column; gap: 5px;
    max-height: 700px; overflow-y: auto; padding-right: 2px;
}
.bsai-seq-cards::-webkit-scrollbar { width: 6px; }
.bsai-seq-cards::-webkit-scrollbar-track { background: #111; }
.bsai-seq-cards::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
.bsai-clip {
    border: 1px solid #3a3a3a; border-radius: 5px; overflow: hidden;
    background: #1e1e1e; transition: border-color 0.2s;
}
.bsai-clip:hover { border-color: #4a6a8a; }
.bsai-clip-hdr {
    padding: 4px 8px; background: linear-gradient(135deg, #2a3a4a, #1e2e3e);
    color: #8cf; font-size: 12px; font-weight: bold;
    display: flex; justify-content: space-between; align-items: center;
    user-select: none;
}
.bsai-clip-num {
    display: flex; align-items: center; gap: 5px;
}
.bsai-clip-num-badge {
    display: inline-block; min-width: 20px; height: 20px; line-height: 20px;
    text-align: center; background: #3f789e; color: #fff; border-radius: 10px;
    font-size: 11px; padding: 0 4px;
}
.bsai-clip-del {
    width: 20px; height: 20px; background: rgba(180,40,40,0.85); color: #fff;
    border-radius: 50%; font-size: 11px; display: flex; align-items: center;
    justify-content: center; cursor: pointer; border: 1px solid #633;
    font-weight: bold; transition: background 0.15s;
}
.bsai-clip-del:hover { background: rgba(220,60,60,1); }

/* === Two-column body: left asset panel + right params === */
.bsai-clip-body {
    display: flex; gap: 0; padding: 0;
}
.bsai-clip-left {
    width: 160px; min-width: 160px; flex-shrink: 0;
    border-right: 1px solid #333; background: #181818;
    display: flex; flex-direction: column; gap: 4px;
    padding: 6px;
}
.bsai-clip-left-hdr {
    font-size: 10px; color: #8cf; font-weight: bold;
    display: flex; justify-content: space-between; align-items: center;
    padding-bottom: 3px; border-bottom: 1px solid #2a2a2a;
}
.bsai-clip-left-hint {
    font-size: 8px; color: #556; font-weight: normal;
}
.bsai-asset-list {
    display: flex; flex-direction: column; gap: 3px;
    max-height: 250px; overflow-y: auto; padding-right: 2px;
}
.bsai-asset-list::-webkit-scrollbar { width: 4px; }
.bsai-asset-list::-webkit-scrollbar-track { background: #111; }
.bsai-asset-list::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
.bsai-asset-list:empty::after {
    content: "无资产/No assets"; color: #444; font-size: 9px;
    padding: 8px; text-align: center;
}
.bsai-asset-item {
    display: flex; align-items: center; gap: 4px; padding: 2px;
    border-radius: 3px; cursor: pointer; border: 1px solid transparent;
    transition: all 0.12s; user-select: none;
}
.bsai-asset-item:hover { background: #222; border-color: #3a3a3a; }
.bsai-asset-item.selected {
    background: rgba(63,120,158,0.18); border-color: #3f789e;
    box-shadow: 0 0 4px rgba(63,120,158,0.2);
}
.bsai-asset-thumb {
    width: 36px; height: 36px; flex-shrink: 0; border-radius: 3px;
    overflow: hidden; background: #222; border: 1px solid #2a2a2a;
    display: flex; align-items: center; justify-content: center;
}
.bsai-asset-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.bsai-asset-thumb-ph {
    width: 100%; height: 100%; display: flex; align-items: center;
    justify-content: center; color: #555; font-size: 7px; font-weight: bold;
}
.bsai-asset-info {
    flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px;
}
.bsai-asset-label {
    font-size: 10px; color: #ccc; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}
.bsai-asset-item.selected .bsai-asset-label { color: #8cf; }
.bsai-asset-type {
    font-size: 8px; color: #556;
}
.bsai-asset-check {
    width: 14px; height: 14px; flex-shrink: 0; border-radius: 50%;
    border: 1px solid #444; display: flex; align-items: center;
    justify-content: center; font-size: 9px; color: #8cf;
}
.bsai-asset-item:not(.selected) .bsai-asset-check { display: none; }
.bsai-asset-refresh {
    font-size: 9px; color: #556; cursor: pointer; text-align: center;
    padding: 3px; border: 1px solid #2a2a2a; border-radius: 3px;
    background: #1a1a1a; user-select: none;
}
.bsai-asset-refresh:hover { color: #8cf; border-color: #3a3a3a; }

.bsai-clip-right {
    flex: 1; display: flex; flex-direction: column; gap: 4px;
    padding: 6px 8px; min-width: 0;
}
.bsai-clip-lbl {
    font-size: 10px; color: #888; margin-bottom: 1px;
    display: flex; justify-content: space-between; align-items: center;
}
.bsai-clip-lbl-hint {
    font-size: 9px; color: #556; font-weight: normal;
}
.bsai-clip-prompt {
    width: 100%; min-height: 40px; max-height: 150px; resize: vertical;
    background: #111; color: #ddd; border: 1px solid #333; border-radius: 3px;
    padding: 4px 6px; font-size: 11px; font-family: sans-serif;
    box-sizing: border-box; line-height: 1.4;
}
.bsai-clip-prompt:focus { border-color: #3f789e; outline: none; box-shadow: 0 0 3px rgba(63,120,158,0.3); }
.bsai-clip-narr, .bsai-clip-dial {
    width: 100%; min-height: 30px; max-height: 100px; resize: vertical;
    background: #111; color: #ddd; border: 1px solid #333; border-radius: 3px;
    padding: 4px 6px; font-size: 11px; font-family: sans-serif;
    box-sizing: border-box; line-height: 1.4;
}
.bsai-clip-narr:focus, .bsai-clip-dial:focus { border-color: #3f789e; outline: none; }
.bsai-clip-row {
    display: flex; gap: 6px; align-items: flex-end;
}
.bsai-clip-field {
    display: flex; flex-direction: column; flex: 1; gap: 2px;
}
.bsai-clip-field label {
    font-size: 9px; color: #777;
}
.bsai-clip-field input, .bsai-clip-field select {
    background: #111; color: #ddd; border: 1px solid #333; border-radius: 3px;
    padding: 3px 4px; font-size: 11px; width: 100%; box-sizing: border-box;
}
.bsai-clip-field input:focus, .bsai-clip-field select:focus {
    border-color: #3f789e; outline: none;
}
.bsai-clip-adv-toggle {
    font-size: 10px; color: #666; cursor: pointer; padding: 2px 0;
    user-select: none; display: flex; align-items: center; gap: 4px;
}
.bsai-clip-adv-toggle:hover { color: #8cf; }
.bsai-clip-adv {
    padding-top: 4px; display: flex; flex-direction: column; gap: 4px;
}
.bsai-seq-add {
    padding: 7px; background: linear-gradient(135deg, #2a4a3a, #1e3e2e);
    color: #8f8; border: 1px solid #3a6e3a; border-radius: 4px;
    cursor: pointer; text-align: center; font-size: 12px;
    font-weight: bold; user-select: none; transition: all 0.15s;
}
.bsai-seq-add:hover {
    background: linear-gradient(135deg, #3a5e3a, #2e4e2e);
    box-shadow: 0 0 6px rgba(63,158,63,0.3);
}
.bsai-seq-summary {
    font-size: 10px; color: #667; text-align: center; padding: 2px;
    display: flex; justify-content: space-around;
}
.bsai-seq-summary span { color: #8cf; font-weight: bold; }
`;
    document.head.appendChild(st);
}

var DEFAULT_CLIP = {
    prompt: "",
    asset_refs: "",
    narration: "",
    dialogue: "",
    subtitle_source: "manual",
    audio_mode: "H3_auto",
    duration: 5.0,
    width: 1344,
    height: 768,
    seed: 0,
};

var _assetCache = null;
var _assetCacheTime = 0;
var ASSET_CACHE_TTL = 5000;

async function fetchAssetLibrary() {
    var now = Date.now();
    if (_assetCache && (now - _assetCacheTime) < ASSET_CACHE_TTL) {
        return _assetCache;
    }
    try {
        var resp = await fetch("/bsai/list_all_assets");
        var data = await resp.json();
        _assetCache = data;
        _assetCacheTime = now;
        return data;
    } catch (e) {
        console.warn("[BSAI] Failed to fetch asset library:", e);
        return { images: [], videos: [], audios: [] };
    }
}

function parseAssetRefs(refsStr) {
    var refs = { images: [], videos: [], audios: [] };
    if (!refsStr) return refs;
    refs.images = (refsStr.match(/@图(\d+)/g) || []).map(function (s) {
        return parseInt(s.replace("@图", ""));
    });
    refs.videos = (refsStr.match(/@视频(\d+)/g) || []).map(function (s) {
        return parseInt(s.replace("@视频", ""));
    });
    refs.audios = (refsStr.match(/@音频(\d+)/g) || []).map(function (s) {
        return parseInt(s.replace("@音频", ""));
    });
    return refs;
}

function rebuildRefsStr(selected) {
    var parts = [];
    selected.images.forEach(function (n) { parts.push("@图" + n); });
    selected.videos.forEach(function (n) { parts.push("@视频" + n); });
    selected.audios.forEach(function (n) { parts.push("@音频" + n); });
    return parts.join(" ");
}

app.registerExtension({
    name: "BSAI.ClipSequencer",

    setup() {
        window.addEventListener("bsai-assets-changed", function () {
            _assetCache = null;
            _assetCacheTime = 0;
            if (app.graph) {
                for (var i = 0; i < app.graph._nodes.length; i++) {
                    var node = app.graph._nodes[i];
                    if (node.type === "BSAI_ClipSequencer" && node._bsaiCardsWrapper) {
                        var cards = node._bsaiCardsWrapper;
                        var assetLists = cards.querySelectorAll(".bsai-asset-list");
                        assetLists.forEach(function (list) {
                            var clip = list.closest(".bsai-clip");
                            if (!clip) return;
                            var leftPanel = list.closest(".bsai-clip-left");
                            if (!leftPanel) return;
                            var refs = leftPanel.dataset.assetRefs || "";
                            renderAssetList(list, refs, function (newRefs) {
                                leftPanel.dataset.assetRefs = newRefs;
                                serializeClips(node, cards);
                            });
                        });
                    }
                }
            }
        });
    },

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "BSAI_ClipSequencer") return;

        var origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (origCreated) origCreated.apply(this, arguments);
            var node = this;
            setTimeout(function () { setupSequencer(node); }, 50);
        };

        var origConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (data) {
            if (origConfigure) origConfigure.apply(this, arguments);
            var node = this;
            if (node._bsaiSeqReady) {
                setTimeout(function () { reloadFromWidget(node); }, 50);
            }
        };
    },
});

function setupSequencer(node) {
    if (node._bsaiSeqReady) return;
    node._bsaiSeqReady = true;

    var jsonWidget = findWidget(node, "clips_json");
    if (jsonWidget) {
        jsonWidget.computeSize = function (width) { return [width, 0]; };
        jsonWidget.draw = function () {};
        jsonWidget._bsaiHidden = true;
        if (jsonWidget.inputEl) jsonWidget.inputEl.style.display = "none";
        if (jsonWidget.labelEl) jsonWidget.labelEl.style.display = "none";
    }

    var container = document.createElement("div");
    container.className = "bsai-seq";

    var cardsWrapper = document.createElement("div");
    cardsWrapper.className = "bsai-seq-cards";
    container.appendChild(cardsWrapper);

    var summary = document.createElement("div");
    summary.className = "bsai-seq-summary";
    summary.innerHTML = '<span data-sum-clips>0</span> CLIPs &nbsp;|&nbsp; 总时长 <span data-sum-dur>0.0</span>s';
    container.appendChild(summary);

    var addBtn = document.createElement("div");
    addBtn.className = "bsai-seq-add";
    addBtn.textContent = "+ 添加 CLIP / Add CLIP";
    addBtn.addEventListener("click", function () {
        addClipCard(node, cardsWrapper, null);
        serializeClips(node, cardsWrapper);
        updateSummary(cardsWrapper, summary);
    });
    container.appendChild(addBtn);

    node._bsaiCardsWrapper = cardsWrapper;
    node._bsaiSummary = summary;

    if (typeof node.addDOMWidget === "function") {
        var dw = node.addDOMWidget("bsai_clips_ui", "html", container, {
            getValue: function () { return ""; },
            setValue: function () {},
        });
        if (dw) {
            dw.options = dw.options || {};
            dw.options.minHeight = 200;
        }
    } else {
        console.warn("[BSAI] addDOMWidget not available, clip sequencer UI will not be visible");
    }

    setTimeout(function () { reloadFromWidget(node); }, 100);
}

function reloadFromWidget(node) {
    var cardsWrapper = node._bsaiCardsWrapper;
    if (!cardsWrapper) return;

    cardsWrapper.innerHTML = "";

    var jsonWidget = findWidget(node, "clips_json");
    var clips = [];
    if (jsonWidget) {
        try { clips = JSON.parse(jsonWidget.value || "[]"); } catch (e) { clips = []; }
    }

    if (clips.length === 0) {
        addClipCard(node, cardsWrapper, null);
    } else {
        clips.forEach(function (clip) {
            addClipCard(node, cardsWrapper, clip);
        });
    }

    var summary = node._bsaiSummary;
    updateSummary(cardsWrapper, summary);
}

function addClipCard(node, cardsWrapper, clipData) {
    var data = clipData ? Object.assign({}, DEFAULT_CLIP, clipData) : Object.assign({}, DEFAULT_CLIP);
    var index = cardsWrapper.querySelectorAll(".bsai-clip").length + 1;

    var card = document.createElement("div");
    card.className = "bsai-clip";

    // ---- Header ----
    var hdr = document.createElement("div");
    hdr.className = "bsai-clip-hdr";

    var numWrap = document.createElement("div");
    numWrap.className = "bsai-clip-num";
    numWrap.innerHTML = '<span class="bsai-clip-num-badge">' + index + '</span> CLIP';
    hdr.appendChild(numWrap);

    var delBtn = document.createElement("div");
    delBtn.className = "bsai-clip-del";
    delBtn.textContent = "✕";
    delBtn.title = "删除此 CLIP / Delete this clip";
    delBtn.addEventListener("click", function () {
        card.remove();
        renumberCards(cardsWrapper);
        serializeClips(node, cardsWrapper);
        updateSummary(cardsWrapper, node._bsaiSummary);
    });
    hdr.appendChild(delBtn);
    card.appendChild(hdr);

    // ---- Body: two-column layout ----
    var body = document.createElement("div");
    body.className = "bsai-clip-body";

    // === LEFT panel: asset references ===
    var leftPanel = document.createElement("div");
    leftPanel.className = "bsai-clip-left";

    var leftHdr = document.createElement("div");
    leftHdr.className = "bsai-clip-left-hdr";
    leftHdr.innerHTML = '资产引用 <span class="bsai-clip-left-hint">点击选择</span>';
    leftPanel.appendChild(leftHdr);

    var assetList = document.createElement("div");
    assetList.className = "bsai-asset-list";
    leftPanel.appendChild(assetList);

    var refreshBtn = document.createElement("div");
    refreshBtn.className = "bsai-asset-refresh";
    refreshBtn.textContent = "↻ 刷新资产库";
    refreshBtn.addEventListener("click", function () {
        _assetCache = null;
        renderAssetList(assetList, data.asset_refs || "", function (newRefs) {
            data.asset_refs = newRefs;
            serializeClips(node, cardsWrapper);
        });
    });
    leftPanel.appendChild(refreshBtn);

    leftPanel.dataset.assetRefs = data.asset_refs || "";
    body.appendChild(leftPanel);

    // === RIGHT panel: clip parameters ===
    var rightPanel = document.createElement("div");
    rightPanel.className = "bsai-clip-right";

    // Prompt
    var promptLbl = document.createElement("div");
    promptLbl.className = "bsai-clip-lbl";
    promptLbl.innerHTML = '提示词 / Prompt <span class="bsai-clip-lbl-hint">【旁白】【对白】 + @图N</span>';
    rightPanel.appendChild(promptLbl);

    var promptInput = document.createElement("textarea");
    promptInput.className = "bsai-clip-prompt";
    promptInput.rows = 2;
    promptInput.value = data.prompt || "";
    promptInput.placeholder = "输入生成提示词...\n可用 【旁白】/【对白】 标记字幕\n可用 @图1 @视频1 @音频1 引用资产";
    promptInput.addEventListener("input", function () { serializeClips(node, cardsWrapper); });
    rightPanel.appendChild(promptInput);

    // Row: duration + audio_mode + subtitle_source
    var row = document.createElement("div");
    row.className = "bsai-clip-row";

    var durWrap = document.createElement("div");
    durWrap.className = "bsai-clip-field";
    durWrap.dataset.field = "duration";
    var durLbl = document.createElement("label");
    durLbl.textContent = "时长/秒";
    durWrap.appendChild(durLbl);
    var durInput = document.createElement("input");
    durInput.type = "number";
    durInput.value = data.duration || 5.0;
    durInput.min = 0.25; durInput.max = 150; durInput.step = 0.25;
    durInput.addEventListener("input", function () {
        serializeClips(node, cardsWrapper);
        updateSummary(cardsWrapper, node._bsaiSummary);
    });
    durWrap.appendChild(durInput);
    row.appendChild(durWrap);

    var audWrap = document.createElement("div");
    audWrap.className = "bsai-clip-field";
    audWrap.dataset.field = "audio_mode";
    var audLbl = document.createElement("label");
    audLbl.textContent = "音频模式";
    audWrap.appendChild(audLbl);
    var audSel = document.createElement("select");
    [["H3_auto", "H3 自动"], ["custom", "自定义"]].forEach(function (pair) {
        var opt = document.createElement("option");
        opt.value = pair[0]; opt.textContent = pair[1];
        audSel.appendChild(opt);
    });
    audSel.value = data.audio_mode || "H3_auto";
    audSel.addEventListener("change", function () { serializeClips(node, cardsWrapper); });
    audWrap.appendChild(audSel);
    row.appendChild(audWrap);

    var subWrap = document.createElement("div");
    subWrap.className = "bsai-clip-field";
    subWrap.dataset.field = "subtitle_source";
    var subLbl = document.createElement("label");
    subLbl.textContent = "字幕来源";
    subWrap.appendChild(subLbl);
    var subSel = document.createElement("select");
    [["manual", "手动输入"], ["extract_from_prompt", "从提示词提取"]].forEach(function (pair) {
        var opt = document.createElement("option");
        opt.value = pair[0]; opt.textContent = pair[1];
        subSel.appendChild(opt);
    });
    subSel.value = data.subtitle_source || "manual";
    subSel.addEventListener("change", function () { serializeClips(node, cardsWrapper); });
    subWrap.appendChild(subSel);
    row.appendChild(subWrap);

    rightPanel.appendChild(row);

    // ---- Collapsible advanced section ----
    var advToggle = document.createElement("div");
    advToggle.className = "bsai-clip-adv-toggle";
    advToggle.textContent = "▶ 字幕/高级设置 / Subtitle & Advanced";
    advToggle.dataset.expanded = "false";

    var advContent = document.createElement("div");
    advContent.className = "bsai-clip-adv";
    advContent.style.display = "none";

    advToggle.addEventListener("click", function () {
        var isHidden = advContent.style.display === "none";
        advContent.style.display = isHidden ? "flex" : "none";
        advToggle.textContent = isHidden
            ? "▼ 字幕/高级设置 / Subtitle & Advanced"
            : "▶ 字幕/高级设置 / Subtitle & Advanced";
    });

    var narrLbl = document.createElement("div");
    narrLbl.className = "bsai-clip-lbl";
    narrLbl.textContent = "旁白 / Narration";
    advContent.appendChild(narrLbl);

    var narrInput = document.createElement("textarea");
    narrInput.className = "bsai-clip-narr";
    narrInput.rows = 2;
    narrInput.value = data.narration || "";
    narrInput.placeholder = "旁白字幕文本...";
    narrInput.addEventListener("input", function () { serializeClips(node, cardsWrapper); });
    advContent.appendChild(narrInput);

    var dialLbl = document.createElement("div");
    dialLbl.className = "bsai-clip-lbl";
    dialLbl.textContent = "对白 / Dialogue";
    advContent.appendChild(dialLbl);

    var dialInput = document.createElement("textarea");
    dialInput.className = "bsai-clip-dial";
    dialInput.rows = 2;
    dialInput.value = data.dialogue || "";
    dialInput.placeholder = "对白字幕文本...";
    dialInput.addEventListener("input", function () { serializeClips(node, cardsWrapper); });
    advContent.appendChild(dialInput);

    var advRow = document.createElement("div");
    advRow.className = "bsai-clip-row";

    var wWrap = document.createElement("div");
    wWrap.className = "bsai-clip-field";
    wWrap.dataset.field = "width";
    var wLbl = document.createElement("label");
    wLbl.textContent = "宽度 Width";
    wWrap.appendChild(wLbl);
    var wInput = document.createElement("input");
    wInput.type = "number";
    wInput.value = data.width || 1344;
    wInput.min = 256; wInput.max = 2048; wInput.step = 32;
    wInput.addEventListener("input", function () { serializeClips(node, cardsWrapper); });
    wWrap.appendChild(wInput);
    advRow.appendChild(wWrap);

    var hWrap = document.createElement("div");
    hWrap.className = "bsai-clip-field";
    hWrap.dataset.field = "height";
    var hLbl = document.createElement("label");
    hLbl.textContent = "高度 Height";
    hWrap.appendChild(hLbl);
    var hInput = document.createElement("input");
    hInput.type = "number";
    hInput.value = data.height || 768;
    hInput.min = 256; hInput.max = 2048; hInput.step = 32;
    hInput.addEventListener("input", function () { serializeClips(node, cardsWrapper); });
    hWrap.appendChild(hInput);
    advRow.appendChild(hWrap);

    var sWrap = document.createElement("div");
    sWrap.className = "bsai-clip-field";
    sWrap.dataset.field = "seed";
    var sLbl = document.createElement("label");
    sLbl.textContent = "种子 Seed";
    sWrap.appendChild(sLbl);
    var sInput = document.createElement("input");
    sInput.type = "number";
    sInput.value = data.seed || 0;
    sInput.min = 0; sInput.max = 4294967295;
    sInput.addEventListener("input", function () { serializeClips(node, cardsWrapper); });
    sWrap.appendChild(sInput);
    advRow.appendChild(sWrap);

    advContent.appendChild(advRow);

    rightPanel.appendChild(advToggle);
    rightPanel.appendChild(advContent);

    body.appendChild(rightPanel);
    card.appendChild(body);
    cardsWrapper.appendChild(card);

    // Render asset list in left panel
    renderAssetList(assetList, data.asset_refs || "", function (newRefs) {
        data.asset_refs = newRefs;
        leftPanel.dataset.assetRefs = newRefs;
        serializeClips(node, cardsWrapper);
    });
}

async function renderAssetList(container, refsStr, onRefsChange) {
    var assets = await fetchAssetLibrary();
    container.innerHTML = "";

    var selected = parseAssetRefs(refsStr);

    var allItems = [];
    assets.images.forEach(function (a) {
        allItems.push({ type: "image", prefix: "图", index: a.index, name: a.name, thumbnail: a.thumbnail });
    });
    assets.videos.forEach(function (a) {
        allItems.push({ type: "video", prefix: "视频", index: a.index, name: a.name, thumbnail: a.thumbnail });
    });
    assets.audios.forEach(function (a) {
        allItems.push({ type: "audio", prefix: "音频", index: a.index, name: a.name, thumbnail: a.thumbnail });
    });

    if (allItems.length === 0) {
        container.innerHTML = "";
        return;
    }

    allItems.forEach(function (item) {
        var isSelected = selected[item.type + "s"].indexOf(item.index) >= 0;

        var itemEl = document.createElement("div");
        itemEl.className = "bsai-asset-item" + (isSelected ? " selected" : "");
        itemEl.title = item.name;

        var thumb = document.createElement("div");
        thumb.className = "bsai-asset-thumb";

        if (item.thumbnail) {
            var img = document.createElement("img");
            img.src = "data:image/png;base64," + item.thumbnail;
            thumb.appendChild(img);
        } else {
            var ph = document.createElement("div");
            ph.className = "bsai-asset-thumb-ph";
            if (item.type === "video") {
                ph.textContent = "VID";
            } else if (item.type === "audio") {
                ph.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>';
            } else {
                ph.textContent = "IMG";
            }
            thumb.appendChild(ph);
        }
        itemEl.appendChild(thumb);

        var info = document.createElement("div");
        info.className = "bsai-asset-info";

        var label = document.createElement("div");
        label.className = "bsai-asset-label";
        label.textContent = "@" + item.prefix + item.index;
        info.appendChild(label);

        var typeLabel = document.createElement("div");
        typeLabel.className = "bsai-asset-type";
        typeLabel.textContent = item.type;
        info.appendChild(typeLabel);

        itemEl.appendChild(info);

        var check = document.createElement("div");
        check.className = "bsai-asset-check";
        check.textContent = "✓";
        itemEl.appendChild(check);

        itemEl.addEventListener("click", function () {
            var arr = selected[item.type + "s"];
            var pos = arr.indexOf(item.index);
            if (pos >= 0) {
                arr.splice(pos, 1);
                itemEl.classList.remove("selected");
            } else {
                arr.push(item.index);
                itemEl.classList.add("selected");
            }
            var newRefs = rebuildRefsStr(selected);
            onRefsChange(newRefs);
        });

        container.appendChild(itemEl);
    });
}

function renumberCards(cardsWrapper) {
    var cards = cardsWrapper.querySelectorAll(".bsai-clip");
    cards.forEach(function (card, i) {
        var badge = card.querySelector(".bsai-clip-num-badge");
        if (badge) badge.textContent = (i + 1);
    });
}

function serializeClips(node, cardsWrapper) {
    var clips = [];
    var cards = cardsWrapper.querySelectorAll(".bsai-clip");
    cards.forEach(function (card) {
        var clip = {
            prompt: "",
            asset_refs: "",
            narration: "",
            dialogue: "",
            subtitle_source: "manual",
            audio_mode: "H3_auto",
            duration: 5.0,
            width: 1344,
            height: 768,
            seed: 0,
        };

        var promptEl = card.querySelector(".bsai-clip-prompt");
        if (promptEl) clip.prompt = promptEl.value;

        var narrEl = card.querySelector(".bsai-clip-narr");
        if (narrEl) clip.narration = narrEl.value;

        var dialEl = card.querySelector(".bsai-clip-dial");
        if (dialEl) clip.dialogue = dialEl.value;

        var durField = card.querySelector('[data-field="duration"] input');
        if (durField) clip.duration = parseFloat(durField.value) || 5.0;

        var audField = card.querySelector('[data-field="audio_mode"] select');
        if (audField) clip.audio_mode = audField.value;

        var subField = card.querySelector('[data-field="subtitle_source"] select');
        if (subField) clip.subtitle_source = subField.value;

        var wField = card.querySelector('[data-field="width"] input');
        if (wField) clip.width = parseInt(wField.value) || 1344;

        var hField = card.querySelector('[data-field="height"] input');
        if (hField) clip.height = parseInt(hField.value) || 768;

        var sField = card.querySelector('[data-field="seed"] input');
        if (sField) clip.seed = parseInt(sField.value) || 0;

        var leftPanel = card.querySelector(".bsai-clip-left");
        if (leftPanel) {
            clip.asset_refs = leftPanel.dataset.assetRefs || "";
        }

        clips.push(clip);
    });

    var jsonWidget = findWidget(node, "clips_json");
    if (jsonWidget) {
        jsonWidget.value = JSON.stringify(clips);
    }
}

function updateSummary(cardsWrapper, summary) {
    if (!summary) return;
    var cards = cardsWrapper.querySelectorAll(".bsai-clip");
    var totalDur = 0;
    cards.forEach(function (card) {
        var durField = card.querySelector('[data-field="duration"] input');
        if (durField) totalDur += parseFloat(durField.value) || 0;
    });
    var clipsSpan = summary.querySelector("[data-sum-clips]");
    var durSpan = summary.querySelector("[data-sum-dur]");
    if (clipsSpan) clipsSpan.textContent = cards.length;
    if (durSpan) durSpan.textContent = totalDur.toFixed(1);
}

function findWidget(node, name) {
    if (!node.widgets) return null;
    for (var i = 0; i < node.widgets.length; i++) {
        if (node.widgets[i].name === name) return node.widgets[i];
    }
    return null;
}
