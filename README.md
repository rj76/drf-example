drf-example
===========

django `purchase` module of my24service, to give an idea of how to use drf with models in a project.

The view creates the following endpoints:

```
/purchase-device/index/	apps.purchase.views.PurchaseDeviceIndex	purchase-device-index
/purchase/index/	apps.purchase.views.PurchaseIndex	purchase-index
/purchase/product/	apps.purchase.views.ProductViewset	purchase-product-list
/purchase/product/<pk>/	apps.purchase.views.ProductViewset	purchase-product-detail
/purchase/product/autocomplete/	apps.purchase.views.ProductViewset	purchase-product-autocomplete
/purchase/product/total_sales/	apps.purchase.views.ProductViewset	purchase-product-total-sales
/purchase/product/total_sales_per_customer/	apps.purchase.views.ProductViewset	purchase-product-total-sales-per-customer
/purchase/product/total_sales_per_product_customer/	apps.purchase.views.ProductViewset	purchase-product-total-sales-per-product-customer
/purchase/stock-location-inventory/	apps.purchase.views.StockLocationInventoryViewset	stocklocationinventory-list
/purchase/stock-location-inventory/<pk>/	apps.purchase.views.StockLocationInventoryViewset	stocklocationinventory-detail
/purchase/stock-location-inventory/list_full/	apps.purchase.views.StockLocationInventoryViewset	stocklocationinventory-list-full
/purchase/stock-location-inventory/list_product_types/	apps.purchase.views.StockLocationInventoryViewset	stocklocationinventory-list-product-types
/purchase/stock-location/	apps.purchase.views.StockLocationViewset	stocklocation-list
/purchase/stock-location/<pk>/	apps.purchase.views.StockLocationViewset	stocklocation-detail
/purchase/stock-mutation/	apps.purchase.views.StockMutationViewset	stockmutation-list
/purchase/stock-mutation/<pk>/	apps.purchase.views.StockMutationViewset	stockmutation-detail
/purchase/supplier/	apps.purchase.views.SupplierViewset	supplier-list
/purchase/supplier/<pk>/	apps.purchase.views.SupplierViewset	supplier-detail
/purchase/supplier/autocomplete/	apps.purchase.views.SupplierViewset	supplier-autocomplete
/purchase/total_sales_per_customer_export/	apps.purchase.views.ExportXlsView	purchase-total-sales-per-customer-export
```
