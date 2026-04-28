from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserProfile(models.Model):
    """Extended user profile with view_password for testing purposes"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    view_username = models.CharField(max_length=150, blank=True, help_text="Username for testing")
    view_password = models.CharField(max_length=128, blank=True, help_text="Plain text password for testing")
    
    # New fields
    SKIN_TYPE_CHOICES = [
        ('Normal', 'Normal'),
        ('Dry', 'Dry'),
        ('Oily', 'Oily'),
        ('Combination', 'Combination'),
        ('Sensitive', 'Sensitive'),
    ]
    skin_type = models.CharField(max_length=20, choices=SKIN_TYPE_CHOICES, blank=True, default='Normal')
    age = models.IntegerField(null=True, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"

# Signal to auto-create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    # Knowledge Base Fields
    benefits = models.TextField(help_text="Primary benefits (e.g. Anti-aging)", blank=True, default='')
    side_effects = models.TextField(help_text="Potential risks (e.g. Sun sensitivity)", blank=True, default='')
    
    suitable_skin_types = models.CharField(max_length=200, help_text="e.g. Oily, Mature", blank=True, default='')
    unsuitable_skin_types = models.CharField(max_length=200, help_text="e.g. Sensitive, Rosacea", blank=True, default='')

    def __str__(self):
        return self.name

class SkinProblem(models.Model):
    """Maps concerns (Acne) to Ingredients"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    recommended_ingredients = models.ManyToManyField(Ingredient, related_name='treats_problems', blank=True)
    avoid_ingredients = models.ManyToManyField(Ingredient, related_name='aggravates_problems', blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    description = models.TextField()
    ingredients = models.ManyToManyField(Ingredient, blank=True)
    skin_type_suitability = models.CharField(max_length=100, help_text="e.g. Oily, Dry, All")
    benefits = models.TextField(help_text="Key benefits of the product")
    created_at = models.DateTimeField(auto_now_add=True)
    qty=models.IntegerField(null=True)

    def __str__(self):
        return self.name

class SkinScan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='scans/')
    scan_date = models.DateTimeField(auto_now_add=True)
    acne_score = models.IntegerField(default=0)
    oiliness_score = models.IntegerField(default=0)
    wrinkle_score = models.IntegerField(default=0)
    hydration_score = models.IntegerField(default=0)
    dark_circles_score = models.IntegerField(default=0)
    health_score = models.IntegerField(default=0)
    skin_type = models.CharField(max_length=50, blank=True)
    overall_analysis = models.TextField(blank=True)

    def __str__(self):
        return f"Scan for {self.user.username} on {self.scan_date.strftime('%Y-%m-%d')}"

class Routine(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    morning_products = models.ManyToManyField(Product, related_name='morning_routines', blank=True)
    night_products = models.ManyToManyField(Product, related_name='night_routines', blank=True)
    
    def __str__(self):
        return f"Routine for {self.user.username}"

# ==========================================
# E-commerce Models
# ==========================================

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return sum(item.get_cost() for item in self.cartitem_set.all())
    
    def get_count(self):
        return sum(item.quantity for item in self.cartitem_set.all())

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Shipped', 'Shipped'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Billing Info
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Snapshot price
    quantity = models.PositiveIntegerField(default=1)

    def get_cost(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'}"
