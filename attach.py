# Parse Rig file and build rig

import json
# import warn
import SimpleBaseRigGITHUB.warn as warn
import maya.cmds as cmds

def NameSpace(name, prefix=None):
    return prefix + name if prefix else name

def GetRoot():
    return "EXPORT_RIG"

class Joint(dict):
    def __init__(s, name, *args, **kwargs):
        dict.__init__(s, *args, **kwargs)
        s.name = name

class Safe(object):
    def __enter__(s):
        cmds.undoInfo(openChunk=True)
    def __exit__(s, *err):
        cmds.select(clear=True)
        cmds.undoInfo(closeChunk=True)
        if err[0]: cmds.undo()

class Attach(object):
    def __init__(s, data):
        winName = "Make_Rig"
        if cmds.window(winName, ex=True):
            cmds.deleteUI(winName)
        s.win = cmds.window(rtf=True, w=300, t="Attach Skeleton")
        cmds.columnLayout(adj=True)
        cmds.text(l="Do you need to add a prefix? (optional)")
        prefix = cmds.textField(h=30)
        row = cmds.rowLayout(nc=3, adj=1)
        cmds.separator()
        cmds.button(
            l="Add Prefix",
            c=lambda x: warn(s.buildRig, data, cmds.textField(prefix, q=True, tx=True).strip()))
        cmds.button(
            l="No Prefix",
            c=lambda x: warn(s.buildRig, data, ""))
        cmds.showWindow(s.win)

    def buildRig(s, data, prefix):
        with Safe():
            root = NameSpace(GetRoot(), prefix)

            # Check if root is there. IF so, use it, else create
            if not cmds.objExists(root):
                cmds.group(n=root, em=True)


            # Parse and Validate
            # Types 0 = Spoke, 1 = Root, 2 = Limb, 3 = Singleton, 4 = End Effector
            joints = []
            def parse(data, depth=0):
                children = [a for a in data if a[:1] != "_"]
                childNum = len(children) # How many children have we?
                if childNum:
                    if childNum == 1:
                        if depth: # Limb
                            data["_type"] = 2
                        else: # Limb Root
                            data["_type"] = 1
                        depth += 1
                    else: # Center Spoke
                        data["_type"] = 0
                        depth = 0
                    for c in children:
                        if cmds.objExists(c): raise RuntimeError, "%s already exists. Cannot complete..." % c
                        position = data[c].get("_position", "")
                        rotation = data[c].get("_rotation", "")
                        scale = data[c].get("_scale", "")
                        if not position or not cmds.objExists(position): raise RuntimeError, "%s is missing. Cannot complete..." % position or "An Unspecified Joint"
                        if rotation and not cmds.objExists(rotation): raise RuntimeError, "%s is missing. Cannot complete..." % rotation or "An Unspecified Joint"
                        if scale and not cmds.objExists(scale): raise RuntimeError, "%s is missing. Cannot complete..." % scale or "An Unspecified Joint"
                        j = Joint(c, data[c])
                        data[c] = j
                        cmds.select(clear=True)
                        j.joint = cmds.joint(
                            name=NameSpace(c, prefix),
                            p=cmds.xform(position, q=True, t=True, ws=True)
                        )
                        if hasattr(data, "joint"):
                            cmds.parent(j.joint, data.joint)
                        else:
                            cmds.parent(j.joint, root)
                        joints.append(j)
                        parse(data[c], depth)
                elif not depth: # Singleton
                    data["_type"] = 3
                else: # End Effector
                    data["_type"] = 4
            parse(data)

            # Set rotations
            upAxis = "%sup" % cmds.upAxis(q=True, ax=True)
            for j in joints:
                cmds.xform(
                    j.joint,
                    p=True,
                    roo=j.get("_rotationOrder", "xyz")
                    )
                t = j["_type"]
                if t == 1 or t == 2:
                    cmds.joint(
                        j.joint,
                        e=True,
                        zeroScaleOrient=True,
                        orientJoint="xyz",
                        secondaryAxisOrient=upAxis
                        )



            #
            # # Form heirarchy
            # upAxis = "%sup" % cmds.upAxis(q=True, ax=True)
            # def layout(j, parent=None):
            #     if parent:
            #         cmds.parent(j.joint, parent)
            #     else:
            #         cmds.parent(j.joint, root)
            #     children = [b for a, b in j.items() if a[:1] != "_"]
            #     childNum = len(children) # How many children have we?
            #     if childNum:
            #         for c in children:
            #             layout(c, j.joint)
            #         if childNum == 1: # Part of a limb
            #             cmds.joint(
            #                 j.joint,
            #                 e=True,
            #                 zeroScaleOrient=True,
            #                 orientJoint="xyz",
            #                 secondaryAxisOrient=upAxis
            #                 )
            #         else: # Base of a limb
            #             cmds.xform(
            #                 j.joint,
            #                 p=True,
            #                 roo=j.get("_rotationOrder", "xyz")
            #                 )
            #             position = j.get("_position", None)
            #             if position:
            #                 cmds.pointConstraint(j["_position"], j.joint, mo=True)
            #             else:
            #                 print "Warning: %s is missing a Position Target." % j.name
            #     else: # End of a limb
            #         cmds.xform(
            #             j.joint,
            #             p=True,
            #             roo=j.get("_rotationOrder", "xyz")
            #             )
            #     rotation = j.get("_rotation", None)
            #     scale = j.get("_scale", None)
            #     if rotation:
            #         cmds.orientConstraint(j["_rotation"], j.joint, mo=True)
            #     else:
            #         print "Warning: %s is missing a Rotation Target." % j.name
            #     if scale:
            #         cmds.scaleConstraint(j["_scale"], j.joint, mo=True)
            #     else:
            #         print "Warning: %s is missing a Scale Target." % j.name
            # for k in data:
            #     layout(data[k])

            cmds.confirmDialog(t="Wohoo!", m="Skeleton was built successfully")

import os.path
path = "/home/maczone/Dropbox/Dying Ember/Dying Ember/assets/Rig Structure Files/Human/Advanced Skeleton.skeleton"
with open(path, "r") as f:
    data = json.load(f)
    Attach(data)
