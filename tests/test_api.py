import pytest
import datetime

from django.urls import reverse

from tenant_schemas.utils import tenant_context
from rest_framework import status

from apps.customer.tests.factories import CustomerFactory
from apps.purchase import models as purchase_models
from apps.purchase.tests import factories


@pytest.mark.django_db
class TestProductAPI:
    def test_forbidden(self, member1, client1, customeruser1):
        response = client1.get(reverse('purchase-product-list'))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_product_list(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            factories.ProductFactory(
                name='test',
            )

        response = client1.get(reverse('purchase-product-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'test'

    def test_product_list_search(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            factories.ProductFactory(
                name='test',
            )

            factories.ProductFactory(
                name='nog een product',
            )

        response = client1.get('%s?q=nog' % reverse('purchase-product-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'nog een product'

    def test_product_total_sales(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product1 = factories.ProductFactory(
                name='test product 1'
            )

            product2 = factories.ProductFactory(
                name='test product 2'
            )

            location = factories.StockLocationFactory()

        d = datetime.datetime.today().date()
        d += datetime.timedelta(days=1)

        if d.weekday() == 5:
            d += datetime.timedelta(days=2)

        if d.weekday() == 6:
            d += datetime.timedelta(days=1)

        response = client1.post(reverse('order-list'), {
            'customer_id': '1234',
            'start_date': d,
            'end_date': d,
            'order_type': 'sales',
            'orderlines': [
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 10,
                    'price_purchase': 1.00,
                    'price_selling': 3.50
                },
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 10,
                    'price_purchase': 1.00,
                    'price_selling': 3.50
                },
                {
                    'product_relation': product2.id,
                    'location_relation': location.id,
                    'amount': 5,
                    'price_purchase': 0.50,
                    'price_selling': 1.50
                }
            ]
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        response = client1.get(reverse('purchase-product-total-sales'))

        assert response.status_code == status.HTTP_200_OK

        assert response.data['result'][0]['product_name'] == product1.name
        assert response.data['result'][0]['amount'] == 20

        assert response.data['result'][1]['product_name'] == product2.name
        assert response.data['result'][1]['amount'] == 5

    def test_product_total_sales_per_customer(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product1 = factories.ProductFactory(
                name='test product 1'
            )

            product2 = factories.ProductFactory(
                name='test product 2'
            )

            location = factories.StockLocationFactory()

        d = datetime.datetime.today().date()
        d += datetime.timedelta(days=1)

        if d.weekday() == 5:
            d += datetime.timedelta(days=2)

        if d.weekday() == 6:
            d += datetime.timedelta(days=1)

        response = client1.post(reverse('order-list'), {
            'customer_id': '1234',
            'order_name': 'customer 1',
            'start_date': d,
            'end_date': d,
            'order_type': 'sales',
            'orderlines': [
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 10,
                    'price_purchase': 1.00,
                    'price_selling': 3.50
                },
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 10,
                    'price_purchase': 1.00,
                    'price_selling': 3.50
                },
                {
                    'product_relation': product2.id,
                    'location_relation': location.id,
                    'amount': 5,
                    'price_purchase': 0.50,
                    'price_selling': 1.50
                }
            ]
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        response = client1.post(reverse('order-list'), {
            'customer_id': '4321',
            'order_name': 'customer 2',
            'start_date': d,
            'end_date': d,
            'order_type': 'sales',
            'orderlines': [
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 2,
                    'price_purchase': 1.00,
                    'price_selling': 3.50
                },
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 2,
                    'price_purchase': 1.00,
                    'price_selling': 3.50
                },
                {
                    'product_relation': product2.id,
                    'location_relation': location.id,
                    'amount': 1,
                    'price_purchase': 0.50,
                    'price_selling': 1.50
                }
            ]
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        response = client1.get(reverse('purchase-product-total-sales-per-customer'))

        assert response.status_code == status.HTTP_200_OK

        assert response.data['result'][0]['order_name'] == 'customer 1'
        assert response.data['result'][0]['amount'] == 25

        assert response.data['result'][1]['order_name'] == 'customer 2'
        assert response.data['result'][1]['amount'] == 5

    def test_product_total_sales_per_product_customer(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product1 = factories.ProductFactory(
                name='test product 1'
            )

            product2 = factories.ProductFactory(
                name='test product 2'
            )

            location = factories.StockLocationFactory()

        d = datetime.datetime.today().date()
        d += datetime.timedelta(days=1)

        if d.weekday() == 5:
            d += datetime.timedelta(days=2)

        if d.weekday() == 6:
            d += datetime.timedelta(days=1)

        response = client1.post(reverse('order-list'), {
            'customer_id': '1234',
            'order_name': 'customer 1',
            'start_date': d,
            'end_date': d,
            'order_type': 'sales',
            'orderlines': [
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 10,
                    'price_purchase': 1.00,
                    'price_selling': 13.50
                },
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 10,
                    'price_purchase': 1.00,
                    'price_selling': 13.50
                },
                {
                    'product_relation': product2.id,
                    'location_relation': location.id,
                    'amount': 5,
                    'price_purchase': 0.50,
                    'price_selling': 1.50
                }
            ]
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        response = client1.post(reverse('order-list'), {
            'customer_id': '4321',
            'order_name': 'customer 2',
            'start_date': d,
            'end_date': d,
            'order_type': 'sales',
            'orderlines': [
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 2,
                    'price_purchase': 1.00,
                    'price_selling': 3.50
                },
                {
                    'product_relation': product1.id,
                    'location_relation': location.id,
                    'amount': 2,
                    'price_purchase': 1.00,
                    'price_selling': 3.50
                },
                {
                    'product_relation': product2.id,
                    'location_relation': location.id,
                    'amount': 1,
                    'price_purchase': 0.50,
                    'price_selling': 3.50
                }
            ]
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        response = client1.get(reverse('purchase-product-total-sales-per-product-customer'))

        assert response.status_code == status.HTTP_200_OK

        assert response.data['result'][0]['product_name'] == product1.name
        assert response.data['result'][0]['order_name'] == 'customer 1'
        assert response.data['result'][0]['amount'] == 20

        assert response.data['result'][1]['product_name'] == product1.name
        assert response.data['result'][1]['order_name'] == 'customer 2'
        assert response.data['result'][1]['amount'] == 4

        assert response.data['result'][2]['product_name'] == product2.name
        assert response.data['result'][2]['order_name'] == 'customer 2'
        assert response.data['result'][2]['amount'] == 1

        assert response.data['result'][3]['product_name'] == product2.name
        assert response.data['result'][3]['order_name'] == 'customer 1'
        assert response.data['result'][3]['amount'] == 5

    def test_product_autocomplete(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            factories.ProductFactory(
                name='test_product_autocomplete'
            )
            factories.ProductFactory(
                name='bla'
            )

        response = client1.get('%s?q=test_product_autocomplete' % reverse('purchase-product-autocomplete'))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'test_product_autocomplete'

    def test_product_create(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)

        response = client1.post(reverse('purchase-product-list'), {
            'name': 'test name',
            'identifier': 'bla',
            'price_purchase': '0.00',
            'price_selling': '0.00',
            'price_selling_alt': '0.00',
            'price_purchase_ex': '0.00',
            'price_selling_ex': '0.00',
            'price_selling_alt_ex': '0.00',
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'test name'

        response = client1.get(reverse('purchase-product-list'))
        assert response.data['count'] == 1

    def test_product_retrieve(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product = factories.ProductFactory(
                name='test',
                identifier='1234',
            )

        response = client1.get(reverse('purchase-product-detail', kwargs={'pk': product.id}))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['identifier'] == '1234'

    def test_product_update(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product = factories.ProductFactory(
                name='test',
                identifier='bla',
            )

        response = client1.put(reverse('purchase-product-detail', kwargs={'pk': product.id}), {
            'name': 'test name',
            'identifier': 'bla',
            'price_purchase': '0.00',
            'price_selling': '0.00',
            'price_selling_alt': '0.00',
            'price_purchase_ex': '0.00',
            'price_selling_ex': '0.00',
            'price_selling_alt_ex': '0.00',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'test name'

    def test_product_delete(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product = factories.ProductFactory(
                name='test'
            )

        response = client1.delete(reverse('purchase-product-detail', kwargs={'pk': product.pk}), format='json')

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestSupplierAPI:
    def test_forbidden(self, member1, client1, customeruser1):
        with tenant_context(member1.tenant):
            client1.force_login(customeruser1)

        response = client1.get(reverse('supplier-list'))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_supplier_list(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            factories.SupplierFactory(
                name='test',
            )

        response = client1.get(reverse('supplier-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'test'

    def test_supplier_list_search(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            factories.SupplierFactory(
                name='test',
            )

            factories.SupplierFactory(
                name='nog een supplier',
            )

        response = client1.get('%s?q=nog' % reverse('supplier-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'nog een supplier'

    def test_supplier_autocomplete(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            factories.SupplierFactory(
                name='test'
            )
            factories.SupplierFactory(
                name='bla'
            )

        response = client1.get('%s?q=test' % reverse('supplier-autocomplete'))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'test'

    def test_supplier_create(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)

        response = client1.post(reverse('supplier-list'), {
            'name': 'test name',
            'address': 'teststraat 34',
            'postal': '2531DS',
            'city': 'test city',
            'identifier': 'bla',
            'country_code': 'NL',
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'test name'

        response = client1.get(reverse('supplier-list'))
        assert response.data['count'] == 1

    def test_supplier_retrieve(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product = factories.SupplierFactory(
                name='test',
                identifier='1234',
            )

        response = client1.get(reverse('supplier-detail', kwargs={'pk': product.id}))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['identifier'] == '1234'

    def test_supplier_update(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            supplier = factories.SupplierFactory(
                name='test',
                identifier='bla',
            )

        response = client1.put(reverse('supplier-detail', kwargs={'pk': supplier.id}), {
            'name': 'test name',
            'address': 'teststraat 34',
            'postal': '2531DS',
            'city': 'test city',
            'identifier': 'bla',
            'country_code': 'NL',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'test name'

    def test_supplier_delete(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            supplier = factories.SupplierFactory(
                name='test'
            )

        response = client1.delete(reverse('supplier-detail', kwargs={'pk': supplier.pk}), format='json')

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestStockLocationAPI:
    def test_forbidden(self, member1, client1, customeruser1):
        with tenant_context(member1.tenant):
            client1.force_login(customeruser1)

        response = client1.get(reverse('stocklocation-list'))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_stocklocation_list(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            factories.StockLocationFactory(
                name='test',
            )

        response = client1.get(reverse('stocklocation-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'test'

    def test_stocklocation_list_search(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            factories.StockLocationFactory(
                name='test',
            )

            factories.StockLocationFactory(
                name='nog een location',
            )

        response = client1.get('%s?q=nog' % reverse('stocklocation-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'nog een location'

    def test_stocklocation_create(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)

        response = client1.post(reverse('stocklocation-list'), {
            'name': 'test name',
            'identifier': 'bla',
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'test name'

        response = client1.get(reverse('stocklocation-list'))
        assert response.data['count'] == 1

    def test_stocklocation_retrieve(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            stocklocation = factories.StockLocationFactory(
                name='test',
                identifier='1234',
            )

        response = client1.get(reverse('stocklocation-detail', kwargs={'pk': stocklocation.id}))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['identifier'] == '1234'

    def test_stocklocation_update(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            stocklocation = factories.StockLocationFactory(
                name='test',
                identifier='bla',
            )

        response = client1.put(reverse('stocklocation-detail', kwargs={'pk': stocklocation.id}), {
            'name': 'test name',
            'identifier': 'bla',
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'test name'

    def test_stocklocation_delete(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            stocklocation = factories.StockLocationFactory(
                name='test'
            )

        response = client1.delete(reverse('stocklocation-detail', kwargs={'pk': stocklocation.id}), format='json')

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestStockMutationsAPI:
    def test_forbidden(self, member1, client1, customeruser1):
        with tenant_context(member1.tenant):
            client1.force_login(customeruser1)

        response = client1.get(reverse('stockmutation-list'))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_stockmutation_list(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            factories.StockMutationFactory()

        response = client1.get(reverse('stockmutation-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_stockmutation_create_sales(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product = factories.ProductFactory()
            location = factories.StockLocationFactory()
            customer = CustomerFactory()

        response = client1.post(reverse('stockmutation-list'), {
            'product': product.id,
            'fromLocation': location.id,
            'mutationType': 'sales',
            'amount': 10,
            'customer': customer.id,
        })

        assert response.status_code == status.HTTP_201_CREATED

        # should result in one mutation row
        response = client1.get(reverse('stockmutation-list'))
        assert response.data['count'] == 1

        # check inventory
        inventory = purchase_models.StockLocationInventory.objects.get(
            product=product,
            location=location
        )

        assert inventory.amount == -10

    def test_stockmutation_create_purchase(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product = factories.ProductFactory()
            location = factories.StockLocationFactory()
            customer = CustomerFactory()

        response = client1.post(reverse('stockmutation-list'), {
            'product': product.id,
            'toLocation': location.id,
            'mutationType': 'purchase',
            'amount': 10,
            'customer': customer.id,
        })

        assert response.status_code == status.HTTP_201_CREATED

        # should result in one mutation row
        response = client1.get(reverse('stockmutation-list'))
        assert response.data['count'] == 1

        # check inventory
        inventory = purchase_models.StockLocationInventory.objects.get(
            product=product,
            location=location
        )

        assert inventory.amount == 10

    def test_stockmutation_create_purchase_amount_zero(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product = factories.ProductFactory()
            location = factories.StockLocationFactory()
            customer = CustomerFactory()

        response = client1.post(reverse('stockmutation-list'), {
            'product': product.id,
            'toLocation': location.id,
            'mutationType': 'purchase',
            'amount': 0,
            'customer': customer.id,
        })

        assert response.status_code == status.HTTP_201_CREATED

        # should result in one mutation row
        response = client1.get(reverse('stockmutation-list'))
        assert response.data['count'] == 1

        # check inventory
        inventory = purchase_models.StockLocationInventory.objects.get(
            product=product,
            location=location
        )

        assert inventory.amount == 0

    def test_stockmutation_create_move(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product = factories.ProductFactory()
            fromLocation = factories.StockLocationFactory()
            toLocation = factories.StockLocationFactory()
            customer = CustomerFactory()

        response = client1.post(reverse('stockmutation-list'), {
            'product': product.id,
            'toLocation': toLocation.id,
            'fromLocation': fromLocation.id,
            'mutationType': 'move',
            'amount': 10,
            'customer': customer.id,
        })

        assert response.status_code == status.HTTP_201_CREATED

        # should result in one mutation row
        response = client1.get(reverse('stockmutation-list'))
        assert response.data['count'] == 1

        # check inventory
        from_inventory = purchase_models.StockLocationInventory.objects.get(
            product=product,
            location=fromLocation
        )

        assert from_inventory.amount == -10

        to_inventory = purchase_models.StockLocationInventory.objects.get(
            product=product,
            location=toLocation
        )

        assert to_inventory.amount == 10

    def test_stockmutation_retrieve(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            stockmutation = factories.StockMutationFactory()

        response = client1.get(reverse('stockmutation-detail', kwargs={'pk': stockmutation.id}))

        assert response.status_code == status.HTTP_200_OK

    def test_stockmutation_delete(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            stockmutation = factories.StockMutationFactory()

        response = client1.delete(reverse('stockmutation-detail', kwargs={'pk': stockmutation.id}), format='json')

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestStockmutationInventoryAPI:
    def test_forbidden(self, member1, client1, customeruser1):
        with tenant_context(member1.tenant):
            client1.force_login(customeruser1)

        response = client1.get(reverse('stocklocationinventory-list'))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_stocklocationinventory_list(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product = factories.ProductFactory()
            location = factories.StockLocationFactory()

        factories.StockLocationInventoryFactory(
            product=product,
            location=location,
            amount=5,
        )

        response = client1.get(reverse('stocklocationinventory-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['amount'] == 5

    def test_stocklocationinventory_list_search(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product1 = factories.ProductFactory(
                name='test product'
            )

            location1 = factories.StockLocationFactory()

            factories.StockLocationInventoryFactory(
                product=product1,
                location=location1,
                amount=5,
            )

            product2 = factories.ProductFactory(
                name='nog een product'
            )

            location2 = factories.StockLocationFactory()

            factories.StockLocationInventoryFactory(
                product=product2,
                location=location2,
                amount=5,
            )

        response = client1.get('%s?q=test' % reverse('stocklocationinventory-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['amount'] == 5

    def test_stocklocationinventory_list_filter(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            product1 = factories.ProductFactory(
                name='test product'
            )

            location1 = factories.StockLocationFactory()

            factories.StockLocationInventoryFactory(
                product=product1,
                location=location1,
                amount=5,
            )

            product2 = factories.ProductFactory(
                name='nog een product'
            )

            location2 = factories.StockLocationFactory()

            factories.StockLocationInventoryFactory(
                product=product2,
                location=location2,
                amount=5,
            )

        response = client1.get('%s?location=%d' % (reverse('stocklocationinventory-list'), location1.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['amount'] == 5

    def test_stocklocationinventory_list_product_types(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            prod1 = factories.ProductFactory(
                product_type='type 1'
            )

            prod2 = factories.ProductFactory(
                product_type='type 2'
            )

            prod3 = factories.ProductFactory(
                product_type='type 3'
            )

            loc1 = factories.StockLocationFactory()

            factories.StockLocationInventoryFactory(
                product=prod1,
                location=loc1,
                amount=5,
            )

            factories.StockLocationInventoryFactory(
                product=prod1,
                location=loc1,
                amount=15,
            )

            factories.StockLocationInventoryFactory(
                product=prod2,
                location=loc1,
                amount=5,
            )

            factories.StockLocationInventoryFactory(
                product=prod3,
                location=loc1,
                amount=5,
            )

        url = '%s?location_id=%s' % (reverse('stocklocationinventory-list-product-types'), loc1.id)
        response = client1.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_stocklocationinventory_create(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            prod1 = factories.ProductFactory()
            loc1 = factories.StockLocationFactory()

        response = client1.post(reverse('stocklocationinventory-list'), {
            'product': prod1.id,
            'location': loc1.id,
            'amount': 5,
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['amount'] == 5

        response = client1.get(reverse('stocklocationinventory-list'))
        assert response.data['count'] == 1

    def test_stocklocationinventory_retrieve(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            prod1 = factories.ProductFactory()
            loc1 = factories.StockLocationFactory()

        inventory = factories.StockLocationInventoryFactory(
            product=prod1,
            location=loc1,
            amount=5,
        )

        response = client1.get(reverse('stocklocationinventory-detail', kwargs={'pk': inventory.id}))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['amount'] == 5

    def test_stocklocationinventory_update(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            prod1 = factories.ProductFactory()
            loc1 = factories.StockLocationFactory()

            inventory = factories.StockLocationInventoryFactory(
                product=prod1,
                location=loc1,
                amount=5,
            )

        response = client1.put(reverse('stocklocationinventory-detail', kwargs={'pk': inventory.id}), {
            'product': prod1.id,
            'location': loc1.id,
            'amount': 15,
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['amount'] == 15

    def test_stocklocationinventory_delete(self, member1, client1, planninguser1):
        with tenant_context(member1.tenant):
            client1.force_login(planninguser1)
            prod1 = factories.ProductFactory()
            loc1 = factories.StockLocationFactory()

            inventory = factories.StockLocationInventoryFactory(
                product=prod1,
                location=loc1,
                amount=5,
            )

        url = reverse('stocklocationinventory-detail', kwargs={'pk': inventory.id})
        response = client1.delete(url, format='json')

        assert response.status_code == status.HTTP_204_NO_CONTENT
