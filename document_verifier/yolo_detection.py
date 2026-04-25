"""Optional YOLO (Ultralytics) regions for document verification.

Set DOCUMENT_YOLO_MODEL to a local ``.pt`` path or a hub name such as ``yolov8n.pt``.
Train or obtain a document-specific model for meaningful tamper/field localization;
generic COCO weights are useful only to validate the integration.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

from .detection import Issue

_MODEL_CACHE: dict[str, Any] = {}


def resolve_yolo_model_source(model_source: str) -> str | None:
    """Return a string Ultralytics can load, or None if the path is missing / invalid.

    - Existing file paths are resolved absolutely.
    - Bare names like ``yolov8n.pt`` are passed through (hub download or cwd).
    - Placeholder or broken paths (e.g. ``E:\\path\\to\\file.pt``) return None so the app does not crash.
    """
    s = (model_source or "").strip()
    if not s:
        return None
    p = Path(s).expanduser()
    if p.is_file():
        return str(p.resolve())
    # Path contains directories or drive letter but file is missing — do not call YOLO()
    if "\\" in s or "/" in s or p.is_absolute():
        return None
    # Single-component id (hub weight name, e.g. yolov8n.pt)
    return s


def _sanitize_class_name(name: str) -> str:
    slug = "".join(c if c.isalnum() else "_" for c in name.strip().lower())
    slug = "_".join(p for p in slug.split("_") if p)
    raw = f"yolo_{slug}" if slug else "yolo_unknown"
    return raw[:80]


def detect_with_yolo(
    image_path: Path,
    model_source: str,
    *,
    conf: float = 0.35,
    max_det: int = 32,
) -> list[Issue]:
    """Run YOLO on ``image_path`` and return ``Issue`` boxes (empty if unavailable)."""
    raw = (model_source or "").strip()
    if not raw:
        return []

    resolved = resolve_yolo_model_source(raw)
    if resolved is None:
        warnings.warn(
            f"DOCUMENT_YOLO_MODEL is set but not usable ({raw!r}): file missing or not a valid hub name. "
            "Fix the path, use a hub id like yolov8n.pt for a quick test, or unset DOCUMENT_YOLO_MODEL to run without YOLO.",
            UserWarning,
            stacklevel=2,
        )
        return []

    try:
        from ultralytics import YOLO
    except ImportError:
        return []

    if resolved not in _MODEL_CACHE:
        _MODEL_CACHE[resolved] = YOLO(resolved)

    model = _MODEL_CACHE[resolved]
    results = model.predict(
        str(image_path),
        conf=conf,
        max_det=max_det,
        verbose=False,
    )
    issues: list[Issue] = []
    for result in results:
        names = getattr(result, "names", None) or {}
        if result.boxes is None or len(result.boxes) == 0:
            continue
        h, w = result.orig_shape[:2]
        for box in result.boxes:
            xyxy = box.xyxy[0].detach().cpu().numpy().tolist()
            x1, y1, x2, y2 = (int(round(v)) for v in xyxy)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            bw, bh = max(0, x2 - x1), max(0, y2 - y1)
            if bw < 2 or bh < 2:
                continue
            cls_id = int(box.cls[0].item()) if box.cls is not None else -1
            score = float(box.conf[0].item()) if box.conf is not None else 0.0
            raw_name = str(names.get(cls_id, f"class_{cls_id}"))
            issue_type = _sanitize_class_name(raw_name)
            issues.append(
                Issue(
                    issue_type,
                    score,
                    x1,
                    y1,
                    bw,
                    bh,
                    (
                        f"YOLO localized '{raw_name}' with confidence {score:.2f}. "
                        "Review this region against the rest of the document and source records."
                    ),
                )
            )
    return sorted(issues, key=lambda i: i.confidence, reverse=True)[: max_det]
