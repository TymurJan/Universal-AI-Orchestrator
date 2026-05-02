"""
Removes the dark teal background from security_shield_exact.png,
making it a transparent PNG so it sits naturally on any card background.
"""
from PIL import Image
import numpy as np

input_path = "security_shield_exact.png"
output_path = "security_shield_transparent.png"

img = Image.open(input_path).convert("RGBA")
data = np.array(img, dtype=np.float32)

r, g, b, a = data[..., 0], data[..., 1], data[..., 2], data[..., 3]

# The background is a dark teal: low brightness, slightly blue-green tint
# We detect pixels that are "dark" (brightness < 40/255) and make them transparent
brightness = (r + g + b) / 3.0

# Create an alpha mask: dark pixels become transparent
# Use a soft threshold for smooth edges (avoid harsh cutoffs)
threshold = 55.0
mask = np.clip((brightness - threshold) / 40.0, 0.0, 1.0)  # 0=transparent, 1=opaque

data[..., 3] = mask * 255.0

result = Image.fromarray(data.astype(np.uint8), "RGBA")
result.save(output_path)
print(f"Saved transparent PNG to: {output_path}")
