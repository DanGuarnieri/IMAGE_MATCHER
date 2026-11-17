from pathlib import Path
from PIL import Image
import imagehash


def calcular_hash(imagem_path: Path):
    """Calcula o pHash de uma imagem. Retorna None se não conseguir processá-la."""
    try:
        with Image.open(imagem_path) as imagem:
            return imagehash.phash(imagem.convert("L"))
    except Exception:
        return None
