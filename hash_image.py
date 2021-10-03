from PIL import Image
from config import astolfo_source, astolfnt_source
import os


filename_to_hash = {}
hash_is_astolfo = {}


def hash_image(img: Image)-> str:
    img = img.resize((10, 10), Image.ANTIALIAS)
    img = img.convert("L")
    pixel_data = list(img.getdata())
    avg_pixel = sum(pixel_data)/len(pixel_data)
    bits = "".join(['1' if (px>= avg_pixel) else '0' for px in pixel_data])
    hex_representation = str(hex(int(bits, 2)))[2:][::-1].upper()
    return hex_representation


for file in os.listdir(astolfo_source):
    filename = os.path.join(astolfo_source, file)
    hash = hash_image(Image.open(filename))
    filename_to_hash[filename] = hash
    hash_is_astolfo[hash] = True

for file in os.listdir(astolfnt_source):
    filename = os.path.join(astolfnt_source, file)
    hash = hash_image(Image.open(filename))
    filename_to_hash[filename] = hash
    hash_is_astolfo[hash] = False
