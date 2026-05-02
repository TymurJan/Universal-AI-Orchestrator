import os

path = r'd:\ГО Талан UA\Talan UA Antigravity manager\Universal-AI-Orchestrator\css\style.css'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Цей блок ми видаляємо, бо він порожній і заважає основному
old_block = """.stars-layer {
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
old_block_normalized = old_block.replace('\r\n', '\n')

if old_block_normalized in content_normalized:
    # Замінюємо на порожній рядок
    new_content = content_normalized.replace(old_block_normalized, '')
    with open(path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(new_content)
    print("Duplicate empty .stars-layer removed.")
else:
    print("Could not find the duplicate block.")
