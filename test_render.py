import sys
import os
sys.path.append(os.path.abspath("src"))
from zpl_utils import render_scalable_text, log_debug

print("Testing render_scalable_text...")
try:
    img = render_scalable_text("Test", 50, 50)
    if img:
        print(f"Success! Image size: {img.size}")
        img.save("test_render_output.png")
    else:
        print("Failed: returned None")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
