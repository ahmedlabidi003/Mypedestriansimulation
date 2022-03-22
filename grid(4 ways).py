#!/usr/bin/env python
"""
Agent-Based Pedestrian Simulation Model
=======================================
This is an agent-based simulation of three types of  moving in a confined space.

The code has been commented extensively. I will provide a brief overview of the overarching logic of the program here;
for detail on each part of the program see the relevant documentation string. I would suggest starting with the code
in the execution section of the file near the bottom.

The simulation consists of a number of Python objects that interact with each other. The Grid object contains a set of
Cell objects which can either be unoccupied or occupied by one of the three agents described below. The Grid is
initialized and populated (see Grid.initialize() and Grid.populate()) by placing agents in their initial positions.

The Grid is responsible for playing each turn. Each turn iterates through the three agent types and allows each agent on
the board to make a request to move to a certain cell based on their particular logic.

After each agent types turn (so after all the A's have gone, for example) the Grid removes all the agents that have
reached their final destination (see Grid.clean_up()) before starting a new turn.

Each agent has the option of requesting a "swap" from another agent. This request is handled by the Grid and passed to
the agent which is receiving the request. They will respond according to their logic (if they have not moved and it
serves their objectives they will accept - see TypeA.check_swap() for an example)

Agents
======
There are three types of agents (A, B, and C) in the simulation. Each agent is given an initial location and a final destination and
will proceed from their origin to their destination according to the following rules:

Type A - "Movers"
=================
Type A agents will always move towards their desitnation if there is an option to move that will take them closer to
that destination. They will take the shortest path if it's available. If there is no move that will bring them
closer to their destination, they will stay put.

Type B - "Distance Minimizers"
==============================
Type B agents will always move towards their destination along the shortest path possible. If the shortest path move
is not available, they will stay put.

Type C - "Tourist"
==================
Type C agents will survey their surrounding cells and randomly choose an unoccupied cell to move into. If there are no
unoccupied cells, they will stay put.
"""

__author__ = "Ahmed Labidi"
__credits__ = ["Ahmed Labidi"]
__version__ = "0.1"
__status__ = "Development"


import csv   # Used for handling CSV files nicely
import math  # Used for all the mathematical needs
import tkinter
#from TurtleWorld import *
import random  # Used for generating random numbers and choices
import matplotlib.pyplot as plt  # Used for plotting things as needed
from matplotlib.backends.backend_pdf import PdfPages  # Used to create PDF plots
import numpy as np  # Used for various data-related tasks including some mathematical ones
from crosswalk_free_flow import generate_file  # See "crosswalk_free_flow.py"

# This defines how many moves the Type C agents will move before they are done.
MAX_C_MOVES = 40




def shortest_path(a, b):
    """
    A utility function to find the shortest straight-line path between two Cells on the Grid. Returns the Cell
    coordinates adjacent to 'a' which match the shortest path
    :param a: The first Cell object
    :param b: The second Cell object
    :rtype: tuple
    """
    loc = a.loc
    des = b.loc
    if a.loc == b.loc:
        return a.loc
    vec = [des[0] - loc[0], des[1] - loc[1]]
    # Normalize and then set to -1, 1, or 0
    norm = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
    vec = [vec[0] / norm, vec[1] / norm]
    for x in range(2):
        if vec[x] > 0:
            vec[x] = 1
        elif vec[x] < 0:
            vec[x] = -1
        else:
            vec[x] = 0
    return loc[0] + vec[0], loc[1] + vec[1]


def norm(a, b):
    """
    Calculate the normalized distance between two Cell locations.
    :param a: The first Cell object
    :param b: The second Cell object
    :return: The distance between the two cell locations
    """
    des = b.loc
    loc = a.loc
    vec = [des[0] - loc[0], des[1] - loc[1]]
    dist = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
    return dist


class Grid:
    def __init__(self, width, height, verbose=False):
        """
        The grid acts as the controller for all the Cells and the Agents.
        :param width: Sets the width of the Grid
        :param height: Sets the height of the Grid
        :param verbose: Sets whether or not to output every logic step. Default is False.
        """
        self.grid = []  # This will be a 2D list of Cells (so a list of rows)
        self.width = width
        self.height = height
        self.playerAs = []  # Holds the list of all the TypeA agents
        self.playerBs = []  # Holds the list of all the TypeB agents
        self.playerCs = []  # Holds the list of all the TypeC agents
        self.playerDs = []  # Holds the obstacles list
        self.finishedAs = []  # Holds the list of all the TypeA agents removed from the board
        self.finishedBs = []  # Holds the list of all the TypeB agents removed from the board
        self.finishedCs = []  # Holds the list of all the TypeC agents removed from the board
        self.verbose = verbose  # True/False flag of whether or not to provide output during the program.
        self.turn = 0  # Turn counter

    def initialize(self):

        """
        Creates a grid of unoccupied Cell objects according to the specified height and width.
        """
        # First we create the empty cells
        for s in range(self.height):
            grid_row = []
            for r in range(self.width):
                grid_row.append(Cell(r, s))  # Creates a row of cells
            self.grid.append(grid_row)  # Adds the row of cells to the grid list

        # Then we link the Cell objects together so we can easily access the adjacent Cells
        for r in range(self.height):
            for s in range(self.width):
                c = self.grid[r][s]
                for delta_i in range(-1, 2):
                    for delta_j in range(-1, 2):
                        x = r + delta_i
                        y = s + delta_j
                        try:
                            if x < 0 or y < 0:
                                raise IndexError
                            adjacent = self.grid[x][y]
                            c.adjacent.append(adjacent)
                        # This catches and ignores the cases where we are looking for adjacent cells outside the Grid
                        except IndexError:
                            pass

    def populate(self, filename):
        # Populate the grid (remember) x and y are reversed)
        """
        Populates the grid according to a CSV file that contains the agent type and the starting and end locations
        of the agents. File should have rows consisting of Type, x1, y1, x2, y2
        :param filename:
        """
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                s = self.grid[int(row[2])][int(row[1])]  # Extracts the starting coordinates
                e = self.grid[int(row[4])][int(row[3])]  # Extracts the end coordinates
                if row[0][0] == "A":  # If the symbol is "A" it'll put Type A, etc.
                    p = TypeA(s, e, row[0][1:3],  self)
                    self.playerAs.append(p)

                elif row[0][0] == "B":
                    p = TypeB(s, e, row[0][1:3], self)
                    self.playerBs.append(p)
                elif row[0][0] == "D":
                    p = TypeD(s, s, self)
                    self.playerDs.append(p)
                else:
                    p = TypeC(s, e, row[0][1:3], self)
                    self.playerCs.append(p)
        """for i in range(12,19):
           for j in range(12,19):
               s = (i,j)
               p = TypeD(s, s, self)
               self.playerDs.append(p)"""




    def clean_up(self):
        """
        This function goes through all the agents and removes any from the board that have
        reached their destination.
        """
        # The same logic works for each of the three types
        for a in self.playerAs:  # Iterate through all the TypeAs
            if a.end == a.cell:  # If the current location matches the final destination...
                if self.verbose:
                    print("Removing {} at {},{}".format(a.symbol, a.cell.loc[0], a.cell.loc[1]))
                a.cell.occupant = None  # Make sure the cell is set as empty
                self.finishedAs.append(a)  # Put the agent in the 'finished' list
                self.playerAs.remove(a)  # Remove the agent from the 'active' list.
        for b in self.playerBs:
            if b.end == b.cell:
                if self.verbose:
                    print("Removing {} at {},{}".format(b.symbol, b.cell.loc[0], b.cell.loc[1]))
                b.cell.occupant = None
                self.finishedBs.append(b)
                self.playerBs.remove(b)
        for c in self.playerCs:
            if c.end == c.cell or c.move_count > MAX_C_MOVES:
                c.cell.occupant = None
                self.finishedCs.append(c)
                self.playerCs.remove(c)

    def play_turn(self, turn, Nturn):
        """
        Plays one turn of the game, cleaning up the board after each set of players has moved.
        """
        if self.verbose:
            print("As are going")
        random.shuffle(self.playerAs)  # Each set of agent types plays randomly each turn.
        for a in self.playerAs:
                a.move()
        random.shuffle(self.playerBs)
        self.clean_up()
        if self.verbose:
            print("Bs are going")
        for b in self.playerBs:
                b.move()
        self.clean_up()
        if self.verbose:
            print("Cs are going")
        random.shuffle(self.playerCs)
        for c in self.playerCs:
                if turn<=(Nturn/3):
                    c.move2()
                elif (Nturn/3)<turn<=(Nturn*2/3):
                    c.move3()
                elif (Nturn*2/3)<turn<=Nturn:
                    c.move1()

        self.clean_up()
        # Set all the agents as being ready to move again
        for a in self.playerAs:
            a.reset()
        for b in self.playerBs:
            b.reset()
        for c in self.playerCs:
            c.reset()

        # Increment the turn counter
        self.turn += 1

    def cell(self, loc):
        """
        A utility function to find the Cell object at a given location
        :param loc: A tuple specifying the location of the cell requested
        :return: The Cell object at the location
        """
        return self.grid[loc[1]][loc[0]]

    def display(self):
        """
        Utility function which prints the current grid state to the screen.
        """
        print("=========")
        for c in range(self.height):
            print(" ".join([self.grid[c][j].get_symbol() for j in range(self.width)]))

    def display_plot(self, save=True):
        """
        Plot the current state of the grid, with the option to save it as a PDF with the filename turn_x where x is
        the turn number
        :param save: Boolean flag to indicate whether to save.
        """
        with PdfPages('turn_{}.pdf'.format(self.turn)) as pdf:
            # This follows mainly the instructions on plotting a grid of cells in matplotlib.
            nrows, ncols = self.height, self.width
            data_list = []
            for r in self.grid:
                data_list.append([x.get_value() for x in r])
            image = np.array(data_list)

            # Reshape things into a grid
            image = image.reshape((nrows, ncols))

            row_labels = range(nrows)
            col_labels = range(ncols)
            plt.matshow(image, cmap = plt.cm.gray, vmin=0, vmax=3)
            plt.xticks(range(ncols), col_labels)
            plt.yticks(range(nrows), row_labels)
            if save:
                pdf.savefig()
            plt.show()

    def print_states(self):
        """
        Utility function whichprintss to the screen all the active agents in the game and their destination.
        """
        for a in self.playerAs:
                print("{}{} at {},{} with destination {},{}".format(a.symbol, a.id, a.cell.loc[0], a.cell.loc[1], a.end.loc[0], a.end.loc[1]))
        for b in self.playerBs:
            print("{}{} at {},{} with destination {},{}".format(b.symbol, b.id, b.cell.loc[0], b.cell.loc[1], b.end.loc[0], b.end.loc[1]))
        for c in self.playerCs:
            print("{}{} at {},{} with destination {},{}".format(c.symbol, c.id, c.cell.loc[0], c.cell.loc[1], c.end.loc[0], c.end.loc[1]))
        #for d in self.playerDs:
            #print("{} at {},{}".format(c.symbol, c.cell.loc[0], c.cell.loc[1])


class Cell:
    def __init__(self, x, y):
        self.loc = (x, y)  # The x and y tuple coordinates
        self.symbol = "X"  # The symbol used for printing
        self.adjacent = []  # List of accessible adjacent cells
        self.occupant = None  # Boolean flag indicating if the cell is occupied
        self.requester = None  # OBSOLETE Type object indicating if there is someone requesting to move into it.

    def get_symbol(self):
        """
        Utility function which looks up the symbol at a given cell based on its occupant (or lack thereof)
        :return: A single letter indicating the symbol.
        """
        if self.occupant:
            return self.occupant.symbol
        else:
            return self.symbol

    def get_value(self):
        """
        Utility function which looks up the numerical value at a given cell based on its occupant to aid with printing
        :return: An integer indicating the greyscale value of the object
        """
        if self.occupant:
            return self.occupant.value
        else:
            return 1


class TypeA:
    def __init__(self, start, end, id, grid):
        self.symbol = "A"  # The symbol used for printing
        self.id = id
        self.value = 0  # The value used for plotting
        self.grid = grid  # The parent grid the agent lives on
        self.cell = start  # The starting Cell
        self.end = end  # The destination Cell
        self.cell.occupant = self  # Sets the starting cell as occupied with itself
        self.moves = []  # The list of moves the agent will make
        self.moved = False  # A Boolean flag indicating if the agent has moved

    def reset(self):
        """
        Rests the agent's movement for the next turn
        """
        self.moved = False

    def total_distance(self):
        """
        Utility function which calculates the total distanced moved by the agent
        :return: Distance moved (integer)
        """
        dist_count = 0
        for move in self.moves:
            if move[0] != move[1]:
                dist_count += 1
        return dist_count

    def print_moves(self):
        """
        Utility function which prints all the moves of the agent to the screen.
        """
        for move in self.moves:
            print(move)

    def move(self):
        """
        Causes the agent to go through its particular move logic.
        """
        if not self.moved:
            start = self.cell.loc  # Define the starting location
            # Look at the available choices
            choices = [j for j in self.cell.adjacent if ((not j.occupant) and j != self.cell and j.symbol != "D")]
            choice_pair = []
            # Go through the possible choices and find out which one is best
            for k in choices:
                des = self.end.loc
                loc = k.loc
                vec = [des[0] - loc[0], des[1] - loc[1]]
                normal = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
                choice_pair.append((k, normal))
            # Sort by shortest distance
            choice_pair = sorted(choice_pair, key=lambda x: x[1])
            # If there's a choice to take...
            if len(choice_pair) > 0:
                cell = choice_pair[0][0]
                if self.grid.verbose:
                    print("{} at {},{} moving to {},{}".format(self.symbol, self.cell.loc[0], self.cell.loc[1], cell.loc[0], cell.loc[1]))
                # Move to that cell
                prev = self.cell
                self.cell = cell
                prev.occupant = None
                self.cell.occupant = self

            # Otherwise, stay put.
            end = self.cell.loc
            if start == end and self.grid.verbose:
                print("{} at {},{} staying put.".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
            self.moves.append((start, end))
            self.moved = True
        elif self.grid.verbose:
            print("{} at {},{} has already moved this turn".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))

    def check_swap(self, cell):
        # Check if swapping would be advantageous to the player and act accordingly
        if self.grid.verbose:
            print("{} at {},{} was asked for a swap".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))

        if norm(cell, self.end) < norm(self.cell, self.end) and self.grid.verbose:
            print("{} at {},{}: Swapping would be advantageous".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
        if self.moved and self.grid.verbose:
            print("{} at {},{}: Alas, I've already moved!".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))

        if norm(cell, self.end) < norm(self.cell, self.end) and not self.moved:
            self.moved = True
            return True
        else:
            return False


class TypeB:
    # See TypeA for the definitions of common functions and variables.
    def __init__(self, start, end, id, grid):
        self.symbol = "B"
        self.id = id
        self.value = 3
        self.grid = grid
        self.cell = start
        self.end = end
        self.cell.occupant = self
        self.moves = []
        self.moved = False

    def reset(self):
        self.moved = False

    def print_moves(self):
        for move in self.moves:
            print(move)

    def total_distance(self):
        dist_count = 0
        for move in self.moves:
            if move[0] != move[1]:
                dist_count += 1
        return dist_count

    def shortest_path_between(self):
        if not self.moved:
            cellul = self.cell  # Define the starting location
            # Look at the available choices
            choices = [j for j in self.cell.adjacent if ( j != self.cell and j.symbol != "D")]
            choice_pair = []
            # Go through the possible choices and find out which one is best
            for k in choices:
                des = self.end.loc
                loc = k.loc
                vec = [des[0] - loc[0], des[1] - loc[1]]
                normal = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
                choice_pair.append((k, normal))
            # Sort by shortest distance
            choice_pair = sorted(choice_pair, key=lambda x: x[1])
            # If there's a choice to take...
            if len(choice_pair) > 0:
                cellul = choice_pair[0][0]
        return cellul.loc




    def move(self):
        if self.grid.verbose:
            print("{} at {},{}, You're up!".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
        if not self.moved:
            if self.grid.verbose:
                print("{} at {},{}: Haven't moved yet... let's see.".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
            start = self.cell.loc
            # Find the shortest path
            coords = self.shortest_path_between()
            best_choice = None
            # Look up the best choice by coordinates
            for cell in self.cell.adjacent:
                if cell.loc == coords:
                    best_choice = cell

            if self.grid.verbose:
                print("{} at {},{}: My best choice is {},{}".format(self.symbol, self.cell.loc[0], self.cell.loc[1], best_choice.loc[0], best_choice.loc[1]))
            # If someone is in the preferred choice, ask to swap with them!
            if best_choice.occupant:
                if self.grid.verbose:
                    print("Cell is occupied... asking for a swap with a type {}".format(best_choice.occupant.symbol))
                # Check if a swap is possible
                if best_choice.occupant.check_swap(self.cell) and best_choice.occupant.symbol != "D" :
                    if self.grid.verbose:
                        print("{} at {},{}: Swap accepted!".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
                    prev = self.cell
                    partner = best_choice.occupant
                    self.cell = best_choice
                    best_choice.occupant = self
                    partner.cell = prev
                    partner.cell.occupant = partner


                # Otherwise do nothing
                elif self.grid.verbose:
                    print("{} at {},{}: Swap rejected. Staying put.".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
            else:
                # Move to that cell if all is clear
                if self.grid.verbose:
                    print("{} at {},{} moving to {},{}".format(self.symbol, self.cell.loc[0], self.cell.loc[1], best_choice.loc[0], best_choice.loc[1]))
                prev = self.cell
                self.cell = best_choice
                prev.occupant = None
                self.cell.occupant = self
            end = self.cell.loc
            self.moves.append((start, end))
            self.moved = True
        else:
            if self.grid.verbose:
                print("{} at {},{} has already moved this turn".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))

    def check_swap(self, cell):
        # Does the cell move me directly to my destination? If yes, then accept it.
        if self.grid.verbose:
            print("{} at {},{} was asked for a swap".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
        coords = shortest_path(self.cell, self.end)
        if coords == cell.loc and self.grid.verbose:
            print("{} at {},{}: Swapping would be advantageous".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
        if self.moved and self.grid.verbose:
            print("{} at {},{}: Alas, I've already moved!".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
        if coords == cell.loc and not self.moved:
            self.moved = True
            return True
        else:
            return False


class TypeC:
    # See TypeA for common definitions of variables and functions
    def __init__(self, start, end, id, grid):
        self.symbol = "C"
        self.id = id
        self.value = 2
        self.grid = grid
        self.cell = start
        self.end = end
        self.cell.occupant = self
        self.moves = []
        self.moved = False
        self.move_count = 0

    def reset(self):
        self.moved = False

    def total_distance(self):
        dist_count = 0
        for move in self.moves:
            if move[0] != move[1]:
                dist_count += 1
        return dist_count

    def move1(self):
        start = self.cell.loc
        choices = self.cell.adjacent
        choices = [i for i in choices if not i.occupant]
        if len(choices) > 0:
            choice = random.choice(choices)
            # Move to that cell
            prev = self.cell
            self.cell = choice
            prev.occupant = None
            self.cell.occupant = self
            end = self.cell.loc
            self.moves.append((start, end))
        self.move_count += 1

    def move2(self):
        """
        like type A moves, for a short period of time

        Causes the agent to go through its particular move logic.
        """
        if not self.moved:
            start = self.cell.loc  # Define the starting location
            # Look at the available choices
            choices = [j for j in self.cell.adjacent if not j.occupant and j != self.cell]
            choice_pair = []
            # Go through the possible choices and find out which one is best
            for k in choices:
                des = self.end.loc
                loc = k.loc
                vec = [des[0] - loc[0], des[1] - loc[1]]
                normal = math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])
                choice_pair.append((k, normal))
            # Sort by shortest distance
            choice_pair = sorted(choice_pair, key=lambda x: x[1])
            # If there's a choice to take...
            if len(choice_pair) > 0:
                cell = choice_pair[0][0]
                if self.grid.verbose:
                    print("{} at {},{} moving to {},{}".format(self.symbol, self.cell.loc[0], self.cell.loc[1],
                                                               cell.loc[0], cell.loc[1]))
                # Move to that cell
                prev = self.cell
                self.cell = cell
                prev.occupant = None
                self.cell.occupant = self

            # Otherwise, stay put.
            end = self.cell.loc
            if start == end and self.grid.verbose:
                print("{} at {},{} staying put.".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
            self.moves.append((start, end))
            self.moved = True
        elif self.grid.verbose:
            print("{} at {},{} has already moved this turn".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))

    def move3(self):

        start = self.cell.loc
        end = self.cell.loc
        self.moves.append((start, end))
        self.move_count += 1


    def check_swap(self, cell):  # Even though 'cell' is not used here it needs to exist as a placeholder to match A/B
        # Flip a coin, pretty simple.
        return bool(random.randint(0, 1))



class TypeD:
    def __init__(self, start, end, grid):
        self.symbol = "D"  # The symbol used for printing
        self.value = 2.5  # The value used for plotting
        self.id = 0
        self.grid = grid  # The parent grid the agent lives on
        self.cell = start  # The starting Cell
        self.end = end  # The destination Cell
        self.cell.occupant = self  # Sets the starting cell as occupied with itself
        self.moves = []  # The list of moves the agent will make
        self.moved = False  # A Boolean flag indicating if the agent has moved

    def check_swap(self, cell):
        # Does the cell move me directly to my destination? If yes, then accept it.
        if self.grid.verbose:
            print("{} at {},{} was asked for a swap".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
        coords = shortest_path(self.cell, self.end)
        if coords == cell.loc and self.grid.verbose:
            print("{} at {},{}: Swapping would be advantageous".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
        if self.moved and self.grid.verbose:
            print("{} at {},{}: Alas, I've already moved!".format(self.symbol, self.cell.loc[0], self.cell.loc[1]))
        if coords == cell.loc and not self.moved:
            self.moved = True
            return True
        else:
            return False



if __name__ == "__main__":
    avgA_dist = []
    avgB_dist = []
    avgA_time = []
    avgB_time = []
    avgC_dist = []
    avgC_time = []

    # Play 1000 games
    for r in range(1):
        generate_file()  # Creates a randomly populated file.
        grid = Grid(50, 20, verbose=False)  # Create the grid
        grid.initialize()  # Initialize it (should always have this and the above together)
        grid.populate('free_flow_crosswalk.csv')  # Populate it with the file
        grid.display_plot()
        grid.display()

        print("pourcentage of people in the grid : {} ".format(
            len(grid.playerAs + grid.playerBs + grid.playerCs) / (grid.width * grid.height)))
        print("pourcentage of A people in the grid : {} ".format(len(grid.playerAs) / (grid.width * grid.height)))
        print("pourcentage of B people in the grid : {} ".format(len(grid.playerBs) / (grid.width * grid.height)))
        print("pourcentage of C people in the grid : {} ".format(len(grid.playerCs) / (grid.width * grid.height)))
        print(len(grid.playerCs))
        print(len(grid.playerBs))
        print(len(grid.playerAs))
        aa=len(grid.playerAs)
        bb=len(grid.playerBs)
        cc=len(grid.playerCs)

        print("number of people: {}".format(aa+bb+cc))

    with open('mydata.csv', 'w', newline='') as f:
        writer = csv.writer(f)

        Nturn = input("Give me the number of turns ")
        Nturn=int(Nturn)
        for i in range(Nturn):  # Play 40 turns (should be enough, haven't added an "end game" check.
            grid.play_turn(i, Nturn)
            grid.display_plot()
            # grid.display()
            grid.print_states()
            writer.writerow([i])
            for a in grid.playerAs:
                writer.writerow([a.symbol, a.id, a.cell.loc[0], a.cell.loc[1], a.end.loc[0], a.end.loc[1]])
            for b in grid.playerBs:
                writer.writerow([b.symbol, b.id, b.cell.loc[0], b.cell.loc[1], b.end.loc[0], b.end.loc[1]])
            for c in grid.playerCs:
                writer.writerow([c.symbol, c.id, c.cell.loc[0], c.cell.loc[1], c.end.loc[0], c.end.loc[1]])

        distance = 0
        time = 0
        """for typeA in grid.finishedAs:
            distance += typeA.total_distance()
            time += len(typeA.moves)
        avgA_dist.append(float(distance) / len(grid.finishedAs))
        avgA_time.append(float(time) / len(grid.finishedAs))
        distance = 0
        time = 0
        for typeB in grid.finishedBs:
            distance += typeB.total_distance()
            time += len(typeB.moves)
        avgB_dist.append(float(distance) / len(grid.finishedBs))
        avgB_time.append(float(time) / len(grid.finishedBs))
        distance = 0
        time = 0
        for typeC in grid.finishedCs:
            distance += typeC.total_distance()
            time += len(typeC.moves)
        avgC_dist.append(float(distance) / len(grid.finishedCs))
        avgC_time.append(float(time) / len(grid.finishedCs))"""


    #grid.display()


    """print("After 1000 iterations")

    print("pourcentage of people in the grid : {} ".format(
        len(grid.playerAs + grid.playerBs + grid.playerCs) / (grid.width * grid.height)))

    a = (sum(avgA_dist) / float(len(avgA_dist)))
    b = (sum(avgA_time) / float(len(avgA_time)))
    c = (sum(avgB_dist) / float(len(avgB_dist)))
    d = (sum(avgB_time) / float(len(avgB_time)))
    e = (sum(avgC_dist) / float(len(avgC_dist)))
    f = (sum(avgC_time) / float(len(avgC_time)))

    print("Average distance for A: {}".format(sum(avgA_dist) / float(len(avgA_dist))))
    print("Average distance for B: {}".format(sum(avgB_dist) / float(len(avgB_dist))))
    print("Average time for A: {}".format(sum(avgA_time) / float(len(avgA_time))))
    print("Average time for B: {}".format(sum(avgB_time) / float(len(avgB_time))))
    print("Average distance for C: {}".format(sum(avgC_dist) / float(len(avgC_dist))))
    print("Average time for C: {}".format(sum(avgC_time) / float(len(avgC_time))))
    print("Number of obstacles: {} , Density of obstacles: {} ".format(float(len(grid.playerDs)),
                                                                       float(len(grid.playerDs)) / (
                                                                               grid.width * grid.height)))

    print("Average speed for A: {}".format((a / b)))
    print("Average speed for B: {}".format(c / d))
    print("Average speed for C: {}".format(e / f))

    print("flow A: {}".format(aa/(sum(avgA_time) / float(len(avgA_time)))))
    print("flow B: {}".format(bb/(sum(avgB_time) / float(len(avgB_time)))))
    print("flow C: {}".format(cc/(sum(avgC_time) / float(len(avgC_time)))))"""


    #grid.display_plot()

    #grid.print_states()
    print([i.cell.loc for i in grid.playerCs])
