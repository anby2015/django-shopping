from django.db import models
from django.contrib import admin
from fields import ManyToManyField_NoSyncdb
import datetime
from django.db.models import Sum

class Item(models.Model):
    name = models.CharField(max_length=100)
    name_slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    price = models.FloatField()
    active = models.BooleanField(default=True)
    tags = ManyToManyField_NoSyncdb('magictags.Tag', db_table='magictags_tag_items', blank=True, null=True, help_text='Assign Tags to this item for easy filtering when shopping')
    images = models.ManyToManyField('ItemImage', blank=True, null=True)
    
    def __unicode__(self):
        return self.name
    
    def get_num_in_cart(self, order):
        quantity = 0
        for selection in order.selection_set.filter(item=self):
            quantity += selection.quantity
        return quantity
        
    def get_main_image(self):
	    try:
	        main_image = self.images.filter(is_main_image = True)[0]
	        if main_image == None:
	            main_image = item.images.all()[0]
	        return main_image
	    except:
	        pass
	    
    
class Order(models.Model):
    user = models.ForeignKey('auth.User', blank=True, null=True)
    guest = models.CharField(max_length=400, blank=True, help_text='Guests are anonymous, non-logged in visitors')
    date = models.DateField(default = datetime.date.today())
    STATUS_CHOICES = (
        (1,'Saved for later'),
        (2,'Completed'),
    )
    status = models.CharField(choices=STATUS_CHOICES, blank=True, max_length=100)
    
    def __unicode__(self):
    	if self.user:
        	return '' + self.user.username + ' on ' + str(self.date)
        else:
        	return 'Guest shopper on ' + str(self.date)
    
    def get_item_count(self):
        print self.selection_set.all()
        count = self.selection_set.aggregate(Sum('quantity'))
        if count['quantity__sum'] == None:
            return 0
        else:
            return count['quantity__sum']
        
    def get_subtotal(self):
#        subtotal = self.selection_set.all().aggregate(Sum('item__price'))
        subtotal = 0
        from django.template.defaultfilters import floatformat
        for selection in self.selection_set.all():
            subtotal += (selection.item.price * selection.quantity)
        return floatformat(subtotal,2)
    
    def get_selections(self):
        selections = []
        for selection in self.selection_set.all():
            if selection.quantity > 0:
                selections.append(selection)
        return selections
        
    
class Selection(models.Model):
    item = models.ForeignKey('Item')
    quantity = models.IntegerField()
    order = models.ForeignKey('Order')
    item_variations = models.ManyToManyField('ItemVariation')
    
    def __unicode__(self):
        return self.item.name + ' x ' + str(self.quantity)
    
    def display_variations(self):
        response = '( '
        if len(self.item_variations.all()) > 0:
            for variation in self.item_variations.all():
                response += ' '
                response += str(variation.variation_value)
            response += ' )'
            return response
        else:
            return ''
    

class VariationCategory(models.Model):
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name
    
class VariationValue(models.Model):
    value = models.CharField(max_length=100)
    variation_category = models.ForeignKey('VariationCategory')
    
    def __unicode__(self):
        return self.value
    
class ItemVariation(models.Model):
    item = models.ForeignKey('Item')
    variation_value = models.ForeignKey('VariationValue')
    #price_difference = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    def __unicode__(self):
        return self.item.name + ' - ' + str(self.variation_value.variation_category.name) + ': ' + str(self.variation_value)
    
    
from photologue.models import ImageModel
class ItemImage(ImageModel):
    ''' extends photologue for easy image management '''
    name = models.CharField(max_length=120)
    active = models.BooleanField(default=True)
    is_main_image = models.BooleanField(default=False, 
        help_text='If an image is a "main image", it will show up as the product thumbnail, and the first one on the product page. Only one image per product should be marked as main image.'
        )
    
    def __unicode__(self):
        if self.is_main_image:
            return self.name + ' (main image)'
        else:
            return self.name
