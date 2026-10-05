#!/bin/env python


from .classes import Element, Style
from . import primitives 


# Some colors/styles for elements
# (GLOBAL - which is a bit hacky....fix with yaml/config later)
red = Style(
    face_color=(180, 60, 50),
    edge_color=(80, 20, 20),
    edge_width=2,
    show_edges=False,               # not if cylinder
)

blue = Style(
    face_color=(70, 110, 180),
    edge_color=(20, 40, 80),
    edge_width=2,
)

yellow_RGB = (200, 200, 50)


#-------------------------------------------------------------------------------
def create_world(params):
    """ Work backward up the heirachical tree to construct the work """

    # Flat 2d plane environment (what units? Map to physical "mm", thus 30x40m field?
    field_length = params["field"]["length"]
    field_width = params["field"]["width"]
    g = primitives.geom2d(primitives.points_rectangle,x=field_length, y=field_width)
    field = Element('field',geometry=g)

    # A table
    table = create_table(params["table"])
    field.add(table)
    #
    player_length = 1000
    player_pos = (5000,5000,100)
    player = Element('player', geometry=primitives.cube(player_length), style=blue,)
    field.add(player, position=player_pos,)

    # World constructor
    world = Element('world')
    world.add(field)

    return world



def create_table(params, filename=None, save=False):
    if filename is not None:
        table = Element.load(filename)
        return table

    # Define reusable geometry
    length = params["length"]
    width = params["width"]
    height = params["height"]
    leg_thick = params["leg_thick"]
    top_thick = params["top_thick"]

    leg = Element('leg', geometry=primitives.cylinder(leg_thick/2, height), style=red)
    top = Element('top', geometry=primitives.rectangle(length, width, top_thick), style=blue)

    # Create the table assembly
    table = Element('table')

    o_leg = (0, 0, 0)
    x0 = 0
    y0 = 0
    x1 = width - leg_thick
    y1 = width - leg_thick
    table.add( leg, name='leg_SW',position=(x0, y0, 0), orientation=o_leg)       # SW
    table.add( leg, name='leg_SE',position=(x1, y0, 0), orientation=o_leg)       # SE
    table.add( leg, name='leg_NW',position=(x0, y1, 0), orientation=o_leg)       # NW
    table.add( leg, name='leg_NE',position=(x1, y1, 0), orientation=o_leg)       # NE
    leg_mid = table.add( leg, name='leg_mid',position=(0.5*x1, y1, 0), orientation=o_leg)   # extra leg at the back
    table.add( top, name='top'  ,position=( 0,  0, height), orientation=(0, 0, 0))

    leg_mid.style.face_color = yellow_RGB   # change color of the mid leg

    # Save the object as a json file
    if save:
        if filename is None:
            filename = 'table.json'
        print('SAVING: ',filename)
        table.save(filename)
    return table

