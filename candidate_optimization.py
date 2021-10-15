import candidate_locations
import csv
import random
import numpy
import math

candidates = candidate_locations.candidate_process()

candidates = [1, 8, 10, 15, 17, 23, 25, 26, 27, 28, 29, 32, 34, 37, 42, 47, 55, 63, 65, 66]

from scipy.optimize import minimize, LinearConstraint

# assign data to constants 

rate_of_interest = 0.07
planning_period = 10

C_install = 3500.0
cost_of_electricity = 0.07
max_charging_stations = len(candidates)

arrival_rate = 25
prob_no_evs_waiting = 0.4182
utilization_rate = 0.9

# scipy

def objective_function(F):
    return (
        sum(initial_F) * (C_install + cost_of_electricity) * rate_of_interest * ((1 + rate_of_interest) ** planning_period) / (((1 + rate_of_interest) ** planning_period) - 1)/3569.3767421581256
        + (sum([sum([utilization_rate for j in range(int(F[i]+1))]) / (numpy.math.factorial(int(F[i]-1)) * ((F[i]-utilization_rate)**2)) for i in range(max_charging_stations)]) * prob_no_evs_waiting / arrival_rate)
    )

initial_F = [1] * max_charging_stations

res = minimize(objective_function, initial_F, method='SLSQP', bounds=[(1, 20)] * len(initial_F))

print(res)