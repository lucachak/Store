# SaaS starter: Django, Stripe, PostgreSQL

Accounts, subscriptions and billing for a SaaS, ready to rebrand.

- **Auth**: email + password, GitHub and Google login, email verification, two-factor (TOTP), password reset (django-allauth)
- **Billing**: plans and prices managed in the admin and mirrored to Stripe, Stripe Checkout, customer portal, cancel and resume, webhook sync
- **Access control**: plan permissions and groups follow the subscription status
- **UI**: Tailwind CSS v4 build, HTMX, dark and light themes, English and Portuguese (pt-BR)
- **Staff**: searchable user list, workspace numbers, Unfold-styled Django admin

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install && npm run build:css

cp env.example .env        # set SECRET_KEY, DATABASE_URL and the Stripe keys
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`DATABASE_URL` takes any URL supported by dj-database-url, for example
`postgres://user:pass@localhost:5432/saas`. Leave it out to use SQLite.

During development, run `npm run watch:css` in a second terminal.

## Stripe

1. Put `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` in `.env`.
2. Create plans in the admin (**Subscription > Subscriptions**). Saving a plan creates the Stripe product, saving a price creates the Stripe price. Prices can't be edited in Stripe, so create a new one instead.
3. Forward events to your machine and copy the signing secret into `STRIPE_WEBHOOK_SECRET`:

   ```bash
   stripe listen --forward-to localhost:8000/checkout/webhook/
   ```

4. In production, add a webhook endpoint at `https://your-domain/checkout/webhook/` for
   `checkout.session.completed` and `customer.subscription.created|updated|deleted`.
5. Enable the customer portal in the Stripe dashboard so "Payment method and invoices" works.

The webhook and the checkout return page write through the same code
(`Subscription/services.py`), so handling an event twice is harmless.
As a safety net for missed events, run `python manage.py sync_billing` from cron.

## Project layout

| Path | What lives there |
| --- | --- |
| `Core/` | Settings, URLs, `billing.py` (the only module that imports Stripe) |
| `Subscription/` | Plans, prices, user subscriptions, pricing and billing pages, sync services |
| `Checkout/` | Start checkout, return page, Stripe webhook |
| `Customers/` | Link between a user and a Stripe customer |
| `Auth/` | Account settings, staff user list, idle logout |
| `Home/` | Landing page and dashboard |
| `Templates/` | `base.html`, `public.html`, `app.html` shells, per-app folders, `allauth/` theme |
| `frontend/app.css` | Design tokens and components. Built to `Static/Css/app.css` |
| `locale/` | Translations |

## Rebranding

- Name: set `SITE_NAME`.
- Colours and type: edit the token block at the top of `frontend/app.css`, then `npm run build:css`.
- Copy: the landing page is `Templates/Home/home.html`.

## Translations

```bash
python manage.py makemessages -l pt_BR -i "node_modules/*" -i ".venv/*" -i "staticfiles/*"
python manage.py compilemessages -l pt_BR
```

## Tests

```bash
python manage.py test
```

Stripe is mocked, no network or keys needed.

## Production

```bash
npm run build:css
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn -c gunicorn.conf.py Core.wsgi:application
```

Set `DEBUG=False`, `ALLOWED_HOSTS`, `BASE_URL`, a long `SECRET_KEY`, and `BEHIND_PROXY=True` if a
proxy terminates TLS. `SECURE_HSTS_SECONDS` is off until you set it.
