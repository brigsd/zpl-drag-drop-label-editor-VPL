import sys
import os
import re
from PIL import Image

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from zpl_utils import image_to_zpl, zpl_gfa_to_image

def test_cycle():
    # Create a simple image
    img = Image.new('1', (16, 16), color=1) # White
    # Draw a black box
    for x in range(4, 12):
        for y in range(4, 12):
            img.putpixel((x, y), 0)
    
    img.save('test_input.png')
    
    # Convert to ZPL
    zpl = image_to_zpl('test_input.png')
    print(f"Generated ZPL: {zpl}")
    
    # Parse ZPL
    match = re.search(r'\^FO(\d+),(\d+)\^GFA,?(\d+),(\d+),(\d+),([A-Fa-f0-9\s]+)\^FS', zpl)
    if not match:
        print("Failed to match generated ZPL with regex")
        return
        
    x, y, total_bytes, total_bytes_displayed, width_bytes, data = match.groups()
    print(f"Parsed: width_bytes={width_bytes}, data_len={len(data)}")
    
    # Convert back to Image
    recovered_img = zpl_gfa_to_image(data, int(width_bytes))
    
    if recovered_img:
        print("Successfully recovered image")
        recovered_img.save('test_output.png')
        print("Saved test_output.png")
    else:
        print("Failed to recover image")

if __name__ == "__main__":
    test_cycle()
