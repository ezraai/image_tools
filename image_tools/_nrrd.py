import nrrd
import numpy as np
import SimpleITK as sitk

from _math import num_from_str_vec, trx_lps_to_ras

NRRD_SPACE_ORIGIN = u'space origin'
NRRD_SPACE_DIRECTIONS = u'space directions'
NRRD_SPACE = u'space'
NRRD_LPS_SPACE='left-posterior-superior'
NRRD_RAS_SPACE='right-anterior-superior'


def _info_image(image, title=None):

    size = image.GetSize()
    dimension = image.GetDimension()
    width = image.GetWidth()
    height = image.GetHeight()
    depth = image.GetDepth()
    origin = image.GetOrigin()
    direction = image.GetDirection()
    spacing = image.GetSpacing()


    print 'Image Details' if title is None else 'Image Details [%s]'%title
    print 'origin    :', origin
    print 'direction : ', ['%.2f'%x for x in direction]
    print 'size      :', size
    print 'dimension :', dimension
    print 'width     :', width
    print 'height    :', height
    print 'depth     :', depth
    print 'spacing   :', spacing

def _load_multi_image(header, data, validation_file = None):
    images = []
    N = np.shape(data)[0] # number of volumes
    for i in range(N):
        vol_header = header.copy()
        vol_header[NRRD_SPACE_DIRECTIONS] = header[NRRD_SPACE_DIRECTIONS][1:]
        volume = _load_single_image(vol_header, data[i,...])
        #_info_image(volume,title='image %d'%i)
        images.append(volume)
    # if validation_file is not None:
    #     from ezra.image.nrrd_tools_old import load_volumes
    #     n, volumes = load_volumes(validation_file)
    return images

def _load_single_image(header, data, validation_file=None):
    """
    Creates a valid SimpleITK image using the metadata from the NRRD file.
    This effort is necessary since SimpleITK in its current version does not read
    correctly segmentation files from Slicer in the NRRD format.

    We have this problem trying to read NRRD files with multiple prostate lesions
    """

    # Get array data in sitk format [z,y,x]
    # -------------------------------------------------------------
    image = None

    # SimpleITK expects [z,y,x] but we read [x,y,z] with the nrrd library
    # So we need to change the indices like this: 2->z, 1->y, 0->x
    reversed_data = data.transpose(2,1,0)
    image = sitk.GetImageFromArray(reversed_data)

    # Check if we need to from_dicom_to_nrrd to RAS
    convert_to_ras = False
    if header[NRRD_SPACE] != NRRD_RAS_SPACE:
        convert_to_ras = True

    # Set Origin
    #-------------------------------------------------------------
    v_origin = num_from_str_vec(header[NRRD_SPACE_ORIGIN])

    if convert_to_ras:
        v_origin_h = np.append(v_origin,1)
        ras_origin_h = trx_lps_to_ras(v_origin_h)
        ras_origin = ras_origin_h[0:3]
        image.SetOrigin(ras_origin)
    else:
        image.SetOrigin(v_origin)

    # Set Spacing
    # -------------------------------------------------------------
    num_directions = len(header[NRRD_SPACE_DIRECTIONS])
    if num_directions != 3:
        raise AssertionError('We expect 3D images here!')
    dir1 = num_from_str_vec(header[NRRD_SPACE_DIRECTIONS][0])
    dir2 = num_from_str_vec(header[NRRD_SPACE_DIRECTIONS][1])
    dir3 = num_from_str_vec(header[NRRD_SPACE_DIRECTIONS][2])
    sp1 = np.linalg.norm(dir1)
    sp2 = np.linalg.norm(dir2)
    sp3 = np.linalg.norm(dir3)
    if sp1 == 0 or sp2 == 0 or sp3 == 0:
        raise AssertionError('Spacing cannot be zero')
    image.SetSpacing([sp1, sp2, sp3])

    # Set Directions
    # -------------------------------------------------------------
    ndir1 = dir1 / sp1
    ndir2 = dir2 / sp2
    ndir3 = dir3 / sp3
    # This step is required because in SimpleITK the directions are transposed (don't ask me why, I just
    # checked comparing the header from NRRD with the GetDirections method from the same image read with sitk
    matrix = np.matrix(np.vstack((ndir1, ndir2, ndir3)))

    if convert_to_ras:
        matrix2 =  np.mat(np.diag([-1, -1, 1])) * matrix # shouldn't we be left-multiplying here?
        ndir1 = np.squeeze(np.asarray(matrix2[:,0]))
        ndir2 = np.squeeze(np.asarray(matrix2[:,1]))
        ndir3 = np.squeeze(np.asarray(matrix2[:,2]))

    dir_vec = np.concatenate((ndir1, ndir2, ndir3))
    image.SetDirection(dir_vec)
    image.SetMetaData('NRRD_space',NRRD_RAS_SPACE)
    
    for key in header.keys():
        print key
    
    slicer_segmentations_metadata = header[u'keyvaluepairs']
    for item in slicer_segmentations_metadata:
        image.SetMetaData(item.encode('ascii','ignore'),
                          slicer_segmentations_metadata[item].encode('ascii','ignore'))

    # if validation_file is not None:
    #     im = sitk.ReadImage(validation_file) #only for validation that we are capturing what we need
    #     _info_image(image, title='Image built from data')
    #     _info_image(im, title='Image read with simpleitk')
    #     print 'meta %s'%im.GetMetaData('NRRD_space')

    return image

def _load(filename):
    try:
        data, header = nrrd.read(filename)
    except Exception as e:
        raise Exception('Could not read image file: %s'%(filename))

    # data could be multi-volume (for instance in a segmentation subject with multiple segments)
    image = None
    if header[u'dimension'] == 4:
        image =  _load_multi_image(header, data, validation_file=filename)
        return image
    else:
        image = _load_single_image(header, data, validation_file=filename)
        return [image]

def load_images(filename):
    """
    By default we assume the NRRD file is in left-posterior-superior format.
    If convert_to_ras is True, then the appropriate transformation is applied to from_dicom_to_nrrd to RAS.

    Thus, files generated by slicer should have convert_to_ras = False

    :param filename: the file to load
    :param convert_to_ras: flag to determine if the lps_to_ras transform should be applied
    :return: a list of images
    """
    images = _load(filename)
    #_info_image(image, title=os.path.basename(filename))
    return images
