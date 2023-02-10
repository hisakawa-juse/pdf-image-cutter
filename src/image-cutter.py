import sys
import os
import itertools
import fitz


class ImageCutter:
    """PDFからイメージを取り出す
    """
    def __init__(self, args):
        assert len(args) > 0
        self.__filename = args[0]
        self.__dirname = self.__filename.split('.')[0]
        if not os.path.isdir(self.__dirname):
            os.mkdir(self.__dirname)
        self.__pngs = None
        self.__jpegs = None
        self.__tiffs = None

    def read(self):
        self.__doc = fitz.open(self.__filename)
        images = map(lambda page: self.__doc[page].get_images(),
                     range(len(self.__doc)))
        chain_images = itertools.chain(*images)
        pngs, jpegs, tiffs = itertools.tee(enumerate(chain_images), 3)
        pngs = filter(lambda e: e[1][8] == 'FlateDecode', pngs)
        jpegs = filter(lambda e: e[1][8] == 'DCTDecode', jpegs)
        tiffs = filter(lambda e: e[1][8] == 'CCITTFaxDecode', tiffs)
        self.__pngs = self.__make_png(pngs)
        self.__jpegs = self.__make_jpegs(jpegs)
        self.__tiffs = self.__make_tiffs(tiffs)

    def __make_png(self, pngs):
        png_sets = itertools.tee(pngs, 2)
        png_ids = map(lambda e: e[0], png_sets[0])
        pngs_images = map(lambda e: e[1], png_sets[1])
        pngs_images = map(lambda e: fitz.Pixmap(self.__doc.extract_image(e[0])['image']),
                          pngs_images)
        return zip(png_ids, pngs_images)

    def __make_jpegs(self, jpegs):
        jpeg_masks, jpeg_nomasks = itertools.tee(jpegs, 2)
        jpeg_nomasks = filter(lambda e: e[1][1] <= 0, jpeg_nomasks)
        jpeg_nomask_sets = itertools.tee(jpeg_nomasks, 2)
        jpeg_nomask_ids = map(lambda e: e[0], jpeg_nomask_sets[0])
        jpeg_nomask_images = map(lambda e: e[1][0], jpeg_nomask_sets[1])
        jpeg_nomask_images = map(lambda e: fitz.Pixmap(self.__doc.extract_image(e)['image']),
                                 jpeg_nomask_images)
        jpeg_nomasks = zip(jpeg_nomask_ids, jpeg_nomask_images)

        jpeg_masks = filter(lambda e: e[1][1] > 0, jpeg_masks)
        jpeg_mask_sets = itertools.tee(jpeg_masks, 3)
        jpeg_mask_ids = map(lambda e: e[0], jpeg_mask_sets[0])
        jpeg_mask_images = map(lambda e: e[1][0], jpeg_mask_sets[1])
        jpeg_mask_masks = map(lambda e: e[1][1], jpeg_mask_sets[2])
        jpeg_mask_images = map(lambda e: fitz.Pixmap(self.__doc.extract_image(e)['image']),
                               jpeg_mask_images)
        jpeg_mask_masks = map(lambda e: fitz.Pixmap(self.__doc.extract_image(e)['image']),
                              jpeg_mask_masks)
        jpeg_mask_images = map(lambda e: fitz.Pixmap(e, 0), jpeg_mask_images)
        jpeg_mask_images = map(lambda e: fitz.Pixmap(*e), zip(jpeg_mask_images, jpeg_mask_masks))
        jpeg_masks = zip(jpeg_mask_ids, jpeg_mask_images)
        return itertools.chain(jpeg_masks, jpeg_nomasks)

    def __make_tiffs(self, tiffs):
        tiff_sets = itertools.tee(tiffs, 2)
        tiff_ids = map(lambda e: e[0], tiff_sets[0])
        tiff_images = map(lambda e: e[1], tiff_sets[1])
        tiff_images = map(lambda e: fitz.Pixmap(self.__doc.extract_image(e[0])['image']), tiff_images)
        return zip(tiff_ids, tiff_images)

    def write(self):
        for idx, image in self.__pngs:
            image_file = f'{self.__dirname}/image_{idx}.png'
            image.save(image_file)
        for idx, image in self.__jpegs:
            image_file = f'{self.__dirname}/image_{idx}.jpeg'
            image.save(image_file)
        for idx, image in self.__tiffs:
            image_file = f'{self.__dirname}/image_{idx}.tiff'
            image.save(image_file)


if __name__ == '__main__':
    image_cutter = ImageCutter(sys.argv[1:])
    image_cutter.read()
    image_cutter.write()

