// ========================================
// DATA KERANJANG
// ========================================

let cart = [];


// ========================================
// TAMBAH PRODUK
// ========================================

function addToCart(name, price) {

    const existingProduct = cart.find(
        item => item.name === name
    );


    if (existingProduct) {

        existingProduct.quantity++;

    } else {

        cart.push({
            name: name,
            price: price,
            quantity: 1
        });

    }


    updateCart();

    showNotification(
        name + " ditambahkan ke keranjang"
    );
}


// ========================================
// UPDATE KERANJANG
// ========================================

function updateCart() {

    const cartCount =
        document.getElementById("cartCount");

    const cartItems =
        document.getElementById("cartItems");

    const cartTotal =
        document.getElementById("cartTotal");


    // jumlah produk

    let totalItems = 0;

    cart.forEach(item => {

        totalItems += item.quantity;

    });


    cartCount.innerText = totalItems;


    // keranjang kosong

    if (cart.length === 0) {

        cartItems.innerHTML = `

            <div class="empty-cart">

                <div>
                    🛒
                </div>

                <p>
                    Keranjang masih kosong.
                </p>

            </div>

        `;

        cartTotal.innerText = "Rp0";

        return;
    }


    // tampilkan produk

    cartItems.innerHTML = "";


    let totalPrice = 0;


    cart.forEach((item, index) => {

        const subtotal =
            item.price * item.quantity;

        totalPrice += subtotal;


        cartItems.innerHTML += `

            <div class="cart-item">

                <div>

                    <h4>
                        ${item.name}
                    </h4>

                    <p>
                        Rp${item.price.toLocaleString("id-ID")}
                        × ${item.quantity}
                    </p>

                </div>

                <button
                    class="remove-item"
                    onclick="removeFromCart(${index})"
                >
                    🗑
                </button>

            </div>

        `;

    });


    cartTotal.innerText =
        "Rp" + totalPrice.toLocaleString("id-ID");
}


// ========================================
// HAPUS PRODUK
// ========================================

function removeFromCart(index) {

    cart.splice(index, 1);

    updateCart();

}


// ========================================
// BUKA CART
// ========================================

function openCart() {

    document.getElementById(
        "cartModal"
    ).style.display = "block";

    document.body.style.overflow = "hidden";

}


// ========================================
// TUTUP CART
// ========================================

function closeCart() {

    document.getElementById(
        "cartModal"
    ).style.display = "none";

    document.body.style.overflow = "auto";

}


// ========================================
// FAVORITE
// ========================================

function toggleFavorite(button) {

    button.classList.toggle("active");


    if (
        button.classList.contains("active")
    ) {

        button.innerHTML = "♥";

        showNotification(
            "Produk ditambahkan ke favorit"
        );

    } else {

        button.innerHTML = "♡";

    }

}


// ========================================
// FILTER KATEGORI
// ========================================

function filterCategory(category) {

    const products =
        document.querySelectorAll(
            ".product-card"
        );


    products.forEach(product => {

        const productCategory =
            product.dataset.category;


        if (
            category === "all" ||
            productCategory === category
        ) {

            product.style.display = "";

        } else {

            product.style.display = "none";

        }

    });


    scrollToSection("produk");

}


// ========================================
// SEARCH
// ========================================

function searchProducts() {

    const keyword =
        document
            .getElementById("searchInput")
            .value
            .toLowerCase()
            .trim();


    const category =
        document
            .getElementById("categorySelect")
            .value;


    const products =
        document.querySelectorAll(
            ".product-card"
        );


    products.forEach(product => {

        const name =
            product.dataset.name.toLowerCase();

        const productCategory =
            product.dataset.category;


        const matchName =
            name.includes(keyword);


        const matchCategory =
            category === "all" ||
            productCategory === category;


        if (
            matchName &&
            matchCategory
        ) {

            product.style.display = "";

        } else {

            product.style.display = "none";

        }

    });


    scrollToSection("produk");

}


// ========================================
// ENTER UNTUK SEARCH
// ========================================

document
    .getElementById("searchInput")
    .addEventListener(
        "keydown",
        function(event) {

            if (event.key === "Enter") {

                searchProducts();

            }

        }
    );


// ========================================
// SHOW ALL PRODUCTS
// ========================================

function showAllProducts() {

    const products =
        document.querySelectorAll(
            ".product-card"
        );


    products.forEach(product => {

        product.style.display = "";

    });

}


// ========================================
// SCROLL
// ========================================

function scrollToSection(id) {

    const section =
        document.getElementById(id);


    if (section) {

        section.scrollIntoView({
            behavior: "smooth"
        });

    }

}


// ========================================
// CHECKOUT
// ========================================

function checkout() {

    if (cart.length === 0) {

        showNotification(
            "Keranjang masih kosong"
        );

        return;

    }


    alert(
        "Checkout akan terhubung ke backend Python + MySQL."
    );

}


// ========================================
// NOTIFICATION
// ========================================

function showNotification(message) {

    const notification =
        document.createElement("div");


    notification.innerText = message;


    notification.style.position =
        "fixed";

    notification.style.bottom =
        "25px";

    notification.style.right =
        "25px";

    notification.style.background =
        "#302015";

    notification.style.color =
        "white";

    notification.style.padding =
        "13px 20px";

    notification.style.borderRadius =
        "5px";

    notification.style.zIndex =
        "9999";

    notification.style.fontSize =
        "13px";

    notification.style.boxShadow =
        "0 8px 25px rgba(0,0,0,.2)";


    document.body.appendChild(
        notification
    );


    setTimeout(() => {

        notification.remove();

    }, 2200);

}


// ========================================
// TUTUP MODAL KETIKA KLIK LUAR
// ========================================

document
    .getElementById("cartModal")
    .addEventListener(
        "click",
        function(event) {

            if (
                event.target === this
            ) {

                closeCart();

            }

        }
    );


// ========================================
// INIT
// ========================================

updateCart();