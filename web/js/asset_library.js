/**
 * BSAI Asset Library - Upload-Based Frontend Extension
 *
 * Three panels: Images (图片), Videos (视频), Audio (音频)
 * - Batch upload via Windows file picker (multi-select)
 * - Single file delete (X button per thumbnail)
 * - Remove All button per panel
 * - Number labels BELOW each thumbnail (图1, 视频1, 音频1...)
 */

import { app } from "../../../scripts/app.js";

var STYLE_ID = "bsai-asset-library-css";
if (!document.getElementById(STYLE_ID)) {
    var st = document.createElement("style");
    st.id = STYLE_ID;
    st.textContent = `
.bsai-gal {
    display:flex; flex-direction:column; gap:6px;
    padding:8px; background:#181818; width:100%; box-sizing:border-box;
    font-family:sans-serif;
}
.bsai-sec {
    border:1px solid #333; border-radius:5px; overflow:hidden;
}
.bsai-sec-hdr {
    padding:5px 10px; background:#262626; color:#8cf; font-size:12px;
    font-weight:bold; cursor:pointer; display:flex;
    justify-content:space-between; align-items:center; user-select:none;
}
.bsai-sec-hdr:hover { background:#333; }
.bsai-sec-cnt {
    color:#aaa; font-weight:normal; font-size:11px;
    background:#1a1a1a; padding:2px 8px; border-radius:10px; min-width:18px;
    text-align:center;
}
.bsai-tb {
    display:flex; gap:6px; padding:6px; background:#1e1e1e;
}
.bsai-btn {
    padding:5px 12px; border-radius:4px; cursor:pointer;
    font-size:11px; border:1px solid #444; user-select:none;
    text-align:center; transition:background 0.15s;
}
.bsai-btn-up {
    background:#2a4a6a; color:#fff; border-color:#3f789e; flex:1;
}
.bsai-btn-up:hover { background:#3f789e; }
.bsai-btn-rm {
    background:#4a2222; color:#f88; border-color:#633;
}
.bsai-btn-rm:hover { background:#633; }
.bsai-grid {
    display:flex; flex-wrap:wrap; gap:6px; padding:6px;
    max-height:280px; overflow-y:auto; background:#111;
}
.bsai-grid:empty::after {
    content:"No assets / 无资产"; color:#555; font-size:11px;
    padding:16px; width:100%; text-align:center;
}
.bsai-thumb-wrap {
    display:flex; flex-direction:column; align-items:center; gap:3px;
    width:84px;
}
.bsai-thumb-wrap.bsai-dragging {
    opacity:0.4;
}
.bsai-thumb-wrap.bsai-drag-over {
    outline:2px dashed #3f789e; outline-offset:2px;
}
.bsai-thumb {
    position:relative; width:80px; height:80px; flex-shrink:0;
    border:1px solid #3a3a3a; border-radius:4px; overflow:hidden;
    background:#222; cursor:grab;
}
.bsai-thumb:hover {
    border-color:#3f789e; box-shadow:0 0 6px rgba(63,120,158,0.4);
}
.bsai-thumb img { width:100%; height:100%; object-fit:cover; display:block; }
.bsai-thumb-ph {
    width:100%; height:100%; display:flex; align-items:center;
    justify-content:center; color:#555; font-size:10px; font-weight:bold;
}
.bsai-thumb-ph svg { opacity:0.7; }
.bsai-thumb-del {
    position:absolute; top:2px; right:2px; width:18px; height:18px;
    background:rgba(180,40,40,0.9); color:#fff; border-radius:50%;
    font-size:11px; display:flex; align-items:center; justify-content:center;
    cursor:pointer; border:1px solid #633; line-height:1; padding:0;
    font-weight:bold;
}
.bsai-thumb-del:hover { background:rgba(220,60,60,1); }
.bsai-thumb-rep {
    position:absolute; top:2px; left:2px; width:18px; height:18px;
    background:rgba(30,100,60,0.9); color:#fff; border-radius:50%;
    font-size:12px; display:flex; align-items:center; justify-content:center;
    cursor:pointer; border:1px solid #274; line-height:1; padding:0;
    font-weight:bold; z-index:2;
}
.bsai-thumb-rep:hover { background:rgba(40,140,80,1); }
.bsai-thumb-num {
    font-size:12px; font-weight:bold; color:#8cf; text-align:center;
    text-shadow:0 0 3px rgba(0,0,0,0.8);
}
.bsai-thumb-dur {
    position:absolute; top:2px; right:22px;
    background:rgba(0,0,0,0.8); color:#8cf; font-size:9px;
    padding:1px 5px; border-radius:3px;
}
.bsai-sec.collapsed .bsai-tb,
.bsai-sec.collapsed .bsai-grid { display:none; }
.bsai-spin {
    display:inline-block; width:14px; height:14px;
    border:2px solid #555; border-top-color:#8cf;
    border-radius:50%; animation:bsai-rot 0.8s linear infinite;
}
@keyframes bsai-rot { to { transform:rotate(360deg); } }
`;
    document.head.appendChild(st);
}

var SECTIONS = [
    { id: "images", title: "图片资产 / Images", prefix: "图", accept: "image/*", widget: "image_files" },
    { id: "videos", title: "视频资产 / Videos", prefix: "视频", accept: "video/*", widget: "video_files" },
    { id: "audios", title: "音频资产 / Audio", prefix: "音频", accept: "audio/*", widget: "audio_files" },
];

app.registerExtension({
    name: "BSAI.AssetLibrary",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "BSAI_AssetLibraryInput") return;
        var orig = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (orig) orig.apply(this, arguments);
            var node = this;
            setTimeout(function () { setupGallery(node); }, 50);
        };
    },
});

function setupGallery(node) {
    if (node._bsaiGal) return;
    node._bsaiGal = true;

    // Hide the three string widgets
    SECTIONS.forEach(function (sec) {
        var w = findWidget(node, sec.widget);
        if (w) {
            w.computeSize = function (width) { return [width, 0]; };
            w.draw = function () {};
            w._bsaiHidden = true;
            if (w.inputEl) w.inputEl.style.display = "none";
            if (w.labelEl) w.labelEl.style.display = "none";
        }
    });

    var container = document.createElement("div");
    container.className = "bsai-gal";

    SECTIONS.forEach(function (sec) {
        container.appendChild(createSection(sec, node));
    });

    if (typeof node.addDOMWidget === "function") {
        var dw = node.addDOMWidget("bsai_gallery", "html", container, {
            getValue: function () { return ""; },
            setValue: function () {},
        });
        if (dw) {
            dw.options = dw.options || {};
            dw.options.minHeight = 250;
        }
    } else {
        console.warn("[BSAI] addDOMWidget not available, gallery UI will not be visible");
    }

    // Load existing files from widget values (for workflow reload)
    setTimeout(function () { loadExistingFiles(node, container); }, 100);
}

function findWidget(node, name) {
    if (!node.widgets) return null;
    for (var i = 0; i < node.widgets.length; i++) {
        if (node.widgets[i].name === name) return node.widgets[i];
    }
    return null;
}

function createSection(sec, node) {
    var el = document.createElement("div");
    el.className = "bsai-sec";
    el.dataset.sec = sec.id;

    var hdr = document.createElement("div");
    hdr.className = "bsai-sec-hdr";
    hdr.innerHTML = '<span>' + sec.title + '</span><span class="bsai-sec-cnt" data-cnt="' + sec.id + '">0</span>';
    hdr.addEventListener("click", function () { el.classList.toggle("collapsed"); });

    var tb = document.createElement("div");
    tb.className = "bsai-tb";

    var upBtn = document.createElement("div");
    upBtn.className = "bsai-btn bsai-btn-up";
    upBtn.textContent = "+ 上传" + (sec.id === "images" ? "图片" : sec.id === "videos" ? "视频" : "音频") + " / Upload";
    upBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        openFilePicker(sec, node, el);
    });

    var rmBtn = document.createElement("div");
    rmBtn.className = "bsai-btn bsai-btn-rm";
    rmBtn.textContent = "全部删除 / Remove All";
    rmBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        removeAllInSection(sec, node, el);
    });

    tb.appendChild(upBtn);
    tb.appendChild(rmBtn);

    var grid = document.createElement("div");
    grid.className = "bsai-grid";
    grid.dataset.grid = sec.id;

    el.appendChild(hdr);
    el.appendChild(tb);
    el.appendChild(grid);
    return el;
}

function openFilePicker(sec, node, sectionEl) {
    var input = document.createElement("input");
    input.type = "file";
    input.multiple = true;
    input.accept = sec.accept;
    input.addEventListener("change", function (e) {
        var files = Array.prototype.slice.call(e.target.files);
        files.sort(function (a, b) {
            return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
        });
        (async function () {
            for (var i = 0; i < files.length; i++) {
                await uploadAndAdd(files[i], sec, node, sectionEl);
            }
        })();
    });
    input.click();
}

async function uploadAndAdd(file, sec, node, sectionEl) {
    var grid = sectionEl.querySelector('[data-grid="' + sec.id + '"]');

    // Add loading placeholder
    var loadingWrap = document.createElement("div");
    loadingWrap.className = "bsai-thumb-wrap";
    loadingWrap.innerHTML = '<div class="bsai-thumb"><div class="bsai-thumb-ph"><span class="bsai-spin"></span></div></div>';
    grid.appendChild(loadingWrap);

    var formData = new FormData();
    formData.append("file", file);

    try {
        var resp = await fetch("/bsai/upload_asset?type=" + sec.id, {
            method: "POST",
            body: formData,
        });
        var result = await resp.json();

        if (result.error) {
            console.error("[BSAI] Upload failed:", result.error);
            loadingWrap.remove();
            return;
        }

        loadingWrap.remove();
        addThumbnail(sec, node, sectionEl, result.filename, null, file.name);
    } catch (e) {
        console.error("[BSAI] Upload error:", e);
        loadingWrap.remove();
    }
}

async function replaceAsset(sec, node, sectionEl, wrap) {
    var oldFilename = wrap.dataset.filename;
    if (!oldFilename) return;

    var input = document.createElement("input");
    input.type = "file";
    input.accept = sec.accept;

    input.addEventListener("change", async function (e) {
        var file = e.target.files[0];
        if (!file) return;

        // Show loading state on the thumbnail
        var thumbEl = wrap.querySelector(".bsai-thumb");
        var oldContent = thumbEl.innerHTML;
        thumbEl.innerHTML = '<div class="bsai-thumb-ph"><span class="bsai-spin"></span></div>';

        var formData = new FormData();
        formData.append("file", file);

        try {
            var resp = await fetch("/bsai/replace_asset?type=" + sec.id + "&old_filename=" + encodeURIComponent(oldFilename), {
                method: "POST",
                body: formData,
            });
            var result = await resp.json();

            if (result.error) {
                console.error("[BSAI] Replace failed:", result.error);
                thumbEl.innerHTML = oldContent;
                return;
            }

            // Update the thumbnail image — use direct file URL
            thumbEl.innerHTML = "";
            if (sec.id === "images") {
                var img = document.createElement("img");
                img.src = "/bsai/asset_file?type=images&filename=" + encodeURIComponent(result.filename);
                img.style.cssText = "width:100%;height:100%;object-fit:cover;";
                img.loading = "lazy";
                thumbEl.appendChild(img);
            } else if (sec.id === "videos") {
                var img = document.createElement("img");
                img.src = "/bsai/video_frame?filename=" + encodeURIComponent(result.filename);
                img.style.cssText = "width:100%;height:100%;object-fit:cover;";
                img.loading = "lazy";
                thumbEl.appendChild(img);
            } else {
                var ph = document.createElement("div");
                ph.className = "bsai-thumb-ph";
                ph.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>';
                thumbEl.appendChild(ph);
            }

            // Re-add the delete and replace buttons
            var del = document.createElement("div");
            del.className = "bsai-thumb-del";
            del.textContent = "X";
            del.title = "删除 / Delete";
            del.addEventListener("click", function (e) {
                e.stopPropagation();
                wrap.remove();
                renumberThumbnails(sec, sectionEl);
                updateCount(sec, sectionEl);
                updateWidgetValue(sec, node, sectionEl);
            });
            thumbEl.appendChild(del);

            var rep = document.createElement("div");
            rep.className = "bsai-thumb-rep";
            rep.innerHTML = "&#8635;";
            rep.title = "替换 / Replace (保持编号不变)";
            rep.addEventListener("click", function (e) {
                e.stopPropagation();
                e.preventDefault();
                replaceAsset(sec, node, sectionEl, wrap);
            });
            thumbEl.appendChild(rep);

            // Update filename - numbering stays the same (position in grid unchanged)
            wrap.dataset.filename = result.filename;
            thumbEl.title = file.name || result.filename;

            // Update the widget value (for persistence)
            updateWidgetValue(sec, node, sectionEl);

            // Notify other nodes that assets changed
            saveManifestAndNotify(node);

            console.log("[BSAI] Replaced:", oldFilename, "->", result.filename);
        } catch (err) {
            console.error("[BSAI] Replace error:", err);
            thumbEl.innerHTML = oldContent;
        }
    });

    input.click();
}

function addThumbnail(sec, node, sectionEl, filename, thumbnail, displayName) {
    var grid = sectionEl.querySelector('[data-grid="' + sec.id + '"]');

    // Wrapper: thumbnail + number below
    var wrap = document.createElement("div");
    wrap.className = "bsai-thumb-wrap";
    wrap.dataset.filename = filename;
    wrap.draggable = true;

    // --- Drag-and-drop reordering ---
    wrap.addEventListener("dragstart", function (e) {
        e.stopPropagation();
        sec._draggedWrap = wrap;
        wrap.classList.add("bsai-dragging");
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", filename);
    });

    wrap.addEventListener("dragend", function (e) {
        e.stopPropagation();
        wrap.classList.remove("bsai-dragging");
        var gridEl = sectionEl.querySelector('[data-grid="' + sec.id + '"]');
        if (gridEl) {
            gridEl.querySelectorAll(".bsai-thumb-wrap").forEach(function (w) {
                w.classList.remove("bsai-drag-over");
            });
        }
        sec._draggedWrap = null;
    });

    wrap.addEventListener("dragover", function (e) {
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = "move";
        if (sec._draggedWrap && sec._draggedWrap !== wrap) {
            wrap.classList.add("bsai-drag-over");
        }
    });

    wrap.addEventListener("dragleave", function (e) {
        e.stopPropagation();
        wrap.classList.remove("bsai-drag-over");
    });

    wrap.addEventListener("drop", function (e) {
        e.preventDefault();
        e.stopPropagation();
        wrap.classList.remove("bsai-drag-over");

        var draggedWrap = sec._draggedWrap;
        if (!draggedWrap || draggedWrap === wrap) return;

        var gridEl = sectionEl.querySelector('[data-grid="' + sec.id + '"]');
        if (!gridEl) return;

        // Determine insertion position
        var allWraps = Array.prototype.slice.call(gridEl.querySelectorAll(".bsai-thumb-wrap[data-filename]"));
        var dragIdx = allWraps.indexOf(draggedWrap);
        var dropIdx = allWraps.indexOf(wrap);

        if (dragIdx < 0 || dropIdx < 0) return;

        // Remove dragged element from current position
        gridEl.removeChild(draggedWrap);

        // Re-insert at new position
        if (dragIdx < dropIdx) {
            // Dragged was before drop target — insert after
            gridEl.insertBefore(draggedWrap, wrap.nextSibling);
        } else {
            // Dragged was after drop target — insert before
            gridEl.insertBefore(draggedWrap, wrap);
        }

        // Renumber all thumbnails in new order
        renumberThumbnails(sec, sectionEl);
        updateWidgetValue(sec, node, sectionEl);

        // Notify other nodes (H3 Extender, ClipSequencer) about the new order
        saveManifestAndNotify(node);
    });

    // Thumbnail box — use direct file URL (browser does thumbnailing, no PIL needed)
    var thumb = document.createElement("div");
    thumb.className = "bsai-thumb";
    thumb.title = displayName || filename;

    if (sec.id === "images") {
        var img = document.createElement("img");
        img.src = "/bsai/asset_file?type=images&filename=" + encodeURIComponent(filename);
        img.style.cssText = "width:100%;height:100%;object-fit:cover;";
        img.loading = "lazy";
        img.onerror = function() {
            img.style.display = "none";
            var ph = document.createElement("div");
            ph.className = "bsai-thumb-ph";
            ph.textContent = "IMG";
            thumb.appendChild(ph);
        };
        thumb.appendChild(img);
    } else if (sec.id === "videos") {
        var img = document.createElement("img");
        img.src = "/bsai/video_frame?filename=" + encodeURIComponent(filename);
        img.style.cssText = "width:100%;height:100%;object-fit:cover;";
        img.loading = "lazy";
        img.onerror = function() {
            img.style.display = "none";
            var ph = document.createElement("div");
            ph.className = "bsai-thumb-ph";
            ph.textContent = "VIDEO";
            thumb.appendChild(ph);
        };
        thumb.appendChild(img);
    } else {
        // Audio: use icon placeholder (no thumbnail needed)
        var ph = document.createElement("div");
        ph.className = "bsai-thumb-ph";
        ph.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>';
        thumb.appendChild(ph);
    }

    // Delete X button
    var del = document.createElement("div");
    del.className = "bsai-thumb-del";
    del.textContent = "X";
    del.title = "删除 / Delete";
    del.addEventListener("click", function (e) {
        e.stopPropagation();
        wrap.remove();
        renumberThumbnails(sec, sectionEl);
        updateCount(sec, sectionEl);
        updateWidgetValue(sec, node, sectionEl);
    });
    thumb.appendChild(del);

    // Replace button (top-left)
    var rep = document.createElement("div");
    rep.className = "bsai-thumb-rep";
    rep.innerHTML = "&#8635;";
    rep.title = "替换 / Replace (保持编号不变)";
    rep.addEventListener("click", function (e) {
        e.stopPropagation();
        e.preventDefault();
        replaceAsset(sec, node, sectionEl, wrap);
    });
    thumb.appendChild(rep);

    wrap.appendChild(thumb);

    // Number label BELOW thumbnail
    var num = document.createElement("div");
    num.className = "bsai-thumb-num";
    num.textContent = "@" + sec.prefix + "?";
    wrap.appendChild(num);

    // Click thumbnail to insert @图N into H3 Extender's active prompt
    wrap.addEventListener("mousedown", function (e) {
        // Skip if clicking delete button
        if (e.target.closest(".bsai-thumb-del")) return;

        var ta = window._h3_activeTextarea;
        if (!ta) return; // No active prompt textarea

        e.preventDefault(); // Keep textarea focus — preserve cursor position

        var prefix = wrap.dataset.assetPrefix || sec.prefix;
        var index = parseInt(wrap.dataset.assetIndex || "1", 10);
        var tag = "@" + prefix + index;
        var promptVal = ta.value;

        // Get cursor position (from active focus or saved fallback)
        var cursorPos = (document.activeElement === ta) ? ta.selectionStart : (ta._savedCursorPos || 0);

        // Toggle: remove if exists, insert if not
        if (promptVal.indexOf(tag) >= 0) {
            // Remove tag
            var newPrompt = promptVal.replace(tag, "").replace(/\s+/g, " ").trim();
            ta.value = newPrompt;
            var newPos = Math.max(0, cursorPos - tag.length);
            ta.setSelectionRange(newPos, newPos);
        } else {
            // Insert at cursor position
            var before = promptVal.substring(0, cursorPos);
            var after = promptVal.substring(cursorPos);
            var needSpaceBefore = before.length > 0 && !before.endsWith(" ") && !before.endsWith("\n");
            var needSpaceAfter = after.length > 0 && !after.startsWith(" ") && !after.startsWith("\n");
            var insertStr = (needSpaceBefore ? " " : "") + tag + (needSpaceAfter ? " " : "");
            var newPrompt = before + insertStr + after;
            ta.value = newPrompt;
            var newPos = cursorPos + insertStr.length;
            ta.setSelectionRange(newPos, newPos);
        }
        ta.focus();

        // Update clip data and refresh H3 Extender's asset panel
        if (window._h3_activeClip) {
            window._h3_activeClip.prompt = ta.value;
        }
        if (window._h3_refreshAssetPanel) {
            window._h3_refreshAssetPanel();
        }
    });

    grid.appendChild(wrap);
    updateCount(sec, sectionEl);
    updateWidgetValue(sec, node, sectionEl);
    renumberThumbnails(sec, sectionEl);
}

function renumberThumbnails(sec, sectionEl) {
    var grid = sectionEl.querySelector('[data-grid="' + sec.id + '"]');
    var wraps = grid.querySelectorAll(".bsai-thumb-wrap[data-filename]");
    wraps.forEach(function (wrap, i) {
        var num = wrap.querySelector(".bsai-thumb-num");
        if (num) num.textContent = "@" + sec.prefix + (i + 1);
        wrap.dataset.assetIndex = String(i + 1);
        wrap.dataset.assetPrefix = sec.prefix;
    });
}

function removeAllInSection(sec, node, sectionEl) {
    // Delete actual files from disk via backend
    var assetType = sec.id === "audios" ? "audio" : sec.id;
    fetch("/bsai/remove_all_assets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ asset_type: assetType }),
    }).catch(function (e) {
        console.warn("[BSAI] Failed to remove assets from disk:", e);
    });
    var grid = sectionEl.querySelector('[data-grid="' + sec.id + '"]');
    grid.innerHTML = "";
    updateCount(sec, sectionEl);
    updateWidgetValue(sec, node, sectionEl);
}

function updateCount(sec, sectionEl) {
    var grid = sectionEl.querySelector('[data-grid="' + sec.id + '"]');
    var cnt = sectionEl.querySelector('[data-cnt="' + sec.id + '"]');
    if (cnt) {
        var n = grid.querySelectorAll(".bsai-thumb-wrap[data-filename]").length;
        cnt.textContent = n;
    }
}

function updateWidgetValue(sec, node, sectionEl) {
    var grid = sectionEl.querySelector('[data-grid="' + sec.id + '"]');
    var filenames = [];
    grid.querySelectorAll(".bsai-thumb-wrap").forEach(function (wrap) {
        if (wrap.dataset.filename) filenames.push(wrap.dataset.filename);
    });
    var w = findWidget(node, sec.widget);
    if (w) {
        w.value = JSON.stringify(filenames);
    }
    saveManifestAndNotify(node);
}

function saveManifestAndNotify(node) {
    var manifest = { images: [], videos: [], audios: [] };
    SECTIONS.forEach(function (sec) {
        var w = findWidget(node, sec.widget);
        var files = [];
        if (w) {
            try { files = JSON.parse(w.value || "[]"); } catch (e) { files = []; }
        }
        var key = sec.id === "audios" ? "audios" : sec.id;
        manifest[key] = files;
    });

    fetch("/bsai/save_asset_order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(manifest),
    }).catch(function (e) {
        console.warn("[BSAI] Failed to save asset order:", e);
    });

    window.dispatchEvent(new CustomEvent("bsai-assets-changed", { detail: manifest }));
}

function loadExistingFiles(node, container) {
    SECTIONS.forEach(function (sec) {
        var w = findWidget(node, sec.widget);
        var files = [];
        if (w) {
            try { files = JSON.parse(w.value || "[]"); } catch (e) { files = []; }
        }
        if (!files.length) return;

        var sectionEl = container.querySelector('[data-sec="' + sec.id + '"]');
        var grid = sectionEl.querySelector('[data-grid="' + sec.id + '"]');

        files.forEach(function (filename, j) {
            // Use addThumbnail for consistent rendering (direct file URL, drag-drop, replace button)
            addThumbnail(sec, node, sectionEl, filename, null, filename);
        });
        updateCount(sec, sectionEl);
        renumberThumbnails(sec, sectionEl);
    });
    saveManifestAndNotify(node);
}

async function fetchThumbnail(sec, filename, thumbEl) {
    try {
        var resp = await fetch("/bsai/asset_thumbnail?filename=" + encodeURIComponent(filename) + "&type=" + sec.id);
        var result = await resp.json();
        var ph = thumbEl.querySelector(".bsai-thumb-ph");
        if (ph) {
            if (result.thumbnail) {
                var img = document.createElement("img");
                img.src = "data:image/jpeg;base64," + result.thumbnail;
                thumbEl.replaceChild(img, ph);
            } else {
                if (sec.id === "audios") {
                    ph.innerHTML = '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>';
                } else {
                    ph.textContent = sec.id === "videos" ? "VIDEO" : "IMG";
                }
            }
        }
    } catch (e) {
        var ph2 = thumbEl.querySelector(".bsai-thumb-ph");
        if (ph2) ph2.textContent = "?";
    }
}

function makeImageThumb(file) {
    return new Promise(function (resolve) {
        var reader = new FileReader();
        reader.onload = function (e) {
            var img = new Image();
            img.onload = function () {
                var canvas = document.createElement("canvas");
                canvas.width = 128; canvas.height = 128;
                var ctx = canvas.getContext("2d");
                var sz = Math.min(img.width, img.height);
                var sx = (img.width - sz) / 2, sy = (img.height - sz) / 2;
                ctx.drawImage(img, sx, sy, sz, sz, 0, 0, 128, 128);
                var dataUrl = canvas.toDataURL("image/png");
                resolve(dataUrl.split(",")[1]);
            };
            img.onerror = function () { resolve(null); };
            img.src = e.target.result;
        };
        reader.onerror = function () { resolve(null); };
        reader.readAsDataURL(file);
    });
}

function makeVideoThumb(file) {
    return new Promise(function (resolve) {
        var video = document.createElement("video");
        video.preload = "metadata";
        video.muted = true;
        video.src = URL.createObjectURL(file);
        video.addEventListener("loadeddata", function () {
            try { video.currentTime = Math.min(0.1, (video.duration || 1) / 2); } catch (e) {}
        });
        video.addEventListener("seeked", function () {
            var canvas = document.createElement("canvas");
            canvas.width = 128; canvas.height = 128;
            var ctx = canvas.getContext("2d");
            var vw = video.videoWidth, vh = video.videoHeight;
            if (vw > 0 && vh > 0) {
                var sz = Math.min(vw, vh);
                var sx = (vw - sz) / 2, sy = (vh - sz) / 2;
                ctx.drawImage(video, sx, sy, sz, sz, 0, 0, 128, 128);
            }
            URL.revokeObjectURL(video.src);
            var dataUrl = canvas.toDataURL("image/png");
            resolve(dataUrl.split(",")[1]);
        });
        video.addEventListener("error", function () {
            URL.revokeObjectURL(video.src);
            resolve(null);
        });
    });
}
