# Author:Kenghagho Kenfack, Franklin
# Copyrights 2022, AINHSA


# Loading the libraries

import cv2
from PIL import Image, ImageFilter
import sys
import glob
import numpy as np
import time
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_diff_matrix import delta_e_cie2000 as fast_delta_e_cie2000
from skimage import io, color
import colorsys


# dv.qualia_v2(self,imgp, steps=1, ks=5, filter=['Blue','Black','White','Orange' ], file=True, bckg='Gray', rdim=(80,80), mSize=(5,5))


class BildProjektion():

    def __init__(self):
        pass

    def project(self, image):
        return (color.rgb2lab(image))


class BildEntrauschung():
    def __init__(self):
        pass
        self.ks = (3, 3)

    def setFilter(self, size):
        self.ks = size

    def denoise(self, image):
        pil_image = Image.fromarray(image)
        return {"mean": cv2.blur(image, self.ks),
                "median": cv2.medianBlur(image, self.ks[0]),
                "gaussian": cv2.GaussianBlur(image, self.ks, cv2.BORDER_DEFAULT),
                "mode": cv2.cvtColor(np.asarray(pil_image.filter(ImageFilter.ModeFilter(size=self.ks[0]))),
                                     cv2.COLOR_RGB2BGR)
                }


class Kamera():
    def __init__(self):
        self.cameraId = 0
        self.cameraFrequency = 10
        self.camera = None

    def start(self):
        self.camera = cv2.VideoCapture(self.cameraId)

    def release(self):
        self.camera.release()

    def read(self):
        return self.camera.read()

    def setCameraId(self, cameraId):
        self.cameraId = cameraId

    def setCameraFrequency(self, cameraFrequency):
        self.cameraFrequency = cameraFrequency


class BildVerarbeitung():

    def __init__(self):

        # BildEntrauschung
        self.denoiser = BildEntrauschung()
        # BildProjektion
        self.projector = BildProjektion()
        # Map of color name-code
        """
		{"Black":[0,0,0], "White":[255,255,255], "Red":[255,0,0], "Cyan":[0,255,255], "Magenta":[255,0,255], "Silver":[192,192,192], "Maroon":[128,0,0], "Olive":[128,128,0], "Green1":[0,128,0], "Purple":[128,0,128], "Teal":[0,128,128], "Navy":[0,0,128],"Orange":[255,168,0],"Orange1":[255,69,0],"Orange2":[255,140,0],"Violet":[155,38,182], "Green2":[0,255,0], "Blue":[0,0,255], "Yellow":[255,255,0], "Gray":[128,128,128]}
		"""
        self.MapQualiaToPixel = {"Orange": [255, 168, 0], "Black": [0, 0, 0], "Brown": [119, 90, 48],
                                 "Silver": [100, 100, 100], "White": [255, 255, 255], "Red": [255, 0, 0],
                                 "Green": [0, 255, 0], "Blue": [0, 0, 255], "Yellow": [255, 255, 0]}
        # convert colors from rgb to cie2000 lab space
        self.MapQualiaToPixel1 = {}
        self.MapQualiaToPixel_KEYS = []
        # background color
        self.WildCardQualia = 'white'
        for q in self.MapQualiaToPixel.keys():
            # Target Color
            self.MapQualiaToPixel_KEYS.append(q)
            color_rgb = (self.MapQualiaToPixel[q][0], self.MapQualiaToPixel[q][1], self.MapQualiaToPixel[q][2])
            # Convert from RGB to Lab Color Space
            # self.MapQualiaToPixel1[q] = convert_color(color2_rgb, LabColor).get_value_tuple()
            self.MapQualiaToPixel1[q] = self.getColorDL(color_rgb)

    def getQualiaHistogram(self, imgp, bbox, filter=[]):
        x, y, w, h = bbox
        img = cv2.cvtColor(cv2.imread(imgp), cv2.COLOR_BGR2RGB)
        dico = {}
        for color in filter:
            dico[color] = 0
        for i in range(y, y + h):
            for j in range(x, x + w):
                q = self.getQualia(list(img[i, j]))
                if q in filter:
                    dico[q] += 1
        return dico

    def getColorDL(self, color, min_value=30, max_value=240):
        r = float(color[0]) / 255.
        g = float(color[1]) / 255.
        b = float(color[2]) / 255.
        if self.getLightness(np.max(color)) == 0.0:
            return (0.0, 0.0, 0.0, 0.0)
        else:
            if self.getLightness(np.min(color)) == 1.0:
                return (0.0, 0.0, 0.0, 1.0)
            else:
                return (r - g, r - b, g - b, (r + b + g) / 3)

    def getLightness(self, lightness, min_value=30, max_value=240):
        if lightness > max_value:
            return 1.0
        else:
            if lightness < min_value:
                return 0.0
            else:
                return float(lightness) / 255.

    def getColorDelta(self, c1, c2):
        if c1 == (0.0, 0.0, 0.0, 0.0) and c2 == (0.0, 0.0, 0.0, 0.0):
            return (1.0, 0.0)
        else:
            if c1 == (0.0, 0.0, 0.0, 0.0) or c2 == (0.0, 0.0, 0.0, 0.0):
                return (+np.inf, +np.inf)
        cosinus = np.round(np.dot(c1, c2) / (np.linalg.norm(c1) * np.linalg.norm(c2)))
        return (cosinus, np.arccos(cosinus) + np.abs(c1[3] - c2[3]))

    # extract essential color from an image: Extrem fast sequential computation

    def getQualia(self, pixel):
        qualia = None
        for key in self.MapQualiaToPixel.keys():
            if pixel == self.MapQualiaToPixel[key]:
                qualia = key
                break
        return qualia

    def extract_figure_v1(self, imgp, imgp2, min_y=200, max_y=350, min_x=300, max_x=400, min_size=20, threshold=10, max_value=255, type=0, result=[], gt={}, names=[]):
        t = time.time()
        img = cv2.cvtColor(imgp, cv2.COLOR_BGR2GRAY)
        img1 = imgp2.copy()
        ret, thresh = cv2.threshold(img, threshold, max_value, type)
        contours, hierarchy = cv2.findContours(thresh, 1,cv2.CHAIN_APPROX_SIMPLE)

        for i in range(len(result)):
            rect=result[i]
            x1, y1, x2, y2 = rect
            cv2.rectangle(img1, (x1, y1), (x2, y2), (0, 255, 0), 2)
            font = cv2.FONT_HERSHEY_SIMPLEX
            # org
            org = (x1, y1)
            # fontScale
            fontScale = 0.6
            # Blue color in BGR
            color = (255,0,0)
            # Line thickness
            thickness = 1
            area = (x2 - x1) * (y2 - y1)
            if i<len(names):
                img1 = cv2.putText(img1, str(names[i]), org, font, fontScale,
                                   color, thickness, cv2.LINE_AA)


        for obj in gt.keys():
            print('*******************************************************************************************************',gt)
            x1, y1, x2, y2 = list(gt[obj]['bbox'])
            cv2.rectangle(img1, (x1, y1), (x2, y2), gt[obj]['color_font'], 2)
            font = cv2.FONT_HERSHEY_SIMPLEX
            # org
            org = (x1, y1)
            # fontScale
            fontScale = 0.6
            # Blue color in BGR
            color = gt[obj]['color_font']
            # Line thickness
            thickness = 1
            area=(x2-x1)*(y2-y1)
            img1 = cv2.putText(img1,  str(gt[obj]['name']) , org, font, fontScale,
                               color, thickness, cv2.LINE_AA)

        """
        for cnt in contours:
            M = cv2.moments(cnt)
            if M["m00"] != 0:

                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                area = int(cv2.contourArea(cnt))
                perimeter = int(cv2.arcLength(cnt, True))
                x, y, w, h = cv2.boundingRect(cnt)
                if w > min_size and h > min_size and y > min_y and y<max_y and x > min_x and x<max_x:
                    print("figure found!!!")
                    print(x, y, w, h)
                    cv2.rectangle(img1, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    # font
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    # org
                    org = (x, y)
                    # fontScale
                    fontScale = 1
                    # Blue color in BGR
                    color = (0, 0, 255)
                    # Line thickness
                    thickness = 2
                    img1 = cv2.putText(img1, str('A=') + str(area) + ' - P=' + str(perimeter), org, font, fontScale,
                                       color, thickness, cv2.LINE_AA)
        """
        #cv2.drawContours(img1, contours, -1, (255, 0, 0), 2)
        #cv2.imwrite('RESULT_CONTOUR' + str(t) + '.png', img1)
        return img1


    def figure_v1(self, imgp, T_lower=0, T_upper=255, aperture_size=3, steps=1, L2Gradient=0.):
        img =imgp.copy()
        for i in range(steps):
            t = time.time()
            img = cv2.Canny(img, T_lower, T_upper, apertureSize=aperture_size)
            img = cv2.merge([img, img, img])
            #cv2.imwrite('RESULT_EDGE' + str(t) + '.png', img)
        return img

    def filtering_V1(self, imgp, steps=1, ks=5, filter=[], file=False, bckg='White', rdim=(10, 10), mSize=(5, 5)):
        # compute the color map of the input image
        qualia_color_image = self.qualia_v2(imgp, steps=steps, ks=ks, filter=filter, file=file, bckg=bckg, rdim=rdim,
                                            mSize=mSize)
        return qualia_color_image

    def faster_delta_e_cie2000(self, color, list_color):
        # ignore the lightness component
        result = np.zeros((list_color.shape[0]), dtype='float')
        for i in range(list_color.shape[0]):
            result[i] = self.getColorDelta(color, self.getColorDL(tuple(list_color[i])))[1]
        return result

    def qualia_v2(self, imgp, steps=1, ks=5, filter=[], file=False, bckg='White', rdim=(10, 10), mSize=(5, 5)):
        self.WildCardQualia = bckg
        t = int(time.time())
        # read image
        if file:
            img = io.imread(imgp)[:, :, :3]
        else:
            img = imgp.copy()
            b = img[:, :, 0].copy()
            img[:, :, 0] = img[:, :, 2].copy()
            img[:, :, 2] = b.copy()
        Orows, Ocols, Odims = img.shape
        assert ((Orows % rdim[0] == 0) and (Ocols % rdim[1] == 0))

        img = cv2.resize(img, (Ocols // rdim[0], Orows // rdim[1]), interpolation=cv2.INTER_CUBIC)
        for l in range(steps):
            if ks > 0:
                self.denoiser.setFilter((ks, ks))
                list_of_images = self.denoiser.denoise(img)
            else:
                list_of_images = {"mean": img}
            for key in list_of_images.keys():
                # convert image
                img = list_of_images[key]
                # img=self.projector.project(img)
                rows, cols, dims = img.shape
                results = []
                # array flattening
                img = img.reshape([rows * cols, dims])
                # concatenate the results

                for q in self.MapQualiaToPixel_KEYS:
                    results.append(self.faster_delta_e_cie2000(self.MapQualiaToPixel1[q], img).reshape([rows, cols]))
                results = np.stack(results, axis=2)

                img = np.zeros([rows, cols, 3], dtype='uint8')
                for i in range(rows):
                    for j in range(cols):

                        qualia = self.MapQualiaToPixel_KEYS[np.argmin(results[i, j, :])]
                        found = False
                        if qualia not in filter:
                            for f in filter:
                                if f in qualia:
                                    found = True
                                    qualia = f
                                    break
                            if not found:
                                qualia = self.WildCardQualia
                        img[i][j] = self.MapQualiaToPixel[qualia]
                b = img[:, :, 0].copy()
                img[:, :, 0] = img[:, :, 2].copy()
                img[:, :, 2] = b.copy()
                img1 = np.zeros([Orows, Ocols, 3], dtype='uint8')
                for r in range(rows):
                    for c in range(cols):
                        img1[r * rdim[1]:(r + 1) * rdim[1], c * rdim[0]:(c + 1) * rdim[0], :] = img[r, c]

                # img = cv2.resize(img, (Ocols,Orows), fx=0,fy=0,interpolation = cv2.INTER_NEAREST)
                cv2.imwrite('RESULT_QUALIA_' + str(l) + str(t) + str(key) + '.png', img1)
        return img1

    def qualia_v1(self, imgp, steps=1, ks=5, filter=[], file=False, bckg='White', rdim=(80, 80), mSize=(5, 5)):
        self.WildCardQualia = bckg
        # read image
        if file:
            img = io.imread(imgp)[:, :, :3]
        else:
            img = imgp.copy()
            b = img[:, :, 0].copy()
            img[:, :, 0] = img[:, :, 2].copy()
            img[:, :, 2] = b.copy()
        Orows, Ocols, Odims = img.shape
        img = cv2.resize(img, rdim, interpolation=cv2.INTER_CUBIC)
        for l in range(steps):
            if ks > 0:
                self.denoiser.setFilter((ks, ks))
                img = self.denoiser.denoise(img)
            # convert image
            img = self.projector.project(img)
            rows, cols, dims = img.shape
            results = []
            # array flattening
            img = img.reshape([rows * cols, dims])
            # concatenate the results

            for q in self.MapQualiaToPixel_KEYS:
                results.append(fast_delta_e_cie2000(self.MapQualiaToPixel1[q], img).reshape([rows, cols]))
            results = np.stack(results, axis=2)

            img = np.zeros([rows, cols, 3], dtype='uint8')
            # mSize=(mSize[0]+1,mSize[1]+2)
            led_matrix = np.full(mSize, bckg, dtype='U100', order='C')
            matrix = np.full(rdim, bckg, dtype='U100', order='C')
            for i in range(rows):
                for j in range(cols):

                    qualia = self.MapQualiaToPixel_KEYS[np.argmin(results[i, j, :])]
                    found = False
                    if qualia not in filter:
                        for f in filter:
                            if f in qualia:
                                found = True
                                qualia = f
                                break
                        if not found:
                            qualia = self.WildCardQualia
                    img[i][j] = self.MapQualiaToPixel[qualia]
                    matrix[i][j] = qualia

            # Extracting the led from the image
            cs = cols / mSize[1]
            rs = rows / mSize[0]

            for i in range(mSize[0]):
                for j in range(mSize[1]):
                    cdict = {}
                    for qualia in filter:
                        cdict[qualia] = 0
                    cdict[bckg] = 0
                    for idx in range(i * rs, (i + 1) * rs):
                        for jdx in range(j * cs, (j + 1) * cs):
                            cdict[matrix[idx, jdx]] += 1
                    cdict[bckg] = 0
                    kay = max(cdict, key=cdict.get)
                    if kay != bckg and cdict[kay] > 0:
                        led_matrix[i, j] = kay
                    else:
                        led_matrix[i, j] = bckg
            b = img[:, :, 0].copy()
            img[:, :, 0] = img[:, :, 2].copy()
            img[:, :, 2] = b.copy()
            # cv2.imwrite('RESULT'+str(l)+'.png',img)
            print('Done with step: ' + str(l))
            b = img[:, :, 0].copy()
            img[:, :, 0] = img[:, :, 2].copy()
            img[:, :, 2] = b.copy()

        b = img[:, :, 0].copy()
        img[:, :, 0] = img[:, :, 2].copy()
        img[:, :, 2] = b.copy()
        img = cv2.resize(img, (Ocols, Orows), interpolation=cv2.INTER_CUBIC)
        return img, led_matrix


bildVerarbeitung=BildVerarbeitung()
print('Reading input image ...')
img=cv2.imread('test2.png')
img=bildVerarbeitung.filtering_V1( 'test6.png', steps=1, ks=1, filter=['White', 'Blue', 'Red', 'Yellow', 'Green', 'Black'], file=True, bckg='Silver', rdim=(1, 1), mSize=(5, 5))
b = img[:, :, 0].copy()
img[:, :, 0] = img[:, :, 2].copy()
img[:, :, 2] = b.copy()
cv2.imwrite('processed_test.png',img)
print("Processing of Image completed!!!")