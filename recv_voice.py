# -*- coding: utf-8 -*-
import pyaudio
import socket
import time
from threading import Thread

VOICEPORT = 54321
frames = []
FORMAT = pyaudio.paInt16
CHUNK = 1024
CHANNELS = 2
RATE = 44100

p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK,
                )


def udpStream(CHUNK, port):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(('', port))

    while True:
        sound_data, addr = udp.recvfrom(CHUNK * CHANNELS * 2)
        frames.append(sound_data)

    # udp.close()


def play(stream, CHUNK):
    BUFFER = 10
    while True:
        if len(frames) == BUFFER:
            while True:
                try:
                    voice = frames.pop(0)
                except IndexError:
                    time.sleep(0.2)
                    continue
                stream.write(voice, CHUNK)


def receive_voice(port=VOICEPORT):
    Ts = Thread(target=udpStream, args=(CHUNK, port))
    Tp = Thread(target=play, args=(stream, CHUNK))
    Ts.setDaemon(True)
    Tp.setDaemon(True)
    Ts.start()
    Tp.start()
    Ts.join()
    Tp.join()


if __name__ == "__main__":
    receive_voice(33333)
