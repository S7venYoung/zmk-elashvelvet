#!/usr/bin/env python3
"""Repo-native pixel artwork, drawn to match the supplied theme reference."""
from pathlib import Path
from PIL import Image, ImageDraw

im = Image.new('1', (82, 55), 0)
d = ImageDraw.Draw(im)
d.polygon([(20,44),(16,41),(14,36),(16,31),(15,26),(11,24),(7,25),(3,29),(1,34),(1,40),(4,45),(10,48),(18,48)], fill=1)
d.polygon([(18,44),(12,43),(8,41),(6,37),(7,33),(10,30),(12,30),(12,33),(9,36),(10,40),(16,41)], fill=0)
d.polygon([(16,43),(18,36),(22,31),(23,25),(22,21),(22,12),(25,7),(29,5),(33,6),(40,12),(45,14),(51,13),(57,5),(61,1),(65,1),(68,5),(70,12),(71,20),(74,25),(75,30),(79,35),(80,41),(77,45),(74,47),(74,51),(64,52),(60,50),(55,52),(42,51),(37,49),(32,51),(27,49),(19,49)], fill=1)
d.polygon([(26,20),(25,13),(28,9),(31,9),(37,15),(35,22),(31,25),(27,25)], fill=0)
d.polygon([(28,13),(31,14),(34,18),(31,18),(31,22),(29,21)], fill=1)
d.polygon([(54,14),(59,7),(63,4),(66,8),(68,16),(68,19),(62,16)], fill=0)
d.polygon([(34,29),(39,24),(44,21),(46,16),(53,16),(59,17),(65,20),(69,23),(70,29),(74,33),(76,37),(76,41),(72,44),(62,45),(57,47),(48,46),(42,44),(35,42),(30,38),(29,34)], fill=0)
d.polygon([(19,42),(22,38),(27,40),(31,44),(31,48),(27,47),(25,44),(23,44),(23,47),(19,46)], fill=0)
d.polygon([(42,48),(44,44),(47,43),(49,44),(49,49)], fill=0)
d.polygon([(53,49),(53,46),(56,44),(59,44),(61,47),(61,50)], fill=0)
d.polygon([(64,50),(64,46),(68,44),(72,45),(72,50)], fill=0)
d.line([(43,32),(45,30),(48,30),(50,31)], fill=1, width=2)
d.line([(64,31),(66,28),(69,28),(71,30)], fill=1, width=2)
d.line([(54,33),(55,35),(57,35),(58,33),(59,35),(61,35),(62,33)], fill=1)
for x in (40,43,71,74):
    d.line([(x,35),(x,37)], fill=1)
for x,y in ((5,9),(73,17)):
    d.polygon([(x,y+1),(x+1,y),(x+3,y),(x+4,y+2),(x+5,y),(x+7,y),(x+8,y+1),(x+8,y+4),(x+4,y+7),(x,y+4)], fill=1)
d.line([(3,50),(77,50)], fill=1, width=2)
d.point((0,50), fill=1)
d.point((80,50), fill=1)
d.line([(74,7),(76,5)], fill=1)
d.line([(78,46),(80,44)], fill=1)
raw = []
for y in range(im.height):
    for bx in range(11):
        raw.append(sum((128 >> bit) for bit in range(8)
                       if bx*8+bit < im.width and im.getpixel((bx*8+bit,y))))
root = Path(__file__).resolve().parents[1]
(root/'cat_art.h').write_text('/* SPDX-License-Identifier: MIT */\n#pragma once\n#include <stdint.h>\n#define CAT_ART_WIDTH 82\n#define CAT_ART_HEIGHT 55\n#define CAT_ART_STRIDE 11\nstatic const uint8_t cat_art[] = {\n'+''.join('    '+', '.join('0x%02x'%v for v in raw[i:i+11])+',\n' for i in range(0,len(raw),11))+'};\n')
