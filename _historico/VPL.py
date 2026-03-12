import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import PIL
from PIL import Image, ImageTk
import re
import barcode
from barcode.writer import ImageWriter
from tkinter import simpledialog


# Definição de variaveis globais
tamanhos_codigo_barras = {}

# Variável global para verificar se a janela foi redimensionada
janela_redimensionada = False

# Adiciona uma variável global para armazenar o estado do botão "Aplicar"
botao_aplicar_habilitado = False

# Adiciona uma variável global para definir a lista a seguir
elementos_movidos = []


def redimensionar_imagem_codigo_barras(imagem, tamanho):
    # Redimensiona a imagem do código de barras com base no tamanho selecionado
    largura_imagem = 200 * tamanho
    altura_imagem = 200 * tamanho
    imagem.thumbnail((largura_imagem, altura_imagem))
    return imagem


# Atualiza a visualização da etiqueta com base no código ZPL inserido pelo usuário
def atualizar_visualizacao():
    global deslocamento_x, deslocamento_y

    # Obtém o código ZPL do campo de texto
    codigo_zpl = entrada_texto.get("1.0", tk.END)

    # Analisa o código ZPL para extrair informações sobre os elementos
    elementos = []
    for match in re.finditer(r'\^FO(\d+),(\d+)\^A[^\^]+,(\d+),(\d+)(\^FH)?\^FD([^\^]+)\^FS', codigo_zpl):
        x, y, altura_fonte, largura_fonte, _, texto = match.groups()
        elementos.append(('texto', int(x), int(y), int(altura_fonte), int(largura_fonte), texto))
    for match in re.finditer(r'\^FO(\d+),(\d+)\^BY[^\^]+\^B[^\^]+\^FD([^\^]+)\^FS', codigo_zpl):
        x, y, dados = match.groups()
        elementos.append(('codigo_barras', int(x), int(y), dados))

    # Limpa o canvas e o dicionário de códigos de barras
    for item in canvas.find_all():
        if canvas.type(item) in ("text", "image"):
            canvas.delete(item)
    canvas.dados_codigo_barras = {}

    # Cria objetos gráficos interativos para representar os elementos
    for elemento in elementos:
        if elemento[0] == 'texto':
            _, x, y, altura_fonte, largura_fonte, texto = elemento
            fator_escala = 0.79 # Fator de escala para o tamanho da fonte
            item = canvas.create_text(x + deslocamento_x, y + deslocamento_y, text=texto, anchor=tk.NW,
                                      font=("Calibri Bold", int((altura_fonte + 1) * fator_escala)))
            canvas.tag_bind(item, "<ButtonPress-1>", ao_pressionar_elemento)
            canvas.tag_bind(item, "<B1-Motion>", ao_arrastar_elemento)
        elif elemento[0] == 'codigo_barras':
            _, x, y, dados = elemento
            escritor = ImageWriter()
            escritor.dpi = 300
            escritor.altura_modulo = 5.0
            upca = barcode.get('upca', dados, writer=escritor)
            imagem = upca.render()
            foto = ImageTk.PhotoImage(imagem)
            item = canvas.create_image(x + deslocamento_x, y + deslocamento_y, image=foto, anchor=tk.NW)
            canvas.dados_codigo_barras[item] = dados
            tamanho = tamanhos_codigo_barras.get(item, 1)
            imagem = redimensionar_imagem_codigo_barras(imagem, float(tamanho))
            foto = ImageTk.PhotoImage(imagem)
            canvas.itemconfig(item, image=foto)
            canvas.tag_bind(item, "<ButtonPress-1>", ao_pressionar_elemento)
            canvas.tag_bind(item, "<B1-Motion>", ao_arrastar_elemento)

            # Adiciona a imagem ao dicionário de imagens do canvas
            if not hasattr(canvas, '_imagens'):
                canvas._imagens = {}
            canvas._imagens[item] = foto

            # Armazena uma referência ao objeto PhotoImage para evitar que ele seja coletado pelo coletor de lixo
            if not hasattr(canvas, '_fotos'):
                canvas._fotos = []
            canvas._fotos.append(foto)

# Chamada quando o usuário pressiona um elemento no canvas
def ao_pressionar_elemento(evento):
    # Armazena a posição atual do elemento
    canvas.elemento_atual = canvas.find_withtag("current")
    canvas.x_atual = evento.x
    canvas.y_atual = evento.y

# Chamada quando o usuário arrasta um elemento no canvas
def ao_arrastar_elemento(evento):
    rx1, ry1, rx2, ry2 = canvas.coords(retangulo)
    valor_snap = int(snap.get())
    x1, y1 = canvas.coords(canvas.elemento_atual)
    x2 = evento.x
    y2 = evento.y
    x2 = round((x2 + 1) / valor_snap) * valor_snap
    y2 = round((y2 + 1) / valor_snap) * valor_snap
    if trava_eixo_x.get():
        x2 = x1
    if trava_eixo_y.get():
        y2 = y1
    tipo_elemento = canvas.type(canvas.elemento_atual)
    if tipo_elemento == "text":
        bbox = canvas.bbox(canvas.elemento_atual)
        largura_elemento = bbox[2] - bbox[0]
        altura_elemento = bbox[3] - bbox[1]
    elif tipo_elemento == "image":
        bbox = canvas.bbox(canvas.elemento_atual)
        largura_elemento = bbox[2] - bbox[0]
        altura_elemento = bbox[3] - bbox[1]
    else:
        largura_elemento = 0
        altura_elemento = 0
    if x2 < 0:
        x2 = 0
    if y2 < 0:
        y2 = 0
    if x2 < rx1:
        x2 = rx1
    if y2 < ry1:
        y2 = ry1
    if x2 + largura_elemento > rx2:
        x2 = rx2 - largura_elemento
    if y2 + altura_elemento > ry2:
        y2 = ry2 - altura_elemento
    canvas.coords(canvas.elemento_atual, x2 - deslocamento_x, y2 - deslocamento_y)
    # Calcula as coordenadas do elemento em relação ao retângulo
    x_relativo = x2 - rx1
    y_relativo = y2 - ry1

    rotulo_coordenadas.config(text=f"x: {x_relativo + 10}, y: {y_relativo + 10}")

    # Atualiza o estado do botão "Aplicar"
    global botao_aplicar_habilitado
    botao_aplicar_habilitado = True
    botao_aplicar.config(state=tk.NORMAL)

    # Adiciona o elemento à lista de elementos movidos
    if canvas.elemento_atual not in elementos_movidos:
        elementos_movidos.append(canvas.elemento_atual)


# Aplica as mudanças feitas pelo usuário no canvas ao código ZPL
def aplicar_mudancas():
    # Obtém o código ZPL do campo de texto
    codigo_zpl = entrada_texto.get("1.0", tk.END)

    for item in canvas.find_all():
        if canvas.type(item) == "text":
            x, y = canvas.coords(item)
            texto = re.escape(canvas.itemcget(item, "text"))
            novo_x = max(0, int(x) - deslocamento_x )
            novo_y = max(0, int(y) - deslocamento_y )
            codigo_zpl = re.sub(rf'(\^FO)\d+,\d+(\^A[^\^]+\^FD{texto}\^FS)', rf'\g<1>{novo_x},{novo_y}\g<2>',
                                codigo_zpl)
        elif canvas.type(item) == "image":
            x, y = canvas.coords(item)
            dados = re.escape(canvas.dados_codigo_barras[item])
            novo_x = max(0, int(x) - deslocamento_x)
            novo_y = max(0, int(y) - deslocamento_y)
            codigo_zpl = re.sub(rf'(\^FO)\d+,\d+(\^[BY][^\^]+\^[B][^\^]+\^FD{dados}\^FS)',
                                rf'\g<1>{novo_x},{novo_y}\g<2>', codigo_zpl)

    # Atualiza o campo de texto com o novo código ZPL
    entrada_texto.delete("1.0", tk.END)
    entrada_texto.insert(tk.END, codigo_zpl)

    # Atualiza o estado do botão "Aplicar"
    global botao_aplicar_habilitado
    botao_aplicar_habilitado = False
    botao_aplicar.config(state=tk.DISABLED)

# Chamada quando a janela principal é redimensionada
def ao_redimensionar(evento):
    global janela_redimensionada
    # Verifica se o evento está sendo gerado pela janela principal
    if evento.widget == janela_principal:
        # Atualiza as coordenadas do retângulo
        nova_largura = evento.width - 30
        nova_altura = evento.height * 0.47  # Calcula a nova altura com base na altura atual da janela
        if not janela_redimensionada:
            canvas.coords(retangulo, deslocamento_x + 10, deslocamento_y + 10, nova_largura + 10, nova_altura + 10)
            janela_redimensionada = True
        else:
            canvas.coords(retangulo, deslocamento_x + 10, deslocamento_y + 10, nova_largura + 10, nova_altura + 10)


# Cria a janela principal
janela_principal = tk.Tk()
janela_principal.after(1,
                       atualizar_visualizacao)  # Chamar a função atualizar_vizualizacao para definir tamanhominimox=0 e tamanhominimoy=0
janela_principal.title("Visualizador de Etiquetas ZPL")

# Altera a largura e a altura da janela principal
janela_principal.geometry("800x800")

# Configura as linhas e colunas para se expandirem ou encolherem proporcionalmente à janela
janela_principal.rowconfigure(0, weight=1)
janela_principal.rowconfigure(6, weight=1)
janela_principal.columnconfigure(0, weight=1, minsize=100)
janela_principal.columnconfigure(1, weight=1, minsize=100)

# Cria o campo de texto para entrada de código ZPL
entrada_texto = tk.Text(janela_principal, height=9)
entrada_texto.grid(row=0, column=0, columnspan=2, padx=20, sticky="nsew")

# Cria um frame para conter os botões
frame_botoes = tk.Frame(janela_principal)
frame_botoes.grid(row=1, column=0, columnspan=2, pady=15)

# Cria o botão para atualizar a visualização da etiqueta
botao_atualizar = tk.Button(frame_botoes, text="Atualizar preview", command=atualizar_visualizacao)
botao_atualizar.pack(side=tk.LEFT, padx=5)
botao_atualizar.config(font=("fonte", 12, "bold"))

# Cria o botão para aplicar as mudanças no código ZPL
botao_aplicar = tk.Button(frame_botoes, text="Aplicar posição", command=aplicar_mudancas)
botao_aplicar.pack(side=tk.LEFT, padx=5)
botao_aplicar.config(font=("fonte", 12, "bold"))


# Cria uma janela secundária para permitir que o usuário crie um novo elemento (texto ou código de barras)
def criar_elemento():
    # Cria a janela secundária
    janela_criar_elemento = tk.Toplevel(janela_principal)
    janela_criar_elemento.title("Criar elemento")

    # Define a geometria da janela (largura x altura)
    janela_criar_elemento.geometry("400x300")  # Defina o tamanho desejado

    # Cria o rótulo para o tipo de elemento
    rotulo_tipo_elemento = tk.Label(janela_criar_elemento, text="Tipo de elemento:")
    rotulo_tipo_elemento.pack(side=tk.TOP, padx=5, pady=5)

    # Cria o elemento de seleção para escolher o tipo de elemento
    tipo_elemento = ttk.Combobox(janela_criar_elemento, values=["Texto", "Código de barras"])
    tipo_elemento.pack(side=tk.TOP, padx=5, pady=5)

    # Cria o rótulo para o tamanho da fonte
    rotulo_tamanho_fonte = tk.Label(janela_criar_elemento, text="Tamanho da fonte:")

    # Cria o elemento de seleção para escolher o tamanho da fonte
    tamanho_fonte = ttk.Combobox(janela_criar_elemento, values=[16, 18, 20, 30, 40, 50, 60])
    tamanho_fonte.current(2)

    # Cria o rótulo para o tamanho do código de barras
    rotulo_tamanho_codigo_barras = tk.Label(janela_criar_elemento, text="Tamanho do código de barras:")

    # Cria o elemento de seleção para escolher o tamanho do código de barras
    tamanho_codigo_barras = ttk.Combobox(janela_criar_elemento, values=[1, 2, 3, 4, 5])
    tamanho_codigo_barras.current(2)

    # Cria o rótulo para o formato do código de barras
    rotulo_formato_codigo_barras = tk.Label(janela_criar_elemento, text="Formato do código de barras:")

    # Cria o elemento de seleção para escolher o formato do código de barras
    formato_codigo_barras = ttk.Combobox(janela_criar_elemento, values=["UPC-A", "EAN-13"])
    formato_codigo_barras.current(0)

    # Cria o rótulo para o conteúdo do elemento
    rotulo_conteudo_elemento = tk.Label(janela_criar_elemento, text="Conteúdo do elemento:")
    rotulo_conteudo_elemento.pack(side=tk.TOP, padx=5, pady=5)

    # Cria o campo de entrada para o conteúdo do elemento
    conteudo_elemento = tk.Entry(janela_criar_elemento, width=50)
    conteudo_elemento.pack(side=tk.TOP, padx=5, pady=5)

    def ao_selecionar_tipo_elemento(evento):
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

        # Verifica se todos os campos obrigatórios foram preenchidos
        if (tipo_elemento.get() == "Texto" and conteudo_elemento.get() and tamanho_fonte.get()) or (
                tipo_elemento.get() == "Código de barras" and conteudo_elemento.get() and tamanho_codigo_barras.get()):
            botao_adicionar_elemento.config(state=tk.NORMAL)
        else:
            botao_adicionar_elemento.config(state=tk.DISABLED)

    tipo_elemento.bind("<<ComboboxSelected>>", ao_selecionar_tipo_elemento)

    # Vincula os eventos de alteração dos campos obrigatórios à função ao_selecionar_tipo_elemento
    conteudo_elemento.bind("<KeyRelease>", ao_selecionar_tipo_elemento)
    tamanho_fonte.bind("<<ComboboxSelected>>", ao_selecionar_tipo_elemento)
    tamanho_codigo_barras.bind("<<ComboboxSelected>>", ao_selecionar_tipo_elemento)
    formato_codigo_barras.bind("<<ComboboxSelected>>", ao_selecionar_tipo_elemento)

    def adicionar_elemento():
        global imagem_codigo_barras
        if tipo_elemento.get() == "Texto":
            tamanho = tamanho_fonte.get()
            texto = conteudo_elemento.get()
            codigo_zpl = f"^FO200,200^A0,{tamanho},{tamanho}^FD{texto}^FS"
            entrada_texto.insert(tk.END, codigo_zpl)
        elif tipo_elemento.get() == "Código de barras":
            tamanho = tamanho_codigo_barras.get()
            codigo = conteudo_elemento.get()
            formato = formato_codigo_barras.get()

            # Gera a imagem do código de barras
            if formato == "UPC-A":
                BARCODE = barcode.get_barcode_class('upca')
                barcode_instance = BARCODE(codigo, writer=ImageWriter())
                imagem_codigo_barras = barcode_instance.render()
            elif formato == "EAN-13":
                BARCODE = barcode.get_barcode_class('ean13')
                barcode_instance = BARCODE(codigo, writer=ImageWriter())
                imagem_codigo_barras = barcode_instance.render()

            # Redimensiona a imagem do código de barras com base no tamanho selecionado
            imagem_codigo_barras = redimensionar_imagem_codigo_barras(imagem_codigo_barras, float(tamanho))

            # Converte a imagem em um objeto PhotoImage
            foto = ImageTk.PhotoImage(imagem_codigo_barras)

            # Cria um elemento de imagem no canvas
            elemento_imagem = canvas.create_image(150, 150, image=foto, anchor=tk.NW)
            canvas.foto = foto  # Armazena a referência para evitar coleta de lixo

            # Vincula os eventos de arrastar ao elemento de imagem
            canvas.tag_bind(elemento_imagem, "<ButtonPress-1>", ao_pressionar_elemento)
            canvas.tag_bind(elemento_imagem, "<B1-Motion>", arrastar_imagem)

            # Atualiza o dicionário de códigos de barras do canvas
            canvas.dados_codigo_barras[elemento_imagem] = codigo
            tamanhos_codigo_barras[elemento_imagem] = tamanho

            # Gera o código ZPL para o elemento de código de barras
            if formato == "UPC-A":
                codigo_zpl = f"^FO200,200^BY{tamanho}^BUN,80^FD{codigo}^FS"
            elif formato == "EAN-13":
                codigo_zpl = f"^FO200,200^BY{tamanho}^BEN,80^FD{codigo}^FS"

            # Insere o código ZPL no campo de texto
            entrada_texto.insert(tk.END, codigo_zpl)

        janela_criar_elemento.destroy()
        atualizar_visualizacao()

    # Cria o botão para adicionar o elemento
    botao_adicionar_elemento = tk.Button(janela_criar_elemento, text="Adicionar elemento", command=adicionar_elemento)
    botao_adicionar_elemento.config(state=tk.DISABLED)
    botao_adicionar_elemento.pack(side=tk.BOTTOM, padx=5, pady=5)


# Converte uma imagem em um código ZPL que pode ser usado para imprimir a imagem em uma impressora Zebra
def image_to_zpl(image_path, offset_x=0, offset_y=0):
    image = Image.open(image_path).convert('1')
    # Desloca os pixels da imagem
    if offset_x != 0 or offset_y != 0:
        image = image.transform(image.size, Image.AFFINE, (1, 0, offset_x, 0, 1, offset_y))
    width, height = image.size

    # Verifica se a largura da imagem é um múltiplo de 8
    if width % 8 != 0:
        # Reduz as proporções da imagem até que a largura seja um múltiplo de 8
        while width % 8 != 0:
            width -= 1
            height -= 1
        image = image.resize((width, height))

    # Cria uma lista vazia chamada `data` para armazenar os dados da imagem
    data = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append('1' if image.getpixel((x, y)) == 0 else '0')
        data.append(''.join(row))
    hex_data = ''.join(['{:X}'.format(int(x, 2)) for x in data])
    zpl = "^FO200,200^GFA,{},{},{},{}^FS".format(len(hex_data), len(hex_data) // 2, width // 8, hex_data)
    return zpl


# Define a função `altera_8_para_0` que recebe como parâmetro um código ZPL
def altera_8_para_0(codigo_zpl_imagem):
    codigo_zpl_imagem = list(codigo_zpl_imagem)

    for i in range(0, len(codigo_zpl_imagem), 1):
        if codigo_zpl_imagem[i] == '8':
            codigo_zpl_imagem[i] = '0'
    return ''.join(codigo_zpl_imagem)


zpl_code_imagem = image_to_zpl('barcode.png', offset_x=-1, offset_y=0)


# Permite que o usuário arraste imagens no canvas
def arrastar_imagem(evento):
    # Verifica se o elemento que está sendo arrastado é uma imagem
    if canvas.type(canvas.elemento_atual) == "image":
        # Obtém as coordenadas atuais do elemento de imagem
        x, y = canvas.coords(canvas.elemento_atual)

        # Calcula as novas coordenadas do elemento de imagem
        x += evento.x - canvas.x_atual
        y += evento.y - canvas.y_atual

        # Verifica se as travas de x e y estão ativadas
        if trava_eixo_x.get():
            x = canvas.coords(canvas.elemento_atual)[0]
        if trava_eixo_y.get():
            y = canvas.coords(canvas.elemento_atual)[1]

        # Obtém as coordenadas do retângulo de visualização
        rx1, ry1, rx2, ry2 = canvas.coords(retangulo)

        # Obtém a largura e a altura da imagem
        largura_imagem = canvas.bbox(canvas.elemento_atual)[2] - canvas.bbox(canvas.elemento_atual)[0]
        altura_imagem = canvas.bbox(canvas.elemento_atual)[3] - canvas.bbox(canvas.elemento_atual)[1]

        # Verifica se a imagem ultrapassou os limites do retângulo de visualização
        if x < rx1:
            x = rx1
        if y < ry1:
            y = ry1
        if x + largura_imagem > rx2:
            x = rx2 - largura_imagem
        if y + altura_imagem > ry2:
            y = ry2 - altura_imagem

        # Atualiza as coordenadas do elemento de imagem
        canvas.coords(canvas.elemento_atual, x, y)

        # Atualiza as coordenadas do mouse
        canvas.x_atual = evento.x
        canvas.y_atual = evento.y

        # Atualiza os valores de X e Y no código ZPL
        codigo_zpl = entrada_texto.get("1.0", tk.END)
        novo_codigo_zpl = re.sub(r'(\^FO)\d+,\d+(\^GFA[^\^]+\^FS)', rf'\g<1>{int(x)},{int(y)}\g<2>'
                                 , codigo_zpl)
        entrada_texto.delete("1.0", tk.END)
        entrada_texto.insert(tk.END, novo_codigo_zpl)


# Permite ao usuário selecionar uma imagem para importar
def importar_imagem():
    file_path = filedialog.askopenfilename(filetypes=[("Imagens PNG", "*.png")])
    if file_path:
        try:
            # Abre a imagem usando a biblioteca PIL
            imagem = Image.open(file_path)

            # Redimensiona a imagem para o tamanho desejado
            largura_desejada = 200
            altura_desejada = 200
            imagem.thumbnail((largura_desejada, altura_desejada))

            # Converte a imagem para o formato PhotoImage
            foto = ImageTk.PhotoImage(imagem)

            # Cria um elemento de imagem no canvas
            elemento_imagem = canvas.create_image(150, 150, image=foto, anchor=tk.NW)
            canvas.foto = foto  # Armazena a referência para evitar coleta de lixo

            # Vincula os eventos de arrastar ao elemento de imagem
            canvas.tag_bind(elemento_imagem, "<ButtonPress-1>", ao_pressionar_elemento)
            canvas.tag_bind(elemento_imagem, "<B1-Motion>", arrastar_imagem)

            # Converte a imagem em código ZPL
            zpl_code_imagem = image_to_zpl(file_path)

            # Insere o código ZPL no campo de texto
            entrada_texto.insert(tk.END, zpl_code_imagem)

        except Exception as e:
            # Lida com erros ao abrir a imagem
            print("Erro ao abrir a imagem:", e)


# Cria o botão para criar um novo elemento
botao_criar_elemento = tk.Button(frame_botoes, text="Criar elemento", command=criar_elemento)
botao_criar_elemento.pack(side=tk.LEFT, padx=5)
botao_criar_elemento.config(font=("fonte", 12, "bold"))

# Cria o botão para importar uma imagem
botao_importar_imagem = tk.Button(frame_botoes, text="Importar Imagem", command=importar_imagem)
botao_importar_imagem.pack(side=tk.LEFT, padx=5)
botao_importar_imagem.config(font=("fonte", 12, "bold"))

# Cria um frame para conter os botões de trava
frame_travas = tk.Frame(janela_principal)
frame_travas.grid(row=2, column=0, columnspan=2)

# Cria as variáveis para armazenar o estado das travas nos eixos X e Y
trava_eixo_x = tk.BooleanVar()
trava_eixo_y = tk.BooleanVar()

# Cria os botões para habilitar as travas nos eixos X e Y
botao_trava_x = tk.Checkbutton(frame_travas, text="Travar eixo X", variable=trava_eixo_x)
botao_trava_x.pack(side=tk.LEFT, padx=5)
botao_trava_x.config(font=("fonte", 10, "bold"))

botao_trava_y = tk.Checkbutton(frame_travas, text="Travar eixo Y", variable=trava_eixo_y)
botao_trava_y.pack(side=tk.LEFT, padx=5)
botao_trava_y.config(font=("fonte", 10, "bold"))

# Cria um frame para conter o rótulo e o elemento de seleção
frame_elemento_selecao = tk.Frame(janela_principal)
frame_elemento_selecao.grid(row=3, column=0, columnspan=2)

# Cria o rótulo para o elemento de seleção
rotulo_elemento_selecao = tk.Label(frame_elemento_selecao, text="Ajuste de posição:")
rotulo_elemento_selecao.pack(side=tk.LEFT, padx=5)
rotulo_elemento_selecao.config(font=("fonte", 10, "bold"), foreground="darkblue")

# Cria o elemento de seleção para escolher o valor pelo qual as coordenadas dos elementos devem ser incrementadas
snap = ttk.Combobox(frame_elemento_selecao, values=[1, 5, 10, 50])
snap.current(0)
snap.pack(side=tk.LEFT, padx=5)

# Cria o campo informativo para exibir as coordenadas atuais do elemento
rotulo_coordenadas = tk.Label(janela_principal, text="")
rotulo_coordenadas.grid(row=4, column=0, columnspan=2, padx=5)

# Cria o canvas para exibir a imagem da etiqueta
canvas = tk.Canvas(janela_principal)
canvas.grid(row=6, column=0, columnspan=2, padx=5, sticky="nsew")
canvas.dados_codigo_barras = {}

# Adiciona um retângulo para delimitar a área de visualização da etiqueta
deslocamento_x = 0
deslocamento_y = 0
retangulo = canvas.create_rectangle(deslocamento_x + 10, deslocamento_y + 10, canvas.winfo_width() + deslocamento_x + 10
                                    , canvas.winfo_height() + deslocamento_y + 10)

# Vincula o evento de redimensionamento da janela à função ao_redimensionar
janela_principal.bind("<Configure>", ao_redimensionar)

# Inicia o loop principal da janela
janela_principal.mainloop()