import stripe
import datetime
from decouple import config 


if config('DEBUG',default=False,cast=bool):
    stripe.api_key = config('STRIPE_TEST_SEC_KEY',default="",cast=str)
else:
    stripe.api_key = config('STRIPE_LIVE_SEC_KEY',default="",cast=str)

if "sk_test" in f'{stripe.api_key}' and not config('DEBUG',default=False,cast=bool):
    raise ValueError("Invalid credentials")


def timestamp_as_datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC)

def serialize_subscription_data(subscription_response):
    status = subscription_response.status
    current_period_start = timestamp_as_datetime(subscription_response.current_period_start)
    current_period_end = timestamp_as_datetime(subscription_response.current_period_end)
    cancel_at_period_end = subscription_response.cancel_at_period_end
    return {
        "current_period_start": current_period_start,
        "current_period_end": current_period_end,
        "status": status,
        "cancel_at_period_end": cancel_at_period_end,
    }


def create_customer(name:str="", email:str="", metadata:dict={}, raw:bool=False):
    response = stripe.Customer.create(
        name=name,
        email=email,
        metadata=metadata
    )

    if raw:
        return response
    stripe_id = response.id
    return stripe_id


def create_product(name:str="", metadata:dict={}, raw:bool=False):
    response = stripe.Product.create(
        name=name,
        metadata=metadata,
    )
    if raw:
        return response
    stripe_id = response.id
    return stripe_id


def create_price(currency="usd", unit_amount:int=9999, interval="month", product=None, metadata={},
        raw=False):

    if product is None:
        return None

    response = stripe.Price.create(
            currency=currency,
            unit_amount=unit_amount,
            recurring={"interval": interval },
            product=product,
            metadata=metadata
        )
    if raw:
        return response
    stripe_id = response.id
    return stripe_id


def start_checkout_session(customer_id:str="", success_url:str="",
                           cancel_url:str="", price_stripe_id:str="",raw:bool=True):
    if not success_url.endswith("?session_id={CHECKOUT_SESSION_ID}"):
        success_url = f"{success_url}" + "?session_id={CHECKOUT_SESSION_ID}"
    response = stripe.checkout.Session.create(
        customer = customer_id,
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{"price": price_stripe_id, "quantity": 1}],
        mode="subscription",
    )
    if raw:
        return response
    return response.url


def get_checkout_session(stripe_id, raw=True):
    response =  stripe.checkout.Session.retrieve(stripe_id)
    if raw:
        return response
    return response.url

def get_subscription(stripe_id, raw=True):
    response =  stripe.Subscription.retrieve(stripe_id)
    if raw:
        return response
    return serialize_subscription_data(response)


def get_checkout_customer_plan(session_id):

        checkout_r = get_checkout_session(session_id, raw=True)
        customer_id = checkout_r.customer
        sub_stripe_id = checkout_r.subscription
        sub_r = get_subscription(sub_stripe_id, raw=True)
        sub_plan = sub_r.plan
        return customer_id, sub_plan.id
