# -*- coding: utf-8 -*-
DEBUG = True


""" Alignment constants """
LEFT =       0b000001
RIGHT =      0b000010
HCENTER =    0b000100
TOP =        0b001000
BOTTOM =     0b010000
VCENTER =    0b100000

CENTER = HCENTER + VCENTER
TOPLEFT = TOP + LEFT
TOPRIGHT = TOP + RIGHT
TOPCENTER = TOP + HCENTER
BOTTOMLEFT = BOTTOM + LEFT
BOTTOMRIGHT = BOTTOM + RIGHT 
BOTTOMCENTER = BOTTOM + HCENTER
LEFTCENTER = LEFT + VCENTER
RIGHTCENTER = RIGHT + VCENTER



""" Scene stats """
ACTIVE =     0b000001
QUIT =       0b100000  # scene wants to quit



""" Menu item highlight modes """
LIGHTENUP =  1
SELECTOR  =  2



""" Menu selection modes """
MOUSE    = 1
KEYBOARD = 2



""" Item selection states """
DEFAULT = 0
HOVERED = 1
ACTIVATED = 2



""" Scrolling directions """
SCROLL_UP = 1
SCROLL_DOWN = 2
SCROLL_LEFT = 3
SCROLL_RIGHT = 4