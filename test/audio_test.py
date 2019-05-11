"""Platform-indepedent way to generate sound.
Friedrich Schotte, 2 Jul 2010
Need to install the package PyAudio from people.csail.mit.edu/hubert/pyaudio
"""

def play_sound(filename):
    # based on people.csail.mit.edu/hubert/pyaudio/#examples
    try: import pyaudio
    except ImportError:
        print "pyaudio module not found. Sound not played."; return
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
        stream.write(data)
        data = wf.readframes(chunk)
    stream.close()
    p.terminate()

def module_dir():
    "directory in which the .py file of current module is located"
    from sys import path
    from os import getcwd
    from os.path import exists
    from inspect import getmodulename,getfile
    modulename = getmodulename(getfile(lambda x: None))
    ##print "module name: %r" % modulename
    dirs = [dir for dir in [getcwd()]+path if exists(dir+"/"+modulename+".py")]
    dir = dirs[0] if len(dirs) > 0 else "."
    return dir

if __name__ == "__main__":
    play_sound(module_dir()+"/sounds/ding.wav")
