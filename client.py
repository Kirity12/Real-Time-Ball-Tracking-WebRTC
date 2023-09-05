import asyncio

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
)
from aiortc.contrib.signaling import TcpSocketSignaling
import cv2 
import numpy as np
import multiprocessing as mp
        

class ClientHandler:

    def __init__(self, ):
        self.__track = []
        self.x_coordinate_value = mp.Value('d', 0)
        self.y_coordinate_value = mp.Value('d', 0)
        self.process_a = mp.Process(target=self.track_ball, args=())
        self.frame_queue = mp.Queue()
        self.process_a.start()

    
    def track_ball(self):
        while  True:
            if self.frame_queue:
                try:
                    frame_ff = self.frame_queue.get()
                    gray = cv2.cvtColor(frame_ff, cv2.COLOR_BGR2GRAY)
                    # Apply Gaussian blur to reduce noise
                    blur = cv2.GaussianBlur(gray, (5, 5), 0)

                    # Apply Hough Circle Transform
                    circles = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, dp=1, minDist=50, param1=50, param2=30, minRadius=10, maxRadius=30)
                    if circles is not None:
                        # Convert the (x, y) coordinates and radius of the circles to integers
                        circles = np.round(circles[0, :]).astype("int")

                        x, y, _ = circles[0]
                        self.x_coordinate_value.value = x
                        self.y_coordinate_value.value = y
                    else:
                        self.x_coordinate_value.value = 5000
                        self.y_coordinate_value.value = 5000
                except:
                    pass
            else:
                self.x_coordinate_value.value = 5000
                self.y_coordinate_value.value = 5000
    

    async def run_track(self, track):
        while True:
            try:
                frame = await track.recv()
                frame_ff = frame.to_ndarray(format='bgr24')
                self.frame_queue.put(frame_ff)

                cv2.imshow('Client Window', frame_ff)
                if cv2.waitKey(1)== ord('q') or cv2.getWindowProperty('Client Window', cv2.WND_PROP_VISIBLE) <1:
                    print("Press cntrl + C to exit")
                    cv2.destroyAllWindows()
                    self.process_a.join()
                    break
                await asyncio.sleep(0.1)
            except:
                cv2.destroyAllWindows()
                self.process_a.join()
                return

    async def start(self):
        for track in self.__track:
            asyncio.ensure_future(self.run_track(track))

    async def run(self, pc, signaling):
        # add meadia media track to our media player
        @pc.on("track")
        def on_track(track):
            self.__track.append(track)

        # connect signaling
        await signaling.connect()

        # establishing data-channel to send messages to server
        @pc.on("datachannel")
        def on_datachannel(channel):

            @channel.on("message")
            def on_message(message):
                channel.send(f"{self.x_coordinate_value.value},{self.y_coordinate_value.value}")

        # consume signaling
        while True:
            try:
                obj = await signaling.receive()

                if isinstance(obj, RTCSessionDescription):
                    await pc.setRemoteDescription(obj)
                    await pc.setLocalDescription(await pc.createAnswer())
                    await signaling.send(pc.localDescription)

                    await self.start()
                    # send answer
                elif obj is None:
                    print("Exiting")
                    break
            except:
                pass


if __name__ == "__main__":

    # create signaling and peer connection
    signaling = TcpSocketSignaling('127.0.0.1', 8000)
    pc = RTCPeerConnection()

    # create media source
    client = ClientHandler()
    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            client.run(
                pc=pc,
                signaling=signaling,
            )
        )
    except KeyboardInterrupt:
        print('Finished process')
        cv2.destroyAllWindows()
        client.process_a.join()
        pass
    finally:
        # cleanup
        cv2.destroyAllWindows()
        client.frame_queue.put(None)
        client.process_a.join()
        # loop.run_until_complete(client.process_a.join())
        loop.run_until_complete(pc.close())
        loop.run_until_complete(signaling.close())
        
