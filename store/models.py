from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db.models.signals import post_save
from uppsell.workflow import Workflow, BadTransition, pre_transition_handler, \
        post_transition_handler

ADDRESS_TYPES = ( # (type, description)
    ('billing', 'Billing'),
    ('shipping', 'Shipping'),
)
ORDER_STATES = ( # (order_state, description)
    ('init', 'Initialized'),
    ('pending_payment', 'Pending Payment'),
    ('processing', 'Processing'),
    ('shipping', 'Shipping'),
    ('completed', 'Completed'),
    ('cancellation_requested', 'Cancellation Requested'),
    ('canceled', 'Canceled'),
    ('hold', 'On Hold'),
)
ORDER_TRANSITIONS = ( # (order_transition, description)
    ('open', 'Open'),
    ('capture', 'Capture payment'),
    ('ship', 'Ship'),
    ('receive', 'Receive'),
    ('cancel', 'Cancel'),
    ('deny', 'Deny cancelation'),
    ('process', 'Process order'),
)
ORDER_WORKFLOW = ( # (transition, state_before, state_after)
    ('open', 'init', 'pending_payment'),
    ('capture', 'pending_payment', 'processing'),
    ('cancel', 'pending_payment', 'canceled'),
    ('cancel', 'processing', 'canceled'),
    ('ship', 'processing', 'shipping'),
    ('receive', 'shipping', 'completed'),
    ('process', 'processing', 'completed'),
    ('cancel', 'completed', 'cancellation_requested'),
    ('deny', 'cancellation_requested', 'completed'),
    ('cancel', 'cancellation_requested', 'canceled'),
)
PAYMENT_STATES = ( # (payment_state, description)
    ('init', 'Initialized'),
    ('pending', 'Pending Payment'),
    ('authorized', 'Authorized'),
    ('captured', 'Captured'),
    ('canceled', 'Canceled'),
    ('declined', 'Declined'),
    ('expired', 'Expired'),
    ('disputed', 'Disputed'),
    ('charged_back', 'Charge Back'),
    ('refunded', 'Refunded'),
)
PAYMENT_TRANSITIONS = ( # (payment_transition, description)
    ('start', 'Start'),
    ('authorize', 'Authorize'),
    ('capture', 'Capture'),
    ('decline', 'Decline'),
    ('expire', 'Expire'),
    ('cancel', 'Cancel'),
    ('dispute', 'Dispute'),
    ('refuse', 'Refuse dispute'),
    ('chargeback', 'Chargeback'),
    ('refund', 'Refund'),
)
PAYMENT_WORKFLOW = ( # (transition, state_before, state_after)
    ('start', 'init', 'pending'),
    ('capture', 'pending', 'captured'),
    ('authorize', 'pending', 'authorized'),
    ('capture', 'authorized', 'captured'),
    ('decline', 'pending', 'declined'),
    ('cancel', 'pending', 'canceled'),
    ('expire', 'pending', 'expired'),
    ('expire', 'authorized', 'expired'),
    ('dispute', 'capture', 'disputed'),
    ('refuse', 'disputed', 'capture'),
    ('chargeback', 'disputed', 'charged_back'),
    ('refund', 'capture', 'refunded'),
)
PRODUCT_STATES = ( # (product_state, description)
    ('init', 'Init'),
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('hidden', 'Hidden')
)
PRODUCT_TRANSITIONS = ( # (product_transition, description)
    ('create', 'Create'),
    ('activate', 'Activate'),
    ('deactivate', 'Deactivate'),
    ('hide', 'Hide'),
    ('show', 'Show'),
)
PRODUCT_TRANSITIONS = ( # (transition, state_before, state_after)
    ('create', 'init', 'active'),
    ('activate', 'inactive', 'active'),
    ('hide', 'inactive', 'hidden'),
    ('hide', 'active', 'hidden'),
    ('show', 'hidden', 'active'),
    ('deactivate', 'hidden', 'inactive'),
    ('deactivate', 'active', 'inactive'),
)
ORDER_EVENT_TYPES = (
    ('order', 'Order Event'),
    ('payment', 'Payment  Event'),
    ('fraud', 'Fraud Event'),
)

class Customer(models.Model):
    username = models.CharField("Username", max_length=30, unique=True)
    first_name = models.CharField('First name', max_length=30, blank=True)
    last_name = models.CharField('Last name', max_length=30, blank=True)
    email = models.EmailField('Email address', blank=True)
    created_at = models.DateTimeField('Date Added', auto_now_add=True)
    last_logged_in_at = models.DateTimeField('Last logged in')
    
    def __unicode__(self):
        return self.username

class Address(models.Model):
    type = models.CharField("Address type", max_length=10, choices=ADDRESS_TYPES)
    customer = models.ForeignKey(Customer)
    line1 = models.CharField("Address line 1", max_length=255)
    line2 = models.CharField("Address line 2", max_length=255)
    line3 = models.CharField("Address line 3", max_length=255)
    city = models.CharField("City", max_length=255)
    zip = models.CharField("Zip or Post Code", max_length=255)
    province= models.CharField("State, Province or County", max_length=255)
    country = models.CharField("Country", max_length=255)
    country_code = models.CharField("Country", max_length=3)
    other = models.CharField("Other Details", max_length=255)
    created_at = models.DateTimeField('Date Added', auto_now_add=True)
    last_used = models.DateTimeField('Date Added', blank=True, null=True)

class LinkedAccountType(models.Model):
    type = models.CharField("Account Type", max_length=32)

class LinkedAccount(models.Model):
    type = models.ForeignKey(LinkedAccountType)
    customer = models.ForeignKey(Customer)
    account_id = models.CharField("Linked Account ID", max_length=255)
    linked_at = models.DateTimeField('Date Linked', auto_now_add=True)
    updated_at = models.DateTimeField('Date Modifeid',  auto_now=True)

class Store(models.Model):
    code = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    default_lang = models.CharField(max_length=3)
    default_currency = models.CharField(max_length=3)
    sales_tax_rate = models.FloatField()
    created_at = models.DateTimeField('date created', auto_now_add=True)
    updated_at = models.DateTimeField('date modifeid',  auto_now=True)
    
    def __unicode__(self):
        return self.name

class ProductGroup(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class Product(models.Model):
    group = models.ForeignKey(ProductGroup)
    sku = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200)
    description = models.CharField(max_length=10000)
    stock_units = models.FloatField()
    created_at = models.DateTimeField('date created', auto_now_add=True)
    updated_at = models.DateTimeField('date modified', auto_now=True)
    
    def __unicode__(self):
        return self.name

class ProductCode(models.Model):
    """
    Different products have different identifiers, such as ISBN (books),
    ISSN (seriels), ICCID (SIM cards), EAN (International Article Number)...
    """
    type = models.CharField(max_length=20)
    product = models.ForeignKey(ProductGroup)
    code = models.CharField(max_length=255)
    def __unicode__(self):
        return u"<%s %s>" % (self.type, self.code)

class Listing(models.Model):
    store = models.ForeignKey(Store)
    product = models.ForeignKey(Product)
    state = models.CharField(max_length=10, choices=PRODUCT_STATES)
    sales_tax_rate = models.FloatField(null=True)
    name = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=200, blank=True)
    subtitle = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=10000, blank=True)
    
    def __unicode__(self):
        return self.product.name

class Cart(models.Model):
    store = models.ForeignKey(Store)
    customer = models.ForeignKey(Listing)
    created_at = models.DateTimeField('date created', auto_now_add=True)
    updated_at = models.DateTimeField('date modified', auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart)
    product = models.ForeignKey(Listing)
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    
    store = models.ForeignKey(Store)
    customer = models.ForeignKey(Customer)
    
    order_state = models.CharField(max_length=30, choices=ORDER_STATES, default="init")
    payment_state = models.CharField(max_length=30, choices=PAYMENT_STATES, default="init")
    fraud_state = models.CharField(max_length=30)
    
    transaction_id = models.CharField(max_length=200, blank=True)
    shipping_address = models.ForeignKey(Address, related_name="shipping_address", null=True, blank=True)
    billing_address = models.ForeignKey(Address, related_name="billing_address", null=True, blank=True)

    order_total = models.DecimalField(max_digits=8, decimal_places=2)
    order_shipping_total = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3)

    payment_made_ts = models.DateTimeField('timestamp payment captured', null=True, blank=True)
    created_at = models.DateTimeField('timestamp created', auto_now_add=True)
    updated_at = models.DateTimeField('timestamp modifeid', auto_now=True)
    
    _order_workflow = None
    _payment_workflow = None

    def save(self, *args, **kwargs):
        super(Order, self).save(*args, **kwargs)
        if self.order_state == "init":
            OrderEvent.objects.create(order=self, action_type="order", event="open")
    
    @property
    def order_workflow(self, transitions = None):
        if self._order_workflow is None:
            self._order_workflow = Workflow(self, u"order_state", ORDER_WORKFLOW)
        return self._order_workflow
    
    @property
    def payment_workflow(self, transitions = None):
        if self._payment_workflow is None:
            self._payment_workflow = Workflow(self, u"payment_state", PAYMENT_WORKFLOW)
        return self._payment_workflow
    
    def event(self, event_type, event):
        OrderEvent.objects.create(order=self,
                action_type=event_type, event=event)

class OrderItem(models.Model):
    order = models.ForeignKey(Order)
    product = models.ForeignKey(Listing)
    quantity = models.PositiveIntegerField(default=1)

class OrderEvent(models.Model):
    order = models.ForeignKey(Order)
    action_type = models.CharField(max_length=30, choices=ORDER_EVENT_TYPES)
    event = models.CharField(max_length=30)
    state_before = models.CharField(max_length=30)
    state_after = models.CharField(max_length=30)
    comment = models.CharField(max_length=2000, blank=True)
    created_at = models.DateTimeField('Event timestamp', auto_now_add=True)

    def save(self, *args, **kwargs):
        try:
            if self.action_type == 'order':
                self.state_before = self.order.order_state
                self.order.order_workflow.do(self.event)
                self.state_after = self.order.order_state
            if self.action_type == 'payment':
                self.state_before = self.order.payment_state
                self.order.payment_workflow.do(self.event)
                self.state_after = self.order.payment_state
        except BadTransition:
            raise
        self.order.save()
        super(OrderEvent, self).save(*args, **kwargs)

class Invoice(models.Model):
    order_id = models.IntegerField(unique=True) # non-relational
    store_id = models.IntegerField() # non-relational
    product_id = models.IntegerField() # non-relational
    psp_id = models.IntegerField() # non-relational
    
    psp_type = models.CharField(max_length=200)
    user_jid = models.CharField(max_length=200)
    transaction_id = models.CharField(max_length=200)
    psp_type = models.CharField(max_length=200)
    quantity = models.IntegerField(default=0)
    order_total = models.DecimalField(max_digits=8, decimal_places=2)
    order_shipping_total = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3)

    user_fullname = models.CharField(max_length=1000)
    shipping_address = models.CharField(max_length=1000)
    billing_address = models.CharField(max_length=1000)
    user_mobile_msisdn = models.CharField(max_length=200)
    user_email = models.CharField(max_length=200)
    psp_response_code = models.CharField(max_length=200)
    psp_response_text = models.CharField(max_length=10000)
    
    payment_made_ts = models.DateTimeField('timestamp payment captured')
    created_at = models.DateTimeField('timestamp created', auto_now_add=True)


