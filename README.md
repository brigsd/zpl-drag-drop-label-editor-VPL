# 🏷️ ZPL Label Editor — Drag & Drop Visual Editor

**Editor visual de etiquetas ZPL com arrastar e soltar** | **Visual ZPL label editor with drag-and-drop**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()

---

## 🇧🇷 Português

### O que é?

O **ZPL Label Editor** é uma ferramenta visual para criar e editar etiquetas ZPL (Zebra Programming Language). Diferente de editores tradicionais onde você precisa escrever coordenadas manualmente, aqui você pode **arrastar elementos diretamente na tela** e o código ZPL é atualizado automaticamente.

### ✨ Principais Funcionalidades

- 🖱️ **Arrastar e Soltar** — Converta linhas de código em objetos visuais arrastáveis
- 👁️ **Preview em Tempo Real** — Visualize a etiqueta via API Labelary
- 🎨 **Syntax Highlighting** — Código ZPL colorido para fácil leitura
- 📊 **Códigos de Barras** — Suporte completo a criação e edição
- 📐 **Grade de Alinhamento** — Grade com snap para posicionamento preciso
- 🔍 **Zoom** — Ctrl+Scroll para zoom de 10% a 400%
- 🎭 **Temas** — 4 temas visuais (Padrão, Escuro Laranja, Escuro Dourado, Cinza)
- ⚙️ **Configurável** — Fontes, tamanhos e dimensões personalizáveis

### 🚀 Como Usar

#### Opção 1: Executável (Recomendado)
> **Não precisa ter Python instalado!**

1. Baixe o arquivo `ZPL_Visualizer.exe` da pasta `dist/`
2. Execute o arquivo
3. Pronto! O programa abre direto

#### Opção 2: Via Python
```bash
pip install -r requirements.txt
python src/main.py
```

### 📖 Documentação

| Documento | Descrição |
|-----------|-----------|
| [Guia da Interface (PT)](docs/GUI_PT.md) | Explicação completa de cada botão e funcionalidade |
| [Interface Guide (EN)](docs/GUI_EN.md) | Complete guide for every button and feature |
| [Documentação do Código (PT)](docs/BACKEND_PT.md) | Arquitetura e explicação técnica do código |
| [Code Documentation (EN)](docs/BACKEND_EN.md) | Architecture and technical code explanation |

---

## 🇺🇸 English

### What is it?

**ZPL Label Editor** is a visual tool for creating and editing ZPL (Zebra Programming Language) labels. Unlike traditional editors where you need to manually type coordinates, here you can **drag elements directly on the canvas** and the ZPL code updates automatically.

### ✨ Key Features

- 🖱️ **Drag and Drop** — Convert code lines into draggable visual objects
- 👁️ **Real-time Preview** — Visualize labels via Labelary API
- 🎨 **Syntax Highlighting** — Color-coded ZPL code for easy reading
- 📊 **Barcodes** — Full barcode creation and editing support
- 📐 **Alignment Grid** — Grid with snap for precise positioning
- 🔍 **Zoom** — Ctrl+Scroll for 10% to 400% zoom
- 🎭 **Themes** — 4 visual themes (Default, Dark Orange, Dark Gold, Gray)
- ⚙️ **Configurable** — Customizable fonts, sizes, and dimensions

### 🚀 How to Use

#### Option 1: Executable (Recommended)
> **No Python installation required!**

1. Download `ZPL_Visualizer.exe` from the `dist/` folder
2. Run the file
3. Done! The program opens immediately

#### Option 2: Via Python
```bash
pip install -r requirements.txt
python src/main.py
```

### 📖 Documentation

| Document | Description |
|----------|-------------|
| [Guia da Interface (PT)](docs/GUI_PT.md) | Complete interface guide in Portuguese |
| [Interface Guide (EN)](docs/GUI_EN.md) | Complete guide for every button and feature |
| [Documentação do Código (PT)](docs/BACKEND_PT.md) | Architecture and code explanation in Portuguese |
| [Code Documentation (EN)](docs/BACKEND_EN.md) | Architecture and technical code explanation |

---

## 📁 Estrutura do Projeto / Project Structure

```
zpl-label-editor/
├── src/
│   ├── main.py              # Aplicação principal / Main application
│   ├── zpl_utils.py          # Utilitários ZPL / ZPL utilities
│   ├── bitmap_fonts.py       # Renderização de fontes / Font rendering
│   └── config.json           # Configurações / Settings
├── dist/
│   └── ZPL_Visualizer.exe    # Executável / Executable
├── docs/
│   ├── GUI_PT.md             # Guia da Interface (PT)
│   ├── GUI_EN.md             # Interface Guide (EN)
│   ├── BACKEND_PT.md         # Documentação técnica (PT)
│   └── BACKEND_EN.md         # Technical documentation (EN)
├── _historico/               # Versões anteriores / Previous versions
├── requirements.txt
└── README.md
```

---

## 🛠️ Tecnologias / Technologies

- **Python 3.10+** com Tkinter
- **Pillow (PIL)** para manipulação de imagem
- **API Labelary** para renderização ZPL
- **python-barcode** para geração de códigos de barras
- **PyInstaller** para empacotamento do executável

---

## 👤 Autor / Author

**Tiago Marcondes Schadeck** — [@brigsd](https://github.com/brigsd)

---

*Última atualização / Last update: Março 2026*
