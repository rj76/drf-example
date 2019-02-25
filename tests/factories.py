import factory
from factory import fuzzy

from apps.purchase import models


class ProductFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Product

    identifier = fuzzy.FuzzyText(length=255)
    name = fuzzy.FuzzyText(length=255)


class SupplierFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Supplier

    name = fuzzy.FuzzyText(length=20)
    address = fuzzy.FuzzyText(length=20)
    postal = fuzzy.FuzzyText(length=10)
    city = fuzzy.FuzzyText(length=20)
    country_code = fuzzy.FuzzyText(length=2)


class StockLocationFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.StockLocation

    identifier = fuzzy.FuzzyText(length=255)
    name = fuzzy.FuzzyText(length=255)


class StockMutationFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.StockMutation

    product = factory.SubFactory(ProductFactory)
    fromLocation = factory.SubFactory(StockLocationFactory)
    toLocation = factory.SubFactory(StockLocationFactory)
    mutationType = fuzzy.FuzzyChoice([o[0] for o in models.StockMutation.TYPES])
    amount = fuzzy.FuzzyInteger(high=10, low=1, step=1)


class StockLocationInventoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.StockLocationInventory

    product = factory.SubFactory(ProductFactory)
    location = factory.SubFactory(StockLocationFactory)
    amount = fuzzy.FuzzyInteger(high=100, low=1, step=1)
