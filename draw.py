import math
import pandas as pd
import cairo

WIDTH, HEIGHT = 2000, 720

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
ctx = cairo.Context(surface)
ctx.select_font_face("Times", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

lanes = {} # identified by index
lane_count = {} # number of discipline per lane
discipline = {} # identified by code

def draw_background(*color):
    ctx.set_source_rgb(*color)
    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    ctx.fill()


def set_font_size_and_get_width(font_size, text):
    ctx.set_font_size(font_size)
    _, _, w, _, _, _ = ctx.text_extents(text)
    return w

def find_max_font_size(text, max_width):
    font_size, width = 0, 0
    while width < max_width:
        font_size += 0.1
        width = set_font_size_and_get_width(font_size, text)
    width = set_font_size_and_get_width(font_size, text)
    return font_size, width

def center_horizontally(x, text_width, total_width):
    return x + total_width / 2 - text_width / 2

def middle(a, b):
    return (a + b) / 2
        

def draw_text_centered_f(x, y, text, max_width, max_font_size=-float('inf')):
    """
        automatically adjust font size so that the width of text keeps constant
    """
    font_size, text_width = find_max_font_size(text, max_width)
    text_width = set_font_size_and_get_width(min(font_size, max_font_size), text)
    ctx.move_to(center_horizontally(x, text_width, max_width), y)
    ctx.show_text(text)

def draw_text_centered(x, y, text, width):
    """
        draw a text centered in the space spacified by width starting at
        position (x, y)
    """
    
    ctx.set_font_size(14)
    _, _, w, _, _, _ = ctx.text_extents(text)
    ctx.move_to(x + (width / 2 - w / 2), y)
    ctx.show_text(text)
    
def draw_rectangle(xi, yi, xf, yf, color, border_color, border_size):
    ctx.set_source_rgb(*border_color)
    ctx.rectangle(xi, yi, xf - xi, yf - yi)
    ctx.fill()

    xi += border_size
    yi += border_size
    xf -= border_size
    yf -= border_size
    
    ctx.set_source_rgb(*color)
    ctx.rectangle(xi, yi, xf - xi, yf - yi)
    ctx.fill()
    return xi, yi, xf, yf

def draw_lanes(n_lanes, color=(1, 0, 0), line_width=1):
    ctx.set_source_rgb(*color)
    width = WIDTH // n_lanes
    ctx.set_line_width(line_width)
    
    for i in range(n_lanes):
        ctx.move_to((i + 1) * width, 0)
        ctx.line_to((i + 1) * width, HEIGHT)
        ctx.stroke()
        lanes[i + 1] = (i * width, (i + 1) * width)
        lane_count[i + 1] = 0
        

def draw_discipline(code, name, duration, semester, lanes, margin_size=30,
                    border_size=4, padding_size=4, color=(1, 1, 1),
                    border_color=(0, 0, 0)):
    xi, xf = lanes[semester]
    index_v = lane_count[semester]
    
    xi += margin_size
    xf -= margin_size
    yi = 25 + 100 * index_v
    yf =  yi + 80
    discipline[code] = {"back": (xi, middle(yi, yf)), "front": (xf, middle(yi, yf))}
    xi, yi, xf, yf = draw_rectangle(xi, yi, xf, yf, color, border_color,
                                    border_size)
    xi, yi, xf, yf = xi + padding_size, yi + padding_size, xf - padding_size, yf - padding_size
    width = xf - xi
    ctx.set_source_rgb(1, 0, 0)
    draw_text_centered(xi, yi + 15, code, width) ## draw discipline's code
    draw_text_centered_f(xi, yi + 40, name, width, max_font_size=12) ## draw discipline's name
    draw_text_centered(xi, yi + 65, str(duration), width) ## draw discipline's durantion
    lane_count[semester] += 1   

    
def connect(src_code, dst_code, line_width=3, color=(0.1, 0.1, 0.1)):
    ctx.save()
    ctx.set_line_width(line_width)
    ctx.set_source_rgba(*color)
    src = discipline[src_code]["front"]
    dst = discipline[dst_code]["back"]
    ctx.move_to(*src)
    ctx.line_to(*dst)
    ctx.stroke()

    ctx.restore()


def main():
    draw_background(0.9, 1, 1)
    draw_lanes(8)

    df = pd.read_csv("matrix.csv")
    requirements = []
    for i, row in df.iterrows():
        draw_discipline(row["code"], row["name"], row["duration"], row["semester"], lanes)
        if str(row["requirement"]).startswith("ENC"):
            reqs = list(map(str.strip, row["requirement"].split(';')))
            for r in reqs:
                requirements.append((r, row["code"]))

    for req in requirements:
        connect(req[0], req[1])
        
    surface.write_to_png("example.png")  # Output to PNG

if __name__ == "__main__":
    main()
