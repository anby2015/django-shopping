from shopping.models import Order

def get_order(request, create_if_none = False):
    '''Make the order globally available. If user is logged in, order is linked to the user.
        If no user logged in, get or create the order in the session.
        Note that the order is NOT saved to the database until an item is added to the order.
        This solves the issue of having an empty order for visitors that aren't shopping'''
    order = None
    if request.user.is_authenticated():
        try:
            order = Order.objects.get(user=request.user, status=1)
        except:
            order = Order(status=1, user=request.user)
    else:
        #see if order in session
        if 'shopping_order' in request.session:
            order = request.session['shopping_order']
        else:
            #create it and store in session
            order = Order(status=1, guest='ip here')
            request.session['shopping_order'] = order
    
    return order    
    