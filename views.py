import datetime
from operator import itemgetter

from django.conf import settings
from django.db.models import Q, Subquery, Sum
from django.views.generic.base import TemplateView

from braces.views import LoginRequiredMixin
from rest_framework import renderers
from rest_framework.decorators import action
from rest_framework.response import Response

from drf_renderer_xlsx.mixins import XLSXFileMixin
from drf_renderer_xlsx.renderers import XLSXRenderer

from apps.core import permissions
from apps.core.rest import BaseMy24ViewSet, BaseListView
from apps.order.models import OrderLine
from . import models
from . import serializers


class PurchaseIndex(LoginRequiredMixin, TemplateView):
    template_name = 'purchase/index.html'


class PurchaseDeviceIndex(LoginRequiredMixin, TemplateView):
    template_name = 'purchase/device.html'


class ProductQueryMixin(object):
    def get_totals(self, year):
        filter_q = Q(product_relation__in=Subquery(self.queryset.values('id')),
                     order__order_type='sales', order__start_date__year=year)

        return OrderLine.objects.filter(filter_q).aggregate(Sum('price_selling'), Sum('amount'), Sum('price_purchase'))

    def get_total_sales(self, year, query):
        totals = self.get_totals(year)

        product_row = {}

        filter_q = Q(product_relation__in=Subquery(self.queryset.values('id')),
                     order__order_type='sales', order__start_date__year=year)

        if query:
            filter_q = filter_q & Q(product_relation__name__icontains=query)

        for orderline in OrderLine.objects.filter(filter_q).select_related('order').select_related('product_relation'):

            if orderline.product_relation.id in product_row:
                product_row[orderline.product_relation.id]['amount'] += orderline.amount
                product_row[orderline.product_relation.id]['price_purchase_amount'] += orderline.price_purchase.amount
                product_row[orderline.product_relation.id]['price_selling_amount'] += orderline.price_selling.amount
            else:
                product_row[orderline.product_relation.id] = {
                    'product_image': orderline.product_relation.image.url if orderline.product_relation.image else '',
                    'product_name': orderline.product_relation.name,
                    'amount': orderline.amount,
                    'price_purchase_amount': orderline.price_purchase.amount,
                    'price_purchase_currency': '%s' % orderline.price_purchase.currency,
                    'price_selling_amount': orderline.price_selling.amount,
                    'price_selling_currency': '%s' % orderline.price_selling.currency,
                }

        response = []

        # for row in result:
        for key in product_row.keys():
            profit = round(product_row[key]['price_selling_amount'] - product_row[key]['price_purchase_amount'], 2)
            product_row[key]['profit'] = profit

            price_selling_amount = product_row[key]['price_selling_amount']
            amount = product_row[key]['amount']

            product_row[key]['amount_perc'] = round((amount / totals['amount__sum']) * 100, 2)
            product_row[key]['amount_selling_perc'] = round(
                (price_selling_amount / totals['price_selling__sum']) * 100, 2
            )

            response.append(product_row[key])

        return sorted(response, key=itemgetter('price_selling_amount'), reverse=True)

    def get_total_sales_per_customer(self, year, query):
        totals = self.get_totals(year)

        customers = {}

        filter_q = Q(product_relation__in=Subquery(self.queryset.values('id')),
                     order__order_type='sales', order__start_date__year=year)

        if query:
            filter_q = filter_q & Q(order__order_name__icontains=query)

        for orderline in OrderLine.objects.filter(filter_q).select_related('order').select_related('product_relation'):
            if orderline.order.customer_id in customers:
                customers[orderline.order.customer_id]['amount'] += orderline.amount
                customers[orderline.order.customer_id]['price_purchase_amount'] += orderline.price_purchase.amount
                customers[orderline.order.customer_id]['price_selling_amount'] += orderline.price_selling.amount
            else:
                customers[orderline.order.customer_id] = {
                    'order_name': orderline.order.order_name,
                    'amount': orderline.amount,
                    'price_purchase_amount': orderline.price_purchase.amount,
                    'price_purchase_currency': '%s' % orderline.price_purchase.currency,
                    'price_selling_amount': orderline.price_selling.amount,
                    'price_selling_currency': '%s' % orderline.price_selling.currency,
                }

        response = []

        for key in customers.keys():
            profit = round(customers[key]['price_selling_amount'] - customers[key]['price_purchase_amount'], 2)
            customers[key]['profit'] = profit

            customers[key]['amount_perc'] = round((customers[key]['amount'] / totals['amount__sum']) * 100, 2)
            customers[key]['amount_selling_perc'] = round(
                (customers[key]['price_selling_amount'] / totals['price_selling__sum']) * 100, 2
            )

            response.append(customers[key])

        return sorted(response, key=itemgetter('price_selling_amount'), reverse=True)


class ExportXlsView(ProductQueryMixin, XLSXFileMixin, BaseListView):
    pagination_class = None
    renderer_classes = (XLSXRenderer,)
    filename = 'total_sales_per_customer.xlsx'
    serializer_class = serializers.ProductTotalSerializer
    queryset = models.Product.objects.all()

    def get_queryset(self, *arg, **kwargs):
        now = datetime.datetime.now()
        year = self.request.GET.get('year', now.year)

        query = self.request.query_params.get('q')

        return self.get_total_sales_per_customer(year, query)


class ProductViewset(ProductQueryMixin, BaseMy24ViewSet):
    serializer_class = serializers.ProductSerializer
    serializer_detail_class = serializers.ProductSerializer
    permission_classes = (
        permissions.IsPlanningUser |
        permissions.IsEngineer |
        permissions.IsCustomerUser |
        permissions.IsSalesUser,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    paginate_by = 20
    filterset_fields = ('product_type',)
    search_fields = ('identifier', 'name', 'search_name', 'unit', 'supplier', 'product_type')
    queryset = models.Product.objects.all()
    model = models.Product

    @action(detail=False, methods=['GET'])
    def autocomplete(self, request, *args, **kwargs):
        query = self.request.query_params.get('q')

        data = []
        qs = self.queryset
        qs = qs.filter(
            Q(identifier__icontains=query) |
            Q(name__icontains=query) |
            Q(name_short__icontains=query) |
            Q(search_name__icontains=query) |
            Q(unit__icontains=query) |
            Q(supplier__icontains=query) |
            Q(product_type__icontains=query)
        )

        for product in qs:
            image = '%s%s' % (settings.MEDIA_URL, product.image.name) if product.image else ''
            data.append({
                'id': product.id,
                'identifier': product.identifier,
                'name': product.name,
                'value': '%s (%s)' % (product, product.unit),
                'price_purchase': '%s' % product.price_purchase,
                'price_selling': '%s' % product.price_selling,
                'price_selling_alt': '%s' % product.price_selling_alt,
                'image': image
            })

        return Response(data)

    def get_totals(self, year):
        filter_q = Q(product_relation__in=Subquery(self.queryset.values('id')),
                     order__order_type='sales', order__start_date__year=year)

        return OrderLine.objects.filter(filter_q).aggregate(Sum('price_selling'), Sum('amount'), Sum('price_purchase'))

    @action(detail=False, methods=['GET'])
    def total_sales(self, request, *args, **kwargs):
        """
        total sales per product
        """
        now = datetime.datetime.now()
        year = self.request.GET.get('year', now.year)

        query = self.request.query_params.get('q')

        response = self.get_total_sales(year, query)

        return Response({
            'result': response,
            'num_pages': 1
        })

    @action(detail=False, methods=['GET'])
    def total_sales_per_customer(self, request, *args, **kwargs):
        """
        group product sales per customer and totalize
        """
        now = datetime.datetime.now()
        year = self.request.GET.get('year', now.year)

        query = self.request.query_params.get('q')

        response_data = self.get_total_sales_per_customer(year, query)

        return Response({
            'result': response_data,
            'num_pages': 1
        })

    @action(detail=False, methods=['GET'])
    def total_sales_per_product_customer(self, request, *args, **kwargs):
        """
        group product sales per customer and totalize
        """
        now = datetime.datetime.now()
        year = self.request.GET.get('year', now.year)

        totals = self.get_totals(year)

        query = self.request.query_params.get('q')

        customer_products = {}

        filter_q = Q(product_relation__in=Subquery(self.queryset.values('id')),
                     order__order_type='sales', order__start_date__year=year)

        if query:
            filter_q = filter_q & (Q(order__order_name__icontains=query) | Q(product_relation__name__icontains=query))

        for orderline in OrderLine.objects.filter(filter_q).select_related('order').select_related('product_relation'):
            key = '%s-%s' % (orderline.order.customer_id, orderline.product_relation.id)

            if key in customer_products:
                customer_products[key]['amount'] += orderline.amount
                customer_products[key]['price_purchase_amount'] += orderline.price_purchase.amount
                customer_products[key]['price_selling_amount'] += orderline.price_selling.amount
            else:
                customer_products[key] = {
                    'product_image': orderline.product_relation.image.url if orderline.product_relation.image else '',
                    'product_name': orderline.product_relation.name,
                    'order_name': orderline.order.order_name,
                    'amount': orderline.amount,
                    'price_purchase_amount': orderline.price_purchase.amount,
                    'price_purchase_currency': '%s' % orderline.price_purchase.currency,
                    'price_selling_amount': orderline.price_selling.amount,
                    'price_selling_currency': '%s' % orderline.price_selling.currency,
                }

        response = []

        for key in customer_products.keys():
            customer_products[key]['amount_perc'] = round(
                (customer_products[key]['amount'] / totals['amount__sum']) * 100, 2
            )
            customer_products[key]['amount_selling_perc'] = round(
                (customer_products[key]['price_selling_amount'] / totals['price_selling__sum']) * 100, 2
            )

            response.append(customer_products[key])

        response = sorted(response, key=itemgetter('price_selling_amount'), reverse=True)

        return Response({
            'result': response,
            'num_pages': 1
        })


class SupplierViewset(BaseMy24ViewSet):
    serializer_class = serializers.SupplierSerializer
    serializer_detail_class = serializers.SupplierSerializer
    permission_classes = (permissions.IsPlanningUser,)
    search_fields = ('name', 'city', 'identifier', 'email')
    queryset = models.Supplier.objects.all()
    model = models.Supplier

    @action(detail=False, methods=['GET'])
    def autocomplete(self, request, *args, **kwargs):
        query = self.request.query_params.get('q')

        data = []
        qs = self.queryset
        qs = qs.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(city__icontains=query) |
            Q(email__icontains=query)
        )

        for supplier in qs:
            value = '(%s) %s, %s (%s)' % (supplier.identifier, supplier.name, supplier.city, supplier.country_code)

            data.append({
                'id': supplier.id,
                'name': supplier.name,
                'postal': supplier.postal,
                'city': supplier.city,
                'country_code': supplier.country_code,
                'tel': supplier.tel,
                'mobile': supplier.mobile,
                'email': supplier.email,
                'identifier': supplier.identifier,
                'contact': supplier.contact,
                'remarks': supplier.remarks,
                'value': value
            })

        return Response(data)


class StockLocationViewset(BaseMy24ViewSet):
    serializer_class = serializers.StockLocationSerializer
    serializer_detail_class = serializers.StockLocationSerializer
    permission_classes = (permissions.IsPlanningUser,)
    search_fields = ('identifier', 'name')
    queryset = models.StockLocation.objects.all()
    model = models.StockLocation


class StockMutationViewset(BaseMy24ViewSet):
    serializer_class = serializers.StockMutationSerializer
    serializer_detail_class = serializers.StockMutationSerializer
    permission_classes = (permissions.IsPlanningUser | permissions.IsSalesUser,)
    queryset = models.StockMutation.objects.select_related('product').all()
    model = models.StockMutation


class StockLocationInventoryViewset(BaseMy24ViewSet):
    serializer_class = serializers.StockLocationInventorySerializer
    serializer_detail_class = serializers.StockLocationInventorySerializer
    permission_classes = (permissions.IsPlanningUser | permissions.IsSalesUser,)
    search_fields = ('product__name', 'location__name')
    filterset_fields = ('product', 'location')
    page_size = 200
    queryset = models.StockLocationInventory. \
        objects. \
        select_related('product', 'location'). \
        order_by('product__name'). \
        all()
    model = models.StockLocationInventory

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.StockLocationInventorySerializer
        if self.action == 'list_full':
            return serializers.StockLocationInventoryFullSerializer

        return serializers.StockLocationInventorySerializer

    @action(detail=False, methods=['GET'])
    def list_full(self, request, *args, **kwargs):
        return super().list(request, args, kwargs)

    @action(detail=False, methods=['GET'])
    def list_product_types(self, request, *args, **kwargs):
        location_id = self.request.query_params.get('location_id')

        qs = self.get_queryset().filter(location_id=location_id).values('product__product_type').distinct()
        data = []

        for product_type in qs:
            data.append({
                'location_id': int(location_id),
                'product_type': product_type['product__product_type'],
            })

        return Response(data)
