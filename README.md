# Video Streaming Server-Client

This repository contains a server-client program for video streaming using the aiortc library. The server generates continuous 2D images of a bouncing ball and transmits them to the client, which displays the images using OpenCV. The client performs ball tracking on the received frames and sends the computed ball coordinates back to the server.

## Requirements

- Python 3.10 or higher
- aiortc library
- OpenCV library

## Server Usage

To run the server, follow these steps:

1. Open a terminal and navigate to the repository's directory.

2. Run the server program:

        python server.py

3. The server will start generating the bouncing ball animation and transmitting the frames to the client.

4. On the server sider terminal, user can see message (coordinates and error) sent by client

## Client Usage

To run the client, follow these steps:

1. Open a new terminal and navigate to the repository's directory.

2. Run the client program:

        python3 client.py

3. The client will receive the offer from the server and display the received frames using OpenCV. It will also start a separate process for ball tracking.

4. The client process will track the ball in the frames using OpenCV's Hough Circle Transform and store the computed x, y coordinates.

5. The client will open an aiortc data channel to the server and send the ball coordinates to the server.

6. The server will receive the coordinates from the client and compute the error to the actual location of the ball.

7. The server will display the received coordinates and the calculated error.

## Configuration

- Server IP Address: 127.0.0.1

- Server Port: 8000
