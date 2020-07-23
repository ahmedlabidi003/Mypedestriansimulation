"""
Generate a file to be used to populate the crosswalk.
"""

import random

# Adjust these as needed for various dimensions.
HEIGHT = 20
WIDTH = 50
W_MIN = 0  # These define the bounding box in which we will place the agents.
W_MAX = 6
H_MIN = 7
H_MAX = 13
PROB_A = 0.5
PROB_B = 0.3
PROB_C = 0.15
# The leftover probability will be considered "EMPTY" probability.


def generate_file():  # Create a random starting scenario according to the above specificiations
    to_write = []
    a = 1
    b = 1
    c = 1
    for x in range(W_MIN, W_MAX):
        for y in range(H_MIN, H_MAX):
            # Randomly choose which type of Agent. Their destination is always directly opposite.
            roll = random.random()
            if roll < PROB_A:
                to_write.append("A{},{},{},{},{}".format(a, x, y, 49, random.randint(7,12)))
                a = a + 1
            elif roll < PROB_A + PROB_B:
                to_write.append("B{},{},{},{},{}".format(b, x, y, 49, random.randint(7,12)))
                b = b + 1
            elif roll < PROB_A + PROB_B + PROB_C:
                to_write.append("C{},{},{},{},{}".format(c, x, y, 49, random.randint(7,12)))
                c = c + 1

    for x in range(W_MIN, W_MAX):
        for y in range(H_MIN, H_MAX):
            # Randomly choose which type of Agent. Their destination is always directly opposite.
            roll = random.random()
            if roll < PROB_A:
                to_write.append("A{},{},{},{},{}".format(a, 49-x, y, 1, random.randint(7,12)))
                a = a + 1
            elif roll < PROB_A + PROB_B:
                to_write.append("B{},{},{},{},{}".format(b, 49-x, y, 1, random.randint(7,12)))
                b = b + 1
            elif roll < PROB_A + PROB_B + PROB_C:
                to_write.append("C{},{},{},{},{}".format(c, 49-x, y, 1, random.randint(7,12)))
                c = c + 1

    for i in range(0, 50): #These two loops are for the obsctacles in the grid (to shape the T junction)
        for j in range(0, 7):
            to_write.append("D,{},{},{},{}".format(i, j, i, j))
            to_write.append("D,{},{},{},{}".format(i, j+13, i, j+13))
            #to_write.append("D,{},{},{},{}".format(i+28, j, i+28, j))
            #to_write.append("D,{},{},{},{}".format(i+28, j+13, i+28, j+13))

    with open("free_flow_crosswalk.csv", "w") as outfile:
        outfile.write("\n".join(to_write))
