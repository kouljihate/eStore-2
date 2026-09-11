import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


def make_icon(path):
    size = 400
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=90,
                        fill=(0, 137, 123, 255))
    # shopping bag body
    d.rounded_rectangle([110, 150, 290, 320], radius=26,
                        fill=(255, 255, 255, 255))
    # handle
    d.arc([140, 90, 260, 190], start=200, end=340, fill=(255, 255, 255, 255),
          width=24)
    img.save(path)


def make_loading(path):
    frames = []
    n = 12
    for i in range(n):
        frame = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        color = (0, 137, 123, 255)
        d.arc([15, 15, 105, 105], start=i * 30, end=i * 30 + 200,
              width=10, fill=color)
        frames.append(frame)
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=60, loop=0)


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    make_icon(os.path.join(ASSETS, "eshop_icon.png"))
    make_loading(os.path.join(ASSETS, "loading.gif"))
    print("assets generated")