#!/usr/bin/env python
import xml.etree.ElementTree
import copy
import re

import numpy

_KEYBOARD_TEMPLATE = 'keyboard_base.svg'
_KEYBOARD_OUTPUT = 'keyboard_cobra.svg'
_KEY_TEMPLATE = 'template.svg'

# Template values are in mm and must be scaled to pixel units
_MM_SCALE = 0.26458

def parse_svg_matrix(matrix):
    result = re.search('matrix\((.*)\)', matrix)
    elements = result.group(1).split(',')
    matrix = numpy.array((
        (float(elements[0]), float(elements[2]), float(elements[4])),
        (float(elements[1]), float(elements[3]), float(elements[5])),
        (0,  0, 1)
    ))
    return matrix

def parse_dimensions_from_path(path):
    class MinMaxCursor:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.min_x = x
            self.min_y = y
            self.max_x = x
            self.max_y = y

        def add(self, x, y, draw=True):
            new_x = self.x + x
            new_y = self.y + y
            if draw:
                self.min_x = min(self.min_x, new_x)
                self.min_y = min(self.min_y, new_y)
                self.max_x = max(self.max_x, new_x)
                self.max_y = max(self.max_y, new_y)
            self.x = new_x
            self.y = new_y

        def set(self, x, y, draw=True):
            self.min_x = min(self.min_x, x)
            self.min_y = min(self.min_y, y)
            self.max_x = max(self.max_x, x)
            self.max_y = max(self.max_y, y)
            if draw:
                self.x = x
                self.y = y

        def set_x(self, x):
            self.min_x = min(self.min_x, x)
            self.max_x = max(self.max_x, x)
            self.x = x

        def set_y(self, y):
            self.min_y = min(self.min_y, y)
            self.max_y = max(self.max_y, y)
            self.y = y

        def minimum(self):
            return self.min_x, self.min_y

        def maximum(self):
            return self.max_x, self.max_y

    def peek(iterator):
        return next(copy.deepcopy(iterator))

    def isint(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    d = path.attrib['d']
    d_iter = iter(d.split(' '))

    cursor = None
    while True:
        try:
            token = next(d_iter)
        except StopIteration:
            break
        if token == 'm':
            offset = tuple([int(x) for x in next(d_iter).split(',')])
            if cursor is None:
                cursor = MinMaxCursor(*offset)
            else:
                cursor.add(*offset, draw=False)
        elif token == 'M':
            pos = tuple([int(x) for x in next(d_iter).split(',')])
            if cursor is None:
                cursor = MinMaxCursor(*pos)
            else:
                cursor.set(*pos, draw=False)
        elif token == 'c':
            offset_a = tuple([int(x) for x in next(d_iter).split(',')])
            offset_b = tuple([int(x) for x in next(d_iter).split(',')])
            offset_c = tuple([int(x) for x in next(d_iter).split(',')])
            # Only care about the end point
            cursor.add(*offset_c)
        elif token == 'C':
            pos_a = tuple([int(x) for x in next(d_iter).split(',')])
            pos_b = tuple([int(x) for x in next(d_iter).split(',')])
            pos_c = tuple([int(x) for x in next(d_iter).split(',')])
            # Only care about the end point
            cursor.set(*pos_c)
        elif token == 'h':
            while isint(peek(d_iter)):
                x = int(next(d_iter))
                cursor.add(x, 0)
        elif token == 'v':
            while isint(peek(d_iter)):
                y = int(next(d_iter))
                cursor.add(0, y)
        elif token == 'H':
            while isint(peek(d_iter)):
                x = int(next(d_iter))
                cursor.set_x(x)
        elif token == 'V':
            while isint(peek(d_iter)):
                y = int(next(d_iter))
                cursor.set_y(y)
        elif token == 'z':
            pass
        else:
            raise Exception(token)
    style = path.attrib['style']
    stroke_width = float(re.search('stroke-width:([0-9\.]*);', style).group(1))
    x0, y0 = cursor.minimum()
    x1, y1 = cursor.maximum()
    x, y = x0 - stroke_width / 2, y0 - stroke_width / 2
    w, h = x1 - x + stroke_width / 2, y1 - y + stroke_width / 2
    return ((x, y), (w, h))

def parse_translate_from_transform(transform):
    result = re.search('translate\(([0-9\-\.]*,[0-9\-\.]*)\)', transform)
    translate = result.group(1).split(',')
    return float(translate[0]), float(translate[1])

def transform_y(matrix, y):
    inverse = numpy.linalg.inv(matrix)
    v = inverse.dot(numpy.array((0, y / _MM_SCALE, 0)))
    return v[1]

def transform_x(matrix, x):
    inverse = numpy.linalg.inv(matrix)
    v = inverse.dot(numpy.array((x / _MM_SCALE, 0, 0)))
    return v[0]

def transform_x_y(obj, translate, matrix, g):
    path = g.find('{http://www.w3.org/2000/svg}path')

    old_x = float(obj.attrib['x']) + translate[0]
    old_y = float(obj.attrib['y']) + translate[1]

    (x, y), _ = parse_dimensions_from_path(path)
    obj.attrib['x'] = str(x + transform_x(matrix, old_x))
    obj.attrib['y'] = str(y + transform_y(matrix, old_y))

def add_rect(cobra, translate, svg_matrix, rect, g, stretched=False):
    matrix = parse_svg_matrix(svg_matrix)
    path = g.find('{http://www.w3.org/2000/svg}path')

    transform_x_y(rect, translate, matrix, g)

    if 'ry' in rect.attrib:
        ry = transform_y(matrix, float(rect.attrib['ry']))
        rect.attrib['ry'] = str(ry)

    if stretched:
        path = g.find('{http://www.w3.org/2000/svg}path')
        (gx, _), (gw, _) = parse_dimensions_from_path(path)
        x_offset = float(rect.attrib['x']) - gx
        width = gw - x_offset * 2
    else:
        width = transform_y(matrix, float(rect.attrib['width']))
    rect.attrib['width'] = str(width)

    height = transform_y(matrix, float(rect.attrib['height']))
    rect.attrib['height'] = str(height)

    style = rect.attrib['style']
    stroke_width = re.search('stroke-width:([0-9\.]*);', style).group(1)
    new_stroke_width = transform_x(matrix, float(stroke_width))
    new_stroke_width_str = 'stroke-width:' + str(new_stroke_width) + ';'
    new_style = re.sub('stroke-width:([0-9\.]*);', new_stroke_width_str, style)
    rect.attrib['style'] = new_style

    g.remove(g.find('{http://www.w3.org/2000/svg}path'))
    g.attrib['transform'] = svg_matrix
    g.append(rect)
    cobra.append(g)

def add_text(cobra, translate, svg_matrix, text, g, centered=False):
    matrix = parse_svg_matrix(svg_matrix)
    path = g.find('{http://www.w3.org/2000/svg}path')

    transform_x_y(text, translate, matrix, g)

    if centered:
        (gx, _), (gw, _) = parse_dimensions_from_path(path)
        text.attrib['x'] = str(gx + gw / 2)

    tspan = text.find('{http://www.w3.org/2000/svg}tspan')
    transform_x_y(tspan, translate, matrix, g)

    style = tspan.attrib['style']
    font_size = re.search('font-size:([0-9\.]*)px', style).group(1)
    new_font_size = transform_y(matrix, float(font_size))
    new_font_size_str = 'font-size:' + str(new_font_size) + 'px'
    new_style = re.sub('font-size:([0-9\.]*)px', new_font_size_str, style)
    tspan.attrib['style'] = new_style

    g = copy.deepcopy(g)
    g.attrib['transform'] = svg_matrix
    g.remove(g.find('{http://www.w3.org/2000/svg}path'))
    g.append(text)
    cobra.append(g)

def replace_text(text, s):
    tspan = text.find('{http://www.w3.org/2000/svg}tspan')
    tspan.text = s

def replace_fill(text, s):
    color = 'fill:' + s

    text_style = text.attrib['style']
    text.attrib['style'] = re.sub('fill:#([0-9a-f]*)', color, text_style)

    tspan = text.find('{http://www.w3.org/2000/svg}tspan')
    tspan_style = tspan.attrib['style']
    tspan.attrib['style'] = re.sub('fill:#([0-9a-f]*)', color, tspan_style)

def load_template(filename):
    template = {}

    svg = xml.etree.ElementTree.parse(filename)
    template['g'] = svg.getroot().find('{http://www.w3.org/2000/svg}g')
    template['translate'] = \
        parse_translate_from_transform(template['g'].attrib['transform'])

    template['rects'] = {}
    for rect in template['g'].findall('{http://www.w3.org/2000/svg}rect'):
        label = rect.attrib[
                    '{http://www.inkscape.org/namespaces/inkscape}label']
        template['rects'][label] = rect

    template['texts'] = {}
    for text in template['g'].findall('{http://www.w3.org/2000/svg}text'):
        label = text.attrib[
                    '{http://www.inkscape.org/namespaces/inkscape}label']
        template['texts'][label] = text

    return template

def make_special(lines, background=True):
    definition = {}

    definition['texts'] = {}
    if len(lines) == 1:
        definition['texts']['special middle'] = lines[0]
    else:
        definition['texts']['special top'] = lines[0]
        definition['texts']['special bottom'] = lines[1]

    if background:
        definition['rects'] = ['background']

    return definition

def make_arrow_vertical(lines, background=True):
    definition = {}

    definition['texts'] = {}
    definition['texts']['arrow vertical'] = lines[0]

    if background:
        definition['rects'] = ['background']

    return definition

def make_arrow_horizontal(lines, background=True):
    definition = {}

    definition['texts'] = {}
    definition['texts']['arrow horizontal'] = lines[0]

    if background:
        definition['rects'] = ['background']

    return definition

def make_number(number, top, bottom, symbol, grid, top_background=False):
    definition = {}

    definition['texts'] = {}
    if number is not None:
        if number in '012':
            definition['texts']['number 012'] = number
        elif number in '34579':
            definition['texts']['number 34579'] = number
        else:
            definition['texts']['number'] = number
    if top is not None:
        definition['texts']['top'] = top
    if bottom is not None:
        definition['texts']['bottom'] = bottom
    if symbol is not None:
        definition['texts']['number symbol'] = symbol

    definition['rects'] = ['background']
    if top_background:
        definition['rects'].append('top background')

    if grid[0] != ' ':
        definition['rects'].append('grid border')
    if grid[1] != ' ':
        definition['rects'].append('grid a')
    if grid[2] != ' ':
        definition['rects'].append('grid b')
    if grid[3] != ' ':
        definition['rects'].append('grid c')
    if grid[4] != ' ':
        definition['rects'].append('grid d')

    return definition


def make_letter_symbol(letter, top, bottom, secondary, symbol):
    definition = {}

    definition['rects'] = ['background']

    definition['texts'] = {}
    if letter is not None:
        definition['texts']['letter'] = letter
    if top is not None:
        definition['texts']['top'] = top
    if bottom is not None:
        definition['texts']['bottom'] = bottom
    if secondary is not None:
        definition['texts']['letter secondary'] = secondary
    if symbol is not None:
        definition['texts']['letter symbol'] = symbol

    return definition


def make_letter_word(letter, top, bottom, secondary, tertiary):
    definition = {}

    definition['rects'] = ['background']

    definition['texts'] = {}
    if letter is not None:
        definition['texts']['letter'] = letter
    if top is not None:
        definition['texts']['top'] = top
    if bottom is not None:
        definition['texts']['bottom'] = bottom
    if secondary is not None:
        definition['texts']['letter secondary'] = secondary
    if tertiary is not None:
        definition['texts']['letter tertiary'] = tertiary

    return definition

def make_space():
    definition = {}

    definition['rects'] = ['background']
    definition['texts'] = {'break': 'BREAK', 'space': 'SPACE'}

    return definition


def alt_color(labels):
    return [(label, '#000000') for label in labels]


def main():
    template = load_template(_KEY_TEMPLATE)

    keys = {}

    arrow_vertical_defs = {
        'g11554': (['⇧'],), # up
        'g11558': (['⇩'],), # down
    }

    arrow_horizontal_defs = {
        'g11658': (['⇨'],), # right
        'g11538': (['⇦'],), # left
    }

    arrow_vertical_alt_defs = {
        'g11638': (['⇧'],), # up red
        'g11634': (['⇩'],), # down red
        'g11674': (['⇧'],), # up
        'g11678': (['⇩'],), # down
    }

    arrow_horizontal_alt_defs = {
        'g11646': (['⇨'],), # right red
        'g11642': (['⇦'],), # left red
        'g11598': (['⇨'],), # right
        'g11670': (['⇦'],), # left
    }

    special_alt_defs = {
        'g11654': (['ESC'],), # red
        'g11370': (['ESC'],),
        'g11626': (['F1'],), # red
        'g11622': (['F2'],), # red
        'g11618': (['F3'],), # red
        'g11614': (['F4'],), # red
        'g11374': (['F1'],),
        'g11378': (['F2'],),
        'g11382': (['F3'],),
        'g11386': (['F4'],),
        'g11602': (['LINE', 'FEED'],), # red
        'g11610': (['NO', 'SCROLL'],), # red
        'g11606': (['CTRL'],), # red
        'g11562': (['LINE', 'FEED'],),
        'g11566': (['NO', 'SCROLL'],),
        'g11570': (['CTRL'],),
    }

    special_defs = {
        'g11338': (['ESC'],),
        'g11342': (['F1'],),
        'g11346': (['F2'],),
        'g11350': (['F3'],),
        'g11354': (['F4'],),
        'g11358': (['LINE', 'FEED'],),
        'g11362': (['NO', 'SCROLL'],),
        'g11366': (['CTRL'],),
        'g11746': (['GRAPH', 'NORM'],),
        'g11514': (['NEW', 'MODE'],),
        'g11390': (['PG EDT'],),
        'g11734': (['TAB'],),
        'g11718': (['DEL'],),
        'g11742': (['CAPS', 'LOCK'],),
        'g11750': (['ENTER'],),
        'g11738': (['CAPS', 'SHIFT'],),
        'g11726': ([('SYMBOL', '#fc3d4a'), ('SHIFT', '#fc3d4a')],),
    }

    number_defs = {
        'g11394': ('1', ('BLUE', '#2aacfd'), 'DEF FN', '!', '[a cd'),
        'g11398': ('2', ('RED', '#fc3d4a'), 'FN', '@', '[ bcd'),
        'g11402': ('3', ('MAGENTA', '#fe70e9'), 'LINE', '#', '[  cd'),
        'g11406': ('4', ('GREEN', '#ccf96f'), 'OPEN #', '$', '[abc '),
        'g11410': ('5', ('CYAN', '#55ebe8'), 'CLOSE #', '%', '[a c '),
        'g11414': ('6', ('YELLOW', '#f5ec71'), 'MOVE', '&', '[ bc '),
        'g11418': ('7', ('WHITE', '#ffffff'), 'ERASE', "'", '[ b  '),
        'g11518': ('8', None, 'POINT', '(', '[abcd'),
        'g11522': ('9', None, 'CAT', ')', '     '),
        'g11526': ('0', ('BLACK', '#000000'), 'FORMAT', '_', '     ', True),
    }

    symbol_defs = {
        'g11422': ('Q', 'SIN', 'ASN', 'PLOT', '<='),
        'g11426': ('W', 'COS', 'ACS', 'DRAW', '<>'),
        'g11430': ('E', 'TAN', 'ATN', 'REM', '>='),
        'g11434': ('R', 'INT', 'VERIFY', 'RUN', '<'),
        'g11438': ('T', 'RND', 'MERGE', 'RAND', '>'),
        'g11530': ('O', 'PEEK', 'OUT', 'POKE', ';'),
        'g11534': ('P', 'TAB', '©', 'PRINT', '"'),
        'g11474': ('H', 'SQR', 'CIRCLE', 'GOSUB', '↑'),
        'g11478': ('J', 'VAL', 'VAL $', 'LOAD', '-'),
        'g11482': ('K', 'LEN', 'SCREEN $', 'LIST', '+'),
        'g11542': ('L', 'USR', 'ATTR', 'LET', '='),
        'g11486': ('Z', 'LN', 'BEEP', 'COPY', ':'),
        'g11490': ('X', 'EXP', 'INK', 'CLEAR', '£'),
        'g11494': ('C', 'L PRINT', 'PAPER', 'CONT', '?'),
        'g11498': ('V', 'L LIST', 'FLASH', 'CLS', '/'),
        'g11502': ('B', 'BIN', 'BRIGHT', 'BORDER', '*'),
        'g11506': ('N', 'IN KEY $', 'OVER', 'NEXT', ','),
        'g11510': ('M', 'PI', 'INVERSE', 'PAUSE', '.'),
        'g11550': ('J', 'VAL', 'VAL $', 'LOAD', '-'),
    }

    word_defs = {
        'g11442': ('Y', 'STR $', '[', 'RETURN', 'AND'),
        'g11446': ('U', 'CHR $', ']', 'IF', 'OR'),
        'g11450': ('I', 'CODE', 'IN', 'INPUT', 'AT'),
        'g11454': ('A', 'READ', '~', 'NEW', 'STOP'),
        'g11458': ('S', 'RESTORE', '|', 'SAVE', 'NOT'),
        'g11462': ('D', 'DATA', '\\', 'DIM', 'STEP'),
        'g11466': ('F', 'SGN', '{', 'FOR', 'TO'),
        'g11470': ('G', 'ABS', '}', 'GOTO', 'THEN'),
        'g11546': ('F', 'SGN', '{', 'FOR', 'TO'),
    }

    keys['g11730'] = make_space()

    for key, definition in arrow_vertical_defs.items():
        keys[key] = make_arrow_vertical(*definition)

    for key, definition in arrow_vertical_alt_defs.items():
        keys[key] = make_arrow_vertical(*definition, background=False)

    for key, definition in arrow_horizontal_defs.items():
        keys[key] = make_arrow_horizontal(*definition)

    for key, definition in arrow_horizontal_alt_defs.items():
        keys[key] = make_arrow_horizontal(*definition, background=False)

    for key, definition in special_defs.items():
        keys[key] = make_special(*definition)

    for key, definition in special_alt_defs.items():
        keys[key] = make_special(*definition, background=False)

    for key, definition in number_defs.items():
        keys[key] = make_number(*definition)

    for key, definition in symbol_defs.items():
        keys[key] = make_letter_symbol(*definition)

    for key, definition in word_defs.items():
        keys[key] = make_letter_word(*definition)

    svg = xml.etree.ElementTree.parse(_KEYBOARD_TEMPLATE)
    frames = None
    cobra = None
    for g in svg.getroot().findall('{http://www.w3.org/2000/svg}g'):
        label = g.attrib['{http://www.inkscape.org/namespaces/inkscape}label']
        if label == 'Key Frames (Not Printed)':
            frames = g
        elif label == 'Cobra':
            cobra = g
    if frames is None:
        print('"Key Frames (Not Printed)" not found')
        return
    if cobra is None:
        print('"Cobra" not found')
        return


    cobra.set('transform', frames.attrib['transform'])
    g = frames.find('{http://www.w3.org/2000/svg}g')
    svg_matrix = g.attrib['transform']
    for g in g.findall('{http://www.w3.org/2000/svg}g'):
        if g.attrib['id'] in keys:
            key = keys[g.attrib['id']]
            translate = template['translate']
            for label, rect in template['rects'].items():
                if 'rects' in key and label in key['rects']:
                    stretch = label == 'background'
                    add_rect(cobra, translate, svg_matrix,
                             copy.deepcopy(rect), copy.deepcopy(g), stretch)

            for label, text in template['texts'].items():
                if label in key['texts']:
                    new_text = copy.deepcopy(text)
                    if type(key['texts'][label]) is tuple:
                        replace_text(new_text, key['texts'][label][0])
                        replace_fill(new_text, key['texts'][label][1])
                    else:
                        replace_text(new_text, key['texts'][label])
                    center = (label.startswith('special ')
                              or label in ['break', 'space'])
                    add_text(cobra, translate, svg_matrix, new_text,
                             copy.deepcopy(g), center)

    svg.write(_KEYBOARD_OUTPUT)

if __name__ == '__main__':
    main()
