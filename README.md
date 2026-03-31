# sq

CLI tool for creating Allen & Heath SQ mixer show files from a JSON channel config.

Copies a clean template show and patches channel names into the binary NVDATA.DAT, recalculating the A&H CRC32 checksum.

## Usage

```
uv run sq <config.json> <output_path> [--template PATH]
```

## Example

```json
{
  "show_name": "Sunday Service",
  "channels": [
    {"type": "input", "number": 1, "name": "Kick"},
    {"type": "mix", "number": 1, "name": "MonDrm"},
    {"type": "group", "number": 1, "name": "Drums"}
  ]
}
```

## Channel types

| Type | Count | Description |
|------|-------|-------------|
| `input` | 1–48 | Input channels |
| `mix` | 1–12 | Mix outputs |
| `group` | 1–12 | Groups |
| `fx_return` | 1–8 | FX returns |
| `fx_send` | 1–4 | FX sends |
| `lr` | 1 | LR master |
| `matrix` | 1–3 | Matrix outputs |

Channel names are max 6 ASCII characters (mixer display limit).

## Setup

```
uv sync
```

## Binary format

See [PROTOCOL.md](PROTOCOL.md) for the reverse-engineered SQ show file format documentation.
