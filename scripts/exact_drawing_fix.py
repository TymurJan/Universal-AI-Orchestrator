import re

html_path = 'd:/ГО Талан UA/Talan UA Antigravity manager/Universal-AI-Orchestrator/landing/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Exact Brain & Profile paths (high fidelity)
exact_drawing = """
<div style="width: 100%; height: 400px; position: relative; display: flex; align-items: center; justify-content: center; overflow: visible;">
    <!-- Background Ambient Glow -->
    <div style="position: absolute; top: 25%; left: 5%; width: 50%; height: 50%; background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%); filter: blur(40px);"></div>
    
    <svg viewBox="0 0 500 300" style="width: 100%; height: 100%; z-index: 2;" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <filter id="gentleGlow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>

        <!-- Left Component: Detailed Brain Structure -->
        <g transform="translate(60, 40) scale(1.05)" style="filter: url(#gentleGlow);">
            <!-- Base silhouette (very faint) -->
            <path d="M100,50 C140,50 175,75 175,120 C175,165 140,195 100,195 C60,195 25,165 25,120 C25,75 60,50 100,50 Z" 
                  fill="rgba(255,255,255,0.02)" stroke="none" />
            
            <!-- Structural Lobe Lines (Fine & Technical) -->
            <g stroke="rgba(255,255,255,0.4)" stroke-width="0.8" fill="none">
                <!-- Frontal -->
                <path d="M100,50 C130,50 150,70 155,100 Q158,130 145,160 Q130,190 100,195" />
                <!-- Temporal/Occipital -->
                <path d="M100,50 C70,50 50,70 45,100 Q42,130 55,160 Q70,190 100,195" />
                <!-- Mid fissure -->
                <path d="M100,50 L100,195" stroke-dasharray="2 4" stroke-opacity="0.3" />
                
                <!-- Internal Gyri / Organic folds -->
                <path d="M70,80 Q90,75 110,85 T140,110 T130,160" stroke-opacity="0.5" />
                <path d="M130,100 Q110,110 90,105 T60,140" stroke-opacity="0.4" />
                <path d="M100,70 Q120,65 140,85 Q160,110 150,140" stroke-dasharray="1 1" />
                <path d="M100,180 Q80,175 60,155 Q45,130 55,100" stroke-dasharray="1 1" />
                
                <!-- Central Synapse Pulse (Subtle wavy line) -->
                <path d="M30,122 L45,122 L50,110 L55,135 L60,118 L140,118 L145,105 L150,130 L155,115 L170,115" stroke="var(--step-peak)" stroke-width="1.2" />
            </g>
        </g>

        <!-- Right Component: Side Profile Profile -->
        <g transform="translate(320, 20) scale(0.95)">
            <!-- Face Outline (Delicate as per image) -->
            <path d="M80,20 C110,20 145,55 145,110 C145,135 140,165 130,185 L120,250 L95,250 C85,250 78,235 75,220 C72,205 72,175 65,150 C58,125 50,110 50,90 C50,55 65,20 80,20 Z" 
                  fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1" />
            
            <!-- Neural Activity Cluster inside Head -->
            <g style="filter: url(#gentleGlow);">
                <!-- Ambient glow in head -->
                <circle cx="100" cy="75" r="30" fill="rgba(16,185,129,0.15)" />
                <!-- Neural Nodes -->
                <circle cx="95" cy="65" r="1.2" fill="#fff" />
                <circle cx="110" cy="75" r="1" fill="#fff" opacity="0.8" />
                <circle cx="90" cy="85" r="1.5" fill="var(--step-peak)" />
                <circle cx="105" cy="95" r="0.8" fill="#fff" />
                <circle cx="120" cy="60" r="1" fill="#fff" opacity="0.6" />
                <circle cx="85" cy="55" r="1.2" fill="#fff" />
                
                <!-- Connections (Spider-web style) -->
                <g stroke="rgba(255,255,255,0.2)" stroke-width="0.3">
                    <line x1="95" y1="65" x2="110" y2="75" />
                    <line x1="110" y1="75" x2="105" y2="95" />
                    <line x1="105" y1="95" x2="90" y2="85" />
                    <line x1="90" y1="85" x2="95" y2="65" />
                    <line x1="100" y1="75" x2="120" y2="60" />
                    <line x1="95" y1="65" x2="85" y2="55" />
                </g>
            </g>
        </g>
    </svg>
</div>
"""

# Replace the graphic block in Mission section
pattern = re.compile(r'<div style="width: 100%; height: 400px; position: relative; display: flex; align-items: center; justify-content: center; overflow: visible;">.*?</div>', re.DOTALL)
content = pattern.sub(exact_drawing, content)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Brain and Profile graphic updated (frameless, no text, no waves).")
