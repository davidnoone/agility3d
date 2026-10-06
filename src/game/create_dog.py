#
# dog.py
#
# Simple skeletal dog model.
#
# The skeleton is a graph of:
#
#     Joint ---- Connection ---- Joint
#
# A Beam is a rigid Connection.
#
# For the initial renderer representation, every Beam is
# converted to a cylinder Element.
#
# Later, Skeleton can be animated independently of rendering.
#
import numpy as np
from .classes import  Skeleton

# ======================================================================
# DOG - fuly parametric
# ======================================================================
def create_dog():

    skeleton = Skeleton("dog")

    # ==================================================================
    # DOG SKELETON
    #
    # Coordinate system:
    #
    #     x = left / right
    #     y = front / rear
    #     z = up
    #
    #     +y = front of dog
    #     -y = rear of dog
    #
    # All dimensions are in mm.
    #
    #
    #                              o nose
    #                             /
    #                       o head
    #                      /     \
    #                     /       o chin
    #                    /
    #                   o axis
    #                   |
    #                   | neck_upper
    #                   |
    #                   o WITHERS
    #                   |
    #                   | thoracic
    #                   |
    #                   o ribbase
    #                   |
    #                   | upper_lumbar
    #                   |
    #                   o lumbar
    #                   |
    #                   | lower_lumbar
    #                   |
    #                   o pelvis
    #                  / \
    #                 /   \
    #
    # REAR LEG
    #
    #                o hip
    #                 \
    #                  o stifle
    #                   \
    #                    o hock
    #                     \
    #                      o paw
    #                       \
    #                        o tow
    #
    #
    # FRONT LEG
    #
    #                o shoulder
    #                  \
    #                   o elbow
    #                    \
    #                     o wrist
    #                      \
    #                       o paw
    #                        \
    #                         o tow
    #
    #
    # TAIL
    #
    #                o pelvis
    #                  \
    #                   o tail_1
    #                    \
    #                     o tail_2
    #                      \
    #                       o tail_3
    #                        \
    #                         o tail_4
    #
    #
    # The left and right legs are mirror images in x.
    #
    # The skeleton represents the kinematic structure required for
    # locomotion and animation, rather than every anatomical bone.
    #
    # ==================================================================


    # ==================================================================
    # BODY PROPORTIONS
    # ==================================================================

    body_length = 720
    body_height = 570

    withers_y = 0

    rib_fraction = 0.30
    lumbar_fraction = 0.70

    pelvis_z_offset = -30
    lumbar_z_offset = -60
    rib_z_offset = -20

    pelvis_y = withers_y - body_length
    lumbar_y = withers_y - lumbar_fraction * body_length
    rib_y = withers_y - rib_fraction * body_length

    pelvis_z = body_height + pelvis_z_offset
    lumbar_z = body_height + lumbar_z_offset
    rib_z = body_height + rib_z_offset
    withers_z = body_height


    # ==================================================================
    # MAIN BODY / SPINE
    # ==================================================================

    withers = skeleton.add_joint("withers", [0, withers_y, withers_z])
    ribbase = skeleton.add_joint("ribbase", [0, rib_y, rib_z])
    lumbar = skeleton.add_joint("lumbar", [0, lumbar_y, lumbar_z])
    pelvis = skeleton.add_joint("pelvis", [0, pelvis_y, pelvis_z])

    skeleton.add_beam("thoracic", ribbase, withers, radius=85)
    skeleton.add_beam("upper_lumbar", lumbar, ribbase, radius=85)
    skeleton.add_beam("lower_lumbar", pelvis, lumbar, radius=85)


    # ==================================================================
    # PELVIS / HIPS
    #
    # Pelvis is the central body joint.
    # Hip points are lateral attachment points for the rear legs.
    # ==================================================================

    hip_width = 180
    hip_back = 90
    hip_drop = 90      # drop defined + down

    hip_L = skeleton.add_joint("hip_L", [-hip_width, pelvis_y - hip_back, pelvis_z - hip_drop])
    hip_R = skeleton.add_joint("hip_R", [hip_width, pelvis_y - hip_back, pelvis_z - hip_drop])

    skeleton.add_beam("pelvis_L", pelvis, hip_L, radius=60)
    skeleton.add_beam("pelvis_R", pelvis, hip_R, radius=60)


    # ==================================================================
    # REAR LEGS
    #
    #     hip
    #      \
    #       o stifle
    #        \
    #         o hock
    #          \
    #           o paw
    #            \
    #             o tow
    #
    # upper_rear = femur
    # lower_rear = tibia / fibula
    # tarsal      = metatarsals
    # paw_rear    = phalanges
    # ==================================================================

    rear_upper = 320
    rear_lower = 200
    rear_tarsal = 150
    rear_paw = 80

    rear_stifle_y = 170
    rear_hock_y = -20
    rear_paw_y = 50
    rear_tow_y = 70

    rear_tow_z = 35

    def make_rear_leg(side, x):

        hip = hip_L if side == "L" else hip_R

        # --------------------------------------------------------------
        # Stifle / knee
        # --------------------------------------------------------------

        stifle_y = pelvis_y + rear_stifle_y
        stifle_dy = stifle_y - hip.position[1]
        stifle_z = hip.position[2] - np.sqrt(rear_upper**2 - stifle_dy**2)

        stifle = skeleton.add_joint(f"stifle_{side}", [x, stifle_y, stifle_z])

        # --------------------------------------------------------------
        # Hock
        # --------------------------------------------------------------

        hock_y = pelvis_y + rear_hock_y
        hock_dy = hock_y - stifle_y
        hock_z = stifle_z - np.sqrt(rear_lower**2 - hock_dy**2)

        hock = skeleton.add_joint(f"hock_{side}", [x, hock_y, hock_z])

        # --------------------------------------------------------------
        # Paw (connection point)
        #
        # This is the proximal end of the paw/phalangeal structure.
        # The paw -> tow beam represents the phalanges.
        # --------------------------------------------------------------

        paw_y = pelvis_y + rear_paw_y
        paw_z = hock_z - np.sqrt(rear_tarsal**2 - (paw_y - hock_y)**2)

        paw = skeleton.add_joint(f"paw_rear_{side}", [x, paw_y, paw_z])

        # --------------------------------------------------------------
        # Tow: Terminal skeletal point used as the foot/ground contact point.
        # --------------------------------------------------------------
        tow_y = pelvis_y + rear_tow_y
        tow = skeleton.add_joint(f"tow_rear_{side}", [x, tow_y, rear_tow_z])

        # --------------------------------------------------------------
        # Connections
        # --------------------------------------------------------------
        skeleton.add_beam(f"upper_rear_{side}", hip   , stifle, radius=55)
        skeleton.add_beam(f"lower_rear_{side}", stifle, hock  , radius=45)
        skeleton.add_beam(f"tarsal_{side}"    , hock  , paw   , radius=40)
        skeleton.add_beam(f"paw_rear_{side}"  , paw   , tow   , radius=35)


    make_rear_leg("L", -hip_width)
    make_rear_leg("R", hip_width)


    # ==================================================================
    # SHOULDERS
    #
    # The shoulder represents the effective scapular attachment point.
    # ==================================================================

    shoulder_width = 180
    shoulder_back = 0      # minus, as want forward, but negative givs NAN...
    shoulder_drop = 120

    shoulder_L = skeleton.add_joint("shoulder_L", [-shoulder_width, withers_y - shoulder_back, withers_z - shoulder_drop])
    shoulder_R = skeleton.add_joint("shoulder_R", [shoulder_width, withers_y - shoulder_back, withers_z - shoulder_drop])

    skeleton.add_beam("scapula_L", withers, shoulder_L, radius=60)
    skeleton.add_beam("scapula_R", withers, shoulder_R, radius=60)


    # ==================================================================
    # FRONT LEGS
    #
    #     shoulder
    #        \
    #         o elbow
    #          \
    #           o wrist
    #            \
    #             o paw
    #              \
    #               o tow
    #
    # upper_front = humerus
    # lower_front = radius / ulna
    # carpal      = metacarpals
    # paw_front   = phalanges
    # ==================================================================

    front_upper = 300
    front_lower = 300


    front_carpal = 180
    front_paw = 80

    front_elbow_y = -260
    front_wrist_y = -90
    front_paw_y = 60
    front_tow_y = 80
    front_tow_z = 0    # on the ground



    def make_front_leg(side, x):
        shoulder = shoulder_L if side == "L" else shoulder_R

        # --------------------------------------------------------------
        # Elbow
        # --------------------------------------------------------------
        elbow_y = withers_y + front_elbow_y
        elbow_dy = elbow_y - shoulder.position[1]
        elbow_z = shoulder.position[2] - np.sqrt(front_upper**2 - elbow_dy**2)

        elbow = skeleton.add_joint(f"elbow_{side}", [x, elbow_y, elbow_z])

        # --------------------------------------------------------------
        # Wrist
        # --------------------------------------------------------------
        wrist_y = withers_y + front_wrist_y
        wrist_dy = wrist_y - elbow_y
        wrist_z = elbow_z - np.sqrt(front_lower**2 - wrist_dy**2)

        wrist = skeleton.add_joint(f"wrist_{side}", [x, wrist_y, wrist_z])

        # --------------------------------------------------------------
        # Paw
        # --------------------------------------------------------------
        paw_y = withers_y + front_paw_y
        paw_z = wrist_z - np.sqrt(front_carpal**2 - (paw_y - wrist_y)**2)

        paw = skeleton.add_joint(f"paw_front_{side}", [x, paw_y, paw_z])

        # --------------------------------------------------------------
        # Tow
        # --------------------------------------------------------------
        tow_y = withers_y + front_tow_y
        tow = skeleton.add_joint(f"tow_front_{side}", [x, tow_y, front_tow_z])

        # --------------------------------------------------------------
        # Connections
        # --------------------------------------------------------------

        skeleton.add_beam(f"upper_front_{side}", shoulder, elbow, radius=50)
        skeleton.add_beam(f"lower_front_{side}", elbow, wrist, radius=42)
        skeleton.add_beam(f"carpal_{side}", wrist, paw, radius=38)
        skeleton.add_beam(f"paw_front_{side}", paw, tow, radius=35)


    make_front_leg("L", -shoulder_width)
    make_front_leg("R", shoulder_width)


    # ==================================================================
    # NECK / HEAD
    #
    #              o nose
    #             /
    #        o head
    #       /    \
    #      /      o chin
    #     /
    #    o axis
    #    |
    #    |
    #    o withers
    #
    # There are only two neck/head connections:
    #
    #     withers -> axis
    #     axis    -> head
    #
    # nose and chin are geometric endpoints rather than additional
    # articulated joints.
    # ==================================================================

    axis_y = 150
    axis_z_offset = 100

    head_y_offset = 150
    head_z_offset = 130

    nose_y_offset = 250
    nose_z_offset = 100

    chin_y_offset = 180
    chin_z_offset = 60

    axis = skeleton.add_joint("axis", [0, axis_y, body_height + axis_z_offset])

    head = skeleton.add_joint("head", [0, axis_y + head_y_offset, body_height + head_z_offset])

    nose = skeleton.add_joint("nose", [0, axis_y + head_y_offset + nose_y_offset, body_height + nose_z_offset])

    chin = skeleton.add_joint("chin", [0, axis_y + head_y_offset + chin_y_offset, body_height + chin_z_offset])

    skeleton.add_beam("neck_lower", withers, axis, radius=75)
    skeleton.add_beam("neck_upper", axis, head, radius=70)
    skeleton.add_beam("skull", head, nose, radius=55)
    skeleton.add_beam("jaw", head, chin, radius=35)


    # ==================================================================
    # TAIL
    #
    # The tail is an explicit chain so that future animation can apply
    # progressively increasing rotations from the pelvis to the tip.
    # ==================================================================

    tail_length = 600

    tail_1_fraction = 0.25
    tail_2_fraction = 0.25
    tail_3_fraction = 0.25
    tail_4_fraction = 0.25

    tail_1_z_offset = -100
    tail_2_z_offset = -150
    tail_3_z_offset = -100
    tail_4_z_offset = -50

    tail_1_y = pelvis_y - tail_length * tail_1_fraction
    tail_2_y = tail_1_y - tail_length * tail_2_fraction
    tail_3_y = tail_2_y - tail_length * tail_3_fraction
    tail_4_y = tail_3_y - tail_length * tail_4_fraction

    tail_1 = skeleton.add_joint("tail_1", [0, tail_1_y, pelvis_z + tail_1_z_offset])
    tail_2 = skeleton.add_joint("tail_2", [0, tail_2_y, pelvis_z + tail_2_z_offset])
    tail_3 = skeleton.add_joint("tail_3", [0, tail_3_y, pelvis_z + tail_3_z_offset])
    tail_4 = skeleton.add_joint("tail_4", [0, tail_4_y, pelvis_z + tail_4_z_offset])

    skeleton.add_beam("tail_base", pelvis, tail_1, radius=55)
    skeleton.add_beam("tail_1", tail_1, tail_2, radius=48)
    skeleton.add_beam("tail_2", tail_2, tail_3, radius=40)
    skeleton.add_beam("tail_3", tail_3, tail_4, radius=30)


    # ==================================================================
    # CONVERT SKELETON -> RENDERABLE ELEMENT
    # ==================================================================

    skeleton.print_graph()
    dog = skeleton.to_element()

    return dog
