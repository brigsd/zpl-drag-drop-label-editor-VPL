
import re

def test_regex():
    examples_text = [
        "^FO10,80,^A0B,25,35^FD78372/401^FS",
        "^FO210,80^A0B,25,35^FD78372/401^FS",
        "^FO410,80,^A0B,25,35^FD78372/401^Fs",
        "^FO610,80,^A0B,25,35^FD78372/401^FS",
        "^FO35,70^A0b,25,30^fh_^FDCont_82m 1 p_87.^Fs",
        "^FO65,25^A0b,20,20^fh_^FDContains 1 pc. | Contiene 1 pz.^Fs",
        "^FO100,100^A0b,15,15^fh_^FD01 Serrote | Pruning | Serrucho^Fs"
    ]

    examples_barcode = [
        "^fO135,0^by3,50,3.0^Beb,30,y,n^Fd7891117004479^FS",
        "^Fo335,0^By3,50,3.0^beb,30,Y,N^Fd7891117004479^FS",
        "^FO530,0^by3,50,3.0^BeB,30,Y,N^FD7891117004479^FS", 
        "^FO730,0^By3,50,3.0^beb,30,Y,N^FD7891117004479^FS"
    ]

    # Proposed Regex for Text
    # Handles:
    # - Case insensitive (?i)
    # - Spaces/commas between FO and A
    # - Params with flexible separation
    # - Any intermediate commands before FD
    regex_text = r'(?i)\^FO\s*(\d+)\s*,\s*(\d+).*?\^A[A-Z0-9@]+\s*,?\s*(\d+)\s*,\s*(\d+).*?\^FD(.*?)\^FS'

    print("--- Testing TEXT Regex ---")
    for ex in examples_text:
        match = re.search(regex_text, ex)
        if match:
            print(f"MATCH: {ex}")
            print(f"  Groups: {match.groups()}")
        else:
            print(f"FAIL:  {ex}")

    # Proposed Regex for Barcode
    # Handles:
    # - Case insensitive
    # - Flexible spacers
    # - Intermediate commands (^by...)
    regex_barcode = r'(?i)\^FO\s*(\d+)\s*,\s*(\d+).*?(\^B[CUE][^\^]*).*?\^FD(.*?)\^FS'

    print("\n--- Testing BARCODE Regex ---")
    for ex in examples_barcode:
        match = re.search(regex_barcode, ex)
        if match:
            print(f"MATCH: {ex}")
            print(f"  Groups: {match.groups()}")
        else:
            print(f"FAIL:  {ex}")

if __name__ == "__main__":
    test_regex()
