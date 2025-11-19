from PIL import Image
import os

path = './utils/documents/filmposter.jpg'

print("Exists:", os.path.exists(path))
print("Size:", os.path.getsize(path))

try:
    img = Image.open(path)
    print("Image:", img.size, img.mode, img.format)
except Exception as e:
    print("Image error:", e)
