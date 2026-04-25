from pathlib import Path

from document_verifier.yolo_detection import resolve_yolo_model_source


def test_resolve_missing_absolute_path_returns_none():
    assert resolve_yolo_model_source(r"E:\nonexistent_folder\model.pt") is None


def test_resolve_missing_relative_subpath_returns_none():
    assert resolve_yolo_model_source("weights/missing.pt") is None


def test_resolve_bare_hub_name_returns_string():
    assert resolve_yolo_model_source("yolov8n.pt") == "yolov8n.pt"


def test_resolve_existing_file_returns_absolute_str(tmp_path: Path):
    weights = tmp_path / "best.pt"
    weights.write_bytes(b"fake")
    out = resolve_yolo_model_source(str(weights))
    assert out == str(weights.resolve())
