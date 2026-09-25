from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import date
import os

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "mec-mart-dev-secret-change-this"
)

# =========================================================
# DATABASE
# =========================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "kkEFgVJbQhbSWaXIRHSlrwxkwLwCETYj"),
    "database": os.getenv("DB_NAME", "railway"),
    "port": int(os.getenv("DB_PORT", "54529")),
    "connection_timeout": int(os.getenv("DB_TIMEOUT", "10")),
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# =========================================================
# KONFIGURASI
# =========================================================

STAFF_WHATSAPP = {
    "minuman": "628817297054",
    "makanan": "",
}

CUSTOMER_SERVICE_WHATSAPP = ""

DELIVERY_FEE = 2000


# =========================================================
# HALAMAN
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/status")
def status_page():
    return render_template("status.html")


# =========================================================
# PRODUK
# =========================================================

@app.get("/api/products")
def products():

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT
                id,
                name,
                category,
                price,
                available
            FROM products
            ORDER BY category, id
        """)

        rows = cur.fetchall()

        return jsonify(rows)

    finally:
        cur.close()
        conn.close()


# =========================================================
# BUAT PESANAN
# =========================================================

@app.post("/api/orders")
def create_order():

    data = request.get_json(silent=True) or {}

    customer_name = str(
        data.get("customer_name", "")
    ).strip()

    phone = str(
        data.get("phone", "")
    ).strip()

    address = str(
        data.get("address", "")
    ).strip()

    note = str(
        data.get("note", "")
    ).strip()

    delivery_method = str(
        data.get("delivery_method", "pickup")
    ).strip()

    class_name = str(
        data.get("class_name", "")
    ).strip()

    payment_method = str(
        data.get("payment_method", "")
    ).strip()

    items = data.get("items", [])


    # -----------------------------------------------------
    # VALIDASI
    # -----------------------------------------------------

    if not customer_name:
        return jsonify({
            "success": False,
            "message": "Nama wajib diisi."
        }), 400

    if not phone:
        return jsonify({
            "success": False,
            "message": "Nomor HP wajib diisi."
        }), 400

    if not payment_method:
        return jsonify({
            "success": False,
            "message": "Metode pembayaran wajib dipilih."
        }), 400

    if not items:
        return jsonify({
            "success": False,
            "message": "Keranjang masih kosong."
        }), 400


    if delivery_method not in (
        "pickup",
        "delivery"
    ):
        return jsonify({
            "success": False,
            "message": "Metode penerimaan tidak valid."
        }), 400


    if delivery_method == "delivery" and not class_name:
        return jsonify({
            "success": False,
            "message": "Kelas wajib diisi untuk delivery."
        }), 400


    if payment_method not in (
        "qris",
        "cod"
    ):
        return jsonify({
            "success": False,
            "message": "Metode pembayaran tidak valid."
        }), 400


    conn = get_db()

    try:

        conn.start_transaction()

        cur = conn.cursor(dictionary=True)


        # -------------------------------------------------
        # PROSES ITEM
        # -------------------------------------------------

        product_ids = []
        quantities = {}


        for item in items:

            try:
                product_id = int(
                    item.get("product_id")
                )

                quantity = int(
                    item.get("quantity", 0)
                )

            except (
                TypeError,
                ValueError
            ):
                continue


            if quantity > 0:

                product_ids.append(
                    product_id
                )

                quantities[product_id] = (
                    quantities.get(product_id, 0)
                    + quantity
                )


        if not product_ids:
            raise ValueError(
                "Keranjang kosong."
            )


        unique_ids = list(
            set(product_ids)
        )


        placeholders = ",".join(
            ["%s"] * len(unique_ids)
        )


        cur.execute(
            f"""
            SELECT
                id,
                name,
                category,
                price,
                available
            FROM products
            WHERE id IN ({placeholders})
            """,
            tuple(unique_ids)
        )


        products_db = {
            row["id"]: row
            for row in cur.fetchall()
        }


        order_items = []
        subtotal = 0


        # -------------------------------------------------
        # HITUNG TOTAL
        # -------------------------------------------------

        for product_id, quantity in quantities.items():

            product = products_db.get(
                product_id
            )


            if not product:
                raise ValueError(
                    "Produk tidak ditemukan."
                )


            if not product["available"]:

                raise ValueError(
                    f'{product["name"]} '
                    f'belum tersedia.'
                )


            if product["price"] is None:

                raise ValueError(
                    f'{product["name"]} '
                    f'belum memiliki harga.'
                )


            price = int(
                product["price"]
            )


            line_total = (
                price * quantity
            )


            subtotal += line_total


            section = (
                "minuman"
                if product["category"] == "minuman"
                else "makanan"
            )


            order_items.append({

                "product_id":
                    product_id,

                "product_name":
                    product["name"],

                "price":
                    price,

                "quantity":
                    quantity,

                "subtotal":
                    line_total,

                "section":
                    section
            })


        # -------------------------------------------------
        # ONGKIR
        # -------------------------------------------------

        if delivery_method == "delivery":
            delivery_fee = DELIVERY_FEE
        else:
            delivery_fee = 0


        total = (
            subtotal
            + delivery_fee
        )


        # -------------------------------------------------
        # NOMOR ANTREAN
        # -------------------------------------------------

        today = date.today()


        cur.execute(
            """
            SELECT last_number
            FROM daily_counters
            WHERE counter_date=%s
            FOR UPDATE
            """,
            (today,)
        )


        counter = cur.fetchone()


        if counter:

            queue_number = (
                int(counter["last_number"])
                + 1
            )


            cur.execute(
                """
                UPDATE daily_counters
                SET last_number=%s
                WHERE counter_date=%s
                """,
                (
                    queue_number,
                    today
                )
            )

        else:

            queue_number = 1


            cur.execute(
                """
                INSERT INTO daily_counters
                (
                    counter_date,
                    last_number
                )
                VALUES (%s,%s)
                """,
                (
                    today,
                    queue_number
                )
            )


        # -------------------------------------------------
        # NOMOR PESANAN
        # -------------------------------------------------

        order_number = (
            f"MEC-"
            f"{today.strftime('%Y%m%d')}-"
            f"{queue_number:04d}"
        )


        # -------------------------------------------------
        # SIMPAN ORDER
        # -------------------------------------------------

        cur.execute(
            """
            INSERT INTO orders
            (
                order_number,
                queue_number,
                queue_date,
                customer_name,
                phone,
                address,
                class_name,
                note,
                subtotal,
                delivery_fee,
                total,
                delivery_method,
                payment_method,
                payment_status,
                status
            )
            VALUES
            (
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s
            )
            """,
            (
                order_number,
                queue_number,
                today,
                customer_name,
                phone,
                address,
                class_name,
                note,
                subtotal,
                delivery_fee,
                total,
                delivery_method,
                payment_method,
                "pending",
                "waiting"
            )
        )


        order_id = cur.lastrowid


        # -------------------------------------------------
        # SIMPAN ITEM
        # -------------------------------------------------

        for item in order_items:

            cur.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    product_name,
                    price,
                    quantity,
                    subtotal,
                    section
                )
                VALUES
                (
                    %s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    order_id,
                    item["product_id"],
                    item["product_name"],
                    item["price"],
                    item["quantity"],
                    item["subtotal"],
                    item["section"]
                )
            )


        conn.commit()


        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "order_id":
                order_id,

            "order_number":
                order_number,

            "queue_number":
                queue_number,

            "subtotal":
                subtotal,

            "delivery_fee":
                delivery_fee,

            "total":
                total,

            "payment_method":
                payment_method,

            "delivery_method":
                delivery_method,

            "class_name":
                class_name
        })


    except (
        Error,
        ValueError
    ) as e:

        conn.rollback()

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 400


    finally:

        try:
            cur.close()
            conn.close()

        except Exception:
            pass


# =========================================================
# STATUS PESANAN BERDASARKAN NOMOR PESANAN
# =========================================================

@app.get("/api/orders/<order_number>")
def order_status(order_number):

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:

        cur.execute(
            """
            SELECT
                id,
                order_number,
                queue_number,
                customer_name,
                class_name,
                delivery_method,
                payment_method,
                payment_status,
                subtotal,
                delivery_fee,
                total,
                status,
                created_at
            FROM orders
            WHERE order_number=%s
            """,
            (order_number,)
        )


        order = cur.fetchone()


        if not order:

            return jsonify({

                "success": False,

                "message":
                    "Pesanan tidak ditemukan."

            }), 404


        cur.execute(
            """
            SELECT
                product_name,
                price,
                quantity,
                subtotal,
                section
            FROM order_items
            WHERE order_id=%s
            ORDER BY id
            """,
            (order["id"],)
        )


        order["items"] = (
            cur.fetchall()
        )


        order.pop("id", None)


        return jsonify({

            "success": True,

            "order":
                order

        })

    finally:

        cur.close()
        conn.close()


# =========================================================
# STATUS PESANAN BERDASARKAN NOMOR HP
# =========================================================

@app.get("/api/order-status")
def order_status_by_phone():

    phone = str(
        request.args.get(
            "phone",
            ""
        )
    ).strip()


    if not phone:

        return jsonify({

            "success": False,

            "message":
                "Nomor HP wajib diisi."

        }), 400


    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:

        cur.execute(
            """
            SELECT
                id,
                order_number,
                queue_number,
                customer_name,
                class_name,
                delivery_method,
                payment_method,
                payment_status,
                subtotal,
                delivery_fee,
                total,
                status,
                created_at
            FROM orders
            WHERE phone=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (phone,)
        )


        order = cur.fetchone()


        if not order:

            return jsonify({

                "success": False,

                "message":
                    "Pesanan dengan nomor HP "
                    "tersebut tidak ditemukan."

            }), 404


        cur.execute(
            """
            SELECT
                product_name,
                price,
                quantity,
                subtotal,
                section
            FROM order_items
            WHERE order_id=%s
            ORDER BY id
            """,
            (order["id"],)
        )


        order["items"] = (
            cur.fetchall()
        )


        order.pop("id", None)


        return jsonify({

            "success": True,

            "order":
                order

        })

    finally:

        cur.close()
        conn.close()


# =========================================================
# ADMIN - DAFTAR PESANAN
# =========================================================

@app.get("/api/admin/orders")
def admin_orders():

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:

        cur.execute(
            """
            SELECT
                id,
                order_number,
                queue_number,
                customer_name,
                phone,
                address,
                class_name,
                delivery_method,
                payment_method,
                payment_status,
                subtotal,
                delivery_fee,
                total,
                status,
                note,
                created_at
            FROM orders
            ORDER BY id DESC
            LIMIT 100
            """
        )


        orders = cur.fetchall()


        for order in orders:

            cur.execute(
                """
                SELECT
                    product_name,
                    price,
                    quantity,
                    subtotal,
                    section
                FROM order_items
                WHERE order_id=%s
                ORDER BY id
                """,
                (order["id"],)
            )


            order["items"] = (
                cur.fetchall()
            )


        return jsonify({

            "success": True,

            "orders":
                orders

        })

    finally:

        cur.close()
        conn.close()
# =========================================================
# ADMIN - VERIFIKASI PEMBAYARAN QRIS
# =========================================================

@app.post("/api/orders/<int:order_id>/verify-payment")
def verify_payment(order_id):

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute(
            """
            SELECT
                id,
                payment_method,
                payment_status
            FROM orders
            WHERE id=%s
            """,
            (order_id,)
        )

        order = cur.fetchone()

        if not order:
            return jsonify({
                "success": False,
                "message": "Pesanan tidak ditemukan."
            }), 404

        # Hanya QRIS yang perlu diverifikasi
        if order["payment_method"] != "qris":
            return jsonify({
                "success": False,
                "message": "Pesanan ini menggunakan COD."
            }), 400

        if order["payment_status"] == "paid":
            return jsonify({
                "success": False,
                "message": "Pembayaran sudah diverifikasi."
            }), 400

        cur.execute(
            """
            UPDATE orders
            SET payment_status='paid'
            WHERE id=%s
            """,
            (order_id,)
        )

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Pembayaran QRIS berhasil diverifikasi."
        })

    except Error as e:

        conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        cur.close()
        conn.close()

# =========================================================
# ADMIN - UBAH STATUS
# =========================================================

@app.post("/api/orders/<int:order_id>/status")
def update_status(order_id):

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    status = str(
        data.get(
            "status",
            ""
        )
    ).strip()


    allowed = {
        "waiting",
        "making",
        "ready",
        "done"
    }


    if status not in allowed:

        return jsonify({

            "success": False,

            "message":
                "Status tidak valid."

        }), 400


    conn = get_db()
    cur = conn.cursor()
        # QRIS harus sudah diverifikasi sebelum pesanan diproses
    cur.execute(
        """
        SELECT payment_method, payment_status
        FROM orders
        WHERE id=%s
        """,
        (order_id,)
    )

    order = cur.fetchone()

    if not order:
        cur.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Pesanan tidak ditemukan."
        }), 404

    payment_method, payment_status = order

    if (
        payment_method == "qris"
        and payment_status != "paid"
        and status != "waiting"
    ):
        cur.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Pembayaran QRIS belum diverifikasi. Pesanan belum boleh diproses."
        }), 400

    try:

        cur.execute(
            """
            UPDATE orders
            SET status=%s
            WHERE id=%s
            """,
            (
                status,
                order_id
            )
        )


        conn.commit()


        if cur.rowcount == 0:

            return jsonify({

                "success": False,

                "message":
                    "Pesanan tidak ditemukan."

            }), 404


        return jsonify({

            "success": True

        })

    finally:

        cur.close()
        conn.close()


# =========================================================
# KONFIGURASI UNTUK JAVASCRIPT
# =========================================================

@app.get("/api/config")
def config():

    return jsonify({

        "delivery_fee":
            DELIVERY_FEE,

        "staff_whatsapp":
            STAFF_WHATSAPP,

        "customer_service_whatsapp":
            CUSTOMER_SERVICE_WHATSAPP

    })


# =========================================================
# JALANKAN FLASK
# =========================================================

if __name__ == "__main__":
    app.run()
