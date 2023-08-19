# Helper functions to be used within
# the MainSupervisor to give points
# to teams for the outputted map
# matrix.

import numpy as np

def _get_start_instance(matrix: np.array) -> np.array:
    """Gets the matrix coordinate of the first occurrence of the start
    tile char '5'.

    Args:
        matrix (np.array): Map matrix

    Returns:
        np.array: Matrix coordinate of the first occurrence of the start
        tile char '5' 
    """
    n, m = matrix.shape
    for y in range(n):
        for x in range(m):
            if matrix[y, x] == '5':
                return np.array([y, x])
    return None


def _shift_matrix(
    answer_matrix: np.array,
    sub_matrix: np.array,
    dy: int,
    dx: int,
) -> np.array:
    """Shifts the submission matrix by a given x,y amount. The matrix size stays
    the same and empty space from the shift is filled with 0s.

    Args:
        answer_matrix (np.array): Answer matrix
        sub_matrix (np.array): Submission matrix to be shifted
        dy (int): Shift by x direction
        dx (int): Shift by y direction

    Returns:
        np.array: Shifted matrix
    """
    n, m = sub_matrix.shape
    an, am = answer_matrix.shape

    big_sub_matrix = np.full((n * 3, m * 3), '0', dtype=sub_matrix.dtype)
    big_sub_matrix[n:2*n, m:2*m] = sub_matrix

    x = m - (dx)
    y = n - (dy)
    return big_sub_matrix[y:y+an, x:x+am]


def _align(
    answer_matrix: np.array,
    sub_matrix: np.array,
) -> np.array:
    """Aligns the sub_matrix with the answer_matrix via the start tile

    Args:
        answer_matrix (np.array): Answer matrix to align to
        sub_matrix (np.array): Submission matrix to align

    Raises:
        Exception: No starting tile found in the answer matrix
        Exception: No starting tile found in the submitted map

    Returns:
        np.array: Shifted matrix aligned via the start tile of the two matrices
    """
    ans_con_pos = _get_start_instance(answer_matrix)
    if ans_con_pos is None:
        raise Exception("No starting tile('5') was found on the answer map")
    sub_con_pos = _get_start_instance(sub_matrix)
    if sub_con_pos is None:
        raise Exception("No starting tile('5') was found on the submitted map")

    d_pos = ans_con_pos - sub_con_pos

    return _shift_matrix(answer_matrix, sub_matrix, *d_pos)


def _calculate_completeness(
    answer_matrix: np.array,
    sub_matrix: np.array,
) -> float:
    """
    Calculate the quantifiable completeness score of a matrix, compared to
    another

    Args:
        answer_matrix (np.array): answer matrix to check against
        subMatrix (np.array): matrix to compare

    Returns:
        float: completeness score
    """
    correct = 0
    incorrect = 0

    if answer_matrix.shape != sub_matrix.shape:
        return 0

    for i in range(len(answer_matrix)):
        for j in range(len(answer_matrix[0])):
            # If the cells are equal
            if not ((sub_matrix[i][j] == '0' and answer_matrix[i][j] == '0') or
                    answer_matrix[i][j] == '20'):
                if sub_matrix[i][j] == answer_matrix[i][j]:
                    correct += 1
                # if a victim is on either side of the wall
                elif len(answer_matrix[i][j]) == 2:
                    if (sub_matrix[i][j] == answer_matrix[i][j] or
                            sub_matrix[i][j] == answer_matrix[i][j][::-1]):
                        correct += 1
                    else:
                        incorrect += 1
                else:
                    incorrect += 1

    # Calculate completeness as a ratio of the correct count over the sum of
    # the correct count and incorrect count
    return (correct / (correct + incorrect))


def _calculate_map_completeness(
    answer_matrix: np.array,
    sub_matrix: np.array,
) -> float:
    """
    Calculate completeness of submitted map area matrix. 4x 90 degree rotations
    are tried to account for the submission matrix being submitted in the wrong
    orientation.

    Args:
        answer_matrix (int): specifies which map to score
        sub_matrix (np.array): team submitted array

    Returns:
        float: completeness score
    """
    completeness_list = []

    for i in range(0, 4):
        answer_matrix = np.rot90(answer_matrix, k=i, axes=(1, 0))
        aSubMatrix = _align(answer_matrix, sub_matrix)

        completeness = _calculate_completeness(answer_matrix, aSubMatrix)
        completeness_list.append(completeness)

    # Return the highest score
    return max(completeness_list)


def calculateScore(answer_matrices: list, sub_matrix: list) -> float:
    """
    Calculate the quantifiable completeness score of a matrix, compared to
    another

    Args:
        answer_matrix (list): answer matrix to check against
        subMatrix (list): matrix to compare

    Returns:
        float: completeness score
    """
    score = _calculate_map_completeness(
        np.array(answer_matrices), np.array(sub_matrix))
    return score
