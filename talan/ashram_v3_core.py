import sys
import os

# Додаємо корінь проекту до шляху пошуку модулів
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from talan.cad_core import TalanCADCore
from talan.architecture_standards import ASHRAM_ROOMS, FURNITURE, RULES, CONSTRUCTION

class AshramV3Architect:
    def __init__(self, filename="ashram_v3_model.dxf"):
        self.cad = TalanCADCore(filename, base_dir="_DROPZONE/OUT")
        # Базові габарити будівлі (орієнтовно 12м х 24м для розміщення всіх зон)
        self.width = 12000
        self.length = 24000
        self.wall_ext = CONSTRUCTION["WALL_EXTERIOR"]
        self.wall_int = CONSTRUCTION["WALL_PARTITION"]

    def build_foundation_axes(self):
        """Створення сітки осей для всієї будівлі."""
        x_axes = [0, 4000, 8000, 12000, 16000, 20000, 24000]
        y_axes = [0, 4000, 8000, 12000]
        self.cad.add_axis_grid(x_axes, y_axes)

    def build_floor_0(self):
        """Нижній поверх: Хол, Кухня, Тераса, Баня."""
        f = 0
        # Зовнішні стіни Level 0
        self.cad.add_rect((0, 0), (self.length, self.width), layer="WALLS", floor=f)
        
        # Головний хол (Центральна частина, двосвітла)
        # Координати: x=8000 до 16000, y=0 до 12000
        self.cad.add_text("ГОЛОВНИЙ ХОЛ (ДВОСВІТНИЙ)", (10000, 6000), floor=f)
        self.cad.add_furniture((11000, 1000), "FIREPLACE", floor=f)
        
        # Тераса (вздовж фасаду)
        t_depth = 4000
        self.cad.add_rect((0, -t_depth), (self.length, 0), layer="WALLS", floor=f)
        self.cad.add_text("ТЕРАСА (ГЛИБИНА 4М)", (10000, -2000), floor=f)
        # Криниця на терасі
        self.cad.msp.add_circle((4000, -2000), 600, dxfattribs={'layer': f'F{f}_WALLS'})
        self.cad.add_text("КРИНИЦЯ", (3500, -2500), floor=f)

        # Банний блок (L-крило)
        # Спрощено: окрема зона зліва
        self.cad.add_rect((-6000, 0), (0, 8000), layer="WALLS", floor=f)
        self.cad.add_text("БАННИЙ КОМПЛЕКС", (-5000, 4000), floor=f)
        self.cad.add_text("РЕАБІЛІТАЦІЙНИЙ БАСЕЙН", (-5000, 1000), floor=f)

        # Кухня (20м2) - приблизно 4х5м
        self.cad.add_rect((0, 8000), (5000, self.width), layer="WALLS", floor=f)
        self.cad.add_text("КУХНЯ", (1000, 10000), floor=f)

    def build_floor_1(self):
        """Верхній поверх: Вхід, Житлові кімнати, Адмін."""
        f = 1
        # Зовнішні стіни Level 1
        self.cad.add_rect((0, 0), (self.length, self.width), layer="WALLS", floor=f)
        
        # Галерея (балкон над холом)
        g_width = ASHRAM_ROOMS["HALL_GALLERY"]["width"]
        self.cad.add_line((8000, self.width - g_width), (16000, self.width - g_width), layer="WALLS", floor=f)
        self.cad.add_text("БАЛКОН-ГАЛЕРЕЯ", (10000, self.width - 1000), floor=f)

        # Приклад розміщення одномісної кімнати (3.0 x 3.5м)
        self.cad.add_rect((0, 0), (3000, 3500), layer="WALLS", floor=f)
        self.cad.add_text("ROOM SINGLE 1", (500, 1500), floor=f)
        self.cad.add_inclusion_marker((1500, 1750), floor=f) # Перевірка розвороту

        # Вхідна група
        self.cad.add_text("ВХІД (РІВЕНЬ ДОРОГИ)", (self.length - 3000, 6000), floor=f)

    def generate(self):
        self.build_foundation_axes()
        self.build_floor_0()
        self.build_floor_1()
        self.cad.add_title_block("ASHRAM V3 - REINTEGRATION HUB")
        
        dxf_path = self.cad.save_dxf()
        
        # Генеруємо окремі SVG для поверхів
        svg0 = self.cad.get_svg_preview() # Потрібно додати фільтрацію в cad_core або просто підсвітити
        # Для демонстрації поки збережемо загальний
        with open("_DROPZONE/OUT/ashram_v3_full.svg", "w", encoding="utf-8") as f:
            f.write(svg0)
            
        return dxf_path

if __name__ == "__main__":
    architect = AshramV3Architect()
    path = architect.generate()
    print(f"Model generated: {path}")
