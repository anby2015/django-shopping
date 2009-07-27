from django.contrib import admin
from shopping.models import *

class SelectionInline(admin.TabularInline):
    model = Selection
    extra = 1
    
class ItemVariationInline(admin.TabularInline):
    model = ItemVariation
    extra = 1
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'status')
    list_filter = ('user', 'status',)
    search_fields = ('user',)
    ordering = ('date',)
    inlines = [SelectionInline,]
    
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'active',)
    list_filter = ('tags', 'active',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    inlines = [ItemVariationInline,]
    prepopulated_fields = {"name_slug":("name",)}
    
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_main_image')
    

admin.site.register(Order,OrderAdmin)
admin.site.register(Item, ItemAdmin)

admin.site.register(VariationCategory)
admin.site.register(VariationValue)
admin.site.register(ItemVariation)
admin.site.register(ItemImage, ItemImageAdmin)

