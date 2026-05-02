import random, math, re

star_colors = ['#ffffff', '#ffffff', '#e0f2fe', '#fef3c7', '#6ee7b7', '#0ea5e9']
trail_stars = []
for _ in range(16000):
    dist_along = random.gauss(0, 440)
    dist_perp = random.gauss(0, 10)
    angle = math.radians(-18)
    cx = 500 + dist_along * math.cos(angle) - dist_perp * math.sin(angle)
    cy = 500 + dist_along * math.sin(angle) + dist_perp * math.cos(angle)
    if not (0 <= cx <= 1000 and 0 <= cy <= 1000): continue
    prob = math.exp(-(dist_perp**2) / 60)
    if random.random() > prob: continue
    r = random.uniform(0.1, 0.4)
    op = random.uniform(0.3, 0.9) * prob
    trail_stars.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}" fill="{random.choice(star_colors)}" opacity="{op:.2f}"/>')

backdrop_stars = []
for _ in range(3500):
    cx = random.uniform(0, 1000)
    cy = random.uniform(0, 1000)
    nx = 500 + (cx - 500) * math.cos(math.radians(18)) + (cy - 500) * math.sin(math.radians(18))
    ny = 500 - (cx - 500) * math.sin(math.radians(18)) + (cy - 500) * math.cos(math.radians(18))
    dist_to_line = abs(ny - 500)
    prob = math.exp(-(dist_to_line**2) / 8000)
    if random.random() > prob: continue
    r = random.uniform(0.3, 1.0)
    op = random.uniform(0.1, 0.4) * prob
    backdrop_stars.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}" fill="{random.choice(star_colors)}" opacity="{op:.2f}"/>')

nebula_layers = [
    '<ellipse cx="500" cy="500" rx="900" ry="80" fill="#064e3b" filter="url(#nebulaFilter)" opacity="0.2"/>',
    '<ellipse cx="500" cy="500" rx="750" ry="50" fill="#059669" filter="url(#nebulaFilter)" opacity="0.3"/>',
    '<ellipse cx="500" cy="500" rx="600" ry="30" fill="#10b981" filter="url(#nebulaFilter)" opacity="0.6"/>',
    '<ellipse cx="500" cy="500" rx="400" ry="15" fill="#34d399" filter="url(#nebulaFilter)" opacity="0.8"/>'
]

svg = f'''<svg id="raw-stars-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid slice" style="width: 100%; height: 100%; position: absolute; top: 0; left: 0; pointer-events: none; z-index: 2;">
    <defs>
        <filter id="nebulaFilter" x="-50%" y="-50%" width="200%" height="200%">
            <feTurbulence type="fractalNoise" baseFrequency="0.015" numOctaves="4" seed="13" result="velvetNoise"/>
            <feGaussianBlur stdDeviation="25" in="SourceGraphic" result="blurBase"/>
            <feDisplacementMap in="blurBase" in2="velvetNoise" scale="90" xChannelSelector="R" yChannelSelector="G" result="displacedMist"/>
            <feComposite in="displacedMist" in2="velvetNoise" operator="arithmetic" k1="0.5" k2="0.5"/>
        </filter>
    </defs>
    <g id="cosmic-scene" transform="translate(200, 200) scale(0.6)">
        <g id="nebula-group" transform="rotate(-18, 500, 500)">{''.join(nebula_layers)}</g>
        <g id="stars-group">{''.join(backdrop_stars)}{''.join(trail_stars)}</g>
    </g>
</svg>'''

html_path = 'd:/ГО Талан UA/Talan UA Antigravity manager/Universal-AI-Orchestrator/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Clean old inlined style if it exists
html = re.sub(r'<style id="inlined-stars">.*?</style>', '', html, flags=re.DOTALL)

# Inject into .stars-layer. If it already has an svg inside, replace the whole div.
pattern = r'<div class="stars-layer">.*?</div>'
replacement = f'<div class="stars-layer">{svg}</div>'
if re.search(pattern, html, flags=re.DOTALL):
    html = re.sub(pattern, replacement, html, flags=re.DOTALL)
else:
    print("Could not find <div class='stars-layer'></div>")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("SUCCESS: Injected raw SVG into index.html")
