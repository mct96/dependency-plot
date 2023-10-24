import math
import pandas as pd
import cairo
import networkx as nx
from collections import defaultdict, Counter
import random
from matplotlib.pyplot import cm
import numpy as np
import matplotlib

r = 297 / 210
WIDTH, HEIGHT = int(1500 * r), 1000

random.seed(1)

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
ctx = cairo.Context(surface)
ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

colors_palette = matplotlib.colormaps['prism'](np.linspace(0, 1, 30))
colors_index = 0
colors = {}

class Configuration:
    col = 8
    lin = 7
    gap_v = 60
    gap_h = 100
    line_offset = 10
    box_width = 170
    box_height = 80
    start_point = (10, 50)
    line_width = 3
    arrow_width = 3
    arrow_size = 8
    attach_space = 15

class BoxConfiguration:
    margin_size=30
    border_size=1
    padding_size=4
    color=(.1, .1, .1)
    bg_color=(1, 1, 1)
    border_color=(0, 0, 0)
    

box = dict()    
    
    
lane_count = {} # number of discipline per lane
disciplines = defaultdict(dict) # identified by code

def draw_background(*color):
    ctx.save()
    ctx.set_source_rgb(*color)
    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    ctx.fill()
    ctx.restore()


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
    
def draw_rectangle(xi, yi, xf, yf, bconfig):
    ctx.set_source_rgb(*bconfig.bg_color)
    ctx.rectangle(xi, yi, xf-xi, yf-yi)
    ctx.fill()

    ctx.set_source_rgb(*bconfig.border_color)
    ctx.set_line_width(bconfig.border_size)
    ctx.rectangle(xi, yi, xf-xi, yf-yi)
    ctx.stroke()

def draw_box(code, name, duration, i, j, bconfig, gconfig):
    xi = gconfig.start_point[0] + (gconfig.box_width + gconfig.gap_h) * j
    xf = xi + gconfig.box_width
    yi = gconfig.start_point[1] + (gconfig.box_height + gconfig.gap_v) * i
    yf = yi + gconfig.box_height
    
    disciplines[code]["geometry"] = {
        "back": (xi, middle(yi, yf)),
        "front": (xf, middle(yi, yf)),
        "xi": xi,
        "xf": xf,
        "yi": yi,
        "yf": yf,
        "i": i,
    }
    
    draw_rectangle(xi, yi, xf, yf, bconfig)
    xi, yi, xf, yf = xi + bconfig.padding_size, yi + bconfig.padding_size, xf - bconfig.padding_size, yf - bconfig.padding_size
    ctx.set_source_rgb(*bconfig.color)
    draw_text_centered(xi, yi + 15, code, xf-xi) ## draw discipline's code
    draw_text_centered_f(xi, yi + 40, name, xf-xi, max_font_size=12) ## draw discipline's name
    draw_text_centered(xi, yi + 65, str(duration), gconfig.box_width) ## draw discipline's durantion

def get_gap_v(j, gconfig):
    xi = gconfig.start_point[0] + (gconfig.box_width + gconfig.gap_h) * j + gconfig.box_width
    xf = xi + gconfig.gap_h
    return xi, xf

def get_gap_h(i, gconfig):
    yi = gconfig.start_point[1] + (gconfig.box_height + gconfig.gap_v) * i + gconfig.box_height
    yf = yi + gconfig.gap_v
    return yi, yf  

def reserve(src_code, dst_code, hor, vert, gconfig):
    src, dst = disciplines[src_code], disciplines[dst_code]
    vert[src["semester"] - 1].append(src_code)
    vert[dst["semester"] - 2].append(src_code)
    
    if src["semester"] + 1 < dst["semester"]:
        if src["geometry"]["i"] == 0 == dst["geometry"]["i"]:
            hor[0].append(src_code)
        else:
            hor[dst["geometry"]["i"] - 1].append(src_code)
        
def alloc(direction, func, gconfig):
    lines = defaultdict(lambda: defaultdict(float))
    for i, codes in direction.items():
        yi, yf = func(i) # calculate the init and end of the gap
        mid = (yf + yi) / 2
        start = mid - gconfig.line_offset * len(set(codes)) / 2
        for code in set(codes):
            lines[i][code] = start
            start += gconfig.line_offset
    return lines

def retrive_color(code):
    global colors_index
    if code not in colors:
        colors[code] = colors_palette[colors_index]
        colors_index += 1
    return colors[code]
                
def connect(src_code, dst_code, h, v, gconfig):
    ctx.save()
    ctx.set_line_width(gconfig.line_width)
    
    src = disciplines[src_code]
    dst = disciplines[dst_code]
    
    if len(dst["reqs"]):
        ctx.set_source_rgba(*retrive_color(src_code))
        
    p0, pf = src["geometry"]["front"], dst["geometry"]["back"]

    if len(dst["reqs"]) > 1:
        yy = gconfig.attach_space * (dst["reqs"].index(src_code) - len(dst["reqs"]) / 2)
        pf = (pf[0], pf[1] + yy)
    
    ctx.move_to(*p0)
    ctx.line_to(v[src["semester"] - 1][src_code], p0[1])
    if src["semester"] + 1 < dst["semester"]:
        if src["geometry"]["i"] == 0 == dst["geometry"]["i"]:
            y = h[0][src_code]
        else:
            y = h[dst["geometry"]["i"] - 1][src_code]
        ctx.line_to(v[src["semester"] - 1][src_code], y)
        ctx.line_to(v[dst["semester"] - 2][src_code], y)
    ctx.line_to(v[dst["semester"] - 2][src_code], pf[1])
    
    ctx.line_to(*pf)
    
    ctx.stroke()

    ctx.set_line_width(gconfig.arrow_width)
    
    ctx.move_to(*pf)
    ctx.rel_line_to(-gconfig.arrow_size, -gconfig.arrow_size)
    ctx.stroke()

    ctx.move_to(*pf)
    ctx.rel_line_to(-gconfig.arrow_size, +gconfig.arrow_size)
    ctx.stroke()

    ctx.restore()


def main():
    draw_background(0.8, 0.8, 0.8)


    bconfig = BoxConfiguration()
    gconfig = Configuration()
    df = pd.read_csv("matrix.csv")        
    requirements = []
    G = nx.DiGraph()

    c = Counter()
    for i, row in df.iterrows():
        disciplines[row["code"]] = {
            "code": row["code"],
            "name": row["name"],
            "duration": row["duration"],
            "semester": row["semester"]
        }

        if str(row["requirement"]).startswith("ENC"):
            reqs = list(map(str.strip, row["requirement"].split(';')))
            disciplines[row["code"]]["reqs"] = sorted(list(set(reqs)))
            for r in reqs:
                requirements.append((r, row["code"]))
                G.add_edge(r, row["code"])
                
        draw_box(row["code"], row["name"], row["duration"], c[row["semester"] - 1], row["semester"] - 1, bconfig, gconfig)
        c[row["semester"] - 1] += 1
                    
    hor, vert = defaultdict(list), defaultdict(list)
    for i, req in enumerate(requirements):
        reserve(req[0], req[1], hor, vert, gconfig)

    h = alloc(hor, lambda x: get_gap_h(x, gconfig), gconfig)
    v = alloc(vert, lambda x: get_gap_v(x, gconfig), gconfig)

    for i, req in enumerate(requirements):
        connect(req[0], req[1], h, v, gconfig)



    surface.write_to_png("v3.png")  # Output to PNG

if __name__ == "__main__":
    main()
