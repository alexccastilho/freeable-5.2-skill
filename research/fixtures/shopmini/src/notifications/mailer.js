const nodemailer = require('nodemailer');
const transport = nodemailer.createTransport({ host: process.env.SMTP_HOST, port: 587 });
const templates = {
  orderConfirmation: (order, user) => ({
    subject: `Order #${order.id} confirmed`,
    text: `Hi ${user.name}, we received your order #${order.id}.`,
  }),
};
// Sends synchronously in the request path. Errors are logged and swallowed.
async function send(templateName, order, user) {
  const t = templates[templateName](order, user);
  try { await transport.sendMail({ to: user.email, from: 'orders@shopmini.example', ...t }); }
  catch (e) { console.error('mail failed', e.message); }
}
module.exports = { send, templates };
