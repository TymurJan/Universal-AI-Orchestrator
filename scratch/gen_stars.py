import random

def generate_stars(count, width, height):
    stars = []
    for _ in range(count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        opacity = random.uniform(0.3, 1.0)
        stars.append(f"{x}px {y}px rgba(255, 255, 255, {opacity:.2f})")
    return ", ".join(stars)

# Small stars
s1 = generate_stars(200, 2000, 2000)
# Medium stars
s2 = generate_stars(100, 2000, 2000)

print("SMALL STARS:")
print(s1)
print("\nMEDIUM STARS:")
print(s2)
