# -*- coding: utf-8 -*-
import pyaudio
import socket
from threading import Thread

VOICEPORT = 54321
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
frames = []
p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                )

def udpStream(address):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        if len(frames) > 0:
            data = frames.pop(0)
            for addr in address:
                udp.sendto(data, addr)

    # udp.close()

def record(stream, CHUNK):
    while True:
        frames.append(stream.read(CHUNK))


def send_voice(address):
    Tr = Thread(target=record, args=(stream, CHUNK))
    Ts = Thread(target=udpStream, args=(address, ))
    Tr.setDaemon(True)
    Ts.setDaemon(True)
    Tr.start()
    Ts.start()
    Tr.join()
    Ts.join()


if __name__ == "__main__":
    send_voice([('192.168.191.2', VOICEPORT)])
