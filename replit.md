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
    - **Delivery Area Control:** Geographic coverage validation system that restricts deliveries to a configurable radius (in km) from the store location. Admin enters only the store's ZIP code (CEP), and the system automatically fetches the street name via ViaCEP API (free, no API key required). Admin then adds the building number, and the system calculates coordinates (latitude/longitude) automatically using Nominatim/OpenStreetMap. During checkout, the system validates customer addresses and blocks orders outside the coverage area with clear messaging.

## External Dependencies
- **Mercado Pago API:** Integrated for payment processing. Requires `MERCADOPAGO_ACCESS_TOKEN` environment variable.
- **ViaCEP API:** Used for automatic address lookup from Brazilian ZIP codes (CEP). 100% free with unlimited usage, no API key required. Simplifies store address configuration for delivery radius setup.
- **Nominatim/OpenStreetMap API:** Used for address geocoding and distance calculation in the delivery area control system. 100% free with unlimited usage, no API key required. Uses OpenStreetMap community-maintained address data.
- **Gunicorn:** Used for deploying the Flask application, especially for services like Render.
- **SQLite3:** Default database for development.
- **SQLAlchemy ORM:** Used for interacting with the database.
- **Flask-Login:** Manages user sessions and authentication.
- **Werkzeug:** Utilized for secure password hashing.
- **Requests:** HTTP library for API calls to external services.

## Environment Variables Required
The following environment variables should be configured in production:

- `SECRET_KEY`: Flask secret key for session encryption (required for production)
- `ADMIN_PASSWORD`: Initial admin password (recommended to set)
- `MERCADOPAGO_ACCESS_TOKEN`: Token for Mercado Pago payment integration
- `CORS_ALLOWED_ORIGINS`: (Optional) Comma-separated list of allowed origins for CORS. Defaults to '*' for development. For production, specify domains like: `https://seudominio.com,https://www.seudominio.com`

See `.env.example` for a template.

## Recent Changes
- **2025-11-06**:
  - **Sistema de Estilos PDV com Alto Contraste:** Implementado sistema completo de CSS dedicado para o PDV, garantindo excelente legibilidade com contraste adequado:
    - **Container Principal (`.pdv-container`):** Fundo claro (#f5f5f5) que sobrescreve o tema escuro global do site
    - **Cards e Headers (`.pdv-card`, `.pdv-header`):** Fundos brancos com texto escuro (#111-#333) para máxima legibilidade
    - **Tabelas (`.pdv-table`):** Cabeçalhos com fundo #f8f9fa, texto escuro e bordas bem definidas
    - **Atalhos Visuais (`.pdv-shortcut-card`):** Cards brancos com bordas coloridas ao invés de fundos coloridos, texto sempre escuro para garantir contraste WCAG
    - **Badges e Status (`.pdv-badge`, `.pdv-stat-card`):** Fundos pastéis (#d4edda, #f8d7da, #fff3cd) com texto escuro (#155724, #721c24, #856404) seguindo padrões de acessibilidade
    - **Modais (`.pdv-modal`):** Fundos brancos com texto escuro e formulários com labels em negrito
    - **Foco em Acessibilidade:** Todas as combinações de cores atendem aos padrões WCAG de contraste mínimo
  - **Refatoração de Templates PDV:** Substituição massiva de estilos inline por classes CSS dedicadas nos templates `comanda_detail.html`, `tables.html`, `index.html`, `cash_register.html` e `table_detail.html`, resultando em código mais limpo, manutenível e consistente visualmente
  - **Criação Automática de Comanda ao Abrir Mesa:** Otimizado o fluxo de trabalho do PDV - quando o garçom abre uma mesa, o sistema automaticamente cria uma comanda e redireciona para a página de pedidos, eliminando a etapa manual de criação de comanda e acelerando o atendimento.
    - **Transação Atômica:** Implementado tratamento de exceções com rollback automático - se houver qualquer erro na criação da comanda, a mesa não fica travada como ocupada
    - **Fluxo Direto:** Garçom clica em "Abrir Mesa" e já pode começar a lançar pedidos imediatamente
    - **Mensagem Clara:** Sistema exibe feedback confirmando abertura da mesa e número da comanda criada
  - **Sistema de Gerenciamento de Usuários e Atendentes:** Implementado painel administrativo completo para gerenciar usuários do sistema:
    - **Criação de Atendentes:** Admin pode criar usuários com diferentes papéis (roles): Cliente, Atendente, Cozinha, Gerente e Admin
    - **Gestão de Permissões:** Sistema de controle de acesso baseado em roles - atendentes têm acesso ao PDV para abrir mesas, gerenciar caixa e lançar pedidos
    - **Interface de Listagem:** Listagem completa de usuários com filtros por papel, busca por nome/email/CPF, e estatísticas por categoria
    - **CRUD Completo:** Funcionalidades de criar, editar e deletar usuários com validação de dados (email único, CPF válido, etc)
    - **Máscaras de Entrada:** Formatação automática para CPF e telefone nos formulários
    - **Integração com PDV:** Atendentes criados podem fazer login e acessar o sistema PDV para operações de salão
- **2025-11-05**:
  - **Sistema Completo de Gerenciamento de Status de Pedidos:** Implementado sistema robusto e visual para controle de pedidos com múltiplas etapas:
    - **Novos Status Intermediários:** Adicionados status "Em Preparo", "Pronto", "Saiu para Entrega" e "Retirado" para melhor rastreamento do ciclo de vida do pedido.
    - **Botões de Ação Rápida:** Interface intuitiva com botões contextuais que mudam dinamicamente baseados no status atual do pedido, facilitando transições com um clique.
    - **Timeline Visual Moderna:** Adicionada visualização em timeline vertical mostrando o progresso do pedido com indicadores visuais, cores e ícones para cada etapa.
    - **Registro Automático de Timestamps:** Sistema aprimorado registra automaticamente `accepted_at`, `ready_at` e `delivered_at` nas transições de status, garantindo auditoria completa.
    - **Badges de Status Coloridos:** Implementado sistema consistente de cores e ícones para todos os status em listagens e detalhes.
    - **Fluxos Diferenciados:** Sistema inteligente que adapta o fluxo de status baseado no tipo de entrega (delivery vs retirada).
    - **Histórico Detalhado:** Mantém registro completo de todas as mudanças de status com timestamps, responsável e observações.
- **2025-11-04**: 
  - Improved CORS security configuration to support environment-based origin restrictions. CORS now uses `CORS_ALLOWED_ORIGINS` environment variable for production security instead of allowing all origins by default.
  - Implemented delivery area control system with geographic radius validation. Admin can now configure store location (latitude/longitude) and maximum delivery radius in km. System validates customer addresses during checkout and blocks orders outside coverage area.
  - **Enhanced delivery radius configuration with automatic address lookup:** Admin now simply enters the store's ZIP code (CEP), and the system automatically fetches the complete address (street, neighborhood, city, state) via ViaCEP API. After entering the building number, coordinates are calculated automatically using Nominatim/OpenStreetMap. This eliminates the need for manual coordinate lookup, making setup much easier for administrators.
  - **Enhanced customer checkout with automatic address lookup:** Customers now enter their ZIP code (CEP) during delivery checkout, and the system automatically populates street, neighborhood, city, and state fields via ViaCEP API. Customers only need to manually enter their house number and optional complement. Address fields become editable if ViaCEP lookup fails, ensuring customers can always proceed with manual entry.
  - **NEW: Reverse CEP Search Functionality:** Implemented complete reverse ZIP code search for both customer checkout and admin settings. Users who don't know their CEP can now search for it by entering their state, city, and street name. The system returns all matching addresses from ViaCEP API, and users can select the correct one with a single click. This feature includes:
    - Backend API routes (`/api/cep/buscar/<cep>` and `/api/cep/buscar-endereco`) for both direct and reverse CEP lookup
    - Utility module (`app/utils/cep.py`) with robust error handling and validation
    - Interactive UI with search results display and one-click selection
    - Automatic form population after CEP selection
    - Visual feedback with color-coded success indicators
  - Removed redundant customer name and phone fields from checkout form - now uses data from user registration.
  - Integrated Nominatim/OpenStreetMap API for free address geocoding and distance calculation using Haversine formula. No API key required, 100% free with unlimited usage.
  - Integrated ViaCEP API for automatic Brazilian ZIP code lookup with real-time address population in both admin store settings and customer checkout flows.
  - Added robust error handling for ViaCEP failures: fields automatically unlock for manual entry, values are cleared, and users receive helpful error messages.
  - Implemented comprehensive form validation on checkout submission to ensure all required address fields are populated before processing orders.