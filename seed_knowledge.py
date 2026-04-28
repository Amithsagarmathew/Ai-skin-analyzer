
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from app.models import Ingredient, SkinProblem

def seed():
    print("Seeding Knowledge Base...")

    # 1. Define Ingredients Data
    ingredients_data = [
        {
            "name": "Salicylic Acid",
            "benefits": "Deep pore cleansing, exfoliates dead skin, reduces sebum.",
            "side_effects": "Dryness, Potential irritation.",
            "suitable": "Oily, Acne",
            "unsuitable": "Dry, Sensitive"
        },
        {
            "name": "Retinol",
            "benefits": "Increases cell turnover, reduces fine lines, boosts collagen.",
            "side_effects": "Redness, Peeling, Sun sensitivity.",
            "suitable": "Mature, Acne, Oily",
            "unsuitable": "Sensitive, Pregnant, Rosacea"
        },
        {
            "name": "Vitamin C",
            "benefits": "Brightens tone, fades dark spots, antioxidant protection.",
            "side_effects": "Mild tingling, potential irritation at high %.",
            "suitable": "All, Dull",
            "unsuitable": "Sensitive (if L-Ascorbic Acid)"
        },
        {
            "name": "Hyaluronic Acid",
            "benefits": "Intense hydration, plumps skin.",
            "side_effects": "None (generally safe).",
            "suitable": "All, Dry, Dehydrated",
            "unsuitable": ""
        },
        {
            "name": "Niacinamide",
            "benefits": "Regulates oil, strengthens barrier, reduces redness.",
            "side_effects": "Rare irritation at high concentrations.",
            "suitable": "All, Oily, Sensitive",
            "unsuitable": ""
        }
    ]

    qs_map = {}
    for data in ingredients_data:
        ing, created = Ingredient.objects.get_or_create(name=data["name"])
        ing.benefits = data["benefits"]
        ing.side_effects = data["side_effects"]
        ing.suitable_skin_types = data["suitable"]
        ing.unsuitable_skin_types = data["unsuitable"]
        ing.save()
        qs_map[data["name"]] = ing
        print(f"Updated Ingredient: {ing.name}")

    # 2. Define Skin Problems
    problems_data = [
        {
            "name": "Acne",
            "desc": "Clogged pores leading to pimples and inflammation.",
            "rec": ["Salicylic Acid", "Niacinamide", "Retinol"],
            "avoid": [] # Usually oils, but that's generic
        },
        {
            "name": "Wrinkles",
            "desc": "Loss of collagen and elasticity.",
            "rec": ["Retinol", "Vitamin C", "Hyaluronic Acid"],
            "avoid": []
        },
        {
            "name": "Dryness",
            "desc": "Lack of moisture and barrier function.",
            "rec": ["Hyaluronic Acid", "Niacinamide"],
            "avoid": ["Salicylic Acid", "Retinol"] # Can aggravate
        },
        {
            "name": "Dark Circles",
            "desc": "Pigmentation under eyes.",
            "rec": ["Vitamin C", "Niacinamide"],
            "avoid": []
        }
    ]

    for p_data in problems_data:
        prob, _ = SkinProblem.objects.get_or_create(name=p_data["name"])
        prob.description = p_data["desc"]
        prob.save()
        
        # Add Recommended
        for rec_name in p_data["rec"]:
            if rec_name in qs_map:
                prob.recommended_ingredients.add(qs_map[rec_name])
        
        # Add Avoid
        for av_name in p_data["avoid"]:
            if av_name in qs_map:
                prob.avoid_ingredients.add(qs_map[av_name])
                
        print(f"Updated Problem: {prob.name}")

if __name__ == "__main__":
    seed()
