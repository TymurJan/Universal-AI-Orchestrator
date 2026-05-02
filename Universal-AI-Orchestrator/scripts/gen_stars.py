import random
import urllib.parse
import math
import re

def generate_svg():
    # 1. STARS (Backdrop with distance-based density)
    stars = []
    angle_rad = math.radians(18) # Reverse of the core rotation to check distance
    for _ in range(1800): # Increased for full-screen coverage

        cx = random.uniform(0, 1000)
        cy = random.uniform(0, 1000)
        
        # Calculate distance to the diagonal line (rotated -18 deg)
        nx = 500 + (cx - 500) * math.cos(angle_rad) - (cy - 500) * math.sin(angle_rad)
        ny = 500 + (cx - 500) * math.sin(angle_rad) + (cy - 500) * math.cos(angle_rad)
        
        dist_to_line = abs(ny - 500)
        
        # 200% core / 18% periphery logic (added a bit more to edges to avoid "bald" spots)
        # Sharpest decay to concentrate almost everything on the trail line
        prob = 0.18 + 0.82 * math.exp(-(dist_to_line**2) / 12000)
        
        if random.random() > prob:
            continue




            
        r = round(random.uniform(0.3, 1.2), 1)
        op = round(random.uniform(0.4, 0.9), 2)
        fill = '#ffffff' if random.random() > 0.1 else '#6ee7b7'
        stars.append(f"<circle cx='{round(cx, 1)}' cy='{round(cy, 1)}' r='{r}' fill='{fill}' opacity='{op}'/>")


    # 1.1 TRAIL CLUSTER (Extremely dense, wide-reaching micro-stars)
    trail_stars = []
    for _ in range(16000): # High density to fill the outlined areas
        dist_along = random.gauss(0, 440) 
        dist_perp = random.gauss(0, 10)  # Wider gauss for better coverage
        
        length_mod = 0.6 + 0.4 * math.sin(dist_along / 60)
        
        # 2. Edge-thinning (Widened to fill the tails)
        edge_factor = math.exp(-(dist_perp**2) / 60) # Less sharp falloff to fill the edges
        
        if random.random() > (length_mod * edge_factor):
            continue
            
        scx = 500 + dist_along
        scy = 500 + dist_perp
        
        dist_from_center = math.sqrt(dist_along**2 + dist_perp**2)
        brightness_factor = math.exp(-dist_from_center / 1000) 
        
        r = round(random.uniform(0.1, 0.3) + (0.12 * brightness_factor), 2)
        op = round(min(1.0, random.uniform(0.3, 0.6) + (0.3 * brightness_factor)), 2)

        
        bloom_chance = 0.3 + (0.5 * brightness_factor)
        # Stronger bloom (blur) for the absolute center stars
        if brightness_factor > 0.85:
            filter_attr = "filter='url(#starBloomCenter)'"
        else:
            filter_attr = "filter='url(#starBloom)'" if random.random() < bloom_chance else ""
        
        trail_stars.append(f"<circle cx='{scx}' cy='{scy}' r='{r}' fill='#ffffff' opacity='{op}' {filter_attr}/>")




    # 1.2 HALO STARS (Dense scattering around the core edges)
    halo_stars = []
    for _ in range(8000):
        dist_along = random.gauss(0, 500)
        dist_perp = random.gauss(0, 80) # Wide spread
        
        # Density peaks at the core line
        prob = math.exp(-(dist_perp**2) / 3000)
        
        if random.random() > prob:
            continue
            
        scx = 500 + dist_along
        scy = 500 + dist_perp
        
        r = round(random.uniform(0.15, 0.45), 2)
        op = round(random.uniform(0.2, 0.5), 2)
        halo_stars.append(f"<circle cx='{round(scx, 1)}' cy='{round(scy, 1)}' r='{r}' fill='#ffffff' opacity='{op}'/>")

    # 2. MULTI-LAYERED NEBULA
    nebula_layers = [
        # 2.1 Emerald Tint (Base atmospheric layer)
        f"<ellipse cx='500' cy='500' rx='750' ry='35' fill='#059669' filter='url(#nebulaFilter)' opacity='0.08'/>",
        # 2.2 Wide Mist (Soft light)
        f"<ellipse cx='500' cy='500' rx='700' ry='28' fill='#ffffff' filter='url(#nebulaFilter)' opacity='0.1'/>",
        # 2.3 Neon Halo (More intense textured glow)
        f"<ellipse cx='500' cy='500' rx='520' ry='22' fill='#00f2ff' filter='url(#nebulaFilter)' opacity='0.5'/>",
        # 2.4 Neon Core (Ultra-intense textured highlight)
        f"<ellipse cx='500' cy='500' rx='320' ry='12' fill='#00f2ff' filter='url(#nebulaFilter)' opacity='0.8'/>"
    ]

    nebula_path = "".join(nebula_layers)







    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 1000' preserveAspectRatio='xMidYMid slice'>
        <defs>
            <filter id='nebulaFilter' x='-80%' y='-80%' width='260%' height='260%'>
                <feTurbulence type='fractalNoise' baseFrequency='0.008 0.03' numOctaves='3' seed='{random.randint(1, 999)}' result='velvetNoise'/>
                <feTurbulence type='fractalNoise' baseFrequency='0.04 0.09' numOctaves='5' seed='{random.randint(1, 999)}' result='detailNoise'/>
                <!-- Increased blur for softer edges -->
                <feGaussianBlur stdDeviation='25' in='SourceGraphic' result='blurBase'/>
                <feDisplacementMap in='blurBase' in2='velvetNoise' scale='90' xChannelSelector='R' yChannelSelector='G' result='displacedMist'/>
                <feComposite operator='in' in='detailNoise' in2='displacedMist' result='maskedMist'/>

                <feColorMatrix type='matrix' values='1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1.5 -0.4' />
            </filter>

            
            <filter id='starBloom' x='-100%' y='-100%' width='300%' height='300%'>
                <feGaussianBlur stdDeviation='0.5' result='blur'/>
                <feComposite operator='over' in='SourceGraphic' in2='blur'/>
            </filter>

            <filter id='starBloomCenter' x='-150%' y='-150%' width='400%' height='400%'>
                <feGaussianBlur stdDeviation='1.5' result='blur'/>
                <feComposite operator='over' in='SourceGraphic' in2='blur'/>
            </filter>

            <!-- SMOOTH BACKGROUND GLOW (No noise/orange peel) -->
            <filter id='smoothGlow' x='-100%' y='-100%' width='300%' height='300%'>
                <feGaussianBlur stdDeviation='80' result='blur'/>
            </filter>


            
            <filter id='grain'>
                <feTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/>
                <feColorMatrix type='matrix' values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.04 0'/>
            </filter>
        </defs>
        
        <rect width='1000' height='1000' fill='#000000'/>
        
        <!-- SMOOTH BACKGROUND GLOWS (No artifacts) -->
        <g id='bg-glows' transform='rotate(-18, 500, 500)'>
            <ellipse cx='500' cy='500' rx='900' ry='220' fill='#059669' filter='url(#smoothGlow)' opacity='0.08'/>
            <ellipse cx='500' cy='500' rx='800' ry='180' fill='#00f2ff' filter='url(#smoothGlow)' opacity='0.05'/>
        </g>
        
        <rect width='1000' height='1000' filter='url(#grain)' opacity='0.5'/>



        
        <!-- FULL SCREEN BACKDROP STARS -->
        <g id='stars-back'>{"".join(stars[:len(stars)//2])}</g>
        
        <!-- ZOOMED OUT GALACTIC CORE ONLY -->
        <g id='cosmic-scene' transform='translate(150, 150) scale(0.7)'>
            <g id='galactic-core' transform='rotate(-18, 500, 500)'>
                <g id='nebulae'>
                    {nebula_path}
                </g>
                <g id='halo-stars'>
                    {"".join(halo_stars)}
                </g>
                <g id='trail-stars'>
                    {"".join(trail_stars)}
                </g>
            </g>
        </g>
        
        <g id='stars-front'>{"".join(stars[len(stars)//2:])}</g>
        
    </svg>"""
    return urllib.parse.quote(svg)

svg_data_uri = f"data:image/svg+xml,{generate_svg()}"

css_block = f"""
.stars-layer {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url("{svg_data_uri}");
  background-size: 100% 100%;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 1;
  z-index: 1;

  animation: cosmicDrift 400s linear infinite;
}}

@keyframes cosmicDrift {{
  0% {{ transform: scale(1); }}
  50% {{ transform: scale(1.04); }}
  100% {{ transform: scale(1); }}
}}
"""

target_css = 'd:/ГО Талан UA/Talan UA Antigravity manager/Universal-AI-Orchestrator/css/style.css'

try:
    with open(target_css, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Try to replace both block and keyframes
    pattern_full = r'\.stars-layer\s*\{.*?\}\s*@keyframes\s+cosmicDrift\s*\{.*?\}'
    new_content = re.sub(pattern_full, css_block.strip(), content, flags=re.DOTALL)
    
    if new_content == content:
        # 2. Try to replace just the block
        pattern_block = r'\.stars-layer\s*\{.*?\}'
        new_content = re.sub(pattern_block, css_block.strip(), content, flags=re.DOTALL)
    
    if new_content == content:
        # 3. If still no match, append to the end
        new_content = content.rstrip() + "\n\n" + css_block.strip() + "\n"
        print("Appended .stars-layer block to the end of file.")
    else:
        print("Successfully updated existing .stars-layer block!")

    with open(target_css, 'w', encoding='utf-8') as f:
        f.write(new_content)

except Exception as e:
    print(f"Error: {e}")

