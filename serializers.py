import datetime

from djmoney.contrib.django_rest_framework import MoneyField
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, validators

from apps.core import rest
from apps.order.models import OrderLine
from . import models


class ProductTotalSerializer(serializers.Serializer):
    order_name = serializers.CharField()
    amount = serializers.FloatField()
    price_purchase_amount = serializers.FloatField()
    price_purchase_currency = serializers.CharField()
    price_selling_amount = serializers.FloatField()
    price_selling_currency = serializers.CharField()
    profit = serializers.FloatField()
    amount_perc = serializers.FloatField()
    amount_selling_perc = serializers.FloatField()


class ProductSerializer(rest.TransformDatesMixin, serializers.ModelSerializer):
    show_name = serializers.SerializerMethodField()

    price_purchase = MoneyField(max_digits=10, decimal_places=2)
    price_selling = MoneyField(max_digits=10, decimal_places=2)
    price_selling_alt = MoneyField(max_digits=10, decimal_places=2)

    price_purchase_ex = MoneyField(max_digits=10, decimal_places=2)
    price_selling_ex = MoneyField(max_digits=10, decimal_places=2)
    price_selling_alt_ex = MoneyField(max_digits=10, decimal_places=2)

    image = Base64ImageField(required=False)

    def get_show_name(self, obj):
        if hasattr(obj, 'show_name'):
            return obj.show_name()

        return ''

    class Meta:
        model = models.Product
        fields = ('id', 'identifier', 'show_name', 'name', 'name_short', 'unit', 'supplier', 'product_type', 'modified',
                  'price_purchase', 'price_selling', 'price_selling_alt',
                  'price_purchase_ex', 'price_selling_ex', 'price_selling_alt_ex',
                  'image')


class SupplierSerializer(rest.TransformDatesMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Supplier
        validators = [
            validators.UniqueTogetherValidator(
                queryset=models.Supplier.objects.all(),
                fields=('identifier', 'name', 'address', 'city', 'postal', 'country_code')
            )
        ]
        fields = ('id', 'name', 'address', 'postal', 'city', 'country_code', 'tel',
                  'email', 'contact', 'mobile', 'remarks', 'identifier', 'created', 'modified')


class StockLocationSerializer(rest.TransformDatesMixin, serializers.ModelSerializer):
    class Meta:
        model = models.StockLocation
        fields = ('id', 'identifier', 'name', 'modified')


class StockLocationInventorySerializer(rest.TransformDatesMixin, serializers.ModelSerializer):
    class Meta:
        model = models.StockLocationInventory
        fields = ('id', 'product', 'location', 'amount', 'modified')


class StockLocationInventoryFullSerializer(rest.TransformDatesMixin, serializers.ModelSerializer):
    location = StockLocationSerializer()
    product = ProductSerializer()
    sales_amount_today = serializers.SerializerMethodField()

    def get_sales_amount_today(self, obj):
        amount = 0

        orderlines = OrderLine.objects.filter(
            location_relation=obj.location,
            product_relation=obj.product,
            order__start_date=datetime.date.today(),
            order__order_type='sales'
        )

        for orderline in orderlines:
            amount += orderline.amount

        return amount

    class Meta:
        model = models.StockLocationInventory
        fields = ('id', 'product', 'location', 'amount', 'sales_amount_today', 'modified')


class StockMutationSerializer(rest.TransformDatesMixin, serializers.ModelSerializer):
    summary = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()

    def get_product_name(self, obj):
        return '%s' % obj.product

    def get_summary(self, obj):
        if obj.mutationType == 'purchase':
            return '<b>Purchase to</b> %s' % obj.toLocation

        if obj.mutationType == 'sales':
            return '<b>Sales from</b> %s' % obj.fromLocation

        if obj.mutationType == 'move':
            return '<b>Move from</b> %s <b>to</b> %s' % (obj.fromLocation, obj.toLocation)

    class Meta:
        model = models.StockMutation
        fields = ('id', 'product', 'fromLocation', 'toLocation', 'amount',
                  'mutationType', 'modified', 'summary', 'product_name')
