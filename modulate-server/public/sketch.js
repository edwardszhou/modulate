// Copyright (c) 2019 ml5
//
// This software is released under the MIT License.
// https://opensource.org/licenses/MIT

/* ===
Basic Pitch Detection
=== */

var socket;

let audioContext;
let mic;
let pitch;
let vol = 0;

let freqList = [];
let lastFreq = 0;
let freqListCounter = 0;
let waveformPoints = [];
let smoothWaveform = [];

let ball;

// Ball object representing user in sketch, stores position and y velocity
class Ball {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.yspeed = 0;
  }
  // visualizes ball
  show() {
    fill(255, 0, 0);
    noStroke();
    circle(this.x, this.y-15, 40);
    strokeWeight(10);
  }
}
function setup() {
  createCanvas(1268, 760) // Fixed canvas mapped to Blender object

  // gets audioContext for pitch detection
  audioContext = getAudioContext();
  mic = new p5.AudioIn();
  mic.start(startPitch);

  // connects with localhost port
  socket = io.connect('http://localhost:5050')
  
  // initializes default pitch line in the center
  for(let i = 0; i < 50; i++) {
    waveformPoints[i] = height/2;
  }

  // initializes user instance of Ball
  ball = new Ball(width/5, height/2);
}

function draw() {

  // displays pitch graph and basic visual info

  background(vol);
  noStroke();
  textSize(64);
  textAlign(CENTER)
  text(lastFreq.toFixed(3), width/2, height/2);
  strokeWeight(10)
  stroke(0, 0, 250)

  for(let i = 1; i < waveformPoints.length; i++) {
    line(width/50*(i-1), height - waveformPoints[i-1], width/50*i, height - waveformPoints[i])
  }

  // Calculates ball's next position via Euler integration
  tempY = ball.y + ball.yspeed;

  if(tempY < height-waveformPoints[10]) { // ball is above line

    if(ball.yspeed <= -5) { // limits ball's y velocity to -5 (UPWARDS)
      ball.yspeed = -5;
    }
    
  } else {
    if((tempY - (height - waveformPoints[10])) < 2) { // Ball stops bouncing when sufficiently close to pitch graph at ball x
      ball.yspeed = 0;
    } else {
      ball.yspeed = -0.8*(tempY - (height - waveformPoints[10])); // Ball bounces upwards proportional to how far below the line it is
    }
    tempY = ball.y + ball.yspeed;
  }
    
    
  ball.y = tempY;
  ball.yspeed++; // ball accelerates downward POSITIVE IS DOWN
  ball.show();
  
  

}
function mousePressed() {
  userStartAudio();
}

function startPitch() {
  // loads ml5 pitch detection model
  pitch = ml5.pitchDetection('./model/', audioContext , mic.stream, modelLoaded);
}

// callback for when ml5 model is loaded, logs update and begins getting pitch
function modelLoaded() {
  console.log("Model Loaded");
  select('#status').html('Model Loaded');
  getPitch();
}

// emits the data via socket to Blender python script
function sendData() {
  var data = {
    data: waveformPoints, // sends array of points representing pitch graph
    ballHeight: ball.y.toFixed(2),
    bkgd: vol
  }
  socket.emit('data', data)
}
function getPitch() {
  pitch.getPitch(
    function(err, frequency) {
      if (err) console.error(error);
      
      waveformPoints.shift(); // shifts array of points over by 1
      if(lastFreq > 0) { // adds last detected frequency to end of pitch graph
        waveformPoints[49] = map(lastFreq, 6, 10, height/5, 4*height/5).toFixed(3);
      }
      else {
        waveformPoints[49] = map(300, 50, 800, height/5, 4*height/5).toFixed(3);
      }
      
      if (frequency) {
        vol = map(mic.getLevel(), 0, 1, 0, 255);
        lastFreq = log(frequency)/log(2); // logarithmic scale for pitch
        select('#result').html(lastFreq);
        
        sendData();

      }
      else {
        select('#result').html('no freqency');
        if(vol > 0) {
          vol--;
        }
        sendData();
      }

      getPitch(); // calls itself over and over again
    }
  )
}
