from flask import Flask, request, render_template, redirect, url_for
import psycopg2
from psycopg2 import OperationalError
from datetime import datetime
import os

# 환경변수 읽기
host = os.getenv("host")
user = os.getenv("user")
password = os.getenv("password")
database = os.getenv("database")

app = Flask(__name__)

username = os.getenv("USERNAME") or "default_user"
print(username)

def get_db_connection():
    """데이터베이스 연결 생성"""
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database,
        )
        return connection
    except OperationalError as e:
        print(f"데이터베이스 연결 실패: {e}")
        raise

@app.route("/")
def index():
    category1 = request.args.get("category1", "")  # URL에서 category1 가져오기
    category2 = request.args.get("category2", "")  # URL에서 category2 가져오기

    with get_db_connection() as db:
        with db.cursor() as cursor:
            if category1 and category2:
                cursor.execute("""
                    SELECT id, title, created_at, author, category1, category2
                    FROM posts
                    WHERE category1 = %s AND category2 = %s AND is_deleted = FALSE
                    ORDER BY created_at DESC
                """, (category1, category2))
            elif category1:
                cursor.execute("""
                    SELECT id, title, created_at, author, category1, category2
                    FROM posts
                    WHERE category1 = %s AND is_deleted = FALSE
                    ORDER BY created_at DESC
                """, (category1,))
            else:
                cursor.execute("""
                    SELECT id, title, created_at, author, category1, category2
                    FROM posts WHERE is_deleted = FALSE
                    ORDER BY created_at DESC
                """)

            posts = cursor.fetchall()
            cursor.execute("SELECT DISTINCT category1 FROM posts WHERE is_deleted = FALSE")
            categories1 = [row[0] for row in cursor.fetchall()]

            categories2 = []
            if category1:
                cursor.execute("SELECT DISTINCT category2 FROM posts WHERE category1 = %s AND is_deleted = FALSE", (category1,))
                categories2 = [row[0] for row in cursor.fetchall()]

    return render_template(
        "index.html",
        posts=posts,
        categories1=categories1,
        categories2=categories2,
        current_category1=category1,
        current_category2=category2
    )

@app.route("/filter/<category1>")
def filter_by_category1(category1):
    with get_db_connection() as db:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, created_at, author, category1, category2
                FROM posts
                WHERE category1 = %s AND is_deleted = FALSE
                ORDER BY created_at DESC
            """, (category1,))
            posts = cursor.fetchall()

            cursor.execute("SELECT DISTINCT category2 FROM posts WHERE category1 = %s AND is_deleted = FALSE", (category1,))
            categories2 = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT category1 FROM posts WHERE is_deleted = FALSE")
            categories1 = [row[0] for row in cursor.fetchall()]

    return render_template("index.html", posts=posts, categories1=categories1, current_category1=category1, categories2=categories2)

@app.route("/filter/<category1>/<category2>")
def filter_by_category1_and_category2(category1, category2):
    with get_db_connection() as db:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, created_at, author, category1, category2
                FROM posts
                WHERE category1 = %s AND category2 = %s AND is_deleted = FALSE
                ORDER BY created_at DESC
            """, (category1, category2))
            posts = cursor.fetchall()

            cursor.execute("SELECT DISTINCT category2 FROM posts WHERE category1 = %s AND is_deleted = FALSE", (category1,))
            categories2 = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT category1 FROM posts WHERE is_deleted = FALSE")
            categories1 = [row[0] for row in cursor.fetchall()]

    return render_template("index.html", posts=posts, categories1=categories1, current_category1=category1, categories2=categories2, current_category2=category2)

@app.route("/editor", methods=["GET"])
def editor():
    category1 = request.args.get("category1", "")
    category2 = request.args.get("category2", "")
    category_mapping = {
        "AMAT-CENTURA": ["EFEM", "TM", "DPN", "RTP", "CSF"],
        "AMAT-VANTAGE": ["EFEM", "RTP"],
        "FTP": ["EFEM", "CH", "FPSU", "SM", "MPSU"],
        "LSA": ["EFEM", "CH", "H/X", "TR"],
        "HPA": ["EFEM", "CH", "H/X", "CSF"],
        "문의": ["질문건의"],
    }
    return render_template("editor.html", category1=category1, category2=category2, category_mapping=category_mapping)

@app.route("/submit", methods=["POST"])
def submit():
    title = request.form["title"]
    content = request.form["content"]
    category1 = request.form["category1"]
    category2 = request.form["category2"]
    author = username  # 현재 사용자 이름 가져오기

    with get_db_connection() as db:
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO posts (title, content, category1, category2, author, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (title, content, category1, category2, author))
            db.commit()
    return redirect("/")

@app.route("/post/<int:post_id>")
def post_detail(post_id):
    with get_db_connection() as db:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content, author, created_at, updated_at, updated_by, deleted_at, deleted_by, category1, category2
                FROM posts
                WHERE id = %s AND is_deleted = FALSE
            """, (post_id,))
            post = cursor.fetchone()

    if not post:
        return "게시글을 찾을 수 없습니다.", 404

    return render_template("post_detail.html", post=post)

@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    with get_db_connection() as db:
        with db.cursor() as cursor:
            if request.method == "POST":
                title = request.form["title"]
                content = request.form["content"]
                category1 = request.form["category1"]
                category2 = request.form["category2"]
                updated_by = username

                cursor.execute("""
                    UPDATE posts
                    SET title = %s, content = %s, category1 = %s, category2 = %s,
                        updated_at = NOW(), updated_by = %s
                    WHERE id = %s AND is_deleted = FALSE
                """, (title, content, category1, category2, updated_by, post_id))
                db.commit()
                return redirect(url_for("post_detail", post_id=post_id))

            cursor.execute("""
                SELECT id, title, content, category1, category2
                FROM posts WHERE id = %s AND is_deleted = FALSE
            """, (post_id,))
            post = cursor.fetchone()

    if not post:
        return "게시글을 찾을 수 없습니다.", 404

    return render_template("edit_post.html", post=post)

@app.route("/post/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    deleted_at = datetime.now()
    deleted_by = username

    with get_db_connection() as db:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE posts
                SET is_deleted = TRUE, deleted_at = %s, deleted_by = %s
                WHERE id = %s
            """, (deleted_at, deleted_by, post_id))
            db.commit()

    return redirect("/")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
