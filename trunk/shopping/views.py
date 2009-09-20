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
from magictags.models import Tag
import urllib
import urllib2
import datetime
from django.template import loader
from django.template import Context

def display_items(request):
    context = {}
    items = Item.objects.all()
    context['items'] = items
    
    return render_to_response('shopping/item_list.html', context, context_instance=RequestContext(request))

def display_items_by_tag(request, tag_slug):
    context = {}
    items = Item.objects.filter(tags__slug__contains=tag_slug).distinct()
    context['items'] = items
    tag_name = Tag.objects.get(slug=tag_slug)
    context['tag_name'] = tag_name
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
        order = shopping_utils.get_order(request)
        xml = '<?xml version="1.0"?><response>'
        #get the selections
        xml += '<selections>'
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
        #also return the new item count and new subtotal
        new_total_count = shopping_utils.get_order(request).get_item_count()
        xml += '<itemcount>' + str(new_total_count) + '</itemcount>'
        new_subtotal = order.get_subtotal()
        xml += '<subtotal>' + str(new_subtotal) + '</subtotal>'
        xml += '</response>'
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
    log = "\n\n ---------Paypal notification result----------"
    log += "\n Date: " + str(datetime.date.today())
    payer_email = ""
    payment_status = ""
    order = None
    price = 0
    
    if request.method == "POST":
        try:
            #get order info
            payment_status = request.POST.__getitem__('payment_status')
            order_id = request.POST.__getitem__('custom') #the order id sent in the paypal form
            receiver_email = request.POST.__getitem__('receiver_email')
            mc_gross = float(request.POST.__getitem__('mc_gross'))
            mc_handling = float(request.POST.__getitem__('mc_handling'))
            mc_shipping = float(request.POST.__getitem__('mc_shipping'))
            tax = float(request.POST.__getitem__('tax'))
            
            #get shopper info
            payer_email = request.POST.__getitem__('payer_email')
            first_name = request.POST.__getitem__('first_name')
            #error
            last_name = request.POST.__getitem__('last_name')
            payer_business_name = request.POST.__getitem__('payer_business_name')
            address_street = request.POST.__getitem__('address_street')
            address_city = request.POST.__getitem__('address_city')
            address_state = request.POST.__getitem__('address_state')
            address_country = request.POST.__getitem__('address_country')
            contact_phone = request.POST.__getitem__('contact_phone')
            #error
        except:
            pass
        
        #find the order in the system
        order = Order.objects.get(id=order_id)
        
        #log order details
        log +='\n Payer Email: '
        log += payer_email
        log += '\n Payer name:'
        log += first_name
        log += last_name
        log +='\n Payer address: '
        log += address_street
        log += address_city
        log += address_state
        log += address_country
        log +='\n Payer contact phone: '
        log += contact_phone
        
        log += ' \n Payment Status: '
        log += payment_status
        log += " \n Order ID: " 
        log += order_id
        log += "\n Receiver Email: "
        log += receiver_email
        log += "\n Gross: "
        log += str(mc_gross)
        log += "\n Handling: "
        log += str(mc_handling)
        log += "\n Shipping: "
        log += str(mc_shipping)
        log += "\n Tax: "
        log += str(tax)
    
        valid = True
#        
#        #Verify transaction with paypal
#        data = dict(request.POST.items())
#        args = {'cmd': '_notify-validate'}
#        args.update(data)
#        verify_url = "https://www.sandbox.paypal.com/cgi-bin/webscr"
#        response = urllib2.urlopen(verify_url, urllib.urlencode(args)).read()
#        log += "\n VERIFIED: "
#        log += str(response)
#        if str(response) != 'VERIFIED':
#            valid = False
#            log += "\n Failed because paypal verification was not VERIFIED" 
#        
#        #TODO: Verify correct payment_status
#        
#        #Verify correct receiver email
#        if receiver_email != settings.PAYPAL_ADDRESS:
#            valid = False
#            log += "\n Failed because receiver email and paypal_address in settings were different"
#            
#        #Verify correct price:  gross - (shipping + tax + handling)
#        subtotal = (mc_gross - mc_handling - mc_shipping - tax)
#        if str(subtotal) != str(order.get_subtotal()):
#            valid = False
#            log += "\n Failed because subtotal returned was different. "
#            log += "\n Required: " + str(order.get_subtotal())
#            log += "\n Actual: " + str(subtotal)
#        log += "\n Subtotal: "
#        log += str(subtotal)
#        
#        if valid:
#            log += "\n ORDER VALID"
#            #internally process the order
#            order_succeeded(order)
#            
#            #prepare the email content to the buyer
#            t = loader.get_template('shopping/email/email_buyer.html')
#            buyer_email_content = t.render(Context({'order': order, 'total':total}))
#            
#            #prepare the email content to the seller
#            t = loader.get_template('shopping/email/email_seller.html')
#            seller_email_content = t.render(Context({'order': order, 'total':total}))
#            log += "\n email content prepared"
#            
#            notify_by_email(buyer_email_content, seller_email_content)
#        else:
#            log += "\n ORDER INVALID!"
         
    #log transactions for manual inspection
    filename = "transaction-log.txt"
    file = open(filename, 'a')
    file.write(log)
    file.close()
    return HttpResponse('')

def order_succeeded(order):
    #set order to completed
    order.status = 2
    order.date = datetime.date.today()
    order.save()
    
def notify_by_email(buyer_email_content, seller_email_content):
    '''send email notifications to the buyer and the seller(s)'''
    from django.core.mail import EmailMultiAlternatives
    from_email = settings.PAYPAL_ADDRESS
    
    #email the buyer 
    msg = EmailMultiAlternatives('Order Confirmation', buyer_email_content, from_email, [payer_email])
    msg.attach_alternative(buyer_email_content, "text/html")
    msg.send()
   
    #email the seller(s)
    msg = EmailMultiAlternatives('Order Received', seller_email_content, from_email, settings.STORE_OWNERS)
    msg.attach_alternative(seller_email_content, "text/html")
    msg.send()
    
    
def get_paypal_form(request):
    '''this gets called anytime the viewcart page gets updated, to keep the paypal form in sync'''
    context = {}
    context['order'] = shopping_utils.get_order(request)
    context['business'] = settings.PAYPAL_ADDRESS
    return render_to_response('shopping/paypal_form.html', context, context_instance=RequestContext(request)) 
    
    