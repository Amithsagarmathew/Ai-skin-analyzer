import logging
import base64
from django.core.files.base import ContentFile
from app.models import Product, Ingredient, SkinProblem

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self):
        # Auto-seed if empty
        try:
            if Product.objects.count() < 5:
                self.seed_catalog()
        except Exception as e:
            logger.error(f"Seeding failed (DB might not be ready): {e}")

    def seed_catalog(self):
        """Creates dummy products if none exist."""
        import os
        from django.core.files import File
        
        # Define Catalog
        products_data = [
            # Cleansers
            {"name": "Salicylic Acid Pore Cleanser", "brand": "LCC Active", "category": "Cleanser", "price": 18.00, 
             "skin_type": "Oily, Acne", "description": "2% Salicylic acid cleanser.", "ingredients": "Salicylic Acid, Tea Tree", 
             "benefits": "Unclogs pores", "image_src": "cleanser_acne.jpg"},
             
            {"name": "Hydrating Foam Cleanser", "brand": "LCC Pure", "category": "Cleanser", "price": 22.00, 
             "skin_type": "Dry, Sensitive", "description": "Gentle creamy wash.", "ingredients": "Glycerin, Ceramides", 
             "benefits": "Hydrates barrier", "image_src": "product_cleanser.png"},
             
            {"name": "Gentle Daily Wash", "brand": "LCC Essentials", "category": "Cleanser", "price": 15.00, 
             "skin_type": "Normal, Combination", "description": "pH balanced wash.", "ingredients": "Aloe, Vitamin E", 
             "benefits": "Daily clean", "image_src": "product_cleanser.png"},

            # Toners
            {"name": "Balancing Willow Bark Toner", "brand": "LCC Active", "category": "Toner", "price": 19.00, 
             "skin_type": "Oily", "description": "Exfoliating toner.", "ingredients": "Willow Bark", 
             "benefits": "Oil control", "image_src": "toner.jpg"},
             
            {"name": "Hydrating Essence Toner", "brand": "LCC Pure", "category": "Toner", "price": 24.00, 
             "skin_type": "Dry", "description": "Milky toner.", "ingredients": "Rice Water", 
             "benefits": "Softening", "image_src": "toner.jpg"},

            # Serums
            {"name": "Vitamin C Radiance Serum", "brand": "LCC Glow", "category": "Serum", "price": 45.00, 
             "skin_type": "All", "description": "15% Vitamin C.", "ingredients": "Ascorbic Acid", 
             "benefits": "Brightening", "image_src": "serum_vitc.jpg"},
             
            {"name": "Niacinamide 10% Zinc", "brand": "LCC Clarity", "category": "Serum", "price": 12.00, 
             "skin_type": "Oily, Acne", "description": "Pore refining.", "ingredients": "Niacinamide, Zinc", 
             "benefits": "Reduces blemishes", "image_src": "serum_niacinamide.jpg"},
             
            {"name": "Hyaluronic Acid 2% + B5", "brand": "LCC Hydro", "category": "Serum", "price": 15.00, 
             "skin_type": "Dry", "description": "Deep hydration.", "ingredients": "Hyaluronic Acid", 
             "benefits": "Plumping", "image_src": "serum_ha.jpg"},
             
            {"name": "Retinol 0.5% in Squalane", "brand": "LCC Renew", "category": "Serum", "price": 28.00, 
             "skin_type": "Mature", "description": "Anti-aging powerhouse.", "ingredients": "Retinol", 
             "benefits": "Resurfacing", "image_src": "serum_retinol.jpg"},
             
            # Moisturizers
            {"name": "Water Gel Moisturizer", "brand": "LCC Hydro", "category": "Moisturizer", "price": 32.00, 
             "skin_type": "Oily", "description": "Oil-free gel.", "ingredients": "Gel Base", 
             "benefits": "Lightweight", "image_src": "moisturizer_gel.jpg"},
             
            {"name": "Barrier Repair Cream", "brand": "LCC Pure", "category": "Moisturizer", "price": 35.00, 
             "skin_type": "Dry, Sensitive", "description": "Thick cream.", "ingredients": "Shea Butter", 
             "benefits": "Restores barrier", "image_src": "moisturizer_cream.jpg"},
             
            {"name": "Daily Lotion", "brand": "LCC Essentials", "category": "Moisturizer", "price": 20.00, 
             "skin_type": "Combination", "description": "Standard lotion.", "ingredients": "Jojoba", 
             "benefits": "Balanced", "image_src": "moisturizer_cream.jpg"},

            # Sunscreen
            {"name": "Invisible Shield SPF 50", "brand": "LCC Solar", "category": "Sunscreen", "price": 25.00, 
             "skin_type": "All", "description": "No white cast.", "ingredients": "SPF Filters", 
             "benefits": "Protection", "image_src": "sunscreen.png"},
        ]
        
        base_path = os.path.join(os.getcwd(), 'app/static/assets/images/products')

        for item in products_data:
            prod, created = Product.objects.get_or_create(
                name=item['name'],
                defaults={
                    'brand': item['brand'],
                    'skin_type_suitability': item['skin_type'],
                    'price': item['price'],
                    'description': item['description'],
                    'benefits': item['benefits']
                }
            )
            
            # Update Image if missing or new
            img_filename = item['image_src']
            img_path = os.path.join(base_path, img_filename)
            
            if os.path.exists(img_path):
                try:
                    with open(img_path, 'rb') as f:
                        prod.image.save(img_filename, File(f), save=False)
                        prod.save()
                except Exception as e:
                    print(f"Error saving image for {item['name']}: {e}")
            
            if created:
                for ing_name in item['ingredients'].split(','):
                    ing, _ = Ingredient.objects.get_or_create(name=ing_name.strip())
                    prod.ingredients.add(ing)
                prod.save()
        
        print(f"Database seeded with {len(products_data)} products.")

    def analyze_needs(self, scores, skin_type):
        """Determines skin needs based on scores."""
        needs = []
        conditions = []
        
        if scores['acne'] > 30: 
            needs.append('Acne Control')
            conditions.append('acne')
        if scores['oiliness'] > 40: 
            needs.append('Oil Control')
            conditions.append('oily')
        if scores['wrinkles'] > 30: 
            needs.append('Anti-Aging')
            conditions.append('wrinkles')
        if scores['dryness'] > 40: 
            needs.append('Hydration')
            conditions.append('dry')
        if scores['dark_circles'] > 30: 
            needs.append('Brightening')
            conditions.append('dark_circles')
        if 'Sensitive' in skin_type: 
            needs.append('Soothing')
            conditions.append('sensitive')
            
        return needs, conditions

    def _serialize(self, products):
        return [{
            'id': p.id,
            'name': p.name,
            'brand': p.brand,
            'image_url': p.image.url if p.image else '',
            'price': float(p.price),
            'benefits': p.benefits
        } for p in products]

    def generate_recommendations(self, analysis_result):
        scores = analysis_result['scores']
        skin_type = analysis_result['skin_type']
        
        needs, conditions = self.analyze_needs(scores, skin_type)
        
        # FILTERING LOGIC with FALLBACKS
        def get_product(query, category_backup):
            p = Product.objects.filter(name__icontains=query).first()
            if not p:
                p = Product.objects.filter(name__icontains=category_backup).first()
            return p

        # 1. Cleanser
        if 'Oily' in skin_type or 'acne' in conditions:
            cleanser = get_product("Salicylic", "Cleanser")
        elif 'Dry' in skin_type or 'sensitive' in conditions:
            cleanser = get_product("Hydrating", "Cleanser")
        else:
            cleanser = get_product("Gentle", "Cleanser")
            
        # 2. Toner
        if 'Oily' in skin_type:
            toner = get_product("Balancing", "Toner")
        else:
            toner = get_product("Essence", "Toner")
            
        # 3. Targeted Serums (Morning & Night split)
        serum_am = get_product("Vitamin C", "Serum")
        
        if 'acne' in conditions:
            serum_pm = get_product("Niacinamide", "Serum")
        elif 'wrinkles' in conditions:
            serum_pm = get_product("Retinol", "Serum")
        else:
            serum_pm = get_product("Hyaluronic", "Serum")
            
        # 4. Moisturizer
        if 'Oily' in skin_type:
            moist = get_product("Gel", "Moisturizer")
        elif 'Dry' in skin_type:
            moist = get_product("Barrier", "Moisturizer")
        else:
            moist = get_product("Lotion", "Moisturizer")
            
        # 5. SPF (Always)
        spf = get_product("SPF", "Sunscreen") 
        if not spf: spf = get_product("Shield", "Serum") # Fallback if Sunscreen keyword fails
        
        # Build Routines
        morning_routine = list(filter(None, [cleanser, toner, serum_am, moist, spf]))
        night_routine = list(filter(None, [cleanser, toner, serum_pm, moist]))
        
        # Ingredients Logic (Knowledge Base Driven)
        active_ingredients = set()
        avoid_ingredients = set()
        
        # 1. Map Conditions to Active Ingredients
        for condition_key in conditions:
            # Simple mapping or query (assuming names match partially)
            problems = []
            if condition_key == 'acne': problems = SkinProblem.objects.filter(name__icontains='Acne')
            elif condition_key == 'wrinkles': problems = SkinProblem.objects.filter(name__icontains='Wrinkle')
            elif condition_key == 'dry': problems = SkinProblem.objects.filter(name__icontains='Dry')
            elif condition_key == 'dark_circles': problems = SkinProblem.objects.filter(name__icontains='Dark')
            
            for problem in problems:
                for ing in problem.recommended_ingredients.all():
                    active_ingredients.add(ing.name)
                for ing in problem.avoid_ingredients.all():
                    avoid_ingredients.add(ing.name)

        if not active_ingredients: 
            active_ingredients = {"Vitamin C", "Hyaluronic Acid"}

        # 2. Map Skin Type Constraints
        # Query Ingredients that are explicitly unsuitable
        if 'Sensitive' in skin_type:
            bad_for_sensitive = Ingredient.objects.filter(unsuitable_skin_types__icontains='Sensitive')
            for ing in bad_for_sensitive:
                avoid_ingredients.add(ing.name)
        
        # Filter exclusions (Safety Check)
        final_active = [x for x in list(active_ingredients) if x not in avoid_ingredients]
        
        return {
            'needs': needs,
            'morning_routine': self._serialize(morning_routine),
            'night_routine': self._serialize(night_routine),
            'active_ingredients': final_active[:5],
            'avoid_ingredients': list(avoid_ingredients)[:5]
        }
        

