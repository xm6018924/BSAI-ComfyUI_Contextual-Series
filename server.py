"""
BSAI Asset Library Server
API endpoints for file upload, thumbnail generation, and asset management.
Files are stored in input/bsai_assets/{images,videos,audio}/.
"""

import os
import io
import base64
import json

try:
    from server import PromptServer
    from aiohttp import web
    _HAS_SERVER = True
except Exception:
    _HAS_SERVER = False

try:
    import folder_paths
    _HAS_FOLDER_PATHS = True
except Exception:
    _HAS_FOLDER_PATHS = False

try:
    from PIL import Image
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False

try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False

_IMG_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
_VID_EXTS = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv')
_AUD_EXTS = ('.wav', '.mp3', '.flac', '.ogg', '.aac', '.m4a')


def _get_asset_dir(asset_type):
    if _HAS_FOLDER_PATHS:
        base = folder_paths.get_input_directory()
    else:
        base = os.path.join(os.path.dirname(__file__), '..', '..', 'input')
    d = os.path.join(base, 'bsai_assets', asset_type)
    os.makedirs(d, exist_ok=True)
    return d


def _make_thumbnail(path, size=80):
    if not _HAS_PIL:
        return None
    try:
        if path.lower().endswith(_IMG_EXTS):
            img = Image.open(path).convert('RGB')
        elif _HAS_CV2 and path.lower().endswith(_VID_EXTS):
            cap = cv2.VideoCapture(path)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return None
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
        else:
            return None
        img.thumbnail((size, size), Image.BILINEAR)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=50)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception:
        return None


if _HAS_SERVER:
    @PromptServer.instance.routes.post("/bsai/upload_asset")
    async def upload_asset(request):
        asset_type = request.query.get('type', 'images')
        target_dir = _get_asset_dir(asset_type)

        reader = await request.multipart()
        async for field in reader:
            if field.name == 'file':
                filename = os.path.basename(field.filename or 'unnamed')

                base, ext = os.path.splitext(filename)
                counter = 1
                filepath = os.path.join(target_dir, filename)
                while os.path.exists(filepath):
                    filename = f"{base}_{counter}{ext}"
                    filepath = os.path.join(target_dir, filename)
                    counter += 1

                with open(filepath, 'wb') as f:
                    while True:
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        f.write(chunk)

                print(f"[BSAI AssetServer] Uploaded: {filename} -> {asset_type}/")
                return web.json_response({
                    "filename": filename,
                })

        return web.json_response({"error": "No file field found"}, status=400)

    @PromptServer.instance.routes.get("/bsai/asset_file")
    async def serve_asset_file(request):
        """Serve raw asset files directly — browser does thumbnailing via CSS, no PIL needed."""
        asset_type = request.query.get('type', 'images')
        filename = os.path.basename(request.query.get('filename', ''))
        if not filename:
            return web.json_response({"error": "Missing filename"}, status=400)
        target_dir = _get_asset_dir(asset_type)
        filepath = os.path.join(target_dir, filename)
        if not os.path.exists(filepath):
            return web.json_response({"error": "File not found"}, status=404)
        return web.FileResponse(filepath)

    @PromptServer.instance.routes.get("/bsai/video_frame")
    async def serve_video_frame(request):
        """Extract first frame from a video and serve as JPEG — for thumbnail display."""
        filename = os.path.basename(request.query.get('filename', ''))
        if not filename:
            return web.json_response({"error": "Missing filename"}, status=400)
        target_dir = _get_asset_dir('videos')
        filepath = os.path.join(target_dir, filename)
        if not os.path.exists(filepath):
            return web.json_response({"error": "File not found"}, status=404)
        if _HAS_CV2:
            try:
                cap = cv2.VideoCapture(filepath)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                    return web.Response(body=buf.tobytes(), content_type='image/jpeg')
            except Exception as e:
                print(f"[BSAI AssetServer] Video frame extraction failed: {e}")
        return web.json_response({"error": "Failed to extract frame"}, status=500)

    @PromptServer.instance.routes.post("/bsai/replace_asset")
    async def replace_asset(request):
        asset_type = request.query.get('type', 'images')
        old_filename = request.query.get('old_filename', '')
        target_dir = _get_asset_dir(asset_type)

        # Delete old file
        if old_filename:
            old_path = os.path.join(target_dir, os.path.basename(old_filename))
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception as e:
                    print(f"[BSAI AssetServer] Failed to delete old file: {e}")

        reader = await request.multipart()
        async for field in reader:
            if field.name == 'file':
                filename = os.path.basename(field.filename or 'unnamed')

                base, ext = os.path.splitext(filename)
                counter = 1
                filepath = os.path.join(target_dir, filename)
                while os.path.exists(filepath):
                    filename = f"{base}_{counter}{ext}"
                    filepath = os.path.join(target_dir, filename)
                    counter += 1

                with open(filepath, 'wb') as f:
                    while True:
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        f.write(chunk)

                print(f"[BSAI AssetServer] Replaced: {old_filename} -> {filename} in {asset_type}/")
                return web.json_response({
                    "filename": filename,
                })

        return web.json_response({"error": "No file field found"}, status=400)

    @PromptServer.instance.routes.get("/bsai/asset_thumbnail")
    async def get_asset_thumbnail(request):
        filename = request.query.get('filename', '')
        asset_type = request.query.get('type', 'images')
        if not filename:
            return web.json_response({"error": "Missing filename"}, status=400)

        target_dir = _get_asset_dir(asset_type)
        filepath = os.path.join(target_dir, filename)

        if not os.path.exists(filepath):
            return web.json_response({"error": "File not found", "thumbnail": None}, status=404)

        thumb = _make_thumbnail(filepath)
        return web.json_response({"thumbnail": thumb})

    @PromptServer.instance.routes.get("/bsai/list_all_assets")
    async def list_all_assets(request):
        """Return all assets from default bsai_assets directories with thumbnails.
        Uses asset_order.json manifest for correct ordering (matches Asset Library UI)."""
        manifest_path = os.path.join(_get_asset_dir(""), "asset_order.json")
        manifest = {}
        try:
            if os.path.isfile(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
        except Exception:
            manifest = {}

        result = {"images": [], "videos": [], "audios": []}
        for asset_type, exts, key in [
            ("images", _IMG_EXTS, "images"),
            ("videos", _VID_EXTS, "videos"),
            ("audio", _AUD_EXTS, "audios"),
        ]:
            d = _get_asset_dir(asset_type)
            if not os.path.isdir(d):
                continue
            all_files = [f for f in os.listdir(d) if f.lower().endswith(exts)]

            # Use manifest as filter+order: if the manifest has this key,
            # only return files listed in the manifest. This respects
            # "Remove All" which clears the manifest entry.
            ordered = manifest.get(key, [])
            if key in manifest:
                files = [f for f in ordered if f in all_files]
            else:
                files = list(all_files)

            for i, fname in enumerate(files):
                entry = {"index": i + 1, "name": fname}
                result[key].append(entry)
        return web.json_response(result)

    @PromptServer.instance.routes.post("/bsai/save_asset_order")
    async def save_asset_order(request):
        """Save the current asset order from Asset Library widget values."""
        try:
            post = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        manifest_path = os.path.join(_get_asset_dir(""), "asset_order.json")
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(post, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
        return web.json_response({"ok": True})

    @PromptServer.instance.routes.post("/bsai/remove_all_assets")
    async def remove_all_assets(request):
        """Delete all files of a given asset type from disk."""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)
        asset_type = str(body.get("asset_type", ""))
        if asset_type not in ("images", "videos", "audio"):
            return web.json_response({"error": "Invalid asset_type"}, status=400)
        d = _get_asset_dir(asset_type)
        deleted = 0
        for fname in os.listdir(d):
            filepath = os.path.join(d, fname)
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    deleted += 1
            except OSError:
                pass
        return web.json_response({"ok": True, "deleted": deleted})

    @PromptServer.instance.routes.get("/bsai/list_fonts")
    async def list_fonts(request):
        """List system fonts from Windows Fonts folder."""
        fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        fonts = []
        if os.path.isdir(fonts_dir):
            for f in os.listdir(fonts_dir):
                if f.lower().endswith(('.ttf', '.otf', '.ttc')):
                    fonts.append(f)
        return web.json_response({"fonts": sorted(fonts)})

    @PromptServer.instance.routes.post("/bsai/scan_assets")
    async def scan_assets(request):
        """Legacy endpoint for directory-based scanning (backward compatibility)."""
        try:
            post = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        image_dir = post.get("image_directory", "")
        video_dir = post.get("video_directory", "")
        audio_dir = post.get("audio_directory", "")

        def resolve(path):
            if not path:
                return None
            p = path.strip().strip('"').strip("'")
            if os.path.isabs(p) and os.path.isdir(p):
                return p
            if _HAS_FOLDER_PATHS:
                for base_func in [folder_paths.get_input_directory, folder_paths.get_output_directory]:
                    full = os.path.join(base_func(), p)
                    if os.path.isdir(full):
                        return full
            return p if os.path.isdir(p) else None

        result = {"images": [], "videos": [], "audios": []}
        for dirpath, exts, key in [
            (resolve(image_dir), _IMG_EXTS, "images"),
            (resolve(video_dir), _VID_EXTS, "videos"),
            (resolve(audio_dir), _AUD_EXTS, "audios"),
        ]:
            if dirpath and os.path.isdir(dirpath):
                files = sorted(
                    [f for f in os.listdir(dirpath) if f.lower().endswith(exts)],
                    key=lambda s: s.lower()
                )
                for i, fname in enumerate(files):
                    fpath = os.path.join(dirpath, fname)
                    entry = {"index": i + 1, "name": fname, "thumbnail": _make_thumbnail(fpath)}
                    result[key].append(entry)

        return web.json_response(result)
