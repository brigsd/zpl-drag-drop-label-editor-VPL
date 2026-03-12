# 🖥️ Interface Guide — ZPL Label Editor

Complete explanation of every element in the ZPL Label Editor interface.

---

## General Layout

The interface is divided into 4 main areas:

```
┌──────┬──────────────────────────────────────────────────────┐
│      │  Menu: Settings > Preferences                        │
│  S   ├────────────────────┬─────────────────────────────────┤
│  I   │                    │                                 │
│  D   │  ZPL Code          │    Preview Canvas               │
│  E   │  Editor            │    (Label visualization)        │
│  B   │                    │                                 │
│  A   ├────────────────────┤                                 │
│  R   │ Label Settings     │                                 │
│      │ [DPI][Unit][W][H]  ├─────────────────────────────────┤
│      │ [Update Preview]   │ [Movement] [Grid] [Resolution]  │
└──────┴────────────────────┴─────────────────────────────────┘
```

---

## 1. Sidebar (Tools)

The sidebar on the left contains the main tools:

### 🔤 "T" Button — Text
- **What it does:** Activates text creation mode
- **How to use:** Click the button, then click on the canvas to insert a text element
- **Result:** Inserts `^FO{x},{y}^A0N,30,30^FDText^FS` in the ZPL code

### ║║║║ "||||" Button — Barcode
- **What it does:** Activates barcode creation mode
- **How to use:** Click the button, then click on the canvas to insert a barcode
- **Result:** Inserts `^FO{x},{y}^BY2^BUN,80^FD0000000000^FS` in the ZPL code

### ↖ "Selection" Button
- **What it does:** Returns to selection mode (normal cursor)
- **How to use:** Click to deactivate any tool and return to select/drag mode

### ⟳ "Convert" Button
- **What it does:** Activates **conversion mode** — the core drag-and-drop feature
- **How to use:**
  1. Click the "Convert" button
  2. Convertible code lines become **highlighted** in the editor:
     - 🟢 **Green** = Text elements
     - 🟠 **Orange** = Barcodes
  3. **Double-click** a highlighted line
  4. The element becomes a **draggable mini-object** on the canvas
  5. Drag to reposition
  6. Click **"Update Preview"** to apply the new position

> **💡 Tip:** When you convert a line, the main preview automatically regenerates WITHOUT that element, and the element appears as an independent object you can freely move.

---

## 2. ZPL Code Editor (Left Column)

### Text Field
- **What it is:** Text editor where you write or paste ZPL code
- **Features:**
  - **Automatic Syntax Highlighting:**
    - Dark red (`^FO`, `^A0`, `^BY`) = Commands
    - Teal (numbers, parameters) = Parameters
  - **Auto-complete `^XA`/`^XZ`** — Added automatically when clicking "Update Preview"
  - **Smart paste** — Syntax highlighting reapplied after pasting

---

## 3. Label Settings

Below the editor, inside the "Label Settings" group:

| Control | Options | Description |
|---------|---------|-------------|
| **DPI** | 203, 300 | Printer resolution (203=8dpmm, 300=12dpmm) |
| **Unit** | mm, cm, inches | Measurement unit for label dimensions |
| **Width** | 1-300 | Label width (default: 54mm) |
| **Height** | 1-300 | Label height (default: 38mm) |
| **Update Preview** | Button | Sends ZPL to Labelary API and renders the label |

---

## 4. Preview Canvas (Right Column)

### Interactions
| Action | Result |
|--------|--------|
| Single click (with tool active) | Place new element |
| Double-click on mini-object | Open edit dialog |
| Drag mini-object | Move element |
| Ctrl + Scroll | Zoom (10% to 400%) |

---

## 5. Controls Below Preview

### Movement Group
- **Lock X:** Prevents horizontal movement
- **Lock Y:** Prevents vertical movement

### Grid Group
- **Show:** Toggle grid visibility
- **Snap:** Elements snap to grid points when released
- **Spacing:** Grid spacing (10, 50, 100, or 1000 pixels)

### Resolution Indicator
- Bottom-right corner, shows current window dimensions

---

## 6. Settings > Preferences

| Category | Options |
|----------|---------|
| **Theme** | Default, Dark Orange, Dark Gold, Gray |
| **Editor Font** | Family (Consolas, Courier New, etc.) + Size |
| **UI Font** | Family (Segoe UI, Arial, etc.) + Size |
| **Canvas Size** | Max width and height (pixels) |
| **Window Size** | Initial width and height |

---

## 7. Edit Dialogs

### Text Edit (double-click on text)
- **Text:** Content of `^FD`
- **Position X/Y:** Coordinates of `^FO`
- **Height/Width:** Font parameters of `^A0`

### Barcode Edit (double-click on barcode)
- **Data:** Content of `^FD` (barcode numbers)
- **Position X/Y:** Coordinates of `^FO`
- **Height:** Bar height

---

## 8. Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Scroll` | Canvas zoom |
| `Double-click` (editor, Conv. mode) | Convert line to mini-object |
| `Double-click` (canvas) | Edit mini-object |
| `Drag` | Move mini-object |

---

*Author: Tiago Marcondes Schadeck — March 2026*
