from __future__ import annotations

import shutil
from pathlib import Path

from sq.binary import update_crc, write_channel_name, write_show_name
from sq.models import ShowConfig


def create_show(
    config: ShowConfig,
    output_path: Path,
    template_path: Path,
) -> None:
    """Create a new SQ show by copying a template and patching channel names.

    Args:
        config: Show configuration with channel names.
        output_path: Destination directory for the new show.
        template_path: Path to the template show directory.

    Raises:
        FileExistsError: If output_path already exists.
        FileNotFoundError: If template_path or required files are missing.
    """
    if output_path.exists():
        raise FileExistsError(f"Output path already exists: {output_path}")

    nvdata_src = template_path / "NVDATA.DAT"
    show_dat_src = template_path / "SHOW.DAT"

    if not nvdata_src.exists():
        raise FileNotFoundError(f"Template missing NVDATA.DAT: {nvdata_src}")
    if not show_dat_src.exists():
        raise FileNotFoundError(f"Template missing SHOW.DAT: {show_dat_src}")

    # Create full AHSQ folder structure
    show_dir = output_path / "SHOWS" / "SHOW0000"
    shutil.copytree(template_path, show_dir)
    (output_path / "LIBRARY").mkdir(parents=True, exist_ok=True)
    (output_path / "SCENES").mkdir(parents=True, exist_ok=True)

    # Patch NVDATA.DAT with channel names
    nvdata_path = show_dir / "NVDATA.DAT"
    nvdata = bytearray(nvdata_path.read_bytes())

    for ch in config.channels:
        write_channel_name(nvdata, ch.type, ch.number, ch.name)

    update_crc(nvdata)
    nvdata_path.write_bytes(nvdata)

    # Patch SHOW.DAT with show name
    show_dat_path = show_dir / "SHOW.DAT"
    show_dat = bytearray(show_dat_path.read_bytes())
    write_show_name(show_dat, config.show_name)
    show_dat_path.write_bytes(show_dat)
