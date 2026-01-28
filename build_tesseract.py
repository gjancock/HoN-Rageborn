import hashlib
import zipfile
import os
from pathlib import Path

# ============================================================
# CONFIG — EDIT IF NEEDED
# ============================================================

# This folder MUST exist before running this script
# Structure expected:
#
# tesseract_runtime/
# ├─ tesseract.exe
# └─ tessdata/
#    └─ eng.traineddata
#
TESSERACT_SOURCE_DIR = Path("tesseract_runtime")

# Output artifacts
OUTPUT_ZIP = Path("tesseract-5.3.3-win64.zip")

# ============================================================
# HELPERS
# ============================================================

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_zip_sha256(zip_path: Path):
    sha = sha256_of_file(zip_path)
    sha_file = zip_path.with_suffix(".zip.sha256")

    sha_file.write_text(
        f"{sha}  {zip_path.name}\n",
        encoding="utf-8"
    )

    print(f"[OK] Generated checksum: {sha_file.name}")
    return sha


# ============================================================
# BUILD
# ============================================================

def build():
    if not TESSERACT_SOURCE_DIR.exists():
        raise RuntimeError(
            f"Tesseract source dir not found: {TESSERACT_SOURCE_DIR}"
        )

    print("[INFO] Building Tesseract runtime ZIP...")

    with zipfile.ZipFile(
        OUTPUT_ZIP,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as z:

        for root, _, files in os.walk(TESSERACT_SOURCE_DIR):
            for file in files:
                full_path = Path(root) / file

                # Preserve folder name `tesseract/` in zip
                rel_path = full_path.relative_to(
                    TESSERACT_SOURCE_DIR.parent
                )

                z.write(full_path, rel_path)

    sha = write_zip_sha256(OUTPUT_ZIP)

    print("\n=== TESSERACT RELEASE READY ===")
    print(f"ZIP     : {OUTPUT_ZIP.name}")
    print(f"SHA256  : {sha}")
    print("\nUpload BOTH files to GitHub Releases:")
    print(f"- {OUTPUT_ZIP.name}")
    print(f"- {OUTPUT_ZIP.with_suffix('.zip.sha256').name}")


if __name__ == "__main__":
    build()
