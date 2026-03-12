# ⚙️ Documentação Técnica — ZPL Label Editor

Documentação da arquitetura e código-fonte do ZPL Label Editor.

---

## Arquitetura Geral

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────┐
│   main.py    │────▶│   zpl_utils.py   │────▶│ API Labelary  │
│  (Frontend)  │     │  (Processamento) │     │  (Renderização)│
└──────────────┘     └──────────────────┘     └───────────────┘
       │                     │
       ▼                     ▼
┌──────────────┐     ┌──────────────────┐
│ config.json  │     │ bitmap_fonts.py  │
│  (Config)    │     │ (Fontes locais)  │
└──────────────┘     └──────────────────┘
```

---

## Arquivos

### `src/main.py` — Aplicação Principal
Contém a classe `ZPLVisualizerApp` que gerencia toda a interface Tkinter e a lógica do editor.

### `src/zpl_utils.py` — Utilitários ZPL
Funções auxiliares para processamento, normalização e renderização de código ZPL.

### `src/bitmap_fonts.py` — Fontes Bitmap
Fontes bitmap para renderização local de texto (fallback quando não usa Labelary).

### `src/config.json` — Configurações
Armazena preferências do usuário em formato JSON.

---

## Classe Principal: `ZPLVisualizerApp`

### Variáveis de Estado

| Variável | Tipo | Descrição |
|----------|------|-----------|
| `mini_objetos` | `dict` | Mini-objetos no canvas. Chave = ID do item, Valor = `{zpl, x, y, photo, image_raw, params, barcode_offset_x}` |
| `linhas_convertidas` | `list` | Snippets ZPL que foram convertidos em mini-objetos |
| `linhas_convertiveis` | `dict` | Linhas que podem ser convertidas (preenchido no modo conversão) |
| `modo_conversao_ativo` | `bool` | Se o modo de conversão está ativo |
| `zoom_level` | `float` | Nível de zoom atual (1.0 = 100%) |
| `scale_factor` | `float` | Fator de escala para grade |
| `canvas_margin` | `int` | Margem do canvas (10px) |
| `ferramenta_selecionada` | `str\|None` | Ferramenta ativa: `None`, `'texto'`, `'codigo_barras'`, `'converter'` |
| `theme` | `str` | Tema atual: `'default'`, `'classic_dark'`, `'modern_dark'`, `'modern_light'` |

---

### Métodos — Inicialização

| Método | Descrição |
|--------|-----------|
| `__init__()` | Inicializa variáveis de estado, carrega config, configura UI, aplica tema |
| `_setup_ui()` | Cria todos os widgets: sidebar, editor, canvas, controles |
| `_setup_bindings()` | Configura eventos: `<Configure>`, clique, duplo clique, zoom, paste |

---

### Métodos — Preview e Renderização

| Método | Descrição |
|--------|-----------|
| `fetch_labelary_preview()` | Coleta dados da UI e inicia thread de preview. Inclui debounce de 1.5s |
| `_executar_preview_labelary()` | Thread de background. Filtra snippets convertidos, chama API Labelary |
| `_atualizar_canvas_com_preview()` | Recebe imagem e atualiza o canvas (thread principal). Calcula auto-fit zoom |
| `atualizar_tudo()` | Limpa mini-objetos e regenera preview completo |
| `limpar_mini_objetos()` | Remove todos mini-objetos do canvas e do dicionário |

#### Fluxo de Preview:
```
fetch_labelary_preview() → [Main Thread]
    ├── Coleta ZPL do editor
    ├── Auto-adiciona ^XA/^XZ
    ├── Snapshot de linhas_convertidas
    └── Inicia thread →
         _executar_preview_labelary() → [Background Thread]
             ├── Filtra snippets convertidos do ZPL
             ├── POST para API Labelary
             └── Callback →
                  _atualizar_canvas_com_preview() → [Main Thread]
                      ├── Auto-fit zoom
                      └── Exibe imagem no canvas
```

---

### Métodos — Mini-Objetos (Drag & Drop)

| Método | Descrição |
|--------|-----------|
| `criar_mini_objeto_labelary()` | Cria mini-objeto: normaliza ZPL, busca imagem no Labelary, posiciona no canvas |
| `converter_linha_para_objeto()` | Converte linha do editor: adiciona a `linhas_convertidas`, regenera preview, cria mini-objeto |
| `destacar_linhas_convertiveis()` | Analisa o código e destaca linhas que podem ser convertidas (regex) |
| `editar_mini_objeto()` | Abre modal de edição para texto |
| `abrir_janela_edicao_codigo_barras()` | Abre modal de edição para código de barras |
| `atualizar_mini_objeto()` | Atualiza ZPL do mini-objeto e re-renderiza |

#### Compensação de Código de Barras:
Códigos de barras usam um `left_offset` para evitar corte do primeiro dígito na renderização. O `barcode_offset_x` é armazenado e compensado:
- **Ao criar:** `canvas_x = posição_original - offset` (visual mais preciso)
- **Ao salvar:** `zpl_x = canvas_x + offset` (coordenada ZPL correta)

---

### Métodos — Arrasto e Posicionamento

| Método | Descrição |
|--------|-----------|
| `ao_pressionar_elemento()` | Armazena posição inicial ao clicar |
| `ao_arrastar_elemento()` | Move elemento com mouse. Respeita travas X/Y, mostra coordenadas |
| `ao_soltar_arrasto()` | Snap à grade (se ativo), chama `aplicar_mudancas()` |
| `aplicar_mudancas()` | Atualiza `^FO` no código ZPL com novas coordenadas. Compensa `barcode_offset_x` |
| `canvas_para_zpl()` | Converte coordenadas canvas → ZPL (remove margem e zoom) |
| `zpl_para_canvas()` | Converte coordenadas ZPL → canvas (adiciona margem e zoom) |

---

### Métodos — Zoom

| Método | Descrição |
|--------|-----------|
| `ao_scroll_zoom()` | Ctrl+Scroll: ajusta `zoom_level` (+/- 5% por notch), chama `aplicar_zoom()` |
| `aplicar_zoom()` | Redimensiona preview de fundo, reposiciona mini-objetos, atualiza grade |

---

### Métodos — Interface e Tema

| Método | Descrição |
|--------|-----------|
| `aplicar_tema()` | Aplica cores do tema a todos os widgets recursivamente |
| `aplicar_fonte_ui()` | Aplica família e tamanho da fonte a widgets da interface |
| `estilizar_modal()` | Aplica tema e fonte a janelas modais |
| `abrir_preferencias()` | Abre modal de preferências com todas as configurações |
| `atualizar_grade()` | Desenha/remove grade no canvas baseado em DPI e dimensões |
| `ao_redimensionar()` | Atualiza label de resolução ao redimensionar janela |

---

### Métodos — Configuração

| Método | Descrição |
|--------|-----------|
| `carregar_configuracoes()` | Lê `config.json`. Usa `get_base_path()` para funcionar no .exe |
| `salvar_configuracoes()` | Salva em `config.json` |

---

## Funções Globais

### `get_base_path()`
Retorna o diretório correto para `config.json`:
- **Modo desenvolvimento:** `os.path.dirname(__file__)` → pasta `src/`
- **Modo executável:** `os.path.dirname(sys.executable)` → pasta do `.exe`

---

## `zpl_utils.py` — Funções

| Função | Descrição |
|--------|-----------|
| `fetch_labelary_element()` | Busca imagem de elemento ZPL individual via API Labelary. Auto-crop whitespace |
| `normalizar_zpl_para_mini_objeto()` | Remove `^FO` original, adiciona `^FO0,0`, envolve com `^XA...^XZ` |
| `extrair_parametros_texto()` | Extrai `x`, `y`, `altura`, `largura`, `texto` de um snippet ZPL via regex |
| `calcular_dimensoes_texto()` | Calcula dimensões em mm baseado em fonte, DPI e orientação |
| `render_scalable_text()` | Renderiza texto `^A0` usando TrueType (Arial) com escala independente W/H |
| `render_bitmap_text()` | Renderiza texto usando fontes bitmap customizadas |
| `zpl_gfa_to_image()` | Converte dados hexadecimais `^GFA` de volta para imagem PIL |
| `redimensionar_imagem_codigo_barras()` | Redimensiona imagem de código de barras por fator |

---

## `bitmap_fonts.py`

Contém definições de fontes bitmap para renderização local de texto ZPL. Usado como fallback quando a API Labelary não é utilizada.

| Função/Constante | Descrição |
|-------------------|-----------|
| `FONT_A_WIDTH` | Largura padrão da fonte A em pixels |
| `FONT_A_HEIGHT` | Altura padrão da fonte A em pixels |
| `get_char_bitmap()` | Retorna bitmap de um caractere específico |

---

## API Labelary

O programa usa a API Labelary para renderização:

```
POST http://api.labelary.com/v1/printers/{dpmm}dpmm/labels/{w}x{h}/0/
Content-Type: multipart/form-data
Body: file=<código ZPL>
Response: image/png
```

| Parâmetro | Valores |
|-----------|---------|
| `dpmm` | 8 (203 DPI), 12 (300 DPI), 24 (600 DPI) |
| `w` | Largura em polegadas |
| `h` | Altura em polegadas |
| Limite | ~1 req/segundo (erro 429 se exceder) |

---

## Empacotamento (PyInstaller)

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

| Flag | Propósito |
|------|-----------|
| `--onefile` | Gera um único `.exe` |
| `--windowed` | Sem janela de console |
| `--add-data` | Inclui `config.json` |
| `--hidden-import` | Dependências não detectadas automaticamente |

---

*Autor: Tiago Marcondes Schadeck — Março 2026*
