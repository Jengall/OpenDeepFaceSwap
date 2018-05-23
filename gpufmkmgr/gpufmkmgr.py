import os
import sys
import contextlib

from utils import std_utils
from .pynvml import *

dlib_module = None
def import_dlib(device_idx):
    global dlib_module
    if dlib_module is not None:
        raise Exception ('Multiple import of dlib is not allowed, reorganize your program.')
        
    import dlib
    dlib_module = dlib
    dlib_module.cuda.set_device(device_idx)    
    return dlib_module

tf_module = None
tf_session = None
keras_module = None
keras_contrib_module = None
keras_vggface_module = None

def get_tf_session():
    global tf_session
    return tf_session
    
#allow_growth=False for keras model
#allow_growth=True for tf only model
def import_tf( device_idxs_list, allow_growth ):
    global tf_module
    global tf_session
    
    if tf_module is not None:
        raise Exception ('Multiple import of tf is not allowed, reorganize your program.')

    if 'TF_SUPPRESS_STD' in os.environ.keys() and os.environ['TF_SUPPRESS_STD'] == '1':
        suppressor = std_utils.suppress_stdout_stderr().__enter__()
    else:
        suppressor = None

    if 'CUDA_VISIBLE_DEVICES' in os.environ.keys():
        os.environ.pop('CUDA_VISIBLE_DEVICES')
    
    os.environ['TF_MIN_GPU_MULTIPROCESSOR_COUNT'] = '2'
    
    import tensorflow as tf
    tf_module = tf
    
    visible_device_list = ''
    for idx in device_idxs_list: visible_device_list += str(idx) + ','
    visible_device_list = visible_device_list[:-1]
        
    config = tf_module.ConfigProto()
    config.gpu_options.allow_growth = allow_growth
    config.gpu_options.visible_device_list=visible_device_list
    config.gpu_options.force_gpu_compatible = True
    tf_session = tf_module.Session(config=config)
        
    if suppressor is not None:  
        suppressor.__exit__()

    return tf_module

def finalize_tf():
    global tf_module
    global tf_session
    
    tf_session.close()
    tf_session = None
    tf_module = None

def import_keras():
    global keras_module
    
    if keras_module is not None:
        raise Exception ('Multiple import of keras is not allowed, reorganize your program.')
        
    sess = get_tf_session()
    if sess is None:
        raise Exception ('No TF session found. Import TF first.')
        
    if 'TF_SUPPRESS_STD' in os.environ.keys() and os.environ['TF_SUPPRESS_STD'] == '1':
        suppressor = std_utils.suppress_stdout_stderr().__enter__()
        
    import keras     

    keras.backend.tensorflow_backend.set_session(sess)
    
    if 'TF_SUPPRESS_STD' in os.environ.keys() and os.environ['TF_SUPPRESS_STD'] == '1':        
        suppressor.__exit__()

    keras_module = keras
    return keras_module
    
def finalize_keras():
    global keras_module
    keras_module.backend.clear_session()
    keras_module = None
    
def import_keras_contrib():
    global keras_contrib_module
    
    if keras_contrib_module is not None:
        raise Exception ('Multiple import of keras_contrib is not allowed, reorganize your program.')
    import keras_contrib
    keras_contrib_module = keras_contrib
    return keras_contrib_module
    
def finalize_keras_contrib():
    global keras_contrib_module
    keras_contrib_module = None
    
def import_keras_vggface(optional=False):
    global keras_vggface_module
    
    if keras_vggface_module is not None:
        raise Exception ('Multiple import of keras_vggface_module is not allowed, reorganize your program.')

    try:
        import keras_vggface
    except:
        if optional:
            print ("Unable to import keras_vggface. It will not be used.")
        else:
            raise Exception ("Unable to import keras_vggface.")
        keras_vggface = None
        
    keras_vggface_module = keras_vggface
    return keras_vggface_module
    
def finalize_keras_vggface():
    global keras_vggface_module
    keras_vggface_module = None    
    
#returns [ (device_idx, device_name), ... ]
def getDevicesWithAtLeastFreeMemory(freememsize):
    result = []
    
    nvmlInit()
    for i in range(0, nvmlDeviceGetCount() ):
        handle = nvmlDeviceGetHandleByIndex(i)
        memInfo = nvmlDeviceGetMemoryInfo( handle )
        if (memInfo.total - memInfo.used) >= freememsize:
            result.append (i)
        
    nvmlShutdown()
        
    return result
    
def getDevicesWithAtLeastTotalMemoryGB(totalmemsize_gb):
    result = []
    
    nvmlInit()
    for i in range(0, nvmlDeviceGetCount() ):
        handle = nvmlDeviceGetHandleByIndex(i)
        memInfo = nvmlDeviceGetMemoryInfo( handle )
        if (memInfo.total) >= totalmemsize_gb*1024*1024*1024:
            result.append (i)
        
    nvmlShutdown()
        
    return result
def getAllDevicesIdxsList ():
    nvmlInit()    
    result = [ i for i in range(0, nvmlDeviceGetCount() ) ]    
    nvmlShutdown()        
    return result
    
def getDeviceVRAMFree (idx):
    result = 0
    nvmlInit()
    if idx < nvmlDeviceGetCount():    
        handle = nvmlDeviceGetHandleByIndex(idx)
        memInfo = nvmlDeviceGetMemoryInfo( handle )
        result = (memInfo.total - memInfo.used)        
    nvmlShutdown()
    return result
    
def getDeviceVRAMTotalGb (idx):
    result = 0
    nvmlInit()
    if idx < nvmlDeviceGetCount():    
        handle = nvmlDeviceGetHandleByIndex(idx)
        memInfo = nvmlDeviceGetMemoryInfo( handle )
        result = memInfo.total / (1024*1024*1024)
    nvmlShutdown()
    return result
    
def getBestDeviceIdx():
    nvmlInit()    
    idx = -1
    idx_mem = 0
    for i in range(0, nvmlDeviceGetCount() ):
        handle = nvmlDeviceGetHandleByIndex(i)
        memInfo = nvmlDeviceGetMemoryInfo( handle )
        if memInfo.total > idx_mem:
            idx = i
            idx_mem = memInfo.total

    nvmlShutdown()
    return idx
    
def getWorstDeviceIdx():
    nvmlInit()    
    idx = -1
    idx_mem = sys.maxsize
    for i in range(0, nvmlDeviceGetCount() ):
        handle = nvmlDeviceGetHandleByIndex(i)
        memInfo = nvmlDeviceGetMemoryInfo( handle )
        if memInfo.total < idx_mem:
            idx = i
            idx_mem = memInfo.total

    nvmlShutdown()
    return idx
    
def isValidDeviceIdx(idx):
    nvmlInit()    
    result = (idx < nvmlDeviceGetCount())
    nvmlShutdown()
    return result
    
def getDeviceIdxsEqualModel(idx):
    result = []
    
    nvmlInit()    
    idx_name = nvmlDeviceGetName(nvmlDeviceGetHandleByIndex(idx)).decode()

    for i in range(0, nvmlDeviceGetCount() ):
        if nvmlDeviceGetName(nvmlDeviceGetHandleByIndex(i)).decode() == idx_name:
            result.append (i)
         
    nvmlShutdown()
    return result
    
def getDeviceName (idx):
    result = ''
    nvmlInit()    
    if idx < nvmlDeviceGetCount():    
        result = nvmlDeviceGetName(nvmlDeviceGetHandleByIndex(idx)).decode()
    nvmlShutdown()
    return result