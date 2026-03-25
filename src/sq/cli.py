from __future__ import annotations

import json
import sys
from pathlib import Path

import rich_click as click
from pydantic import ValidationError

from sq.models import ShowConfig
from sq.show import create_show

TEMPLATE_DEFAULT = Path.home() / "Documents" / "SQ MixPad" / "SHOWS" / "SHOW0002"


@click.command()
@click.argument("config_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_path", type=click.Path(path_type=Path))
@click.option(
    "--template",
    type=click.Path(exists=True, path_type=Path),
    default=TEMPLATE_DEFAULT,
    show_default=True,
    help="Template show directory to copy from.",
)
def cli(config_file: Path, output_path: Path, template: Path) -> None:
    """Create an Allen & Heath SQ show from a JSON channel config."""
    raw = json.loads(config_file.read_text())

    try:
        config = ShowConfig(**raw)
    except ValidationError as e:
        click.echo(f"Invalid config: {e}", err=True)
        sys.exit(1)

    try:
        create_show(config, output_path, template)
    except (FileExistsError, FileNotFoundError) as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    click.echo(f"Show created at {output_path}")
