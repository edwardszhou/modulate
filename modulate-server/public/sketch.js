// Copyright (c) 2019 ml5
//
// This software is released under the MIT License.
// https://opensource.org/licenses/MIT

/* ===
ml5 Example
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

class Ball {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.yspeed = 0;
  }
  show() {
    fill(255, 0, 0);
    noStroke();
    circle(this.x, this.y-15, 40);
    strokeWeight(10);
  }
}
function setup() {
  createCanvas(1268, 760)
  audioContext = getAudioContext();
  mic = new p5.AudioIn();
  mic.start(startPitch);

  socket = io.connect('http://localhost:5050')
  
  for(let i = 0; i < 50; i++) {
    waveformPoints[i] = height/2;
  }

  ball = new Ball(width/5, height/2);
}

function draw() {


  background(vol);
  noStroke();
  textSize(64);
  textAlign(CENTER)
  text(lastFreq.toFixed(3), width/2, height/2);
  strokeWeight(10)
  stroke(0, 0, 250)

  for(let i = 1; i < waveformPoints.length; i++) {
    //circle(width/50*i,height-waveformPoints[i],width/100)
    line(width/50*(i-1), height - waveformPoints[i-1], width/50*i, height - waveformPoints[i])
  }

  tempY = ball.y + ball.yspeed;
  if(tempY < height-waveformPoints[10]) { // ball is above line

    if(ball.yspeed <= -5) {
      ball.yspeed = -5;
    }
    
  } else {
    if((tempY - (height - waveformPoints[10])) < 2) {
      ball.yspeed = 0;
    } else {
      ball.yspeed = -0.8*(tempY - (height - waveformPoints[10]));
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
  pitch = ml5.pitchDetection('./model/', audioContext , mic.stream, modelLoaded);
}

function modelLoaded() {
  console.log("Model Loaded");
  select('#status').html('Model Loaded');
  getPitch();
}
function sendData() {
  var data = {
    data: waveformPoints,
    ballHeight: ball.y.toFixed(2),
    bkgd: vol
  }
  // let encodedData = encoder.encode();
  // console.log(encodedData)
  // console.log(data)
  socket.emit('data', data)
  //console.log(data);
}
function getPitch() {
  pitch.getPitch(
    function(err, frequency) {
      if (err) console.error(error);
      
      waveformPoints.shift();
      if(lastFreq > 0) {
        waveformPoints[49] = map(lastFreq, 6, 10, height/5, 4*height/5).toFixed(3);
      }
      else {
        waveformPoints[49] = map(300, 50, 800, height/5, 4*height/5).toFixed(3);
      }
      smoothWaveform = smoothThatShit(waveformPoints, 0.999)
      
      if (frequency) {
        // console.log(mic.getLevel());
        vol = map(mic.getLevel(), 0, 1, 0, 255);
        lastFreq = log(frequency)/log(2);
        select('#result').html(lastFreq);
        // if(freqListCounter % 1 == 0 && freqListCounter > 0) {
        //   freqListCounter = 0;
        //   freqList = sort(freqList);
        //   lastFreq = freqList[0]
        //   freqList = []
        // }
        // freqList[freqListCounter] = frequency
        // freqListCounter++;
        
        sendData();

      }
      else {
        select('#result').html('no freqency');
        if(vol > 0) {
          vol--;
        }
        sendData();
      }
      //sendData();

      getPitch();
    }
  )
}
function smoothThatShit(values, alpha) {
  var weighted = average(values) * alpha;
  var smoothed = [];
  for (var i in values) {
      var curr = values[i];
      var prev = smoothed[i - 1] || values[values.length - 1];
      var next = curr || values[0];
      var improved = Number(this.average([weighted, prev, curr, next]).toFixed(2));
      smoothed.push(improved);
  }
  return smoothed;
}

function average(data) {
  var sum = data.reduce(function(sum, value) {
      return sum + value;
  }, 0);
  var avg = sum / data.length;
  return avg;
}
