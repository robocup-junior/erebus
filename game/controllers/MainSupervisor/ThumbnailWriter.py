from controller import Supervisor
from Tools import get_file_path
import os

import numpy as np
from PIL import Image


def export_map_to_img(
    supervisor: Supervisor,
    map: list[list[str]]
) -> None:
    """Export map answer to world thumbnail

    Args:
        supervisor (Supervisor): Game supervisor
        map (list[list[str]]): Erebus map answer matrix
    """
    img_array: list[int] = []

    for row in map:
        for element in row:
            if element == '*':
                img_array.append(128)
            elif element == '1':
                img_array.append(0)
            elif element.isdigit():
                img_array.append(255)
            else:
                img_array.append(0)

    img_np_array = np.array(img_array)
    img_np_array = np.reshape(img_np_array, (len(map), len(map[0])))
    im = Image.fromarray(img_np_array.astype(np.uint8))

    path = get_file_path(
        "plugins/robot_windows/MainSupervisorWindow/thumbnails",
        "../../plugins/robot_windows/MainSupervisorWindow/thumbnails")
    path = os.path.join(path, 
                        os.path.split(supervisor.getWorldPath())[1][:-4]+'.png')

    im.save(path, 'png')
