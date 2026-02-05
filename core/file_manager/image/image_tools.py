"""
Image Tools
===========
Image processing: resize, convert, compress, batch operations.
"""

from typing import List, Dict, Tuple, Optional
from pathlib import Path

from core.logging import app_logger


class ImageTools:
    """Image processing tools."""

    @staticmethod
    def resize(image_path: str, output_path: str,
               size: Tuple[int, int] = None,
               scale: float = None) -> Dict:
        """
        Resize an image.

        Args:
            image_path: Source image path
            output_path: Output path
            size: Target size (width, height)
            scale: Scale factor (e.g., 0.5 for half size)

        Returns:
            Dict with results
        """
        from PIL import Image

        try:
            img = Image.open(image_path)
            original_size = img.size

            if scale:
                new_size = (int(img.width * scale), int(img.height * scale))
            elif size:
                new_size = size
            else:
                return {"success": False, "message": "Must specify size or scale"}

            resized = img.resize(new_size, Image.Resampling.LANCZOS)
            resized.save(output_path)

            return {
                "success": True,
                "original_size": original_size,
                "new_size": new_size,
            }
        except Exception as e:
            app_logger.error(f"Resize failed: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def convert(image_path: str, output_path: str,
                fmt: str = "PNG") -> Dict:
        """
        Convert image format.

        Args:
            image_path: Source image
            output_path: Output path
            fmt: Target format ('PNG', 'JPEG', 'BMP', 'WEBP', 'TIFF')

        Returns:
            Dict with results
        """
        from PIL import Image

        try:
            img = Image.open(image_path)

            # Handle RGBA -> JPEG
            if fmt.upper() == "JPEG" and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.save(output_path, format=fmt.upper())

            return {
                "success": True,
                "original_format": img.format or Path(image_path).suffix,
                "new_format": fmt.upper(),
            }
        except Exception as e:
            app_logger.error(f"Convert failed: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def compress(image_path: str, output_path: str,
                 quality: int = 85) -> Dict:
        """
        Compress an image.

        Args:
            image_path: Source image
            output_path: Output path
            quality: JPEG quality (1-100)

        Returns:
            Dict with compression stats
        """
        from PIL import Image

        try:
            img = Image.open(image_path)
            original_size = Path(image_path).stat().st_size

            if output_path.lower().endswith('.png'):
                img.save(output_path, optimize=True)
            else:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(output_path, quality=quality, optimize=True)

            compressed_size = Path(output_path).stat().st_size

            return {
                "success": True,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "reduction_percent": round(
                    (1 - compressed_size / original_size) * 100, 1
                ) if original_size > 0 else 0,
            }
        except Exception as e:
            app_logger.error(f"Compress failed: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def rotate(image_path: str, output_path: str,
               angle: float, expand: bool = True) -> Dict:
        """
        Rotate an image.

        Args:
            image_path: Source image
            output_path: Output path
            angle: Rotation angle in degrees
            expand: Whether to expand output to fit rotated image

        Returns:
            Dict with results
        """
        from PIL import Image

        try:
            img = Image.open(image_path)
            rotated = img.rotate(angle, expand=expand)
            rotated.save(output_path)

            return {
                "success": True,
                "angle": angle,
                "original_size": img.size,
                "new_size": rotated.size,
            }
        except Exception as e:
            app_logger.error(f"Rotate failed: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def crop(image_path: str, output_path: str,
             box: Tuple[int, int, int, int]) -> Dict:
        """
        Crop an image.

        Args:
            image_path: Source image
            output_path: Output path
            box: (left, upper, right, lower) crop coordinates

        Returns:
            Dict with results
        """
        from PIL import Image

        try:
            img = Image.open(image_path)
            cropped = img.crop(box)
            cropped.save(output_path)

            return {
                "success": True,
                "original_size": img.size,
                "crop_box": box,
                "new_size": cropped.size,
            }
        except Exception as e:
            app_logger.error(f"Crop failed: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_info(image_path: str) -> Dict:
        """
        Get image information.

        Args:
            image_path: Image file path

        Returns:
            Dict with image metadata
        """
        from PIL import Image

        try:
            img = Image.open(image_path)
            file_size = Path(image_path).stat().st_size

            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "file_size": file_size,
                "file_size_formatted": _format_size(file_size),
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def batch_process(image_paths: List[str], output_folder: str,
                      operations: List[Dict]) -> List[Dict]:
        """
        Batch process multiple images with the same operations.

        Args:
            image_paths: List of source image paths
            output_folder: Output directory
            operations: List of operation dicts:
                - {"type": "resize", "size": (w, h)} or {"type": "resize", "scale": 0.5}
                - {"type": "convert", "format": "JPEG"}
                - {"type": "rotate", "angle": 90}
                - {"type": "compress", "quality": 85}

        Returns:
            List of result dicts per image
        """
        from PIL import Image

        Path(output_folder).mkdir(parents=True, exist_ok=True)
        results = []

        for path in image_paths:
            try:
                img = Image.open(path)

                for op in operations:
                    op_type = op.get("type", "")

                    if op_type == "resize":
                        if "scale" in op:
                            new_size = (
                                int(img.width * op["scale"]),
                                int(img.height * op["scale"]),
                            )
                        else:
                            new_size = op.get("size", img.size)
                        img = img.resize(new_size, Image.Resampling.LANCZOS)

                    elif op_type == "convert":
                        target_fmt = op.get("format", "PNG")
                        if target_fmt.upper() == "JPEG" and img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")

                    elif op_type == "rotate":
                        img = img.rotate(op.get("angle", 0), expand=True)

                # Determine output format
                fmt = "PNG"
                for op in operations:
                    if op.get("type") == "convert":
                        fmt = op.get("format", "PNG")

                filename = Path(path).stem
                ext = fmt.lower()
                if ext == "jpeg":
                    ext = "jpg"
                output_path = str(Path(output_folder) / f"{filename}.{ext}")

                quality = 95
                for op in operations:
                    if op.get("type") == "compress":
                        quality = op.get("quality", 85)

                if fmt.upper() == "PNG":
                    img.save(output_path, optimize=True)
                else:
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(output_path, quality=quality, optimize=True)

                results.append({
                    "file": path,
                    "success": True,
                    "output": output_path,
                })

            except Exception as e:
                results.append({
                    "file": path,
                    "success": False,
                    "error": str(e),
                })

        return results

    @staticmethod
    def create_thumbnail(image_path: str, output_path: str,
                         max_size: Tuple[int, int] = (200, 200)) -> Dict:
        """
        Create a thumbnail.

        Args:
            image_path: Source image
            output_path: Thumbnail output path
            max_size: Maximum size (width, height)

        Returns:
            Dict with results
        """
        from PIL import Image

        try:
            img = Image.open(image_path)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(output_path)

            return {
                "success": True,
                "thumbnail_size": img.size,
            }
        except Exception as e:
            return {"success": False, "message": str(e)}


def _format_size(size_bytes: int) -> str:
    """Format file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
