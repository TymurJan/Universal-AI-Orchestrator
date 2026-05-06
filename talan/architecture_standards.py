"""
Модуль архітектурних стандартів та ергономіки для проекту Ashram.
Базується на стандартах Neufert та принципах NGO Talan UA.
"""

# Одиниці виміру: мм
UNIT = 1.0

# --- Ергономіка: Меблі та Обладнання ---
FURNITURE = {
    # Житлова зона
    "BED_SINGLE": {"width": 900, "length": 2000, "clearance": 600},
    "BED_DOUBLE": {"width": 1600, "length": 2000, "clearance": 700},
    "BED_CHILD": {"width": 800, "length": 1600, "clearance": 500},
    "WARDROBE": {"width": 600, "length": 1200},
    "DESK": {"width": 1200, "length": 600, "chair_zone": 800},
    "ARMCHAIR": {"width": 800, "length": 800},
    "SOFA_SMALL": {"width": 1500, "length": 800},
    "SOFA_LARGE": {"width": 2400, "length": 1000},
    "FIREPLACE": {"width": 1200, "length": 800},
    "TV_STAND": {"width": 1500, "length": 450},
    "CLOSET": {"width": 600, "length": 1800},
    
    # Кухня та Їдальня
    "KITCHEN_COUNTER_DEPTH": 600,
    "DINING_TABLE_PER_PERSON": {"width": 600, "length": 400},
    "DINING_TABLE_20": {"width": 1000, "length": 5000},
    "CHAIR_ZONE": 600,
    
    # Санітарна зона
    "TOILET_ZONE": {"width": 800, "length": 1200},
    "SHOWER_MIN": {"width": 900, "length": 900},
    "WASHBASIN_ZONE": {"width": 700, "length": 1100},
    "BATHROOM_INCLUSIVE": {"width": 2100, "length": 2200}
}

# --- Специфічні розміри кімнат Ashram (згідно ТЗ) ---
ASHRAM_ROOMS = {
    "SINGLE": {"width": 3000, "length": 3500}, # 10.5 m2
    "DOUBLE": {"width": 3500, "length": 4000}, # 14 m2
    "FAMILY": {"width": 3500, "length": 4500}, # ~16 m2
    "SILENCE": {"width": 2000, "length": 2000}, # 4 m2
    "ADMIN": {"width": 3000, "length": 4000},   # 12 m2
    "SECURITY": {"width": 2000, "length": 3000}, # 6 m2
    "TECH_MUSHROOM": {"width": 4000, "length": 5000}, # 20 m2
    "HALL_GALLERY": {"width": 5000, "length": 12000}, # Main space
    "SERVICE": {"width": 3000, "length": 6000}       # Staff/Laundry
}

# --- Архітектурні правила (Neufert) ---
RULES = {
    "DOOR_INTERNAL_CLEAR": {"width": 900, "height": 2100}, # Ashram TZ
    "DOOR_BATHROOM_INCLUSIVE": {"width": 900, "height": 2100},
    "DOOR_MAIN": {"width": 1000, "height": 2200},
    "CORRIDOR_WIDTH": 1500, # Ashram TZ
    "TURN_RADIUS": 1200,    # Ashram TZ
    
    # Сходи: 2H + G = 630мм
    "STAIRS": {
        "IDEAL_HEIGHT": 150, # More comfortable for accessibility
        "IDEAL_GOING": 300,
        "MIN_WIDTH": 1200
    }
}

# --- Матеріали та конструкції (За замовчуванням) ---
CONSTRUCTION = {
    "WALL_EXTERIOR": 400,  # Газоблок + утеплення
    "WALL_INTERIOR_LOAD": 250,
    "WALL_PARTITION": 120, # Цегла/Гіпсокартон
    "FLOOR_THICKNESS": 300 # Перекриття + стяжка
}

def calculate_stairs(total_height):
    """Розрахунок кількості та розміру ступенів."""
    h = RULES["STAIRS"]["IDEAL_HEIGHT"]
    count = round(total_height / h)
    actual_h = total_height / count
    # 2H + G = 630 => G = 630 - 2H
    actual_g = 630 - (2 * actual_h)
    return {
        "count": count,
        "height": actual_h,
        "going": actual_g
    }
