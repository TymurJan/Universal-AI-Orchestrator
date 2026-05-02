import re

html_path = 'd:/ГО Талан UA/Talan UA Antigravity manager/Universal-AI-Orchestrator/landing/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_shield = """<div class="feature-icon" style="color: var(--step-3);">
    <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <!-- Double-layered outline -->
        <path d="M 15 30 Q 25 32 35 23 Q 45 32 55 30 V 55 C 55 75 40 85 35 88 C 30 85 15 75 15 55 Z" stroke-width="3" />
        
        <!-- Inner bright left facet -->
        <path d="M 19 33 Q 27 34 33 28 V 83 C 29 80 19 72 19 55 Z" fill="currentColor" stroke="none" opacity="0.35" />
        
        <!-- Outer faint right facet -->
        <path d="M 37 28 Q 43 34 51 33 V 55 C 51 72 41 80 37 83 Z" fill="currentColor" stroke="none" opacity="0.1" />

        <!-- Technical circuitry extending to the right -->
        <g stroke-width="2">
            <!-- Path 1 (Top) -->
            <path d="M 53 32 L 63 32 L 63 20 L 73 20" />
            <circle cx="75" cy="20" r="2.5" fill="currentColor" stroke="none"/>
            
            <!-- Path 2 -->
            <path d="M 55 42 L 85 42" />
            <circle cx="88" cy="42" r="2.5" fill="currentColor" stroke="none"/>

            <!-- Path 3 (Short middle) -->
            <path d="M 55 54 L 68 54" />
            <circle cx="71" cy="54" r="2.5" fill="currentColor" stroke="none"/>

            <!-- Path 4 (Z-shape right-down-right) -->
            <path d="M 52 64 L 65 64 L 65 74 L 78 74" />
            <circle cx="81" cy="74" r="2.5" fill="currentColor" stroke="none"/>

            <!-- Path 5 (Bottom short) -->
            <path d="M 48 76 L 56 76" />
            <circle cx="59" cy="76" r="2.5" fill="currentColor" stroke="none"/>
            
            <!-- Top small floating node -->
            <path d="M 58 12 L 61 12" />
            <circle cx="64" cy="12" r="1.5" fill="currentColor" stroke="none"/>
        </g>

        <!-- Additional floating tech particles -->
        <circle cx="20" cy="18" r="1.5" fill="currentColor" stroke="none"/>
        <circle cx="45" cy="16" r="1.5" fill="currentColor" stroke="none"/>
        <circle cx="25" cy="85" r="2" fill="currentColor" stroke="none"/>
    </svg>
</div>
                <h4>Абсолютна Безпека (Human-in-the-loop)"""

# Regex replacing the whole feature-icon div up to the h4
pattern = re.compile(r'<div class="feature-icon"[^>]*>.*?</div>\s*<h4>Абсолютна Безпека \(Human-in-the-loop\)', re.DOTALL)
content = pattern.sub(new_shield, content)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Exact shield updated.")
