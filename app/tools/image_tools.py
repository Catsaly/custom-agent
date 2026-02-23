"""Image upload, processing, and analysis tools."""
import base64
import io
from pathlib import Path
from typing import Optional
from PIL import Image


class ImageTools:
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    MAX_SIZE_MB = 20
    MAX_DIMENSION = 2048

    def validate(self, content: bytes, media_type: str) -> None:
        if media_type not in self.ALLOWED_TYPES:
            raise ValueError(f"Unsupported image type: {media_type}")
        if len(content) > self.MAX_SIZE_MB * 1024 * 1024:
            raise ValueError(f"Image exceeds {self.MAX_SIZE_MB}MB limit")

    def to_base64(self, content: bytes) -> str:
        return base64.standard_b64encode(content).decode("utf-8")

    def resize_if_needed(self, content: bytes) -> bytes:
        img = Image.open(io.BytesIO(content))
        if max(img.size) > self.MAX_DIMENSION:
            ratio = self.MAX_DIMENSION / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            buffer = io.BytesIO()
            fmt = img.format or "PNG"
            img.save(buffer, format=fmt)
            return buffer.getvalue()
        return content

    def get_info(self, content: bytes) -> dict:
        img = Image.open(io.BytesIO(content))
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "size_bytes": len(content),
        }

    async def process_upload(
        self, content: bytes, media_type: str, filename: str
    ) -> dict:
        self.validate(content, media_type)
        content = self.resize_if_needed(content)
        info = self.get_info(content)
        b64 = self.to_base64(content)
        return {
            "filename": filename,
            "media_type": media_type,
            "base64": b64,
            "info": info,
        }

    def save_to_disk(self, content: bytes, filename: str, base_path: str = "workspace/uploads") -> str:
        path = Path(base_path)
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / filename
        file_path.write_bytes(content)
        return str(file_path)
