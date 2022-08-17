import random
from turtle import pos
import numpy as np

#              (    sq,   y,   x)
# Convert from (square, row, col) format of np array to (x, y) on sudoku board
def calculateGlobalXY(square, row, col):
    sq_x = square % 3
    sq_y = square // 3
    X = sq_x * 3 + col
    Y = sq_y * 3 + row

    return (X, Y)

#                                           (    sq,   y,   x)
# Convert from (x, y) format of np array to (square, row, col) on sudoku board
def calculateSqRowCol(x, y):
    square = 3*(y // 3) + (x // 3)
    row = y % 3
    col = x % 3

    return (square, row, col)

# Create 4-dim np array representing sudoku board
def initBoard():
    board = np.ones((9,3,3,9))
    
    return board

# Returns the index of the first possibility of a space
# Used to get the value of collapsed spaces (spaces with only 1 possibility)
def getValue(board, space):
    square, row, col = space
    return np.nonzero(board[square][row][col])[0][0]

# Count the number of spaces that need to choose a value
def countUnsolved(board):
    unsolvedSpaces = 0

    for square in board:
        for y in square:
            for x in y:
                if np.count_nonzero(x) > 1:
                    unsolvedSpaces += 1
    
    return unsolvedSpaces

# Print visual representation of board.
# Blank squares have multiple possibilities.
def printBoard(board):
    for y in range(9):
        for x in range(9):
            square, row, col = calculateSqRowCol(x, y)

            possibilities = np.nonzero(board[square][row][col])[0]

            if len(possibilities) != 1:
                print("| ", end='')
            else:
                print(f"|{possibilities[0]+1}", end='')
            
        print('|')
    print()

# Print visual representation of finished board.
# Red numbers indicate flaws
def printBoardFlaws(board, flaws_board):
    red = "\u001b[31m"
    white = "\033[0m"

    for y in range(9):
        for x in range(9):
            square, row, col = calculateSqRowCol(x, y)
            val = getValue(board, (square, row, col))

            if flaws_board[square][row][col]:
                print(f"|{red}{val}{white}", end='')
            else:
                print(f"|{val}", end='')
            
        print('|')
    print()

# Print visual representation of board.
# Number correspond to remaining possible values (Entropies)
def printBoardEs(board):
    for y in range(9):
        for x in range(9):
            square, row, col = calculateSqRowCol(x, y)

            possibilities = np.nonzero(board[square][row][col])[0]
            print(f"|{len(possibilities)}", end='')
            
        print('|')
    print()
        
# Locate square with the lowest entropy (least possibilities)
# Ties are decided by python's random function
# Solved spaces (entropy == 1) are not counted
def lowestEntropy(board):
    # 2d List storing [square, y, x] of lowest entropy places
    lowest = []
    # Lowest seen entropy so far
    lowestE = 9

    # Loop through every space
    for square in range(9):
        for row in range(3):
            for col in range(3):
                # Find number of possibilities left
                possibilities = np.nonzero(board[square][row][col])[0]
                entropy = len(possibilities)

                # If the entropy is lower than the current lowest, update lowestE and clear list of higher entropy spaces
                if entropy < lowestE and entropy > 1:
                    lowestE = entropy
                    lowest = [(square, row, col)]
                # If the entropy is equal to the current lowest, add this space to the list
                elif entropy == lowestE:
                    lowest.append((square, row, col))
    
    # Return random space from list of lowest spaces
    # If there is only 1, that one is returned
    return random.choice(lowest)

# Get the value of this space from the possible values
def collapseValue(board, space):
    square, row, col = space
    possibilities = np.nonzero(board[square][row][col])[0]

    return random.choice(possibilities)

# Remove all possibilities other than those in plist
def updateSpace(board, space, plist):
    square, row, col = space

    for i in range(9):
        if i not in plist:
            board[square][row][col][i] = 0
    
    return board

# Choose what number this space is going to collapse to and update the possibilities of other spaces
def updateBoard(board, space):
    square, row, col = space
    X, Y = calculateGlobalXY(square, row, col)
    new_value = collapseValue(board, space)
    # update space
    board = updateSpace(board, space, [new_value])

    plist = [0,1,2,3,4,5,6,7,8]
    plist.remove(new_value)
    # For every other square in the board, update the possibilities based on newly chosen number
    for sq in range(9):
        for y in range(3):
            for x in range(3):
                # Skip this current space
                if (sq, y, x) == space:
                    continue
                # If the space already has a chosen value, skip it
                num_possibilities = np.count_nonzero(board[sq][y][x])
                if num_possibilities == 1:
                    continue

                global_x, global_y = calculateGlobalXY(sq, y, x)
                # True if space is in the same row or same collumn
                same_row_col = (global_x == X or global_y == Y)
                if sq == square or same_row_col:
                    # remove the chosen number from other spaces possible values
                    board = updateSpace(board, (sq, y, x), plist)
                    
                    # If the space has only 1 possible value left, do recursion magic
                    num_possibilities = np.count_nonzero(board[sq][y][x])
                    if num_possibilities == 1:
                        board = updateBoard(board, (sq, y, x))

    return board

# Check if a single space conflicts with any other spaces in a finished board
# Returns True for conflict, False for no conflict
def hasConflicts(board, space):
    square, row, col = space
    X, Y = calculateGlobalXY(square, row, col)
    space_val = getValue(board, space)

    # Loop through other spaces in this square and check for conflicts
    for y in range(3):
        for x in range(3):
            # Skip this space
            if (y, x) == (row, col):
                continue
            # Repeating val -> conflict
            if getValue(board, (square, y, x)) == space_val:
                return True
    
    # Loop through spaces in the same row and check for conflicts
    for curr_y in range(9):
        curr_space = curr_square, curr_row, curr_col = calculateSqRowCol(X, curr_y)
        # Skip this space
        if curr_space == space:
            continue
        # Repeating val -> conflict
        if getValue(board, (curr_square, curr_row, curr_col)) == space_val:
            return True
    
    # Do the same for the collumn
    for curr_x in range(9):
        curr_space = curr_square, curr_row, curr_col = calculateSqRowCol(curr_x, Y)
        # Skip this space
        if curr_space == space:
            continue
        # Repeating val -> conflict
        if getValue(board, (curr_square, curr_row, curr_col)) == space_val:
            return True

    # If no conflicts arise, return false
    return False

# Count and report the flaws in the final board
def detectFlaws(board):
    flaws_board = np.zeros((9,3,3))
    flaws = 0
    # Loop though each space on the board and check for conflicts
    for square in range(9):
        for row in range(3):
            for col in range(3):
                # If a conflict is found
                if hasConflicts(board, (square, row, col)):
                    # Set this space to 1 on the flaws board and increment flaws counter
                    flaws_board[square][row][col] = 1
                    flaws += 1
    
    if flaws == 0:
        print(f"Congradulations!! {flaws} flaws were found! :)")
    else:
        print(f"{flaws} flaws were found >:(")

    printBoardFlaws(board, flaws_board)


# Main loop
def main():
    # Create new board with all squares having all 9 possibilities
    # Equal entropy throughout
    board = initBoard()

    # While there are still unknown spaces on the board
    while countUnsolved(board) > 0:
        # Display current board to user
        printBoard(board)
        input("Hit ENTER: ")

        # Update the board based on the next lowest entropy space
        board = updateBoard(board, lowestEntropy(board))

    # Show user final board
    printBoard(board)

    # Show user final board's flaws
    input("Hit ENTER to scan for flaws: ")
    flaws_board = detectFlaws(board)


main()