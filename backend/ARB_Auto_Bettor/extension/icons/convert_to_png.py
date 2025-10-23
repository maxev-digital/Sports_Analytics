"""
Convert SVG icon to PNG at multiple sizes
"""
try:
    from PIL import Image, ImageDraw
    import os

    # Create the icon programmatically
    sizes = [16, 32, 48, 128]

    for size in sizes:
        # Create a new image with white background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Calculate dimensions based on size
        center = size // 2
        radius = int(size * 0.47)  # 60/128 = 0.47
        stroke_width = max(1, int(size * 0.03))  # 4/128 = 0.03

        # Draw white circle with blue border
        draw.ellipse(
            [(center - radius, center - radius),
             (center + radius, center + radius)],
            fill='white',
            outline='#3b82f6',
            width=stroke_width
        )

        # Draw lightning bolt (scaled)
        scale = size / 128.0
        points = [
            (int(75 * scale), int(28 * scale)),   # Top
            (int(45 * scale), int(64 * scale)),   # Left middle
            (int(60 * scale), int(64 * scale)),   # Middle
            (int(53 * scale), int(100 * scale)),  # Bottom
            (int(83 * scale), int(64 * scale)),   # Right middle
            (int(68 * scale), int(64 * scale))    # Middle
        ]

        draw.polygon(points, fill='#3b82f6', outline='#2563eb')

        # Save PNG
        output_path = os.path.join(os.path.dirname(__file__), f'icon{size}.png')
        img.save(output_path, 'PNG')
        print(f'Created {output_path}')

    print('\nAll PNG icons created successfully!')
    print('Now update manifest.json to use .png files instead of .svg')

except ImportError:
    print('PIL (Pillow) not installed. Installing...')
    import subprocess
    subprocess.run(['pip', 'install', 'pillow'])
    print('Please run this script again.')
