import math
import pandas as pd
import cairo
import networkx as nx
from collections import defaultdict, Counter
import random

WIDTH, HEIGHT = 2000, 1000
random.seed(1)

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
ctx = cairo.Context(surface)
ctx.select_font_face("Times", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
colors = [(random.random(), random.random(), random.random(), .8) for i in range(50)]

lanes = {} # identified by index
lane_count = {} # number of discipline per lane
discipline = defaultdict(dict) # identified by code
gaps_h = defaultdict(set)
gaps_v = defaultdict(set)

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
                    border_size=4, padding_size=4, color=(.1, .1, .1), bg_color=(1, 1, 1),
                    border_color=(0, 0, 0)):
    xi, xf = lanes[semester]
    index_v = lane_count[semester]
    
    xi += margin_size
    xf -= margin_size
    yi = 25 + 140 * index_v
    yf =  yi + 80
    discipline[code]["geometry"] = {
        "back": (xi, middle(yi, yf)),
        "front": (xf, middle(yi, yf)),
        "index_y": index_v
    }
    
    xi, yi, xf, yf = draw_rectangle(xi, yi, xf, yf, bg_color, border_color,
                                    border_size)

    xi, yi, xf, yf = xi + padding_size, yi + padding_size, xf - padding_size, yf - padding_size
    width = xf - xi
    ctx.set_source_rgb(*color)
    draw_text_centered(xi, yi + 15, code, width) ## draw discipline's code
    draw_text_centered_f(xi, yi + 40, name, width, max_font_size=12) ## draw discipline's name
    draw_text_centered(xi, yi + 65, str(duration), width) ## draw discipline's durantion
    lane_count[semester] += 1   


def reserve(src_code, dst_code, discipline):
    src = discipline[src_code]["geometry"]["front"]
    dst = discipline[dst_code]["geometry"]["back"]

    gaps_v[discipline[src_code]["meta-data"]["semester"] - 1].add(src_code)
    gaps_v[discipline[dst_code]["meta-data"]["semester"] - 2].add(src_code)
    if discipline[src_code]["meta-data"]["semester"] + 1 < discipline[dst_code]["meta-data"]["semester"]:
        if discipline[src_code]["geometry"]["index_y"] < discipline[dst_code]["geometry"]["index_y"]:
            gaps_h[discipline[dst_code]["geometry"]["index_y"] + 1].add(src_code)
        else:
            gaps_h[discipline[src_code]["geometry"]["index_y"]].add(src_code)

def calculate_offsets(reservation):
    offsets = dict()
    return offsets
    
def connect(src_code, dst_code, discipline, lanes, line_width=2, arrow_width=3, color=(0.1, 0.1, 0.1)):
    ctx.save()
    ctx.set_line_width(line_width)
    
    ctx.set_source_rgba(*color)
    src = discipline[src_code]["geometry"]["front"]
    dst = discipline[dst_code]["geometry"]["back"]
    ctx.move_to(*src)
    if discipline[src_code]["meta-data"]["semester"] + 1 == discipline[dst_code]["meta-data"]["semester"]:
        ctx.line_to(lanes[discipline[src_code]["meta-data"]["semester"]][1], discipline[src_code]["geometry"]["front"][1])
        ctx.line_to(lanes[discipline[src_code]["meta-data"]["semester"]][1], discipline[dst_code]["geometry"]["back"][1])
        ctx.line_to(*dst)
    else:
        ctx.line_to(lanes[discipline[src_code]["meta-data"]["semester"]][1], discipline[src_code]["geometry"]["front"][1])
        if discipline[src_code]["geometry"]["back"][1] < discipline[dst_code]["geometry"]["back"][1]:
            yf = discipline[dst_code]["geometry"]["back"][1] - 50
        else:
            yf = discipline[dst_code]["geometry"]["back"][1] + 50
        ctx.line_to(lanes[discipline[src_code]["meta-data"]["semester"]][1], yf)
        ctx.line_to(lanes[discipline[dst_code]["meta-data"]["semester"]][0], yf)
        ctx.line_to(lanes[discipline[dst_code]["meta-data"]["semester"]][0], dst[1])
        ctx.line_to(*dst)
    ctx.stroke()

    ctx.set_line_width(arrow_width)
    
    ctx.move_to(*dst)
    ctx.rel_line_to(-5, -5)
    ctx.stroke()

    ctx.move_to(*dst)
    ctx.rel_line_to(-5, +5)
    ctx.stroke()

    ctx.restore()


def main():
    draw_background(0.9, 0.9, 0.9)
    draw_lanes(8, color=(0.8, 0.8, 0.8))

    df = pd.read_csv("matrix.csv")
    requirements = []
    G = nx.DiGraph()
    
    for i, row in df.iterrows():
        discipline[row["code"]]["meta-data"] = {
            "code": row["code"],
            "name": row["name"],
            "duration": row["duration"],
            "semester": row["semester"]
        }
        
        G.add_node(row["code"])
        
        if str(row["requirement"]).startswith("ENC"):
            reqs = list(map(str.strip, row["requirement"].split(';')))
            for r in reqs:
                requirements.append((r, row["code"]))
                G.add_edge(r, row["code"])
                
    paths = []
    for i, row in df.iterrows():
        path = list(nx.dfs_edges(G, source=row["code"]))
        paths.append(path)

    paths.sort(key=lambda l:-len(l))

    already_drawn = []
    for path in paths:
        if not len(path):
            continue

        border_color = (.1, .1, .1)
        border_size = 2
        data = discipline[path[0][0]]["meta-data"]
        if data["code"] not in already_drawn:
            already_drawn.append(data["code"])
            draw_discipline(data["code"], data["name"], data["duration"], data["semester"], lanes, bg_color=(.9, .9, .9), border_color=border_color, border_size=border_size)
        for src, dst in path:
            data = discipline[dst]["meta-data"]
            if data["code"] not in already_drawn:
                already_drawn.append(data["code"])
                draw_discipline(data["code"], data["name"], data["duration"], data["semester"], lanes, bg_color=(0.9, 0.9, 0.9), border_color=border_color, border_size=border_size)

    for d in discipline:
        if d not in already_drawn:
            data = discipline[d]["meta-data"]
            draw_discipline(data["code"], data["name"], data["duration"], data["semester"], lanes, bg_color=(0.9, 0.9, 0.9), border_color=border_color, border_size=border_size)
            
    for i, req in enumerate(requirements):
        reservation = reserve(req[0], req[1], discipline)
        offsets = calculate_offsets(reservation)
        connect(req[0], req[1], discipline, lanes, offsets, color=colors[i])


    surface.write_to_png("v1.png")  # Output to PNG

if __name__ == "__main__":
    main()
