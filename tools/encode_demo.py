"""Optional asset tool: requires Pillow, not needed to run the simulator."""

import argparse
from pathlib import Path
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, default=Path("runs/demo-frames"))
    parser.add_argument("--output", type=Path, default=Path("docs/assets/demo.gif"))
    args = parser.parse_args()
    frames = []
    for path in sorted(args.frames.glob("frame-*.png")):
        with Image.open(path) as image:
            frames.append(image.convert("RGB").quantize(colors=128))
    if not frames:
        parser.error("No rendered frames found. Run tools/render_demo.py first.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(args.output, save_all=True, append_images=frames[1:],
                   duration=125, loop=0, optimize=True, disposal=2)
    print(f"Saved {args.output} ({args.output.stat().st_size / 1_000_000:.2f} MB)")


if __name__ == "__main__":
    main()
