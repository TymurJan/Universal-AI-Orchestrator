import re

file_path = r'd:\ГО Талан UA\Talan UA Antigravity manager\Universal-AI-Orchestrator\landing\css\style.css'

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# The clean, perfectly working background
replacement = """#space-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  background-color: #020617;
  overflow: hidden;
  pointer-events: none;
  background-image: 
    radial-gradient(ellipse at 80% 0%, rgba(19, 196, 95, 0.4) 0%, transparent 60%),
    radial-gradient(ellipse at 20% 100%, rgba(14, 165, 233, 0.3) 0%, transparent 60%),
    radial-gradient(ellipse at 50% 50%, rgba(16, 185, 129, 0.15) 0%, transparent 80%);
}

#space-background::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.2;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
  z-index: 10;
  pointer-events: none;
}

.stars-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(circle, #ffffff 1px, transparent 2px),
    radial-gradient(circle, rgba(255, 255, 255, 0.8) 2px, transparent 3px),
    radial-gradient(circle, #ffffff 1px, transparent 2px),
    radial-gradient(circle, rgba(16, 185, 129, 0.8) 2px, transparent 3px);
  background-size: 150px 150px, 250px 250px, 100px 100px, 300px 300px;
  background-position: 10px 20px, 50px 60px, 90px 10px, 30px 150px;
  animation: cosmicDrift 200s linear infinite;
  opacity: 0.9;
  z-index: 2;
}

@keyframes cosmicDrift {
  from { background-position: 10px 20px, 50px 60px, 90px 10px, 30px 150px; }
  to { background-position: -390px -380px, -350px -340px, -310px -390px, -370px -250px; }
}"""

# Use regex to replace everything from #space-background { to @keyframes auroraPulse { ... }
new_text = re.sub(r'#space-background \{.*?@keyframes auroraPulse \{.*?\n\}', replacement, text, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Background CSS perfectly restored!")
