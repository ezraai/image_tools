import numpy as np
LPS_TO_RAS = np.mat(np.diag([-1, -1, 1, 1]))


def num_from_str_vec(vec):
    return np.array(vec).astype(np.float)


def dot(matrix, pos):
    ''' Implements dot product of the form matrix * pos'''
    return np.squeeze(np.asarray(np.dot(matrix, pos)))


def trx_lps_to_ras(vec):
    """
    Transforms a vector expressed in LPS to RAS
    :param vec: 4-dimensional vector (homogeneous coordinates)
    """
    return dot(LPS_TO_RAS, vec)