from rest_framework import routers

from . import views


class My24Router(routers.SimpleRouter):
    pass


purchase = My24Router()
purchase.register(r'product', views.ProductViewset, basename='purchase-product')
purchase.register(r'supplier', views.SupplierViewset)
purchase.register(r'stock-location', views.StockLocationViewset)
purchase.register(r'stock-mutation', views.StockMutationViewset)
purchase.register(r'stock-location-inventory', views.StockLocationInventoryViewset)
