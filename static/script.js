let products = [];
let cart = [];
const DELIVERY_FEE = 2000;
let customerServiceWhatsapp = "";

document.addEventListener("DOMContentLoaded", async () => {
    await loadProducts();
    await loadConfig();
    document.getElementById("searchInput").addEventListener("input", searchProducts);
});

async function loadConfig() {
    try {
        const res = await fetch("/api/config");
        const data = await res.json();
        customerServiceWhatsapp = data.customer_service_whatsapp || "";
    } catch (e) {
        console.warn("Config MEC tidak berhasil dimuat.", e);
    }
}

async function loadProducts() {
    const res = await fetch("/api/products");
    products = await res.json();

    const drinks = products.filter(p => p.category === "minuman");
    const foods = products.filter(p => p.category === "makanan");

    document.getElementById("drinkGrid").innerHTML = drinks.map(productCard).join("");
    document.getElementById("foodGrid").innerHTML = foods.map(productCard).join("");
}

function productCard(p) {
    const available = Boolean(p.available) && p.price !== null;
    const icons = {
        "Thai Tea":"🧋", "Matcha":"🍵", "Blackcurrant":"🫐",
        "Latte":"☕", "Latte + Art":"🎨", "Chocolate":"🍫",
        "Espresso":"☕", "Americano":"🥤", "Kentang":"🍟",
        "Dimsum":"🥟", "Gyoza":"🥟", "Dumpling":"🥟",
        "Onigiri":"🍙", "Sushi":"🍣"
    };

    return `
    <article class="product-card" data-name="${p.name.toLowerCase()}">
        <div class="product-icon">${icons[p.name] || "🍽️"}</div>
        <div class="product-info">
            <span class="product-cat">${p.category}</span>
            <h3>${escapeHtml(p.name)}</h3>
            <div class="product-bottom">
                <strong>${available ? formatRupiah(p.price) : "Harga segera tersedia"}</strong>
                ${available
                    ? `<button onclick="addToCart(${p.id})">+ Keranjang</button>`
                    : `<span class="unavailable">Belum tersedia</span>`}
            </div>
        </div>
    </article>`;
}

function formatRupiah(number) {
    return "Rp" + Number(number).toLocaleString("id-ID");
}

function addToCart(productId) {
    const p = products.find(x => Number(x.id) === Number(productId));
    if (!p || Number(p.available) !== 1 || p.price === null || p.price === undefined) {
        console.warn("Produk tidak tersedia:", productId);
        return;
    }

    const id = Number(p.id);
    const existing = cart.find(x => Number(x.product_id) === id);
    if (existing) existing.quantity++;
    else cart.push({product_id: id, name: p.name, price: Number(p.price), quantity: 1});

    updateCart();
    openCart();
}

function updateCart() {
    const count = cart.reduce((sum, x) => sum + x.quantity, 0);
    document.getElementById("cartCount").textContent = count;

    const box = document.getElementById("cartItems");
    if (!cart.length) {
        box.innerHTML = '<div class="empty">Keranjang masih kosong.</div>';
    } else {
        box.innerHTML = cart.map((item, i) => `
            <div class="cart-item">
                <div>
                    <b>${escapeHtml(item.name)}</b>
                    <small>${formatRupiah(item.price)} / item</small>
                </div>
                <div class="qty">
                    <button onclick="changeQuantity(${i}, -1)">−</button>
                    <span>${item.quantity}</span>
                    <button onclick="changeQuantity(${i}, 1)">+</button>
                </div>
                <strong>${formatRupiah(item.price * item.quantity)}</strong>
                <button class="remove" onclick="removeItem(${i})">×</button>
            </div>
        `).join("");
    }

    document.getElementById("cartTotal").textContent =
        formatRupiah(cart.reduce((sum, x) => sum + x.price * x.quantity, 0));
}

function changeQuantity(index, amount) {
    cart[index].quantity += amount;
    if (cart[index].quantity <= 0) cart.splice(index, 1);
    updateCart();
}

function removeItem(index) {
    cart.splice(index, 1);
    updateCart();
}

function openCart() {
    document.getElementById("cartOverlay").classList.add("active");
    document.body.classList.add("no-scroll");
    updateCart();
}

function closeCart() {
    document.getElementById("cartOverlay").classList.remove("active");
    document.body.classList.remove("no-scroll");
}

function closeCartOutside(e) {
    if (e.target === e.currentTarget) closeCart();
}

function openCheckout() {
    if (!cart.length) {
        alert("Keranjang masih kosong.");
        return;
    }
    closeCart();
    document.getElementById("checkoutOverlay").classList.remove("hidden");
    renderCheckout();
}

function closeCheckout() {
    document.getElementById("checkoutOverlay").classList.add("hidden");
}

function renderCheckout() {
    const subtotal = getSubtotal();
    document.getElementById("checkoutSummary").innerHTML = cart.map(x =>
        `<div class="summary-item"><span>${escapeHtml(x.name)} × ${x.quantity}</span><b>${formatRupiah(x.price * x.quantity)}</b></div>`
    ).join("");
    updateCheckoutTotal();
}

function getSubtotal() {
    return cart.reduce((sum, x) => sum + x.price * x.quantity, 0);
}

function getDeliveryMethod() {
    return document.querySelector('input[name="delivery"]:checked').value;
}

function getPaymentMethod() {
    return document.querySelector('input[name="payment"]:checked').value;
}

function toggleDelivery() {
    const delivery = getDeliveryMethod() === "delivery";
    document.getElementById("deliveryFields").classList.toggle("hidden", !delivery);
    updateCheckoutTotal();
}

function togglePayment() {
    const qris = getPaymentMethod() === "qris";
    document.getElementById("qrisBox").classList.toggle("hidden", !qris);
}

function updateCheckoutTotal() {
    const subtotal = getSubtotal();
    const fee = getDeliveryMethod() === "delivery" ? DELIVERY_FEE : 0;

    document.getElementById("checkoutSubtotal").textContent = formatRupiah(subtotal);
    document.getElementById("checkoutDelivery").textContent = formatRupiah(fee);
    document.getElementById("checkoutTotal").textContent = formatRupiah(subtotal + fee);
}

async function submitOrder() {
    const name = document.getElementById("customerName").value.trim();
    const phone = document.getElementById("customerPhone").value.trim();
    const delivery = getDeliveryMethod();
    const payment = getPaymentMethod();
    const className = document.getElementById("className").value.trim();
    const address = document.getElementById("address").value.trim();
    const note = document.getElementById("note").value.trim();
    const message = document.getElementById("checkoutMessage");
    const btn = document.getElementById("submitOrderBtn");

    if (!name || !phone) {
        message.textContent = "Nama dan nomor HP wajib diisi.";
        return;
    }

    if (delivery === "delivery" && !className) {
        message.textContent = "Kelas wajib diisi untuk delivery.";
        return;
    }

    btn.disabled = true;
    btn.textContent = "Menyimpan pesanan...";
    message.textContent = "";

    try {
        const res = await fetch("/api/orders", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                customer_name: name,
                phone,
                delivery_method: delivery,
                class_name: className,
                address,
                note,
                payment_method: payment,
                items: cart.map(x => ({
                    product_id: x.product_id,
                    quantity: x.quantity
                }))
            })
        });

        const data = await res.json();

        if (!data.success) {
            message.textContent = data.message || "Pesanan gagal dibuat.";
            btn.disabled = false;
            btn.textContent = "Buat Pesanan";
            return;
        }

        closeCheckout();
        showSuccess(data);
        cart = [];
        updateCart();
    } catch (e) {
        message.textContent = "Tidak bisa terhubung ke server.";
    } finally {
        btn.disabled = false;
        btn.textContent = "Buat Pesanan";
    }
}

function showSuccess(data) {
    document.getElementById("successQueue").textContent =
        "#" + String(data.queue_number).padStart(3, "0");
    document.getElementById("successOrder").textContent =
        "Nomor Pesanan: " + data.order_number;

    document.getElementById("successInfo").innerHTML = `
        <div><b>Penerimaan</b><span>${data.delivery_method === "delivery" ? "🛵 Delivery ke kelas" : "🚶 Ambil sendiri"}</span></div>
        ${data.class_name ? `<div><b>Kelas</b><span>${escapeHtml(data.class_name)}</span></div>` : ""}
        <div><b>Total</b><span>${formatRupiah(data.total)}</span></div>
        <div><b>Status</b><span>🟡 Menunggu diproses</span></div>
    `;

    document.getElementById("statusLink").href =
        "/status?phone=" + encodeURIComponent(
            document.getElementById("customerPhone").value.trim()
        );

    document.getElementById("successOverlay").classList.remove("hidden");
}

function closeSuccess() {
    document.getElementById("successOverlay").classList.add("hidden");
}

function searchProducts() {
    const keyword = document.getElementById("searchInput").value.toLowerCase().trim();
    document.querySelectorAll(".product-card").forEach(card => {
        card.style.display = card.dataset.name.includes(keyword) ? "" : "none";
    });
}

function escapeHtml(text) {
    return String(text ?? "").replace(/[&<>"']/g, char => ({
        "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
    }[char]));
}

