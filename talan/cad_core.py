import ezdxf
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
import io
import base64
import os
from .architecture_standards import FURNITURE, RULES, CONSTRUCTION, calculate_stairs

class TalanCADCore:
    def __init__(self, filename="plan.dxf", base_dir="CAD_Projects"):
        self.doc = ezdxf.new('R2010')
        self.msp = self.doc.modelspace()
        
        # Ensure base directory exists
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
        self.filename = os.path.join(self.base_dir, filename)
        self._setup_layers()

    def _setup_layers(self):
        self.doc.layers.add("WALLS", color=1)
        self.doc.layers.add("WINDOWS", color=4)
        self.doc.layers.add("DOORS", color=2)
        self.doc.layers.add("TEXT", color=3)
        self.doc.layers.add("DIMENSIONS", color=5)
        self.doc.layers.add("AXES", color=7)
        self.doc.layers.add("TABLES", color=7)
        self.doc.layers.add("STAMP", color=7)
        self.doc.layers.add("INCLUSION", color=6)
        self.doc.layers.add("STAIRS", color=1)

    def _get_layer_name(self, layer, floor):
        """Повертає ім'я шару з префіксом поверху (напр. F1_WALLS)."""
        layer_name = f"F{floor}_{layer}" if floor != 0 else layer
        if layer_name not in self.doc.layers:
            color = self.doc.layers.get(layer).color if layer in self.doc.layers else 7
            self.doc.layers.add(layer_name, color=color)
        return layer_name

    def add_line(self, start, end, layer="0", floor=0):
        layer_name = self._get_layer_name(layer, floor)
        self.msp.add_line(start, end, dxfattribs={'layer': layer_name})

    def add_inclusion_marker(self, center, radius=1200, floor=0):
        """Малює пунктирне коло для перевірки інклюзивності."""
        layer_name = self._get_layer_name("INCLUSION", floor)
        self.msp.add_circle(center, radius, dxfattribs={'layer': layer_name, 'linetype': 'DASHED'})
        self.add_text("R1200", (center[0]-200, center[1]-50), height=100, layer="INCLUSION", floor=floor)

    def add_axis_grid(self, x_coords, y_coords, radius=300, floor=0):
        """Створення сітки осей для конкретного поверху."""
        layer = "AXES"
        # Вертикальні осі
        for i, x in enumerate(x_coords, 1):
            start = (x, min(y_coords) - 1000)
            end = (x, max(y_coords) + 1000)
            self.add_line(start, end, layer=layer, floor=floor)
            self.add_text(str(i), (x - 80, end[1] + radius), height=radius, layer=layer, floor=floor)

        # Горизонтальні осі
        alphabet = "АБВГДЕЖЗИКЛМНОПРСТ"
        for i, y in enumerate(y_coords):
            start = (min(x_coords) - 1000, y)
            end = (max(x_coords) + 1000, y)
            self.add_line(start, end, layer=layer, floor=floor)
            label = alphabet[i] if i < len(alphabet) else str(i)
            self.add_text(label, (start[0] - radius - 500, y - 100), height=radius, layer=layer, floor=floor)

    def add_hatch_wall(self, points, pattern="CLEAR", scale=0.5, layer="WALLS"):
        # Professional hatching (Brick, Concrete, etc.)
        if pattern == "CLEAR":
            # Just draw the boundary as a polyline
            self.msp.add_lwpolyline(points, close=True, dxfattribs={'layer': layer})
            return
            
        hatch = self.msp.add_hatch(color=7, dxfattribs={'layer': layer}) # Grey/White
        hatch.paths.add_polyline_path(points, is_closed=True)
        
        if pattern == "SOLID":
            hatch.set_solid_fill()
        else:
            # e.g. "ANSI31" for brick
            hatch.set_pattern_fill(pattern, scale=scale)

    def add_table(self, pos, data, headers=None, col_widths=[500, 2000, 1000]):
        x, y = pos
        row_h = 400
        cur_y = y
        
        # Headers
        if headers:
            for i, h in enumerate(headers):
                cell_x = x + sum(col_widths[:i])
                self.add_rect((cell_x, cur_y), (cell_x + col_widths[i], cur_y - row_h), layer="TABLES")
                self.add_text(h, (cell_x + 50, cur_y - row_h + 100), height=150, layer="TABLES")
            cur_y -= row_h
            
        # Rows
        for row in data:
            for i, val in enumerate(row):
                cell_x = x + sum(col_widths[:i])
                self.add_rect((cell_x, cur_y), (cell_x + col_widths[i], cur_y - row_h), layer="TABLES")
                self.add_text(str(val), (cell_x + 50, cur_y - row_h + 100), height=120, layer="TABLES")
            cur_y -= row_h

    def add_title_block(self, project_name="Talan UA Ashram"):
        # standard stamp at the bottom right
        # Let's assume a fixed page size or just put it far right
        x, y = 10000, -2000
        w, h = 1850, 550 # Reduced scale for better fit
        self.add_rect((x, y), (x + w, y + h), layer="STAMP")
        self.add_line((x, y + 275), (x + w, y + 275), layer="STAMP")
        self.add_text("PROJECT: " + project_name, (x + 50, y + 350), height=100, layer="STAMP")
        self.add_text("STAGE: P (Draft)", (x + 50, y + 100), height=80, layer="STAMP")
        self.add_text("Talan UA", (x + 1200, y + 100), height=120, layer="STAMP")

    def add_wall_thick(self, start, end, thickness=None, layer="WALLS", floor=0):
        if thickness is None:
            thickness = CONSTRUCTION["WALL_EXTERIOR"]
            
        x1, y1 = start
        x2, y2 = end
        if x1 == x2: # Vertical
            self.add_rect((x1 - thickness/2, y1), (x1 + thickness/2, y2), layer=layer, floor=floor)
        elif y1 == y2: # Horizontal
            self.add_rect((x1, y1 - thickness/2), (x2, y1 + thickness/2), layer=layer, floor=floor)
            
    def add_window(self, center, width=1200, orientation="H", layer="WINDOWS", floor=0):
        cx, cy = center
        thickness = CONSTRUCTION["WALL_EXTERIOR"]
        if orientation == "H":
            self.add_rect((cx - width/2, cy - thickness/2), (cx + width/2, cy + thickness/2), layer=layer, floor=floor)
            self.add_line((cx - width/2, cy), (cx + width/2, cy), layer=layer, floor=floor)
        else:
            self.add_rect((cx - thickness/2, cy - width/2), (cx + thickness/2, cy + width/2), layer=layer, floor=floor)
            self.add_line((cx, cy - width/2), (cx, cy + width/2), layer=layer, floor=floor)

    def add_door(self, point, width=None, orientation="H", door_type="INTERNAL_CLEAR", layer="DOORS", floor=0):
        if width is None:
            width = RULES[f"DOOR_{door_type}"]["width"]
            
        x, y = point
        # Draw arc-like door representation
        if orientation == "H":
            self.add_line((x, y), (x + width, y), layer=layer) # Threshold
            self.add_line((x, y), (x, y + width), layer=layer) # Leaf
            # Simple arc (polyline)
            arc_pts = []
            import math
            for a in range(0, 91, 15):
                angle = math.radians(a)
                arc_pts.append((x + width * math.sin(angle), y + width * math.cos(angle)))
            self.msp.add_lwpolyline(arc_pts, dxfattribs={'layer': layer})
        else:
            self.add_line((x, y), (x, y + width), layer=layer)
            self.add_line((x, y), (x + width, y), layer=layer)
            # arc logic mirror... simplified for now
            
    def add_furniture(self, point, item_key, orientation=0, layer="FURNITURE", floor=0):
        item = FURNITURE[item_key]
        w, l = item["width"], item["length"]
        # Basic rect at angle (simplified 0/90)
        x, y = point
        if orientation == 0:
            self.add_rect((x, y), (x + w, y + l), layer=layer, floor=floor)
        else:
            self.add_rect((x, y), (x + l, y + w), layer=layer, floor=floor)
            
        self.add_text(item_key.lower(), (x + 50, y + 50), height=100, layer=layer, floor=floor)

    def add_rect(self, p1, p2, layer="0", floor=0):
        layer_name = self._get_layer_name(layer, floor)
        x1, y1 = p1
        x2, y2 = p2
        points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
        self.msp.add_lwpolyline(points, dxfattribs={'layer': layer_name})

    def add_text(self, text, insert, height=200, layer="TEXT", floor=0):
        layer_name = self._get_layer_name(layer, floor)
        self.msp.add_text(text, dxfattribs={'layer': layer_name, 'height': height}).set_placement(insert)

    def add_dimension(self, start, end, distance=300, layer="DIMENSIONS"):
        # Ensure dimension style exists
        if "EZ_ARCH" not in self.doc.dimstyles:
            setup = self.doc.dimstyles.new("EZ_ARCH")
            setup.dxf.dimtxt = 100
            setup.dxf.dimasz = 50
        
        dim = self.msp.add_linear_dim(base=(min(start[0], end[0]), max(start[1], end[1]) + distance), 
                                     p1=start, p2=end,
                                     dimstyle="EZ_ARCH",
                                     dxfattribs={'layer': layer})
        dim.render()

    def add_dimension_chain(self, points, orientation="H", distance=300, layer="DIMENSIONS"):
        for i in range(len(points) - 1):
            self.add_dimension(points[i], points[i+1], distance=distance, layer=layer)

    def add_symbol(self, point, type="ELECTRIC", layer="COMMUNICATIONS"):
        if layer not in self.doc.layers:
            self.doc.layers.add(layer, color=6)
        
        x, y = point
        if type == "ELECTRIC":
            # Outlet symbol
            self.msp.add_circle((x, y), radius=40, dxfattribs={'layer': layer})
            self.msp.add_line((x, y+40), (x, y+80), dxfattribs={'layer': layer})
        elif type == "LIGHT":
            # Cross in circle
            self.msp.add_circle((x, y), radius=60, dxfattribs={'layer': layer})
            self.msp.add_line((x-40, y-40), (x+40, y+40), dxfattribs={'layer': layer})
            self.msp.add_line((x+40, y-40), (x-40, y+40), dxfattribs={'layer': layer})
        elif type == "WATER":
            # Triangle for tap
            self.msp.add_lwpolyline([(x-40, y-40), (x+40, y-40), (x, y+40), (x-40, y-40)], dxfattribs={'layer': layer})
        elif type == "SEWER":
            # Circle with 'S'
            self.msp.add_circle((x, y), radius=50, dxfattribs={'layer': layer})
            self.add_text("S", (x-20, y-20), height=40, layer=layer)

    def save_dxf(self):
        self.doc.saveas(self.filename)
        return self.filename

    def get_svg_preview(self, layout_name=None):
        try:
            fig = plt.figure(figsize=(12, 9))
            ax = fig.add_axes([0, 0, 1, 1])
            
            # Select target layout: Modelspace or Paperspace
            if layout_name:
                layout = self.doc.layout(layout_name)
            else:
                layout = self.msp
                
            ctx = RenderContext(self.doc)
            out = MatplotlibBackend(ax)
            Frontend(ctx, out).draw_layout(layout)
            
            ax.set_aspect('equal')
            ax.axis('off')
            
            buf = io.BytesIO()
            fig.savefig(buf, format='svg', bbox_inches='tight', pad_inches=0.1)
            plt.close(fig)
            return buf.getvalue().decode('utf-8')
        except Exception as e:
            return f"Error generating preview: {str(e)}"

# Приклад використання:
# cad = TalanCADCore("my_house.dxf")
# cad.add_rect((0,0), (5000, 3000), layer="WALLS")
# cad.save_dxf()
