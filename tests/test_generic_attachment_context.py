from src.document_processor import build_user_content


class _UploadHandler:
    def __init__(self, uploads):
        self.uploads = uploads

    def resolve_upload(self, upload_id, owner=None):
        upload = self.uploads.get(upload_id)
        if upload and upload.get("owner") == owner:
            return dict(upload)
        return None

    def _inside_upload_dir(self, path):
        return True

    def is_image_file(self, filename, content_type=None):
        return False

    def is_audio_file(self, filename, content_type=None):
        return False

    def is_document_file(self, filename, content_type=None):
        return False


def test_generic_binary_attachment_includes_agent_usable_path(tmp_path):
    stl_path = tmp_path / "part.stl"
    stl_path.write_bytes(b"solid cube\nendsolid cube\n")
    handler = _UploadHandler({
        "abc123.stl": {
            "id": "abc123.stl",
            "name": "part.stl",
            "mime": "model/stl",
            "size": stl_path.stat().st_size,
            "path": str(stl_path),
            "owner": "alice",
        }
    })

    content = build_user_content(
        "Calculate this STL volume.",
        ["abc123.stl"],
        str(tmp_path),
        handler,
        owner="alice",
        expose_generic_attachment_paths=True,
    )

    assert "[Attached file: part.stl]" in content
    assert "- Upload id: abc123.stl" in content
    assert "- MIME type: model/stl" in content
    assert f"- Server path: {stl_path}" in content
    assert "use the server path above" in content
    assert "[Attached non-text file]" not in content


def test_generic_binary_attachment_omits_path_by_default(tmp_path):
    stl_path = tmp_path / "part.stl"
    stl_path.write_bytes(b"solid cube\nendsolid cube\n")
    handler = _UploadHandler({
        "abc123.stl": {
            "id": "abc123.stl",
            "name": "part.stl",
            "mime": "model/stl",
            "size": stl_path.stat().st_size,
            "path": str(stl_path),
            "owner": "alice",
        }
    })

    content = build_user_content(
        "What is this file?",
        ["abc123.stl"],
        str(tmp_path),
        handler,
        owner="alice",
    )

    assert "[Attached file: part.stl]" in content
    assert "- Upload id: abc123.stl" in content
    assert "Switch to agent mode" in content
    assert "Server path:" not in content
    assert str(stl_path) not in content


def test_generic_binary_attachment_does_not_leak_unresolved_upload(tmp_path):
    stl_path = tmp_path / "bob.stl"
    stl_path.write_bytes(b"solid bob\nendsolid bob\n")
    handler = _UploadHandler({
        "bob.stl": {
            "id": "bob.stl",
            "name": "bob.stl",
            "mime": "model/stl",
            "size": stl_path.stat().st_size,
            "path": str(stl_path),
            "owner": "bob",
        }
    })

    content = build_user_content(
        "Read this file.",
        ["bob.stl"],
        str(tmp_path),
        handler,
        owner="alice",
    )

    assert content == "Read this file."
    assert str(stl_path) not in content
