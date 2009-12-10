from django.conf import settings
from django.http import HttpResponseRedirect

def check_allow_guest_shoppers(func):
    '''if Guest Shopping is not allowed redirect to login'''
    def wrapped(request, *args, **kwargs):  
        if not request.user.is_authenticated():
            if settings.ALLOW_GUEST_SHOPPERS:
                return func(request, *args, **kwargs)
            else:
                return HttpResponseRedirect('/')
        else:
            return func(request, *args, **kwargs)
        
    return wrapped