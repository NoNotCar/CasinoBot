import colorsys
def rgb2hsv(rgb):
    rgb=tuple(n/255.0 for n in rgb)
    return colorsys.rgb_to_hsv(*rgb)
def hsv2rgb(hsv):
    rgb=colorsys.hsv_to_rgb(*hsv)
    return tuple(int(n * 255) for n in rgb)
def darker(col,fract=0.5):
    return tuple(int(c*fract) for c in col)
def lighter(col,fract=0.5):
    return tuple(int(c+(255-c)*fract) for c in col)