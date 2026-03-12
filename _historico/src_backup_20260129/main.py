import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from PIL import ImageTk, Image
import re
import threading
import requests
import io
import barcode
from barcode.writer import ImageWriter
from zpl_utils import (
    image_to_zpl, redimensionar_imagem_codigo_barras, zpl_gfa_to_image, 
    render_bitmap_text, render_scalable_text, fetch_labelary_element,
    calcular_dimensoes_texto, normalizar_zpl_para_mini_objeto, extrair_parametros_texto
)

class ZPLVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualizador de Etiquetas ZPL")
        self.root.geometry("1400x700")  # Two column layout (wider, less tall)
        
        # State variables
        self.tamanhos_codigo_barras = {}
        self.janela_redimensionada = False
        self.elementos_movidos = []
        self.deslocamento_x = 0
        self.deslocamento_y = 0
        
        # Canvas specific state
        self.canvas_element_current = None
        self.canvas_x_current = 0
        self.canvas_y_current = 0
        
        # Tool state
        self.ferramenta_selecionada = None  # None, 'texto', 'imagem', 'codigo_barras'
        self.elemento_selecionado = None  # Canvas item ID of currently selected element
        self.handles_redimensionar = []  # List of handle item IDs
        
        # Labelary Preview state (NEW)
        self.mini_objetos = {}  # {canvas_item_id: {'zpl': snippet, 'x': x, 'y': y, 'match_start': s, 'match_end': e}}
        self.imagem_preview_fundo = None  # PhotoImage reference for background
        self.item_preview_fundo = None  # Canvas item ID for background image
        self.redimensionamento_habilitado = False  # Disable resize handles
        
        # Conversion mode state (NEW)
        self.modo_conversao_ativo = False  # True when "Conv." tool is selected
        self.linhas_convertiveis = {}  # {linha_num: {'snippet': str, 'params': dict}}
        self.linhas_convertidas = []  # List of ZPL snippets that became mini-objects

        self._setup_ui()
        self._setup_bindings()
        
        # Initial ZPL Wrapper
        if not self.entrada_texto.get("1.0", "end-1c").strip():
            self.entrada_texto.insert("1.0", "^XA\n\n\n\n^XZ")
        
        # Apply initial syntax highlighting
        self.root.after(10, self.aplicar_syntax_highlight)
        
        # Initial update
        self.root.after(1, self.atualizar_visualizacao)

    def _setup_ui(self):
        # Configure main grid - sidebar on left, content area on right
        self.root.columnconfigure(0, weight=0, minsize=80)  # Sidebar
        self.root.columnconfigure(1, weight=1)  # Main content area
        self.root.rowconfigure(0, weight=1)
        
        # ===== SIDEBAR =====
        self.sidebar = tk.Frame(self.root, bg="#f0f0f0", width=80)
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=2, pady=2)
        self.sidebar.grid_propagate(False)
        
        # Sidebar title
        tk.Label(self.sidebar, text="Ferramentas", bg="#f0f0f0", font=("Arial", 9, "bold")).pack(pady=5)
        
        # Tool buttons
        self.botao_texto = tk.Button(self.sidebar, text="T", font=("Arial", 18, "bold"), width=3, height=1,
                                      command=lambda: self.selecionar_ferramenta('texto'))
        self.botao_texto.pack(pady=3)
        tk.Label(self.sidebar, text="Texto", bg="#f0f0f0", font=("Arial", 8)).pack()
        
        # self.botao_imagem = tk.Button(self.sidebar, text="🖼", font=("Arial", 16), width=3, height=1,
        #                                command=lambda: self.selecionar_ferramenta('imagem'))
        # self.botao_imagem.pack(pady=3)
        # tk.Label(self.sidebar, text="Imagem", bg="#f0f0f0", font=("Arial", 8)).pack()
        
        self.botao_codigo_barras = tk.Button(self.sidebar, text="||||", font=("Arial", 14), width=3, height=1,
                                              command=lambda: self.selecionar_ferramenta('codigo_barras'))
        self.botao_codigo_barras.pack(pady=3)
        tk.Label(self.sidebar, text="Cód.Barras", bg="#f0f0f0", font=("Arial", 8)).pack()
        
        # Separator
        tk.Frame(self.sidebar, height=2, bg="#cccccc").pack(fill=tk.X, pady=10, padx=5)
        
        # Deselect tool button
        self.botao_selecao = tk.Button(self.sidebar, text="↖", font=("Arial", 16), width=3, height=1,
                                        command=lambda: self.selecionar_ferramenta(None))
        self.botao_selecao.pack(pady=3)
        tk.Label(self.sidebar, text="Seleção", bg="#f0f0f0", font=("Arial", 8)).pack()
        
        # Convert to object button
        self.botao_converter = tk.Button(self.sidebar, text="⟳", font=("Arial", 16), width=3, height=1,
                                          command=lambda: self.selecionar_ferramenta('converter'))
        self.botao_converter.pack(pady=3)
        tk.Label(self.sidebar, text="Conv.", bg="#f0f0f0", font=("Arial", 8)).pack()
        
        # ===== MAIN CONTENT (Two Columns: Left=ZPL, Right=Preview) =====
        self.main_frame = tk.Frame(self.root)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)  # Left column (ZPL) expands
        self.main_frame.columnconfigure(1, weight=0)  # Right column (Preview) fixed
        self.main_frame.rowconfigure(0, weight=1)  # Main row expands
        
        # ===== LEFT COLUMN: ZPL Code =====
        self.frame_esquerdo = tk.Frame(self.main_frame)
        self.frame_esquerdo.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.frame_esquerdo.rowconfigure(0, weight=1)  # Text entry expands
        self.frame_esquerdo.columnconfigure(0, weight=1)
        
        # ZPL Text Entry (expands to fill)
        self.entrada_texto = tk.Text(self.frame_esquerdo, height=25, width=50, font=("Consolas", 12))
        self.entrada_texto.grid(row=0, column=0, sticky="nsew", pady=5)
        
        # Configure syntax highlighting tags (Labelary style)
        self.entrada_texto.tag_configure("comando", foreground="#8B0000")  # Dark red for commands
        self.entrada_texto.tag_configure("parametro", foreground="#008080")  # Teal for parameters
        self.entrada_texto.tag_configure("convertivel", background="#90EE90")  # Light green for convertible lines
        
        # Row 1: Labelary Config (DPI, Unidade, Largura, Altura)
        self.frame_config_labelary = tk.Frame(self.frame_esquerdo)
        self.frame_config_labelary.grid(row=1, column=0, sticky="w", pady=3)
        
        # DPI
        tk.Label(self.frame_config_labelary, text="DPI:").pack(side=tk.LEFT, padx=2)
        self.combo_dpi = ttk.Combobox(self.frame_config_labelary, values=["203", "300"], width=5, state="readonly")
        self.combo_dpi.current(1)  # Default 300
        self.combo_dpi.pack(side=tk.LEFT, padx=2)
        
        # Unidade
        tk.Label(self.frame_config_labelary, text="Unidade:").pack(side=tk.LEFT, padx=2)
        self.combo_unit = ttk.Combobox(self.frame_config_labelary, values=["mm", "cm", "inches"], width=7, state="readonly")
        self.combo_unit.current(0)  # Default mm
        self.combo_unit.pack(side=tk.LEFT, padx=2)
        
        # Largura
        tk.Label(self.frame_config_labelary, text="Largura:").pack(side=tk.LEFT, padx=2)
        self.spin_width = tk.Spinbox(self.frame_config_labelary, from_=1, to=300, width=5)
        self.spin_width.delete(0, "end")
        self.spin_width.insert(0, "54")  # Default 54mm
        self.spin_width.pack(side=tk.LEFT, padx=2)
        
        # Altura
        tk.Label(self.frame_config_labelary, text="Altura:").pack(side=tk.LEFT, padx=2)
        self.spin_height = tk.Spinbox(self.frame_config_labelary, from_=1, to=300, width=5)
        self.spin_height.delete(0, "end")
        self.spin_height.insert(0, "38")  # Default 38mm
        self.spin_height.pack(side=tk.LEFT, padx=2)
        
        # Row 2: Update Button
        self.frame_botoes = tk.Frame(self.frame_esquerdo)
        self.frame_botoes.grid(row=2, column=0, sticky="w", pady=5)
        
        self.botao_atualizar = tk.Button(self.frame_botoes, text="Atualizar Preview", command=self.atualizar_tudo)
        self.botao_atualizar.pack(side=tk.LEFT, padx=5)
        self.botao_atualizar.config(font=("Arial", 10, "bold"))
        
        # Coordinates Label
        self.rotulo_coordenadas = tk.Label(self.frame_botoes, text="")
        self.rotulo_coordenadas.pack(side=tk.LEFT, padx=10)
        
        # ===== RIGHT COLUMN: Preview =====
        self.frame_direito = tk.Frame(self.main_frame)
        self.frame_direito.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Row 0: Canvas (Preview Area) - NOW FIRST
        # Calculate fixed canvas size based on default dimensions (54x38mm at 300 DPI)
        # 300 DPI = 12 dpmm, so: 54*12 = 648 pixels, 38*12 = 456 pixels
        default_dpmm = 12  # 300 DPI
        default_width_mm = 54
        default_height_mm = 38
        canvas_width_px = int(default_width_mm * default_dpmm) + 20  # +20 for border margin
        canvas_height_px = int(default_height_mm * default_dpmm) + 20
        
        self.canvas = tk.Canvas(self.frame_direito, bg="white", width=canvas_width_px, height=canvas_height_px)
        self.canvas.pack(pady=5)
        self.canvas.dados_codigo_barras = {}
        self.canvas.dados_texto_bitmap = {}
        self.canvas.dados_zpl_posicao = {}
        
        # Store canvas offset (margin for the viewport)
        self.canvas_margin = 10
        
        # Viewport Rectangle (visual border) - matches configured dimensions
        self.retangulo = self.canvas.create_rectangle(
            self.canvas_margin, 
            self.canvas_margin, 
            self.canvas_margin + int(default_width_mm * default_dpmm), 
            self.canvas_margin + int(default_height_mm * default_dpmm),
            outline="#cccccc"
        )
        
        # Row 1: Controls BELOW preview (axis locks + position snap)
        self.frame_preview_controls = tk.Frame(self.frame_direito)
        self.frame_preview_controls.pack(fill=tk.X, pady=5)
        
        # Axis lock checkboxes
        self.trava_eixo_x = tk.BooleanVar()
        self.trava_eixo_y = tk.BooleanVar()
        
        self.botao_trava_x = tk.Checkbutton(self.frame_preview_controls, text="Travar eixo X", variable=self.trava_eixo_x)
        self.botao_trava_x.pack(side=tk.LEFT, padx=5)
        
        self.botao_trava_y = tk.Checkbutton(self.frame_preview_controls, text="Travar eixo Y", variable=self.trava_eixo_y)
        self.botao_trava_y.pack(side=tk.LEFT, padx=5)
        
        # Separator
        tk.Label(self.frame_preview_controls, text="|").pack(side=tk.LEFT, padx=5)
        
        # Grid checkbox
        self.grade_ativa = tk.BooleanVar()
        self.check_grade = tk.Checkbutton(self.frame_preview_controls, text="Ativar grade", 
                                           variable=self.grade_ativa, command=self.atualizar_grade)
        self.check_grade.pack(side=tk.LEFT, padx=5)
        
        # Grid spacing dropdown
        tk.Label(self.frame_preview_controls, text="Espaço:").pack(side=tk.LEFT, padx=2)
        self.combo_espacamento_grade = ttk.Combobox(self.frame_preview_controls, values=[10, 50, 100, 1000], width=5, state="readonly")
        self.combo_espacamento_grade.current(1)  # Default 50
        self.combo_espacamento_grade.pack(side=tk.LEFT, padx=2)
        self.combo_espacamento_grade.bind("<<ComboboxSelected>>", lambda e: self.atualizar_grade())
        
        # Snap to grid checkbox
        self.alinhar_grade = tk.BooleanVar()
        self.check_alinhar = tk.Checkbutton(self.frame_preview_controls, text="Alinhar à grade", 
                                             variable=self.alinhar_grade)
        self.check_alinhar.pack(side=tk.LEFT, padx=5)
        
        # Store grid line IDs for cleanup
        self.linhas_grade = []



    def _setup_bindings(self):
        self.root.bind("<Configure>", self.ao_redimensionar)
        # Canvas click for placing elements when tool selected
        self.canvas.bind("<Button-1>", self.ao_clicar_canvas)
        # Double-click for editing
        self.canvas.bind("<Double-Button-1>", self.ao_duplo_clique_canvas)
        
        # Bind Paste Event
        self.entrada_texto.bind("<<Paste>>", self.ao_colar_texto)
        
        # Bind syntax highlighting (on key release for performance)
        self.entrada_texto.bind("<KeyRelease>", self.aplicar_syntax_highlight)
        # Also apply on paste
        self.entrada_texto.bind("<<Paste>>", lambda e: self.root.after(10, self.aplicar_syntax_highlight), add="+")
        
        # Double-click on editor for conversion mode
        self.entrada_texto.bind("<Double-Button-1>", self.ao_duplo_clique_editor)
    
    def atualizar_grade(self):
        """Draw or remove the grid on the canvas."""
        # Clear existing grid lines
        for linha_id in self.linhas_grade:
            try:
                self.canvas.delete(linha_id)
            except:
                pass
        self.linhas_grade = []
        
        if not self.grade_ativa.get():
            return
        
        # Get grid spacing
        try:
            espacamento = int(self.combo_espacamento_grade.get())
        except:
            espacamento = 50
        
        # Get canvas/viewport dimensions
        margin = getattr(self, 'canvas_margin', 10)
        dpmm = 12 if self.combo_dpi.get() == "300" else 8
        
        try:
            width_mm = float(self.spin_width.get())
            height_mm = float(self.spin_height.get())
        except:
            width_mm, height_mm = 54, 38
        
        canvas_w = int(width_mm * dpmm)
        canvas_h = int(height_mm * dpmm)
        
        # Grid line color (light gray)
        cor_grade = "#d0d0d0"
        
        # Draw vertical lines
        x = espacamento
        while x < canvas_w:
            linha_id = self.canvas.create_line(
                margin + x, margin,
                margin + x, margin + canvas_h,
                fill=cor_grade, tags=("grade",)
            )
            self.linhas_grade.append(linha_id)
            # Bring to front (on top of other elements)
            self.canvas.tag_raise(linha_id)
            x += espacamento
        
        # Draw horizontal lines
        y = espacamento
        while y < canvas_h:
            linha_id = self.canvas.create_line(
                margin, margin + y,
                margin + canvas_w, margin + y,
                fill=cor_grade, tags=("grade",)
            )
            self.linhas_grade.append(linha_id)
            self.canvas.tag_raise(linha_id)
            y += espacamento
    
    def aplicar_syntax_highlight(self, event=None):
        """Apply Labelary-style syntax highlighting to ZPL code."""
        # Remove existing tags
        self.entrada_texto.tag_remove("comando", "1.0", tk.END)
        self.entrada_texto.tag_remove("parametro", "1.0", tk.END)
        
        codigo = self.entrada_texto.get("1.0", tk.END)
        
        # Two patterns needed:
        # 1. Barcode commands: ^B followed by digit/letter IS part of command (^B0, ^B1, ^BC, etc.)
        # 2. Other commands: just 1-2 letters, trailing digits are parameters
        
        # Pattern for barcode commands: ^B[0-9A-Z] (digit/letter is part of command)
        barcode_pattern = r'([~^])(B[0-9A-Z])((?:,?[\d\.]+)+)?'
        
        for match in re.finditer(barcode_pattern, codigo):
            # Highlight command
            cmd_start = f"1.0+{match.start()}c"
            cmd_end = f"1.0+{match.end(2)}c"
            self.entrada_texto.tag_add("comando", cmd_start, cmd_end)
            
            # Highlight parameters if present
            if match.group(3):
                param_start = f"1.0+{match.start(3)}c"
                param_end = f"1.0+{match.end(3)}c"
                self.entrada_texto.tag_add("parametro", param_start, param_end)
        
        # Pattern for other commands: ^XX or ~XX (1-2 letters, NO trailing digit in command)
        # Excludes ^B[0-9A-Z] which is handled above as barcode
        other_pattern = r'([~^])([A-Z@][A-Z]?)((?:[\d,\.]+)+)?'
        
        for match in re.finditer(other_pattern, codigo):
            cmd_name = match.group(2)
            # Skip if this is a barcode command (starts with B followed by alphanumeric)
            if cmd_name.startswith('B') and len(cmd_name) == 2 and cmd_name[1].isalnum():
                continue
            
            # Highlight command
            cmd_start = f"1.0+{match.start()}c"
            cmd_end = f"1.0+{match.end(2)}c"
            self.entrada_texto.tag_add("comando", cmd_start, cmd_end)
            
            # Highlight parameters if present
            if match.group(3):
                param_start = f"1.0+{match.start(3)}c"
                param_end = f"1.0+{match.end(3)}c"
                self.entrada_texto.tag_add("parametro", param_start, param_end)

    def ao_colar_texto(self, event):
        try:
            texto_colado = self.root.clipboard_get()
        except tk.TclError:
            return "break"

        # Get current editor content
        conteudo_atual = self.entrada_texto.get("1.0", "end-1c").strip()
        
        # Check if editor already has wrapper tags
        editor_tem_xa = "^XA" in conteudo_atual
        editor_tem_xz = "^XZ" in conteudo_atual

        # Check for multiple labels in pasted content
        ocorr_xa = texto_colado.count("^XA")
        ocorr_xz = texto_colado.count("^XZ")
        
        if ocorr_xa > 1 or ocorr_xz > 1:
            resposta = messagebox.askyesno("Múltiplas Etiquetas", 
                                           "Múltiplas etiquetas (Tags ^XA/^XZ) detectadas.\nDeseja mesclar tudo em uma única etiqueta?")
            if resposta:
                # Strip all wrapper tags
                texto_limpo = texto_colado.replace("^XA", "").replace("^XZ", "").strip()
                self.entrada_texto.insert(tk.INSERT, texto_limpo)
                return "break"
            else:
                # Paste as is (user chose not to merge)
                return None 
        
        # If editor is empty or has no wrappers, paste content as-is (preserve ^XA/^XZ)
        if not conteudo_atual or (not editor_tem_xa and not editor_tem_xz):
            # Allow full paste including ^XA/^XZ
            return None
        
        # Editor has wrappers - strip wrappers from pasted content to insert into existing label
        if "^XA" in texto_colado or "^XZ" in texto_colado:
             texto_colado = texto_colado.replace("^XA", "").replace("^XZ", "").strip()
             self.entrada_texto.insert(tk.INSERT, texto_colado)
             return "break"
        
        return None
    
    def destacar_linhas_convertiveis(self):
        """Highlight lines that can be converted to mini-objects."""
        self.entrada_texto.tag_remove("convertivel", "1.0", tk.END)
        self.linhas_convertiveis = {}
        
        codigo = self.entrada_texto.get("1.0", tk.END)
        linhas = codigo.split('\n')
        
        # Pattern for text commands: ^FO followed by ^A and ^FD
        pattern = r'\^FO(\d+),(\d+)\^A[A-Z0-9@]*,(\d+),(\d+)(?:\^FH)?\^FD([^\^]+)\^FS'
        
        for linha_num, linha in enumerate(linhas, start=1):
            match = re.search(pattern, linha)
            if match:
                snippet = match.group(0)
                params = {
                    'x': int(match.group(1)),
                    'y': int(match.group(2)),
                    'altura': int(match.group(3)),
                    'largura': int(match.group(4)),
                    'texto': match.group(5)
                }
                
                # Check if this snippet was already converted
                if snippet not in self.linhas_convertidas:
                    self.linhas_convertiveis[linha_num] = {'snippet': snippet, 'params': params}
                    
                    # Highlight the entire line in green
                    start_idx = f"{linha_num}.0"
                    end_idx = f"{linha_num}.end"
                    self.entrada_texto.tag_add("convertivel", start_idx, end_idx)
    
    def ao_duplo_clique_editor(self, evento):
        """Handle double-click on text editor - convert line if in conversion mode."""
        if not self.modo_conversao_ativo:
            return  # Normal behavior (select word)
        
        # Get the line number where the click occurred
        index = self.entrada_texto.index(tk.INSERT)
        linha_num = int(index.split('.')[0])
        
        if linha_num in self.linhas_convertiveis:
            linha_info = self.linhas_convertiveis[linha_num]
            self.converter_linha_para_objeto(linha_num, linha_info['snippet'], linha_info['params'])
            return "break"  # Prevent normal double-click behavior
    
    def converter_linha_para_objeto(self, linha_num, zpl_snippet, params):
        """Convert a ZPL text line into a mini-object."""
        # Calculate canvas position from ZPL coordinates
        margin = getattr(self, 'canvas_margin', 10)
        canvas_x = params['x'] + margin
        canvas_y = params['y'] + margin
        
        # Mark this snippet as converted (will be filtered from API request)
        self.linhas_convertidas.append(zpl_snippet)
        
        # Remove all highlights and exit conversion mode
        self.entrada_texto.tag_remove("convertivel", "1.0", tk.END)
        self.linhas_convertiveis = {}
        self.modo_conversao_ativo = False
        self.selecionar_ferramenta(None)  # Switch to selection tool
        
        # Re-apply syntax highlighting
        self.aplicar_syntax_highlight()
        
        # Step 1: Update main preview (filtered, without this line)
        # Step 2: After delay, create the mini-object
        def atualizar_preview_filtrado():
            threading.Thread(target=self.fetch_labelary_preview, daemon=True).start()
        
        def criar_objeto_apos_delay():
            self.criar_mini_objeto_labelary(zpl_snippet, canvas_x, canvas_y)
        
        # Execute: update preview first, then create mini-object after 500ms delay
        atualizar_preview_filtrado()
        self.root.after(500, criar_objeto_apos_delay)
    
    def selecionar_ferramenta(self, ferramenta):
        """Select a tool and update cursor/button states."""
        self.ferramenta_selecionada = ferramenta
        
        # Reset all button appearances
        self.botao_texto.config(relief=tk.RAISED)
        # self.botao_imagem.config(relief=tk.RAISED)
        self.botao_codigo_barras.config(relief=tk.RAISED)
        self.botao_selecao.config(relief=tk.RAISED)
        self.botao_converter.config(relief=tk.RAISED)
        
        # Deactivate conversion mode and remove highlights if switching away
        if ferramenta != 'converter':
            self.modo_conversao_ativo = False
            self.entrada_texto.tag_remove("convertivel", "1.0", tk.END)
            self.linhas_convertiveis = {}
        
        # Highlight selected tool and change cursor
        if ferramenta == 'texto':
            self.botao_texto.config(relief=tk.SUNKEN)
            self.canvas.config(cursor="crosshair")
        # elif ferramenta == 'imagem':
        #     self.botao_imagem.config(relief=tk.SUNKEN)
        #     self.canvas.config(cursor="crosshair")
        elif ferramenta == 'codigo_barras':
            self.botao_codigo_barras.config(relief=tk.SUNKEN)
            self.canvas.config(cursor="crosshair")
        elif ferramenta == 'converter':
            self.botao_converter.config(relief=tk.SUNKEN)
            self.canvas.config(cursor="")
            self.modo_conversao_ativo = True
            self.destacar_linhas_convertiveis()
        else:
            self.botao_selecao.config(relief=tk.SUNKEN)
            self.canvas.config(cursor="")
    
    def ao_clicar_canvas(self, evento):
        """Handle click on canvas - either place new element or select existing."""
        # Check if clicking on a handle (don't process as canvas click)
        current_tags = self.canvas.gettags("current")
        if "handle" in current_tags:
            return
        
        # Check if clicking on an existing element (but NOT the background or border)
        item = self.canvas.find_withtag("current")
        if item:
            item_id = item[0]
            # Skip preview background, viewport rectangle and items with preview_fundo tag
            if item_id != self.retangulo and item_id != self.item_preview_fundo and "preview_fundo" not in self.canvas.gettags(item_id):
                # Clicking on existing element - show resize handles and handle drag
                self.mostrar_handles_redimensionar(item_id)
                self.ao_pressionar_elemento(evento)
                return
        
        # Clicked on empty space or background - hide handles
        self.ocultar_handles()
        
        # If a tool is selected, place element at click position
        if self.ferramenta_selecionada == 'texto':
            self.criar_texto_em_posicao(evento.x, evento.y)
        # elif self.ferramenta_selecionada == 'imagem':
        #     self.criar_imagem_em_posicao(evento.x, evento.y)
        elif self.ferramenta_selecionada == 'codigo_barras':
            self.criar_codigo_barras_em_posicao(evento.x, evento.y)
    
    def ao_duplo_clique_canvas(self, evento):
        """Handle double-click on canvas - edit element."""
        item = self.canvas.find_withtag("current")
        if item and item[0] != self.retangulo:
            self.editar_elemento(item[0])
    
    def criar_texto_em_posicao(self, x, y):
        """Create a default text element at the given position."""
        # Calculate ZPL coordinates (relative to canvas margin)
        margin = getattr(self, 'canvas_margin', 10)
        zpl_x = max(0, int(x) - margin)
        zpl_y = max(0, int(y) - margin)
        
        # Default text parameters
        altura_fonte = 30
        largura_char = 25
        texto = "texto"
        
        # Generate ZPL snippet
        zpl_snippet = f"^FO{zpl_x},{zpl_y}^A0,{altura_fonte},{largura_char}^FD{texto}^FS"
        
        # Insert before ^XZ if possible
        pos_xz = self.entrada_texto.search("^XZ", "1.0", tk.END)
        if pos_xz:
            self.entrada_texto.insert(pos_xz, zpl_snippet + "\n")
        else:
            self.entrada_texto.insert(tk.END, zpl_snippet + "\n")
        
        # Re-apply syntax highlighting
        self.aplicar_syntax_highlight()
        
        # Create mini-object at canvas position (don't update full preview)
        self.criar_mini_objeto_labelary(zpl_snippet, x, y)
        
        # Switch to selection mode
        self.selecionar_ferramenta(None)
    
    def criar_imagem_em_posicao(self, x, y):
        """Open file dialog and create image at given position."""
        file_path = filedialog.askopenfilename(filetypes=[("Imagens PNG", "*.png")])
        if file_path:
            # Calculate ZPL coordinates (relative to canvas margin)
            margin = getattr(self, 'canvas_margin', 10)
            zpl_x = max(0, int(x) - margin)
            zpl_y = max(0, int(y) - margin)
            
            # Generate ZPL for image
            zpl_code = image_to_zpl(file_path, zpl_x, zpl_y)
            
            # Insert before ^XZ if possible
            pos_xz = self.entrada_texto.search("^XZ", "1.0", tk.END)
            if pos_xz:
                self.entrada_texto.insert(pos_xz, zpl_code + "\n")
            else:
                self.entrada_texto.insert(tk.END, zpl_code + "\n")
            
            # Re-apply syntax highlighting
            self.aplicar_syntax_highlight()
            
            # Create mini-object (for images, use the ZPL code directly)
            self.criar_mini_objeto_labelary(zpl_code, x, y)
        
        # Switch to selection mode
        self.selecionar_ferramenta(None)
    
    def criar_codigo_barras_em_posicao(self, x, y):
        """Create a barcode element at the given position."""
        # Calculate ZPL coordinates (relative to canvas margin)
        margin = getattr(self, 'canvas_margin', 10)
        zpl_x = max(0, int(x) - margin)
        zpl_y = max(0, int(y) - margin)
        
        # Default barcode (UPC-A format, needs 11 digits)
        zpl_snippet = f"^FO{zpl_x},{zpl_y}^BY2^BUN,80^FD12345678901^FS"
        
        # Insert before ^XZ if possible
        pos_xz = self.entrada_texto.search("^XZ", "1.0", tk.END)
        if pos_xz:
            self.entrada_texto.insert(pos_xz, zpl_snippet + "\n")
        else:
            self.entrada_texto.insert(tk.END, zpl_snippet + "\n")
        
        # Re-apply syntax highlighting
        self.aplicar_syntax_highlight()
        
        # Create mini-object at canvas position
        self.criar_mini_objeto_labelary(zpl_snippet, x, y)
        
        # Switch to selection mode
        self.selecionar_ferramenta(None)
    
    def criar_mini_objeto_labelary(self, zpl_snippet, canvas_x, canvas_y):
        """
        Create a mini-object on canvas by fetching from Labelary API.
        The snippet is rendered independently with ^FO0,0.
        """
        def fetch_and_create():
            try:
                # Get DPI from UI
                dpi = self.combo_dpi.get()
                dpmm = 12 if dpi == "300" else 8
                
                # Calculate dimensions based on element type
                # Try to parse as text element
                params = extrair_parametros_texto(zpl_snippet)
                if params:
                    # Text element - calculate dimensions
                    largura_mm, altura_mm = calcular_dimensoes_texto(
                        params['altura'], params['largura'], params['texto'], 
                        dpi=int(dpi)
                    )
                else:
                    # Other element (barcode, image) - use larger default
                    largura_mm = 40
                    altura_mm = 20
                
                # Normalize ZPL: remove original ^FO and add ^FO0,0
                zpl_normalizado = normalizar_zpl_para_mini_objeto(zpl_snippet)
                
                # Fetch from Labelary
                image = fetch_labelary_element(zpl_normalizado, dpmm, largura_mm, altura_mm)
                
                if image:
                    # Create PhotoImage in main thread
                    def create_on_canvas():
                        photo = ImageTk.PhotoImage(image)
                        
                        # Create image on canvas
                        item_id = self.canvas.create_image(
                            canvas_x, canvas_y,
                            image=photo,
                            anchor=tk.NW,
                            tags=("mini_objeto",)
                        )
                        
                        # Store reference
                        self.mini_objetos[item_id] = {
                            'zpl': zpl_snippet,
                            'x': canvas_x,
                            'y': canvas_y,
                            'photo': photo  # Keep reference to prevent GC
                        }
                        
                        # Store ZPL position info for editing
                        # Find the match position in the text
                        codigo_zpl = self.entrada_texto.get("1.0", tk.END)
                        match_start = codigo_zpl.find(zpl_snippet)
                        if match_start >= 0:
                            match_end = match_start + len(zpl_snippet)
                            self.canvas.dados_zpl_posicao[item_id] = (match_start, match_end, 'texto' if params else 'outro')
                        
                        # Bind drag events
                        self.canvas.tag_bind(item_id, "<ButtonPress-1>", self.ao_pressionar_elemento)
                        self.canvas.tag_bind(item_id, "<B1-Motion>", self.ao_arrastar_elemento)
                        self.canvas.tag_bind(item_id, "<ButtonRelease-1>", self.ao_soltar_arrasto)
                        # Bind double-click for editing
                        self.canvas.tag_bind(item_id, "<Double-Button-1>", lambda e, item=item_id: self.editar_mini_objeto(item))
                        
                    self.root.after(0, create_on_canvas)
                    
            except Exception as e:
                print(f"Erro ao criar mini-objeto: {e}")
        
        # Run in thread to avoid blocking UI
        threading.Thread(target=fetch_and_create, daemon=True).start()

    def editar_elemento(self, item):
        """Open edit dialog for an element."""
        # Check if it's a mini-object
        if item in self.mini_objetos:
            self.editar_mini_objeto(item)
        # Check if it's a text element
        elif item in self.canvas.dados_texto_bitmap:
            self.abrir_janela_edicao_texto(item)
        elif self.canvas.type(item) == "text":
            self.abrir_janela_edicao_texto(item)
    
    def editar_mini_objeto(self, item):
        """Open edit dialog for a mini-object created via Labelary API."""
        if item not in self.mini_objetos:
            return
        
        mini_obj = self.mini_objetos[item]
        zpl_snippet = mini_obj['zpl']
        
        # Try to parse text parameters
        params = extrair_parametros_texto(zpl_snippet)
        
        janela = tk.Toplevel(self.root)
        janela.title("Editar Elemento")
        janela.geometry("320x220")
        janela.transient(self.root)
        janela.grab_set()
        
        # Current values
        texto_atual = params.get('texto', '') if params else ''
        altura_atual = params.get('altura', 30) if params else 30
        largura_atual = params.get('largura', 25) if params else 25
        
        # Text field
        tk.Label(janela, text="Texto:").pack(pady=5)
        entrada_texto = tk.Entry(janela, width=35)
        entrada_texto.insert(0, texto_atual)
        entrada_texto.pack(pady=5)
        
        # Size fields
        frame_tamanho = tk.Frame(janela)
        frame_tamanho.pack(pady=5)
        
        tk.Label(frame_tamanho, text="Altura:").pack(side=tk.LEFT, padx=5)
        entrada_altura = tk.Entry(frame_tamanho, width=5)
        entrada_altura.insert(0, str(altura_atual))
        entrada_altura.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_tamanho, text="Largura:").pack(side=tk.LEFT, padx=5)
        entrada_largura = tk.Entry(frame_tamanho, width=5)
        entrada_largura.insert(0, str(largura_atual))
        entrada_largura.pack(side=tk.LEFT, padx=5)
        
        def confirmar():
            novo_texto = entrada_texto.get()
            altura = entrada_altura.get() or "30"
            largura = entrada_largura.get() or "25"
            
            # Get current canvas position and convert to ZPL coordinates  
            coords = self.canvas.coords(item)
            if coords:
                canvas_x, canvas_y = coords[:2]
                # Calculate ZPL position (relative to canvas margin)
                margin = getattr(self, 'canvas_margin', 10)
                zpl_x = max(0, int(canvas_x) - margin)
                zpl_y = max(0, int(canvas_y) - margin)
            else:
                canvas_x, canvas_y = 50, 50
                zpl_x, zpl_y = 0, 0
            
            # Create new ZPL snippet
            new_zpl = f"^FO{zpl_x},{zpl_y}^A0,{altura},{largura}^FD{novo_texto}^FS"
            
            # Update ZPL in text editor - find and replace the old snippet
            codigo_zpl = self.entrada_texto.get("1.0", tk.END)
            old_zpl = mini_obj['zpl'].strip()  # Strip whitespace for comparison
            
            # Try to find the old ZPL (may have trailing newline in editor)
            if old_zpl in codigo_zpl:
                codigo_zpl = codigo_zpl.replace(old_zpl, new_zpl, 1)
                self.entrada_texto.delete("1.0", tk.END)
                self.entrada_texto.insert("1.0", codigo_zpl.rstrip())  # Use 1.0 not END
            elif old_zpl + "\n" in codigo_zpl:
                codigo_zpl = codigo_zpl.replace(old_zpl + "\n", new_zpl + "\n", 1)
                self.entrada_texto.delete("1.0", tk.END)
                self.entrada_texto.insert("1.0", codigo_zpl.rstrip())
            else:
                # Fallback: just inform user the ZPL was not found
                print(f"[DEBUG] Could not find old ZPL to replace:")
                print(f"  old_zpl: '{old_zpl}'")
                print(f"  in code: {codigo_zpl[:200]}...")
            
            # Delete old mini-object from canvas
            try:
                self.canvas.delete(item)
                del self.mini_objetos[item]
            except:
                pass
            
            # Create new mini-object with updated ZPL
            self.criar_mini_objeto_labelary(new_zpl, canvas_x, canvas_y)
            
            janela.destroy()
        
        tk.Button(janela, text="Confirmar", command=confirmar, font=("Arial", 10, "bold")).pack(pady=15)
    
    def abrir_janela_edicao_texto(self, item):
        """Open text edit popup."""
        janela = tk.Toplevel(self.root)
        janela.title("Editar Texto")
        janela.geometry("300x200")
        janela.transient(self.root)
        janela.grab_set()
        
        # Get current text
        if item in self.canvas.dados_texto_bitmap:
            texto_atual = self.canvas.dados_texto_bitmap[item]
        else:
            texto_atual = self.canvas.itemcget(item, "text")
        
        # Text field
        tk.Label(janela, text="Texto:").pack(pady=5)
        entrada_texto = tk.Entry(janela, width=30)
        entrada_texto.insert(0, texto_atual)
        entrada_texto.pack(pady=5)
        
        # Size fields
        frame_tamanho = tk.Frame(janela)
        frame_tamanho.pack(pady=5)
        
        tk.Label(frame_tamanho, text="Altura:").pack(side=tk.LEFT, padx=5)
        entrada_altura = tk.Entry(frame_tamanho, width=5)
        entrada_altura.insert(0, "20")
        entrada_altura.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_tamanho, text="Largura:").pack(side=tk.LEFT, padx=5)
        entrada_largura = tk.Entry(frame_tamanho, width=5)
        entrada_largura.insert(0, "20")
        entrada_largura.pack(side=tk.LEFT, padx=5)
        
        def confirmar():
            novo_texto = entrada_texto.get()
            altura = entrada_altura.get() or "20"
            largura = entrada_largura.get() or "20"
            
            # Get current position
            x, y = self.canvas.coords(item)
            zpl_x = max(0, int(x) - self.deslocamento_x)
            zpl_y = max(0, int(y) - self.deslocamento_y)
            
            # Update ZPL - find and replace old text command
            if item in self.canvas.dados_zpl_posicao:
                match_start, match_end, _ = self.canvas.dados_zpl_posicao[item]
                codigo_zpl = self.entrada_texto.get("1.0", tk.END)
                new_zpl = f"^FO{zpl_x},{zpl_y}^A0,{altura},{largura}^FD{novo_texto}^FS"
                codigo_zpl = codigo_zpl[:match_start] + new_zpl + codigo_zpl[match_end:]
                self.entrada_texto.delete("1.0", tk.END)
                self.entrada_texto.insert(tk.END, codigo_zpl)
            
            self.atualizar_visualizacao()
            janela.destroy()
        
        tk.Button(janela, text="Confirmar", command=confirmar, font=("Arial", 10, "bold")).pack(pady=15)
    
    # ===== RESIZE HANDLES (REDIMENSIONAR) =====
    
    def mostrar_handles_redimensionar(self, item):
        """Show resize handles around the selected element."""
        # Resize is disabled - dimensions should be set via edit modal
        if not self.redimensionamento_habilitado:
            self.elemento_selecionado = item
            return
            
        self.ocultar_handles()  # Clear any existing handles
        self.elemento_selecionado = item
        
        bbox = self.canvas.bbox(item)
        if not bbox:
            return
        
        x1, y1, x2, y2 = bbox
        handle_size = 6
        cx = (x1 + x2) // 2  # Center X
        cy = (y1 + y2) // 2  # Center Y
        
        # Create handles at corners and midpoints
        # Format: (x, y, position_name)
        handle_positions = [
            # Corners (uniform resize)
            (x1, y1, 'nw'),  # Top-left
            (x2, y2, 'se'),  # Bottom-right
            (x2, y1, 'ne'),  # Top-right
            (x1, y2, 'sw'),  # Bottom-left
            # Midpoints (single-axis resize)
            (cx, y1, 'n'),   # Top center (vertical only)
            (cx, y2, 's'),   # Bottom center (vertical only)
            (x1, cy, 'w'),   # Left center (horizontal only)
            (x2, cy, 'e'),   # Right center (horizontal only)
        ]
        
        for hx, hy, pos in handle_positions:
            handle = self.canvas.create_rectangle(
                hx - handle_size//2, hy - handle_size//2,
                hx + handle_size//2, hy + handle_size//2,
                fill="blue", outline="white", tags=("handle", f"handle_{pos}")
            )
            self.handles_redimensionar.append(handle)
            
            # Bind drag events to handles
            self.canvas.tag_bind(handle, "<ButtonPress-1>", 
                                 lambda e, p=pos: self.ao_pressionar_handle(e, p))
            self.canvas.tag_bind(handle, "<B1-Motion>", 
                                 lambda e, p=pos: self.ao_arrastar_handle(e, p))
            self.canvas.tag_bind(handle, "<ButtonRelease-1>", self.ao_soltar_handle)
    
    def ocultar_handles(self):
        """Remove all resize handles from canvas."""
        for handle in self.handles_redimensionar:
            self.canvas.delete(handle)
        self.handles_redimensionar = []
    
    def ao_pressionar_handle(self, evento, posicao):
        """Store initial state when handle is pressed."""
        self.handle_posicao_atual = posicao
        self.handle_x_inicial = evento.x
        self.handle_y_inicial = evento.y
        # Store original position for delta calculation in ao_soltar_handle
        self.handle_x_original = evento.x
        self.handle_y_original = evento.y
        if self.elemento_selecionado:
            self.bbox_inicial = self.canvas.bbox(self.elemento_selecionado)
    
    def ao_arrastar_handle(self, evento, posicao):
        """Resize element while dragging handle."""
        if not self.elemento_selecionado or not hasattr(self, 'bbox_inicial'):
            return
        
        dx = evento.x - self.handle_x_inicial
        dy = evento.y - self.handle_y_inicial
        
        # This is a simplified approach - for bitmap/images we would need to
        # re-render at new size. For now, we'll update the visual feedback
        # and recalculate on release.
        
        # Update handle positions to show resize preview
        self.handle_x_inicial = evento.x
        self.handle_y_inicial = evento.y
    
    def ao_soltar_handle(self, evento):
        """Finalize resize when handle is released."""
        if not self.elemento_selecionado:
            return
        
        # Get new dimensions based on handle movement
        if hasattr(self, 'bbox_inicial') and self.bbox_inicial and hasattr(self, 'handle_posicao_atual'):
            old_x1, old_y1, old_x2, old_y2 = self.bbox_inicial
            old_width = old_x2 - old_x1
            old_height = old_y2 - old_y1
            
            # Determine resize mode based on handle position
            pos = self.handle_posicao_atual
            
            # Calculate delta from original press position
            dx = evento.x - getattr(self, 'handle_x_original', evento.x)
            dy = evento.y - getattr(self, 'handle_y_original', evento.y)
            
            # For text elements, update font size in ZPL
            if self.elemento_selecionado in self.canvas.dados_zpl_posicao:
                match_start, match_end, elem_type = self.canvas.dados_zpl_posicao[self.elemento_selecionado]
                
                if elem_type == 'texto':
                    # Get current text
                    if self.elemento_selecionado in self.canvas.dados_texto_bitmap:
                        texto = self.canvas.dados_texto_bitmap[self.elemento_selecionado]
                    else:
                        texto = self.canvas.itemcget(self.elemento_selecionado, "text")
                    
                    # Extract current ZPL dimensions from the original ZPL
                    codigo_zpl = self.entrada_texto.get("1.0", tk.END)
                    original_snippet = codigo_zpl[match_start:match_end]
                    
                    # Parse current height and width from ZPL
                    match_dims = re.search(r'\^A\d*,(\d+),(\d+)', original_snippet)
                    if match_dims:
                        current_zpl_height = int(match_dims.group(1))
                        current_zpl_width = int(match_dims.group(2))
                    else:
                        current_zpl_height = 20
                        current_zpl_width = 20
                    
                    # Apply resize based on handle position
                    if pos in ('n', 's'):
                        # Vertical only - keep width, change height
                        new_zpl_width = current_zpl_width
                        new_zpl_height = max(10, current_zpl_height + dy if pos == 's' else current_zpl_height - dy)
                    elif pos in ('e', 'w'):
                        # Horizontal only - keep height, change width
                        new_zpl_width = max(10, current_zpl_width + dx if pos == 'e' else current_zpl_width - dx)
                        new_zpl_height = current_zpl_height
                    else:
                        # Corner handles - both dimensions
                        if pos == 'se':
                            new_zpl_width = max(10, current_zpl_width + dx)
                            new_zpl_height = max(10, current_zpl_height + dy)
                        elif pos == 'nw':
                            new_zpl_width = max(10, current_zpl_width - dx)
                            new_zpl_height = max(10, current_zpl_height - dy)
                        elif pos == 'ne':
                            new_zpl_width = max(10, current_zpl_width + dx)
                            new_zpl_height = max(10, current_zpl_height - dy)
                        else:  # sw
                            new_zpl_width = max(10, current_zpl_width - dx)
                            new_zpl_height = max(10, current_zpl_height + dy)
                    
                    x, y = self.canvas.coords(self.elemento_selecionado)
                    zpl_x = max(0, int(x) - self.deslocamento_x)
                    zpl_y = max(0, int(y) - self.deslocamento_y)
                    
                    # Update ZPL with new dimensions
                    new_zpl = f"^FO{zpl_x},{zpl_y}^A0,{int(new_zpl_height)},{int(new_zpl_width)}^FD{texto}^FS"
                    codigo_zpl = codigo_zpl[:match_start] + new_zpl + codigo_zpl[match_end:]
                    self.entrada_texto.delete("1.0", tk.END)
                    self.entrada_texto.insert(tk.END, codigo_zpl)
                    
                    self.atualizar_visualizacao()
        
        # Clear handles after resize
        self.ocultar_handles()

        self.ocultar_handles()
    
    def atualizar_tudo(self):
        """Update full preview: fetch from Labelary and set as canvas background, clear mini-objects."""
        # Clear mini-objects (they'll be merged into the main preview)
        self.limpar_mini_objetos()
        # Reset converted lines (merge everything back into main preview)
        self.linhas_convertidas = []
        # Run Labelary fetch in thread
        threading.Thread(target=self.fetch_labelary_preview, daemon=True).start()

    def limpar_mini_objetos(self):
        """Remove all mini-object items from canvas and clear tracking dict."""
        for item_id in list(self.mini_objetos.keys()):
            try:
                self.canvas.delete(item_id)
            except:
                pass
        self.mini_objetos = {}
        # Also clear old local preview items
        for item in self.canvas.find_all():
            if self.canvas.type(item) in ("text", "image") and item != self.item_preview_fundo:
                self.canvas.delete(item)
        self.canvas.dados_codigo_barras = {}
        self.canvas.dados_texto_bitmap = {}
        self.canvas.dados_zpl_posicao = {}

    def fetch_labelary_preview(self):
        """Fetch label preview from Labelary API and set as canvas background."""
        zpl = self.entrada_texto.get("1.0", tk.END).strip()
        if not zpl: return
        
        # Filter out converted snippets from ZPL before sending to API
        if hasattr(self, 'linhas_convertidas') and self.linhas_convertidas:
            for snippet in self.linhas_convertidas:
                zpl = zpl.replace(snippet, "")
        
        
        try:
            dpi = self.combo_dpi.get()
            width = float(self.spin_width.get())
            height = float(self.spin_height.get())
            unit = self.combo_unit.get()
            
            # dpmm: 8dpmm (203dpi) or 12dpmm (300dpi)
            dpmm = 8
            if dpi == "300": dpmm = 12
            elif dpi == "600": dpmm = 24
            
            # Convert dimensions to inches for the URL
            if unit == "mm":
                w_in = width / 25.4
                h_in = height / 25.4
            elif unit == "cm":
                w_in = width / 2.54
                h_in = height / 2.54
            else:
                w_in = width
                h_in = height
            
            url = f"http://api.labelary.com/v1/printers/{dpmm}dpmm/labels/{w_in:.2f}x{h_in:.2f}/0/"
            
            response = requests.post(url, files={'file': zpl}, stream=True, timeout=15)
            
            if response.status_code == 200:
                response.raw.decode_content = True
                image = Image.open(io.BytesIO(response.content))
                
                # Keep original API image
                self._labelary_image_raw = image
                
                # Create photo for canvas
                photo = ImageTk.PhotoImage(image)
                
                # Update UI in main thread
                def update_canvas_bg():
                    # Delete old background if exists
                    if self.item_preview_fundo:
                        try:
                            self.canvas.delete(self.item_preview_fundo)
                        except:
                            pass
                    
                    margin = getattr(self, 'canvas_margin', 10)
                    
                    # Create new background image at top-left with offset
                    self.item_preview_fundo = self.canvas.create_image(
                        margin, 
                        margin, 
                        image=photo, 
                        anchor=tk.NW, 
                        tags="preview_fundo"
                    )
                    # Send to back so mini-objects appear on top
                    self.canvas.tag_lower(self.item_preview_fundo)
                    # Ensure rectangle is above background
                    self.canvas.tag_raise(self.retangulo)
                    
                    # Keep reference to prevent garbage collection
                    self.imagem_preview_fundo = photo
                    
                    # Update viewport rectangle to match image size
                    img_w, img_h = image.size
                    self.canvas.coords(
                        self.retangulo,
                        margin, 
                        margin, 
                        margin + img_w, 
                        margin + img_h
                    )
                
                self.root.after(0, update_canvas_bg)
                
            else:
                def show_err():
                    messagebox.showerror("Erro Labelary", f"Erro API: {response.status_code}\n{response.text[:200]}")
                self.root.after(0, show_err)
                
        except Exception as e:
            def show_ex():
                messagebox.showerror("Erro Labelary", f"Erro: {e}")
            self.root.after(0, show_ex)

    def atualizar_visualizacao(self):
        """
        Legacy function - local rendering is deprecated.
        Now we use Labelary for all previews (main preview + mini-objects).
        This function is kept for compatibility but does minimal work.
        """
        # Just update the coordinate label if needed
        self.rotulo_coordenadas.config(text="")

    def ao_pressionar_elemento(self, evento):
        self.canvas_element_current = self.canvas.find_withtag("current")
        self.canvas_x_current = evento.x
        self.canvas_y_current = evento.y
        
        # Calculate offset from mouse to element top-left corner
        if self.canvas_element_current:
            coords = self.canvas.coords(self.canvas_element_current)
            if coords:
                self.arrasto_offset_x = evento.x - coords[0]
                self.arrasto_offset_y = evento.y - coords[1]
            else:
                self.arrasto_offset_x = 0
                self.arrasto_offset_y = 0
        
        # Initialize drag border rectangle
        self.retangulo_arrasto = None

    def ao_arrastar_elemento(self, evento):
        if not self.canvas_element_current:
            return
        
        # Hide resize handles during drag for cleaner visual
        if self.handles_redimensionar:
            self.ocultar_handles()
            
        rx1, ry1, rx2, ry2 = self.canvas.coords(self.retangulo)
        # Use value 1 for free movement (snap dropdown was removed)
        valor_snap = 1
        
        # Current element coords
        coords = self.canvas.coords(self.canvas_element_current)
        if not coords: return
        x1, y1 = coords[:2]
        
        # Calculate new position maintaining grab offset
        offset_x = getattr(self, 'arrasto_offset_x', 0)
        offset_y = getattr(self, 'arrasto_offset_y', 0)
        
        x2 = evento.x - offset_x
        y2 = evento.y - offset_y
        
        # Apply snap (minimal snap when not aligned to grid)
        x2 = round((x2 + 1) / valor_snap) * valor_snap
        y2 = round((y2 + 1) / valor_snap) * valor_snap
        
        if self.trava_eixo_x.get():
            x2 = x1
        if self.trava_eixo_y.get():
            y2 = y1

        bbox = self.canvas.bbox(self.canvas_element_current)
        largura_elemento = 0
        altura_elemento = 0
        if bbox:
            largura_elemento = bbox[2] - bbox[0]
            altura_elemento = bbox[3] - bbox[1]

        if x2 < rx1: x2 = rx1
        if y2 < ry1: y2 = ry1
        if x2 + largura_elemento > rx2: x2 = rx2 - largura_elemento
        if y2 + altura_elemento > ry2: y2 = ry2 - altura_elemento

        # Move element
        self.canvas.coords(self.canvas_element_current, x2, y2)
        
        # Update or create drag border rectangle
        if hasattr(self, 'retangulo_arrasto') and self.retangulo_arrasto:
            self.canvas.coords(self.retangulo_arrasto, x2, y2, x2 + largura_elemento, y2 + altura_elemento)
        else:
            self.retangulo_arrasto = self.canvas.create_rectangle(
                x2, y2, x2 + largura_elemento, y2 + altura_elemento,
                outline="black", width=1, dash=(2, 2), tags="arrasto_border"
            )

        x_relativo = x2 - rx1
        y_relativo = y2 - ry1
        self.rotulo_coordenadas.config(text=f"x: {x_relativo + 10}, y: {y_relativo + 10}")

        self.rotulo_coordenadas.config(text=f"x: {x_relativo + 10}, y: {y_relativo + 10}")

        if self.canvas_element_current[0] not in self.elementos_movidos:
             self.elementos_movidos.append(self.canvas_element_current[0])
    
    def ao_soltar_arrasto(self, evento):
        """Clean up drag border and update ZPL automatically."""
        if hasattr(self, 'retangulo_arrasto') and self.retangulo_arrasto:
            self.canvas.delete(self.retangulo_arrasto)
            self.retangulo_arrasto = None
        
        # Snap to grid if enabled
        if hasattr(self, 'alinhar_grade') and self.alinhar_grade.get():
            if self.canvas_element_current and self.canvas_element_current[0]:
                try:
                    espacamento = int(self.combo_espacamento_grade.get())
                except:
                    espacamento = 50
                
                margin = getattr(self, 'canvas_margin', 10)
                item = self.canvas_element_current[0]
                coords = self.canvas.coords(item)
                
                if coords:
                    # Current position (top-left)
                    x, y = coords[0], coords[1]
                    
                    # Convert to ZPL coordinates (relative to margin)
                    zpl_x = x - margin
                    zpl_y = y - margin
                    
                    # Snap to nearest grid intersection
                    snapped_x = round(zpl_x / espacamento) * espacamento
                    snapped_y = round(zpl_y / espacamento) * espacamento
                    
                    # Convert back to canvas coordinates
                    new_x = snapped_x + margin
                    new_y = snapped_y + margin
                    
                    # Move the element to snapped position
                    dx = new_x - x
                    dy = new_y - y
                    self.canvas.move(item, dx, dy)
            
        # Update ZPL position automatically on release
        if self.elementos_movidos:
            self.aplicar_mudancas()
            self.atualizar_visualizacao()  # Refresh canvas and indices

    def aplicar_mudancas(self):
        codigo_zpl = self.entrada_texto.get("1.0", tk.END)
        
        # Collect all updates with their positions
        # Format: [(match_start, match_end, new_coords_str, element_type), ...]
        updates = []
        
        for item in self.elementos_movidos:
            if item not in self.canvas.dados_zpl_posicao:
                continue
                
            match_start, match_end, element_type = self.canvas.dados_zpl_posicao[item]
            x, y = self.canvas.coords(item)
            margin = getattr(self, 'canvas_margin', 10)
            novo_x = max(0, int(x) - margin)
            novo_y = max(0, int(y) - margin)
            
            # Get the original ZPL snippet for this element
            original_snippet = codigo_zpl[match_start:match_end]
            
            # Replace only the ^FO coordinates in this specific snippet
            new_snippet = re.sub(r'\^FO\d+,\d+', f'^FO{novo_x},{novo_y}', original_snippet, count=1)
            
            updates.append((match_start, match_end, new_snippet))
        
        # Sort by position descending to avoid offset issues when replacing
        updates.sort(key=lambda x: x[0], reverse=True)
        
        # Apply updates from end to start
        for match_start, match_end, new_snippet in updates:
            codigo_zpl = codigo_zpl[:match_start] + new_snippet + codigo_zpl[match_end:]

        self.entrada_texto.delete("1.0", tk.END)
        self.entrada_texto.insert(tk.END, codigo_zpl)
        
        # Re-apply syntax highlighting
        self.aplicar_syntax_highlight()

        self.elementos_movidos = []

    def arrastar_imagem_direto(self, evento):
        # Specific handler for imported images (direct ZPL update)
        if self.canvas.type(self.canvas_element_current) == "image":
             # Same logic as VPL.py lines 408-453
             x, y = self.canvas.coords(self.canvas_element_current)
             x += evento.x - self.canvas_x_current
             y += evento.y - self.canvas_y_current
             
             if self.trava_eixo_x.get(): x = self.canvas.coords(self.canvas_element_current)[0]
             if self.trava_eixo_y.get(): y = self.canvas.coords(self.canvas_element_current)[1]

             rx1, ry1, rx2, ry2 = self.canvas.coords(self.retangulo)
             bbox = self.canvas.bbox(self.canvas_element_current)
             w = bbox[2] - bbox[0]
             h = bbox[3] - bbox[1]

             if x < rx1: x = rx1
             if y < ry1: y = ry1
             if x + w > rx2: x = rx2 - w
             if y + h > ry2: y = ry2 - h

             self.canvas.coords(self.canvas_element_current, x, y)
             self.canvas_x_current = evento.x
             self.canvas_y_current = evento.y

             # Update ZPL directly
             codigo_zpl = self.entrada_texto.get("1.0", tk.END)
             # Regex for GFA (image)
             novo_codigo_zpl = re.sub(r'(\^FO)\d+,\d+(\^GFA[^\^]+\^FS)', rf'\g<1>{int(x)},{int(y)}\g<2>', codigo_zpl)
             self.entrada_texto.delete("1.0", tk.END)
             self.entrada_texto.insert(tk.END, novo_codigo_zpl)

    def criar_elemento(self):
        janela = tk.Toplevel(self.root)
        janela.title("Criar elemento")
        janela.geometry("400x300")
        
        tk.Label(janela, text="Tipo de elemento:").pack(side=tk.TOP, padx=5, pady=5)
        tipo_elemento = ttk.Combobox(janela, values=["Texto", "Código de barras"])
        tipo_elemento.pack(side=tk.TOP, padx=5, pady=5)

        rotulo_tamanho_fonte = tk.Label(janela, text="Tamanho da fonte:")
        tamanho_fonte = ttk.Combobox(janela, values=[16, 18, 20, 30, 40, 50, 60])
        tamanho_fonte.current(2)

        rotulo_tamanho_codigo_barras = tk.Label(janela, text="Tamanho do código de barras:")
        tamanho_codigo_barras = ttk.Combobox(janela, values=[1, 2, 3, 4, 5])
        tamanho_codigo_barras.current(2)

        rotulo_formato_codigo_barras = tk.Label(janela, text="Formato do código de barras:")
        formato_codigo_barras = ttk.Combobox(janela, values=["UPC-A", "EAN-13"])
        formato_codigo_barras.current(0)

        rotulo_conteudo_elemento = tk.Label(janela, text="Conteúdo do elemento:")
        rotulo_conteudo_elemento.pack(side=tk.TOP, padx=5, pady=5)
        
        conteudo_elemento = tk.Entry(janela, width=50)
        conteudo_elemento.pack(side=tk.TOP, padx=5, pady=5)
        
        botao_adicionar = tk.Button(janela, text="Adicionar elemento", state=tk.DISABLED)
        botao_adicionar.pack(side=tk.BOTTOM, padx=5, pady=5)

        def atualizar_estado_botao(*args):
             if (tipo_elemento.get() == "Texto" and conteudo_elemento.get() and tamanho_fonte.get()) or \
                (tipo_elemento.get() == "Código de barras" and conteudo_elemento.get() and tamanho_codigo_barras.get()):
                 botao_adicionar.config(state=tk.NORMAL)
             else:
                 botao_adicionar.config(state=tk.DISABLED)

        def ao_selecionar_tipo(event):
            atualizar_estado_botao()
            if tipo_elemento.get() == "Texto":
                rotulo_tamanho_fonte.pack(side=tk.TOP, padx=5, pady=5)
                tamanho_fonte.pack(side=tk.TOP, padx=5, pady=5)
                rotulo_tamanho_codigo_barras.pack_forget()
                tamanho_codigo_barras.pack_forget()
                rotulo_formato_codigo_barras.pack_forget()
                formato_codigo_barras.pack_forget()
            elif tipo_elemento.get() == "Código de barras":
                rotulo_tamanho_fonte.pack_forget()
                tamanho_fonte.pack_forget()
                rotulo_tamanho_codigo_barras.pack(side=tk.TOP, padx=5, pady=5)
                tamanho_codigo_barras.pack(side=tk.TOP, padx=5, pady=5)
                rotulo_formato_codigo_barras.pack(side=tk.TOP, padx=5, pady=5)
                formato_codigo_barras.pack(side=tk.TOP, padx=5, pady=5)

        tipo_elemento.bind("<<ComboboxSelected>>", ao_selecionar_tipo)
        conteudo_elemento.bind("<KeyRelease>", atualizar_estado_botao)
        tamanho_fonte.bind("<<ComboboxSelected>>", atualizar_estado_botao)
        tamanho_codigo_barras.bind("<<ComboboxSelected>>", atualizar_estado_botao)
        formato_codigo_barras.bind("<<ComboboxSelected>>", atualizar_estado_botao)

        def adicionar():
            if tipo_elemento.get() == "Texto":
                t = tamanho_fonte.get()
                txt = conteudo_elemento.get()
                zpl = f"^FO200,200^A0,{t},{t}^FD{txt}^FS"
                
                # Insert before ^XZ if possible
                pos_xz = self.entrada_texto.search("^XZ", "1.0", tk.END)
                if pos_xz:
                    self.entrada_texto.insert(pos_xz, zpl + "\n")
                else:
                    self.entrada_texto.insert(tk.END, zpl + "\n")
            elif tipo_elemento.get() == "Código de barras":
                t = tamanho_codigo_barras.get()
                cod = conteudo_elemento.get()
                fmt = formato_codigo_barras.get()
                
                # Logic to render and add to canvas/ZPL
                # VPL.py duplicates logic here (rendering image + adding ZPL).
                # Simplified: Just add ZPL and let update_preview handle rendering?
                # VPL.py line 313 adds ZPL. Line 320 renders image specifically for "previewing" immediately?
                # Actually VPL.py does both: adds ZPL AND directly adds image to canvas.
                # Adding ZPL is enough if we call `atualizar_visualizacao` after.
                
                if fmt == "UPC-A":
                    zpl = f"^FO200,200^BY{t}^BUN,80^FD{cod}^FS"
                elif fmt == "EAN-13":
                    zpl = f"^FO200,200^BY{t}^BEN,80^FD{cod}^FS"
                
                # Insert before ^XZ if possible
                pos_xz = self.entrada_texto.search("^XZ", "1.0", tk.END)
                if pos_xz:
                    self.entrada_texto.insert(pos_xz, zpl + "\n")
                else:
                    self.entrada_texto.insert(tk.END, zpl + "\n")

            janela.destroy()
            self.atualizar_tudo()
 
        botao_adicionar.config(command=adicionar)

    def importar_imagem(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imagens PNG", "*.png")])
        if file_path:
            try:
                imagem = Image.open(file_path)
                imagem.thumbnail((200, 200))
                foto = ImageTk.PhotoImage(imagem)
                
                # Create image on canvas
                item = self.canvas.create_image(150, 150, image=foto, anchor=tk.NW)
                
                # Bind events - Special handler for imported images
                self.canvas.tag_bind(item, "<ButtonPress-1>", self.ao_pressionar_elemento)
                self.canvas.tag_bind(item, "<B1-Motion>", self.arrastar_imagem_direto)

                # Convert to ZPL and insert
                zpl_code = image_to_zpl(file_path)
                
                # Insert before ^XZ if possible
                pos_xz = self.entrada_texto.search("^XZ", "1.0", tk.END)
                if pos_xz:
                    self.entrada_texto.insert(pos_xz, zpl_code + "\n")
                else:
                    self.entrada_texto.insert(tk.END, zpl_code + "\n")
                
                # Keep ref
                if not hasattr(self.canvas, '_imagens'): self.canvas._imagens = {}
                self.canvas._imagens[item] = foto

            except Exception as e:
                print(f"Erro ao abrir imagem: {e}")


    def ao_redimensionar(self, evento):
        if evento.widget == self.root:
            # Simplified: Update rectangle based on canvas width
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                 # Update viewport rect to match canvas size minus margins
                 self.canvas.coords(self.retangulo, 
                                    self.deslocamento_x + 10, 
                                    self.deslocamento_y + 10, 
                                    self.deslocamento_x + canvas_width - 10, 
                                    self.deslocamento_y + canvas_height - 10)

if __name__ == "__main__":
    root = tk.Tk()
    app = ZPLVisualizerApp(root)
    root.mainloop()
