
import re

def test_multiline():
    zpl_example = """^XA
^PQ2
^FX Comandas RFID para serializar
^RU
^RB96,8,3,3,24,20,38^FS
^RFW,E^FD48,2,5,7891117,310602,#S^FS
^RLM,P,P,P,P,P^FS

^FX Comandos para Gerar o Datamatrix utilizando o EPC
^FO640,25
^BXN,9,200
^FN0^FS
^FN0^RFR,H^FS

^FX Referência
^FO30,33
^A0N,49
^FD77703422^FS

^FX Quantidade
^FO30,80
^A0N,40,40
^FD72 unidades^FS

^FX Código de barras
^FO30,120
^BY3^BCN,70,Y,N,N,
^FD37891117106020^FS

^XZ"""

    print("--- Testing Text Regex ---")
    # New regex from main.py
    pattern_text = r'(?is)\^FO\s*(\d+)\s*,\s*(\d+)(?:(?!\^FO).)*?\^A[A-Z0-9@]([NRIBnrib]?)\s*,?\s*(\d+)\s*,\s*(\d+).*?\^FD(.*?)\^FS'
    
    for match in re.finditer(pattern_text, zpl_example):
        print(f"MATCH: {match.group(0)!r}")
        print(f"  X: {match.group(1)}")
        print(f"  Y: {match.group(2)}")
        print(f"  Orient: {match.group(3)}")
        print(f"  H: {match.group(4)}")
        print(f"  W: {match.group(5)}")
        print(f"  Text: {match.group(6)!r}")
        print("-" * 20)

    print("\n--- Testing Barcode Regex ---")
    # New regex from main.py
    pattern_barcode = r'(?is)\^FO\s*(\d+)\s*,\s*(\d+)(?:(?!\^FO).)*?(\^B[CUE][^\^]*).*?\^FD(.*?)\^FS'
    
    for match in re.finditer(pattern_barcode, zpl_example):
        print(f"MATCH: {match.group(0)!r}")
        print(f"  X: {match.group(1)}")
        print(f"  Y: {match.group(2)}")
        print(f"  Cmd: {match.group(3)!r}")
        print(f"  Data: {match.group(4)!r}")
        print("-" * 20)

if __name__ == "__main__":
    test_multiline()
