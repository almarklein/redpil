import numpy as np

header_t = np.dtype([
    ('signature', '|S2'),
    ('filesize', '<u4'),
    ('reserved1', '<u2'),
    ('reserved2', '<u2'),
    ('file_offset_to_pixelarray', '<u4')
])

info_header_t = np.dtype([
    ('header_size', '<u4'),
    ('image_width', '<u4'),
    ('image_height', '<u4'),
    ('image_planes', '<u2'),
    ('bits_per_pixel', '<u2'),
    ('compression', '<u4'),
    ('image_size', '<u4'),
    ('x_pixels_per_meter', '<u4'),
    ('y_pixels_per_meter', '<u4'),
    ('colors_in_color_table', '<u4'),
    ('important_color_count', '<u4'),
])

compression_types = ['BI_RGB', 'BI_RLE8', 'BI_RLE4', 'BI_BITFIELDS', 'BI_JPEG',
                     'BI_PNG', 'BI_ALPHABITFIELDS', 'BI_CMYK', 'BI_CMYKRLE8'
                     'BI_CMYKRLE4']

gray_color_table = np.arange(256, dtype='<u1')
gray_color_table = np.stack([gray_color_table,
                             gray_color_table,
                             gray_color_table,
                             np.full_like(gray_color_table,
                                          fill_value=255)], axis=1)

def imwrite(filename, image):
    image = np.atleast_2d(image)
    if image.ndim > 2:
        raise NotImplementedError('Only monochrome images are supported.')

    if image.dtype != np.uint8:
        raise NotImplementedError('Only uint8 images are supported.')

    with open(filename, 'bw+') as f:
        offset = 0
        header = np.memmap(f, dtype=header_t, mode='w+', shape=1,
                           offset=offset)
        offset += header.nbytes

        info_header = np.memmap(f, dtype=info_header_t, mode='w+', shape=1,
                                offset=offset)
        offset += info_header.nbytes

        color_table = np.memmap(f, dtype=gray_color_table.dtype, mode='w+',
                                shape=gray_color_table.shape, offset=offset)
        offset += color_table.nbytes

        header['signature'] = 'BM'.encode()

        bits_per_pixel = image.itemsize * 8
        # Not correct for color images
        # BMP wants images to be padded to a multiple of 4
        row_size = (bits_per_pixel * image.shape[1] + 31) // 32
        image_size = row_size * image.shape[0]

        data = np.memmap(f, dtype=np.uint8, mode='w+',
                         shape=(image.shape[0], row_size * 4), offset=offset)
        offset += data.nbytes

        # Now slice just the part of the image that we actually write to.
        data = data[:image.shape[0], :image.shape[1]]

        header['file_offset_to_pixelarray'] = (header.nbytes +
                                               info_header.nbytes +
                                               color_table.nbytes)

        header['filesize'] = (header['file_offset_to_pixelarray'] + image_size)

        info_header['header_size'] = info_header.nbytes
        info_header['image_width'] = image.shape[1]
        # A positive height states the the array is saved "bottom to top"
        # A negative height states that the array is saved "top to bottom"
        # Top to bottom has a larger chance of being contiguous in C memory
        info_header['image_height'] = -image.shape[0]
        info_header['image_planes'] = 1
        info_header['bits_per_pixel'] = bits_per_pixel
        info_header['compression'] = compression_types.index('BI_RGB')
        info_header['image_size'] = 0
        info_header['x_pixels_per_meter'] = 0
        info_header['y_pixels_per_meter'] = 0
        info_header['colors_in_color_table'] = 0
        info_header['important_color_count'] = 0

        color_table[...] = gray_color_table
        data[...] = image
