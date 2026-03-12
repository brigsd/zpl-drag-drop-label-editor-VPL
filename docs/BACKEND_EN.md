# ⚙️ Technical Documentation — ZPL Label Editor

Architecture and source code documentation for the ZPL Label Editor.

---

## Architecture Overview

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────┐
│   main.py    │────▶│   zpl_utils.py   │────▶│ Labelary API  │
│  (Frontend)  │     │  (Processing)    │     │  (Rendering)  │
└──────────────┘     └──────────────────┘     └───────────────┘
       │                     │
       ▼                     ▼
┌──────────────┐     ┌──────────────────┐
│ config.json  │     │ bitmap_fonts.py  │
│  (Settings)  │     │ (Local fonts)    │
└──────────────┘     └──────────────────┘
```

---

## Files

| File | Purpose |
|------|---------|
| `src/main.py` | Main app — `ZPLVisualizerApp` class with Tkinter UI and editor logic |
| `src/zpl_utils.py` | ZPL processing, normalization, and rendering utilities |
| `src/bitmap_fonts.py` | Bitmap fonts for local text rendering (fallback) |
| `src/config.json` | User preferences in JSON format |

---

## Main Class: `ZPLVisualizerApp`

### State Variables

| Variable | Type | Description |
|----------|------|-------------|
| `mini_objetos` | `dict` | Canvas mini-objects. Key=item ID, Value=`{zpl, x, y, photo, image_raw, params, barcode_offset_x}` |
| `linhas_convertidas` | `list` | ZPL snippets converted to mini-objects |
| `linhas_convertiveis` | `dict` | Lines eligible for conversion (populated in conversion mode) |
| `modo_conversao_ativo` | `bool` | Whether conversion mode is active |
| `zoom_level` | `float` | Current zoom level (1.0 = 100%) |
| `scale_factor` | `float` | Scale factor for grid calculations |
| `canvas_margin` | `int` | Canvas margin (10px) |
| `ferramenta_selecionada` | `str\|None` | Active tool: `None`, `'texto'`, `'codigo_barras'`, `'converter'` |
| `theme` | `str` | Current theme: `'default'`, `'classic_dark'`, `'modern_dark'`, `'modern_light'` |

---

### Methods — Preview & Rendering

| Method | Description |
|--------|-------------|
| `fetch_labelary_preview()` | Collects UI data, starts background preview thread. Includes 1.5s debounce |
| `_executar_preview_labelary()` | Background thread: filters converted snippets, calls Labelary API |
| `_atualizar_canvas_com_preview()` | Receives image and updates canvas (main thread). Calculates auto-fit zoom |
| `atualizar_tudo()` | Clears mini-objects and regenerates full preview |
| `limpar_mini_objetos()` | Removes all mini-objects from canvas and tracking dict |

#### Preview Flow:
```
fetch_labelary_preview() → [Main Thread]
    ├── Collects ZPL from editor
    ├── Auto-adds ^XA/^XZ if missing
    ├── Snapshots linhas_convertidas
    └── Starts thread →
         _executar_preview_labelary() → [Background Thread]
             ├── Filters converted snippets from ZPL
             ├── POST to Labelary API
             └── Callback →
                  _atualizar_canvas_com_preview() → [Main Thread]
                      ├── Auto-fit zoom
                      └── Displays image on canvas
```

---

### Methods — Mini-Objects (Drag & Drop)

| Method | Description |
|--------|-------------|
| `criar_mini_objeto_labelary()` | Creates mini-object: normalizes ZPL, fetches image from Labelary, positions on canvas |
| `converter_linha_para_objeto()` | Converts editor line: adds to `linhas_convertidas`, regenerates preview, creates mini-object |
| `destacar_linhas_convertiveis()` | Analyzes code and highlights convertible lines via regex |
| `editar_mini_objeto()` | Opens text edit modal |
| `abrir_janela_edicao_codigo_barras()` | Opens barcode edit modal |
| `atualizar_mini_objeto()` | Updates mini-object ZPL and re-renders |

#### Barcode Position Compensation:
Barcodes use a `left_offset` to prevent first-digit clipping during rendering. The `barcode_offset_x` is stored and compensated:
- **On creation:** `canvas_x = original_position - offset` (more accurate visual)
- **On save:** `zpl_x = canvas_x + offset` (correct ZPL coordinate)

---

### Methods — Dragging & Positioning

| Method | Description |
|--------|-------------|
| `ao_pressionar_elemento()` | Stores initial position on click |
| `ao_arrastar_elemento()` | Moves element with mouse. Respects X/Y locks, shows coordinates |
| `ao_soltar_arrasto()` | Snaps to grid (if active), calls `aplicar_mudancas()` |
| `aplicar_mudancas()` | Updates `^FO` in ZPL code with new coordinates. Compensates `barcode_offset_x` |
| `canvas_para_zpl()` | Converts canvas → ZPL coordinates (removes margin and zoom) |
| `zpl_para_canvas()` | Converts ZPL → canvas coordinates (adds margin and zoom) |

---

### Methods — Zoom

| Method | Description |
|--------|-------------|
| `ao_scroll_zoom()` | Ctrl+Scroll: adjusts `zoom_level` (±5% per notch), calls `aplicar_zoom()` |
| `aplicar_zoom()` | Resizes background preview, repositions mini-objects, updates grid |

---

### Methods — UI & Theming

| Method | Description |
|--------|-------------|
| `aplicar_tema()` | Applies theme colors to all widgets recursively |
| `aplicar_fonte_ui()` | Applies font family and size to UI widgets |
| `estilizar_modal()` | Applies theme and font to modal windows |
| `abrir_preferencias()` | Opens preferences modal with all settings |
| `atualizar_grade()` | Draws/removes grid based on DPI and dimensions |
| `ao_redimensionar()` | Updates resolution label when window is resized |

---

### Methods — Configuration

| Method | Description |
|--------|-------------|
| `carregar_configuracoes()` | Reads `config.json`. Uses `get_base_path()` to work in .exe |
| `salvar_configuracoes()` | Writes to `config.json` |

---

## Global Functions

### `get_base_path()`
Returns the correct directory for `config.json`:
- **Development mode:** `os.path.dirname(__file__)` → `src/` folder
- **Executable mode:** `os.path.dirname(sys.executable)` → `.exe` folder

---

## `zpl_utils.py` — Functions

| Function | Description |
|----------|-------------|
| `fetch_labelary_element()` | Fetches individual ZPL element image via Labelary API. Auto-crops whitespace |
| `normalizar_zpl_para_mini_objeto()` | Removes original `^FO`, adds `^FO0,0`, wraps with `^XA...^XZ` |
| `extrair_parametros_texto()` | Extracts `x`, `y`, `height`, `width`, `text` from ZPL snippet via regex |
| `calcular_dimensoes_texto()` | Calculates dimensions in mm based on font, DPI, and orientation |
| `render_scalable_text()` | Renders `^A0` text using TrueType (Arial) with independent W/H scaling |
| `render_bitmap_text()` | Renders text using custom bitmap fonts |
| `zpl_gfa_to_image()` | Converts `^GFA` hex data back to PIL image |
| `redimensionar_imagem_codigo_barras()` | Resizes barcode image by factor |

---

## `bitmap_fonts.py`

Contains bitmap font definitions for local ZPL text rendering.

| Function/Constant | Description |
|--------------------|-------------|
| `FONT_A_WIDTH` | Default Font A width in pixels |
| `FONT_A_HEIGHT` | Default Font A height in pixels |
| `get_char_bitmap()` | Returns bitmap for a specific character |

---

## Labelary API

The program uses the Labelary API for rendering:

```
POST http://api.labelary.com/v1/printers/{dpmm}dpmm/labels/{w}x{h}/0/
Content-Type: multipart/form-data
Body: file=<ZPL code>
Response: image/png
```

| Parameter | Values |
|-----------|--------|
| `dpmm` | 8 (203 DPI), 12 (300 DPI), 24 (600 DPI) |
| `w` | Width in inches |
| `h` | Height in inches |
| Rate limit | ~1 req/second (429 error if exceeded) |

---

## Packaging (PyInstaller)

```bash
pyinstaller --onefile --windowed --name "ZPL_Visualizer" \
    --add-data "src\config.json;." \
    --hidden-import PIL._tkinter_finder \
    --hidden-import barcode \
    --hidden-import barcode.ean \
    --hidden-import barcode.codex \
    --hidden-import barcode.code128 \
    --hidden-import barcode.writer \
    src/main.py
```

| Flag | Purpose |
|------|---------|
| `--onefile` | Single `.exe` output |
| `--windowed` | No console window |
| `--add-data` | Includes `config.json` |
| `--hidden-import` | Dependencies not auto-detected |

---

*Author: Tiago Marcondes Schadeck — March 2026*
