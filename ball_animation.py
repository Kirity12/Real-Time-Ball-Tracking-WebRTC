import cv2
import numpy as np
from av import VideoFrame

from aiortc import (
    VideoStreamTrack
)

class BallVideoStreamTrack(VideoStreamTrack):
    """
    A video track that returns an animated flag.
    """

    def __init__(self):
        super().__init__()  # don't forget this!

        self.width = 800
        self.height = 600

        # Set up the ball properties
        self.ball_radius = 20
        self.ball_color = (0, 0, 255)
        self.ball_position = [np.random.randint(self.ball_radius, self.width - self.ball_radius), np.random.randint(self.ball_radius, self.height - self.ball_radius)]
        self.ball_velocity = [20,20]

    def get_ball_coord(self):
        return int(self.ball_position[0]), int(self.ball_position[1])
    
    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame = np.ones((self.height, self.width, 3), dtype=np.uint8)*255

        # Update the ball position
        self.ball_position[0] += self.ball_velocity[0]
        self.ball_position[1] += self.ball_velocity[1]

        # Check for collision with walls
        if self.ball_position[0] < self.ball_radius or self.ball_position[0] > self.width - self.ball_radius:
            self.ball_velocity[0] = -self.ball_velocity[0]
        if self.ball_position[1] < self.ball_radius or self.ball_position[1] > self.height - self.ball_radius:
            self.ball_velocity[1] = -self.ball_velocity[1]

        # Draw the ball on the frame
        cv2.circle(frame, (int(self.ball_position[0]), int(self.ball_position[1])), self.ball_radius, self.ball_color, -1)

        frame = VideoFrame.from_ndarray(frame, format="bgr24")

        frame.pts = pts
        frame.time_base = time_base

        return frame
