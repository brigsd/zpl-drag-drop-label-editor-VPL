from PIL import Image, ImageOps, ImageFont, ImageDraw
import os
import datetime
import requests
import io
import re

def log_debug(message):
    try:
        with open("debug_zpl.txt", "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def calcular_dimensoes_texto(altura_fonte, largura_char, texto, dpi=300, orientacao='N'):
    """
    Calcula as dimensões em mm de um texto ZPL baseado nos parâmetros da fonte.
    
    :param altura_fonte: Altura da fonte em dots (do comando ^A0,h,w)
    :param largura_char: Largura do caractere em dots (do comando ^A0,h,w)
    :param texto: O texto a ser renderizado
    :param dpi: DPI da impressora (203 ou 300)
    :param orientacao: 'N', 'R', 'I', 'B' (Normal, 90, 180, 270)
    :return: Tupla (largura_mm, altura_mm)
    """
    # Converter dots para mm: mm = dots / dpi * 25.4
    # Largura total = largura_char * numero_de_caracteres
    num_chars = len(texto)
    largura_dots = largura_char * num_chars
    altura_dots = altura_fonte
    
    largura_mm = (largura_dots / dpi) * 25.4
    altura_mm = (altura_dots / dpi) * 25.4
    
    # Se orientação for R (90) ou B (270), inverte largura e altura da "caixa"
    if orientacao and orientacao.upper() in ['R', 'B']:
        largura_mm, altura_mm = altura_mm, largura_mm
    
    # Adicionar margem pequena para evitar corte
    largura_mm = max(1, largura_mm + 0.5)
    altura_mm = max(1, altura_mm + 0.5)
    
    return (round(largura_mm, 1), round(altura_mm, 1))


def fetch_labelary_element(zpl_content, dpmm=12, width_mm=20, height_mm=10, auto_crop=True):
    """
    Busca uma imagem de um elemento ZPL específico via API Labelary.
    O ZPL deve estar no formato ^XA...^XZ com o elemento em ^FO0,0.
    
    :param zpl_content: Código ZPL completo (^XA...^XZ)
    :param dpmm: Dots per mm (8=203dpi, 12=300dpi)
    :param width_mm: Largura da etiqueta em mm
    :param height_mm: Altura da etiqueta em mm
    :param auto_crop: Se True, recorta espaço em branco automaticamente
    :return: PIL.Image ou None se falhar
    """
    try:
        # Converter mm para inches para a URL
        w_in = width_mm / 25.4
        h_in = height_mm / 25.4
        
        url = f"http://api.labelary.com/v1/printers/{dpmm}dpmm/labels/{w_in:.3f}x{h_in:.3f}/0/"
        
        response = requests.post(url, files={'file': zpl_content}, stream=True, timeout=10)
        
        if response.status_code == 200:
            response.raw.decode_content = True
            image = Image.open(io.BytesIO(response.content))
            
            # Auto-crop: remove whitespace from the image
            if auto_crop and image.mode in ('RGB', 'RGBA', 'L'):
                # Convert to RGB if needed for getbbox
                if image.mode == 'RGBA':
                    # Create white background for alpha
                    bg = Image.new('RGB', image.size, (255, 255, 255))
                    bg.paste(image, mask=image.split()[3])
                    image = bg
                elif image.mode == 'L':
                    image = image.convert('RGB')
                
                # Invert to find non-white content (getbbox finds non-zero)
                inverted = ImageOps.invert(image)
                bbox = inverted.getbbox()
                
                if bbox:
                    # Add small padding (2 pixels)
                    padding = 2
                    left = max(0, bbox[0] - padding)
                    top = max(0, bbox[1] - padding)
                    right = min(image.width, bbox[2] + padding)
                    bottom = min(image.height, bbox[3] + padding)
                    image = image.crop((left, top, right, bottom))
            
            return image
        else:
            log_debug(f"Labelary API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        log_debug(f"fetch_labelary_element error: {e}")
        return None


def normalizar_zpl_para_mini_objeto(zpl_snippet):
    """
    Transforma um snippet ZPL em formato para mini-objeto.
    Remove ^FO existente e adiciona ^FO0,0, envolve com ^XA...^XZ.
    
    :param zpl_snippet: Snippet como "^FO128,17^A0,34,34^FDComprimento^FS"
    :return: ZPL completo como "^XA^FO0,0^A0,34,34^FDComprimento^FS^XZ"
    """
    # Remover ^FO existente
    zpl_sem_fo = re.sub(r'\^FO\d+,\d+', '', zpl_snippet)
    
    # Adicionar ^FO0,0 no início e envolver com ^XA...^XZ
    zpl_normalizado = f"^XA^FO0,0{zpl_sem_fo}^XZ"
    
    return zpl_normalizado


def extrair_parametros_texto(zpl_snippet):
    """
    Extrai parâmetros de um snippet de texto ZPL.
    
    :param zpl_snippet: Snippet como "^FO128,17^A0,34,34^FDComprimento^FS"
    :return: Dict com 'x', 'y', 'altura', 'largura', 'texto' ou None
    """
    # Updated regex - width is optional (^A0N,49 only has height)
    match = re.search(r'(?i)\^FO\s*(\d+)\s*,\s*(\d+).*?\^A[A-Z0-9@]([NRIBnrib]?)\s*,?\s*(\d+)(?:\s*,\s*(\d+))?.*?\^FD(.*?)\^FS', zpl_snippet)
    if match:
        altura = int(match.group(4))
        # Width defaults to height if not specified
        largura = int(match.group(5)) if match.group(5) else altura
        return {
            'x': int(match.group(1)),
            'y': int(match.group(2)),
            'orientacao': match.group(3) if match.group(3) else 'N',
            'altura': altura,
            'largura': largura,
            'texto': match.group(6)
        }
    return None


from bitmap_fonts import get_char_bitmap, FONT_A_WIDTH, FONT_A_HEIGHT

def redimensionar_imagem_codigo_barras(imagem, tamanho):
    """
    Redimensiona a imagem do código de barras com base no tamanho selecionado.
    :param imagem: Objeto PIL.Image
    :param tamanho: Fator de tamanho (float ou int)
    :return: Objeto PIL.Image redimensionado
    """
    largura_imagem = int(200 * tamanho)
    altura_imagem = int(200 * tamanho)
    imagem.thumbnail((largura_imagem, altura_imagem), Image.Resampling.LANCZOS)
    return imagem



def altera_8_para_0(codigo_zpl_imagem):
    """
    Substitui caracteres '8' por '0' em uma string ZPL (função legada encontrada no histórico).
    """
    codigo_zpl_imagem = list(codigo_zpl_imagem)

    for i in range(0, len(codigo_zpl_imagem), 1):
        if codigo_zpl_imagem[i] == '8':
            codigo_zpl_imagem[i] = '0'
    return ''.join(codigo_zpl_imagem)

def zpl_gfa_to_image(data_str, width_bytes):
    """
    Converte dados hexadecimais do comando ^GFA de volta para uma imagem PIL.
    Assumes compression type A (ASCII Hex) which is the default/what image_to_zpl produces.
    
    :param data_str: String hexadecimal dos dados da imagem.
    :param width_bytes: Número de bytes por linha.
    :return: Objeto PIL.Image
    """
    # Remove qualquer whitespace que possa existir
    hex_data = data_str.strip()
    
    # Converte hex para bytes
    # A string pode ser enorme, então iteramos
    try:
        # Tenta converter direto se for par
        if len(hex_data) % 2 != 0:
            hex_data += '0' # Padding se necessario
        
        binary_data = bytes.fromhex(hex_data)
        
        width_pixels = width_bytes * 8
        if width_pixels == 0: return None
        
        height_pixels = len(binary_data) // width_bytes
        
        # Cria a imagem a partir dos bytes (modo '1' = 1-bit pixels, black and white, stored with one pixel per byte)
        # O PIL frombytes com modo '1' espera 1 pixel por byte? Não, modo '1' usually packs bits.
        # Mas 'frombytes' geralmente le bytes brutos.
        # Vamos testar criando com '1' e passando os bytes packed.
        
        image = Image.frombytes('1', (width_pixels, height_pixels), binary_data)
        
        # O ZPL usa 0 para branco e 1 para preto? Ou o contrario?
        # image_to_zpl: '1' if image.getpixel((x, y)) == 0 else '0'
        # Se pixel é 0 (preto), vira '1'. Se pixel é >0 (branco/outro), vira '0'.
        # Então '1' no ZPL = Preto.
        # No PIL mode '1', 0 é preto e 1 é branco normalmente?
        # Vamos inverter para garantir. Se ZPL '1' (preto) virou bit 1, e PIL exibe bit 1 como branco...
        # ImageOps.invert so funciona em imagens 'L' ou 'RGB' as vezes.
        # Na duvida, retornamos a imagem e testamos. O image_to_zpl inverte logica explicitamente.
        
        # Correcao: Image.frombytes com '1' le bits packed.
        # Se 1=Preto no ZPL, e PIL interpreta 1=Branco, precisaremos inverter.
        # Mas vamos assumir padrao primeiro.
        
        return image.convert('L').point(lambda x: 0 if x == 255 else 255) # Invert: 1(from ZPL Black) -> 255(White) -> Invert to 0(Black)
        # Wait, frombytes '1': 1 is usually White in PIL logic for matching palette?
        # Actually usually: 1-bit pixel. 0 or 1.
        # convert('L') maps 0->0, 1->255.
        # If ZPL data has 1 for Black content.
        # We want that 1 to become 0 (Black).
        # We want 0 (Background) to become 255 (White).
        # So: 1 -> 255 -> Invert -> 0. Correct.
        #     0 -> 0 -> Invert -> 255. Correct.
        
    except Exception as e:
        print(f"Erro ao converter GFA para imagem: {e}")
        return None

def render_bitmap_text(text, height, width):
    """
    Renders text using the custom bitmap font engine.
    Scales the bitmap to match the requested height/width.
    Returns RGBA image with transparent background.
    """
    if not text: return None
    
    # Base font is FONT_A (5x9)
    # Calculate scale factor
    scale_y = max(1, height // FONT_A_HEIGHT)
    scale_x = max(1, width // FONT_A_WIDTH)
    
    # Character spacing (1 pixel base, scaled)
    char_spacing = max(1, scale_x // 2)

    # Total size (including spacing between chars)
    char_width_with_spacing = (FONT_A_WIDTH * scale_x) + char_spacing
    total_width = len(text) * char_width_with_spacing - char_spacing  # No trailing space
    total_height = FONT_A_HEIGHT * scale_y # Multi-line not supported yet
    
    # Create blank image with TRANSPARENT background (RGBA)
    # (0, 0, 0, 0) = fully transparent
    img = Image.new('RGBA', (total_width, total_height), (255, 255, 255, 0))
    
    cursor_x = 0
    
    for char in text:
        bitmap = get_char_bitmap(char)
        if not bitmap: continue
        
        # Draw char
        # Bitmap is list of bytes, each byte is a row
        for row_idx, byte in enumerate(bitmap):
            # Iterate bits (width 5)
            for bit_idx in range(FONT_A_WIDTH):
                # Check if bit is set. (1 = Pixel ON = Black)
                shift = (FONT_A_WIDTH - 1) - bit_idx
                pixel_on = (byte >> shift) & 1
                
                if pixel_on:
                    # Draw scaled pixel block
                    x_start = cursor_x + (bit_idx * scale_x)
                    y_start = (row_idx * scale_y)
                    
                    for dx in range(scale_x):
                        for dy in range(scale_y):
                             img.putpixel((x_start + dx, y_start + dy), (0, 0, 0, 255))  # Black, fully opaque
        
        cursor_x += char_width_with_spacing
        
    return img

def render_scalable_text(text, height, width):
    """
    Renders text using TrueType font (Arial) with independent scaling for width and height.
    mimicking ZPL ^A0 behavior.
    """
    if not text: return None
    
    # Prioritize Arial Narrow Bold (match for CG Triumvirate Bold Condensed)
    font_candidates = [
        "C:/Windows/Fonts/ARIALNB.TTF",
        "C:/Windows/Fonts/ARIALN.TTF",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "arialnb.ttf",
        "arialn.ttf",
        "arialbd.ttf",
        "arial.ttf"
    ]
    
    font = None
    font_size = height
    
    for font_path in font_candidates:
        try:
            if os.path.exists(font_path) or not os.path.dirname(font_path): # Check abs path or allow local/generic load
                log_debug(f"Trying font: {font_path} at size {font_size}")
                font = ImageFont.truetype(font_path, font_size)
                break
        except Exception as e:
            log_debug(f"Failed to load {font_path}: {e}")
            continue

    if not font:
        try:
           log_debug("Falling back to LiberationSans-Regular")
           font = ImageFont.truetype("LiberationSans-Regular.ttf", height)
        except IOError:
           log_debug("Falling back to default font")
           font = ImageFont.load_default()

    log_debug(f"Font loaded: {font}")

    # Determine text geometry
    try:
        bbox = font.getbbox(text) # left, top, right, bottom
        text_width = bbox[2]
        if hasattr(font, 'getlength'):
             advance = int(font.getlength(text))
             text_width = max(text_width, advance)
    except AttributeError:
        # Fallback for older Pillow
        text_width, _ = font.getsize(text)

    if text_width == 0: return None

    # Calculate final width for scaling
    final_width = 0
    if width > 0:
        # Calculate scale factor based on reference char '0'
        try:
           # Try to get reference width
           ref_char = "0"
           if hasattr(font, 'getlength'):
               ref_w = font.getlength(ref_char)
           else:
               ref_w = font.getbbox(ref_char)[2]
        except:
           try:
              ref_w, _ = font.getsize("0")
           except:
              ref_w = 0
           
        if ref_w > 0:
            scale_x = width / ref_w
            final_width = int(text_width * scale_x)
            log_debug(f"Scaling: ZPL_W={width}, Ref_W={ref_w}, Scale={scale_x:.2f}, Orig_W={text_width} -> Final_W={final_width}")
        else:
             final_width = int(text_width)
    else:
         final_width = int(text_width)

    # Create image of exact requested height (font size) and natural width
    # We do NOT crop vertically to preserve baseline/alignment
    img_temp = Image.new('RGBA', (text_width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img_temp)
    
    # Draw text at (0,0) - this generally aligns top-left of font cell to (0,0)
    # The font's internal vertical metrics determine where glyphs sit (e.g. baseline)
    draw.text((0, 0), text, font=font, fill="black")
    
    # Resize ONLY horizontally if needed
    final_width = max(1, final_width)
    final_height = height # Keep height fixed to preserve aspect/alignment
    
    # Only resize if dimensions differ significantly to avoid blur
    if final_width != text_width:
        img_final = img_temp.resize((final_width, final_height), Image.Resampling.LANCZOS)
    else:
        img_final = img_temp
    
    return img_final
