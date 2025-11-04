let socket = null;
let orderNotificationSound = null;
let mutedNotifications = localStorage.getItem('mutedNotifications') === 'true';
let lastOrderCount = 0;

function initializeSocket() {
    socket = io({
        transports: ['websocket', 'polling']
    });

    socket.on('connect', function() {
        console.log('✅ Conectado ao sistema de pedidos em tempo real');
    });

    socket.on('connected', function(data) {
        console.log(data.message);
        showToast('Sistema conectado', 'success');
    });

    socket.on('new_order', function(data) {
        console.log('🔔 Novo pedido recebido:', data);
        showNewOrderNotification(data);
        playNotificationSound();
        requestOrderUpdate();
    });

    socket.on('order_updated', function(data) {
        console.log('📝 Pedido atualizado:', data);
        updateOrderInList(data);
        
        if (window.location.pathname.includes('/admin/pedidos')) {
            setTimeout(() => {
                console.log('Auto-atualizando ap\u00f3s altera\u00e7\u00e3o de status...');
                window.location.reload();
            }, 2000);
        }
    });

    socket.on('orders_update', function(data) {
        console.log('📋 Lista de pedidos atualizada');
        updateOrdersList(data.orders);
    });

    socket.on('order_stats', function(data) {
        updatePendingCounter(data.pending_count);
    });

    socket.on('disconnect', function() {
        console.log('❌ Desconectado do sistema');
        showToast('Conexão perdida. Tentando reconectar...', 'warning');
    });
}

function requestOrderUpdate() {
    if (socket && socket.connected) {
        socket.emit('request_order_update');
    }
}

function playNotificationSound() {
    if (mutedNotifications) return;
    
    if (!orderNotificationSound) {
        orderNotificationSound = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBStux/DajjgJEWSz6OWpVxgLQ5ji8L1tJAUqcsXu2YPFAAAAAAA=');
    }
    
    orderNotificationSound.play().catch(e => console.log('Erro ao reproduzir som:', e));
}

function showNewOrderNotification(order) {
    const notificationHtml = `
        <div class="order-notification" style="position: fixed; top: 80px; right: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); z-index: 10000; min-width: 350px; animation: slideInRight 0.5s;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0; font-size: 18px; display: flex; align-items: center; gap: 10px;">
                    <i class="fa fa-bell" style="font-size: 24px; animation: ring 1s infinite;"></i>
                    Novo Pedido #${order.id}!
                </h3>
                <button onclick="closeNotification(this)" style="background: transparent; border: none; color: white; font-size: 24px; cursor: pointer; padding: 0; width: 30px; height: 30px;">&times;</button>
            </div>
            <div style="font-size: 14px; line-height: 1.8;">
                <p style="margin: 5px 0;"><strong>Cliente:</strong> ${order.customer_name}</p>
                <p style="margin: 5px 0;"><strong>Telefone:</strong> ${order.customer_phone || 'Não informado'}</p>
                <p style="margin: 5px 0;"><strong>Total:</strong> R$ ${order.total.toFixed(2)}</p>
                <p style="margin: 5px 0;"><strong>Tipo:</strong> ${order.delivery_type === 'delivery' ? 'Entrega' : 'Retirada'}</p>
                <p style="margin: 5px 0;"><strong>Itens:</strong> ${order.items_count}</p>
            </div>
            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <a href="/admin/pedidos/${order.id}" style="flex: 1; background: #fff; color: #667eea; padding: 10px; text-align: center; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px;">
                    Ver Detalhes
                </a>
                <button onclick="quickAcceptOrder(${order.id}, this)" style="flex: 1; background: #4CAF50; color: white; padding: 10px; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px;">
                    Aceitar
                </button>
            </div>
        </div>
    `;
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = notificationHtml;
    document.body.appendChild(tempDiv.firstElementChild);
    
    setTimeout(function() {
        const notif = document.querySelector('.order-notification');
        if (notif) {
            notif.style.animation = 'slideOutRight 0.5s';
            setTimeout(() => notif.remove(), 500);
        }
    }, 10000);
}

function closeNotification(button) {
    const notification = button.closest('.order-notification');
    notification.style.animation = 'slideOutRight 0.5s';
    setTimeout(() => notification.remove(), 500);
}

function quickAcceptOrder(orderId, button) {
    button.disabled = true;
    button.textContent = 'Aceitando...';
    
    fetch(`/admin/pedidos/${orderId}/aceitar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Pedido aceito com sucesso!', 'success');
            closeNotification(button);
            requestOrderUpdate();
        } else {
            showToast(data.message, 'error');
            button.disabled = false;
            button.textContent = 'Aceitar';
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showToast('Erro ao aceitar pedido', 'error');
        button.disabled = false;
        button.textContent = 'Aceitar';
    });
}

function showToast(message, type = 'info') {
    const colors = {
        success: '#4CAF50',
        error: '#f44336',
        warning: '#ff9800',
        info: '#2196F3'
    };
    
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: ${colors[type]};
        color: white;
        padding: 15px 25px;
        border-radius: 6px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 10001;
        animation: slideInUp 0.5s;
        font-size: 14px;
        font-weight: 500;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutDown 0.5s';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function toggleNotifications() {
    mutedNotifications = !mutedNotifications;
    localStorage.setItem('mutedNotifications', mutedNotifications);
    
    const icon = document.getElementById('notificationIcon');
    const button = document.getElementById('notificationToggle');
    
    if (mutedNotifications) {
        icon.className = 'fa fa-bell-slash';
        button.title = 'Ativar notificações sonoras';
        showToast('Notificações sonoras desativadas', 'info');
    } else {
        icon.className = 'fa fa-bell';
        button.title = 'Desativar notificações sonoras';
        showToast('Notificações sonoras ativadas', 'success');
        playNotificationSound();
    }
}

function updatePendingCounter(count) {
    const counter = document.getElementById('pendingCounter');
    if (counter) {
        counter.textContent = count;
        if (count > lastOrderCount && lastOrderCount > 0) {
            counter.style.animation = 'pulse 0.5s';
            setTimeout(() => counter.style.animation = '', 500);
        }
        lastOrderCount = count;
    }
    
    const badges = document.querySelectorAll('.pending-badge');
    badges.forEach(badge => {
        badge.textContent = count;
        if (count === 0) {
            badge.style.display = 'none';
        } else {
            badge.style.display = 'inline-block';
        }
    });
}

function updateOrderInList(orderData) {
    const orderRow = document.querySelector(`tr[data-order-id="${orderData.id}"]`);
    if (orderRow) {
        const statusCell = orderRow.querySelector('.order-status');
        if (statusCell) {
            const statusBadge = statusCell.querySelector('span');
            if (statusBadge) {
                statusBadge.textContent = orderData.status;
                statusBadge.className = getStatusClass(orderData.status);
            }
        }
    }
}

function updateOrdersList(orders) {
    console.log('Atualizando lista de pedidos:', orders.length);
    
    const tableBody = document.querySelector('tbody');
    if (!tableBody) return;
    
    lastOrderCount = orders.filter(o => o.status === 'Pendente').length;
    updatePendingCounter(lastOrderCount);
}

function getStatusClass(status) {
    const classes = {
        'Pendente': 'badge badge-warning',
        'Confirmado': 'badge badge-success',
        'Enviado': 'badge badge-info',
        'Entregue': 'badge badge-success',
        'Cancelado': 'badge badge-danger'
    };
    return classes[status] || 'badge badge-secondary';
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    @keyframes slideInUp {
        from {
            transform: translateY(100px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutDown {
        from {
            transform: translateY(0);
            opacity: 1;
        }
        to {
            transform: translateY(100px);
            opacity: 0;
        }
    }
    
    @keyframes ring {
        0%, 100% { transform: rotate(0deg); }
        10%, 30% { transform: rotate(-10deg); }
        20%, 40% { transform: rotate(10deg); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.2); }
    }
`;
document.head.appendChild(style);

if (typeof io !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        if (window.location.pathname.includes('/admin/pedidos') || window.location.pathname.includes('/admin/')) {
            initializeSocket();
            setInterval(requestOrderUpdate, 30000);
        }
    });
}
