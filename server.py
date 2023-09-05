import asyncio
from av import VideoFrame

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription
    )
from aiortc.contrib.signaling import TcpSocketSignaling
from ball_animation import BallVideoStreamTrack


class ServerHandler:

    async def run(self, pc, signaling, ):

        ball_animation = BallVideoStreamTrack()
        def add_tracks():
            pc.addTrack(ball_animation)

        # connect signaling
        await signaling.connect()

        # establishing data-channel to send messages to server
        channel = pc.createDataChannel("coordinates")

        async def send_pings():
            while True:
                channel.send("ping" )
                await asyncio.sleep(0.01)

        @channel.on("open")
        def on_open():
            asyncio.ensure_future(send_pings())

        @channel.on("message")
        def on_message(message):
            rec_x, rec_y = message.split(',')
            rec_x, rec_y = float(rec_x.strip()), float(rec_y.strip())
            if rec_x > 1000:
                 print(f"Frame not parsed")
            else:
                current_x, current_y = ball_animation.get_ball_coord()
                error = ((current_x - rec_x)**2 + (current_y - rec_y)**2)**0.5
                print(f"Old Coordinates: ({rec_x}, {rec_y}) | Error: {error})")

        # send offer
        add_tracks()
        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)

        # consume signaling
        while True:
            obj = await signaling.receive()

            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)
                
            elif obj is None:
                print("Exiting")
                break

if __name__ == "__main__":

    # create signaling and peer connection
    signaling = TcpSocketSignaling('127.0.0.1', 8000)
    pc = RTCPeerConnection()
    server = ServerHandler()
    # run event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            server.run(
                pc=pc,
                signaling=signaling,
            )
        )
    except KeyboardInterrupt:
        print('Finished process')
        pass
    finally:
        # cleanup
        loop.run_until_complete(signaling.close())
        loop.run_until_complete(pc.close())