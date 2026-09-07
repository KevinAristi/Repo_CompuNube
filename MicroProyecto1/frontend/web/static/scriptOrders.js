const HOST = window.location.hostname;

const ORDERS_API =
    `http://${HOST}:5004/api/orders`;


function showMessage(message, type = 'error') {

    const element =
        document.getElementById('message');

    element.textContent = message;

    element.className =
        `message ${type}`;
}


function clearMessage() {

    const element =
        document.getElementById('message');

    element.textContent = '';
    element.className = 'message';
}


async function loadOrders() {

    clearMessage();

    const tbody =
        document.getElementById(
            'ordersTableBody'
        );

    tbody.innerHTML =
        '<tr><td colspan="7">Loading orders...</td></tr>';

    try {

        const response = await fetch(
            ORDERS_API,
            {
                method: 'GET',
                credentials: 'include'
            }
        );

        if (response.status === 401) {

            tbody.innerHTML = '';

            showMessage(
                'No active user session. Please login before viewing orders.'
            );

            return;
        }

        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const orders =
            await response.json();

        tbody.innerHTML = '';

        if (orders.length === 0) {

            tbody.innerHTML =
                '<tr><td colspan="7">No orders found.</td></tr>';

            return;
        }

        orders.forEach(order => {

            const row =
                document.createElement('tr');

            const createdAt =
                order.created_at
                    ? new Date(
                        order.created_at
                    ).toLocaleString()
                    : '';

            row.innerHTML = `
                <td>${order.id}</td>
                <td>${order.user_name}</td>
                <td>${order.user_email}</td>
                <td>$${Number(order.total).toFixed(2)}</td>
                <td>${order.status}</td>
                <td>${createdAt}</td>
                <td>
                    <button onclick="viewOrder(${order.id})">
                        View Details
                    </button>
                </td>
            `;

            tbody.appendChild(row);
        });

    } catch (error) {

        console.error(
            'Error loading orders:',
            error
        );

        tbody.innerHTML = '';

        showMessage(
            'Unable to load orders.'
        );
    }
}


async function viewOrder(orderId) {

    clearMessage();

    try {

        const response = await fetch(
            `${ORDERS_API}/${orderId}`,
            {
                method: 'GET',
                credentials: 'include'
            }
        );

        if (response.status === 401) {

            showMessage(
                'No active user session.'
            );

            return;
        }

        if (response.status === 404) {

            showMessage(
                'Order not found.'
            );

            return;
        }

        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const order =
            await response.json();


        document.getElementById(
            'detailTitle'
        ).textContent =
            `Order #${order.id}`;


        document.getElementById(
            'detailUser'
        ).textContent =
            order.user_name;


        document.getElementById(
            'detailEmail'
        ).textContent =
            order.user_email;


        document.getElementById(
            'detailTotal'
        ).textContent =
            Number(
                order.total
            ).toFixed(2);


        document.getElementById(
            'detailStatus'
        ).textContent =
            order.status;


        document.getElementById(
            'detailDate'
        ).textContent =
            order.created_at
                ? new Date(
                    order.created_at
                ).toLocaleString()
                : '';


        const itemsBody =
            document.getElementById(
                'orderItemsBody'
            );

        itemsBody.innerHTML = '';

        order.items.forEach(item => {

            const row =
                document.createElement('tr');

            row.innerHTML = `
                <td>${item.product_id}</td>
                <td>${item.quantity}</td>
                <td>$${Number(item.unit_price).toFixed(2)}</td>
                <td>$${Number(item.subtotal).toFixed(2)}</td>
            `;

            itemsBody.appendChild(row);
        });


        document.getElementById(
            'orderDetails'
        ).style.display = 'block';


        document.getElementById(
            'orderDetails'
        ).scrollIntoView({
            behavior: 'smooth'
        });

    } catch (error) {

        console.error(
            'Error loading order:',
            error
        );

        showMessage(
            'Unable to load order details.'
        );
    }
}


document.addEventListener(
    'DOMContentLoaded',
    loadOrders
);
