import re

html_path = 'd:/ГО Талан UA/Talan UA Antigravity manager/Universal-AI-Orchestrator/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

cube_html = '''<div class="hero-cube-visual">
                    <div class="cube-container">
                        <div class="cube-face front"></div>
                        <div class="cube-face back"></div>
                        <div class="cube-face right"></div>
                        <div class="cube-face left"></div>
                        <div class="cube-face top"></div>
                        <div class="cube-face bottom"></div>
                    </div>
                    <img src="assets/hero_brain_glass.png" alt="AI Brain" class="cube-brain">
                </div>'''

pattern = re.compile(r'<div class="hero-graphic">.*?</div>', re.DOTALL)
content = pattern.sub(cube_html, content)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Replaced hero-graphic with hero-cube-visual.')
