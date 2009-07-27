from django.conf.urls.defaults import *


urlpatterns = patterns('shopping.views',
     url(r'^$', 'display_items', name='shopping-items'),
     url(r'^cart/$', 'view_cart', name='shopping-cart'),
     #empty cart
     url(r'cart/empty/$', 'empty_cart', name='shopping-empty-cart'),
     url(r'^cart/update/$', 'update_cart', name='shopping-update'),
     url(r'^cart/add/$', 'add_to_cart', name='shopping-add'),
     url(r'^items/(?P<slug>[\-\d\w]+)/$', 'view_item_details', name='shopping-item'),
     #filter by tag
     url(r'tags/(?P<tag_slug>[\-\d\w]+)/$', 'display_items_by_tag', name='shopping-filter-by-tag'),
     #notify url for paypal callback
     url(r'notify/paypal/$', 'handle_paypal_notify', name='shopping-paypal-notify'),
)