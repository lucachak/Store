from django.db import models
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.conf import settings 
from django.urls import reverse
import Core.billing 
# Create your models here.

User = settings.AUTH_USER_MODEL

ALLOW_CUSTOM_GROUPS = True

SUBSCRIPTION_PERMISSIONS = [
            ("advanced", "Advanced Perm"),
            ("pro", "Pro Perm"),
            ("basic", "Basic Perm"),
            ("basic_ai", "Basic AI permission"),
        ]

class Subscription(models.Model):
    
    # fields for subscriptions    
    name = models.CharField(max_length=120)
    subtitle = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permission = models.ManyToManyField(
        Permission,
        limit_choices_to={
            "content_type__app_label":"Subscription",
            "codename__in":[ x[0] for x in SUBSCRIPTION_PERMISSIONS]
        }
    )

    stripe_id = models.CharField(max_length=120, blank=True, null=True)


    order = models.IntegerField(default=-1, help_text='Ordering on Django pricing page' ,name='order')
    featured = models.BooleanField(default=True, help_text='Featured on Django pricing page')
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    features = models.TextField(help_text="Features for pricing, seperated by new line", blank=True, null=True)
    
    #methods from the class subscription
    class Meta:
        ordering = [
         'order', 'featured', '-updated']
        permissions =  SUBSCRIPTION_PERMISSIONS
    
    
    def display_features_list(self):
        if not self.features:
            return [] 
        return [ x.strip() for x in self.features.split('\n') ]

    def save(self, *args, **kwargs):
        if not self.stripe_id:
            stripe_id = Core.billing.create_product(
                name=self.name,
                # PARSE USER INFO FROM OUR DB TO STRIPE
                metadata = {
                    "subscription_plan_id":self.id,
                    },
                # TYPE OF RESPONSE FROM  BILLING
                raw=False
                )
            self.stripe_id = stripe_id

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class SubscriptionPrice(models.Model):
    """
    Subscription Price = Stripe Price
    """
    class IntervalChoices(models.TextChoices):
        MONTHLY = "month", "Monthly"
        YEARLY = "year", "Yearly"

    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    interval = models.CharField(max_length=120, 
                                default=IntervalChoices.MONTHLY, 
                                choices=IntervalChoices.choices
                            )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=99.99)
    order = models.IntegerField(default=-1, help_text='Ordering on Django pricing page')
    featured = models.BooleanField(default=True, help_text='Featured on Django pricing page')
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subscription__order',
         'order', 'featured', '-updated']

    def __str__(self):
        return f"{(self.interval).upper()}LY {self.subscription} subscription costing {self.price}$"
    
    def get_checkout_url(self):
        return reverse("sub-price-checkout",kwargs = {"price_id": self.id})

    @property
    def display_features_list(self):
        if not self.subscription:
            return []
        else:return self.subscription.display_features_list()
    
    @property
    def display_sub_name(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.name

    @property
    def display_sub_subtitle(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.subtitle
    
    @property
    def stripe_currency(self):
        return "usd"
    
    @property
    def stripe_price(self) -> int:
        """
        remove decimal places
        """
        return int(self.price * 100)

    @property
    def product_stripe_id(self):
        if not self.subscription:
            return None
        return self.subscription.stripe_id
    
    def save(self, *args, **kwargs):
        if (not self.stripe_id and 
            self.product_stripe_id is not None):
            stripe_id = Core.billing.create_price(
                currency=self.stripe_currency,
                unit_amount=self.stripe_price,
                interval=self.interval,
                product=self.product_stripe_id,
                metadata={
                        "subscription_plan_price_id": self.id
                },
                raw=False
            )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)
        if self.featured and self.subscription:
            qs = SubscriptionPrice.objects.filter(
                subscription=self.subscription,
                interval=self.interval
            ).exclude(id=self.id)
            qs.update(featured=False)

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete= models.SET_NULL, null=True, blank=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True) 
    active = models.BooleanField(default=True)

def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.values_list('id', flat=True)
    if not  ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups_ids)
    else:
        subs_qs = Subscription.objects.filter(active=True)
        if subscription_obj is not None:
            subs_qs = subs_qs.exclude(id=subscription_obj.id)
        subs_groups = subs_qs.values_list("groups__id", flat=True)
        subs_groups_set = set(subs_groups)


        current_groups = user.groups.all().values_list('id', flat=True)
        groups_ids_set = set(groups_ids)
        
        current_groups_set = set(current_groups) - subs_groups_set 

        final_group_ids = list(groups_ids_set | current_groups_set)

        user.groups.set(final_group_ids)

post_save.connect(user_sub_post_save, sender=UserSubscription)


