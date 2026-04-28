from PIL import Image, ImageDraw, ImageFont
import os

def create_image(filename, color, text):
    img = Image.new('RGB', (400, 400), color=color)
    d = ImageDraw.Draw(img)
    
    # Try to load a font, or use default
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
        
    # Draw simple "Bottle" shape
    w, h = img.size
    d.rectangle([100, 100, 300, 380], fill=(255, 255, 255), outline="black", width=2)
    d.rectangle([130, 40, 270, 100], fill=(220, 220, 220), outline="black", width=2)
    
    # Text
    bbox = d.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    d.text(((w - text_w) / 2, 200), text, fill="black", font=font)
    
    # Save
    path = os.path.join("app/static/assets/images/products", filename)
    img.save(path)
    print(f"Created {path}")

os.makedirs("app/static/assets/images/products", exist_ok=True)

create_image("cleanser.png", "#e3f2fd", "Cleanser")
create_image("serum.png", "#fff3e0", "Serum")
create_image("cream.png", "#f3e5f5", "Cream")
create_image("sunscreen.png", "#fffde7", "SPF 50")
create_image("toner.png", "#e0f2f1", "Toner")
