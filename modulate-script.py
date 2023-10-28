import socketio
import bpy
import random
from math import radians

so = bpy.data.objects["Plane"]
verts = so.data.vertices

ball = bpy.data.objects["Sphere"]
ball_loc = ball.location

buildings = bpy.data.collections["buildings"]
backdrop = bpy.data.collections["backdrop"]

coins = bpy.data.collections["coincollection"]
generate_freq = 1
score_text = bpy.data.objects["score"]


world_strength = bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1]
world_strength.default_value = 0.5Í

day = True

ydist = 100
zdist = 100
generate = 200

score = 0
score_text.data.body = "Score: " + str(score)
bpy.data.objects["Text"].data.body = "Pitch-based path generation"
bpy.data.lights["Spot"].color = (1, 0.563, 0.391)
bpy.data.materials["textglow"].node_tree.nodes["Emission"].inputs[0].default_value = (0.195, 0.943, 1, 1)
bpy.data.materials["ground"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.682, 0.901, 0.943, 1)


waveArr = None
ballHeight = None
bkgd = None
socket = socketio.Client()

for i in range(4):
    coins.all_objects[i].location[1] = random.randrange(100, 250, 1)
    coins.all_objects[i].rotation_euler[2] = radians(45*i)
bpy.data.objects["deathcoin"].location[1] = 300

def endGame():
    socket.disconnect()
    bpy.data.objects["Text"].data.body = "Game Over!"
    bpy.data.materials["textglow"].node_tree.nodes["Emission"].inputs[0].default_value = (1, 0, 0, 1)
    bpy.data.materials["ground"].node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.942862, 0.681628, 0.793757, 1)
    world_strength.default_value = 0
    bpy.data.lights["Spot"].color = (1, 0, 0)
    
@socket.event
def message(data):
    
    global day
    waveArr = data['data']
    ballHeight = data['ballHeight']
    bkgd = data['bkgd']
    
    if day:
        world_strength.default_value += 0.001
        if world_strength.default_value >= 1:
            day = False
    else:
        world_strength.default_value -= 0.001
        if world_strength.default_value <= -0.5:
            day = True
    
    for i in range(50):
        verts[i].co[2] = float(waveArr[i])
        verts[50+i].co[2] = float(waveArr[i])
        verts[100+i].co[2] = float(waveArr[i])-5
        verts[150+i].co[2] = float(waveArr[i])-5

    ball.location[2] = 20-float(ballHeight)/22
    
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
    
    
    for coin in coins.all_objects:
        global ydist
        global zdist
        global generate_freq
        ydist = abs(coin.location[1]-ball_loc[1])
        zdist = abs(coin.location[2]-(ball.location[2]+5.78))
        if ydist < 2 and zdist < 3:
            coin.location[1] = -20
            global score
            if coin == bpy.data.objects["deathcoin"]:
                endGame() 
            score += 1
            score_text.data.body = "Score: " + str(score)
            if score % 5 == 0:
                generate_freq += 1
            
        elif coin.location[1] < -15:    
            global generate  
            generate = random.randrange(0, 200, 1)
            if coin == bpy.data.objects["deathcoin"]:
                 generate = random.randrange(0, 500, 1)
            if generate <= generate_freq:
                coin.location[2] = random.randrange(3, 18, 1)
                coin.location[1] = 130
        coin.location[1] -= 0.5
        coin.rotation_euler[2] += 0.1

            

@socket.event
def connect():
    print('connected')


@socket.event
def connect_error():
    print("The connection failed!")

socket.connect('http://localhost:5050')
socket.on('data', message)
