import sys
import os
from PIL import Image

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from zpl_utils import render_bitmap_text

def test_render():
    text = "AB01"
    height = 30
    width = 30
    
    print(f"Rendering '{text}' with h={height}, w={width}")
    img = render_bitmap_text(text, height, width)
    
    if img:
        print(f"Image mode: {img.mode}")
        print(f"Size: {img.size}")
        # Save as PNG to verify visual correctness (PIL handles PNG headers correctly)
        img.save('debug_font_output.png')
        print("Saved debug_font_output.png")
        
        # Check corner pixel (should be background)
        bg_pixel = img.getpixel((0, 0))
        print(f"Top-left pixel value: {bg_pixel} (Should be 1 for White)")
        
        # Check a pixel that should be black (part of 'A')
        # 'A' first row 0x0E (00001110)
        # With scale 6x3.
        # Top-left of 'A' starts at x=0.
        # Row 0, bits 0,1 are 0. Bit 2,3,4 are 1.
        # My loop: bit 0 is MSB? No.
        # code: shift = (5-1) - bit_idx.
        # bit_idx 0 (Leftmost visually) -> shift 4.
        # 0x0E >> 4 is 0. So Pixel OFF (1=Background?).
        # Wait, in my code:
        # img = Image.new('1', size, 1) -> 1 is Background.
        # if pixel_on: img.putpixel(..., 0) -> 0 is Foreground (Black).
        
        # bit_idx 2 -> shift 2. (0x0E >> 2) & 1 -> 1. Pixel ON.
        # So x = 2 * scale_x = 12.
        # pixel (12, 0) should be 0 (Black).
        
        fg_pixel = img.getpixel((12, 0))
        print(f"Target foreground pixel (12,0) value: {fg_pixel} (Should be 0 for Black)")

if __name__ == "__main__":
    test_render()
