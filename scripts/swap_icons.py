import re

html_path = 'd:/ГО Талан UA/Talan UA Antigravity manager/Universal-AI-Orchestrator/landing/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

icons = {
    '🎯': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg></div>',
    '📱': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg></div>',
    '📄': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M16 13l-4 4-2-2"/><path d="M12 9v1"/></svg></div>',
    '⚖️': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><path d="M3 14h18"/><path d="M12 2v12"/><path d="M3 14v4a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-4"/><circle cx="6" cy="10" r="3"/><circle cx="18" cy="10" r="3"/></svg></div>',
    '🧠': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><path d="M9.5 2C10.88 2 12 3.12 12 4.5v15c0 1.38-1.12 2.5-2.5 2.5-1.55 0-2.83-1.12-2.96-2.58A3.001 3.001 0 0 1 3.1 14.5a2.5 2.5 0 0 1 .4-4.74 2.5 2.5 0 0 1 2-4.76C6.1 3.32 7.6 2 9.5 2Z"/><path d="M14.5 2c-1.38 0-2.5 1.12-2.5 2.5v15c0 1.38 1.12 2.5 2.5 2.5 1.55 0 2.83-1.12 2.96-2.58a3.001 3.001 0 0 0 3.44-4.82 2.5 2.5 0 0 0-.4-4.74 2.5 2.5 0 0 0-2-4.76 3 3 0 0 0-3.9-3.08Z"/></svg></div>',
    '📊': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="M18 9l-5 5-4-4-6 6"/></svg></div>',
    '🛡️': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>',
    '⚙️': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></div>',
    '💸': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div>',
    '📝': '<div class="feature-icon" style="color: var(--step-3);"><svg viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg></div>'
}

for emoji, replacement in icons.items():
    content = re.sub(rf'<div class="feature-icon[^>]*>{emoji}</div>', replacement, content)

# 2. Add Neural Sphere Graphic
neural_sphere = """
<div style="width: 100%; height: 350px; position: relative; border-radius: 1.5rem; overflow: hidden; display: flex; align-items: center; justify-content: center; box-shadow: 0 20px 50px rgba(0,0,0,0.5);">
    <!-- Glass Background Box (matches presentation) -->
    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.02); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); border-left: 1px solid rgba(255,255,255,0.3); border-top: 1px solid rgba(255,255,255,0.3);"></div>
    
    <!-- Edge Lighting Glow -->
    <div style="position: absolute; bottom: 0; right: 0; width: 100%; height: 100%; background: radial-gradient(circle at bottom right, rgba(16, 185, 129, 0.1) 0%, transparent 60%); pointer-events: none;"></div>
    
    <!-- Outer Connecting Nodes Sphere (Stars/Nodes) -->
    <svg style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1;" viewBox="0 0 400 350" fill="none">
        <circle cx="200" cy="175" r="140" stroke="rgba(255,255,255,0.05)" stroke-dasharray="4 8" stroke-width="1.5"/>
        <circle cx="200" cy="175" r="100" stroke="rgba(255,255,255,0.08)" stroke-width="0.5"/>
        <path d="M 60 175 Q 200 40 340 175" stroke="rgba(255,255,255,0.15)" stroke-width="1" fill="none"/>
        <path d="M 120 270 Q 200 175 300 80" stroke="rgba(255,255,255,0.1)" stroke-width="1" fill="none"/>
        <path d="M 90 100 Q 200 175 310 250" stroke="rgba(255,255,255,0.1)" stroke-width="1" fill="none"/>
        <!-- Star Nodes -->
        <circle cx="60" cy="175" r="3" fill="#fff" filter="drop-shadow(0 0 5px #fff)"/>
        <circle cx="340" cy="175" r="4" fill="var(--step-peak)" filter="drop-shadow(0 0 6px var(--step-peak))"/>
        <circle cx="200" cy="40" r="3" fill="#fff" filter="drop-shadow(0 0 5px #fff)"/>
        <circle cx="120" cy="270" r="3.5" fill="#fff" filter="drop-shadow(0 0 5px #fff)"/>
        <circle cx="300" cy="80" r="2.5" fill="#fff"/>
        <circle cx="90" cy="100" r="2.5" fill="var(--step-peak)"/>
        <circle cx="310" cy="250" r="3" fill="#fff"/>
        <circle cx="200" cy="315" r="2" fill="#fff"/>
        <circle cx="200" cy="75" r="2" fill="#fff"/>
    </svg>
    
    <!-- Central Brain/Network Drawing -->
    <svg style="position: relative; z-index: 2; width: 140px; height: 140px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="0.8" stroke-linecap="round" stroke-linejoin="round" color="rgba(255,255,255,0.9)">
        <!-- Elegant Brain Structure -->
        <path d="M9.5 2C10.88 2 12 3.12 12 4.5v15c0 1.38-1.12 2.5-2.5 2.5-1.55 0-2.83-1.12-2.96-2.58A3.001 3.001 0 0 1 3.1 14.5a2.5 2.5 0 0 1 .4-4.74 2.5 2.5 0 0 1 2-4.76C6.1 3.32 7.6 2 9.5 2Z" style="filter: drop-shadow(0 0 4px var(--step-peak));"></path>
        <path d="M14.5 2c-1.38 0-2.5 1.12-2.5 2.5v15c0 1.38 1.12 2.5 2.5 2.5 1.55 0 2.83-1.12 2.96-2.58a3.001 3.001 0 0 0 3.44-4.82 2.5 2.5 0 0 0-.4-4.74 2.5 2.5 0 0 0-2-4.76 3 3 0 0 0-3.9-3.08Z" style="filter: drop-shadow(0 0 4px var(--step-peak));"></path>
        <!-- Brainwaves/Synapses -->
        <path d="M7 12h2l1-3 1.5 6 1.5-3h1" stroke="var(--step-peak)" stroke-width="0.8" style="filter: drop-shadow(0 0 6px var(--step-peak));"></path>
        <path d="M14 12h-2l-1-3-1.5 6-1.5-3h-1" stroke="var(--step-peak)" stroke-width="0.8" style="filter: drop-shadow(0 0 6px var(--step-peak));"></path>
    </svg>
    
    <!-- Floating Data Text -->
    <div style="position: absolute; bottom: 20px; left: 20px; font-family: monospace; font-size: 0.75rem; color: var(--text-secondary); z-index: 2;">
        &gt; Resonance: 89%<br>
        &gt; Flow state: Active
    </div>
</div>
"""

# Replace the [Місце для фото Проєкту Ашрам] box
old_box = r'<div style="width: 100%; height: 350px; background: rgba\(255,255,255,0\.05\); border-radius: 1\.5rem; display: flex; align-items: center; justify-content: center; border: 1px dashed rgba\(255,255,255,0\.2\);">\s*<span style="color: var\(--text-secondary\); font-size: 0\.9rem;">\[Місце для фото Проєкту Ашрам\]</span>\s*</div>'
content = re.sub(old_box, neural_sphere, content)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Icons and neural sphere updated successfully!")
