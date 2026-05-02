import os

input_file = r'd:\ГО Талан UA\Talan UA Antigravity manager\Universal-AI-Orchestrator\index.html'
output_file = r'd:\ГО Талан UA\Talan UA Antigravity manager\Universal-AI-Orchestrator\index_clean.html'

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip().startswith('<style id="inlined-stars">'):
        new_lines.append('<style id="inlined-stars">.stars-layer { background: radial-gradient(circle at 50% 50%, #1b2735 0%, #090a0f 100%); }</style>\n')
    else:
        new_lines.append(line)

with open(output_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Done. Cleaned file saved to {output_file}")
