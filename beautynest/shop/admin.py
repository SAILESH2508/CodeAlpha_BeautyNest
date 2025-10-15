from django.contrib import admin
from .models import Category, Product, Review, Profile

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description', 'skin_type_tags')
    list_filter = ('category',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')

admin.site.register(Profile)
