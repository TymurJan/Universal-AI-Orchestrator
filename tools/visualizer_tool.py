import argparse
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt

def get_report_dir():
    base = Path(__file__).parent.parent
    reports = base / "REPORTS" / "graphs"
    os.makedirs(reports, exist_ok=True)
    return reports

def setup_fonts():
    # Проста підтримка кирилиці (може потребувати налаштування на різних ОС)
    plt.rcParams['font.family'] = 'sans-serif'
    
def draw_pie(title: str, labels: list, values: list, output_name: str):
    setup_fonts()
    plt.figure(figsize=(8, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
    plt.title(title, fontweight='bold', pad=20)
    plt.axis('equal')
    
    out_path = get_report_dir() / f"{output_name}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Успішно згенеровано кругову діаграму: {out_path}")

def draw_bar(title: str, labels: list, values: list, output_name: str):
    setup_fonts()
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, values, color='skyblue')
    
    # Додаємо значення над стовпцями
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), va='bottom', ha='center')

    plt.title(title, fontweight='bold', pad=20)
    plt.ylabel('Значення')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    out_path = get_report_dir() / f"{output_name}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Успішно згенеровано стовпчасту діаграму: {out_path}")

def draw_gantt(title: str, tasks: list, output_name: str):
    setup_fonts()
    plt.figure(figsize=(10, 5))
    
    for i, task in enumerate(tasks):
        plt.barh(task["name"], task["duration"], left=task["start"], color='lightgreen', edgecolor='black')
        
    plt.title(title, fontweight='bold', pad=20)
    plt.xlabel('Вісь часу')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    
    out_path = get_report_dir() / f"{output_name}.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Успішно згенеровано таймлайн проєкту (Gantt): {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Data Visualizer Tool")
    parser.add_argument("type", choices=["pie", "bar", "gantt"], help="Тип графіку")
    parser.add_argument("data", type=str, help="JSON строка з даними")
    parser.add_argument("title", type=str, help="Заголовок графіка")
    parser.add_argument("output", type=str, help="Ім'я вихідного файлу (без .png)")
    
    args = parser.parse_args()
    
    try:
        data = json.loads(args.data)
        
        if args.type == "pie" or args.type == "bar":
            if "labels" not in data or "values" not in data:
                raise ValueError("JSON має містити 'labels' та 'values'.")
            
            if args.type == "pie":
                draw_pie(args.title, data["labels"], data["values"], args.output)
            else:
                draw_bar(args.title, data["labels"], data["values"], args.output)
                
        elif args.type == "gantt":
            if not isinstance(data, list):
                raise ValueError("JSON має бути масивом об'єктів [{'name', 'start', 'duration'}]")
            draw_gantt(args.title, data, args.output)
            
    except Exception as e:
        print(f"❌ Помилка генерації: {e}")
