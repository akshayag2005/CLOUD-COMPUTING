import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from minio import Minio
from minio.error import S3Error

app = Flask(__name__)

# ---------------- BLOCK STORAGE (Ceph-like using volume) ----------------
if os.path.exists("/mnt/block_volume"):
    BLOCK_STORAGE_PATH = "/mnt/block_volume/ecommerce.db"
else:
    BLOCK_STORAGE_PATH = os.path.join(os.getcwd(), "my_block_data", "ecommerce.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{BLOCK_STORAGE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- OBJECT STORAGE (MinIO) ----------------
minio_client = Minio(
    "minio:9000",
    access_key="admin_user",        # ← change this
    secret_key="admin_password",    # ← change this
    secure=False
)

BUCKET_NAME = "pes2ug23cs044"   # <-- your SRN

# ---------------- DATABASE MODEL ----------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_name = db.Column(db.String(120))


@app.route('/')
def home():
    return "E-commerce Lab is Running! Send POST to /product"


@app.route('/product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    price = request.form.get('price')
    image = request.files.get('image')

    if not image:
        return jsonify({"error": "No image uploaded"}), 400

    temp_path = image.filename
    image.save(temp_path)

    try:
        # ✅ Create bucket if not exists
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)

        # ---------------- EXPERIMENT 2 (METADATA) ----------------
        file_metadata = {
            "x-amz-meta-product-name": str(name),
            "x-amz-meta-product-price": str(price)
        }

        # ✅ Upload to MinIO
        minio_client.fput_object(
            BUCKET_NAME,
            image.filename,
            temp_path,
            metadata=file_metadata
        )

        # ✅ Store in DB (Block storage)
        new_product = Product(
            name=name,
            price=float(price),
            image_name=image.filename
        )

        db.session.add(new_product)
        db.session.commit()

    except S3Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return jsonify({
        "status": "success",
        "message": "Stored data in Block (DB) and Object (MinIO)"
    })


# ---------------- RUN APP ----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    print("Starting Flask app on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)