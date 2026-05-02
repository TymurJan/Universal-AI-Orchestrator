import re

html_path = 'd:/ГО Талан UA/Talan UA Antigravity manager/Universal-AI-Orchestrator/landing/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_shield = r'<div class="feature-icon" style="color: var\(--step-3\);"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>'

new_shield = """<div class="feature-icon" style="color: var(--step-3);">
    <svg viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <!-- Outer Shield Outline -->
        <path d="M 12 28 C 12 28 20 23 20 15 V 6 L 12 3 L 4 6 V 15 C 4 23 12 28 12 28 Z" />
        
        <!-- 3D Inner Facets -->
        <path d="M 12 25.5 C 12 25.5 18 21 18 14.5 V 7.5 L 12 5.5 Z" fill="currentColor" stroke="none" opacity="0.3" />
        <path d="M 12 25.5 C 12 25.5 6 21 6 14.5 V 7.5 L 12 5.5 Z" fill="currentColor" stroke="none" opacity="0.1" />

        <!-- Circuits extending right -->
        <path d="M 18 9 L 23 9 L 23 6 L 27 6" />
        <circle cx="27" cy="6" r="1.5" fill="currentColor" stroke="none"/>
        
        <path d="M 20 13 L 26 13 L 26 10 L 30 10" />
        <circle cx="30" cy="10" r="1.5" fill="currentColor" stroke="none"/>
        
        <path d="M 20 16.5 L 28 16.5" />
        <circle cx="28" cy="16.5" r="1.5" fill="currentColor" stroke="none"/>

        <path d="M 18.5 20 L 22 20 L 22 23 L 26 23" />
        <circle cx="26" cy="23" r="1.5" fill="currentColor" stroke="none"/>

        <path d="M 15 23 L 19 23 L 19 26 L 24 26" />
        <circle cx="24" cy="26" r="1.5" fill="currentColor" stroke="none"/>
        
        <!-- Floating particles -->
        <circle cx="25" cy="18" r="0.8" fill="currentColor" stroke="none" />
        <circle cx="19" cy="28" r="0.8" fill="currentColor" stroke="none" />
    </svg>
</div>"""

if re.search(old_shield, content):
    content = re.sub(old_shield, new_shield, content)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Shield updated perfectly.")
else:
    print("Old shield not found in index.html.")
