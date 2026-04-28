import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from app.models import Product, Ingredient

def seed_data():
    if Product.objects.count() > 0:
        print("Products already exist. Skipping seed.")
        return

    # Create Ingredients
    ing_ha = Ingredient.objects.create(name="Hyaluronic Acid", description="Hydrates skin")
    ing_vit_c = Ingredient.objects.create(name="Vitamin C", description="Brightens complexion")
    ing_retinol = Ingredient.objects.create(name="Retinol", description="Anti-aging")
    ing_spf = Ingredient.objects.create(name="SPF 50", description="Sun protection")
    ing_tea_tree = Ingredient.objects.create(name="Tea Tree Oil", description="Anti-acne")

    # Create Products
    p1 = Product.objects.create(
        name="Hydrating Foam Cleanser",
        brand="Jeel Pure",
        price=25.00,
        description="A gentle yet effective foam cleanser that removes impurities without stripping moisture.",
        skin_type_suitability="All Skin Types",
        benefits="Deep cleansing, Hydrating",
        # image="products/cleanser.jpg" # Assuming we upload images later or use placeholder logic in template
    )
    p1.ingredients.add(ing_ha)

    p2 = Product.objects.create(
        name="Vitamin C Radiance Serum",
        brand="Jeel Glow",
        price=45.00,
        description="Potent Vitamin C serum to fade dark spots and even skin tone.",
        skin_type_suitability="Dull Skin",
        benefits="Brightening, Anti-oxidant"
    )
    p2.ingredients.add(ing_vit_c, ing_ha)

    p3 = Product.objects.create(
        name="Night Repair Retinol Cream",
        brand="Jeel Age-Defy",
        price=55.00,
        description="Intensive night cream with retinol to reduce fine lines.",
        skin_type_suitability="Mature Skin",
        benefits="Anti-aging, Resurfacing"
    )
    p3.ingredients.add(ing_retinol, ing_ha)

    p4 = Product.objects.create(
        name="Daily Defense Sunscreen",
        brand="Jeel Protect",
        price=30.00,
        description="Lightweight broad-spectrum sunscreen.",
        skin_type_suitability="All Skin Types",
        benefits="Sun protection, Anti-aging"
    )
    p4.ingredients.add(ing_spf)
    
    p5 = Product.objects.create(
        name="Acne Control Spot Treatment",
        brand="Jeel Clear",
        price=20.00,
        description="Targeted gel for active breakouts.",
        skin_type_suitability="Acne Prone",
        benefits="Acne fighting, Soothing"
    )
    p5.ingredients.add(ing_tea_tree)

    print("Successfully seeded 5 products and ingredients.")

if __name__ == "__main__":
    seed_data()
