import asyncio

import unittest

import aioice.stun

from aiortc.exceptions import (
    InvalidAccessError,

)
from ball_animation import BallVideoStreamTrack
from aiortc.mediastreams import AudioStreamTrack, VideoStreamTrack

import asyncio
from aiortc.contrib.signaling import TcpSocketSignaling
from aiortc import RTCPeerConnection
from server import ServerHandler
from client import ClientHandler
from .utils import asynctest


def mids(pc):
    mids = [x.mid for x in pc.getTransceivers()]
    if pc.sctp:
        mids.append(pc.sctp.mid)
    return sorted(mids)


def track_states(pc):
    states = {
        "connectionState": [pc.connectionState],
        "iceConnectionState": [pc.iceConnectionState],
        "iceGatheringState": [pc.iceGatheringState],
        "signalingState": [pc.signalingState],
    }

    @pc.on("connectionstatechange")
    def connectionstatechange():
        states["connectionState"].append(pc.connectionState)

    @pc.on("iceconnectionstatechange")
    def iceconnectionstatechange():
        states["iceConnectionState"].append(pc.iceConnectionState)

    @pc.on("icegatheringstatechange")
    def icegatheringstatechange():
        states["iceGatheringState"].append(pc.iceGatheringState)

    @pc.on("signalingstatechange")
    def signalingstatechange():
        states["signalingState"].append(pc.signalingState)

    return states

class RTCPeerConnectionTest(unittest.TestCase):

    @asynctest
    async def test_addTrack_video(self):
        pc = RTCPeerConnection()

        # add video track
        video_track1 = VideoStreamTrack()
        video_sender1 = pc.addTrack(video_track1)
        self.assertIsNotNone(video_sender1)
        self.assertEqual(video_sender1.track, video_track1)
        self.assertEqual(pc.getSenders(), [video_sender1])
        self.assertEqual(len(pc.getTransceivers()), 1)

        # try to add same track again
        with self.assertRaises(InvalidAccessError) as cm:
            pc.addTrack(video_track1)
        self.assertEqual(str(cm.exception), "Track already has a sender")

        # add another video track
        video_track2 = VideoStreamTrack()
        video_sender2 = pc.addTrack(video_track2)
        self.assertIsNotNone(video_sender2)
        self.assertEqual(video_sender2.track, video_track2)
        self.assertEqual(pc.getSenders(), [video_sender1, video_sender2])
        self.assertEqual(len(pc.getTransceivers()), 2)

    @asynctest
    async def test_connect_audio_and_video_and_data_channel(self):
        pc1 = RTCPeerConnection()
        pc1_states = track_states(pc1)

        pc2 = RTCPeerConnection()
        pc2_states = track_states(pc2)

        self.assertEqual(pc1.iceConnectionState, "new")
        self.assertEqual(pc1.iceGatheringState, "new")
        self.assertIsNone(pc1.localDescription)
        self.assertIsNone(pc1.remoteDescription)

        self.assertEqual(pc2.iceConnectionState, "new")
        self.assertEqual(pc2.iceGatheringState, "new")
        self.assertIsNone(pc2.localDescription)
        self.assertIsNone(pc2.remoteDescription)

        # create offer
        pc1.addTrack(AudioStreamTrack())
        pc1.addTrack(VideoStreamTrack())
        pc1.createDataChannel("chat", protocol="bob")
        offer = await pc1.createOffer()
        self.assertEqual(offer.type, "offer")
        self.assertTrue("m=audio " in offer.sdp)
        self.assertTrue("m=video " in offer.sdp)
        self.assertTrue("m=application " in offer.sdp)

        await pc1.setLocalDescription(offer)

        # handle offer
        await pc2.setRemoteDescription(pc1.localDescription)
        self.assertEqual(pc2.remoteDescription, pc1.localDescription)
        self.assertEqual(len(pc2.getReceivers()), 2)
        self.assertEqual(len(pc2.getSenders()), 2)
        self.assertEqual(len(pc2.getTransceivers()), 2)
        self.assertEqual(mids(pc2), ["0", "1", "2"])

        # create answer
        pc2.addTrack(AudioStreamTrack())
        pc2.addTrack(VideoStreamTrack())
        answer = await pc2.createAnswer()
        self.assertEqual(answer.type, "answer")
        self.assertTrue("m=audio " in answer.sdp)
        self.assertTrue("m=video " in answer.sdp)
        self.assertTrue("m=application " in answer.sdp)

        await pc2.setLocalDescription(answer)
        self.assertTrue("m=audio " in pc2.localDescription.sdp)
        self.assertTrue("m=video " in pc2.localDescription.sdp)
        self.assertTrue("m=application " in pc2.localDescription.sdp)

        # handle answer
        await pc1.setRemoteDescription(pc2.localDescription)
        self.assertEqual(pc1.remoteDescription, pc2.localDescription)

        # check outcome
        # close
        await pc1.close()
        await pc2.close()
    
    def test_video(self):
        track = VideoStreamTrack()
        self.assertEqual(track.kind, "video")
        self.assertEqual(len(track.id), 36)



if __name__ == '__main__':
    # Create an instance of the test class
    unittest.main()
