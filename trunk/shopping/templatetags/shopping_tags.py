from django import template
from django.template import Node
from shopping.models import VariationCategory, Order
from django.db.models import Count

register = template.Library()

def get_num_in_cart(parser, token):
    bits = token.contents.split()
    return NumNode(bits[1], bits[2])

class NumNode(Node):
    def __init__(self, item, order):
        self.item = template.Variable(item) #pass in the real one
        self.order = template.Variable(order)
        
    def render(self, context):
        #resolve to real objects from the template variables
        item = self.item.resolve(context)
        order = self.order.resolve(context)
        quantity = item.get_num_in_cart(order)
        return quantity
            
get_num_in_cart = register.tag(get_num_in_cart)

@register.inclusion_tag('shopping/item_variation.html')
def get_item_variations(item):
    ''' This Tag gets displays the html inputs for possible item variations. Variations
        get grouped by Variation Category. '''
    new_context = {}
    variations = item.itemvariation_set.all()
    categories = []
    for variation in variations:
        category = variation.variation_value.variation_category
        if category not in categories:
            #add the category and its accompanying variation values
            category.variations = item.itemvariation_set.filter(variation_value__variation_category=category)
            categories.append(category)
            
    new_context['categories'] = categories 
    return new_context

#
## This tag is for getting the user's order object so its available on each page
#def get_order(parser, token):
#    bits = token.contents.split()
#    varname = bits[2]
#    return OrderNode(varname)
#
#class OrderNode(Node):
#    def __init__(self, varname):
#        self.varname = varname
#        
#    def render(self, context):
#        order, created = Order.objects.get_or_create(user=context['user'], status=1)
#        context[self.varname] = order
#        return ''
#    
#get_order = register.tag(get_order)
