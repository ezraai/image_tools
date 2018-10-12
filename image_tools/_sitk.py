import numpy as np
import SimpleITK as sitk

import _math as math
import _nrrd as nrrd_tools

SITK_NRRD_SPACE = 'NRRD_space'
SITK_LPS_SPACE ='left-posterior-superior'
SITK_RAS_SPACE ='right-anterior-superior'

def _trx_lps_to_ras(image):

    space = image.GetMetaData(SITK_NRRD_SPACE)
    if space == SITK_RAS_SPACE:
        return image
    elif space != SITK_LPS_SPACE:
        raise AssertionError('Unknown space: %s'%space)

    origin = image.GetOrigin()
    direction = image.GetDirection()

    # Set RAS origin
    origin_h = np.append(origin,1)
    ras_origin_h = math.trx_lps_to_ras(origin_h)
    image.SetOrigin(ras_origin_h[0:3])

    # Set RAS spacing
    matrix = np.matrix(np.vstack((direction[0:3],
                                  direction[3:6],
                                  direction[6:9])))

    matrix2 =  np.mat(np.diag([-1, -1, 1])) * matrix #left-multiplication for op composition

    ndir1 = np.squeeze(np.asarray(matrix2[:, 0]))
    ndir2 = np.squeeze(np.asarray(matrix2[:, 1]))
    ndir3 = np.squeeze(np.asarray(matrix2[:, 2]))

    dir_vec = np.concatenate((ndir1, ndir2, ndir3))
    image.SetDirection(dir_vec)
    image.SetMetaData(SITK_NRRD_SPACE,SITK_RAS_SPACE)

    return image



def load_image(filename):
    """
    Loads a single image from a file
    """
    #Cannot use the vtkNrrdReader because it does not support the gzip encoding.
    #So I am using simple itk
    image = sitk.ReadImage(filename)
    image = _trx_lps_to_ras(image)
    return image

def load_images(filename):
    """Returns a list of images contained in the same file (i.e. lesions)"""
    images = nrrd_tools.load_images(filename)
    return images


def get_lesion_names(images):
    """
    This function receives a list of images since reading lesions returns a list of images
    """
    im = images[0] #all lesions share the same metadata so we can select one
    num_lesions = len([key for key in im.GetMetaDataKeys() if key.startswith('Segment') and key.endswith('_ID')])
    names = []
    for i in range(num_lesions):
        names.append(im.GetMetaData('Segment%s_Name'%i))
    return names



def get_fg_size(image):
    size = image.GetSize()
    if size == (0,0,0):
        return 0
    arr = get_array_from(image)
    wh = np.where(arr>0)
    return np.array(wh).size

def get_fg_location(image):
    arr = get_array_from(image)
    wh = np.where(arr > 0)
    wh = np.array(wh)
    loc = np.average(wh, axis=1)
    return np.mean(wh, axis=1).take([1, 2, 0])



def info_image(image, title=None):

    size = image.GetSize()
    dimension = image.GetDimension()
    width = image.GetWidth()
    height = image.GetHeight()
    depth = image.GetDepth()
    origin = image.GetOrigin()
    direction = image.GetDirection()
    spacing = image.GetSpacing()

    try:
        mspace = image.GetMetaData(SITK_NRRD_SPACE)
    except:
        mspace = 'None'

    print
    print 'Image Details' if title is None else 'Image Details [%s]'%title
    print 'origin    :', origin
    print 'direction : ', direction
    print 'size      :', size
    print 'dimension :', dimension
    print 'width     :', width
    print 'height    :', height
    print 'depth     :', depth
    print 'spacing   :', spacing
    print 'm-space   :', mspace

def get_array_from(image):
    arr = sitk.GetArrayFromImage(image)
    if arr.ndim == 3:
        return arr
        #arr = arr.transpose(1, 2, 0)  # z y x ->  y x z
    elif arr.ndim == 4: #RGB volume
        return arr
        #arr = arr.transpose(1, 2, 0 , 3) # z,y,x,ch -> y,x,z,ch
    return arr

def get_arrays_from_list(images):
    arrays = []
    for i in images:
        arrays.append(get_array_from(i))
    return arrays

def _copy_metadata(reference=None, target=None):
    if reference is None or target is None:
        raise AssertionError('reference and target are required')

    metadata = reference.GetMetaDataKeys()
    for key in metadata:
        target.SetMetaData(key, reference.GetMetaData(key))

def resample_linear(reference=None, target=None):
    if reference is None or target is None:
        raise AssertionError('reference and target are required')

    r = sitk.ResampleImageFilter()
    r.SetReferenceImage(reference)
    r.SetInterpolator(sitk.sitkLinear)
    resampled = r.Execute(target)
    return resampled

def resample_nearest(reference=None, target=None):
    if reference is None or target is None: return
    r = sitk.ResampleImageFilter()
    r.SetReferenceImage(reference)
    r.SetInterpolator(sitk.sitkNearestNeighbor)
    resampled = r.Execute(target)
    return resampled

def resample_and_crop(reference=None, target=None):

    if reference is None or target is None:
        return

    # generate white image
    pixel_type = reference.GetPixelIDValue()
    empty_array = sitk.GetArrayFromImage(target)
    empty_array.fill(1)
    blank_image = sitk.GetImageFromArray(empty_array)
    blank_image.CopyInformation(target)

    # get bounding box
    r_1 = sitk.ResampleImageFilter()
    r_1.SetReferenceImage(reference)
    r_1.SetInterpolator(sitk.sitkNearestNeighbor) # interpolator for detecting boundaries
    r_1.SetDefaultPixelValue(0)
    r_blank = r_1.Execute(blank_image)
    arr = sitk.GetArrayFromImage(r_blank)
    locations = np.array(np.where(arr==1))
    min_l = locations[:,0][::-1]  # remember coords come as [z, y, x] we reverse to [x, y, z] with ::-1
    max_l = locations[:,-1][::-1]
    #print 'Bounds for resampling'
    #print min_l, max_l


    # resample target to reference
    r_2 = sitk.ResampleImageFilter()
    r_2.SetReferenceImage(reference)
    r_2.SetInterpolator(sitk.sitkLinear)
    resampled = r_1.Execute(target)

    # crop according to bounding box
    cropper = sitk.CropImageFilter()
    cropper.SetLowerBoundaryCropSize(min_l)
    cropper.SetUpperBoundaryCropSize(resampled.GetSize()-max_l-1)
    out_image = cropper.Execute(resampled)

    #cast type as input image:
    out_image = sitk.Cast(out_image, pixel_type)

    #info_image(resampled, title='input')
    #info_image(out_image, title='output')

    return out_image

def compose_image(image_list):
    """Creates a multi-channel image"""
    if len(image_list) == 1: # do not compose if there is only one image
        raise AssertionError('Need at least two')
    filter = sitk.ComposeImageFilter()
    return filter.Execute(image_list)


def label_image_from_list(label_images, reference=None):
    """
    Combines labels from multiple images and generates one image
    with the dimensions of the reference image.

    This is useful to aggregate all the lesion segmentations into a volume
    with the same dimensions as the reference image (T2W image)

    """
    N = len(label_images)
    if N == 0:
        raise AssertionError('A list of label images is required')

    r_temp = []
    for image in label_images:
        r_image = resample_nearest(reference=reference, target=image)
        r_temp.append(r_image)

    label_image = label_image_to_binary_image(union_images(r_temp))
    return label_image


def union_images(image_list):
    """
    Adds a list of images with the same dimensions
    """
    arr_union = None
    for image in image_list:
        if arr_union is None:
            arr_union = sitk.GetArrayFromImage(image)
        else:
            arr_union += sitk.GetArrayFromImage(image)
    ima_union = sitk.GetImageFromArray(arr_union)
    return ima_union

def label_image_to_binary_image(image):
    """
    Returns a label image that is binary
    """
    arr = sitk.GetArrayFromImage(image)
    arr[list(np.where(arr > 0))] = 1
    ima_result = sitk.GetImageFromArray(arr)
    return ima_result
