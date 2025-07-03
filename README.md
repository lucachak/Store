# 🔒 SaaS Starter: Django + HTMX + Stripe  

**A production-ready SaaS boilerplate** with authentication, payments, and security – perfect for launching your next project.  

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![HTMX](https://img.shields.io/badge/HTMX-FF6600?style=for-the-badge&logo=htmx&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Stripe](https://img.shields.io/badge/Stripe-008CDD?style=for-the-badge&logo=stripe&logoColor=white)

## ✨ Features  

### 🔐 Authentication  
- **django-allauth** for social & email login  
- Email verification flow  
- Password reset functionality  

### 💳 Payments Ready  
- **Stripe Integration** for subscriptions/one-time payments  
- Webhook handling setup  
- Example checkout flow  

### 🛡️ Enterprise Security  
- **Google Authenticator (2FA)** support  
- CSRF protection  
- Secure session management  

### 🚀 Modern Stack  
- **HTMX** for dynamic interfaces (no React bloat)  
- **Tailwind CSS** for responsive design  
- Django templating with **SQL backend**  

## ⚡ Quick Start  

```bash
# Clone and setup
git clone https://github.com/lucachak/store.git
cd store
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env  # Edit with your Stripe/Google keys

# Run!
python manage.py migrate
python manage.py runserver
