# Sandwich Gourmet - Plataforma E-commerce Profissional

## Overview
This project is a comprehensive e-commerce platform built with Python Flask, designed for a gourmet sandwich shop. It provides all essential functionalities for an online store, focusing on an intuitive user experience and robust administrative control. The platform aims to offer a professional and scalable solution for businesses in the food industry, supporting sales, order management, and customer engagement.

## User Preferences
I want to prioritize iterative development, focusing on one feature at a time. I prefer clear and direct communication, with explanations that are easy to understand. Please ask for confirmation before implementing significant changes or refactoring large parts of the codebase. I value code readability and maintainability.

## System Architecture
The platform is developed using Python 3.11 with Flask 3.0.0 for the backend, SQLAlchemy ORM with SQLite3 for the database, and Flask-Login for authentication. The frontend is built with HTML5, CSS3, and Vanilla JavaScript, ensuring a responsive design across devices.

**Key Architectural Decisions:**
- **Modular Structure:** The application is organized into logical modules (e.g., `main`, `auth`, `cart`, `admin`) to enhance maintainability and scalability.
- **Database:** SQLite3 is used for development, with a recommendation to migrate to PostgreSQL for production environments due to its robustness.
- **Authentication:** Secure user authentication is implemented using Flask-Login with password hashing (Werkzeug), including role-based access control for common users and administrators.
- **UI/UX:**
    - **Design:** Professional and organized layouts with a focus on usability.
    - **Color Scheme:** Utilizes the theme's main color (`#FFA500`) for visual consistency, especially in authentication forms.
    - **Responsiveness:** Designed to be fully responsive for both mobile and desktop users.
    - **Dynamic Content:** Product categories display images on hover, and the homepage carousel loads slides dynamically from the database.
- **Core Features:**
    - **User Management:** Registration with CPF and phone validation/masking, login/logout, session management, and password hashing.
    - **Product Catalog:** Product listing with pagination, detailed product pages, search functionality, category filtering, featured products, and stock control.
    - **Shopping Cart:** Add/remove items, quantity updates, automatic total calculation, stock verification, installment calculation, and PIX discount.
    - **Order System:** Checkout process, user order history, status management, automatic stock deduction, and detailed order viewing.
    - **Admin Panel:** Comprehensive dashboard with statistics, CRUD operations for products, categories (with images), coupons, and carousel slides. Advanced order management with filters, search, pagination, real-time statistics, status history, internal notes, and CSV export.
    - **Wishlist:** Functionality to add, remove, and view products in a wishlist.
    - **Product Reviews:** Users can rate products (1-5 stars) and add comments, with verification of confirmed purchases.
    - **Add-ons and Observations:** Allows customers to select product extras (like bacon, cheese) and add special observations during checkout (e.g., "no onions"). Extras are stored per item with quantity and price tracking.
    - **Payment Gateway:** Integration with Mercado Pago for processing payments, including webhook handling for order status updates. Supports both pickup and delivery options with configurable shipping costs.

## External Dependencies
- **Mercado Pago API:** Integrated for payment processing. Requires `MERCADOPAGO_ACCESS_TOKEN` environment variable.
- **Gunicorn:** Used for deploying the Flask application, especially for services like Render.
- **SQLite3:** Default database for development.
- **SQLAlchemy ORM:** Used for interacting with the database.
- **Flask-Login:** Manages user sessions and authentication.
- **Werkzeug:** Utilized for secure password hashing.

## Environment Variables Required
The following environment variables should be configured in production:

- `SECRET_KEY`: Flask secret key for session encryption (required for production)
- `ADMIN_PASSWORD`: Initial admin password (recommended to set)
- `MERCADOPAGO_ACCESS_TOKEN`: Token for Mercado Pago payment integration
- `CORS_ALLOWED_ORIGINS`: (Optional) Comma-separated list of allowed origins for CORS. Defaults to '*' for development. For production, specify domains like: `https://seudominio.com,https://www.seudominio.com`

See `.env.example` for a template.

## Recent Changes
- **2025-11-04**: Improved CORS security configuration to support environment-based origin restrictions. CORS now uses `CORS_ALLOWED_ORIGINS` environment variable for production security instead of allowing all origins by default.