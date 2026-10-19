"""GodRender provider/model router; honest about ONNX vs deterministic backends."""
from __future__ import annotations
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from core_adapter import CORE

CANONICAL = Path(__file__).resolve().parents[1]/"upstream/mainv2-lab/current-main"

def _engine():
    # Only a machine-attested core counts for real production model inference.
    if not CORE.status().get("bootstrapped"):
        raise RuntimeError("GodRender runtime bootstrap required")
    root=Path(CORE.core_repo).resolve()
    if not (root/"general/reusable/intelligence/MODEL_REGISTRY.json").is_file():
        raise RuntimeError("approved model registry missing")
    if str(root) not in sys.path:
        sys.path.insert(0,str(root))
    return root

def _models(root):
    from general.reusable.tools.model_registry import ModelRegistry
    return ModelRegistry.load(path=root/"general/reusable/intelligence/MODEL_REGISTRY.json",repo_root=root)

def options():
    """Only report executable local backends; do not mislabel renderers as neural models."""
    return {
      "schema":"godrender.provider-catalog.v1",
      "providers":[
        {"id":"beat-this-onnx","capability":"music","kind":"onnx_model","available":bool(importlib.util.find_spec("onnxruntime")) and CORE.status().get("bootstrapped",False),"artifact_required":True},
        {"id":"micro-dsp","capability":"music","kind":"deterministic_dsp","available":CORE.status().get("bootstrapped",False)},
        {"id":"still-fx","capability":"image_to_video","kind":"deterministic_render","available":bool(shutil.which("ffmpeg")) and bool(importlib.util.find_spec("cv2"))},
        {"id":"video-fx","capability":"video_to_video","kind":"deterministic_render","available":bool(shutil.which("ffmpeg")) and bool(importlib.util.find_spec("cv2"))},
        {"id":"godot-scene","capability":"procedural_3d_video","kind":"native_godot_render","available":bool(shutil.which("godot")) and bool(shutil.which("ffmpeg"))},
        {"id":"generative-image-model","capability":"image_generation","kind":"external_model","available":False,"reason":"no approved generation model/provider has been configured"},
        {"id":"generative-video-model","capability":"video_generation","kind":"external_model","available":False,"reason":"no approved generation model/provider has been configured"},
        {"id":"generative-3d-model","capability":"3d_generation","kind":"external_model","available":False,"reason":"no approved generation model/provider has been configured"},
      ],
      "production_authority":"evidence_only",
    }

def select(capability, *, requested=None):
    providers=[x for x in options()["providers"] if x["capability"]==capability]
    if requested:
        providers=[x for x in providers if x["id"]==requested]
    if not providers:
        raise ValueError("unknown provider capability/id")
    chosen=next((x for x in providers if x["available"]),None)
    if chosen is None:
        return {"available":False,"capability":capability,"requested":requested,"candidates":providers,"reason":"no installed or approved provider for this capability"}
    return {"available":True,"capability":capability,"chosen":chosen}

def music_analysis(path, *, allow_provision=None):
    """Called automatically by Studio Media analysis; never hides DSP fallback."""
    root=_engine()
    from general.reusable.tools.model_registry import ModelRegistry
    from general.reusable.tools.music_beat_worker import analyze_music
    model=_models(root)
    provision_error=None
    should_provision=(
        allow_provision if allow_provision is not None else
        os.environ.get("GODRENDER_ONNX_AUTOPROVISION","1").lower() in {"1","true","yes"}
    )
    if should_provision and importlib.util.find_spec("onnxruntime") is not None:
        resolution=model.resolve("music-beat-onnx-v1")
        if resolution.used_fallback:
            try:
                from general.reusable.tools.model_provision import provision
                provision("music-beat-onnx-v1",repo_root=root)
                model=_models(root)
            except Exception as exc:
                provision_error=type(exc).__name__+": "+str(exc)[:280]
    evidence=analyze_music(str(path),registry=model)
    # Model evidence never authorizes a story, creative FX or release.
    evidence["production_authority"]="evidence_only"
    if provision_error:
        evidence["provision_warning"]=provision_error
    return evidence
