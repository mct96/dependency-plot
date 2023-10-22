import math
import cairo

WIDTH, HEIGHT = 2000, 720

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
ctx = cairo.Context(surface)
ctx.select_font_face("Times", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

#ctx.scale(WIDTH, HEIGHT)  # Normalizing the canvas
coord = {}

def draw_background(*color):
    ctx.set_source_rgb(*color)
    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    ctx.fill()

def find_max_font_size(text, max_width):
    font_size = 0
    w = 0
    while w < max_width:
        font_size += 0.1
        ctx.set_font_size(font_size)
        _, _, w, _, _, _ = ctx.text_extents(text)
    return font_size - 0.1

def draw_text_f(x, y, text, max_width):
    font_size = find_max_font_size(text, max_width)
    ctx.set_font_size(font_size)
    _, _, w, _, _, _ = ctx.text_extents(text)
    ctx.move_to(x + (max_width / 2 - w / 2), y)
    ctx.show_text(text)

def draw_text(x, y, text, width):
    ctx.set_font_size(14)
    _, _, w, _, _, _ = ctx.text_extents(text)
    ctx.move_to(x + (width / 2 - w / 2), y)
    ctx.show_text(text)
    
def draw_rectangle(x, y, w, h, color, border):
    ms = 1
    ctx.set_source_rgb(*border)
    ctx.rectangle(x-ms, y-ms, w+2*ms, h+2*ms)
    ctx.fill()
    ctx.set_source_rgb(*color)
    ctx.rectangle(x, y, w, h)
    ctx.fill()

def draw_lanes(n_lanes):
    ctx.set_source_rgb(1, 0, 0)
    width = WIDTH // n_lanes
    ctx.set_line_width(1)
    widths = []
    for i in range(n_lanes):
        ctx.move_to((i+1)*width, 0)
        ctx.line_to((i+1)*width, HEIGHT)
        ctx.stroke()
        widths.append((i*width, (i+1)*width))
    return widths

def draw_discipline(limxi, limxf, width, height, code, name, duration):
    x0 = limxi + ((limxf - limxi)/2 - width / 2)
    xf = x0 + width
    y0 = 20
    draw_rectangle(x0, y0, width, 80, (0.9, 0.9, 0.9), (0.1, 0.1, 0.1))
    coord[code] = [x0, y0, x0+width, y0+80]
    ctx.set_source_rgb(0, 0, 0)
    draw_text(x0, y0 + 15, code, width)
    draw_text_f(x0, y0 + 40, name, width)
    draw_text(x0, y0 + 65, str(duration), width)
    
    
def draw_edges():
    pass

draw_background(0.9, 1, 1)
widths = draw_lanes(8)
for width in widths:
    draw_discipline(width[0], width[1], 180, 150, "ENC-01", "Introdução à Engenharia da Computação", 68)

surface.write_to_png("example.png")  # Output to PNG
