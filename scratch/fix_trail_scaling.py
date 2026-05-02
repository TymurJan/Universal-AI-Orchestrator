import os

path = r'd:\ГО Талан UA\Talan UA Antigravity manager\Universal-AI-Orchestrator\css\style.css'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Текст, який ми шукаємо (той, що я щойно додав)
old_stars_block = """.stars-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  pointer-events: none;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  background-repeat: no-repeat;
}"""

# Новий текст з акцентом на правильне масштабування шлейфу
new_stars_block = """.stars-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1; /* Знижуємо z-index, щоб шлейф був під контентом, але видимим */
  pointer-events: none;
  background-size: cover;
  background-position: center center;
  background-attachment: fixed;
  background-repeat: no-repeat;
  image-rendering: high-quality;
}"""

content_normalized = content.replace('\r\n', '\n')
old_stars_normalized = old_stars_block.replace('\r\n', '\n')
new_stars_normalized = new_stars_block.replace('\r\n', '\n')

if old_stars_normalized in content_normalized:
    new_content = content_normalized.replace(old_stars_normalized, new_stars_normalized)
    with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(new_content)
    print("Stars scaling fix applied.")
else:
    print("Error: Could not find the stars-layer block to fix.")
