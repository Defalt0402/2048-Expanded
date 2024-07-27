from tkinter import *
from tkinter.messagebox import showinfo, askyesno
from csv import *
from PIL import ImageTk, Image
import random
import numpy as np

"""Notes to marker:
    Screen resolution is 1280x720
    There is no pause feature, given that the game is not time dependent
"""


"""Notes to self:
    canvas.move moves based on current position
    rectangle requires x1, y1, x2, y2, fill= color to create a rectangle. always starts at 0, 0
    canvas.coords allows setting and getting of position coords

    Main game grid area will be 720x720, with other elements (score, load, save) on the right side of the screen
    therefore create 720x720 canvas, put buttons on the right
    grid border colour = 815e5e
    grid block colour = a68080

    store blocks in grid as [object, value]
    each block is given a tag in the form (xy) where x and y are cordinates. Images deleted using this tag

    store each block in blocks array in format "yxc" where y, x, c are each numbers. y and x are between 0 and 3, c is any power of 2 up to 65536. y,x make coords. c is value.
    blocks array allows storing and loading game state

    score increases when blocks combine. eg: if combine to make 4, score += 4. If combine to make 128, score += 128

    for text objects, width and height are measured in character size

    for save files, names follow {playerName}Save, contents in form of [blocks,
                                                                        score, highestValue]

    for font 14, width each 10.3px, 144 width if 14
"""


# Handle key presses

"""
    Each direction moves each block in the grid, starting on the same side as the direction to be moved
    After all blocks are moved, a new block is placed on the grid
    All blocks currently on the grid are then added to the blocks array so that the game will be able to be saved correctly
"""
def move_block(block, y, x, dy, dx):
    global score, highestValue
    dist = 3 if dy != 0 else 3 if dx != 0 else 0
    while dist > 0:
        new_y, new_x = y + dy, x + dx
        if 0 <= new_y < 4 and 0 <= new_x < 4:
            valmatch, overlap = overlapping(block[1], new_y, new_x)
            if overlap and valmatch:
                val = block[1]
                newVal = val * 2
                if newVal > highestValue:
                    highestValue = newVal
                canvas.move(block[0], dx * 44, dy * 44)
                grid[y][x] = None
                newBlock = canvas.create_image(GRID_POSITIONS[new_y][new_x][0], GRID_POSITIONS[new_y][new_x][1], image=get_image(newVal), anchor=NW)
                grid[new_y][new_x] = [newBlock, newVal]

                score += newVal
                y, x = new_y, new_x
            elif not overlap:
                canvas.move(block[0], dx * 44, dy * 44)
                grid[y][x] = None
                grid[new_y][new_x] = block
                y, x = new_y, new_x
            else:
                break
        else:
            break
        dist -= 1

def handle_move(dy, dx):
    for y in range(4):
        for x in range(4):
            if dy == 1 or dx == 1:
                y, x = 3-y, 3-x  # Move from bottom or right
            if grid[y][x] is not None:
                move_block(grid[y][x], y, x, dy, dx)

    place_new_block()
    update_blocks()
    refresh_canvas()
    update_score()

def left_key(event):
    handle_move(0, -1)

def right_key(event):
    handle_move(0, 1)

def up_key(event):
    handle_move(-1, 0)

def down_key(event):
    handle_move(1, 0)

def update_blocks():
    blocks.clear()
    for y in range(4):
        for x in range(4):
            if grid[y][x] is not None:
                blocks.append(f"{y}{x}{grid[y][x][1]}")


# Changes game into a work friendly image
def boss_key(event):
    """
    Check if the boss key is active
    If the boss key is not active, forget packing of frames in window, resize the window, replace with an image
    If the boss key is active, set boss to False remove the image from the screen and repack both frames to display game again
    """
    global BOSS, game_frame, side_frame, bossCanvas, window
    if not BOSS:
        BOSS = True
    else:
        BOSS = False

    if BOSS:
        game_frame.pack_forget()
        side_frame.pack_forget()
        window.title("User Details - LibreOffice Calc")
        window.geometry("1920x860")
        bossCanvas = Canvas(window, bg="black", width=1920, height=900)
        bossCanvas.create_image(0, 0, image=IMAGE_BOSS, anchor=NW)
        bossCanvas.pack()
    else:
        screenWidth = window.winfo_screenwidth()
        screenHeight = window.winfo_screenheight()
        windowStartX = int((screenWidth/2)-(WIDTH/2))
        windowStartY = int((screenHeight/2)-(HEIGHT/2))

        window.title("2048: Expanded")
        window.geometry(f"{WIDTH}x{HEIGHT}+{windowStartX}+{windowStartY}")
        bossCanvas.pack_forget()
        window.geometry()
        game_frame.pack(side="left")
        side_frame.pack(side="left")



# A cheat which doubles the value of all blocks on the grid (increases highest value, but not score)
def cheat(event):
    """
    Creates a copy of the blocks list, finds the location and value of each block from this
    updates the original blocks list with blocks of double the value in the same position
    If a block has the value of 65536, it cannot be doubled so it is not doubled
    """
    global highestValue, grid, blocks
    grid = [[None, None, None, None],  # Reset grid
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None]]  # reset grid

    if highestValue != 65536:
        highestValue = highestValue*2  # Double highest value, if it can be doubled

    temp_blocks = blocks
    blocks = []
    for item in temp_blocks:
        y = int(item[0])
        x = int(item[1])
        val = int(item[2:])

        if val != 65536:
            val = val*2

        block = canvas.create_image(GRID_POSITIONS[y][x][0], GRID_POSITIONS[y][x][1], image=get_image(val), anchor=NW)
        grid[y][x] = [block, val]
        block = f"{y}{x}{val}"
        blocks.append(block)

    refresh_canvas()
    update_score()


# Handling each direction of movement

"""
define how many spaces to be moved
if can be moved and combined, move and combine
if can be moved, move
if cannot be moved, dont move

if moved, try to move again

When values combine: 
    get the value from the block and double it,
    If the new value is bigger than the highest value so far, increase the highest value
    Remove the block that would enter the other block 
    Set the grid of the spot where the values combine to be the new block with new value
"""

# Functions for checking colisions below

# If the grid has an object in the specified location, an overlap will occur
def overlapping(val, y, x):
    """
    value of the current block, and the x and y position of the block with which colision is being detected is passed
    If there is a block in this x, y position, there is a colision, therefore the values are checked, and overlap is True
    return the result of matching_values, and overlap
    """
    if grid[y][x] is not None:
        return matching_values(val, y, x), True
    return False, False


# If the value of the element being checked is the same as that it would collid with
def matching_values(val, y, x):
    """
    If the value of the block is 65536, it cannot combine and so return false
    else if the value of the current and the colliding block are the same, return True
    else return true
    """
    return val != 65536 and val == grid[y][x][1]

#Functions for checking end of game

# Check grid for loss condition
def check_loss():
    """
    When the grid is full:
        check if any blocks can combine horizontally
        check if any blocks can combine vertically
        If a combination exists, loss is false
        else, game over
    """
    for y in range(4):
        for x in range(4):
            if grid[y][x] is None:
                return
            if x < 3 and grid[y][x][1] == grid[y][x+1][1] and grid[y][x][1] != 65536:
                return
            if y < 3 and grid[y][x][1] == grid[y+1][x][1] and grid[y][x][1] != 65536:
                return
    game_over()


# If there are no more possible moves, prompt the player to save their score to the leaderboard, or to start a new game
def game_over():
    global gameOverWindow
    gameOverWindow = Toplevel()
    gameOverWindow.title("Game Over")
    message = f"There are no more possible moves! Your score is {score}, and your largest number was {highestValue}. What would you like to do now?"
    Label(gameOverWindow, text=message).pack()
    Button(gameOverWindow, text='Save To Leaderboard', command=save_to_leaderboard).pack()
    Button(gameOverWindow, text='New Game', command=new_game).pack()
    Button(gameOverWindow, text='Quit', command=game_quit).pack()


# Functions for saving to leaderboard below

# Creates the leaderboard file if it doesn't already exist
def create_leaderboard_file():
    while True:
        try:
            f = open("leaderboard.csv", "x")
            f.close()
            break
        except IOError:
            break

# Write to leaderboard
def save_to_leaderboard():
    global gameOverWindow
    if playerName == "":
        get_name()
    elif playerName != "":
        if "gameOverWindow" in globals():
            gameOverWindow.destroy()
            gameOverWindow.update()
        toWrite = [playerName, score, highestValue]
        leaderboardWriter = writer(open("leaderboard.csv", "a"))  # Writes to leaderboard.csv in append mode so that data is added on newline
        leaderboardWriter.writerow(toWrite)


# Allows user to input their name. If name is not suitable, recalls this function
def get_name():
    global nameInputWindow
    if "gameOverWindow" in globals():
        gameOverWindow.destroy()
        gameOverWindow.update()
    if "nameInputWindow" in locals() or "nameInputWindow" in globals():
        nameInputWindow.destroy()
        nameInputWindow.update()

    if not loggedIn:
        nameInputWindow = Toplevel()
        nameInputWindow.title("Enter Name")
        nameInputWindow.geometry(f"250x100+{int(WIDTH/2)}+{int(HEIGHT/2)}")
        message = "Please enter your name"
        nameInput = Text(nameInputWindow, width=10, height=2)
        nameInput.pack()
        messageLabel = Label(nameInputWindow, text=message).pack()
        Button(nameInputWindow, text='Submit', command = lambda: check_name(nameInput.get("1.0", "end-1c"))).pack()
    else:
        check_name(playerName)


# Checks if input name is suitable. if suitable, call save_to_leaderboard
def check_name(name):
    """
    Name is suitable if it is not empty and if it is greater than 2 characters long
    """
    global playerName, nameInputWindow
    if name in ("", " ", "  ", "   "):
        messageBox = showinfo(title="Problem", message="Please enter a name")
        if messageBox == "ok":
            get_name()
    if len(name) < 3:
        messageBox = showinfo(title="Problem", message="Please enter a name of at least 3 characters")
        if messageBox == "ok":
            get_name()

    if len(name) >= 3:
        playerName = name
        nameInputWindow.destroy()
        nameInputWindow.update()
        save_to_leaderboard()


# Functions for new game/quit below

# Resets all states back to default    
def new_game():
    global blocks, grid, score, highestValue
    if 'gameOverWindow' in globals():
        gameOverWindow.destroy()

    if askyesno(title="Are you sure?", message="Are you sure you want to start a new game? All progress will be lost.", icon='warning'):
        grid = [[None for _ in range(4)] for _ in range(4)]
        blocks = []
        score = 0
        highestValue = 2
        generate_start()
        update_leaderboard()
        refresh_canvas()
        update_score()


# Close all game windows
def game_quit():
    if 'gameOverWindow' in globals():
        gameOverWindow.destroy()
    window.quit()
  

# Functions for adding new blocks below

# Chooses a random empty position on the grid to place a new block. new block has 70% chanve to be 2, 20% for 4 and 10% for 8
def place_new_block():
    empty_positions = [(y, x) for y in range(4) for x in range(4) if grid[y][x] is None]
    if not empty_positions:
        check_loss()
        return

    y, x = random.choice(empty_positions)
    val = random.choices([2, 4, 8], [70, 20, 10])[0]
    block = canvas.create_image(GRID_POSITIONS[y][x][0], GRID_POSITIONS[y][x][1], image=get_image(val), anchor=NW)
    grid[y][x] = [block, val]


# Place a block on the board
def generate_start():
    y, x = random.randint(0, 3), random.randint(0, 3)
    blockImage = canvas.create_image(GRID_POSITIONS[y][x][0], GRID_POSITIONS[y][x][1], image=IMAGE_2, anchor=NW)
    grid[y][x] = [blockImage, 2]
    blocks.append(f"{y}{x}2")


# Functions for setting up the window below this point

# Create a window
def set_window_dimensions():
    window = Tk()
    window.title("2048 Expanded")
    screenWidth = window.winfo_screenwidth()
    screenHeight = window.winfo_screenheight()
    windowStartX = int((screenWidth/2)-(WIDTH/2))
    windowStartY = int((screenHeight/2)-(HEIGHT/2))

    window.geometry(f"{WIDTH}x{HEIGHT}+{windowStartX}+{windowStartY}")
    return window


# Creates all elements for the side frame
def create_side_frame_elements():
    global scoreText, highestValueText, scoreLabel, highestValueLabel
    scoreText = f"Score: {score}"
    highestValueText = f"Largest Number: {highestValue}"
    scoreLabel = Label(side_frame, text=scoreText, anchor=CENTER, width=24, height=3, font=("Arial", 14))
    scoreLabel.place(relx= 0.5, y=40, anchor=CENTER)
    highestValueLabel = Label(side_frame, text=highestValueText, anchor=CENTER, width=24, height=3, font=("Arial", 14))
    highestValueLabel.place(relx=0.5, y=110, anchor=CENTER)
    saveButton = Button(side_frame, text="Save", command= lambda: save_game(), width=8, height = 2, bg="tan1")
    saveButton.place(x=37, y=160)
    loadButton = Button(side_frame, text="Load", command= lambda: load_game(), width=8, height=2, bg="tan1")
    loadButton.place(x=223, y=160)
    newGameButton = Button(side_frame, text="New Game", command= lambda: new_game(), width=8, height=2, bg="tan1")
    newGameButton.place(x=410, y=160)
    controlsButton = quitButton = Button(side_frame, text="Controls", width =6, height=2, command= lambda: show_info())
    controlsButton.place(x=74, rely=0.95, anchor=CENTER)
    quitButton = Button(side_frame, text="Quit", width =6, height=2, command= lambda: window.quit(), bg="tan1")
    quitButton.place(relx=0.5, rely=0.95, anchor=CENTER)
    creditsButton = quitButton = Button(side_frame, text="Credits", width =6, height=2, command= lambda: show_credits())
    creditsButton.place(x=470, rely=0.95, anchor=CENTER)

    update_leaderboard()


# Creates two frames on which elements will be placed
def create_frames():
    f1 = Frame(window, width=CANVAS_SIZE, height=CANVAS_SIZE)
    f2 = Frame(window, width=SIDE_WIDTH, height=HEIGHT, bg="grey")
    return f1, f2


# Functions for keeping screen up to date below this point

# Updates the leaderboard so that it is up to date with new scores
def update_leaderboard():
    if "name0" in locals() or "name0" in globals():
        name0.destroy()
        name1.destroy()
        name2.destroy()
        name3.destroy()
        name4.destroy()
        score0.destroy()
        score1.destroy()
        score2.destroy()
        score3.destroy() 
        score4.destroy()
        value0.destroy()
        value1.destroy()
        value2.destroy()
        value3.destroy()
        value4.destroy()


    """
    The following code:
        opens the leaderboard csv in reader mode and creates a reader object
        The reader is then converted into a list so that the data can be accessed as if declared as a list
        The list is then sorted using the inbuilt sorted function, using the scores as a key (sort by score)
        If there aren't enough values in the file to fill all available leaderboard spots, populate the rest of the spots with NA
    """

    leaderReader = reader(open("leaderboard.csv", "r"), delimiter = ",") #Create a reader, read , as delimiter
    temp = list(leaderReader)
    sort = sorted(temp, key=SortScore, reverse = True) #Sorted list is the original list, sorted by the 2nd column (index 1, starts at 0), sorted in descending order

    names = []
    scores = []
    highestValues = []
    for row in sort:
        names.append(row[0])
        scores.append(row[1])
        highestValues.append(row[2])

    #If there aren't 5 scores in existence, append "NA" to fill the remaining spaces
    if len(names) < 5:
        diff = 5 - len(names)
        for i in range(diff, 6):
            names.append("NA")
            scores.append("NA")
            highestValues.append("NA")
    

    # Creating a set of labels to show leaderboard
    # Will show top 5 scores
    leaderBackground = Label(side_frame, text="Leaderboard", anchor=N, width=28, height=10, font=("Arial", 24), background="dark slate gray", pady=10)
    leaderBackground.place(x=20, y=250, anchor=NW)
    nameLeaderLabel = Label(side_frame, text="Name", anchor=CENTER, width=14, height=2, font=("Arial", 14), bg="gray", fg="#f21")
    nameLeaderLabel.place(x=35, y=300, anchor=NW)
    scoreLeaderLabel = Label(side_frame, text="Score", anchor=CENTER, width=14, height=2, font=("Arial", 14), bg="gray", fg="#f21")
    scoreLeaderLabel.place(x=201, y=300, anchor=NW)
    highValueLeaderLabel = Label(side_frame, text="Highest Value", anchor=CENTER, width=14, height=2, font=("Arial", 14), bg="gray", fg="#f21")
    highValueLeaderLabel.place(x=367, y=300, anchor=NW)

    # row 1
    name0 = Label(side_frame, text=names[0], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    name0.place(x=35, y=355, anchor=NW)
    score0 = Label(side_frame, text=scores[0], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    score0.place(x=201, y=355, anchor=NW)
    value0 = Label(side_frame, text=highestValues[0], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    value0.place(x=367, y=355, anchor=NW)
    # row 2
    name1 = Label(side_frame, text=names[1], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    name1.place(x=35, y=410, anchor=NW)
    score1 = Label(side_frame, text=scores[1], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    score1.place(x=201, y=410, anchor=NW)
    value1 = Label(side_frame, text=highestValues[1], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    value1.place(x=367, y=410, anchor=NW)
    # row 3
    name2 = Label(side_frame, text=names[2], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    name2.place(x=35, y=465, anchor=NW)
    score2 = Label(side_frame, text=scores[2], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    score2.place(x=201, y=465, anchor=NW)
    value2 = Label(side_frame, text=highestValues[2], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    value2.place(x=367, y=465, anchor=NW)
    # row 4
    name3 = Label(side_frame, text=names[3], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    name3.place(x=35, y=520, anchor=NW)
    score3 = Label(side_frame, text=scores[3], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    score3.place(x=201, y=520, anchor=NW)
    value3 = Label(side_frame, text=highestValues[3], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    value3.place(x=367, y=520, anchor=NW)
    # row 5
    name4 = Label(side_frame, text=names[4], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    name4.place(x=35, y=575, anchor=NW)
    score4 = Label(side_frame, text=scores[4], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    score4.place(x=201, y=575, anchor=NW)
    value4 = Label(side_frame, text=highestValues[4], anchor=CENTER, width=14, height=2, font=("Arial", 14))
    value4.place(x=367, y=575, anchor=NW)


# Returns integer value in the scores column of leaderboard csv
def SortScore(temp):
    return int(temp[1])


# Update global score variables and labels
def update_score():
    global scoreText, highestValueText, scoreLabel, highestValueLabel
    scoreText = f"Score: {score}"
    highestValueText = f"Largest Number: {highestValue}"
    scoreLabel.place_forget()
    highestValueLabel.place_forget()
    scoreLabel = Label(side_frame, text=scoreText, anchor=CENTER, width=24, height=3, font=("Arial", 14))
    scoreLabel.place(relx= 0.5, y=40, anchor=CENTER)
    highestValueLabel = Label(side_frame, text=highestValueText, anchor=CENTER, width=24, height=3, font=("Arial", 14))
    highestValueLabel.place(relx=0.5, y=110, anchor=CENTER)


# Deletes all canvas elements and redraws them in the correct place
def refresh_canvas():
    canvas.delete('all')
    canvas.create_image(0, 0, image=GRID_BACKGROUND, anchor=NW)
    for item in blocks:
        y = int(item[0])
        x = int(item[1])
        val = int(item[2:])
        block = canvas.create_image(GRID_POSITIONS[y][x][0], GRID_POSITIONS[y][x][1], image=get_image(val), anchor=NW)
        grid[y][x] = [block, val]


# Functions for information below this point

# Show game info/controls
def show_info():
    controlsMessage = "Welcome to 2048: Expanded!\nYour goal is to move the blocks in the grid in order to create the largest value possible. When blocks of the same value collide, they merge into a larger block! Score will increase every time you combine blocks together.\n\nTo control the game, use either:\n\nW - Up, A - left, S - down, D - right\n\nUp key - up,  Left key - left, Down key - down, Right key - right\n\nWant to make your highest value bigger without the effort? Try pressing F6...\n\nOh No! Your boss is coming! Quick, press F5! They'll never know they're paying you to play games!"
    messageBox = showinfo(title="Controls", message=controlsMessage)

# Show game credits
def show_credits():
    creditsMessage = "This game was originally made by Gabriele Cirulli in 2014.\nThis version of the game was made by Lewis Murphy in 2022.\nAll assets used in this version of the game were created by Lewis.\n\nEnjoy the game!"
    messageBox = showinfo(title="Controls", message=creditsMessage)


# Game saving functions below this point

# Save game data to a save file that is unique to each player
def save_game():
    if not loggedIn:
        login("save")
    else:
        messagebox = askyesno(title="Are you sure?", message="Are you sure you want to save your game? Any previous save data will be lost.", icon='warning')
        if messagebox:
            filename = f"saves/{playerName}Save.csv"
            toWrite = [blocks, [score, highestValue]]
            saveWriter = writer(open(filename, "w"))
            saveWriter.writerows(toWrite)
        else:
            pass


# Load a saved game
def load_game():
    global playerName, blocks, score, highestValue, grid
    if not loggedIn:
        login("load")
    else:
        messagebox = askyesno(title="Are you sure?", message="Are you sure you want to load your last saved game? Any progress made here will be lost.", icon='warning')
        if messagebox:
            blocks = []
            grid = [[None, None, None, None],
            [None, None, None, None],
            [None, None, None, None],
            [None, None, None, None]] 
            filename = f"saves/{playerName}Save.csv"
            fReader = reader(open(filename, "r"))
            rows = list(fReader) #Get the file in a form in list form
            for column in rows[0]: #Get all blocks
                blocks.append(column)
            score = int(rows[1][0])
            highestValue = int(rows[1][1])
            refresh_canvas()
            update_score()
        else:
            pass


# Login Functions below this point

# Creates window that allows user to log in to a created account
def login(returnFunction):
    global loggedIn, loginInputWindow
    loginInputWindow = Toplevel()
    loginInputWindow.title("Login")
    loginInputWindow.geometry(f"250x300+{int(WIDTH/2)}+{int(HEIGHT/2)}")
    
    messageUsername = "Please enter a username"
    messageLabelUser = Label(loginInputWindow, text=messageUsername).pack()
    usernameInput = Text(loginInputWindow, width=10, height=2)
    usernameInput.pack()

    messagePassword1 = "Please enter a password"
    messageLabelPassword1 = Label(loginInputWindow, text=messagePassword1).pack()
    password1Input = Text(loginInputWindow, width=10, height=2)
    password1Input.pack()

    Button(loginInputWindow, text='Submit', command = lambda: check_login(usernameInput.get("1.0", "end-1c"), password1Input.get("1.0", "end-1c"), returnFunction)).pack()
    Button(loginInputWindow, text='Create New Login', command = lambda: create_login(returnFunction)).pack()


# Checks if the username and password exist
def check_login(user, pass1, returnFunction):
    global playerName, loggedIn, loginInputWindow
    loginInputWindow.destroy()
    userDetails = reader(open("logins.csv", "r"), delimiter = ",")  # Create a reader, read , as delimiter

    for row in userDetails:
        if row[0] == user and row[1] == pass1:
            playerName = user
            loggedIn = True
            if returnFunction == "save":
                save_game()
            elif returnFunction == "load":
                load_game()
    

# Creates a window that prompts user to input a username and password in order to create a login
def create_login(returnFunction):
    global loginInputWindow, loginCreateInputWindow
    loginInputWindow.destroy()

    loginCreateInputWindow = Toplevel()
    loginCreateInputWindow.title("Create Login")
    loginCreateInputWindow.geometry(f"250x300+{int(WIDTH/2)}+{int(HEIGHT/2)}")

    messageUsername = "Please enter a username"
    messageLabelUser = Label(loginCreateInputWindow, text=messageUsername).pack()
    usernameInput = Text(loginCreateInputWindow, width=10, height=2)
    usernameInput.pack()

    messagePassword1 = "Please enter a password"
    messageLabelPassword1 = Label(loginCreateInputWindow, text=messagePassword1).pack()
    password1Input = Text(loginCreateInputWindow, width=10, height=2)
    password1Input.pack()

    messagePassword2 = "Please enter the password again"
    messageLabelPassword2 = Label(loginCreateInputWindow, text=messagePassword2).pack()
    password2Input = Text(loginCreateInputWindow, width=10, height=2)
    password2Input.pack()
    
    Button(loginCreateInputWindow, text='Submit', command = lambda: check_create_login(usernameInput.get("1.0", "end-1c"), password1Input.get("1.0", "end-1c"), password2Input.get("1.0", "end-1c"), returnFunction)).pack()


# Checks if data enetered to create login matches criteria
def check_create_login(user, pass1, pass2, returnFunction):
    global loginCreateInputWindow
    userGood = False
    passGood = False

    loginCreateInputWindow.destroy()

    # Check if input username follows criteria
    if user in ("", " ", "  ", "   "):
        messageBox = showinfo(title="Problem", message="Please enter a username")
        if messageBox == "ok":
            create_login(returnFunction)
    elif len(user) < 3:
        messageBox = showinfo(title="Problem", message="Please enter a username of at least 3 characters")
        if messageBox == "ok":
            create_login(returnFunction)
    else:
        userGood = True

    userDetails = reader(open("logins.csv", "r"))  # Open file as f, delimiter = ",") #Create a reader, read , as delimiter
    for row in userDetails:
        if row[0] == user:
            userGood = False
            messageBox = showinfo(title="Problem", message="This username already exists. Please use a different username.")
            if messageBox == "ok":
                create_login(returnFunction)


    # Check if password follows criteria
    if pass1 in ("", " ", "  ", "   "):
        messageBox = showinfo(title="Problem", message="Please enter a password")
        if messageBox == "ok":
            create_login(returnFunction)
    elif len(pass1) < 3:
        messageBox = showinfo(title="Problem", message="Please enter a password of at least 3 characters")
        if messageBox == "ok":
            create_login(returnFunction)
    elif pass1 != pass2:
        messageBox = showinfo(title="Problem", message="Please ensure both password inputs match")
        if messageBox == "ok":
            create_login(returnFunction)
    else:
        passGood = True

    # If both username and password fit criteria
    if passGood and userGood:
        save_login(user, pass1)
        messageBox = showinfo(title="Success!", message="Your login has been created! Press ok to go to login.")
        if messageBox == "ok":
            login(returnFunction)
    else:
        messageBox = showinfo(title="Problem", message="A problem occurred, please try again")
        if messageBox == "ok":
            create_login(returnFunction)


# Saves login information to a file, then creates a save file for the player
def save_login(user, pass1):
    toWrite = [user, pass1]
    loginsWriter = writer(open("logins.csv", "a"))
    loginsWriter.writerow(toWrite)

    filename = f"saves/{user}Save.csv"
    toWrite = [blocks, [score, highestValue]]
    saveWriter = writer(open(filename, "w"))
    saveWriter.writerows(toWrite)




# Creating important global variables
# Grid will take up 720x720px, each block will be 160px, leaving 80px total margin per column/row, 16px margin around each block
grid = [[None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None]]  # 4x4 grid
blocks = []
playerName = ""
loggedIn = False
BOSS = False

# Making Score text
highestValue = 2
score = 0  # Score increases every time blocks combine

# Set pixel size of each block
BLOCK_SIZE = 160
# Saving all x, y positions blocks can reside in
GRID_POSITIONS = [[[16,16],[192,16],[368,16],[544,16]],
                  [[16,192],[192,192],[368,192],[544,192]],
                  [[16,368],[192,368],[368,368],[544,368]],
                  [[16,544],[192,544],[368,544],[544,544]]]



# Setting window dimension
WIDTH, HEIGHT = 1280, 720
CANVAS_SIZE = 720
SIDE_WIDTH = 560
RESOLUTION = str(WIDTH)+"x"+str(HEIGHT)
window = set_window_dimensions()
game_frame, side_frame = create_frames()
canvas = Canvas(game_frame, bg="black", width=CANVAS_SIZE, height=CANVAS_SIZE)


# Bind all controls
canvas.bind('<Left>', left_key)
canvas.bind('<Right>', right_key)
canvas.bind('<Up>', up_key)
canvas.bind('<Down>', down_key)
canvas.bind('<a>', left_key)
canvas.bind('<d>', right_key)
canvas.bind('<w>', up_key)
canvas.bind('<s>', down_key)
canvas.bind('<F5>', boss_key)
canvas.bind('<F6>', cheat)
canvas.focus_set()

# Loading all images to be used
load = Image.open("images/background.jpg")
GRID_BACKGROUND = ImageTk.PhotoImage(load)
load = Image.open("images/2.jpg")
IMAGE_2 = ImageTk.PhotoImage(load)
load = Image.open("images/4.jpg")
IMAGE_4 = ImageTk.PhotoImage(load)
load = Image.open("images/8.jpg")
IMAGE_8 = ImageTk.PhotoImage(load)
load = Image.open("images/16.jpg")
IMAGE_16 = ImageTk.PhotoImage(load)
load = Image.open("images/32.jpg")
IMAGE_32 = ImageTk.PhotoImage(load)
load = Image.open("images/64.jpg")
IMAGE_64 = ImageTk.PhotoImage(load)
load = Image.open("images/128.jpg")
IMAGE_128 = ImageTk.PhotoImage(load)
load = Image.open("images/256.jpg")
IMAGE_256 = ImageTk.PhotoImage(load)
load = Image.open("images/512.jpg")
IMAGE_512 = ImageTk.PhotoImage(load)
load = Image.open("images/1024.jpg")
IMAGE_1024 = ImageTk.PhotoImage(load)
load = Image.open("images/2048.jpg")
IMAGE_2048 = ImageTk.PhotoImage(load)
load = Image.open("images/4096.jpg")
IMAGE_4096 = ImageTk.PhotoImage(load)
load = Image.open("images/8192.jpg")
IMAGE_8192 = ImageTk.PhotoImage(load)
load = Image.open("images/16384.jpg")
IMAGE_16384 = ImageTk.PhotoImage(load)
load = Image.open("images/32768.jpg")
IMAGE_32768 = ImageTk.PhotoImage(load)
load = Image.open("images/65536.jpg")
IMAGE_65536 = ImageTk.PhotoImage(load)
load = Image.open("images/bosskey.png")
IMAGE_BOSS = ImageTk.PhotoImage(load)


# Returns image based on value passed
def get_image(val):
    if val == 2:
        return IMAGE_2
    elif val == 4:
        return IMAGE_4
    elif val == 8:
        return IMAGE_8
    elif val == 16:
        return IMAGE_16
    elif val == 32:
        return IMAGE_32
    elif val == 64:
        return IMAGE_64
    elif val == 128:
        return IMAGE_128
    elif val == 256:
        return IMAGE_256
    elif val == 512:
        return IMAGE_512
    elif val == 1024:
        return IMAGE_1024
    elif val == 2048:
        return IMAGE_2048
    elif val == 4096:
        return IMAGE_4096
    elif val == 8192:
        return IMAGE_8192
    elif val == 16384:
        return IMAGE_16384
    elif val == 32768:
        return IMAGE_32768
    elif val == 65536:
        return IMAGE_65536


# Call functions
create_leaderboard_file()
create_side_frame_elements()
game_frame.pack(side="left")
side_frame.pack(side="left")
canvas.create_image(0, 0, image=GRID_BACKGROUND, anchor=NW)
generate_start()
canvas.pack()
window.mainloop()
