# MapScorer.py - Alfred Roberts 2021

# Helper functions to be used within
# the MainSupervisor to give points
# to teams for the outputted map
# matrix.

import AutoInstall
AutoInstall._import("np", "numpy")

def _get_start_instance(matrix: np.array) -> np.array:
    n,m = matrix.shape
    for y in range(n):
        for x in range(m):
            if matrix[y,x] == '5':
                return np.array([y,x])
    return None

def _shift_matrix(answerMatrix: np.array, subMatrix: np.array, dy: int, dx: int) -> np.array:
    n,m = subMatrix.shape
    an,am = answerMatrix.shape

    bigSubMatrix = np.full((n *3,m *3),'0', dtype=subMatrix.dtype) 
    bigSubMatrix[n:2*n,m:2*m] = subMatrix

    x = m - (dx)
    y = n - (dy)
    return bigSubMatrix[y:y+an, x:x+am]
    

def _align(answerMatrix: np.array, subMatrix: np.array) -> np.array:
    """
    Align the subMatrix with the answerMatrix via one of the connectors

    Returns:
        subMatrix aligned with the answerMatrix
    """
    ans_con_pos = _get_start_instance(answerMatrix)
    if ans_con_pos is None:
        raise Exception("No starting tile('5') was found on the answer map")
    sub_con_pos = _get_start_instance(subMatrix)
    if sub_con_pos is None:
        raise Exception("No starting tile('5') was found on the submitted map")

    d_pos = ans_con_pos - sub_con_pos

    return _shift_matrix(answerMatrix, subMatrix,*d_pos)


def _calculate_completeness(answerMatrix: np.array, subMatrix: np.array) -> float:
    """
    Calculate the quatifiable completeness score of a matrix, compared to another

    Args:
        answerMatrix (np.array): answer matrix to check against
        subMatrix (np.array): matrix to compare

    Returns:
        float: completeness score
    """
    correct = 0
    incorrect = 0

    if answerMatrix.shape != subMatrix.shape:
        return 0

    for i in range(len(answerMatrix)):
        for j in range(len(answerMatrix[0])):
            # If the cells are equal
            if not((subMatrix[i][j] == '0' and answerMatrix[i][j] == '0') or answerMatrix[i][j] == '20'):
                if subMatrix[i][j] == answerMatrix[i][j]:
                    correct += 1
                # if a victim is on either side of the wall
                elif len(answerMatrix[i][j]) == 2:
                    if subMatrix[i][j] == answerMatrix[i][j] or subMatrix[i][j] == answerMatrix[i][j][::-1]:
                        correct += 1
                    else:
                        incorrect += 1
                else:
                    incorrect += 1

    # Calculate completeness as a ratio of the correct count over the sum of the correct count and incorrect count 
    return (correct / (correct + incorrect))

def _calculate_map_completeness(answerMatrix: np.array, subMatrix: np.array) -> float:
    """
    Calculate completeness of submitted map area matrix

    Args:
        map (int): specifies which map to score
        subMatrix (np array): team submitted array
    """
    completeness_list = []

    for i in range(0,4):
        answerMatrix = np.rot90(answerMatrix,k=i,axes=(1,0))
        aSubMatrix = _align(answerMatrix,subMatrix)

        completeness = _calculate_completeness(answerMatrix, aSubMatrix)
        completeness_list.append(completeness)
    # Return the highest score
    return max(completeness_list)

    

def calculateScore(answerMatrices: list, subMatrix: list) -> float:
    score = _calculate_map_completeness(np.array(answerMatrices),np.array(subMatrix))
    return score