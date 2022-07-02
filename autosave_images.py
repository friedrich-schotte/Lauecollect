from instrumentation import microscope_camera
from instrumentation import widefield_camera
from time import time
from instrumentation import SampleX, SampleY,SampleZ

root = '\\\\femto\\C\\All Projects\\LaserLab\\Crystalography\\'

def save_to_file(filename,object,):
    """
    save a python object to a file

    Parameters
    ----------
    Args:
        filename (string)
            the full path and filename
        object (python object)
            a python object

    Returns
    -------

    Examples
    --------
    the example of usage

    >>> save_to_file('test.pkl',[1,2,3])
    """
    from pickle import dump
    with open(filename,"wb") as f:
        dump(object,f)


def load_from_file(filename):
    """
    read object from a file

    Parameters
    ----------
    filename : string
        the full path and filename

    Returns
    -------
    object : object
        input object to save.

    Examples
    --------
    the example of usage

    >>> list_out = load_from_file('list.extension')

    """
    from pickle import load
    with open(filename,'rb') as f:
        data = load(f, encoding='bytes')
    return data

def save_image(name = ''):
    from instrumentation import microscope_camera
    from instrumentation import widefield_camera
    from time import time
    from instrumentation import SampleX, SampleY,SampleZ
    dict = {}
    dict['x'] = SampleX.value
    dict['y'] = SampleY.value
    dict['z'] = SampleZ.value
    dict['microscope'] = microscope_camera.RGB_array
    dict['widefield'] = widefield_camera.RGB_array
    dict['name'] = name
    
    from instrumentation import SampleX, SampleY,SampleZ
    filename = root+str(time()) +'_'+name+ '.dicpkl'
    save_to_file(filename,dict)
    print('saved to {}'.format(filename))
    
