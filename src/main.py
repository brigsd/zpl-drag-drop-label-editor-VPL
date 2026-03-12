import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
from PIL import ImageTk, Image
import re
import threading
import requests
import io
import json
import os
import sys
import barcode
from barcode.writer import ImageWriter
from zpl_utils import (
    redimensionar_imagem_codigo_barras, zpl_gfa_to_image, 
    render_bitmap_text, render_scalable_text, fetch_labelary_element,
    calcular_dimensoes_texto, normalizar_zpl_para_mini_objeto, extrair_parametros_texto
)

def get_base_path():
    """Get the correct base path for both development and executable modes."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(__file__)

class ZPLVisualizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualizador de Etiquetas ZPL")
        
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
        
        # Canvas size (fixed)
        self.max_canvas_width = 1000
        self.max_canvas_height = 937
        self.font_size = 12           # ZPL editor font size
        self.editor_font_family = 'Consolas'  # ZPL editor font family
        self.ui_font_size = 12        # UI elements font size (buttons, labels, etc.)
        self.ui_font_family = 'Segoe UI'      # UI font family
        self.window_width = 1400      # Main window width
        self.window_height = 700      # Main window height
        self.theme = 'default'  # 'default', 'classic_dark', 'modern_dark', 'modern_light'
        
        # Available fonts for selection
        self.available_editor_fonts = ['Consolas', 'Courier New', 'Lucida Console', 'Monaco', 'Fira Code', 'Source Code Pro']
        self.available_ui_fonts = ['Segoe UI', 'Arial', 'Tahoma', 'Verdana', 'Calibri', 'Helvetica']
        
        # Zoom state (Ctrl+Scroll) - Always enabled
        self.zoom_level = 1.0       # Current zoom (1.0 = 100%)
        self.zoom_min = 0.10        # Min zoom (10%)
        self.zoom_max = 4.0         # Max zoom (400%)
        self.scale_factor = 1.0     # Scale factor for grid calculations
        
        # Theme definitions
        self.themes = {
            'default': {
                'name': 'Padrão',
                'bg': '#f0f0f0',
                'fg': '#000000',
                'canvas_bg': 'white',
                'button_bg': '#dddddd',
                'button_fg': '#000000',
                'entry_bg': 'white',
                'entry_fg': '#000000',
                'frame_bg': '#f0f0f0',
                'label_bg': '#f0f0f0',
                'label_fg': '#000000'
            },
            'classic_dark': {
                'name': 'Escuro Laranja',
                'bg': '#1e1e1e',
                'fg': '#ffffff',
                'canvas_bg': '#2d2d2d',
                'button_bg': '#3c3c3c',
                'button_fg': '#ffffff',
                'entry_bg': '#2d2d2d',
                'entry_fg': '#ffffff',
                'frame_bg': '#1e1e1e',
                'label_bg': '#1e1e1e',
                'label_fg': '#ffffff',
                'combobox_bg': '#3c3c3c',  # Gray for dropdowns
                'labelframe_border': '#8B4513',  # Dark orange for LabelFrame borders
                'syntax_comando': '#ff6b6b',
                'syntax_parametro': '#5ddef4'
            },
            'modern_dark': {
                'name': 'Escuro Dourado',
                'bg': '#0d1117',
                'fg': '#c9d1d9',
                'canvas_bg': '#161b22',
                'button_bg': '#b8860b',  # Dark golden
                'button_fg': '#ffffff',
                'button_hover': '#d4a017',  # Lighter gold on hover
                'entry_bg': '#21262d',
                'entry_fg': '#c9d1d9',
                'frame_bg': '#0d1117',
                'label_bg': '#0d1117',
                'label_fg': '#c9d1d9',
                'combobox_bg': '#21262d',
                'labelframe_border': '#d4a017',  # Gold border
                'accent': '#ffd700',  # Pure gold accent
                'accent_secondary': '#b8860b',  # Dark goldenrod
                'syntax_comando': '#ff7b72',
                'syntax_parametro': '#79c0ff'
            },
            'modern_light': {
                'name': 'Cinza',
                'bg': '#4a4a4a',           # Medium-dark gray background
                'fg': '#f0f0f0',           # Light text for contrast
                'canvas_bg': '#5a5a5a',    # Slightly lighter gray for canvas
                'button_bg': '#5c6b7a',    # Elegant slate-blue buttons
                'button_fg': '#ffffff',
                'button_hover': '#6d7d8d',
                'entry_bg': '#5a5a5a',
                'entry_fg': '#f0f0f0',
                'frame_bg': '#4a4a4a',
                'label_bg': '#4a4a4a',
                'label_fg': '#f0f0f0',
                'combobox_bg': '#5a5a5a',
                'labelframe_border': '#7a8a9a',  # Subtle slate border
                'accent': '#7d9bb3',       # Muted blue accent
                'accent_secondary': '#8a9aa8',  # Soft slate accent
                'syntax_comando': '#ff9966',    # Soft orange for commands
                'syntax_parametro': '#99ccff'   # Light blue for parameters
            }
        }
        
        # Load saved config
        self.carregar_configuracoes()
        
        # Apply saved window geometry
        self.root.geometry(f"{self.window_width}x{self.window_height}")

        self._setup_ui()
        self._setup_bindings()
        
        # Editor starts empty - wrappers will be auto-added on preview if needed
        
        # Apply initial syntax highlighting
        self.root.after(10, self.aplicar_syntax_highlight)
        
        # Apply saved theme and UI font on startup
        self.root.after(50, self.aplicar_tema)
        self.root.after(60, self.aplicar_fonte_ui)
        
        # Initial update
        self.root.after(1, self.atualizar_visualizacao)

    def _setup_ui(self):
        # ===== MENU BAR =====
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Configurações Menu
        self.menu_config = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Configurações", menu=self.menu_config)
        self.menu_config.add_command(label="Preferências...", command=self.abrir_preferencias)
        
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
        tk.Label(self.sidebar, text="Converter", bg="#f0f0f0", font=("Arial", 8)).pack()
        
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
        self.entrada_texto = tk.Text(self.frame_esquerdo, height=25, width=50, font=("Consolas", self.font_size))
        self.entrada_texto.grid(row=0, column=0, sticky="nsew", pady=5)
        
        # Configure syntax highlighting tags (Labelary style)
        self.entrada_texto.tag_configure("comando", foreground="#8B0000")  # Dark red for commands
        self.entrada_texto.tag_configure("parametro", foreground="#008080")  # Teal for parameters
        self.entrada_texto.tag_configure("convertivel", background="#90EE90")  # Light green for convertible lines
        self.entrada_texto.tag_configure("convertivel_barcode", background="#FFB347")  # Orange for convertible barcodes
        
        # Row 1: Label Settings Group
        self.group_label_config = ttk.LabelFrame(self.frame_esquerdo, text="Configurações da Etiqueta", padding=(5, 5))
        self.group_label_config.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Inner Frame for Inputs
        self.frame_inputs_label = tk.Frame(self.group_label_config)
        self.frame_inputs_label.pack(fill=tk.X, anchor="w")

        # DPI
        tk.Label(self.frame_inputs_label, text="DPI:").pack(side=tk.LEFT, padx=2)
        self.combo_dpi = ttk.Combobox(self.frame_inputs_label, values=["203", "300"], width=5, state="readonly")
        self.combo_dpi.current(1)  # Default 300
        self.combo_dpi.pack(side=tk.LEFT, padx=2)
        
        # Unidade
        tk.Label(self.frame_inputs_label, text="Unidade:").pack(side=tk.LEFT, padx=(10, 2))
        self.combo_unit = ttk.Combobox(self.frame_inputs_label, values=["mm", "cm", "inches"], width=7, state="readonly")
        self.combo_unit.current(0)  # Default mm
        self.combo_unit.pack(side=tk.LEFT, padx=2)
        
        # Largura
        tk.Label(self.frame_inputs_label, text="Largura:").pack(side=tk.LEFT, padx=(10, 2))
        self.spin_width = tk.Spinbox(self.frame_inputs_label, from_=1, to=300, width=5)
        self.spin_width.delete(0, "end")
        self.spin_width.insert(0, "54")  # Default 54mm
        self.spin_width.pack(side=tk.LEFT, padx=2)
        
        # Altura
        tk.Label(self.frame_inputs_label, text="Altura:").pack(side=tk.LEFT, padx=(10, 2))
        self.spin_height = tk.Spinbox(self.frame_inputs_label, from_=1, to=300, width=5)
        self.spin_height.delete(0, "end")
        self.spin_height.insert(0, "38")  # Default 38mm
        self.spin_height.pack(side=tk.LEFT, padx=2)
        
        # Inner Frame for Actions
        self.frame_actions_label = tk.Frame(self.group_label_config)
        self.frame_actions_label.pack(fill=tk.X, anchor="w", pady=(10, 0))
        
        self.botao_atualizar = tk.Button(self.frame_actions_label, text="Atualizar Preview", command=self.atualizar_tudo)
        self.botao_atualizar.pack(side=tk.LEFT, padx=5)
        self.botao_atualizar.config(font=("Arial", 10, "bold"))
        
        # Coordinates Label
        self.rotulo_coordenadas = tk.Label(self.frame_actions_label, text="")
        self.rotulo_coordenadas.pack(side=tk.LEFT, padx=10)
        
        # ===== RIGHT COLUMN: Preview =====
        self.frame_direito = tk.Frame(self.main_frame)
        self.frame_direito.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Row 0: Canvas (Preview Area) - NOW FIRST
        # Use saved canvas size from preferences (or defaults if not set)
        canvas_width_px = self.max_canvas_width
        canvas_height_px = self.max_canvas_height
        
        self.canvas = tk.Canvas(self.frame_direito, bg="white", width=canvas_width_px, height=canvas_height_px)
        self.canvas.pack(pady=5)
        self.canvas.dados_codigo_barras = {}
        self.canvas.dados_texto_bitmap = {}
        self.canvas.dados_zpl_posicao = {}
        
        # Store canvas offset (margin for the viewport)
        self.canvas_margin = 10
        
        # Viewport Rectangle (visual border) - matches canvas dimensions
        self.retangulo = self.canvas.create_rectangle(
            self.canvas_margin, 
            self.canvas_margin, 
            self.canvas_margin + canvas_width_px - 20,  # -20 for margin adjustment
            self.canvas_margin + canvas_height_px - 20,
            outline="#cccccc"
        )
        
        # Row 1: Controls BELOW preview (axis locks + position snap)
        # Row 1: Controls BELOW preview organized in groups
        self.frame_preview_controls = tk.Frame(self.frame_direito)
        self.frame_preview_controls.pack(fill=tk.X, pady=5)
        
        # --- Group 1: Movimento/Travas ---
        self.group_movement = ttk.LabelFrame(self.frame_preview_controls, text="Movimento", padding=(5, 2))
        self.group_movement.pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        self.trava_eixo_x = tk.BooleanVar()
        self.trava_eixo_y = tk.BooleanVar()
        
        self.botao_trava_x = tk.Checkbutton(self.group_movement, text="Travar X", variable=self.trava_eixo_x)
        self.botao_trava_x.pack(side=tk.LEFT, padx=5)
        
        self.botao_trava_y = tk.Checkbutton(self.group_movement, text="Travar Y", variable=self.trava_eixo_y)
        self.botao_trava_y.pack(side=tk.LEFT, padx=5)
        
        # --- Group 2: Grade ---
        self.group_grid = ttk.LabelFrame(self.frame_preview_controls, text="Grade", padding=(5, 2))
        self.group_grid.pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        self.grade_ativa = tk.BooleanVar()
        self.check_grade = tk.Checkbutton(self.group_grid, text="Exibir", 
                                           variable=self.grade_ativa, command=self.atualizar_grade)
        self.check_grade.pack(side=tk.LEFT, padx=5)
        
        self.alinhar_grade = tk.BooleanVar()
        self.check_alinhar = tk.Checkbutton(self.group_grid, text="Alinhar (Snap)", 
                                             variable=self.alinhar_grade)
        self.check_alinhar.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.group_grid, text="Espaço:").pack(side=tk.LEFT, padx=(10, 2))
        self.combo_espacamento_grade = ttk.Combobox(self.group_grid, values=[10, 50, 100, 1000], width=5, state="readonly")
        self.combo_espacamento_grade.current(1)  # Default 50
        self.combo_espacamento_grade.pack(side=tk.LEFT, padx=2)
        self.combo_espacamento_grade.bind("<<ComboboxSelected>>", lambda e: self.atualizar_grade())
        
        # Store grid line IDs for cleanup
        self.linhas_grade = []
        
        # Resolution label in bottom-right corner (will update in real-time)
        self.rotulo_resolucao = tk.Label(
            self.root, 
            text="...", 
            font=("Segoe UI", 9),
            anchor="se"
        )
        self.rotulo_resolucao.place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)
        
        # Update with actual window size after startup
        def atualizar_resolucao_inicial():
            self.rotulo_resolucao.config(text=f"{self.root.winfo_width()}x{self.root.winfo_height()}")
        self.root.after(100, atualizar_resolucao_inicial)



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
        
        # Zoom via Ctrl+Scroll on canvas (Windows)
        self.canvas.bind("<Control-MouseWheel>", self.ao_scroll_zoom)
    
    def ao_redimensionar(self, evento):
        """Update resolution label when window is resized."""
        # Only update for root window events
        if evento.widget == self.root:
            # Use winfo_width/height for actual current size
            largura = evento.width
            altura = evento.height
            if hasattr(self, 'rotulo_resolucao') and largura > 1 and altura > 1:
                self.rotulo_resolucao.config(text=f"{largura}x{altura}")
    
    def abrir_preferencias(self):
        """Open preferences/settings modal."""
        janela = tk.Toplevel(self.root)
        janela.title("Preferências")
        janela.geometry("450x550")  # Increased height for window size section
        janela.transient(self.root)
        janela.grab_set()
        
        # Apply current theme to modal
        t = self.themes.get(self.theme, self.themes['default'])
        janela.config(bg=t['frame_bg'])
        
        # Helper to apply theme to modal widgets
        lf_border = t.get('labelframe_border', t['button_bg'])
        
        def estilizar_modal_widgets(widget):
            try:
                widget_type = widget.winfo_class()
                if widget_type in ('Frame', 'Toplevel'):
                    widget.config(bg=t['frame_bg'])
                elif widget_type == 'Label':
                    widget.config(bg=t['frame_bg'], fg=t['label_fg'])
                elif widget_type == 'Button':
                    widget.config(bg=t['button_bg'], fg=t['button_fg'], 
                                  activebackground=t.get('button_hover', t['button_bg']),
                                  activeforeground=t['button_fg'])
                elif widget_type == 'Spinbox':
                    widget.config(bg=t['entry_bg'], fg=t['entry_fg'], 
                                  buttonbackground=t['button_bg'],
                                  insertbackground=t['entry_fg'])
                elif widget_type == 'LabelFrame':
                    widget.config(bg=t['frame_bg'], fg=t['label_fg'],
                                  highlightbackground=lf_border, highlightcolor=lf_border, highlightthickness=1)
                else:
                    # Try to set bg for unknown widgets
                    try:
                        widget.config(bg=t['frame_bg'])
                    except:
                        pass
            except:
                pass
            for child in widget.winfo_children():
                estilizar_modal_widgets(child)
        
        # Configure ttk styles for modal LabelFrames
        style = ttk.Style()
        style.configure('Modal.TLabelframe', background=t['frame_bg'])
        style.configure('Modal.TLabelframe.Label', 
                        background=t['frame_bg'], 
                        foreground=t['label_fg'],
                        font=('Segoe UI', 10, 'bold'))
        
        # ===== Theme Selection =====
        frame_tema = ttk.LabelFrame(janela, text="Tema", padding=(10, 10), style='Modal.TLabelframe')
        frame_tema.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame_tema, text="Tema da Interface:").pack(side="left")
        theme_names = [(key, self.themes[key]['name']) for key in self.themes]
        theme_var = tk.StringVar(value=self.theme)
        combo_tema = ttk.Combobox(
            frame_tema, 
            values=[name for _, name in theme_names],
            state="readonly",
            width=20
        )
        # Set current theme name
        current_theme_name = self.themes.get(self.theme, {}).get('name', 'Padrão')
        combo_tema.set(current_theme_name)
        combo_tema.pack(side="left", padx=10)
        
        # Store mapping for later
        theme_name_to_key = {name: key for key, name in theme_names}
        # ===== Font Size =====
        frame_fonte = ttk.LabelFrame(janela, text="Fontes", padding=(10, 10), style='Modal.TLabelframe')
        frame_fonte.pack(fill="x", padx=15, pady=10)
        
        # ZPL Editor font
        frame_editor_font = tk.Frame(frame_fonte)
        frame_editor_font.pack(fill="x", pady=2)
        tk.Label(frame_editor_font, text="Editor ZPL:").pack(side="left")
        spin_fonte = tk.Spinbox(frame_editor_font, from_=8, to=24, width=5)
        spin_fonte.delete(0, "end")
        spin_fonte.insert(0, str(self.font_size))
        spin_fonte.pack(side="left", padx=5)
        
        tk.Label(frame_editor_font, text="Fonte:").pack(side="left", padx=(10, 2))
        combo_editor_font = ttk.Combobox(frame_editor_font, values=self.available_editor_fonts, width=15, state="readonly")
        combo_editor_font.set(self.editor_font_family)
        combo_editor_font.pack(side="left", padx=5)
        
        # UI font
        frame_ui_font = tk.Frame(frame_fonte)
        frame_ui_font.pack(fill="x", pady=2)
        tk.Label(frame_ui_font, text="Interface:").pack(side="left")
        spin_ui_fonte = tk.Spinbox(frame_ui_font, from_=8, to=18, width=5)
        spin_ui_fonte.delete(0, "end")
        spin_ui_fonte.insert(0, str(self.ui_font_size))
        spin_ui_fonte.pack(side="left", padx=5)
        
        tk.Label(frame_ui_font, text="Fonte:").pack(side="left", padx=(10, 2))
        combo_ui_font = ttk.Combobox(frame_ui_font, values=self.available_ui_fonts, width=12, state="readonly")
        combo_ui_font.set(self.ui_font_family)
        combo_ui_font.pack(side="left", padx=5)
        
        # ===== Canvas Size =====
        frame_canvas = ttk.LabelFrame(janela, text="Tamanho do Canvas (px)", padding=(10, 10), style='Modal.TLabelframe')
        frame_canvas.pack(fill="x", padx=15, pady=10)
        
        frame_size = tk.Frame(frame_canvas)
        frame_size.pack(fill="x")
        
        tk.Label(frame_size, text="Largura:").pack(side="left")
        spin_max_w = tk.Spinbox(frame_size, from_=400, to=1600, width=6)
        spin_max_w.delete(0, "end")
        spin_max_w.insert(0, str(self.max_canvas_width))
        spin_max_w.pack(side="left", padx=5)
        
        tk.Label(frame_size, text="Altura:").pack(side="left", padx=(10, 0))
        spin_max_h = tk.Spinbox(frame_size, from_=300, to=1200, width=6)
        spin_max_h.delete(0, "end")
        spin_max_h.insert(0, str(self.max_canvas_height))
        spin_max_h.pack(side="left", padx=5)
        
        tk.Label(frame_canvas, text="💡 Use Ctrl+Scroll para zoom no preview", font=("Arial", 9, "italic")).pack(anchor="w", pady=(10, 0))
        
        # ===== Window Size (Resolution) =====
        frame_window = ttk.LabelFrame(janela, text="Tamanho Inicial da Janela (px)", padding=(10, 10), style='Modal.TLabelframe')
        frame_window.pack(fill="x", padx=15, pady=10)
        
        frame_win_size = tk.Frame(frame_window)
        frame_win_size.pack(fill="x")
        
        tk.Label(frame_win_size, text="Largura:").pack(side="left")
        spin_win_w = tk.Spinbox(frame_win_size, from_=800, to=2560, width=6)
        spin_win_w.delete(0, "end")
        spin_win_w.insert(0, str(self.window_width))
        spin_win_w.pack(side="left", padx=5)
        
        tk.Label(frame_win_size, text="Altura:").pack(side="left", padx=(10, 0))
        spin_win_h = tk.Spinbox(frame_win_size, from_=600, to=1440, width=6)
        spin_win_h.delete(0, "end")
        spin_win_h.insert(0, str(self.window_height))
        spin_win_h.pack(side="left", padx=5)
        
        # ===== Apply Button =====
        def aplicar():
            # ZPL Editor font size and family
            try:
                font_size = int(spin_fonte.get())
                self.font_size = font_size
                self.editor_font_family = combo_editor_font.get()
                self.entrada_texto.config(font=(self.editor_font_family, font_size))
            except:
                pass
            
            # UI font size and family (will be applied after theme)
            try:
                ui_font = int(spin_ui_fonte.get())
                self.ui_font_size = ui_font
                self.ui_font_family = combo_ui_font.get()
            except:
                pass
            
            # Canvas size
            try:
                self.max_canvas_width = int(spin_max_w.get())
                self.max_canvas_height = int(spin_max_h.get())
                # Update canvas widget size
                self.canvas.config(width=self.max_canvas_width, height=self.max_canvas_height)
            except:
                pass
            
            # Window size (resolution)
            try:
                self.window_width = int(spin_win_w.get())
                self.window_height = int(spin_win_h.get())
                # Update resolution label
                self.rotulo_resolucao.config(text=f"{self.window_width}x{self.window_height}")
            except:
                pass
            
            # Theme
            selected_theme_name = combo_tema.get()
            self.theme = theme_name_to_key.get(selected_theme_name, 'default')
            
            # Save to config
            self.salvar_configuracoes()
            
            # Apply theme FIRST, then font UI (font must be applied after theme)
            self.aplicar_tema()
            self.aplicar_fonte_ui()
            
            janela.destroy()
            messagebox.showinfo("Preferências", "Configurações salvas!\n\n💡 Use Ctrl+Scroll no preview para zoom.")
        
        tk.Button(janela, text="Aplicar", command=aplicar, bg="#dddddd", height=2).pack(fill="x", padx=15, pady=15)
        
        # Apply theme to all modal widgets
        estilizar_modal_widgets(janela)
    
    def carregar_configuracoes(self):
        """Load settings from config.json."""
        config_path = os.path.join(get_base_path(), 'config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.max_canvas_width = config.get('max_canvas_width', 1000)
                    self.max_canvas_height = config.get('max_canvas_height', 937)
                    self.font_size = config.get('font_size', 12)
                    self.editor_font_family = config.get('editor_font_family', 'Consolas')
                    self.ui_font_size = config.get('ui_font_size', 12)
                    self.ui_font_family = config.get('ui_font_family', 'Segoe UI')
                    self.window_width = config.get('window_width', 1400)
                    self.window_height = config.get('window_height', 700)
                    self.theme = config.get('theme', 'default')
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
    
    def salvar_configuracoes(self):
        """Save settings to config.json."""
        config_path = os.path.join(get_base_path(), 'config.json')
        try:
            config = {
                'max_canvas_width': self.max_canvas_width,
                'max_canvas_height': self.max_canvas_height,
                'font_size': self.font_size,
                'editor_font_family': self.editor_font_family,
                'ui_font_size': self.ui_font_size,
                'ui_font_family': self.ui_font_family,
                'window_width': self.window_width,
                'window_height': self.window_height,
                'theme': self.theme
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
    def aplicar_fonte_ui(self):
        """Apply UI font size and family to all buttons, labels, and other widgets."""
        ui_font = (self.ui_font_family, self.ui_font_size)
        
        # Configure ttk styles for themed widgets
        style = ttk.Style()
        style.configure("TCombobox", font=ui_font)
        style.configure("TButton", font=ui_font)
        style.configure("TLabel", font=ui_font)
        style.configure("TSpinbox", font=ui_font)
        style.configure("TCheckbutton", font=ui_font)
        style.configure("TRadiobutton", font=ui_font)
        style.configure("TLabelframe.Label", font=ui_font)
        
        # Also configure the Option.TMenubutton for combobox dropdown
        self.root.option_add("*TCombobox*Listbox*Font", ui_font)
        
        def update_widget_font(widget):
            try:
                # Skip the ZPL text editor
                if widget == self.entrada_texto:
                    for child in widget.winfo_children():
                        update_widget_font(child)
                    return
                
                # Try to apply font to any widget that supports it
                try:
                    widget.config(font=ui_font)
                except tk.TclError:
                    pass  # Widget doesn't support font config
                
                # Recursively apply to children
                for child in widget.winfo_children():
                    update_widget_font(child)
            except Exception:
                pass
        
        # Apply to root and all children
        update_widget_font(self.root)
    
    def estilizar_modal(self, janela):
        """Apply current theme and font styling to a modal window."""
        t = self.themes.get(self.theme, self.themes['default'])
        ui_font = (self.ui_font_family, self.ui_font_size)
        lf_border = t.get('labelframe_border', t['button_bg'])
        
        janela.config(bg=t['frame_bg'])
        
        def estilizar_widget(widget):
            try:
                widget_type = widget.winfo_class()
                if widget_type in ('Frame', 'Toplevel'):
                    widget.config(bg=t['frame_bg'])
                elif widget_type == 'Label':
                    widget.config(bg=t['frame_bg'], fg=t['label_fg'], font=ui_font)
                elif widget_type == 'Button':
                    widget.config(bg=t['button_bg'], fg=t['button_fg'], 
                                  activebackground=t.get('button_hover', t['button_bg']),
                                  activeforeground=t['button_fg'], font=ui_font)
                elif widget_type in ('Spinbox', 'Entry'):
                    widget.config(bg=t['entry_bg'], fg=t['entry_fg'], 
                                  insertbackground=t['entry_fg'], font=ui_font)
                elif widget_type == 'LabelFrame':
                    widget.config(bg=t['frame_bg'], fg=t['label_fg'],
                                  highlightbackground=lf_border, highlightcolor=lf_border, highlightthickness=1)
                else:
                    try:
                        widget.config(bg=t['frame_bg'])
                    except:
                        pass
            except:
                pass
            for child in widget.winfo_children():
                estilizar_widget(child)
        
        estilizar_widget(janela)
    
    def aplicar_tema(self):
        """Apply the current theme to all widgets."""
        t = self.themes.get(self.theme, self.themes['default'])
        
        # Root window
        self.root.config(bg=t['bg'])
        
        # Main frames
        try:
            self.main_frame.config(bg=t['frame_bg'])
            self.frame_esquerdo.config(bg=t['frame_bg'])
            self.frame_direito.config(bg=t['frame_bg'])
        except:
            pass
        
        # Canvas
        try:
            self.canvas.config(bg=t['canvas_bg'])
        except:
            pass
        
        # Text entry
        try:
            self.entrada_texto.config(bg=t['entry_bg'], fg=t['entry_fg'], 
                                      insertbackground=t['entry_fg'])
        except:
            pass
        
        # Update all buttons recursively
        def update_widget(widget):
            try:
                widget_type = widget.winfo_class()
                if widget_type == 'Button':
                    button_hover = t.get('button_hover', t['button_bg'])
                    widget.config(bg=t['button_bg'], fg=t['button_fg'],
                                  activebackground=button_hover, activeforeground=t['button_fg'],
                                  font=('Segoe UI', 9), relief='flat', bd=0,
                                  padx=10, pady=5)
                    # Bind hover effects
                    widget.bind('<Enter>', lambda e, w=widget, c=button_hover: w.config(bg=c))
                    widget.bind('<Leave>', lambda e, w=widget, c=t['button_bg']: w.config(bg=c))
                elif widget_type == 'Label':
                    widget.config(bg=t['label_bg'], fg=t['label_fg'], font=('Segoe UI', 9))
                elif widget_type == 'Frame':
                    widget.config(bg=t['frame_bg'])
                elif widget_type == 'LabelFrame':
                    # Legacy support for tk.LabelFrame if any remain
                    lf_border = t.get('labelframe_border', t['button_bg'])
                    widget.config(bg=t['frame_bg'], fg=t['label_fg'],
                                  highlightbackground=lf_border, highlightcolor=lf_border,
                                  highlightthickness=1, font=('Segoe UI', 9, 'bold'))
                elif widget_type == 'Checkbutton':
                    widget.config(bg=t['frame_bg'], fg=t['label_fg'],
                                  selectcolor=t['entry_bg'], activebackground=t['frame_bg'],
                                  font=('Segoe UI', 9), activeforeground=t['label_fg'])
                elif widget_type == 'Radiobutton':
                    widget.config(bg=t['frame_bg'], fg=t['label_fg'],
                                  selectcolor=t['entry_bg'], activebackground=t['frame_bg'],
                                  font=('Segoe UI', 9), activeforeground=t['label_fg'])
                elif widget_type == 'Spinbox':
                    widget.config(bg=t['entry_bg'], fg=t['entry_fg'],
                                  buttonbackground=t['button_bg'], insertbackground=t['entry_fg'],
                                  font=('Consolas', 10), relief='flat', bd=5)
                elif widget_type == 'Entry':
                    widget.config(bg=t['entry_bg'], fg=t['entry_fg'],
                                  insertbackground=t['entry_fg'],
                                  font=('Consolas', 10), relief='flat', bd=5)
            except:
                pass
            
            for child in widget.winfo_children():
                update_widget(child)
        
        update_widget(self.root)
        
        # Update ttk Combobox style - use 'clam' theme for better customization
        style = ttk.Style()
        style.theme_use('clam')  # clam theme allows better color control on Windows
        
        # Use combobox_bg if defined, otherwise entry_bg
        combo_bg = t.get('combobox_bg', t['entry_bg'])
        
        # Combobox styling
        style.configure('TCombobox', 
                       fieldbackground=combo_bg,
                       background=t['button_bg'],
                       foreground=t['entry_fg'],
                       arrowcolor=t['entry_fg'],
                       bordercolor=t['button_bg'],
                       lightcolor=t['frame_bg'],
                       darkcolor=t['frame_bg'])
        
        # Map for different states (readonly, disabled, etc)
        style.map('TCombobox',
                  fieldbackground=[('readonly', combo_bg), ('disabled', t['frame_bg']), ('!disabled', combo_bg)],
                  background=[('active', t['button_bg']), ('pressed', t['button_bg'])],
                  foreground=[('disabled', t['label_fg'])],
                  bordercolor=[('focus', t['button_bg'])])
        
        # LabelFrame styling
        labelframe_border = t.get('labelframe_border', t['button_bg'])
        style.configure('TLabelframe', 
                       background=t['frame_bg'],
                       foreground=t['label_fg'],
                       bordercolor=labelframe_border,
                       relief='solid')
        style.configure('TLabelframe.Label', 
                       background=t['frame_bg'],
                       foreground=t['label_fg'],
                       font=('Segoe UI', 9, 'bold'))
        
        # TButton styling for modern look
        button_hover = t.get('button_hover', t['button_bg'])
        style.configure('TButton',
                       background=t['button_bg'],
                       foreground=t['button_fg'],
                       padding=(10, 5),
                       font=('Segoe UI', 9))
        style.map('TButton',
                  background=[('active', button_hover), ('pressed', button_hover)],
                  foreground=[('active', t['button_fg'])])
        
        # TEntry styling
        style.configure('TEntry',
                       fieldbackground=t['entry_bg'],
                       foreground=t['entry_fg'],
                       padding=5)
        
        # TSpinbox styling
        style.configure('TSpinbox',
                       fieldbackground=t['entry_bg'],
                       foreground=t['entry_fg'],
                       arrowcolor=t['entry_fg'])
        
        # TCheckbutton styling
        style.configure('TCheckbutton',
                       background=t['frame_bg'],
                       foreground=t['label_fg'])
        
        # Update syntax highlighting colors for dark themes
        if 'syntax_comando' in t:
            self.entrada_texto.tag_configure("comando", foreground=t['syntax_comando'])
        else:
            self.entrada_texto.tag_configure("comando", foreground="#8B0000")  # Default dark red
        
        if 'syntax_parametro' in t:
            self.entrada_texto.tag_configure("parametro", foreground=t['syntax_parametro'])
        else:
            self.entrada_texto.tag_configure("parametro", foreground="#008B8B")  # Default cyan
        
        # Apply border color to ZPL text editor (entrada_texto)
        labelframe_border = t.get('labelframe_border', t['button_bg'])
        self.entrada_texto.config(
            highlightbackground=labelframe_border,
            highlightcolor=labelframe_border,
            highlightthickness=2
        )
        
        # Apply border color to canvas viewport rectangle
        if hasattr(self, 'retangulo') and self.retangulo:
            self.canvas.itemconfig(self.retangulo, outline=labelframe_border, width=2)
    

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
        
        # Canvas dimensions (apply scale factor)
        canvas_w = int(width_mm * dpmm * self.scale_factor)
        canvas_h = int(height_mm * dpmm * self.scale_factor)
        
        # Scale the spacing too
        espacamento_escala = espacamento * self.scale_factor
        
        # Grid line color (light gray)
        cor_grade = "#d0d0d0"
        
        # Draw vertical lines
        x = espacamento_escala
        while x < canvas_w:
            linha_id = self.canvas.create_line(
                margin + x, margin,
                margin + x, margin + canvas_h,
                fill=cor_grade, tags=("grade",)
            )
            self.linhas_grade.append(linha_id)
            # Bring to front (on top of other elements)
            self.canvas.tag_raise(linha_id)
            x += espacamento_escala
        
        # Draw horizontal lines
        y = espacamento_escala
        while y < canvas_h:
            linha_id = self.canvas.create_line(
                margin, margin + y,
                margin + canvas_w, margin + y,
                fill=cor_grade, tags=("grade",)
            )
            self.linhas_grade.append(linha_id)
            self.canvas.tag_raise(linha_id)
            y += espacamento_escala
    
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
        # Using case-insensitive flag in finditer
        barcode_pattern = r'(?i)([~^])(B[0-9A-Z])((?:,?[\d\.]+)+)?'
        
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
        other_pattern = r'(?i)([~^])([A-Z@][A-Z]?)((?:[\d,\.]+)+)?'
        
        for match in re.finditer(other_pattern, codigo):
            cmd_name = match.group(2)
            # Skip if this is a barcode command (starts with B followed by alphanumeric)
            if cmd_name.upper().startswith('B') and len(cmd_name) == 2 and cmd_name[1].isalnum():
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
        
        # Special rule: ^FD...^FS (Text content)
        
        # Special rule: ^RLM...^FS - ALL content between is parameter (cyan)
        for match in re.finditer(r'(?i)\^RLM([^\^]*)\^FS', codigo):
            if match.group(1):
                param_start = f"1.0+{match.start(1)}c"
                param_end = f"1.0+{match.end(1)}c"
                self.entrada_texto.tag_add("parametro", param_start, param_end)
        
        # Special rule: ^RF...^FD - content between RF and FD is parameter (cyan) 
        for match in re.finditer(r'(?i)\^RF([^\^]*)\^FD', codigo):
            if match.group(1):
                param_start = f"1.0+{match.start(1)}c"
                param_end = f"1.0+{match.end(1)}c"
                self.entrada_texto.tag_add("parametro", param_start, param_end)
        
        # IMPORTANT: Remove parametro tag from ^FD...^FS content (text should be black)
        # This must run AFTER all other rules to override any incorrect tagging
        for match in re.finditer(r'(?i)\^FD([^\^]*)\^FS', codigo):
            if match.group(1):
                text_start = f"1.0+{match.start(1)}c"
                text_end = f"1.0+{match.end(1)}c"
                self.entrada_texto.tag_remove("parametro", text_start, text_end)

    def ao_colar_texto(self, event):
        try:
            texto_colado = self.root.clipboard_get()
        except tk.TclError:
            return "break"

        # Check if there's a selection that covers all text (Ctrl+A was used)
        try:
            sel_start = self.entrada_texto.index(tk.SEL_FIRST)
            sel_end = self.entrada_texto.index(tk.SEL_LAST)
            all_start = self.entrada_texto.index("1.0")
            all_end = self.entrada_texto.index("end-1c")
            
            # If selection covers all text, do a full replacement
            if sel_start == all_start and sel_end == all_end:
                self.entrada_texto.delete("1.0", tk.END)
                self.entrada_texto.insert("1.0", texto_colado)
                self.aplicar_syntax_highlight()
                return "break"
        except tk.TclError:
            # No selection - continue with normal logic
            pass

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
        """Highlight lines that can be converted to mini-objects (Text or Barcode)."""
        self.entrada_texto.tag_remove("convertivel", "1.0", tk.END)
        self.entrada_texto.tag_remove("convertivel_barcode", "1.0", tk.END)
        self.linhas_convertiveis = {}
        
        codigo = self.entrada_texto.get("1.0", tk.END)
        
        # Pattern for text: Multi-line (?is), stops at next ^FO to prevent merging
        # Width is now optional - ^A0N,49 only has height, width defaults to height
        pattern_text = r'(?is)\^FO\s*(\d+)\s*,\s*(\d+)(?:(?!\^FO).)*?\^A[A-Z0-9@]([NRIBnrib]?)\s*,?\s*(\d+)(?:\s*,\s*(\d+))?.*?\^FD(.*?)\^FS'
        
        # Pattern for barcode: Multi-line (?is), stops at next ^FO
        pattern_barcode = r'(?is)\^FO\s*(\d+)\s*,\s*(\d+)(?:(?!\^FO).)*?(\^B[CUE][^\^]*).*?\^FD(.*?)\^FS'
        
        # Helper to convert index to line
        def get_line_from_index(index):
            return int(self.entrada_texto.index(f"1.0 + {index} chars").split('.')[0])

        # Scan for Text
        for match in re.finditer(pattern_text, codigo):
            snippet = match.group(0)
            if snippet in self.linhas_convertidas: continue
            
            altura = int(match.group(4))
            # Width is optional - if not present, default to height (or proportional)
            largura = int(match.group(5)) if match.group(5) else altura
            
            params = {
                'x': int(match.group(1)),
                'y': int(match.group(2)),
                'orientacao': match.group(3) if match.group(3) else 'N',
                'altura': altura,
                'largura': largura,
                'texto': match.group(6),
                'tipo': 'texto'
            }
            
            start_pos = f"1.0 + {match.start()} chars"
            end_pos = f"1.0 + {match.end()} chars"
            self.entrada_texto.tag_add("convertivel", start_pos, end_pos)
            
            start_line = get_line_from_index(match.start())
            end_line = get_line_from_index(match.end())
            for ln in range(start_line, end_line + 1):
                self.linhas_convertiveis[ln] = {'snippet': snippet, 'params': params}
                
        # Scan for Barcode
        for match in re.finditer(pattern_barcode, codigo):
            snippet = match.group(0)
            if snippet in self.linhas_convertidas: continue
                
            cmd_full = match.group(3)
            orientacao_bc = 'N'
            cmd_clean_parse = cmd_full.replace('\n', '').replace('\r', '')
            cmd_only = cmd_clean_parse.split(',')[0]
            if len(cmd_only) >= 4 and cmd_only[3] in 'NRIBnrib':
                 orientacao_bc = cmd_only[3]
            
            params = {
                'x': int(match.group(1)),
                'y': int(match.group(2)),
                'comando': cmd_full,
                'texto': match.group(4),
                'tipo': 'codigo_barras',
                'orientacao': orientacao_bc
            }
            
            start_pos = f"1.0 + {match.start()} chars"
            end_pos = f"1.0 + {match.end()} chars"
            self.entrada_texto.tag_add("convertivel_barcode", start_pos, end_pos)
            
            start_line = get_line_from_index(match.start())
            end_line = get_line_from_index(match.end())
            for ln in range(start_line, end_line + 1):
                self.linhas_convertiveis[ln] = {'snippet': snippet, 'params': params}

        while False: # Loop Deleted
            if match_text:
                snippet = match_text.group(0)
                params = {
                    'x': int(match_text.group(1)),
                    'y': int(match_text.group(2)),
                    'orientacao': match_text.group(3) if match_text.group(3) else 'N',
                    'altura': int(match_text.group(4)),
                    'largura': int(match_text.group(5)),
                    'texto': match_text.group(6),
                    'tipo': 'texto'
                }
                
                # Check if this snippet was already converted
                if snippet not in self.linhas_convertidas:
                    self.linhas_convertiveis[linha_num] = {'snippet': snippet, 'params': params}
                    
                    # Highlight in green
                    start_idx = f"{linha_num}.0"
                    end_idx = f"{linha_num}.end"
                    self.entrada_texto.tag_add("convertivel", start_idx, end_idx)
                continue # Text matched, skip barcode check for this line
                
            # Check for Barcode
            match_barcode = re.search(pattern_barcode, linha)
            if match_barcode:
                snippet = match_barcode.group(0)
                cmd_full = match_barcode.group(3) # e.g. ^BEB,30,Y,N
                
                # Extract orientation from command
                orientacao_bc = 'N'
                cmd_only = cmd_full.split(',')[0] # get just ^BEB part
                if len(cmd_only) >= 4:
                     # e.g. ^BEB -> B at index 3
                     possible_orient = cmd_only[3]
                     if possible_orient in 'NRIBnrib':
                         orientacao_bc = possible_orient
                
                params = {
                    'x': int(match_barcode.group(1)),
                    'y': int(match_barcode.group(2)),
                    'comando': cmd_full,
                    'texto': match_barcode.group(4),
                    'tipo': 'codigo_barras',
                    'orientacao': orientacao_bc
                }
                
                # Check if this snippet was already converted
                if snippet not in self.linhas_convertidas:
                    self.linhas_convertiveis[linha_num] = {'snippet': snippet, 'params': params}
                    
                    # Highlight in orange
                    start_idx = f"{linha_num}.0"
                    end_idx = f"{linha_num}.end"
                    self.entrada_texto.tag_add("convertivel_barcode", start_idx, end_idx)
    
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
        self.entrada_texto.tag_remove("convertivel_barcode", "1.0", tk.END)
        self.linhas_convertiveis = {}
        self.modo_conversao_ativo = False
        self.selecionar_ferramenta(None)  # Switch to selection tool
        
        # Re-apply syntax highlighting
        self.aplicar_syntax_highlight()
        
        # Step 1: Update main preview (filtered, without this line)
        # Step 2: After delay, create the mini-object
        def atualizar_preview_filtrado():
            # Call directly on main thread -- it manages its own threading after data gathering
            self.fetch_labelary_preview()
        
        def criar_objeto_apos_delay():
            self.criar_mini_objeto_labelary(zpl_snippet, canvas_x, canvas_y, params)
        
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
            self.entrada_texto.tag_remove("convertivel_barcode", "1.0", tk.END)
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
            self.canvas.config(cursor="arrow")
            self.modo_conversao_ativo = True
            # Trigger highlight analysis
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
    

    
    def criar_codigo_barras_em_posicao(self, x, y):
        """Create a barcode element at the given position."""
        # Calculate ZPL coordinates (relative to canvas margin)
        margin = getattr(self, 'canvas_margin', 10)
        zpl_x = max(0, int(x) - margin)
        zpl_y = max(0, int(y) - margin)
        
        # Default barcode (UPC-A format, needs 11 digits)
        zpl_snippet = f"^FO{zpl_x},{zpl_y}^BY2^BUN,80^FD12345678901^FS"
        params = {
            'tipo': 'codigo_barras',
            'comando': '^BUN,80',
            'texto': '12345678901',
            'x': zpl_x,
            'y': zpl_y
        }
        
        # Insert before ^XZ if possible
        pos_xz = self.entrada_texto.search("^XZ", "1.0", tk.END)
        if pos_xz:
            self.entrada_texto.insert(pos_xz, zpl_snippet + "\n")
        else:
            self.entrada_texto.insert(tk.END, zpl_snippet + "\n")
        
        # Re-apply syntax highlighting
        self.aplicar_syntax_highlight()
        
        # Create mini-object at canvas position
        self.criar_mini_objeto_labelary(zpl_snippet, x, y, params)
        
        # Switch to selection mode
        self.selecionar_ferramenta(None)
    
    def criar_mini_objeto_labelary(self, zpl_snippet, canvas_x, canvas_y, params=None):
        """
        Create a mini-object on canvas by fetching from Labelary API.
        The snippet is rendered independently with ^FO0,0.
        """
        # Deduplication check: don't create if this snippet already exists as a mini-object
        for item_id, obj_data in self.mini_objetos.items():
            if obj_data.get('zpl') == zpl_snippet:
                print(f"Skipping duplicate mini-object for: {zpl_snippet[:50]}...")
                return
        
        def fetch_and_create():
            try:
                # Get DPI from UI
                dpi = self.combo_dpi.get()
                dpmm = 12 if dpi == "300" else 8
                
                # Use passed params or extract if not provided
                extracted_params = params
                if not extracted_params:
                    # Fallback to extraction (mainly for legacy/text)
                    from zpl_utils import extrair_parametros_texto
                    extracted_params = extrair_parametros_texto(zpl_snippet)
                
                if extracted_params and 'tipo' not in extracted_params:
                     extracted_params['tipo'] = 'texto' # Default to text if not specified

                # Estimate dimensions for the request
                if extracted_params and extracted_params.get('tipo') == 'texto':
                    largura_mm, altura_mm = calcular_dimensoes_texto(
                        extracted_params.get('altura', 30), 
                        extracted_params.get('largura', 30), 
                        extracted_params.get('texto', 'TEXT'), 
                        dpi=int(dpi),
                        orientacao=extracted_params.get('orientacao', 'N')
                    )
                elif extracted_params and extracted_params.get('tipo') == 'codigo_barras':
                    # Barcodes need more width to avoid cutting off numbers
                    largura_mm = 80
                    altura_mm = 40
                    
                    # Swap if vertical orientation
                    orient = extracted_params.get('orientacao', 'N')
                    if orient and orient.upper() in ['R', 'B']:
                        largura_mm, altura_mm = altura_mm, largura_mm
                else:
                    # Default/Fallback dimensions for unknown
                    largura_mm = 50 
                    altura_mm = 30
                
                # Normalize ZPL: remove original ^FO and add ^FO0,0
                # For barcodes: use dynamic ^FO based on ^BY value (prevents cutting first digit)
                barcode_offset_x = 0  # Position compensation
                if extracted_params and extracted_params.get('tipo') == 'codigo_barras':
                    # Extract ^BY value to calculate appropriate left margin
                    by_match = re.search(r'\^BY(\d+)', zpl_snippet)
                    by_value = int(by_match.group(1)) if by_match else 2
                    # Dynamic offset: base 22 + (by_value - 2) * 10  (scales with module width)
                    left_offset = 22 + (by_value - 2) * 10
                    # Remove existing ^FO and add one with calculated left margin
                    zpl_sem_fo = re.sub(r'\^FO\d+,\d+', '', zpl_snippet)
                    zpl_normalizado = f"^XA^FO{left_offset},0{zpl_sem_fo}^XZ"
                    # Compensate canvas position: shift left by the offset amount
                    barcode_offset_x = left_offset
                else:
                    zpl_normalizado = normalizar_zpl_para_mini_objeto(zpl_snippet)
                
                # Fetch from Labelary
                image = fetch_labelary_element(zpl_normalizado, dpmm, largura_mm, altura_mm)
                
                if image:
                    # Store original unscaled image for zoom operations
                    image_raw = image.copy()
                    
                    # Apply current zoom level to mini-object image
                    if self.zoom_level != 1.0:
                        new_width = max(1, int(image.width * self.zoom_level))
                        new_height = max(1, int(image.height * self.zoom_level))
                        image = image.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Calculate zoomed canvas position (compensate for barcode offset)
                    compensated_x = canvas_x - barcode_offset_x
                    zoomed_x = self.canvas_margin + ((compensated_x - self.canvas_margin) * self.zoom_level)
                    zoomed_y = self.canvas_margin + ((canvas_y - self.canvas_margin) * self.zoom_level)
                    
                    # Create PhotoImage in main thread
                    def create_on_canvas():
                        photo = ImageTk.PhotoImage(image)
                        
                        # Create image on canvas at ZOOMED position
                        item_id = self.canvas.create_image(
                            zoomed_x, zoomed_y,
                            image=photo,
                            anchor=tk.NW,
                            tags=("mini_objeto",)
                        )
                        
                        # Store reference (keep ORIGINAL ZPL coords for editing)
                        self.mini_objetos[item_id] = {
                            'zpl': zpl_snippet,
                            'x': canvas_x,  # Original ZPL + margin
                            'y': canvas_y,  # Original ZPL + margin
                            'photo': photo,
                            'image_raw': image_raw,  # Original PIL image for zoom
                            'params': extracted_params, # Store params for editing
                            'barcode_offset_x': barcode_offset_x  # Compensation offset
                        }
                        
                        # Store ZPL position info for editing
                        # Find the match position in the text
                        codigo_zpl = self.entrada_texto.get("1.0", tk.END)
                        match_start = codigo_zpl.find(zpl_snippet)
                        if match_start >= 0:
                            match_end = match_start + len(zpl_snippet)
                            tipo_obj = extracted_params.get('tipo', 'outro') if extracted_params else 'outro'
                            self.canvas.dados_zpl_posicao[item_id] = (match_start, match_end, tipo_obj)
                        
                        # Bind drag events
                        # Bind drag events
                        self.canvas.tag_bind(item_id, "<ButtonPress-1>", self.ao_pressionar_elemento)
                        self.canvas.tag_bind(item_id, "<B1-Motion>", self.ao_arrastar_elemento)
                        self.canvas.tag_bind(item_id, "<ButtonRelease-1>", self.ao_soltar_arrasto)
                        # Double-click handled by global canvas binding (ao_duplo_clique_canvas)
                        
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
        params = mini_obj.get('params', {})
        
        # Dispatch to barcode editor if type is barcode
        if params and params.get('tipo') == 'codigo_barras':
            self.abrir_janela_edicao_codigo_barras(item, mini_obj)
            return

        zpl_snippet = mini_obj['zpl']
        
        # Try to parse text parameters if not present
        if not params:
            params = extrair_parametros_texto(zpl_snippet)
        
        janela = tk.Toplevel(self.root)
        janela.title("Editar Texto")
        janela.geometry("350x280")
        janela.transient(self.root)
        
        # Content content (Text)
        tk.Label(janela, text="Conteúdo:").pack(pady=(10, 0))
        entry_texto = tk.Entry(janela, width=40)
        entry_texto.pack(pady=5)
        current_text = params['texto'] if params else ""
        entry_texto.insert(0, current_text)
        
        # Dimensions (Text specific)
        frame_dim = tk.Frame(janela)
        frame_dim.pack(pady=5)
        
        tk.Label(frame_dim, text="Altura:").pack(side=tk.LEFT)
        spin_h = tk.Spinbox(frame_dim, from_=10, to=200, width=5)
        spin_h.pack(side=tk.LEFT, padx=5)
        spin_h.delete(0, "end")
        spin_h.insert(0, params['altura'] if params else "30")
        
        tk.Label(frame_dim, text="Largura:").pack(side=tk.LEFT)
        spin_w = tk.Spinbox(frame_dim, from_=10, to=200, width=5)
        spin_w.pack(side=tk.LEFT, padx=5)
        spin_w.delete(0, "end")
        spin_w.insert(0, params['largura'] if params else "30")
        
        # Orientation
        frame_orient = tk.Frame(janela)
        frame_orient.pack(pady=5)
        tk.Label(frame_orient, text="Orientação:").pack(side=tk.LEFT)
        combo_orient = ttk.Combobox(frame_orient, values=["N", "R", "I", "B"], width=5, state="readonly")
        combo_orient.pack(side=tk.LEFT, padx=5)
        current_orient = params.get('orientacao', 'N') if params else 'N'
        combo_orient.set(current_orient)

        def confirmar():
            novo_texto = entry_texto.get().strip()
            nova_altura = spin_h.get()
            nova_largura = spin_w.get()
            nova_orient = combo_orient.get()
            
            if novo_texto:
                # Reconstruct ZPL for text
                # Retrieve current position
                orig_x = params['x'] if params else 10
                orig_y = params['y'] if params else 10
                
                # Check for position update from canvas (if moved)
                coords = self.canvas.coords(item)
                if coords:
                    margin = getattr(self, 'canvas_margin', 10)
                    orig_x = int(coords[0] - margin)
                    orig_y = int(coords[1] - margin)
                
                novo_zpl = f"^FO{orig_x},{orig_y}^A0{nova_orient},{nova_altura},{nova_largura}^FD{novo_texto}^FS"
                
                self.atualizar_mini_objeto(item, novo_zpl)
                janela.destroy()
        
        tk.Button(janela, text="Confirmar", command=confirmar, bg="#dddddd").pack(pady=15)
        
        # Apply theme and font styling
        self.estilizar_modal(janela)

    def atualizar_mini_objeto(self, item, novo_zpl):
        """Update a mini-object's ZPL in the editor and refresh it."""
        if item not in self.mini_objetos:
            return

        mini_obj = self.mini_objetos[item]
        old_zpl = mini_obj['zpl'].strip()
        novo_zpl = novo_zpl.strip()
        
        codigo_zpl = self.entrada_texto.get("1.0", tk.END)
        
        # Try to find the old ZPL
        # First try exact match (stripped)
        old_zpl_found = False
        target_zpl = old_zpl
        
        if target_zpl in codigo_zpl:
            old_zpl_found = True
        elif target_zpl + "\n" in codigo_zpl:
             target_zpl = target_zpl + "\n"
             old_zpl_found = True
        # Try strict match (unstripped) if stored differently
        elif mini_obj['zpl'] in codigo_zpl:
             target_zpl = mini_obj['zpl']
             old_zpl_found = True

        if old_zpl_found:
            codigo_zpl = codigo_zpl.replace(target_zpl, novo_zpl + ("\n" if target_zpl.endswith("\n") else ""), 1)
            self.entrada_texto.delete("1.0", tk.END)
            self.entrada_texto.insert("1.0", codigo_zpl.rstrip())
            
            # Remove old item
            self.canvas.delete(item)
            del self.mini_objetos[item]
            
            # Create new item (will take a moment)
            # We need to extract params again if we want to pass them, 
            # OR we can assume the new ZPL is enough for re-parsing.
            # But for barcodes, we might want to pass the type explicitly if we want to rely on it.
            # However, our regex detection in 'converter_linha_para_objeto' handled initial creation.
            # Here we are re-creating. 
            
            # If we just put it in text, user might "Update Preview".
            # But we want immediate feedback.
            
            # We need to pass 'params' to 'criar_mini_objeto_labelary' to ensure type is preserved/updated.
            # Re-parse params from the NEW ZPL to get the correct state.
            from zpl_utils import extrair_parametros_texto
            
            # Determine type from new ZPL content
            new_params = extrair_parametros_texto(novo_zpl) or {}
            if '^BC' in novo_zpl or '^BE' in novo_zpl or '^BU' in novo_zpl:
                new_params['tipo'] = 'codigo_barras'
                # Extract command
                match = re.search(r'(\^B[CUE][^FD]*)', novo_zpl)
                if match:
                    new_params['comando'] = match.group(1)
                match_text = re.search(r'\^FD([^\^]+)\^FS', novo_zpl)
                if match_text:
                    new_params['texto'] = match_text.group(1)
                # Coordinates
                match_fo = re.search(r'\^FO(\d+),(\d+)', novo_zpl)
                if match_fo:
                     new_params['x'] = int(match_fo.group(1))
                     new_params['y'] = int(match_fo.group(2))

            # Extract margin from self
            margin = getattr(self, 'canvas_margin', 10)
            canvas_x = new_params.get('x', 0) + margin
            canvas_y = new_params.get('y', 0) + margin

            self.criar_mini_objeto_labelary(novo_zpl, canvas_x, canvas_y, params=new_params)
            
            # Re-apply syntax highlighting and conversion highlighting
            self.aplicar_syntax_highlight()
            self.destacar_linhas_convertiveis()
            
        else:
            messagebox.showwarning("Aviso", "Não foi possível encontrar o código original para substituir.")

    def abrir_janela_edicao_codigo_barras(self, item, mini_obj):
        """Open dedicated edit dialog for barcode."""
        janela = tk.Toplevel(self.root)
        janela.title("Editar Código de Barras")
        janela.geometry("400x350")
        janela.transient(self.root)
        
        snippet = mini_obj['zpl']
        params = mini_obj.get('params', {})
        
        # Parse existing Barcode Params from snippet (Case Insensitive)
        match_by = re.search(r'(?i)\^BY(\d+)(?:,(\d*\.?\d*))?(?:,(\d+))?', snippet)
        largura_modulo = match_by.group(1) if match_by else "2"
        # by_ratio, by_height ignored for BY dropdown but parsed
        
        # Parse Text/Data
        texto_atual = params.get('texto', '')
        
        # Parse Type and specific params (^BC, ^BE, ^BU)
        cmd_full = params.get('comando', '^BEN') # Default command snippet
        
        tipo_atual = 'EAN-13' # Default
        orientation = params.get('orientacao', 'N') # Use stored orientation if available
        altura_barras = "50"
        
        if re.search(r'(?i)\^BC', cmd_full): tipo_atual = 'Code 128'
        elif re.search(r'(?i)\^BU', cmd_full): tipo_atual = 'UPC-A'
        elif re.search(r'(?i)\^BE', cmd_full): tipo_atual = 'EAN-13'
        
        # Remove ^B[CUE] to parse params
        cmd_clean = re.sub(r'(?i)\^B[CUE]', '', cmd_full)
        
        # Fallback to parse height from snippet if not in params or empty
        # Try to find height in common formats like ^BCN,height,...
        # Captures height from: ^B[CUE]o,h
        match_height = re.search(r'(?i)\^B[CUE][NRIBnrib]?,(\d+)', snippet)
        if match_height:
             altura_barras = match_height.group(1)
        
        parts = cmd_clean.split(',')
        
        # Only parse orientation from command if not already in params (legacy/fallback)
        if hasattr(self, 'linhas_convertiveis') and not params.get('orientacao'):
             if len(parts) > 0 and len(parts[0]) > 0:
                  if parts[0][0] in "NRIB":
                      orientation = parts[0][0]
        
        if len(parts) > 1 and parts[1].strip():
            altura_barras = parts[1].strip()
            
        # UI Fields
        tk.Label(janela, text="Tipo:").pack(anchor="w", padx=20, pady=(10,0))
        combo_tipo = ttk.Combobox(janela, values=['Code 128', 'EAN-13', 'UPC-A'], state="readonly")
        combo_tipo.set(tipo_atual)
        combo_tipo.pack(fill="x", padx=20)
        
        tk.Label(janela, text="Dados:").pack(anchor="w", padx=20, pady=(5,0))
        entry_dados = tk.Entry(janela)
        entry_dados.insert(0, texto_atual)
        entry_dados.pack(fill="x", padx=20)
        
        frame_dims = tk.Frame(janela)
        frame_dims.pack(fill="x", padx=20, pady=10)
        
        tk.Label(frame_dims, text="Tamanho:").pack(side="left")
        combo_width = ttk.Combobox(frame_dims, values=["1", "2", "3", "4", "5"], width=3, state="readonly")
        combo_width.set(largura_modulo)
        combo_width.pack(side="left", padx=5)
        
        tk.Label(frame_dims, text="Altura:").pack(side="left", padx=(10,0))
        spin_height = tk.Spinbox(frame_dims, from_=10, to=2000, width=5)
        spin_height.delete(0, "end")
        spin_height.insert(0, altura_barras)
        spin_height.pack(side="left", padx=5)
        
        tk.Label(frame_dims, text="Orientação:").pack(side="left", padx=(10,0))
        combo_orient = ttk.Combobox(frame_dims, values=["N", "R", "I", "B"], width=10, state="readonly")
        combo_orient.set(orientation)
        combo_orient.pack(side="left", padx=5)
        
        frame_opts = tk.Frame(janela)
        frame_opts.pack(fill="x", padx=20, pady=5)
        
        var_line = tk.BooleanVar(value=True) 
        # var_above removed
        # var_digit removed
        
        tk.Checkbutton(frame_opts, text="Exibir Texto", variable=var_line).pack(side="left")

        def confirmar():
            novo_tipo_label = combo_tipo.get()
            novos_dados = entry_dados.get().strip()
            nova_largura = combo_width.get()
            nova_altura = spin_height.get()
            nova_orient = combo_orient.get()
            
            cmd_char = 'E'
            if novo_tipo_label == 'Code 128': cmd_char = 'C'
            elif novo_tipo_label == 'UPC-A': cmd_char = 'U'
            
            p_line = 'Y' if var_line.get() else 'N'
            # Defaults for removed options
            p_above = 'N' 
            p_digit = 'Y' # Most use Y by default if not specified/changed
            
            cmd_params = f"{nova_orient},{nova_altura},{p_line},{p_above}"
            
            if cmd_char in ['C', 'U']:
                cmd_params += f",{p_digit}"
            if cmd_char == 'C':
                 cmd_params += ",A"
            
            # Position
            coords = self.canvas.coords(item)
            if coords:
                margin = getattr(self, 'canvas_margin', 10)
                orig_x = int(coords[0] - margin)
                orig_y = int(coords[1] - margin)
            else:
                 orig_x = params.get('x', 0)
                 orig_y = params.get('y', 0)

            novo_zpl = f"^FO{orig_x},{orig_y}^BY{nova_largura}^B{cmd_char}{cmd_params}^FD{novos_dados}^FS"
            
            self.atualizar_mini_objeto(item, novo_zpl)
            janela.destroy()
        
        tk.Button(janela, text="Confirmar", command=confirmar, bg="#dddddd", height=2).pack(fill="x", padx=20, pady=20)
        
        # Apply theme and font styling
        self.estilizar_modal(janela)
            

    
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
        
        # Apply theme and font styling
        self.estilizar_modal(janela)
    
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
        """Prepare and start label preview fetch (Main Thread specific)."""
        # --- Debounce Check ---
        import time
        current_time = time.time()
        last_time = getattr(self, '_last_fetch_time', 0)
        
        # Enforce 1.5 second cooldown between requests to avoid 429
        if current_time - last_time < 1.5:
            # Optional: could show a small toast or just ignore
            print("Request throttled (debounce)")
            return
            
        self._last_fetch_time = current_time
        # -----------------------

        # Gather all UI data in Main Thread
        zpl_full = self.entrada_texto.get("1.0", tk.END).strip()
        if not zpl_full: return
        
        # Auto-add wrappers if missing AND update the text field
        modified = False
        if not zpl_full.startswith("^XA"):
            zpl_full = "^XA\n" + zpl_full
            modified = True
        if not zpl_full.rstrip().endswith("^XZ"):
            zpl_full = zpl_full + "\n^XZ"
            modified = True
        
        # Update the text field if wrappers were added
        if modified:
            self.entrada_texto.delete("1.0", tk.END)
            self.entrada_texto.insert("1.0", zpl_full)
            self.aplicar_syntax_highlight()
        
        # Gather settings
        try:
            settings = {
                'dpi': self.combo_dpi.get(),
                'width': float(self.spin_width.get()),
                'height': float(self.spin_height.get()),
                'unit': self.combo_unit.get()
            }
        except ValueError:
            return

        # Snapshot of converted snippets safely
        convertidos = list(self.linhas_convertidas) if hasattr(self, 'linhas_convertidas') else []

        # Start background thread with snapshot data
        threading.Thread(target=self._executar_preview_labelary, args=(zpl_full, settings, convertidos), daemon=True).start()

    def _executar_preview_labelary(self, zpl, settings, convertidos_snapshot):
        """Fetch label preview from Labelary API (Background Worker)."""
        # Filter out converted snippets from ZPL
        if convertidos_snapshot:
            for snippet in convertidos_snapshot:
                # Normalize and replace - handle different whitespace
                if snippet:
                    snippet_clean = snippet.strip()
                    # Try exact match first
                    if snippet_clean in zpl:
                        zpl = zpl.replace(snippet_clean, "")
                    elif snippet in zpl:
                        zpl = zpl.replace(snippet, "")
                    else:
                        # Try line-by-line approach
                        for line in zpl.split('\n'):
                            if snippet_clean in line.strip():
                                zpl = zpl.replace(line, "")
                                break
        
        # Clean up empty lines that may result from removal
        zpl = '\n'.join(line for line in zpl.split('\n') if line.strip())
        
        try:
            dpi = settings['dpi']
            width = settings['width']
            height = settings['height']
            unit = settings['unit']
            
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
                
                # Update UI in main thread (pass image)
                self.root.after(0, self._atualizar_canvas_com_preview, image)
                
            elif response.status_code == 429:
                # Too Many Requests
                def show_limit():
                    messagebox.showwarning("Limite de Requisições", "Muitas requisições ao Labelary.\nAguarde alguns segundos e tente novamente.")
                self.root.after(0, show_limit)
                
            else:
                def show_err_gen():
                    print(f"Erro API Labelary: {response.status_code}")
                self.root.after(0, show_err_gen)
                
        except Exception as e:
            print(f"Erro no thread de preview: {e}")

    def _atualizar_canvas_com_preview(self, image):
        """Update canvas background with image (Main Thread) with auto-fit zoom."""
        # Keep original API image (full resolution)
        self._labelary_image_raw = image
        
        # Calculate auto-fit zoom if image is larger than canvas
        canvas_w = self.max_canvas_width - 2 * self.canvas_margin
        canvas_h = self.max_canvas_height - 2 * self.canvas_margin
        
        # Does the image need to be zoomed out to fit?
        if image.width > canvas_w or image.height > canvas_h:
            zoom_x = canvas_w / image.width
            zoom_y = canvas_h / image.height
            auto_fit_zoom = min(zoom_x, zoom_y)
            
            # Only reduce zoom if needed (never auto zoom-in)
            if auto_fit_zoom < self.zoom_level:
                self.zoom_level = max(self.zoom_min, auto_fit_zoom)
        
        # Apply current zoom level (this handles all rendering)
        self.aplicar_zoom()
        
        # Ensure correct Z-order
        if self.item_preview_fundo:
            self.canvas.tag_lower(self.item_preview_fundo)
        if self.retangulo:
            self.canvas.tag_raise(self.retangulo)
            self.canvas.tag_raise("mini_objeto")
            self.canvas.tag_raise("handle")





    def atualizar_visualizacao(self):
        """
        Legacy function - local rendering is deprecated.
        Now we use Labelary for all previews (main preview + mini-objects).
        This function is kept for compatibility but does minimal work.
        """
        # Just update the coordinate label if needed
        self.rotulo_coordenadas.config(text="")

    # ===== ZOOM FUNCTIONALITY =====
    
    def ao_scroll_zoom(self, evento):
        """Handle Ctrl+MouseWheel for zooming (always enabled)."""
        
        # Determine zoom direction
        if evento.delta > 0:
            fator = 1.15  # Zoom in
        else:
            fator = 0.85  # Zoom out
        
        novo_zoom = self.zoom_level * fator
        
        # Apply limits
        if novo_zoom < self.zoom_min:
            novo_zoom = self.zoom_min
        elif novo_zoom > self.zoom_max:
            novo_zoom = self.zoom_max
            
        if novo_zoom == self.zoom_level:
            return  # No change
        
        self.zoom_level = novo_zoom
        self.aplicar_zoom()
        
        # Show zoom level feedback
        zoom_pct = int(self.zoom_level * 100)
        self.rotulo_coordenadas.config(text=f"Zoom: {zoom_pct}%")
    
    def aplicar_zoom(self):
        """Apply current zoom level to all canvas elements visually."""
        # Resize background image
        if hasattr(self, '_labelary_image_raw') and self._labelary_image_raw:
            img = self._labelary_image_raw
            
            # Apply zoom level directly
            new_w = max(1, int(img.width * self.zoom_level))
            new_h = max(1, int(img.height * self.zoom_level))
            
            resized = img.resize((new_w, new_h), Image.LANCZOS)
            self.imagem_label_tk = ImageTk.PhotoImage(resized)
            
            if self.item_preview_fundo:
                self.canvas.itemconfig(self.item_preview_fundo, image=self.imagem_label_tk)
                self.canvas.coords(self.item_preview_fundo, self.canvas_margin, self.canvas_margin)
            else:
                # Create new background image
                self.item_preview_fundo = self.canvas.create_image(
                    self.canvas_margin, 
                    self.canvas_margin, 
                    image=self.imagem_label_tk, 
                    anchor=tk.NW, 
                    tags="preview_fundo"
                )
                self.canvas.tag_lower(self.item_preview_fundo)
        
        # Update viewport rectangle
        if self.retangulo and hasattr(self, '_labelary_image_raw') and self._labelary_image_raw:
            img = self._labelary_image_raw
            zoomed_w = int(img.width * self.zoom_level)
            zoomed_h = int(img.height * self.zoom_level)
            
            self.canvas.coords(self.retangulo,
                self.canvas_margin,
                self.canvas_margin,
                self.canvas_margin + zoomed_w,
                self.canvas_margin + zoomed_h
            )
        
        # Reposition all mini-objects based on zoom
        for item_id, obj_data in self.mini_objetos.items():
            # obj_data['x'] and ['y'] are original ZPL coords + margin
            orig_x = obj_data.get('x', self.canvas_margin)
            orig_y = obj_data.get('y', self.canvas_margin)
            barcode_offset_x = obj_data.get('barcode_offset_x', 0)
            
            # Convert to zoomed canvas position (with barcode offset compensation)
            compensated_x = orig_x - barcode_offset_x
            zoomed_x = self.canvas_margin + ((compensated_x - self.canvas_margin) * self.zoom_level)
            zoomed_y = self.canvas_margin + ((orig_y - self.canvas_margin) * self.zoom_level)
            
            self.canvas.coords(item_id, zoomed_x, zoomed_y)
            
            # Resize mini-object image based on zoom
            if 'image_raw' in obj_data and obj_data['image_raw']:
                raw_img = obj_data['image_raw']
                new_w = max(1, int(raw_img.width * self.zoom_level))
                new_h = max(1, int(raw_img.height * self.zoom_level))
                resized = raw_img.resize((new_w, new_h), Image.LANCZOS)
                new_photo = ImageTk.PhotoImage(resized)
                obj_data['photo'] = new_photo  # Update reference
                self.canvas.itemconfig(item_id, image=new_photo)
        
        # Redraw grid if active
        if self.grade_ativa.get():
            self.atualizar_grade()
    
    def canvas_para_zpl(self, canvas_x, canvas_y):
        """Convert canvas coordinates (with zoom) to ZPL coordinates."""
        zpl_x = (canvas_x - self.canvas_margin) / self.zoom_level
        zpl_y = (canvas_y - self.canvas_margin) / self.zoom_level
        return int(zpl_x), int(zpl_y)
    
    def zpl_para_canvas(self, zpl_x, zpl_y):
        """Convert ZPL coordinates to canvas coordinates (with zoom)."""
        canvas_x = self.canvas_margin + (zpl_x * self.zoom_level)
        canvas_y = self.canvas_margin + (zpl_y * self.zoom_level)
        return canvas_x, canvas_y

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

        # Show ZPL coordinates (accounting for zoom)
        zpl_x, zpl_y = self.canvas_para_zpl(x2, y2)
        self.rotulo_coordenadas.config(text=f"x: {zpl_x}, y: {zpl_y}")

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
            
            # Convert canvas coords (potentially zoomed) to ZPL coords
            novo_x, novo_y = self.canvas_para_zpl(x, y)
            
            # Compensate for barcode rendering offset (add it back to X)
            if item in self.mini_objetos:
                barcode_offset_x = self.mini_objetos[item].get('barcode_offset_x', 0)
                novo_x += barcode_offset_x
            
            novo_x = max(0, novo_x)
            novo_y = max(0, novo_y)
            
            # Get the original ZPL snippet for this element
            original_snippet = codigo_zpl[match_start:match_end]
            
            # Replace only the ^FO coordinates in this specific snippet
            new_snippet = re.sub(r'\^FO\d+,\d+', f'^FO{novo_x},{novo_y}', original_snippet, count=1)
            
            updates.append((match_start, match_end, new_snippet))
            
            # CRITICAL FIX: Update the internal ZPL record for mini-objects so future edits find the correct string
            if item in self.mini_objetos:
                self.mini_objetos[item]['zpl'] = new_snippet
                # Also update x, y params if present
                if 'params' in self.mini_objetos[item] and self.mini_objetos[item]['params']:
                    self.mini_objetos[item]['params']['x'] = novo_x
                    self.mini_objetos[item]['params']['y'] = novo_y
        
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


if __name__ == "__main__":
    root = tk.Tk()
    app = ZPLVisualizerApp(root)
    root.mainloop()
