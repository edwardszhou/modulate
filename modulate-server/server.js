
var express = require('express');
var app = express();
var server = app.listen(5050)

app.use(express.static('public'));

console.log("server is running");

var socket = require('socket.io');

var io = socket(server);

io.sockets.on('connection', newConnection);

function newConnection(socket) {
    console.log('new connection: ' + socket.id);

    // handles pitch and user data {data: [pitch graph], ballHeight: [ball height], bkgd: vol}
    socket.on('data', dataMsg);
    function dataMsg(data) {
        socket.broadcast.emit('data', data)
        
    }
}