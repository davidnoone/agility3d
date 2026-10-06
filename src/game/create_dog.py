#
# dog.py
#
# "Simple" parametric skeletal dog model.
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
import numpy as np
import yaml

from .classes import Skeleton, Pose



# ======================================================================
# DOG - fully parametric
# ======================================================================
def create_dog(filename=None):

    filename = '/game/assets/config_dog.yaml' if filename is None else filename
#    filename = './assets/config_dog.yaml' if filename is None else filename
    with open(filename, 'r') as file:
        p = yaml.safe_load(file)['dog']['skeleton']

    skeleton = Skeleton("dog")

    # ==============================================================
    # Joints
    # ==============================================================

    # Spine: withers is the reference point for the dog: [0, 0, 0]
    skeleton.add_joint("withers")
    skeleton.add_joint("ribs")
    skeleton.add_joint("lumbar")
    skeleton.add_joint("pelvis")

    # Head / neck
    skeleton.add_joint("axis")
    skeleton.add_joint("head")
    skeleton.add_joint("nose")
    skeleton.add_joint("chin")

    # Tail
    for i in range(p["tail_segments"]):
        skeleton.add_joint(f"tail_{i+1}")

    # Left and right legs
    for LorR in ['L', 'R']:
        skeleton.add_joint("shoulder_"+LorR)
        skeleton.add_joint("elbow_"+LorR)
        skeleton.add_joint("wrist_"+LorR)
        skeleton.add_joint("paw_front_"+LorR)
        skeleton.add_joint("toe_front_"+LorR)

        skeleton.add_joint("hip_"+LorR)
        skeleton.add_joint("stifle_"+LorR)
        skeleton.add_joint("hock_"+LorR)
        skeleton.add_joint("paw_rear_"+LorR)
        skeleton.add_joint("toe_rear_"+LorR)

    # ==============================================================
    # MAIN BODY / SPINE
    # ==============================================================
    length = p['length_to_pelvis']

    rib_length = p['rib_fraction'] * length
    lumbar_length = p['lumbar_fraction'] * length
    pelvis_length = (1 - p['lumbar_fraction']) * length

    skeleton.add_bone("thoracic", "withers", "ribs", rib_length, radius=120)
    skeleton.add_bone("upper_lumbar", "ribs", "lumbar", lumbar_length, radius=90)
    skeleton.add_bone("lower_lumbar", "lumbar", "pelvis", pelvis_length, radius=70)

    # ==============================================================
    # NECK / HEAD
    # ==============================================================
    skeleton.add_bone("neck_lower", "withers", "axis", p['neck_length'], radius=70)
    skeleton.add_bone("neck_upper", "axis", "head", p['axis_length'], radius=50)
    skeleton.add_bone("skull", "head", "nose", p['skull_length'], radius=55)
    skeleton.add_bone("jaw", "head", "chin", p['jaw_length'], radius=35)

    # ==============================================================
    # TAIL
    # ==============================================================
    tail_length = p["tail_length"] / p["tail_segments"]

    previous = "pelvis"
    for i in range(p["tail_segments"]):
        child = f"tail_{i+1}"
        radius = 40 - 20 * i / p["tail_segments"]
        skeleton.add_bone(f"tail_{i+1}", previous, child, tail_length, radius=radius)
        previous = child

    # ==============================================================
    # FRONT/REAR LEGS
    # ==============================================================
    for LorR in ['L', 'R']:
#        skeleton.add_bone("shoulder_"+LorR, "withers", "shoulder_"+LorR,  0.5*p['shoulder_width'], radius=45)
#        skeleton.add_bone("humerours_"+LorR, "shoulder_"+LorR, "elbow_"+LorR, p['front_upper'], radius=45)
        skeleton.add_bone("humerours_"+LorR, "shoulder_"+LorR, "elbow_"+LorR, p['front_upper'], radius=45)
        skeleton.add_bone("forearm_"+LorR, "elbow_"+LorR, "wrist_"+LorR, p['front_lower'], radius=35)
        skeleton.add_bone("carpal_"+LorR, "wrist_"+LorR, "paw_front_"+LorR, p['front_carpal'], radius=30)
        skeleton.add_bone("front_paw_"+LorR, "paw_front_"+LorR, "toe_front_"+LorR, p['front_paw'], radius=25)

        # Missig l/r pelvisis!
#        skeleton.add_bone("pelvis_"+LorR, "pelvis", "hip_"+LorR, 0.5*p['hip_width'], radius=40)
        skeleton.add_bone("femur_"+LorR, "hip_"+LorR, "stifle_"+LorR, p['rear_upper'], radius=50)
        skeleton.add_bone("tibia_"+LorR, "stifle_"+LorR, "hock_"+LorR, p['rear_lower'], radius=40)
        skeleton.add_bone("tarsal_"+LorR, "hock_"+LorR, "paw_rear_"+LorR, p['rear_tarsal'], radius=30)
        skeleton.add_bone("rear_paw_"+LorR, "paw_rear_"+LorR, "toe_rear_"+LorR, p['rear_paw'], radius=25)

    # ==============================================================
    skeleton.print_graph()


    # ==============================================================
    # DEFINE  poses

    print('GENERATING POSE: stand')
    pose_stand = create_pose("stand", skeleton, p)
    pose_sit   = create_pose("sit", skeleton, p)
#    dog = skeleton.to_element(pose_sit)
    dog = skeleton.to_element(pose_stand)

    return dog


def create_pose(pose_name, skeleton, p):

    pose = Pose(skeleton, name=pose_name)

    # --------------------------------------------------------------
    # Select pose definition
    # --------------------------------------------------------------
    if pose_name not in p:
        raise ValueError(f"Unknown pose: {pose_name}")

    q = p[pose_name]

    # Reference joint
    pose.set_position("withers", [0.0, 0.0, 0.0])

    # Neck and head (forwards/positive y)
    pose.set_offset("withers", "axis", axis="z", value=q["axis_dz"], sign=+1)
    pose.set_offset("axis"   , "head", axis="z", value=q["head_dz"], sign=+1)

    pose.set_offset("head", "nose", axis="z", value=q["nose_dz"], sign=+1)
    pose.set_offset("head", "chin", axis="z", value=q["chin_dz"], sign=+1)

    # Spine (backwards/negative y)
    pose.set_offset("withers", "ribs"   , axis="z", value=q["rib_dz"]   , sign=-1)
    pose.set_offset("ribs"   , "lumbar" , axis="z", value=q["lumbar_dz"], sign=-1)
    pose.set_offset("lumbar" , "pelvis" , axis="z", value=q["pelvis_dz"], sign=-1)

    # Tail (backward from pelvis, in general)
    previous = "pelvis"
    for i, dz in enumerate(q["tail_dz"], start=1):
        child = f"tail_{i}"
        pose.set_offset(previous, child, axis="z", value=dz, sign=-1)
        previous = child

    # Shoulder attachment points
    withers = pose.position("withers")

    shoulder_width = p["shoulder_width"]
    shoulder_back = p["shoulder_back"]
    shoulder_drop = p["shoulder_drop"]

    pose.set_position("shoulder_L", withers + [
        -shoulder_width / 2,
        shoulder_back,
        -shoulder_drop
    ])

    pose.set_position("shoulder_R", withers + [
         shoulder_width / 2,
         shoulder_back,
        -shoulder_drop
    ])

    # --------------------------------------------------------------
    # Front legs
    # --------------------------------------------------------------
    for LorR in ["L", "R"]:      # down in z
        pose.set_offset(f"shoulder_{LorR}", f"elbow_{LorR}",axis="y", value=q["front_elbow_dy"], sign=-1)
        pose.set_offset(f"elbow_{LorR}", f"wrist_{LorR}",   axis="y", value=q["front_wrist_dy"], sign=-1)
        pose.set_offset(f"wrist_{LorR}", f"paw_front_{LorR}",axis="y", value=q["front_paw_dy"], sign=-1)
        pose.set_offset(f"paw_front_{LorR}", f"toe_front_{LorR}",axis="z", value=q["front_toe_dz"], sign=1) # fwd

    # --------------------------------------------------------------
    # Hip attachment points
    # --------------------------------------------------------------
    pelvis = pose.position("pelvis")

    hip_width = p["hip_width"]
    hip_back = p["hip_back"]
    hip_drop = p["hip_drop"]

    pose.set_position("hip_L", pelvis + [-hip_width/2, hip_back, -hip_drop])
    pose.set_position("hip_R", pelvis + [ hip_width/2, hip_back, -hip_drop])

    # --------------------------------------------------------------
    # Rear legs
    # --------------------------------------------------------------
    for LorR in ["L", "R"]:
        pose.set_offset(f"hip_{LorR}", f"stifle_{LorR}", axis="y", value=q["rear_stifle_dy"], sign=-1)
        pose.set_offset(f"stifle_{LorR}", f"hock_{LorR}", axis="y", value=q["rear_hock_dy"], sign=-1)
        pose.set_offset(f"hock_{LorR}", f"paw_rear_{LorR}", axis="y", value=q["rear_paw_dy"], sign=-1)
        pose.set_offset(f"paw_rear_{LorR}", f"toe_rear_{LorR}", axis="z", value=q["rear_toe_dz"], sign=1) # fwd
        
    # Validate
    pose.validate()

    return pose