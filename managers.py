from django.db.models import Manager


class ProductManager(Manager):
    pass


class SupplierManager(Manager):
    pass


class StockLocationManager(Manager):
    pass


class StockLocationMutationManager(Manager):
    pass


class StockLocationInventoryManager(Manager):
    pass


class StockAmountProductManager(Manager):
    pass
