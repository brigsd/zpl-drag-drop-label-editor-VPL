# ZPL Visualizer - Documentação

## Índice
1. [Visão Geral](#visão-geral)
2. [Instalação](#instalação)
3. [Interface do Usuário](#interface-do-usuário)
4. [Funcionalidades](#funcionalidades)
5. [Atalhos de Teclado](#atalhos-de-teclado)
6. [Configurações](#configurações)
7. [Build do Executável](#build-do-executável)
8. [Arquitetura Técnica](#arquitetura-técnica)

---

## Visão Geral

O **ZPL Visualizer** é um editor visual para códigos ZPL (Zebra Programming Language), permitindo criar, editar e visualizar etiquetas em tempo real usando a API Labelary.

### Principais Recursos
- ✅ Editor de código ZPL com syntax highlighting
- ✅ Preview em tempo real via API Labelary
- ✅ Conversão de elementos para objetos arrastáveis (mini-objetos)
- ✅ Suporte a códigos de barras e textos
- ✅ Sistema de grade para alinhamento
- ✅ Zoom com Ctrl+Scroll
- ✅ Múltiplos temas visuais
- ✅ Configurações personalizáveis

---

## Instalação

### Requisitos
- Python 3.10+
- Conexão com internet (para API Labelary)

### Via Python
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
python src/main.py
```

### Via Executável
Basta executar `ZPL_Visualizer.exe`. Certifique-se de que `config.json` está na mesma pasta.

---

## Interface do Usuário

### Layout Principal
```
┌─────────────────────────────────────────────────────────────┐
│Barra Superior:Unit│DPI│Largura│Altura│Atualizar│Preferências│
├──────────────────────┬──────────────────────────────────────┤
│                      │                                      │
│   Editor ZPL         │       Canvas de Preview              │
│   (código)           │       (visualização)                 │
│                      │                                      │
├──────────────────────┼──────────────────────────────────────┤
│ Ferramentas:         │  Grade │ Alinhar │ Espaçamento       │
├──────────────────────┴──────────────────────────────────────┤

### Componentes
├──────────────────────────────┬───────────────────────────────────────────┤
| Componente                   | Descrição                                                        |
|------------------------------|------------------------------------------------------------------|
| **Editor ZPL**               | Campo de texto para código ZPL com syntax highlighting           |
| **Canvas**                   | Área de preview da etiqueta renderizada                          |
| **Ferramentas**              | Botões para seleção, texto, imagem, código de barras e conversão |
| **Configurações de Preview** | DPI, unidade, dimensões da etiqueta                              |

---

## Funcionalidades

### 1. Edição de Código ZPL
- **Auto-complete de wrappers**: Adiciona automaticamente `^XA` e `^XZ` se faltando
- **Syntax Highlighting**: Coloração de comandos ZPL
- **Atualização em tempo real**: Clique em "Atualizar Preview" para ver mudanças

### 2. Mini-Objetos (Modo Conversão)
Os mini-objetos permitem arrastar elementos individualmente:

1. Clique no botão **"Conv."** (Conversão)
2. Linhas convertíveis ficam destacadas (verde=texto, azul=código de barras)
3. Dê **duplo clique** em uma linha para convertê-la
4. O elemento se torna um objeto arrastável no canvas
5. Arraste para reposicionar
6. Clique em **"Atualizar Preview"** para aplicar a nova posição

### 3. Grade de Alinhamento
- Ative com o checkbox **"Grade"**
- Configure o espaçamento (10-100 pixels)
- Ative **"Alinhar"** para snap automático à grade

### 4. Zoom
- Use **Ctrl + Scroll** no canvas para zoom
- Intervalo: 10% a 400%

### 5. Edição de Elementos
- **Duplo clique** em um mini-objeto abre o modal de edição
- Para textos: edite conteúdo, posição X/Y, altura e largura da fonte
- Para códigos de barras: edite dados, posição e altura

---

## Atalhos de Teclado
--------------------------------------------------------------------------
| Atalho                  | Ação                                         |
|-------------------------|----------------------------------------------|
| `Ctrl + Scroll`         | Zoom in/out no canvas                        |
| `Duplo clique (editor)` | Converter linha para mini-objeto (modo Conv.)|
| `Duplo clique (canvas)` | Editar mini-objeto                           |
| `Arrastar`              | Mover mini-objeto                            |
--------------------------------------------------------------------------

---

## Configurações

### Preferências (Menu Preferências)
-------------------------------------------------------------------------
| Categoria             | Opções                                        |
|-----------------------|-----------------------------------------------|
| **Tema**              | Padrão, Escuro Laranja, Escuro Dourado, Cinza |
| **Tamanho do Canvas** | Largura e altura máximas                      |
| **Fontes**            | Família e tamanho para editor e UI            |
| **Tamanho da Janela** | Dimensões iniciais                            |
-------------------------------------------------------------------------

### Arquivo config.json
As configurações são salvas em `config.json`:
```json
{
  "max_canvas_width": 1000,
  "max_canvas_height": 937,
  "font_size": 12,
  "editor_font_family": "Consolas",
  "ui_font_size": 12,
  "ui_font_family": "Segoe UI",
  "window_width": 1400,
  "window_height": 700,
  "theme": "default"
}
```

---

## Build do Executável

### Requisitos
```bash
pip install pyinstaller
```

### Comando de Build
```bash
pyinstaller --noconfirm --onefile --windowed --name "ZPL_Visualizer" ^
    --add-data "src\config.json;." ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import barcode ^
    --hidden-import barcode.ean ^
    --hidden-import barcode.codex ^
    --hidden-import barcode.code128 ^
    --hidden-import barcode.writer ^
    src/main.py
```

### Distribuição
1. Copie `dist/ZPL_Visualizer.exe`
2. Copie `config.json` para a mesma pasta
3. Distribua ambos os arquivos

---

## Arquitetura Técnica

### Estrutura de Arquivos
```
visualizador_e_editorZpl VPL/
├── src/
│   ├── main.py           # Aplicação principal (Tkinter)
│   ├── zpl_utils.py      # Utilitários ZPL e renderização
│   ├── bitmap_fonts.py   # Fontes bitmap para renderização local
│   └── config.json       # Configurações
├── dist/
│   └── ZPL_Visualizer.exe
├── requirements.txt
├── build.bat
├── zpl_visualizer.spec
└── DOCUMENTATION.md
```

### Principais Classes e Funções

#### `ZPLVisualizerApp` (main.py)
Classe principal da aplicação Tkinter.
------------------------------------------------------------------------------------
| Método                                | Descrição                                |
|---------------------------------------|------------------------------------------|
| `fetch_labelary_preview()`            | Busca preview da etiqueta via API        |
| `criar_mini_objeto_labelary()`        | Cria mini-objeto arrastável              |
| `converter_linha_para_objeto()`       | Converte linha ZPL em mini-objeto        |
| `aplicar_mudancas()`                  | Atualiza coordenadas no código ZPL       |
| `aplicar_tema()`                      | Aplica tema visual selecionado           |
| `atualizar_grade()`                   | Desenha grade no canvas                  |
------------------------------------------------------------------------------------

#### `zpl_utils.py`

------------------------------------------------------------------------------------
| Função                                | Descrição                                |
|---------------------------------------|------------------------------------------|
| `fetch_labelary_element()`            | Busca elemento individual via Labelary   |
| `normalizar_zpl_para_mini_objeto()`   | Prepara snippet para renderização        |
| `render_scalable_text()`              | Renderiza texto ^A0 localmente           |
| `calcular_dimensoes_texto()`          | Calcula dimensões de texto ZPL           |
------------------------------------------------------------------------------------

### Fluxo de Dados
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Editor ZPL  │──▶│ API Labelary│──▶│   Canvas    │
│  (código)   │    │  (preview)  │    │ (imagem)    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                                     │
       │         ┌─────────────┐             │
       └────────▶│ Mini-Objetos│◀────────────┘
                 │ (arrastar)  │
                 └─────────────┘
```

---

## Suporte

### Problemas Comuns

----------------------------------------------------------------------------------------
| Problema                                | Solução                                    |
|-----------------------------------------|--------------------------------------------|
| Preview não atualiza                    | Verifique conexão com internet             |
| "Erro 429"                              | Aguarde 2 segundos entre requisições       | 
| Config não salva (exe)                  | Coloque config.json na mesma pasta do .exe |
| Grade não aparece                       | Verifique se há preview carregado          |
----------------------------------------------------------------------------------------

### API Labelary
- URL: `http://api.labelary.com/v1/printers/{dpmm}dpmm/labels/{w}x{h}/0/`
- Limite: ~1 requisição por segundo
- Formato: PNG

---

*Última atualização: Janeiro 2026* Tiago Marcondes Schadeck

---

## Easter Egg 🎮

```
                              ╔═══════════════════════════════════════╗
                              ║         A R C   R A I D E R S         ║
                              ╚═══════════════════════════════════════╝

                                           ┌───────┐
                                          ┌┴───────┴┐
                                         ┌┴─────────┴┐
                                        ╔╧═══════════╧╗
                                        ║  ◉       ◉ ║
                                        ║      ▼      ║
                                        ║   ╔═════╗   ║
                                        ╚═══╩═════╩═══╝
                                             │   │
                                    ╔════════╧═══╧════════╗
                                   ╔╝                     ╚╗
                                  ╔╝   ┌─────────────┐     ╚╗
                                 ╔╝    │  A R C  ◊   │      ╚╗
                                ╔╝     │  RAIDER     │       ╚╗
                               ╔╝      └─────────────┘        ╚╗
                              ╔╝                               ╚╗
                             ╔╝    ┌─┐               ┌─┐        ╚╗
                            ╔╝    ┌┘ └┐             ┌┘ └┐        ╚╗
                           ╔╝    ┌┘   └┐           ┌┘   └┐        ╚╗
                          ╔╝    ┌┘ ══╗ └┐         ┌┘ ╔══ └┐        ╚╗
                         ╔╝    ┌┘    ║  └┐       ┌┘  ║    └┐        ╚╗
                        ╔╝     │     ╚══╗│       │╔══╝     │         ╚╗
                       ╔╝      │        ╚╗       ╔╝        │          ╚╗
                      ╔╝       │         ║       ║         │           ╚╗
                     ╚═════════╧═════════╩═══════╩═════════╧═══════════╝
                                         │       │
                                        ┌┴┐     ┌┴┐
                                       ┌┘ └┐   ┌┘ └┐
                                      ┌┘   └┐ ┌┘   └┐
                                     ┌┘     └┬┘     └┐
                                    ┌┘       │       └┐
                                   ╔╝        │        ╚╗
                                  ╔╝        ╔╧╗        ╚╗
                                 ╔╝        ╔╝ ╚╗        ╚╗
                                ╔╝        ╔╝   ╚╗        ╚╗
                               ═╩═       ═╩═   ═╩═       ═╩═
                              ┌───┐     ┌───┐ ┌───┐     ┌───┐
                              │███│     │███│ │███│     │███│
                              └───┘     └───┘ └───┘     └───┘

                         ╔═══════════════════════════════════════════╗
                         ║   "The machines came from the sky..."     ║
                         ║        - Arc Raiders, Embark Studios      ║
                         ╚═══════════════════════════════════════════╝
```
