from django.db import models, connection
from django.utils.translation import ugettext_lazy as _

from djmoney.models.fields import MoneyField
from django_extensions.db.models import TimeStampedModel

from apps.core.models import My24ModelFieldsMixin, LatLonModelMixin

from . import managers


def _image_upload_location(instance, filename):
    filename = filename.replace(' ', '_').replace('..', '').replace('/', '').replace('\\', '')
    return 'purchase-images/%s/%s' % (connection.tenant.member.companycode, filename)


class Product(TimeStampedModel, My24ModelFieldsMixin, models.Model):
    identifier = models.CharField(_('Identifier'), max_length=255, null=True, blank=True)
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True)
    name_short = models.CharField(_('Name'), max_length=255, null=True, blank=True)
    search_name = models.CharField(_('Search name'), max_length=255, null=True, blank=True)
    unit = models.CharField(_('Unit'), max_length=100, null=True, blank=True)
    supplier = models.CharField(_('Supplier'), max_length=100, null=True, blank=True)
    product_type = models.CharField(max_length=100, null=True, blank=True)

    price_purchase = MoneyField(max_digits=10, decimal_places=2, default_currency='EUR', default=0.00)
    price_selling = MoneyField(max_digits=10, decimal_places=2, default_currency='EUR', default=0.00)
    price_selling_alt = MoneyField(max_digits=10, decimal_places=2, default_currency='EUR', default=0.00)

    price_purchase_ex = MoneyField(max_digits=10, decimal_places=2, default_currency='EUR', default=0.00)
    price_selling_ex = MoneyField(max_digits=10, decimal_places=2, default_currency='EUR', default=0.00)
    price_selling_alt_ex = MoneyField(max_digits=10, decimal_places=2, default_currency='EUR', default=0.00)

    tax_percentage = models.DecimalField(_('Tax'), max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(_('Image'), max_length=100, blank=True, null=True, upload_to=_image_upload_location)

    objects = managers.ProductManager()

    class Meta:
        ordering = ['name']

    def show_name(self):
        if self.name and self.name_short:
            return '%s (%s)' % (self.name_short, self.name)

        if self.name and not self.name_short:
            return self.name

        if self.name_short and not self.name:
            return self.name_short

    def __str__(self):
        if self.name and self.identifier:
            return '%s - %s' % (self.name, self.identifier)

        return self.name


class Supplier(TimeStampedModel, LatLonModelMixin, My24ModelFieldsMixin):
    identifier = models.CharField(_('customer ID'), max_length=100, blank=True, null=True)
    name = models.CharField(_('(Company) name'), max_length=255, null=True, blank=True)
    address = models.CharField(_('Address'), max_length=255, null=True, blank=True)
    postal = models.CharField(_('Postal'), max_length=20, null=True, blank=True)
    state = models.CharField(_('State'), max_length=80, null=True, blank=True)
    country_code = models.CharField(_('Country'), max_length=2, default='NL')
    contact = models.TextField(_('Contact'), null=True, blank=True)
    city = models.CharField(_('City'), max_length=255, null=True, blank=True)
    tel = models.CharField(_('Tel'), max_length=100, null=True, blank=True)
    email = models.CharField(_('Email'), max_length=150, null=True, blank=True)
    mobile = models.CharField(_('Mobile'), max_length=100, null=True, blank=True)
    remarks = models.TextField(_('Remarks'), null=True, blank=True)
    lon = models.FloatField(_('Longitute'), null=True, blank=True)
    lat = models.FloatField(_('Latitude'), null=True, blank=True)

    objects = managers.SupplierManager()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        unique_together = ('identifier', 'name', 'address', 'city', 'postal', 'country_code')

    def save(self, **kwargs):
        if not self.lon or not self.lat:
            self.set_lat_lon()

        self.country_code = self.country_code.upper()

        return super(Supplier, self).save(**kwargs)

    def get_update_model_fields(self):
        exclude = ['id']
        return [fld for fld in self.get_model_fields() if fld not in exclude]

    def get_text(self):
        return "%s\n%s\n%s-%s %s" % (
            self.name,
            self.address,
            self.country_code, self.postal, self.city
        )


class StockLocation(TimeStampedModel, My24ModelFieldsMixin, models.Model):
    identifier = models.CharField(_('Identifier'), max_length=255, null=True, blank=True)
    name = models.CharField(_('Name'), max_length=255, null=True, blank=True)

    objects = managers.StockLocationManager()

    class Meta:
        ordering = ['name']

    def __str__(self):
        if self.name and self.identifier:
            return '%s - %s' % (self.name, self.identifier)

        return self.name


class StockLocationInventory(TimeStampedModel, My24ModelFieldsMixin, models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)
    amount = models.IntegerField(_('Amount'))

    objects = managers.StockLocationInventoryManager()

    class Meta:
        ordering = ['location__name']

    def __str__(self):
        return '%s %s %s' % (self.product, self.location, self.amount)


class StockMutation(TimeStampedModel, My24ModelFieldsMixin, models.Model):
    TYPES = (
        ('sales', 'sales'),
        ('purchase', 'purchase'),
        ('move', 'move'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    fromLocation = models.ForeignKey(StockLocation, on_delete=models.CASCADE,
                                     null=True, blank=True, related_name='from_mutations')
    toLocation = models.ForeignKey(StockLocation, on_delete=models.CASCADE,
                                   null=True, blank=True, related_name='to_mutations')
    mutationType = models.CharField(_('Mutation type'), max_length=100, choices=TYPES, default='purchase')
    amount = models.IntegerField(_('Amount'))

    objects = managers.StockLocationMutationManager()

    def save(self, *args, **kwargs):
        super().save(**kwargs)

        if self.mutationType == 'sales':
            self.remove_from_stocklocation(self.product, self.fromLocation, self.amount)

        if self.mutationType == 'purchase':
            self.add_to_stocklocation(self.product, self.toLocation, self.amount)

        if self.mutationType == 'move':
            self.add_to_stocklocation(self.product, self.toLocation, self.amount)
            self.remove_from_stocklocation(self.product, self.fromLocation, self.amount)

    def add_to_stocklocation(self, product, location, amount):
        try:
            stocklocation_inventory = StockLocationInventory.objects.get(location=location, product=product)
            stocklocation_inventory.amount += amount
            stocklocation_inventory.save()
        except StockLocationInventory.DoesNotExist:
            stocklocation_inventory = StockLocationInventory(
                location=location,
                product=product,
                amount=amount
            )
            stocklocation_inventory.save()

    def remove_from_stocklocation(self, product, location, amount):
        try:
            stocklocation_inventory = StockLocationInventory.objects.get(location=location, product=product)
            stocklocation_inventory.amount -= amount
            stocklocation_inventory.save()
        except StockLocationInventory.DoesNotExist:
            stocklocation_inventory = StockLocationInventory(
                location=location,
                product=product,
                amount=amount * -1
            )
            stocklocation_inventory.save()

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return '%s %s' % (self.product, self.amount)
