import os
import re

path = r'd:\ГО Талан UA\Talan UA Antigravity manager\Universal-AI-Orchestrator\index.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Видаляємо блок <style id="inlined-stars">...</style>
# Цей блок містить стару "мазню", яка перебиває ідеальні зірки з CSS
new_content = re.sub(r'<style id="inlined-stars">.*?</style>', '', content, flags=re.DOTALL)

if content != new_content:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Inlined stars removed from index.html. Now style.css will take over.")
else:
    print("Inlined stars block not found or already removed.")
