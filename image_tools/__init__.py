import _sitk


def load_image(image):
  return _sitk.get_array_from(_sitk.load_image(image))

