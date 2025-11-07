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
    - **Simplified Registration (UPDATED - Nov 2025):** Users can register with just name and phone number for faster signup. Email and password are optional fields.
    - **Phone-Based Login (UPDATED - Nov 2025):** Login uses phone number as the primary identifier instead of email, streamlining the authentication process.
    - **Security:** Password hashing remains secure; users without passwords can set one later via password change functionality.
- **UI/UX:**
    - **Design:** Professional and organized layouts with focus on usability, responsive across devices.
    - **Color Scheme:** Updated to use `#00E65D` (vibrant green) with enhanced contrast for better visibility. Shadows and borders strengthened for improved visual hierarchy.
    - **Dynamic Content:** Product categories display images on hover, and the homepage carousel loads dynamically from the database.
- **Core Features:**
    - **User Management:** Simplified registration requiring only name and phone number. Automatic login after registration. Login via phone number only. Optional password setup for enhanced security.
    - **Product Catalog:** Listing with pagination, detailed pages, search, category filtering, featured products, and stock control.
    - **Shopping Cart:** Add/remove items, quantity updates, total calculation, stock verification, installment calculation, and PIX discount.
    - **Order System:** Checkout, user order history, status management, automatic stock deduction, and detailed order viewing.
    - **Admin Panel:** Dashboard with statistics, CRUD for products, categories, coupons, and carousel slides. Advanced order management with filters, search, pagination, real-time statistics, status history, notes, and CSV export. Includes a user management system for creating and managing different roles (Client, Attendant, Kitchen, Manager, Admin) with corresponding permissions.
    - **Wishlist:** Functionality to manage desired products.
    - **Product Reviews:** Users can rate products and add comments, verified by purchase.
    - **Add-ons and Observations:** Allows selecting product extras and adding special observations during checkout, with quantity and price tracking.
    - **Payment Gateway:** Integration with Mercado Pago, including webhook handling for order status updates. Supports pickup and delivery.
    - **Chatbot Sales Funnel (NEW - Nov 2025):**
        - **Data Collection First:** Chatbot collects customer name and phone number BEFORE sending any product/sales links
        - **Conversation State Machine:** Intelligent state tracking prevents links from being shared until both name and phone are captured
        - **Auto-Registration:** System automatically creates user accounts when phone number is provided (register_user_from_chat function)
        - **Smart Detection:** AI-powered recognition of names and Brazilian phone numbers in conversation
        - **Seamless Onboarding:** Customers are automatically logged in and directed to sales page after data collection
        - **Manual Payment Confirmation:** Staff (admins/managers/attendants) confirm payments manually via admin panel instead of online gateway
        - **Payment Tracking:** Orders track who confirmed payment (payment_confirmed_by), when (payment_confirmed_at), and notes (payment_confirmation_notes)
        - **Duplicate Prevention:** System detects existing users by phone number to avoid duplicate registrations
        - **Clickable Links:** URLs in chatbot responses are automatically converted to clickable green links
    - **Delivery Area Control:** Geographic coverage validation restricts deliveries to a configurable radius from the store. Admin enters a ZIP code (CEP), and the system automatically fetches address details via ViaCEP and calculates coordinates using Nominatim/OpenStreetMap for radius validation. Includes reverse CEP search functionality.
    - **Homepage Category Sliders (NEW - Nov 2025):**
        - **Dynamic Category Sections:** Homepage displays specialized horizontal sliders for each product category
        - **Interactive Carousels:** Each category has its own scrollable slider with navigation arrows
        - **Organized Display:** Products organized by categories like Sanduíches, Hambúrgueres, Bebidas, Batatas, Combos, Drinques
        - **Responsive Design:** Sliders adapt to different screen sizes with smooth scrolling
        - **Quick Access:** "Ver todos" links on each section for full category view
    - **Recent Orders & Best Sellers Sections (NEW - Nov 2025):**
        - **Customer Order History:** Authenticated users see their 5 most recent orders on homepage with order number, status, date, items preview, and total
        - **Best Sellers Display:** Dedicated slider showcasing top 6 most-sold products based on aggregated order data
        - **Visual Indicators:** Best seller badge highlights popular items, order status badges show current state with color coding
        - **Smart Queries:** Efficient database queries using GROUP BY aggregation to calculate best sellers without loading unnecessary data
        - **Conditional Display:** Sections appear only when relevant (recent orders for logged-in users, best sellers when order data exists)
        - **Responsive Layout:** Order cards in grid layout, best sellers in horizontal slider with navigation arrows
    - **Real-Time Order Tracking (UPDATED - Nov 2025):**
        - **PIN Authentication:** Customers create their own 4-digit PIN when ordering, providing enhanced security and memorability
        - **Customer-Chosen PINs:** Waiters ask customers to create a 4-digit PIN that they'll use to track their orders
        - **Customer Access:** Customers can log in with comanda number + their 4-digit PIN to view orders in real-time
        - **Live Status Updates:** Real-time notifications via Socket.IO when order status changes (Pending → Preparing → Ready → Delivered)
        - **Kitchen Integration:** Kitchen staff can update order status, automatically notifying both waiters and customers
        - **Waiter Dashboard:** PDV interface displays PIN prominently for easy sharing with customers, with one-click PIN regeneration
        - **Status Timeline:** Visual timeline showing order progress from receipt to delivery
        - **Multi-Party Notifications:** Simultaneous updates to kitchen, waiter, and customer when status changes
    - **QR Code Table Ordering System (UPDATED - Nov 2025):**
        - **QR Code Generation:** Admin can create tables and generate unique QR codes for each table
        - **Customer QR Scanning:** Customers scan QR code on table to access digital menu and order system
        - **Table PIN Authentication:** Each table has a unique 4-digit PIN that customers must enter along with table number to order
        - **Auto-Generated PINs:** System automatically generates secure 4-digit PINs when tables are created
        - **PIN Management:** Admins can view and regenerate PINs from the admin panel at any time
        - **PIN Display:** PINs are prominently displayed in the admin table management interface for easy reference
        - **Security Validation:** Orders require both table number AND correct PIN, preventing unauthorized orders
        - **Auto-Repair:** System automatically generates PINs for legacy tables without one on first access
        - **Digital Catalog:** Full product catalog with images, descriptions, prices, and real-time stock availability
        - **Table Session Management:** Secure session system tracks table orders separately from user accounts
        - **Live Order Status:** Customers view comanda items with real-time status updates (Pending → Preparing → Ready → Delivered)
        - **Order History:** Access to both active comanda items and completed order history for the table
        - **Socket.IO Integration:** Real-time notifications when order items change status
        - **Admin QR Management:** Dashboard interface to create/delete tables, download printable QR codes, and manage PINs
        - **Seamless PDV Integration:** Works alongside existing PDV system with enhanced security

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