from django.contrib import admin
from .models import UserProfile, Ingredient, Product, SkinScan, Routine

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'view_username', 'view_password')
    search_fields = ('user__username', 'view_username')

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'skin_type_suitability')
    search_fields = ('name', 'brand')
    list_filter = ('skin_type_suitability',)

@admin.register(SkinScan)
class SkinScanAdmin(admin.ModelAdmin):
    list_display = ('user', 'scan_date', 'acne_score', 'oiliness_score', 'hydration_score')
    list_filter = ('scan_date',)
    search_fields = ('user__username',)

@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)
