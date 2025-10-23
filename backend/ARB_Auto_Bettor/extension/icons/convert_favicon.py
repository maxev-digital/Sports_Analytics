"""
Convert favicon.ico to PNG icons at multiple sizes for Chrome extension
"""
try:
    from PIL import Image
    import os

    # Open the favicon
    favicon_path = os.path.join(os.path.dirname(__file__), 'favicon.ico')
    icon = Image.open(favicon_path)

    # Sizes needed for Chrome extension
    sizes = [16, 32, 48, 128]

    print(f'Converting favicon.ico to PNG icons...')

    for size in sizes:
        # Resize and save
        resized = icon.resize((size, size), Image.Resampling.LANCZOS)

        # Convert to RGBA if needed
        if resized.mode != 'RGBA':
            resized = resized.convert('RGBA')

        output_path = os.path.join(os.path.dirname(__file__), f'icon{size}.png')
        resized.save(output_path, 'PNG')
        print(f'Created icon{size}.png')

    print('\nAll PNG icons created successfully from favicon!')
    print('Icons are now using your Max EV Sports branding.')

except ImportError:
    print('PIL (Pillow) not installed. Installing...')
    import subprocess
    subprocess.run(['pip', 'install', 'pillow'])
    print('Please run this script again.')
except Exception as e:
    print(f'Error: {e}')
