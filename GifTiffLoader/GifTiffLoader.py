"""GifTiffLoader is a module to automatically load Tiff and Gif files as
numpy arrays using PIL.  Specifically it is designed to deal with 8-bit
and 16-bit images typically used as the standard formats for microscope
images.  It is also designed to deal with image stacks (Animated Gifs and
Multi-page Tiffs) and image sequences (both 3D and 4D sequences).

GifTiffLoader also relies on wxPython and FilenameSort.

Sponsored by the NSF and HFSP through the Shane Hutson Laboratory, part of
Vanderbilt Institute of Integrative Biosystems Research (VIIBRE)."""

__author__ = "David N. Mashburn <david.n.mashburn@gmail.com>"

import os
import numpy as np

try:
    from PIL import Image # Use pillow if available
except:
    import Image # Fall back on old PIL

import wx

from FilenameSort import (cmp_fnames, cmp_fnames_A, getSortedListOfFiles,
                          getSortedListOfNumericalEquivalentFiles as get_ne_files)

# This module can load and save .tiff and .gif formats as numpy arrays...

_gif_names = 'gif GIF Gif'.split()
_tif_names = 'tif TIF Tif tiff TIFF Tiff'.split()

def _select_file_if_none(filename, use_print=False):
    if filename is None:
        filename = wx.FileSelector()
        if use_print:
            print filename
    
    return filename

def _select_dir_if_none(dirname, use_print=False):
    if dirname is None:
        dirname = wx.DirSelector()
        if use_print:
            print dirname
    
    return dirname

def DivideConvertType(arr, bits=16, maxVal=None, zeroMode='clip',
                      maxMode='clip'):
    type_dict = {8: np.uint8, 16: np.uint16, 32: np.uint32, 64: np.uint64}
    
    #Get datatype from bits...
    # Note that this function is only useful for unsigned ints!
    assert maxMode in ['clip', 'stretch'], \
           "'maxMode' must be either 'clip' or 'stretch'"
    assert type(maxVal) in [type(None), int], \
           "'maxVal' must be given as an integer (or None)!"
    assert zeroMode in ['clip' , 'abs' , 'stretch'], \
           "'zeroMode' must be one of: 'clip' , 'abs' , 'stretch'"
    assert bits in type_dict.keys(), \
           "'bits' must be one of 8, 16, 32, 64"
    
    maxClip = (maxVal
               if maxMode == 'stretch' and maxVal is not None else
               2**bits-1)
    
    if maxMode == 'clip' and maxVal is not None:
        arr.clip(arr.min(), maxVal, out=arr) # in place
    
    minVal = arr.min() if zeroMode == 'stretch' else 0
    maxVal = arr.max() if maxVal is None else maxVal
    
    if zeroMode == 'clip':
        arr.clip(0, arr.max(), out=arr) # in place
    elif zeroMode == 'abs':
        np.absolute(arr, out=arr) # in place
    
    clipRatio = 1. * maxClip / (maxVal-minVal)
    
    if zeroMode == 'stretch' or clipRatio < 1:
        arr = np.double(arr)
        arr -= minVal # separate step cuts down on memory usage...
        if clipRatio < 1:
            arr *= clipRatio
    
    return arr.astype(type_dict[bits])

def ConvertTo8Bit(arr):
    return DivideConvertType(arr,8)    

def ConvertTo16Bit(arr):
    return DivideConvertType(arr,16)

def ConvertTo32Bit(arr):
    return arr.asarray(np.float32) #DivideConvertType(t,32) # b/c we want 32 bit float, not uint

def Convert16BitToRGBImage(arr16):
    '''Transform a 16 bit image into an rgba image with:
       red: most significant
       green: least significant
       blue: 0'''
    return np.asarray(a.byteswap(),np.uint32).view(np.uint8).reshape(a.shape+(4,))[:,:,:3]

def Convert16BitToRGBAImage(arr16):
    '''Transform a 16 bit image into an rgba image with:
       red: most significant
       green: least significant
       blue: 0
       alpha: 255'''
    rgba = np.asarray(a.byteswap(),np.uint32).view(np.uint8).reshape(a.shape+(4,))
    rgba[:,:,3] = 255
    return rgba

def ConvertRGBImageTo16Bit(rgb):
    '''Convert the red&green channels of an rgb(a) image to a 16 bit image, with:
       red: most significant
       green: least significant'''
    return np.array(rgb[:,:,::-2]).view(np.uint16).reshape(rgb.shape[:2])    

def GetShape(filename=None):
    filename = _select_file_if_none(filename)
    im = Image.open(filename)
    
    assert im.format in (_tif_names + _gif_names), \
           'Unsupported image format type! {0}'.format(im.format)
    
    datatype = (np.uint16 if im.format in _tif_names else
                np.uint8) # if im.format in _gif_names
    
    h, w = im.size
    
    numFrames = 0
    while True:
        numFrames += 1
        try:
            im.seek(numFrames)
        except EOFError:
            break # end of sequence
    
    return numFrames, w, h

def GetDirectoryFiles(dirname=None, wildcard='*[!.txt]'):
    dirname = _select_dir_if_none(dirname)
    return getSortedListOfFiles(dirname, globArg=wildcard)

def GetFilesAndIndices(dirname=None, wildcard='*[!.txt]', dims=1):
    assert dims <= 2, 'No code for 5D+ stacks... yet...'
    files = GetDirectoryFiles(dirname=None, wildcard='*[!.txt]')
    if len(files) == 0:
        return None
    if dims == 1: # flat sequence (time series)
        return files, len(files)
    else: # series of z-stacks
        ftz = []
        for f in files:
            s = os.path.split(f)[1].split('_')
            if len(s) >= 3:
                t = int(s[-2])
                z = int(s[-1][:3])
                ftz.append([f, t, z])
        return zip(ftz)

def GetDatatype(im, im_arr=None):
    """Automatically determine the datatype using the PIL -> numpy conversion."""
    
    # TODO: Need to add more smarts to this based on the mode 'I;16' vs. RGB, etc...
    #'1','P','RGB','RGBA','L','F','CMYK','YCbCr','I',
    # Can I simplify this by simply fixing the PIL -> numpy conversion?
    
    # Old way:
    #if im.format in _tif_names:  datatype=np.uint16
    #elif im.format in _gif_names: datatype=np.uint8
    
    if im_arr is None:
        im_arr=np.array(im)
    
    # Work around for windows:
    if im_arr.dtype==np.object:
        if im.mode=='L': # 8-bit gray scale
            datatype = np.uint8
        elif im.mode in ['I;16', 'I;16B']: # 16-bit gray scale
            datatype = np.uint16
        elif im.mode in ['I','F']: # 32-bit gray scale (int and float)
            print '32-bit images not supported at this time!'
        else:
            print 'Unknown image type!  Assume to 16-bit...'
            datatype = np.uint16
    elif im_arr.dtype in [np.uint8,np.uint16,np.float32]:
        datatype = im_arr.dtype
    elif im_arr.dtype in [np.int16, np.dtype('>u2'), np.dtype('>i2')]:
        datatype = np.uint16 # Convert from int16 to uint16 (same as what ImageJ does [I think])
    else:
        print 'What kind of image format is this anyway???'
        print 'Datatype looks like:', t.dtype
        print 'Should be a 16 or 32 bit tiff or 8 bit unsigned gif or tiff'
        return
    
    return datatype

def GetShapeMonolithicOrSequence(filename=None):
    filename = _select_file_if_none(filename)
    numFrames, w, h = GetShape(filename)
    isSequence = (numFrames == 1)
    if isSequence:
        numFrames = len(get_ne_files(filename, os.path.split(filename)[0]))
    return numFrames, w, h, isSequence


def LoadSingle(filename=None):
    filename = _select_file_if_none(filename)
    im=Image.open(filename)
    im_arr=np.array(im)
    # Try to automatically determine the datatype using the PIL -> numpy conversion.
    datatype = GetDatatype(im, im_arr)
    im_arr = (im_arr.astype(datatype)
              if im_arr.dtype!=np.object else
              np.array(im.getdata(), datatype)) # work around for windows
    im_arr.resize(im.size[1],im.size[0])
    return im_arr

# No longer needed:
# Patch around 16-bit endianness bug for PIL before version 1.1.7...
#if Image.VERSION in ['1.1.4','1.1.5','1.1.6'] and im.format in _tif_names:
#    fid=open(filename,'rb')
#    endianness=fid.read(2)
#    fid.close()
#    if endianness=='MM':
#        t.byteswap(True)
#    elif endianness=='II':
#        pass
#    else:
#        print "Just so you know... that ain't no tiff!"

def _assert_valid_format(im_format, tiffBits):
    assert im_format in _gif_names+_tif_names, \
           'Unsupported Format!  Choose Gif or Tiff format'
    assert tiffBits in [8, 16, 32], \
           'Unsupported tiff format!  Choose 8, 16, or 32 bit.'

# I also need to check for filenames with the same base in the selected folder
# And then give a "stupidity check" for overwriting
# d = wx.MessageDialog(None, 'Are you sure?')
# d.ShowModal() == wx.ID_CANCEL
# Same for Sequence and monolithic...
# PIL saved images look stupid...  test manually again
# PIL is too dubm to figure out TIF instead of TIFF -- Fix this...
def SaveSingle(arr, filename=None, im_format='gif', tiffBits=16):
    _assert_valid_format(im_format, tiffBits)
    
    formatName = ('Tiff' if im_format in _tif_names else
                  'Gif') #if im_format in _gif_names
    bits = 8 if im_format in _gif_names else tiffBits
    datatype = {8: np.uint8, 16: np.uint16, 32: np.float32}[bits]
    
    if filename is None:
        filename=wx.SaveFileSelector('Array as '+formatName,'.'+format)
    
    # Make the directory if it does not exist
    if not os.path.exists(os.path.split(filename)[0]):
        os.mkdir(os.path.split(filename)[0])
    
    if datatype != arr.dtype:
        arr = (arr.astype(np.float32) if bits==32 else
               DivideConvertType(arr, bits=bits))
    mode = {8: None, 16: 'I;16', 32: 'F'}[bits] # Should I ever use I;16B ???
    im = Image.fromarray(arr, mode=mode)
    im.save(filename, formatName)

def LoadFileSequence(dirname=None, wildcard='*[!.txt]'):
    files = GetDirectoryFiles(dirname, wildcard)
    numFiles = len(files)
    
    if numFiles==0:
        return
    
    t0 = LoadSingle(files[0])
    t = np.zeros([numFiles, t0.shape[0], t0.shape[1]], t0.dtype)
    
    for i in range(numFiles):
        t[i] = LoadSingle(files[i])
    
    return t

def SaveFileSequence(arr, basename=None, im_format='gif', tiffBits=16,
                     sparseSave=None, functionToRunOnFrames=None):
    '''Save a sequence of files with the format _t_zzz where t is the
    stack number and zzz is the frame number.
    "tiffBits" should be 8 or 16.
    "sparseSave" should either be None (the default) or a boolean list the same shape as the z-t shape of the array.
    If specified, it determines which files should be saved and which should not.
    It is basically a way to save only SOME of the files in the sequence.

    If a single (2D) image is passed, z and t will be set to 0,0.
    If a 3D image is passed, t will always be 0'''
    _assert_valid_format(im_format, tiffBits)
    assert arr.ndim <= 4,\
          'SaveFileSequence does not support saving arrays with more than 4 dimensions!'
    if basename is None:
        basename=wx.SaveFileSelector('Array as Sequence of Gifs -- numbers automatically added to',
                                     '.'+im_format)
    
    if arr.dtype == np.uint8 and arr.max() > 255: # THIS CAN NEVER ACTUALLY RUN
        arr = np.array(arr * 255. / arr.max(), np.uint8)
    
    if functionToRunOnFrames is None:
        functionToRunOnFrames = lambda x:x
    
    new_name = os.path.splitext(basename)[0] + '_{}_{:03d}.' + im_format
    
    # Pad arr with extra singleton dimesions to make the loop below work
    arr = arr.reshape((1,)*(4-arr.ndim) + arr.shape)
    
    # Add singleton dimensions to sparseSave if needed
    if (sparseSave is not None and
        len(sparseSave) and
        not hasattr(sparseSave[0], '__iter__')):
        if arr.shape[0] == 1:
            sparseSave = [sparseSave]
        elif arr.shape[1] == 1:
            sparseSave = [[i] for i in sparseSave] # 3D time array passed
        else:
            raise ValueError('sparseSave must be nested for a fully 4D arr!')
    
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            if (sparseSave is None) or sparseSave[i][j]:
                SaveSingle(functionToRunOnFrames(arr[i,j]),
                           new_name.format(i, j),
                           im_format=im_format, tiffBits=tiffBits)
    
SaveFileSequence4D=SaveFileSequence

def LoadMonolithic(filename=None):
    #f='C:/Documents and Settings/Owner/Desktop/Stack_Zproject_GBR_DC.gif'
    filename = _select_file_if_none(filename)
    im = Image.open(filename)
    
    datatype = GetDatatype(im)
    
    l=[]
    numFrames=0
    while True:
        l.append(np.asarray(im.getdata(), dtype=datatype))
        numFrames += 1
        try:
            im.seek(im.tell() + 1)
        except EOFError:
            break # end of sequence
    
    t=np.array(l, dtype=datatype)
    t.resize(numFrames, im.size[1], im.size[0])
    return t

def LoadFrameFromMonolithic(filename=None,frameNum=0):
    #f='C:/Documents and Settings/Owner/Desktop/Stack_Zproject_GBR_DC.gif'
    filename = _select_file_if_none(filename)
    im = Image.open(filename)
    
    datatype = GetDatatype(im)
    
    t = None
    i = 0
    while True:
        if i == frameNum:
            t = np.asarray(im.getdata(), dtype=datatype)
            t.resize(im.size[1], im.size[0])
            break
        i += 1
        try:
            im.seek(im.tell() + 1)
        except EOFError:
            break # end of sequence
    
    if t is None:
        print 'Frame not able to be loaded'
    
    return t

def SaveMonolithic(arr,filename=None):
    pass #Coming soon! -- see Examples/PIL Examples/gifmaker
    # Can I do monolithic Tiff, too??

def LoadMonolithicOrSequenceSpecial(filename=None):
    filename = _select_file_if_none(filename)
    
    numFrames, w, h, isSequence = GetShapeMonolithicOrSequence(filename)
    
    if isSequence:
        files = get_ne_files(filename, os.path.split(filename)[0])
        if len(files)==0:
            print 'Empty Directory!'
            return
        t0=LoadSingle(files[0])
        
        t=np.zeros([len(files), t0.shape[0], t0.shape[1]], t0.dtype)
        
        for i in range(len(files)):
            t[i] = LoadSingle(files[i])
        
        return t
    else:
        return LoadMonolithic(filename)

def LoadSequence4D(dirname=None, wildcard='*[!.txt]'):
    dirname = _select_dir_if_none(dirname)
    
    files, t_inds, z_inds = GetFilesAndIndices(dirname, wildcard, dims=2)
    
    if not files:
        print 'Empty Directory!'
        return
    
    test = LoadSingle(files[0][0])
    
    tdim, zdim = [max(i) + 1 for i in [t_inds, z_inds]]
    xdim, ydim = test.shape
    arr = np.zeros([tdim, zdim, xdim, ydim], test.dtype)
    
    #load the data for each gif directly into one big array, indexing based on numbering
    for f, t, z in zip(files, t_inds, z_inds):
        arr[t, z] = LoadSingle(f)
    
    return arr

def LoadMonolithicSequence4D(dirname=None, wildcard='*[!.txt]'):
    files = GetDirectoryFiles(dirname, wildcard)
    
    if len(files)==0:
        print 'Empty Directory!'
        return
    
    t0 = LoadMonolithic(files[0])
    
    t = np.zeros([len(files)] + list(t0.shape), t0.dtype)
    
    for i in range(len(files)):
        t[i] = LoadMonolithic(files[i])
    
    return t

def LoadGroupedZCroppedByTxtInput(dirname, StartStopTxt, mergeOperation=None):
    """StartStopTxt gives the range to load for each stack... "0: 4-9\n1: 5-10\n2: 5-11"
    The stack number before the colon is NOT ACTUALLY USED, stacks are just processed in order.
    For mergeOperation, select 'None','mean','max','min',or 'sum'"""
    StartStop = [map(int,i.replace(' ','').split(':')[1].split('-'))
                 for i in StartStopTxt.split('\n')]
    stacks = []
    for i,p in enumerate(StartStop):
        stacks.append([])
        files = getSortedListOfFiles(dirname, globArg="*_"+str(i)+"_*PMT1.TIF")
        files = files[p[0]:p[1]+1] # only pick out some files
        for f in files:
            stacks[-1].append(LoadSingle(f))
        stacks[-1] = np.array(stacks[-1])
    
    if mergeOperation in ['mean', 'max', 'min', 'sum']:
        return np.array([i.__getattribute__(mergeOperation)(axis=0) for i in stacks])
    elif mergeOperation != None:
        print 'Invalid mergeOperation!  Returning the stacks list instead'
    
    return stacks # has to be a list not an array b/c elements might not be the same length
        

if __name__=='__main__':
    app = wx.App(0)
    t = LoadFileSequence()
    print 'Loaded an array of type', t.dtype, 'with shape', t.shape
    
    import DelayApp
