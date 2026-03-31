# SQ Show Creator

See PROTOCOL.md for binary format documentation.

When you learn something new about the SQ binary format (offsets, block mappings, field sizes, etc.), always update PROTOCOL.md to reflect the finding.

## Commands

- `uv run ruff check src/` — lint
- `uv run pyright src/` — type check
- `uv run sq <config.json> <output_path>` — create show

## Local Resources

- **SQ MixPad app**: `/Applications/SQ MixPad 1.6.0.app`
- **MixPad binary**: `/Applications/SQ MixPad 1.6.0.app/Contents/MacOS/SQ MixPad`
- **Show files**: `~/Documents/SQ MixPad/SHOWS/`
  - `SHOW0000` — worship show with named channels
  - `SHOW0001` — another named show
  - `SHOW0002` — clean default show (used as template)
