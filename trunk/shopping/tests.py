from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import simplejson
from django.core import mail
from django.template import loader
from django.template import Context

class ViewTest(TestCase):
    fixtures = ['tests/auth.json', 'tests/shopping.json', 'tests/magictags.json']
    
    def setUp(self):
        #for now log in. TODO: enable anonymous users
        self.client.login(username='Cindy', password='ccisum')
#        shopper = User.objects.get(username='geddesign')
#        self.assertEquals(shopper.username, 'geddesign')
    
    def test_add_to_cart(self):
        '''Tests the add_to_cart view'''
        c = self.client
        
        
        '''Test that a Medium orange hoody can be added to the cart for the first time'''
        response = c.post('/shopping/cart/add/', {'item_id': 2, 'quantity': 1, 'variation_Size': 'Medium'})
        #decode the JSON response
        object = simplejson.loads(response.content)
#        print 'JSON response object'
#        print object
#        print 'end JSON response object'
        
        #should now be one medium orange hoody in the cart
        self.assertEquals(object['num_in_cart'], 1)
        #should now be just one item total in cart
        self.assertEquals(object['item_count'], 1)
        
        
        '''Test that one more Medium size hoody can be added '''
        response = c.post('/shopping/cart/add/', {'item_id': 2, 'quantity': 1, 'variation_Size': 'Medium'})
        object = simplejson.loads(response.content)
#        print 'JSON response object'
#        print object
#        print 'end JSON response object'
        
        #should now be two medium orange hoodies in the cart
        self.assertEquals(object['num_in_cart'], 2)
        #should now be just one item total in cart
        self.assertEquals(object['item_count'], 2)
        
        
        '''Test that a third Medium size hoody can be added '''
        response = c.post('/shopping/cart/add/', {'item_id': 2, 'quantity': 1, 'variation_Size': 'Medium'})
        object = simplejson.loads(response.content)
#        print 'JSON response object'
#        print object
#        print 'end JSON response object'
        
        #should now be two medium orange hoodies in the cart
        self.assertEquals(object['num_in_cart'], 3)
        #should now be just one item total in cart
        self.assertEquals(object['item_count'], 3)
        
        
        ''' Test that a Large size hoody can be added '''
        response = c.post('/shopping/cart/add/', {'item_id': 2, 'quantity': 1, 'variation_Size': 'Large'})
        object = simplejson.loads(response.content)
#        print 'JSON response object'
#        print object
#        print 'end JSON response object'
        
        #should now be one Large hoody in the cart, 4 hoodies total
        self.assertEquals(object['num_in_cart'], 4)
        #should now be just one item total in cart
        self.assertEquals(object['item_count'], 4)
        
        
        ''' Test that a second Large size hoody can be added '''
        response = c.post('/shopping/cart/add/', {'item_id': 2, 'quantity': 1, 'variation_Size': 'Large'})
        object = simplejson.loads(response.content)
#        print 'JSON response object'
#        print object
#        print 'end JSON response object'
        
        #should now be one Large hoody in the cart
        self.assertEquals(object['num_in_cart'], 5)
        #should now be just one item total in cart
        self.assertEquals(object['item_count'], 5)
        
        
        ''' Test an item with multiple variations, like the cotton shirt '''
        response = c.post('/shopping/cart/add/', {'item_id': 1, 'quantity': 1, 'variation_Size': 'Small', 'variation_Color': 'Blue'})
        object = simplejson.loads(response.content)
#        print 'JSON response object'
#        print object
#        print 'end JSON response object'
        
        #should now be one Cotton Shirt in the cart
        self.assertEquals(object['num_in_cart'], 1)
        #should now be just one item total in cart
        self.assertEquals(object['item_count'], 6)
        
        
        ''' Add a second item with multiple variations, like the cotton shirt '''
        response = c.post('/shopping/cart/add/', {'item_id': 1, 'quantity': 1, 'variation_Size': 'Small', 'variation_Color': 'Blue'})
        object = simplejson.loads(response.content)
#        print 'JSON response object'
#        print object
#        print 'end JSON response object'
        
        #should now be two Cotton Shirts in the cart
        self.assertEquals(object['num_in_cart'], 2)
        #should now be just one item total in cart
        self.assertEquals(object['item_count'], 7)
        
        
        ''' Add another item with multiple variations, like the cotton shirt, but different variations'''
        response = c.post('/shopping/cart/add/', {'item_id': 1, 'quantity': 1, 'variation_Size': 'Medium', 'variation_Color': 'Blue'})
        object = simplejson.loads(response.content)
#        print 'JSON response object'
#        print object
#        print 'end JSON response object'
        
        #should now be two Cotton Shirts in the cart
        self.assertEquals(object['num_in_cart'], 3)
        #should now be just one item total in cart
        self.assertEquals(object['item_count'], 8)

    def test_view_cart_details(self):
        '''Tests the view_item_details view'''
        c = self.client
        
        ''' Test the details for the orange hoody item'''
        response = c.get('/shopping/items/orange-hoody/')
        item = response.context['item']
        self.assertEquals(item.id, 2)
        self.assertEquals(item.name, "Orange Hoody")
        
        
    def test_display_items_by_tag(self):
        '''Tests the display_items_by_tag view'''
        c = self.client
        
        '''Filter by tag: Summer (so use the tag's slug) '''
        response = c.get('/shopping/tags/summer/')
        items = response.context['items']
        self.assertEquals(items.count(), 1, 'should be just one item with the tag of summer')
        
        '''Filter by tag: Summer (so use the tag's slug) '''
        response = c.get('/shopping/tags/tops/')
        items = response.context['items']
        self.assertEquals(items.count(), 2, 'should be 2 item with the tag of summer')
        
    
    def test_empty_cart(self):
        '''tests the empty_cart view'''
        c = self.client
        
        '''add something to the cart'''
        c.post('/shopping/cart/add/', {'item_id': 2, 'quantity': 1, 'variation_Size': 'Medium'})
        
        ''' empty the cart, should have nothing left after'''
        response = c.post('/shopping/cart/empty/')
        json = simplejson.loads(response.content)
        success = json['success']
        
        self.assertEquals(success, True, 'Should have returned True')
        
        '''make sure it got deleted'''
        
        '''do a page refresh and make sure a new empty order exists'''
        response = c.get('/shopping/')
        order = response.context['order']
        
        self.assertEquals(order.get_item_count(), 0, 'order should be empty')
        
    def test_order_succeeed(self):
        ''' Test that orders are internally processed correctly'''
        from shopping.models import Order
        from shopping.views import order_succeeded
        order = Order.objects.create()
        response = order_succeeded(order)
        self.assertEquals(order.status, 2, 'should be 2 for completed')

    def test_notify_by_email(self):
        '''Test that email notifications are sent'''
        from shopping.views import notify_by_email
        payer_email_content = '<h1>Thanks for shopping!</h1>'
        payer_email_content_text = 'Thanks for shopping!'
#        seller_email_content = '<h1>Order Received</h1>'
#        seller_email_content_text = 'Order Received'
        
        log = "\n-----------test log----------"
        #prepare the email content to the buyer
        t = loader.get_template('shopping/email/paypal/email_buyer.html')
        payer_email_content = t.render(Context(locals()))
        payer_email_content_text = t.render(Context(locals()))
        log += '\n payer email message:'
        log += payer_email_content
        
        #prepare the email content to the seller
        t = loader.get_template('shopping/email/paypal/email_seller.html')
        seller_email_content = t.render(Context(locals()))
        seller_email_content_text = t.render(Context(locals()))
        log += "\n email content prepared"
        log += '\n seller email message:'
        log += seller_email_content
        
        
        notify_by_email('davidcgeddes@gmail.com', payer_email_content, payer_email_content_text, seller_email_content, seller_email_content_text)
        self.assertEquals(len(mail.outbox), 2)
        #log transactions for manual inspection
        filename = "transaction-log-test.txt"
        file = open(filename, 'a')
        file.write(log)
        file.close()
