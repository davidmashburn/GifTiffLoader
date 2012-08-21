GifTiffLoader is a module to automatically load Tiff and Gif files as
numpy arrays using PIL.

Specifically it is designed to deal with 8-bit
and 16-bit images typically used as the standard formats for microscope
images.  It is also designed to deal with image stacks (Animated Gifs and
Multi-page Tiffs) and image sequences (both 3D and 4D sequences).

GifTiffLoader relies on two other modules, FilenameSort and cmpGen.

Sponsored by the NSF, NIH, and HFSP through the Shane Hutson Laboratory, part of
Vanderbilt Institute of Integrative Biosystems Research (VIIBRE).
