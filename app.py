import os
import pymysql
import boto3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "student-app-secret-key-2026")

# S3 Configuration
bucket_name = os.environ.get("S3_BUCKET_NAME")
region = os.environ.get("AWS_REGION", "ap-south-1")

def get_db_connection():
    """
    Establish a connection to the RDS MySQL database using environment variables.
    Re-connects per request to avoid MySQL 'server has gone away' timeout errors.
    """
    return pymysql.connect(
        host=os.environ.get("DB_HOST"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME", "studentdb"),
        autocommit=True
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    course = request.form.get('course')
    photo = request.files.get('photo')

    if not name or not email or not course or not photo:
        return "All fields including photo are required.", 400

    # Upload photo to S3
    # boto3 automatically retrieves short-lived temporary credentials from the attached EC2 IAM Role
    s3 = boto3.client('s3', region_name=region)
    filename = photo.filename

    s3.upload_fileobj(
        photo,
        bucket_name,
        filename,
        ExtraArgs={'ContentType': photo.content_type} if photo.content_type else None
    )

    photo_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{filename}"

    # Insert registration record into MySQL
    db = get_db_connection()
    try:
        with db.cursor() as cursor:
            sql = """
            INSERT INTO students (name, email, course, photo_url)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (name, email, course, photo_url))
        db.commit()
    finally:
        db.close()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Registration Successful</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f7f6; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
            .card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 480px; text-align: center; }}
            h2 {{ color: #16a34a; margin-top: 0; }}
            img {{ width: 140px; height: 140px; object-fit: cover; border-radius: 50%; margin: 15px 0; border: 3px solid #e2e8f0; }}
            p {{ color: #475569; margin: 8px 0; }}
            .btn {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Student Registered Successfully!</h2>
            <img src="{photo_url}" alt="Student Photo" onerror="this.src='https://via.placeholder.com/140?text=Photo';">
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Course:</strong> {course}</p>
            <p><strong>Photo URL:</strong> <a href="{photo_url}" target="_blank">View on S3</a></p>
            <a href="/" class="btn">Register Another Student</a>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
