import os
from pathlib import Path
from typing import Optional


# ============================================================
# Documents directory
# ============================================================

def get_documents_dir() -> Path:
    return Path(os.path.expanduser("~")) / "Documents"


def find_startup_cfg() -> Optional[Path]:
    docs = get_documents_dir()
    candidates = [
        docs / "Juvio" / "Heroes of Newerth" / "startup.cfg"
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


# ============================================================
# UTF-16LE safe replacement helpers
# ============================================================

UTF16_QUOTE = b'\x22\x00'  # " in UTF-16LE


def replace_utf16_value(data: bytes, key: str, new_value: str, logger) -> tuple[bytes, bool]:
    """
    Replace value inside quotes for:
        SetSave "key" "value"
    in UTF-16LE encoded binary.
    """

    key_utf16 = f'SetSave "{key}" '.encode("utf-16le")

    start = data.find(key_utf16)
    if start == -1:
        logger.warning(f"[CFG] {key} key not found")
        return data, False

    # find opening quote
    val_start = data.find(UTF16_QUOTE, start + len(key_utf16))
    if val_start == -1:
        logger.warning(f"[CFG] {key} opening quote not found")
        return data, False

    val_start += len(UTF16_QUOTE)

    # find closing quote
    val_end = data.find(UTF16_QUOTE, val_start)
    if val_end == -1:
        logger.warning(f"[CFG] {key} closing quote not found")
        return data, False

    new_bytes = new_value.encode("utf-16le")

    patched = (
        data[:val_start]
        + new_bytes
        + data[val_end:]
    )

    #logger.info(f"[CFG] {key} patched")
    return patched, True


# ============================================================
# Main patch function
# ============================================================

def patch_startup_cfg(
    cfg_path: Path,
    window_mode: int,
    width: int,
    height: int,
    logger
) -> bool:
    try:
        data = cfg_path.read_bytes()
    except Exception as e:
        logger.error(f"[CFG] Failed to read file: {e}")
        return False

    changed = False

    data, ok1 = replace_utf16_value(
        data,
        "vid_windowMode",
        str(window_mode),
        logger
    )
    changed |= ok1

    data, ok2 = replace_utf16_value(
        data,
        "vid_resolution",
        f"{width},{height},0",
        logger
    )
    changed |= ok2

    if not changed:
        logger.warning("[CFG] No values modified")
        return False

    try:
        cfg_path.write_bytes(data)
    except Exception as e:
        logger.error(f"[CFG] Failed to write file: {e}")
        return False

    logger.info(
        f"[INFO] startup.cfg patched"
    )
    return True


def prepare_game_config(
    logger,
    window_mode: int = 2,
    width: int = 1024,
    height: int = 768,
) -> bool:
    cfg = find_startup_cfg()
    if not cfg:
        logger.warning("[CFG] startup.cfg not found")
        return False

    logger.info(f"[CFG] Found startup.cfg at: {cfg}")
    return patch_startup_cfg(cfg, window_mode, width, height, logger)
