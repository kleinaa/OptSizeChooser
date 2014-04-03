'''
Created on 31.03.2014

@author: Aaron Klein, Simon Bartels
'''
import numpy as np
import scipy.stats as sps
from spearmint.util import slice_sample
from hyper_parameter_sampling import handle_slice_sampler_exception


def compute_expected_improvement(cand, gp):

    incumbent = np.min(gp.getValues())

    (func_m, func_v) = gp.predict_vector(cand)

    func_s = np.sqrt(func_v)
    u = (incumbent - func_m) / func_s
    ncdf = sps.norm.cdf(u)
    npdf = sps.norm.pdf(u)

    ei = func_s * (u * ncdf + npdf)

    return ei


def compute_pmin_bins(Omega, mean, L):
    '''
    Computes a discrete distribution of where the minimum is located in a Gaussian process for some representer points.
    Args:
        Omega: a numpy matrix of standard normal samples
            first dimension is the number of samples
            second dimension is the number points considered
        mean: the mean prediction of the representer points
        L: the cholesky decomposition of the (posterior) covariance matrix at the representer points
    Returns:
        a numpy array with a probability for each representer point
    '''
    number_of_samples = Omega.shape[0]
    #TODO: inefficient to compute idx here?
    idx = np.arange(0, number_of_samples)
    Y = mean[:, np.newaxis] + np.dot(L, Omega.T)
    min_idx = np.argmin(Y, axis=0)
    mins = np.zeros([mean.shape[0], number_of_samples])
    mins[min_idx, idx] = 1
    pmin = np.sum(mins, axis=1)
    pmin = 1. / number_of_samples * pmin
    return pmin


def sample_from_proposal_measure(starting_point, log_proposal_measure, number_of_points, chain_length=20):
    '''
Samples representer points for discretization of Pmin.
Args:
starting_point: The point where to start the sampling.
log_proposal_measure: A function that measures in log-scale how suitable a point is to represent Pmin.
number_of_points: The number of samples to draw.
Returns:
a numpy array containing the desired number of samples
'''
    representer_points = np.zeros([number_of_points, starting_point.shape[0]])
    #TODO: burnin?
    for i in range(0, number_of_points):
        #this for loop ensures better mixing
        for c in range(0, chain_length):
            try:
                starting_point = slice_sample(starting_point, log_proposal_measure)
            except Exception as e:
                starting_point = handle_slice_sampler_exception(e, starting_point, log_proposal_measure)
        representer_points[i] = starting_point
    return representer_points