# Sandwich Gourmet - Plataforma E-commerce Profissional

## Overview
This project is a comprehensive e-commerce platform built with Python Flask, designed for a gourmet sandwich shop. It provides essential functionalities for an online store, focusing on an intuitive user experience and robust administrative control. The platform aims to offer a professional and scalable solution for businesses in the food industry, supporting sales, order management, and customer engagement with features like a dynamic product catalog, shopping cart, order system, and a powerful admin panel.

## User Preferences
I want to prioritize iterative development, focusing on one feature at a time. I prefer clear and direct communication, with explanations that are easy to understand. Please ask for confirmation before implementing significant changes or refactoring large parts of the codebase. I value code readability and maintainability.

## System Architecture
The platform is developed using Python 3.11 with Flask 3.0.0 for the backend, SQLAlchemy ORM with SQLite3 for the database, and Flask-Login for authentication. The frontend is built with HTML5, CSS3, and Vanilla JavaScript, ensuring a responsive design across devices.

**Key Architectural Decisions:**
- **Modular Structure:** The application is organized into logical modules (e.g., `main`, `auth`, `cart`, `admin`) for maintainability and scalability.
- **Database:** SQLite3 is used for development, with PostgreSQL recommended for production.
- **Authentication:** Secure user authentication uses Flask-Login with Werkzeug for password hashing, including role-based access control for users and administrators.
- **UI/UX:**
    - **Design:** Professional and organized layouts with focus on usability, responsive across devices.
    - **Color Scheme:** Uses `#FFA500` for visual consistency.
    - **Dynamic Content:** Product categories display images on hover, and the homepage carousel loads dynamically from the database.
- **Core Features:**
    - **User Management:** Registration with CPF and phone validation, login/logout, and session management.
    - **Product Catalog:** Listing with pagination, detailed pages, search, category filtering, featured products, and stock control.
    - **Shopping Cart:** Add/remove items, quantity updates, total calculation, stock verification, installment calculation, and PIX discount.
    - **Order System:** Checkout, user order history, status management, automatic stock deduction, and detailed order viewing.
    - **Admin Panel:** Dashboard with statistics, CRUD for products, categories, coupons, and carousel slides. Advanced order management with filters, search, pagination, real-time statistics, status history, notes, and CSV export. Includes a user management system for creating and managing different roles (Client, Attendant, Kitchen, Manager, Admin) with corresponding permissions.
    - **Wishlist:** Functionality to manage desired products.
    - **Product Reviews:** Users can rate products and add comments, verified by purchase.
    - **Add-ons and Observations:** Allows selecting product extras and adding special observations during checkout, with quantity and price tracking.
    - **Payment Gateway:** Integration with Mercado Pago, including webhook handling for order status updates. Supports pickup and delivery.
    - **Delivery Area Control:** Geographic coverage validation restricts deliveries to a configurable radius from the store. Admin enters a ZIP code (CEP), and the system automatically fetches address details via ViaCEP and calculates coordinates using Nominatim/OpenStreetMap for radius validation. Includes reverse CEP search functionality.

## External Dependencies
- **Mercado Pago API:** For payment processing.
- **ViaCEP API:** For automatic Brazilian ZIP code (CEP) lookup and address population.
- **Nominatim/OpenStreetMap API:** For address geocoding and distance calculation for delivery area control.
- **Gunicorn:** For deploying the Flask application.
- **SQLite3:** Development database.
- **SQLAlchemy ORM:** For database interaction.
- **Flask-Login:** For user authentication.
- **Werkzeug:** For password hashing.
- **Requests:** HTTP library for API calls.