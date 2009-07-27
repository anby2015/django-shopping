from shopping import shopping_utils

def get_order(request):
    order = shopping_utils.get_order(request)
    return {'order': order}

