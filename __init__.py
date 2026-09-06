from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

try:
    from .nodes_asset import NODE_CLASS_MAPPINGS as ASSET_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as ASSET_DISPLAY
    NODE_CLASS_MAPPINGS.update(ASSET_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(ASSET_DISPLAY)
except Exception as e:
    print(f"[BSAI Contextual-Series] nodes_asset import failed: {e}")

try:
    from .nodes_clip import NODE_CLASS_MAPPINGS as CLIP_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as CLIP_DISPLAY
    NODE_CLASS_MAPPINGS.update(CLIP_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(CLIP_DISPLAY)
except Exception as e:
    print(f"[BSAI Contextual-Series] nodes_clip import failed: {e}")

try:
    from .nodes_subtitle import NODE_CLASS_MAPPINGS as SUBTITLE_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as SUBTITLE_DISPLAY
    NODE_CLASS_MAPPINGS.update(SUBTITLE_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(SUBTITLE_DISPLAY)
except Exception as e:
    print(f"[BSAI Contextual-Series] nodes_subtitle import failed: {e}")

try:
    from .nodes_media import NODE_CLASS_MAPPINGS as MEDIA_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as MEDIA_DISPLAY
    NODE_CLASS_MAPPINGS.update(MEDIA_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(MEDIA_DISPLAY)
except Exception as e:
    print(f"[BSAI Contextual-Series] nodes_media import failed: {e}")

try:
    from . import server
except Exception as e:
    print(f"[BSAI Contextual-Series] server module load failed: {e}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

WEB_DIRECTORY = "./web"
