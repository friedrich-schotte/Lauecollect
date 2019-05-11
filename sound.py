"""Platform-indepedent way to generate sound.
Friedrich Schotte, 2 Jul 2010 - 28 Feb 2016
Setup:
Install the packages "portaudio" and"pyaudio"
("sudo apt-get install portaudio-dev" or "sudo yum install portaudio-devel"
"sudo pip install pyaudio" or "sudo easy_install pyaudio")
"""
from logging import warn
__version__ = "1.0.1" # volume control

def play_sound(name,volume=4.0):
    play_sound_file(module_dir()+"/sounds/"+name+".wav",volume)

def play_sound_file(filename,volume=1.0):
    # based on people.csail.mit.edu/hubert/pyaudio/#examples
    try: import pyaudio
    except ImportError:
        warn("pyaudio module not found. Sound not played."); return
    import wave
    from os.path import exists
    
    if not exists(filename):
        print "%s: file not found. Sound not played" % filename; return
    wf = wave.open(filename,"rb")

    p = pyaudio.PyAudio()

    # open stream
    stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
        channels = wf.getnchannels(),rate = wf.getframerate(),output = True)
    # read data
    chunk = 1024
    data = wf.readframes(chunk)
    # play stream
    while data != '':
        stream.write(scale(data,volume))
        data = wf.readframes(chunk)
    stream.close()
    p.terminate()

def scale(data,factor):
    """Scale the amplitude of a sound waveform.
    data: 16-bit signed integers stereo sound samples, stored as string
    scale factor: flotign point number: >1 louder, <1 softer, 1 keep volume
    return value: scaled data"""
    from numpy import fromstring,int16,clip
    values = fromstring(data,int16)
    values = clip(values*factor,-2**15,2**15-1).astype(int16)
    data = values.tostring()
    return data

def module_dir():
    """directory in which the .py file of current module is located"""
    from os.path import dirname
    return dirname(module_path())

def module_path():
    """Full pathname of the current module"""
    from sys import path
    from os import getcwd
    from os.path import basename,exists
    from inspect import getmodulename,getfile
    # 'getfile' retreives the source file name name compiled into the .pyc file.
    pathname = getfile(lambda x: None)
    if exists(pathname): return pathname
    # The module might have been compiled on a different machine or in a
    # different directory.
    pathname = pathname.replace("\\","/")
    filename = basename(pathname)
    dirs = [dir for dir in [getcwd()]+path if exists(dir+"/"+filename)]
    if len(dirs) == 0: print "pathname of file %r not found" % filename
    dir = dirs[0] if len(dirs) > 0 else "."
    pathname = dir+"/"+filename
    return pathname


if __name__ == "__main__": # for testing
    print("play_sound('ding',volume=1.0)")
