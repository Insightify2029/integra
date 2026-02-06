"""
INTEGRA - Professional Desktop Shortcut Creator
يولّد أيقونة احترافية + shortcut على Desktop
"""

import os
import sys

# === Step 1: Generate Professional Icon ===
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont


def create_icon(output_path):
    """Create professional INTEGRA icon"""
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background: rounded square with gradient effect
    # Dark blue base
    bg_color = (15, 32, 65)       # Deep navy
    accent_color = (0, 150, 255)   # Bright blue
    white = (255, 255, 255)

    # Draw rounded rectangle background
    radius = 50
    # Main background
    draw.rounded_rectangle(
        [(8, 8), (size - 8, size - 8)],
        radius=radius,
        fill=bg_color
    )

    # Accent border
    draw.rounded_rectangle(
        [(8, 8), (size - 8, size - 8)],
        radius=radius,
        outline=accent_color,
        width=4
    )

    # Top accent line
    draw.rounded_rectangle(
        [(8, 8), (size - 8, 60)],
        radius=radius,
        fill=accent_color
    )
    # Fix bottom of accent area
    draw.rectangle(
        [(8, 40), (size - 8, 60)],
        fill=accent_color
    )

    # Letter "I" - bold and centered
    try:
        # Try system fonts
        font_paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        font_large = None
        font_small = None
        for fp in font_paths:
            if os.path.exists(fp):
                font_large = ImageFont.truetype(fp, 130)
                font_small = ImageFont.truetype(fp, 28)
                break
        if font_large is None:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw "I" letter
    bbox = draw.textbbox((0, 0), "I", font=font_large)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = ((size - text_h) // 2) + 10
    draw.text((x, y), "I", fill=white, font=font_large)

    # Draw "INTEGRA" text at top accent bar
    bbox2 = draw.textbbox((0, 0), "INTEGRA", font=font_small)
    tw = bbox2[2] - bbox2[0]
    tx = (size - tw) // 2
    draw.text((tx, 15), "INTEGRA", fill=white, font=font_small)

    # Small decorative dots at bottom
    dot_y = size - 35
    dot_colors = [(0, 150, 255), (0, 200, 150), (255, 180, 0), (0, 150, 255)]
    dot_start = (size - (len(dot_colors) * 20)) // 2
    for i, color in enumerate(dot_colors):
        cx = dot_start + (i * 20) + 8
        draw.ellipse([(cx, dot_y), (cx + 10, dot_y + 10)], fill=color)

    # Save as ICO with multiple sizes
    icon_sizes = []
    for s in [16, 24, 32, 48, 64, 128, 256]:
        resized = img.resize((s, s), Image.LANCZOS)
        icon_sizes.append(resized)

    icon_sizes[0].save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in [16, 24, 32, 48, 64, 128, 256]],
        append_images=icon_sizes[1:]
    )
    print(f"✅ Icon created: {output_path}")
    return True


def create_shortcut(target_dir, icon_path):
    """Create Desktop shortcut using pywin32"""
    try:
        import win32com.client
    except ImportError:
        print("❌ pywin32 not found!")
        return False

    # Get Desktop path
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    shortcut_path = os.path.join(desktop, 'INTEGRA.lnk')

    # Find pythonw.exe (runs without CMD window)
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, 'pythonw.exe')
    if not os.path.exists(pythonw):
        pythonw = sys.executable  # fallback to python.exe

    # Create shortcut
    shell = win32com.client.Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = pythonw
    shortcut.Arguments = 'main.py'
    shortcut.WorkingDirectory = target_dir
    shortcut.IconLocation = icon_path
    shortcut.Description = 'INTEGRA - Integrated Management System'
    shortcut.save()
    print(f"✅ Shortcut created: {shortcut_path}")
    return True


def main():
    # Project directory
    project_dir = r"D:\Projects\Integra"
    resources_dir = os.path.join(project_dir, "resources", "icons")

    # Create resources/icons if not exists
    os.makedirs(resources_dir, exist_ok=True)

    icon_path = os.path.join(resources_dir, "integra.ico")

    print("=" * 50)
    print("  INTEGRA - Desktop Shortcut Creator")
    print("=" * 50)
    print()

    # Step 1: Create icon
    print("[1/2] Creating professional icon...")
    if not create_icon(icon_path):
        print("❌ Failed to create icon")
        return

    # Step 2: Create shortcut
    print("[2/2] Creating Desktop shortcut...")
    if not create_shortcut(project_dir, icon_path):
        print("❌ Failed to create shortcut")
        return

    print()
    print("=" * 50)
    print("  ✅ Done! INTEGRA icon is on your Desktop")
    print("  Double-click to launch the app!")
    print("=" * 50)


if __name__ == '__main__':
    main()
