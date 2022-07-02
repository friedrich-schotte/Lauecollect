"""Platform-independent way to generate sound.
Author: Friedrich Schotte
Date created: 2010-07-02
Date last modified: 2020-09-29
Revision comment: Fixed: Issue: play_sound_file not returning; running in endless loop

Setup:
Install the packages "portaudio" and"pyaudio"
 - "sudo apt-get install portaudio-dev" or "sudo yum install portaudio-devel"
 - "pip install pyaudio"
Revision comment: Cleanup
"""
from logging import warning

__version__ = "1.0.5"


def play_sound(name, volume=4.0):
    play_sound_file(sound_filename(name), volume)


def sound_filename(name):
    return sounds_dir() + "/" + name + ".wav"


def sounds_dir():
    from module_dir import module_dir
    return module_dir(sounds_dir) + "/sounds"


def play_sound_file(filename, volume=1.0):
    # based on people.csail.mit.edu/hubert/pyaudio/#examples
    try:
        import pyaudio
    except ImportError:
        warning("pyaudio module not found. Sound not played.")
    else:
        import wave
        from os.path import exists
        if not exists(filename):
            warning("%s: file not found. Sound not played" % filename)
        else:
            sound_file = wave.open(filename, "rb")

            audio = pyaudio.PyAudio()

            audio_stream = audio.open(
                format=audio.get_format_from_width(sound_file.getsampwidth()),
                channels=sound_file.getnchannels(),
                rate=sound_file.getframerate(),
                output=True,
            )
            chunk_size = 1024
            sound_data = sound_file.readframes(chunk_size)
            while sound_data:
                scaled_data = scale(sound_data, volume)
                audio_stream.write(scaled_data)
                sound_data = sound_file.readframes(chunk_size)
            audio_stream.close()
            audio.terminate()


def scale(data, factor):
    """Scale the amplitude of a sound waveform.
    data: 16-bit signed integers stereo sound samples, stored as string
    scale factor: floating point number: >1 louder, <1 softer, 1 keep volume
    return value: scaled data"""
    from numpy import frombuffer, int16, clip
    values = frombuffer(data, int16)
    values = clip(values * factor, -2 ** 15, 2 ** 15 - 1).astype(int16)
    data = values.tobytes()
    return data


if __name__ == "__main__":  # for testing
    name = 'ding'
    filename = sound_filename(name)
    print(f"play_sound(%r,volume=1.0)" % name)
