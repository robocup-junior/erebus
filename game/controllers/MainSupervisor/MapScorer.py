# Helper functions to be used within
# the MainSupervisor to give points
# to teams for the outputted map
# matrix.

import numpy as np
import numpy.typing as npt

from typing import Optional
from typing import Union

from MapAnswer import Color
from ConsoleLog import Console


def pretty_print_correct_matrix(
    map: Union[list, npt.NDArray], 
    correct_map: Union[list, npt.NDArray]
) -> None:
    """Print a formatted view of an Erebus map matrix, with correct/incorrect
    map features highlighted

    Args:
        map (list): Erebus map matrix to print
        correct_map (Union[list, npt.NDArray]): Binary matrix representing which
        map features are correct (1 for correct, 0 for incorrect)
    """
    for i in range(len(map)):
        for j in range(len(map[0])):
            bg: str = Color.BG_RED
            if correct_map[i][j] == 1:
                bg = Color.BG_GREEN
            elif correct_map[i][j] == 2:
                bg = Color.BG_DEFAULT
            print(f"{bg}{map[i][j]}{Color.RESET}", end='')
        print('')

def _get_start_instance(matrix: npt.NDArray) -> Optional[npt.NDArray]:
    """Gets the matrix coordinate of the first occurrence of the start
    tile char '5'.

    Args:
        matrix (npt.NDArray): Map matrix

    Returns:
        Optional[npt.NDArray]: Matrix coordinate of the first occurrence 
        of the start tile char '5'. None if no start tile char was found.
    """
    n, m = matrix.shape
    for y in range(n):
        for x in range(m):
            if matrix[y, x] == '5':
                return np.array([y, x])
    return None


def _shift_matrix(
    answer_matrix: npt.NDArray,
    sub_matrix: npt.NDArray,
    dy: int,
    dx: int,
) -> npt.NDArray:
    """Shifts the submission matrix by a given x,y amount. The matrix size stays
    the same and empty space from the shift is filled with 0s.

    Args:
        answer_matrix (npt.NDArray): Answer matrix
        sub_matrix (npt.NDArray): Submission matrix to be shifted
        dy (int): Shift by x direction
        dx (int): Shift by y direction

    Returns:
        npt.NDArray: Shifted matrix
    """
    n, m = sub_matrix.shape
    an, am = answer_matrix.shape

    big_sub_matrix = np.full((n * 3, m * 3), '0', dtype=sub_matrix.dtype)
    big_sub_matrix[n:2*n, m:2*m] = sub_matrix

    x = m - (dx)
    y = n - (dy)
    return big_sub_matrix[y:y+an, x:x+am]


def _align(
    answer_matrix: npt.NDArray,
    sub_matrix: npt.NDArray,
) -> npt.NDArray:
    """Aligns the sub_matrix with the answer_matrix via the start tile

    Args:
        answer_matrix (npt.NDArray): Answer matrix to align to
        sub_matrix (npt.NDArray): Submission matrix to align

    Raises:
        Exception: No starting tile found in the answer matrix
        Exception: No starting tile found in the submitted map

    Returns:
        npt.NDArray: Shifted matrix aligned via the start tile of the two matrices
    """
    ans_con_pos = _get_start_instance(answer_matrix)
    if ans_con_pos is None:
        raise Exception("No starting tile('5') was found on the answer map")
    sub_con_pos = _get_start_instance(sub_matrix)
    if sub_con_pos is None:
        raise Exception("No starting tile('5') was found on the submitted map")

    d_pos: npt.NDArray = ans_con_pos - sub_con_pos

    return _shift_matrix(answer_matrix, sub_matrix, *d_pos)


def _calculate_completeness(
    answer_matrix: npt.NDArray,
    sub_matrix: npt.NDArray,
) -> tuple[float, npt.NDArray]:
    """
    Calculate the quantifiable completeness score of a matrix, compared to
    another

    Args:
        answer_matrix (npt.NDArray): answer matrix to check against
        subMatrix (npt.NDArray): matrix to compare

    Returns:
        tuple[float, npt.NDArray]: tuple of completeness score and matrix of 
        correct/incorrect map feature positions 
    """
    correct: int = 0
    incorrect: int = 0

    if answer_matrix.shape != sub_matrix.shape:
        return 0, np.array([])
    
    # Correct matrix used to store positions of correctly identified map 
    # positions
    correct_matrix: npt.NDArray = np.full(sub_matrix.shape, 0)

    for i in range(len(answer_matrix)):
        for j in range(len(answer_matrix[0])):
            # If the cells are equal
            if not ((sub_matrix[i][j] == '0' and answer_matrix[i][j] == '0') or
                    answer_matrix[i][j] == '20'):
                if sub_matrix[i][j] == answer_matrix[i][j]:
                    correct += 1
                    correct_matrix[i][j] = 1
                # if a victim is on either side of the wall
                elif len(answer_matrix[i][j]) == 2:
                    if (sub_matrix[i][j] == answer_matrix[i][j] or
                            sub_matrix[i][j] == answer_matrix[i][j][::-1]):
                        correct += 1
                        correct_matrix[i][j] = 1
                    else:
                        incorrect += 1
                else:
                    incorrect += 1
            else:
                correct_matrix[i][j] = 2

    # Calculate completeness as a ratio of the correct count over the sum of
    # the correct count and incorrect count
    return (correct / (correct + incorrect)), correct_matrix


def _calculate_map_completeness(
    answer_matrix: npt.NDArray,
    sub_matrix: npt.NDArray,
) -> float:
    """
    Calculate completeness of submitted map area matrix. 4x 90 degree rotations
    are tried to account for the submission matrix being submitted in the wrong
    orientation.

    Args:
        answer_matrix (int): specifies which map to score
        sub_matrix (npt.NDArray): team submitted array

    Returns:
        float: completeness score
    """
    completeness_list: list[float] = []

    for i in range(0, 4):
        answer_matrix = np.rot90(answer_matrix, k=i, axes=(1, 0))
        aligned_sub_matrix = _align(answer_matrix, sub_matrix)

        completeness, correct_matrix = _calculate_completeness(answer_matrix, 
                                                      aligned_sub_matrix)
        completeness_list.append(completeness)
        
        if Console.DEBUG_MODE and len(correct_matrix) > 0:
            Console.log_debug(f"Printing aligned correct matrix for rotation "
                              f"{i * 90} degrees with score {completeness}")
            pretty_print_correct_matrix(aligned_sub_matrix, correct_matrix)
            

    # Return the highest score
    return max(completeness_list)


def calculateScore(
    answer_matrices: Union[list, npt.NDArray],
    sub_matrix: Union[list, npt.NDArray]
) -> float:
    """
    Calculate the quantifiable completeness score of a matrix, compared to
    another

    Args:
        answer_matrix (Union[list, npt.NDArray]): answer matrix to check against
        subMatrix (Union[list, npt.NDArray]): matrix to compare

    Returns:
        float: completeness score
    """
    return _calculate_map_completeness(np.array(answer_matrices), 
                                       np.array(sub_matrix))
