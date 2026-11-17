# shopmini

Small order-management API used by our warehouse team.

## Running

    npm install
    npm start        # http://localhost:3000
    npm test

Customers recieve an order confirmation e-mail when they place an order.

## Layout

- `src/server.js` – Express app and routes
- `src/orders/` – order model and service
- `src/notifications/` – e-mail sending (wraps the SMTP provider)
- `src/users/` – user lookup
- `src/admin/` – back-office endpoints used by warehouse staff
