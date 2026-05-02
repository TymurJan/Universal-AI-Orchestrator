"""
Remove background from brain_resonance_exact.png using rembg AI model.
Also crops the bottom 28%.
"""
from rembg import remove
from PIL import Image
import io

input_path = "brain_resonance_exact.png"
output_path = "brain_resonance_final.png"

# Open image
with open(input_path, "rb") as f:
    input_data = f.read()

print("Removing background with AI (rembg)...")
output_data = remove(input_data)
print("Done!")

# Load result and crop bottom 28%
img = Image.open(io.BytesIO(output_data)).convert("RGBA")
w, h = img.size
print(f"Size: {w}x{h}")

crop_bottom = int(h * 0.72)
img_cropped = img.crop((0, 0, w, crop_bottom))
img_cropped.save(output_path)
print(f"Saved -> {output_path} ({w}x{crop_bottom})")
