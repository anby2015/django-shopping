from django.shortcuts import render_to_response
from django.template import RequestContext
from shopping.models import Item, Selection, ItemVariation
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from shopping.models import Order
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import simplejson
from shopping import shopping_utils
import urllib
import urllib2

def display_items(request):
    context = {}
    items = Item.objects.all()
    context['items'] = items
    
    return render_to_response('shopping/item_list.html', context, context_instance=RequestContext(request))

def display_items_by_tag(request, tag_slug):
    context = {}
    items = Item.objects.filter(tags__slug__contains=tag_slug).distinct()
    context['items'] = items
    return render_to_response('shopping/item_list.html', context, context_instance=RequestContext(request))

def empty_cart(request):
    #get the order
    order = shopping_utils.get_order(request)
    #delete it
    order.delete()
    #return success message
    response = {'success':True}
    responseJSON = simplejson.dumps(response)
    return HttpResponse(responseJSON)

def view_cart(request):
    context = {}
    business = settings.PAYPAL_ADDRESS
    context['business'] = business
    
    #get or create current order
    order = shopping_utils.get_order(request)
    context['order'] = order
    
    return render_to_response('shopping/viewcart.html', context, context_instance=RequestContext(request))
  
def update_cart(request):
    """This method is called when user changes selection quantities on the view cart page, when user clicks 'update cart' or before final checkout.
       key value pair is selection id, selection quantity """
    if request.method == "POST":
        xml = '<?xml version="1.0"?><selections>'
        for selection_update in request.POST.items():
            #get the params
            id = selection_update[0]
            quantity = selection_update[1]
            #update the django Selection object
            selection = Selection.objects.get(id=id)
            selection.quantity = quantity
            selection.save()
            #add an xml row to the response
            xml += '<selection><id>%s</id><quantity>%s</quantity></selection>' % (selection.id, selection.quantity)
        xml += '</selections>'
        return HttpResponse(xml)

    
def add_to_cart(request):
    '''Add an item to the shopping cart'''
    if request.method == "POST":
        item_id = request.POST.__getitem__('item_id')
        quantity = request.POST.__getitem__('quantity')
        
        #get the current order and item
        order = shopping_utils.get_order(request)
        #Orders are only saved once an item gets added to it
        order.save()
        #save order back to the session
        request.session['shopping_order'] = order
        
        item = Item.objects.get(id=item_id)
        
        #get the item variations if any
        item_variations = []
        for param in request.POST.items():
            #if the http param is an item variation
            key = param[0]
            if key.startswith("variation_"):
                #get the variation_category
                variation_category = str(key).split("_")[1]
                #print "category: " + variation_category
                #and the value the user selected
                variation_value = param[1]
                #print "value: " + variation_value
                #get the matching ItemVariation object
                item_variation = ItemVariation.objects.get(item = item, variation_value__variation_category__name = variation_category, variation_value__value = variation_value)
                #print "----item variation----"
                #print item_variation
                #add it to the collection of item_variations for this selection
                item_variations.append(item_variation)
        
        
        #if user's order already has a selection of this item - including the same variations - add to the quantity
        #otherwise, create a new selection
        selection = None
        selections = Selection.objects.filter(order=order, item=item)
        if selections.count() == 0:
            #create a new Selection object
            selection = Selection(order=order, item=item, quantity=quantity)
            selection.save()
            for item_variation in item_variations:
                selection.item_variations.add(item_variation)
        else:
            #loop through the selections to find the exact one that matches the variations passed in
            #a match is found if variation count is the same and all variations are in list passed in
            match = False
            for possible_selection in selections:
                if possible_selection.item_variations.count() == len(item_variations):
                    #assume its a match unless the variations don't match
                    match = True
                    for item_variation in possible_selection.item_variations.all():
                        if item_variation not in item_variations:
                            match = False
                            
                    if match == True:
                        #found the match. Add to the quantity
                        selection = possible_selection
                        selection.quantity += int(quantity)
                        selection.save()
                        break
                    
            if match == False:
                #no match ever found. This is for the same item but different variations. creating new selection"
                selection = Selection(order=order, item=item, quantity=quantity)
                selection.save()
                for item_variation in item_variations:
                    selection.item_variations.add(item_variation)
        
        response = {}
        response['num_in_cart'] = item.get_num_in_cart(order)
        response['item_count'] = order.get_item_count()
        responseJSON = simplejson.dumps(response)
        return HttpResponse(responseJSON)

def view_item_details(request, slug):
    context = {}
    #get the item that matches the slug
    item = Item.objects.get(name_slug = slug)
    context['item'] = item
    
    #get the main image to display. If no 'main image' specified, just grab one from the collection
    try:
        main_image = item.images.filter(is_main_image = True)[0]
        if main_image == None:
            main_image = item.images.all()[0]
        context['main_image'] = main_image
    except:
        pass
    
   
    
    return render_to_response('shopping/item_details.html', context, context_instance=RequestContext(request)) 


#This method gets called when an order is purchased or refunded. Paypal does a POST callback
def handle_paypal_notify(request):
    #get order info
    print '---------processing paypal IPN-----------'
    log = "notification result: "
    payer_email = ""
    payment_status = ""
    
    #TODO: post back to PayPal system to validate
    
    #assign post variables
    if request.method == "POST":
        payer_email = request.POST.__getitem__('payer_email')
        payment_status = request.POST.__getitem__('payment_status')
        order_id = request.POST.__getitem__('order_id')
#        receiver_email = request.POST.__getitem('receiver_email')
#        mc_gross = request.POST.__getitem('mc_gross')
        
        log += payer_email
        log += ' - '
        log += payment_status
        log += ' - '
        log += order_id
#        log += "   //   "
#        log += receiver_email
#        log += "   //   "
#        log += mc_gross
    
    #Verify correct payment_status
    #Verify correct receiver email
    #Verify correct price
    #Verify correct  
        
    #set order to complete
    
    #send emails?
    
    #update the page?
    
    #log bad requests for manual inspection
    filename = "test-notify.txt"
    file = open(filename, 'w')
    file.write(log)
    file.close()
    return HttpResponse(log)
    
    