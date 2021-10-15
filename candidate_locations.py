# given table of format
# bus no. | VSF at loading factor 4 | Node no. | Distance

import csv # to read csv data
import random # for probability

"""
function to print lists of data element by element to make it look cleaner
"""
def print_data(data):
    for element in data:
        print(element)

# load data
with open(r'data/candidate_data.csv', 'r') as nodecsv: # Open the file
    nodereader = csv.reader(nodecsv) # Read the csv
    data = [n for n in nodereader][1:] # remove the table headers

# omit incomplete data or busses without a corresponding node no. (since in candidate_data.csv, there were some busses that were
    # not connected to nodes and as such could not be evaluated as candidates)
data_to_omit = []
for i in range(len(data)):
    if data[i][2] == "":
        data_to_omit.append(data[i])

for element in data_to_omit:
    data.remove(element)

# transfer data to numerical from string so that calculations can be performed later
for i in range(len(data)):
    for j in range(len(data[0])):
        if j == 1:
            data[i][j] = float(data[i][j])
        else:
            data[i][j] = int(data[i][j])

# order data by node no. 
data = sorted(data, key=lambda x: x[2])

# add congestion data - import congestion data based on node location
    # congestion data was in a .docx file and was transferred to .csv format
    # would be easier to incorporate into one table, then this code could be removed
with open(r'data/node_locations.csv', 'r') as nodecsv: # Open the file
    nodereader = csv.reader(nodecsv) # Read the csv
    congestion = [n for n in nodereader][1:]

# congestion data - convert node locations to integer
for i in range(len(congestion)):
    congestion[i][0] = int(congestion[i][0])

# add to data based on node
for i in range(len(data)):
    for j in range(len(congestion)):
        if data[i][2] == congestion[j][0]:
            data[i] = data[i] + [congestion[j][1]]

# build dictionary with data
# format: dataset[node no.] = [vsf data, traffic data, congestion data]
dataset = {}

for node in data:
    dataset[node[2]] = [node[i] for i in range(len(node)) if (i != 0 and i != 2)]

# bayesian network construction 
"""
Bayesian network structure: 
Children --> stability factor at a given node, average congestion factor of all corresponding edges, average distances factors of all corresponding edges
Parent --> Candidate (y/n)
"""

from pomegranate import *

# VSF distribution
low_threshold = .2 # from the reference paper
high_threshold = .4 # from the reference paper

# create dictionary for VSF states
# count how many low, medium, and high vsfs are present in the current dataset
vsf_bn = {}
vsf_bn["low"] = 0
vsf_bn["medium"] = 0
vsf_bn["high"] = 0

# add data to dictionary
for node in dataset:
    if dataset[node][0] <= low_threshold:
        vsf_bn["low"] += 1
    elif dataset[node][0] <= high_threshold:
        vsf_bn["medium"] += 1
    else:
        vsf_bn["high"] += 1

# divide by total number of data points for probability
for state in vsf_bn:
    vsf_bn[state] /= len(dataset) 

# add vsf child node 
vsf = Node(DiscreteDistribution({
    "low": vsf_bn["low"],
    "medium": vsf_bn["medium"],
    "high": vsf_bn["high"]
}), name="vsf")

# DISTANCE between nodes and nearest bus
# create dictionary for distance states
# count how many low, medium, and high distances are present in the current dataset
distance_bn = {}
distance_bn["low"] = 0
distance_bn["medium"] = 0
distance_bn["high"] = 0

# distance thresholds to divide into different states 
d_low_t = 5 
d_high_t = 20 # made up values, not sure of the precise ones

# add data to dictionary
for node in dataset:
    if dataset[node][1] <= d_low_t:
        distance_bn["low"] += 1
    elif dataset[node][1] <= d_high_t:
        distance_bn["medium"] += 1
    else:
        distance_bn["high"] += 1

# divide by total number of data points for probability
for state in distance_bn:
    distance_bn[state] /= len(dataset)

# add distance child node 
distance = Node(DiscreteDistribution({
    "low": distance_bn["low"],
    "medium": distance_bn["medium"],
    "high": distance_bn["high"]
}), name="distance")

# CONGESTION
# create dictionary for congestion states
# count how many low and high congestion areas are present in the current dataset
congestion_bn = {}
congestion_bn["low"] = 0
congestion_bn["high"] = 0

# dictionary that maps city locations to the probability that the area is highly congested
congestion_probabilities = { # using test system 2 probabilities
    "Residential": 0.72,
    "School": 0.153,
    "Office": 0.198,
    "Market": 0.54
}

for node in dataset:
    base_prob = congestion_probabilities[dataset[node][2]] # get the probability that the area is congested from congestion_probabilities dicitonary
    rand_int = random.random() # generate random number from 0-1
    # categorize as high or low congestion
    if rand_int < base_prob:
        congestion_bn["high"] += 1
    else:
        congestion_bn["low"] += 1

# divide by total number of data points for probability
for state in congestion_bn:
    congestion_bn[state] /= len(dataset)

# add congestion child node 
congest = Node(DiscreteDistribution({
    "low": congestion_bn["low"],
    "high": congestion_bn["high"]
}), name="congest")

# construction of candidate data table based on following assumptions
# assumptions for probabilities
# * high vsf is bad, low vsf is good | 1/12, 9/12, 11/12
# * high congestion is good, low is bad | 1, 9/12
# * high distance is bad, low is good | 3/12, 10/12, 11/12

# Candidate node is conditional on vsf, congestion, and distance
candidate = Node(ConditionalProbabilityTable([
    ["low", "low", "low", "yes", 11 * 9 * 11 / 1728],
    ["low", "low", "low", "no", 1 - 11 * 9 * 11 / 1728],
    ["low", "low", "medium", "yes", 11 * 9 * 10 / 1728],
    ["low", "low", "medium", "no", 1 - 11 * 9 * 10 / 1728],
    ["low", "low", "high", "yes", 11 * 9 * 3 / 1728],
    ["low", "low", "high", "no", 1 - 11 * 9 * 3 / 1728],
    ["low", "high", "low", "yes", 11 * 12 * 11 / 1728],
    ["low", "high", "low", "no", 1 - 11 * 12 * 11 / 1728],
    ["low", "high", "medium", "yes", 11 * 12 * 10 / 1728],
    ["low", "high", "medium", "no", 1 - 11 * 12 * 10 / 1728],
    ["low", "high", "high", "yes", 11 * 12 * 3 / 1728],
    ["low", "high", "high", "no", 1 - 11 * 12 * 3 / 1728],
    ["medium", "low", "low", "yes", 9 * 9 * 11 / 1728],
    ["medium", "low", "low", "no", 1 - 9 * 9 * 11 / 1728],
    ["medium", "low", "medium", "yes", 9 * 9 * 10 / 1728],
    ["medium", "low", "medium", "no", 1 - 9 * 9 * 10 / 1728],
    ["medium", "low", "high", "yes", 9 * 9 * 3 / 1728],
    ["medium", "low", "high", "no", 1 - 9 * 9 * 3 / 1728],
    ["medium", "high", "low", "yes", 9 * 12 * 11 / 1728],
    ["medium", "high", "low", "no", 1 - 9 * 12 * 11 / 1728],
    ["medium", "high", "medium", "yes", 9 * 12 * 10 / 1728],
    ["medium", "high", "medium", "no", 1 - 9 * 12 * 10 / 1728],
    ["medium", "high", "high", "yes", 9 * 12 * 3 / 1728],
    ["medium", "high", "high", "no", 1 - 9 * 12 * 3 / 1728],
    ["high", "low", "low", "yes", 1 * 9 * 11 / 1728],
    ["high", "low", "low", "no", 1 - 1 * 9 * 11 / 1728],
    ["high", "low", "medium", "yes", 1 * 9 * 10 / 1728],
    ["high", "low", "medium", "no", 1 - 1 * 9 * 10 / 1728],
    ["high", "low", "high", "yes", 1 * 9 * 3 / 1728],
    ["high", "low", "high", "no", 1 - 1 * 9 * 3 / 1728],
    ["high", "high", "low", "yes", 1 * 12 * 11 / 1728],
    ["high", "high", "low", "no", 1 - 1 * 12 * 11 / 1728],
    ["high", "high", "medium", "yes", 1 * 12 * 10 / 1728],
    ["high", "high", "medium", "no", 1 - 1 * 12 * 10 / 1728],
    ["high", "high", "high", "yes", 1 * 12 * 3 / 1728],
    ["high", "high", "high", "no", 1 - 1 * 12 * 3 / 1728],
], [vsf.distribution, congest.distribution, distance.distribution]), name="candidate")

# Create a Bayesian Network and add states
model = BayesianNetwork()
model.add_states(vsf, congest, distance, candidate)
print("model created")

# Add edges connecting nodes
model.add_edge(vsf, candidate)
model.add_edge(congest, candidate)
model.add_edge(distance, candidate)

# Finalize model
model.bake()
print("model finalized")

# DETERMINE CANDIDATES
candidates = []

for node in dataset:
    # map node data to the states for vsf, congestion, and distance respectively
    if dataset[node][0] <= low_threshold:
        vsf_input = "low"
    elif dataset[node][0] <= high_threshold:
        vsf_input = "medium"
    else:
        vsf_input = "high"

    congest_val = congestion_probabilities[dataset[node][2]]
    if congest_val < base_prob:
        congest_input = "high"
    else:
        congest_input = "low"

    if dataset[node][1] <= d_low_t:
        dist_input = "low"
    elif dataset[node][1] <= d_high_t:
        dist_input = "medium"
    else:
        dist_input = "high"

    # find probability of success
    given = model.predict_proba({
    "vsf": vsf_input,
    "congest": congest_input,
    "distance": dist_input
    })
    probability = given[3].probability("yes")

    # determine whether the node is a candidate using the probability computed above
    rand_int = random.random()
    if rand_int <= probability:
        candidates.append(node)

print(candidates)

# import Final1 # for graphical representation