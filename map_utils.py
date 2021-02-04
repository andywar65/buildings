import os
import html
from math import radians, sin, cos, asin, acos, degrees, pi, sqrt, pow, fabs, atan2

from django.conf import settings

def get_layer_dict(dxf_f):
    """Gets layer dict from DXF file.

    Skips some default layers. Returns a dict.
    """

    layer_dict = {}
    value = 'dummy'

    while value !='ENTITIES':
        key = dxf_f.readline().strip()
        value = dxf_f.readline().strip()
        if value == 'AcDbLayerTableRecord':#list of layer names
            key = dxf_f.readline().strip()
            name = dxf_f.readline().strip()
            key = dxf_f.readline().strip()
            value = dxf_f.readline().strip()
            key = dxf_f.readline().strip()
            if name == 'Defpoints':
                value = dxf_f.readline().strip()
            else:
                layer_dict[name] = cad2hex(dxf_f.readline().strip())
        #security to avoid loops if file is corrupted
        elif value=='EOF' or key=='':
            return

    return layer_dict

def parse_dxf(dxf_f):
    """Collects entities from DXF file.

    This function does too many things and maybe should be cut down. Scans
    file for 3Dfaces, lines, polylines and blocks. Assigns values to each
    entity, including geometric and appearance values plus functional
    attributes. Returns a nested dictionary.
    """
    #dxf_f = open(page.path_to_dxf, encoding = 'utf-8')

    collection = {}
    flag = False
    x = 0
    value = 'dummy'

    while value !='ENTITIES':
        key = dxf_f.readline().strip()
        value = dxf_f.readline().strip()
        #security to avoid loops if file is corrupted
        if value=='EOF' or key=='':
            return collection

    while value !='ENDSEC':
        key = dxf_f.readline().strip()
        value = dxf_f.readline().strip()
        #security to avoid loops if file is corrupted
        if value=='EOF' or key=='':
            return collection
        #stores values for all entities (with arbitrary axis algorithm)
        if flag == 'ent':
            d = store_entity_values(d, key, value)

        if key == '0':

            if flag == 'ent':#close all other entities

                    if d['ent'] == 'poly':#close polyline
                        d['2'] = 'a-poly'
                        if d['210'] == 0 and d['220'] == 0:
                            d['10'] = d['vx'][0]
                            d['20'] = d['vy'][0]
                            d['30'] = d['38']
                        d['num'] = x
                        collection[x] = d
                        flag = False

                    elif d['ent'] == 'line':#close line
                        d['2'] = 'a-line'
                        d['num'] = x
                        collection[x] = d
                        flag = False

                    elif d['ent'] == 'circle':#close line
                        d['2'] = 'a-circle'
                        d['num'] = x
                        collection[x] = d
                        flag = False

            if value == 'LINE':#start line
                d = {'ent': 'line', '30': 0, '31': 0, '39': 0, '41': 1, '42': 1, '43': 1,
                '50': 0, '210': 0, '220': 0, '230': 1, }
                flag = 'ent'
                x += 1

            elif value == 'LWPOLYLINE':#start polyline
                #default values
                d = {'ent': 'poly', '38': 0,  '39': 0, '41': 1, '42': 1,
                '43': 1, '50': 0, '70': False, '210': 0, '220': 0, '230': 1,
                'vx': [], 'vy': [], }
                flag = 'ent'
                x += 1

            elif value == 'CIRCLE':#start circle
                #default values
                d = {'ent': 'circle',}
                flag = 'ent'
                x += 1

    return collection

def store_entity_values(d, key, value):
    if key == '2':#block name
        d[key] =  html.escape(value, quote=True)
    if key == '8':#layer name
        d['layer'] = d[key] =  html.escape(value, quote=True)
    elif key == '10':#X position
        if d['ent'] == 'poly':
            d['vx'].append(float(value))
        else:
            d[key] = float(value)
    elif key == '20':#mirror Y position
        if d['ent'] == 'poly':
            d['vy'].append(-float(value))
        else:
            d[key] = -float(value)
    elif key == '11' or key == '12' or key == '13':#X position
        d[key] = float(value)
    elif key == '21' or key == '22' or key == '23':#mirror Y position
        d[key] = -float(value)
    elif key == '30' or key == '31' or key == '32' or key == '33':#Z position
        d[key] = float(value)
    elif key == '38' or  key == '39':#elevation and thickness
        d[key] = float(value)
    elif key == '40':#radius
        d[key] = float(value)
    elif key == '41' or key == '42' or key == '43':#scale values
        d[key] = float(value)
    elif key == '50':#Z rotation
        d[key] = float(value)
    elif key == '62':#color
        d['COLOR'] = cad2hex(value)
    elif key == '70' and value == '1':#closed
        d['70'] = True
    elif key == '90':#vertex num
        d[key] = int(value)
    elif key == '210':#X of OCS unitary vector
        d['Az_1'] = float(value)
        if d['ent'] == 'poly':
            d['10'] = d['vx'][0]
        d['P_x'] = d['10']
    elif key == '220':#Y of OCS unitary vector
        d['Az_2'] = float(value)
        if d['ent'] == 'poly':
            d['20'] = d['vy'][0]
        d['P_y'] = -d['20']#reset original value
    elif key == '230':#Z of OCS unitary vector
        d['Az_3'] = float(value)
        if d['ent'] == 'poly':
            d['30'] = d.get('38', 0)
            d['50'] = 0
        d['P_z'] = d['30']
        d = arbitrary_axis_algorithm(d)

    return d

def arbitrary_axis_algorithm(d):
    #see if OCS z vector is close to world Z axis
    if fabs(d['Az_1']) < (1/64) and fabs(d['Az_2']) < (1/64):
        W = ('Y', 0, 1, 0)
    else:
        W = ('Z', 0, 0, 1)
    #cross product for OCS x arbitrary vector, normalized
    Ax_1 = W[2]*d['Az_3']-W[3]*d['Az_2']
    Ax_2 = W[3]*d['Az_1']-W[1]*d['Az_3']
    Ax_3 = W[1]*d['Az_2']-W[2]*d['Az_1']
    Norm = sqrt(pow(Ax_1, 2)+pow(Ax_2, 2)+pow(Ax_3, 2))
    Ax_1 = Ax_1/Norm
    Ax_2 = Ax_2/Norm
    Ax_3 = Ax_3/Norm
    #cross product for OCS y arbitrary vector, normalized
    Ay_1 = d['Az_2']*Ax_3-d['Az_3']*Ax_2
    Ay_2 = d['Az_3']*Ax_1-d['Az_1']*Ax_3
    Ay_3 = d['Az_1']*Ax_2-d['Az_2']*Ax_1
    Norm = sqrt(pow(Ay_1, 2)+pow(Ay_2, 2)+pow(Ay_3, 2))
    Ay_1 = Ay_1/Norm
    Ay_2 = Ay_2/Norm
    Ay_3 = Ay_3/Norm
    #insertion world coordinates from OCS
    d['10'] = d['P_x']*Ax_1+d['P_y']*Ay_1+d['P_z']*d['Az_1']
    d['20'] = d['P_x']*Ax_2+d['P_y']*Ay_2+d['P_z']*d['Az_2']
    d['30'] = d['P_x']*Ax_3+d['P_y']*Ay_3+d['P_z']*d['Az_3']

    #OCS X vector translated into WCS
    Ax_1 = ((d['P_x']+cos(radians(d['50'])))*Ax_1+(d['P_y']+sin(radians(d['50'])))*Ay_1+d['P_z']*d['Az_1'])-d['10']
    Ax_2 = ((d['P_x']+cos(radians(d['50'])))*Ax_2+(d['P_y']+sin(radians(d['50'])))*Ay_2+d['P_z']*d['Az_2'])-d['20']
    Ax_3 = ((d['P_x']+cos(radians(d['50'])))*Ax_3+(d['P_y']+sin(radians(d['50'])))*Ay_3+d['P_z']*d['Az_3'])-d['30']
    #cross product for OCS y vector, normalized
    Ay_1 = d['Az_2']*Ax_3-d['Az_3']*Ax_2
    Ay_2 = d['Az_3']*Ax_1-d['Az_1']*Ax_3
    Ay_3 = d['Az_1']*Ax_2-d['Az_2']*Ax_1
    Norm = sqrt(pow(Ay_1, 2)+pow(Ay_2, 2)+pow(Ay_3, 2))
    Ay_1 = Ay_1/Norm
    Ay_2 = Ay_2/Norm
    Ay_3 = Ay_3/Norm

    #A-Frame rotation order is Yaw(Z), Pitch(X) and Roll(Y)
    #thanks for help Marilena Vendittelli and https://www.geometrictools.com/
    if Ay_3<1:
        if Ay_3>-1:
            pitch = asin(Ay_3)
            yaw = atan2(-Ay_1, Ay_2)
            roll = atan2(-Ax_3, d['Az_3'])
        else:
            pitch = -pi/2
            yaw = -atan2(d['Az_1'], Ax_1)
            roll = 0
    else:
        pitch = pi/2
        yaw = atan2(d['Az_1'], Ax_1)
        roll = 0

    #Y position, mirrored
    d['20'] = -d['20']
    #rotations from radians to degrees
    d['210'] = degrees(pitch)
    d['50'] = degrees(yaw)
    d['220'] = -degrees(roll)

    return d

def transform_collection(collection, layer_dict, lat, long):
    map_objects = []
    #objects are very small with respect to earth, so our transformation
    #from CAD x,y coords to latlong is approximate
    gy = 1 / (6371*2*pi*1000/360)
    gx = 1 / (6371*2*pi*fabs(cos(radians(lat)))*1000/360)
    handled_objects = ['poly', 'line', 'circle']
    for key, val in collection.items():
        if not val['ent'] in handled_objects:
            continue
        object = {}
        object['popup'] = val['layer']
        if 'COLOR' in val:
            object['color'] = val['COLOR']
        else:
            object['color'] = layer_dict[object['popup']]
        object['coords'] = []
        if val['ent'] == 'poly':
            if val['70']:
                object['type'] = 'polygon'
            else:
                object['type'] = 'polyline'

            for i in range(val['90']):
                object['coords'].append([lat-(val['vy'][i]*gy),
                    long+(val['vx'][i]*gx)])
        elif val['ent'] == 'line':
            object['type'] = 'polyline'
            object['coords'].append([lat-(val['20']*gy),
                long+(val['10']*gx)])
            object['coords'].append([lat-(val['21']*gy),
                long+(val['11']*gx)])
        elif val['ent'] == 'circle':
            object['type'] = 'circle'
            object['coords'] = [lat-(val['20']*gy),
                long+(val['10']*gx)]
            object['radius'] = val['40']

        map_objects.append(object)
    return map_objects

def workflow(dxf, lat, long):
    with open(os.path.join(settings.MEDIA_ROOT, dxf.path)) as dxf_f:
        #extract layer names and colors
        layer_dict = get_layer_dict(dxf_f)
        #rewind dxf file
        dxf_f.seek(0)
        #extract entities according to another project:
        #https://github.com/andywar65/architettura/
        collection = parse_dxf(dxf_f)
        #transform to our needings
        map_objects = transform_collection(collection, layer_dict, lat, long)

    return map_objects

def cad2hex(cad_color):
    cad_color = abs(int(cad_color))
    if cad_color<0 or cad_color>255:
        return '#ffffff'
    else:
        RGB_list = (
        		 (0, 0, 0),
        		 (255, 0, 0),
        		 (255, 255, 0),
        		 (0, 255, 0),
        		 (0, 255, 255),
        		 (0, 0, 255),
        		 (255, 0, 255),
        		 (255, 255, 255),
        		 (128, 128, 128),
        		 (192, 192, 192),
        		 (255, 0, 0),
        		 (255, 127, 127),
        		 (165, 0, 0),
        		 (165, 82, 82),
        		 (127, 0, 0),
        		 (127, 63, 63),
        		 (76, 0, 0),
        		 (76, 38, 38),
        		 (38, 0, 0),
        		 (38, 19, 19),
        		 (255, 63, 0),
        		 (255, 159, 127),
        		 (165, 41, 0),
        		 (165, 103, 82),
        		 (127, 31, 0),
        		 (127, 79, 63),
        		 (76, 19, 0),
        		 (76, 47, 38),
        		 (38, 9, 0),
        		 (38, 23, 19),
        		 (255, 127, 0),
        		 (255, 191, 127),
        		 (165, 82, 0),
        		 (165, 124, 82),
        		 (127, 63, 0),
        		 (127, 95, 63),
        		 (76, 38, 0),
        		 (76, 57, 38),
        		 (38, 19, 0),
        		 (38, 28, 19),
        		 (255, 191, 0),
        		 (255, 223, 127),
        		 (165, 124, 0),
        		 (165, 145, 82),
        		 (127, 95, 0),
        		 (127, 111, 63),
        		 (76, 57, 0),
        		 (76, 66, 38),
        		 (38, 28, 0),
        		 (38, 33, 19),
        		 (255, 255, 0),
        		 (255, 255, 127),
        		 (165, 165, 0),
        		 (165, 165, 82),
        		 (127, 127, 0),
        		 (127, 127, 63),
        		 (76, 76, 0),
        		 (76, 76, 38),
        		 (38, 38, 0),
        		 (38, 38, 19),
        		 (191, 255, 0),
        		 (223, 255, 127),
        		 (124, 165, 0),
        		 (145, 165, 82),
        		 (95, 127, 0),
        		 (111, 127, 63),
        		 (57, 76, 0),
        		 (66, 76, 38),
        		 (28, 38, 0),
        		 (33, 38, 19),
        		 (127, 255, 0),
        		 (191, 255, 127),
        		 (82, 165, 0),
        		 (124, 165, 82),
        		 (63, 127, 0),
        		 (95, 127, 63),
        		 (38, 76, 0),
        		 (57, 76, 38),
        		 (19, 38, 0),
        		 (28, 38, 19),
        		 (63, 255, 0),
        		 (159, 255, 127),
        		 (41, 165, 0),
        		 (103, 165, 82),
        		 (31, 127, 0),
        		 (79, 127, 63),
        		 (19, 76, 0),
        		 (47, 76, 38),
        		 (9, 38, 0),
        		 (23, 38, 19),
        		 (0, 255, 0),
        		 (127, 255, 127),
        		 (0, 165, 0),
        		 (82, 165, 82),
        		 (0, 127, 0),
        		 (63, 127, 63),
        		 (0, 76, 0),
        		 (38, 76, 38),
        		 (0, 38, 0),
        		 (19, 38, 19),
        		 (0, 255, 63),
        		 (127, 255, 159),
        		 (0, 165, 41),
        		 (82, 165, 103),
        		 (0, 127, 31),
        		 (63, 127, 79),
        		 (0, 76, 19),
        		 (38, 76, 47),
        		 (0, 38, 9),
        		 (19, 38, 23),
        		 (0, 255, 127),
        		 (127, 255, 191),
        		 (0, 165, 82),
        		 (82, 165, 124),
        		 (0, 127, 63),
        		 (63, 127, 95),
        		 (0, 76, 38),
        		 (38, 76, 57),
        		 (0, 38, 19),
        		 (19, 38, 28),
        		 (0, 255, 191),
        		 (127, 255, 223),
        		 (0, 165, 124),
        		 (82, 165, 145),
        		 (0, 127, 95),
        		 (63, 127, 111),
        		 (0, 76, 57),
        		 (38, 76, 66),
        		 (0, 38, 28),
        		 (19, 38, 33),
        		 (0, 255, 255),
        		 (127, 255, 255),
        		 (0, 165, 165),
        		 (82, 165, 165),
        		 (0, 127, 127),
        		 (63, 127, 127),
        		 (0, 76, 76),
        		 (38, 76, 76),
        		 (0, 38, 38),
        		 (19, 38, 38),
        		 (0, 191, 255),
        		 (127, 223, 255),
        		 (0, 124, 165),
        		 (82, 145, 165),
        		 (0, 95, 127),
        		 (63, 111, 127),
        		 (0, 57, 76),
        		 (38, 66, 76),
        		 (0, 28, 38),
        		 (19, 33, 38),
        		 (0, 127, 255),
        		 (127, 191, 255),
        		 (0, 82, 165),
        		 (82, 124, 165),
        		 (0, 63, 127),
        		 (63, 95, 127),
        		 (0, 38, 76),
        		 (38, 57, 76),
        		 (0, 19, 38),
        		 (19, 28, 38),
        		 (0, 63, 255),
        		 (127, 159, 255),
        		 (0, 41, 165),
        		 (82, 103, 165),
        		 (0, 31, 127),
        		 (63, 79, 127),
        		 (0, 19, 76),
        		 (38, 47, 76),
        		 (0, 9, 38),
        		 (19, 23, 38),
        		 (0, 0, 255),
        		 (127, 127, 255),
        		 (0, 0, 165),
        		 (82, 82, 165),
        		 (0, 0, 127),
        		 (63, 63, 127),
        		 (0, 0, 76),
        		 (38, 38, 76),
        		 (0, 0, 38),
        		 (19, 19, 38),
        		 (63, 0, 255),
        		 (159, 127, 255),
        		 (41, 0, 165),
        		 (103, 82, 165),
        		 (31, 0, 127),
        		 (79, 63, 127),
        		 (19, 0, 76),
        		 (47, 38, 76),
        		 (9, 0, 38),
        		 (23, 19, 38),
        		 (127, 0, 255),
        		 (191, 127, 255),
        		 (82, 0, 165),
        		 (124, 82, 165),
        		 (63, 0, 127),
        		 (95, 63, 127),
        		 (38, 0, 76),
        		 (57, 38, 76),
        		 (19, 0, 38),
        		 (28, 19, 38),
        		 (191, 0, 255),
        		 (223, 127, 255),
        		 (124, 0, 165),
        		 (145, 82, 165),
        		 (95, 0, 127),
        		 (111, 63, 127),
        		 (57, 0, 76),
        		 (66, 38, 76),
        		 (28, 0, 38),
        		 (33, 19, 38),
        		 (255, 0, 255),
        		 (255, 127, 255),
        		 (165, 0, 165),
        		 (165, 82, 165),
        		 (127, 0, 127),
        		 (127, 63, 127),
        		 (76, 0, 76),
        		 (76, 38, 76),
        		 (38, 0, 38),
        		 (38, 19, 38),
        		 (255, 0, 191),
        		 (255, 127, 223),
        		 (165, 0, 124),
        		 (165, 82, 145),
        		 (127, 0, 95),
        		 (127, 63, 111),
        		 (76, 0, 57),
        		 (76, 38, 66),
        		 (38, 0, 28),
        		 (38, 19, 33),
        		 (255, 0, 127),
        		 (255, 127, 191),
        		 (165, 0, 82),
        		 (165, 82, 124),
        		 (127, 0, 63),
        		 (127, 63, 95),
        		 (76, 0, 38),
        		 (76, 38, 57),
        		 (38, 0, 19),
        		 (38, 19, 28),
        		 (255, 0, 63),
        		 (255, 127, 159),
        		 (165, 0, 41),
        		 (165, 82, 103),
        		 (127, 0, 31),
        		 (127, 63, 79),
        		 (76, 0, 19),
        		 (76, 38, 47),
        		 (38, 0, 9),
        		 (38, 19, 23),
        		 (0, 0, 0),
        		 (51, 51, 51),
        		 (102, 102, 102),
        		 (153, 153, 153),
        		 (204, 204, 204),
        		 (255, 255, 255),
        		)
        r = RGB_list[cad_color][0]
        g = RGB_list[cad_color][1]
        b = RGB_list[cad_color][2]
        hex = "#{:02x}{:02x}{:02x}".format(r,g,b)
        return hex
