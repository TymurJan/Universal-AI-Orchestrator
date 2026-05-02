import re

html_path = 'd:/ГО Талан UA/Talan UA Antigravity manager/Universal-AI-Orchestrator/landing/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Precise SVG reconstruction of the provided image
exact_graphic = """
<div style="width: 100%; height: 400px; position: relative; display: flex; align-items: center; justify-content: center; overflow: visible;">
    <!-- Background Glows (matches the image's "Aurora" feel) -->
    <div style="position: absolute; top: 20%; left: 0%; width: 60%; height: 60%; background: radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, transparent 70%); filter: blur(40px); pointer-events: none;"></div>
    <div style="position: absolute; top: 10%; right: 10%; width: 40%; height: 80%; background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 60%); filter: blur(50px); pointer-events: none;"></div>
    
    <svg viewBox="0 0 500 300" style="width: 100%; height: 100%; z-index: 2;" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:rgba(255,255,255,0.1);stop-opacity:1" />
                <stop offset="50%" style="stop-color:rgba(16,185,129,0.8);stop-opacity:1" />
                <stop offset="100%" style="stop-color:rgba(255,255,255,0.1);stop-opacity:1" />
            </linearGradient>
            <filter id="glow">
                <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>

        <!-- Left: Brain Model (Complex paths) -->
        <g opacity="0.8" transform="translate(50, 40) scale(0.9)">
            <!-- Outer Brain Form -->
            <path d="M100,50 C140,50 170,80 170,120 C170,160 140,190 100,190 C60,190 30,160 30,120 C30,80 60,50 100,50 Z" 
                  fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1" />
            
            <!-- Brain Gyri/Folds (Hand-drawn paths for organic look) -->
            <path d="M100,60 Q120,65 130,80 Q140,100 130,130 Q110,150 90,145 Q70,140 65,110 Q60,80 90,65 Z" fill="rgba(255,255,255,0.05)" />
            <path d="M135,90 Q150,110 145,140 Q130,165 110,170" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="0.8" />
            <path d="M65,95 Q50,115 55,145 Q70,170 95,175" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="0.8" />
            
            <!-- Resonance Waves through Brain -->
            <path d="M10,120 Q50,80 90,120 T170,120 T250,120" stroke="url(#waveGrad)" stroke-width="1.5" fill="none" class="wave-anim" />
            <path d="M10,130 Q50,170 90,130 T170,130 T250,130" stroke="rgba(16,185,129,0.4)" stroke-width="1" fill="none" opacity="0.5" />
            
            <!-- Vertical pulse lines (Matches EEG in image) -->
            <path d="M80,80 V160 M90,70 V170 M100,60 V180 M110,70 V170 M120,80 V160" stroke="rgba(255,255,255,0.1)" stroke-width="0.5" />
        </g>

        <!-- Right: Human Profile Face -->
        <g transform="translate(320, 30) scale(0.85)">
            <!-- Face Outline -->
            <path d="M80,20 C110,20 140,50 140,100 C140,120 135,145 130,160 L125,230 L90,230 C80,230 70,210 65,190 C60,170 60,140 55,120 C50,100 45,90 45,80 C45,45 60,20 80,20 Z" 
                  fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="1.2" />
            
            <!-- Glowing Brain Content in Head -->
            <g filter="url(#glow)">
                <circle cx="95" cy="70" r="25" fill="rgba(16,185,129,0.2)" />
                <circle cx="95" cy="70" r="1" fill="#fff" />
                <circle cx="85" cy="60" r="1.5" fill="#fff" opacity="0.8" />
                <circle cx="105" cy="80" r="1" fill="#fff" opacity="0.6" />
                <circle cx="100" cy="55" r="1.2" fill="var(--step-peak)" />
                <circle cx="80" cy="85" r="1" fill="#fff" />
                
                <!-- Connection lines (Neural network) -->
                <path d="M85,60 L95,70 L105,80 M100,55 L95,70 L80,85" stroke="rgba(255,255,255,0.3)" stroke-width="0.3" />
            </g>
        </g>

        <!-- Dynamic Peak Wave (Bottom Left) -->
        <path d="M50,250 Q80,250 100,210 Q120,250 150,250 T250,250" stroke="rgba(16,185,129,0.8)" stroke-width="2" fill="none" filter="url(#glow)" />
        <circle cx="100" cy="210" r="4" fill="#fff" filter="url(#glow)" />
        <path d="M30,260 Q70,260 100,230 Q130,260 170,260" stroke="rgba(16,185,129,0.3)" stroke-width="1" fill="none" />

        <!-- Text Labels (Matches Image exactly) -->
        <g font-family="Inter, sans-serif" font-size="14" fill="rgba(255,255,255,0.8)">
            <text x="310" y="200" data-i18n="mission.resonance">89% Resonance</text>
            <text x="310" y="225" data-i18n="mission.flow">Active Flow state</text>
            <text x="310" y="250" data-i18n="mission.alignment">Organic Alignment</text>
        </g>
    </svg>
</div>
"""

# Replace the previous neural sphere/box
box_pattern = re.compile(r'<div style="width: 100%; height: 350px; position: relative; border-radius: 1\.5rem; overflow: hidden; display: flex; align-items: center; justify-content: center; box-shadow: 0 20px 50px rgba\(0,0,0,0\.5\);">.*?</div>', re.DOTALL)
content = box_pattern.sub(exact_graphic, content)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Exact image reproduction applied without frame.")
