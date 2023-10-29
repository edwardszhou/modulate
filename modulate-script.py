import socketio
import bpy
import random
from math import radians

# Selects path object (Plane) and its vertices
so = bpy.data.objects["Plane"]
verts = so.data.vertices

# Selects user object (Sphere) and its location
ball = bpy.data.objects["Sphere"]
ball_loc = ball.location

# Selects background items
buildings = bpy.data.collections["buildings"]
backdrop = bpy.data.collections["backdrop"]

# Selects coin objects and score text 
coins = bpy.data.collections["coincollection"]
generate_freq = 1 # coin generation frequency AKA level/difficulty, more coins generate as game progresses
score_text = bpy.data.objects["score"]

# Controls brightness of game world (day/night cycle)
world_strength = bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1]
world_strength.default_value = 0.5

day = True

ydist = 100
zdist = 100
generate = 200

# Sets default materials and properties of game
score = 0
score_text.data.body = "Score: " + str(score)
bpy.data.objects["Text"].data.body = "Pitch-based path generation"
bpy.data.lights["Spot"].color = (1, 0.563, 0.391)
bpy.data.materials["textglow"].node_tree.nodes["Emission"].inputs[0].default_value = (0.195, 0.943, 1, 1)
bpy.data.materials["ground"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.682, 0.901, 0.943, 1)


waveArr = None
ballHeight = None
bkgd = None
socket = socketio.Client() # socket object

# initializes coin positions and rotations randomly
for i in range(4):
    coins.all_objects[i].location[1] = random.randrange(100, 250, 1)
    coins.all_objects[i].rotation_euler[2] = radians(45*i)
bpy.data.objects["deathcoin"].location[1] = 300 # death coin is furthest back

# Function to end game
# disconnects from socket and stops game, changes visuals
def endGame():
    socket.disconnect()
    bpy.data.objects["Text"].data.body = "Game Over!"
    bpy.data.materials["textglow"].node_tree.nodes["Emission"].inputs[0].default_value = (1, 0, 0, 1) # text light changes to red
    bpy.data.materials["ground"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.942862, 0.681628, 0.793757, 1) # ground material changes color
    world_strength.default_value = 0 # night time
    bpy.data.lights["Spot"].color = (1, 0, 0) # ball lighting changes to red
    
# input from server from ml5
# param data - (dictionary) {data: [pitch graph array], ballHeight: [ball height], bkgd: vol}
@socket.event
def message(data): 
    
    global day
    waveArr = data['data']
    ballHeight = data['ballHeight']
    bkgd = data['bkgd']
    
    # control day/night cycle, decrease/increase world brightness accordingly
    if day:
        world_strength.default_value += 0.001
        if world_strength.default_value >= 1:
            day = False
    else:
        world_strength.default_value -= 0.001
        if world_strength.default_value <= -0.5:
            day = True
    
    # translates 1D array waveArr to 3D object vertices
    # 4 vertices map to each waveArr point
    for i in range(50):
        # verts.co[2] refers to z (up/down) value of vertex
        verts[i].co[2] = float(waveArr[i])
        verts[50+i].co[2] = float(waveArr[i])
        verts[100+i].co[2] = float(waveArr[i])-5 # -5 for path thickness
        verts[150+i].co[2] = float(waveArr[i])-5

    # set ball location
    ball.location[2] = 20-float(ballHeight)/22
    
    # move buildings, reset position if past viewer
    for bd in buildings.all_objects:
        if bd.location[1] < -15:
            bd.location[1] += 130
        else:
            bd.location[1] -= 1
            
    for back in backdrop.all_objects:
        if back.location[1] < -60:
            back.location[1] += 535
        else:
            back.location[1] -= 1
    
    # move coins
    for coin in coins.all_objects:
        global ydist
        global zdist
        global generate_freq
        ydist = abs(coin.location[1]-ball_loc[1]) # gets how far away the coin is horizontally
        zdist = abs(coin.location[2]-(ball.location[2]+5.78)) # gets how far away th coin is vertically

        if ydist < 2 and zdist < 3: # if coin is close enough (colliding with) ball, reset coin
            coin.location[1] = -20 
            global score
            if coin == bpy.data.objects["deathcoin"]: # end game if coin is death coin
                endGame() 
            score += 1 # modify score, 
            score_text.data.body = "Score: " + str(score) 
            if score % 5 == 0:
                generate_freq += 1 # increase level/coin generation frequency every 5 coins
            
        elif coin.location[1] < -15: # if coin goes past user, reset coin
            global generate  

            # generates random number, checks if below threshold to determine spawn
            # [generate_freq] in 200 to spawn if regular coin, [generate_freq] in 500 to spawn if death coin
            generate = random.randrange(0, 200, 1)
            if coin == bpy.data.objects["deathcoin"]:
                 generate = random.randrange(0, 500, 1)

            # if spawned, generate random location
            if generate <= generate_freq: 
                coin.location[2] = random.randrange(3, 18, 1)
                coin.location[1] = 130

        # update coin location/rotation
        coin.location[1] -= 0.5
        coin.rotation_euler[2] += 0.1

            

@socket.event
def connect():
    print('connected')


@socket.event
def connect_error():
    print("The connection failed!")

# connect with socket, set up callback
socket.connect('http://localhost:5050')
socket.on('data', message)
