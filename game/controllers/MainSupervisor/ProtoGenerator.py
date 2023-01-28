from Tools import *
import AutoInstall
import math
import numpy as np
from ConsoleLog import Console

AutoInstall._import("cl", "termcolor")

def generate_robot_proto(robot_json):
    
    # Hard coded, values from website
    component_max_counts = {
        "Wheel": 4,
        "Distance Sensor": 8,
        "Camera": 3
    }

    component_counts = {}
    
    templatePath = getFilePath("controllers/MainSupervisor/protoHeaderTemplateFLU.txt", "protoHeaderTemplateFLU.txt")

    with open(templatePath) as protoTemplate:
        proto_code = protoTemplate.read() 
    
    closeBracket = "\n\t\t}\n"

    budget = 3000
    cost = 0
    costs = {
        'Gyro': 100,
        'InertialUnit': 100, 
        'GPS': 250,
        'Camera': 500,
        'Colour sensor': 100,
        'Accelerometer': 100,
        'Lidar': 500,
        'Wheel': 300,
        'Distance Sensor': 50
    }

    genERR = False

    for component in robot_json:

        # Add component to component_counts
        if robot_json[component]["name"] not in component_counts:
            component_counts[robot_json[component]["name"]] = 1
        else:
            # Increase component count
            component_counts[robot_json[component]["name"]] += 1

        component_count = component_counts[robot_json[component]["name"]]
        # If the robot can have more than one of this component
        if robot_json[component]["name"] in component_max_counts:
            component_max_count = component_max_counts[robot_json[component]["name"]]
            # If there are more components in json than there should be, continue
            if component_count > component_max_count:
                Console.log_warn(f"[SKIP] The number of {robot_json[component]['name']} is limited to {component_max_count}.")
                continue
        else:
            # If there should only be one component
            # Skip if count is > 1
            if component_count > 1:
                Console.log_warn(f"[SKIP] The number of {robot_json[component]['name']} is limited to only one.")
                continue

        # Cost calculation
        try:
            cost += costs[robot_json[component]["name"]]
            if cost > budget:
                Console.log_err("The necessary costs exceed the budget.")
                Console.log_err(f"Budget: {budget}  Cost: {cost}")
                genERR = True
                break
        except KeyError as e:
            Console.log_warn(f"[SKIP] {e.args[0]} is no longer supported in this version.")
            continue

        if robot_json[component].get("customName") is None or robot_json[component].get("customName") == "":
            Console.log_err(f"No tag name has been specified for {robot_json[component].get('name')}. Please specify a suitable name in the robot generator.")
            genERR = True
            break

        if robot_json[component].get("name") == "Wheel":
            Console.log_info(
                f"Adding motor... {robot_json[component].get('dictName')} ({robot_json[component].get('customName')} motor)")
            Console.log_info(
                f"Adding sensor... {robot_json[component].get('dictName')} ({robot_json[component].get('customName')} sensor)")
        else:
            Console.log_info(
                f"Adding sensor... {robot_json[component].get('dictName')} ({robot_json[component].get('customName')})")

        # Hard coded, so if ranges change in the website,
        # I need to change them here too :(
        if(robot_json[component]["name"] == "Wheel"):
            x = clamp(robot_json[component]['x'], -370, 370) / 10000
            y = clamp(robot_json[component]['y'], -100, 370) / 10000
            z = clamp(robot_json[component]['z'], -260, 260) / 10000
        else:
            x = clamp(robot_json[component]['x'], -370, 370) / 10000
            y = clamp(robot_json[component]['y'], -100, 370) / 10000
            z = clamp(robot_json[component]['z'], -370, 370) / 10000

        y += 18.5/1000

        if(robot_json[component]["name"] == "Wheel"):
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["rz"]} {robot_json[component]["ry"]} {robot_json[component]["a"]}
            children [
            Transform {{
            translation 0 0 0
            rotation 0.57735 0.57735 0.57735 2.09
            children [
            HingeJoint {{
            jointParameters HingeJointParameters {{
                axis -1 0 0
                anchor 0 0 0
            }}
            device [
                RotationalMotor {{
                name "{robot_json[component]["customName"]} motor"
                consumptionFactor -0.001 # small trick to encourage the movement (calibrated for the rat's life contest)
                maxVelocity IS max_velocity
                multiplier IS wheel_mult
                }}
                PositionSensor {{
                name "{robot_json[component]["customName"]} sensor"
                resolution 0.00628  # (2 * pi) / 1000
                }}
            ]
            endPoint Solid {{
                translation 0 0 0
                rotation 0.707388 0 -0.707388 3.14
                children [
                Transform {{
                   rotation 0 0 0 0
                    children [
                    Shape {{
                        appearance PBRAppearance {{
                        baseColor 1 0.7 0
                        transparency 0
                        roughness 0.5
                        metalness 0
                        }}
                        geometry Cylinder {{
                        height 0.003
                        radius 0.02
                        subdivision 24
                        }}
                        castShadows FALSE
                    }}
                    Shape {{
                        appearance PBRAppearance {{
                            baseColor 0.117647 0.815686 0.65098
                            roughness 0.4
                            metalness 0
                        }}
                        geometry Cylinder {{
                            bottom FALSE
                            height 0.0015
                            radius 0.0201
                            top FALSE
                            subdivision 24
                        }}
                        castShadows FALSE
                    }}
                    Transform {{
                        translation 0 0 -0.0035
                        rotation -1 0 0 6.326802116328499e-06
                        children [
                        Shape {{
                            appearance DEF EPUCK_TRANSPARENT_APPEARANCE PBRAppearance {{
                            baseColor 0.5 0.5 0.5
                            transparency 0
                            roughness 0.5
                            metalness 0
                            }}
                            geometry Cylinder {{
                            height 0.004
                            radius 0.005
                            }}
                            castShadows FALSE
                        }}
                        ]
                    }}
                    Transform {{
                        rotation -1 0 0 6.326802116328499e-06
                        children [
                        Shape {{
                            appearance PBRAppearance {{
                            }}
                            geometry Cylinder {{
                            height 0.013
                            radius 0.003
                            subdivision 6
                            }}
                            castShadows FALSE
                        }}
                        ]
                    }}
                    Transform {{
                        translation 0 0 -0.0065
                        rotation -1 0 0 6.326802116328499e-06
                        children [
                        Shape {{
                            appearance PBRAppearance {{
                            baseColor 1 0.647059 0
                            metalness 0
                            roughness 0.6
                            }}
                            geometry Cylinder {{
                            height 0.0001
                            radius 0.002
                            }}
                            castShadows FALSE
                        }}
                        ]
                    }}
                    ]
                }}
                ]
                name "{robot_json[component]["customName"]}"
                boundingObject Transform {{
                children [
                    Cylinder {{
                    height 0.005
                    radius 0.02
                    subdivision 24
                    }}
                ]
                }}
                physics DEF EPUCK_WHEEL_PHYSICS Physics {{
                    density -1
                    mass 0.8
                }}
            }}
            }}
            ]
            }}
            ]
            }}
            
            """

        if(robot_json[component]["name"] == "Camera"):
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["rz"]} {robot_json[component]["ry"]} {robot_json[component]["a"]}
            children [
                Camera {{
                name "{robot_json[component]["customName"]}"
                rotation 1 0 0 0
                children [
                    Transform {{
                    rotation 9.381865489561552e-07 -9.381865488949227e-07 0.9999999999991198 1.5707944504244395
                    children [
                        Transform {{
                        rotation IS camera_rotation
                        children [
                            Shape {{
                            appearance PBRAppearance {{
                                baseColor 0 0 0
                                roughness 0.4
                                metalness 0
                            }}
                            geometry IndexedFaceSet {{
                                coord Coordinate {{
                                point [
                                    -0.003 -0.000175564 0.003 -0.003 -0.00247555 -0.003 -0.003 -0.00247555 -4.65661e-09 -0.003 -0.00247555 0.003 -0.003 -2.55639e-05 0.0035 -0.003 -2.55639e-05 -0.003 -0.003 0.000427256 0.00574979 -0.003 -0.000175564 0.0035 -0.003 0.000557156 0.0056748 -0.003 0.00207465 0.00739718 -0.003 0.00214964 0.00726728 -0.003 0.00432444 0.008 -0.003 0.00432444 0.00785 -0.003 0.00757444 0.008 -0.003 0.00757444 0.0095 -0.003 0.0115744 0.0095 -0.003 0.0115744 0.008 -0.003 0.0128244 0.008 -0.003 0.0128244 0.00785 0.003 -2.55639e-05 -0.003 0.003 -0.000175564 0.0035 0.003 -0.000175564 0.003 0.003 -0.00247555 0.003 0.003 -0.00247555 -4.65661e-09 0.003 -0.00247555 -0.003 0.003 -2.55639e-05 0.0035 0.003 0.000427256 0.00574979 0.003 0.000557156 0.0056748 0.003 0.00207465 0.00739718 0.003 0.00214964 0.00726728 0.003 0.00432444 0.00785 0.003 0.00432444 0.008 0.003 0.0115744 0.0095 0.003 0.00757444 0.0095 0.003 0.0115744 0.008 0.003 0.00757444 0.008 0.003 0.0128244 0.00785 0.003 0.0128244 0.008 0 -0.00247555 -0.003 -0.00149971 -0.00247555 -0.0025982 0.00149971 -0.00247555 -0.0025982 0.00259801 -0.00247555 -0.00150004 -0.00259801 -0.00247555 -0.00150004 0.00149971 -0.00247555 0.00259821 0.00259801 -0.00247555 0.00150005 0 -0.00247555 0.003 -0.00149971 -0.00247555 0.00259821 -0.00259801 -0.00247555 0.00150005 0.00212127 -0.00377555 0.00212128 0 -0.00377555 0.003 -0.00212127 -0.00377555 0.00212128 -0.0015 -0.00377555 0.002 -0.002 -0.00377555 0.0015 -0.003 -0.00377555 -4.65661e-09 0.0015 -0.00377555 0.002 0.002 -0.00377555 0.0015 0.003 -0.00377555 -4.65661e-09 -0.002 -0.00377555 -0.0015 0.002 -0.00377555 -0.0015 -0.00212127 -0.00377555 -0.0021213 0.0015 -0.00377555 -0.002 -0.0015 -0.00377555 -0.002 0.00212127 -0.00377555 -0.0021213 0 -0.00377555 -0.003 -0.00256063 -0.00377555 0.00106064 -0.00106063 -0.00377555 0.00256064 0.00106063 -0.00377555 0.00256064 0.00256063 -0.00377555 0.00106064 0.00256063 -0.00377555 -0.00106063 0.00106063 -0.00377555 -0.0025606 -0.00106063 -0.00377555 -0.0025606 -0.00256063 -0.00377555 -0.00106063 0.0015 -0.00417556 -0.002 0.002 -0.00417556 -0.0015 -0.0015 -0.00417556 -0.002 -0.002 -0.00417556 -0.0015 0.002 -0.00417556 0.0015 0 -0.00417556 0.000245125 0.00021198 -0.00417556 0.000122716 0.00021198 -0.00417556 -0.000122714 0 -0.00417556 -0.000245124 -0.00021198 -0.00417556 -0.000122714 -0.00021198 -0.00417556 0.000122716 -0.002 -0.00417556 0.0015 0.0015 -0.00417556 0.002 -0.0015 -0.00417556 0.002
                                ]
                                }}
                                coordIndex [
                                33, 14, 35, -1, 13, 35, 14, -1, 15, 32, 16, -1, 34, 16, 32, -1, 14, 33, 15, -1, 32, 15, 33, -1, 72, 74, 60, -1, 61, 60, 74, -1, 74, 75, 61, -1, 57, 61, 75, -1, 75, 83, 57, -1, 52, 57, 83, -1, 83, 85, 52, -1, 51, 52, 85, -1, 85, 84, 51, -1, 54, 51, 84, -1, 84, 76, 54, -1, 55, 54, 76, -1, 76, 73, 55, -1, 58, 55, 73, -1, 73, 72, 58, -1, 60, 58, 72, -1, 72, 73, 74, -1, 75, 74, 73, -1, 76, 77, 78, -1, 76, 78, 79, -1, 79, 80, 75, -1, 79, 75, 73, -1, 73, 76, 79, -1, 75, 80, 81, -1, 75, 81, 82, -1, 82, 77, 76, -1, 82, 76, 83, -1, 83, 75, 82, -1, 76, 84, 83, -1, 85, 83, 84, -1, 56, 68, 23, -1, 41, 23, 68, -1, 68, 62, 41, -1, 40, 41, 62, -1, 62, 69, 40, -1, 40, 69, 63, -1, 38, 40, 63, -1, 63, 70, 38, -1, 39, 38, 70, -1, 70, 59, 39, -1, 42, 39, 59, -1, 59, 71, 42, -1, 42, 71, 53, -1, 2, 42, 53, -1, 53, 64, 2, -1, 47, 2, 64, -1, 64, 50, 47, -1, 46, 47, 50, -1, 50, 65, 46, -1, 46, 65, 49, -1, 45, 46, 49, -1, 49, 66, 45, -1, 43, 45, 66, -1, 66, 48, 43, -1, 44, 43, 48, -1, 48, 67, 44, -1, 44, 67, 56, -1, 23, 44, 56, -1, 48, 49, 50, -1, 51, 48, 50, -1, 52, 51, 50, -1, 50, 53, 52, -1, 48, 51, 54, -1, 48, 54, 55, -1, 56, 48, 55, -1, 57, 52, 53, -1, 55, 58, 56, -1, 59, 60, 61, -1, 59, 61, 57, -1, 53, 59, 57, -1, 60, 59, 62, -1, 58, 60, 62, -1, 62, 56, 58, -1, 59, 63, 62, -1, 0, 45, 22, -1, 21, 0, 22, -1, 45, 0, 3, -1, 38, 39, 1, -1, 40, 38, 24, -1, 41, 40, 24, -1, 24, 23, 41, -1, 1, 39, 42, -1, 2, 1, 42, -1, 22, 43, 44, -1, 23, 22, 44, -1, 45, 43, 22, -1, 46, 45, 3, -1, 47, 46, 3, -1, 3, 2, 47, -1, 20, 26, 7, -1, 6, 7, 26, -1, 26, 28, 6, -1, 9, 6, 28, -1, 28, 31, 9, -1, 11, 9, 31, -1, 31, 35, 11, -1, 13, 11, 35, -1, 34, 37, 16, -1, 17, 16, 37, -1, 36, 18, 37, -1, 17, 37, 18, -1, 36, 30, 18, -1, 12, 18, 30, -1, 4, 8, 25, -1, 27, 25, 8, -1, 8, 10, 27, -1, 29, 27, 10, -1, 10, 12, 29, -1, 30, 29, 12, -1, 25, 19, 4, -1, 5, 4, 19, -1, 24, 38, 19, -1, 19, 38, 1, -1, 5, 19, 1, -1, 20, 7, 21, -1, 0, 21, 7, -1, 19, 20, 21, -1, 19, 21, 22, -1, 19, 22, 23, -1, 24, 19, 23, -1, 20, 19, 25, -1, 26, 20, 25, -1, 25, 27, 26, -1, 28, 26, 27, -1, 27, 29, 28, -1, 28, 29, 30, -1, 31, 28, 30, -1, 32, 33, 34, -1, 34, 33, 35, -1, 36, 34, 35, -1, 36, 35, 31, -1, 30, 36, 31, -1, 37, 34, 36, -1, 0, 1, 2, -1, 3, 0, 2, -1, 0, 4, 5, -1, 1, 0, 5, -1, 4, 0, 6, -1, 6, 0, 7, -1, 8, 4, 6, -1, 6, 9, 8, -1, 10, 8, 9, -1, 9, 11, 10, -1, 12, 10, 11, -1, 11, 13, 12, -1, 14, 15, 13, -1, 13, 15, 16, -1, 12, 13, 16, -1, 12, 16, 17, -1, 18, 12, 17, -1
                                ]
                                creaseAngle 0.785398
                            }}
                            castShadows FALSE
                            }}
                        ]
                        }}
                    ]
                    }}
                ]
                fieldOfView IS camera_fieldOfView
                width IS camera_width
                height IS camera_height
                near 0.0045
                antiAliasing IS camera_antiAliasing
                motionBlur IS camera_motionBlur
                noise IS camera_noise
                zoom Zoom {{
                }}
                physics Physics {{
                }}
                boundingObject Sphere {{
                    radius 0.007
                }}
                }}
            ]
            }}"""

        if robot_json[component]["name"] in ["Gyro", "GPS", "InertialUnit"]:
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["rz"]} {robot_json[component]["ry"]} {robot_json[component]["a"]}
            children [
            {robot_json[component]["name"]} {{
            rotation 0.577 -0.577 -0.577 2.09
            name "{robot_json[component]["customName"]}"
            physics Physics {{
            }}
            boundingObject Sphere {{
                radius 0.003
            }}
            }}
            ]
            }}
            """

        if(robot_json[component]["name"] == "Colour sensor"):
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["rz"]} {robot_json[component]["ry"]} {robot_json[component]["a"]}
            children [
                Transform {{
                rotation 1 0 0 3.14
                children [
                    Transform {{
                        rotation 0 0 1 0
                        children [
                            SpotLight {{
                            attenuation 0 0 12.56
                            intensity   0.01
                            direction   1 0 0
                            cutOffAngle 0.3
                            }}
                        ]
                    }}
                    Camera {{
                    name "{robot_json[component]["customName"]}"
                    rotation 0 0 1 0
                    width 1
                    height 1
                    }}
                ]
                }}
            ]
            }}
            """

        if robot_json[component]["name"] == "Distance Sensor":
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["rz"]} {robot_json[component]["ry"]} {robot_json[component]["a"]}
            children [
            DistanceSensor {{
            name "{robot_json[component]["customName"]}"
            lookupTable [
                0 0 0
                0.8 0.8 0
            ]
            type "infra-red"
            rotation 1 0 0 1.56826
            physics Physics {{
            }}
            boundingObject Sphere {{
                radius 0.003
            }}
            }}
            ]
            }}
            """

        if(robot_json[component]["name"] == "Accelerometer"):
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["rz"]} {robot_json[component]["ry"]} {robot_json[component]["a"]}
            children [
            Accelerometer {{
                lookupTable [ -100 -100 0.003 100 100 0.003 ]
                rotation 0.577 -0.577 -0.577 2.09
                physics Physics {{
                }}
                boundingObject Sphere {{
                    radius 0.003
                }}
            }}
            ]
            }}"""

        if(robot_json[component]["name"] == "Lidar"):
            proto_code += f"""
            Transform {{
            translation {x} {y} {z}
            rotation {robot_json[component]["rx"]} {robot_json[component]["rz"]} {robot_json[component]["ry"]} {robot_json[component]["a"]}
            children [
                Lidar {{
                rotation 0 0 1 3.14159
                fieldOfView 6.2832
                physics Physics {{
                }}
                boundingObject Sphere {{
                    radius 0.003
                }}
                }}
            ]
            }}"""

    proto_code += """DEF EPUCK_RING SolidPipe {
    translation 0 0.0393 0
    rotation -0.5773502691896258 0.5773502691896258 0.5773502691896258 2.0943951023931953
    height 0.007
    radius 0.0356
    thickness 0.004
    subdivision 64
    appearance USE EPUCK_TRANSPARENT_APPEARANCE
    enableBoundingObject FALSE
    }
    \n\t]
        name IS name
        model "GCtronic e-puck"
    description "Educational robot designed at EPFL"
    boundingObject Group {
        children [
        Transform {
            translation 0 0.025 0
            rotation -1 0 0 1.5707963267948966
            children [
            Cylinder {
                height 0.045
                radius 0.037
                subdivision 24
            }
            ]
        }
        ]
    }
    physics Physics {
        density -1
        mass 0.15
        centerOfMass [
        0 0.015 0
        ]
        inertiaMatrix [
        8.74869e-05 9.78585e-05 8.64333e-05
        0 0 0
        ]
    }
    controller IS controller
    controllerArgs IS controllerArgs
    customData IS customData
    """
    proto_code += "\n}"
    proto_code += closeBracket

    if not genERR:
        Console.log_succ("Your custom robot has been successfully generated!")
        Console.log_succ(f"Budget: {budget}  Cost: {cost}")
            
        path = getFilePath("protos", "../../protos")
        path = os.path.join(path, "custom_robot.proto")

        with open(path, 'w') as robot_file:
            robot_file.write(proto_code)
        return True
    else:
        Console.log_err("Your custom robot generation has been cancelled.")
    return False
