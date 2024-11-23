from flask import Flask, request, render_template, redirect, url_for
import psycopg2
import os
from datetime import datetime

# 환경변수 읽기
host = os.getenv("host")
user = os.getenv("user")
password= os.getenv("password")
database = os.getenv("database")

app = Flask(__name__)

# PostgreSQL 연결 설정
db = psycopg2.connect(
    host=host,
    user=user,  # PostgreSQL 사용자 이름
    password=password,  # PostgreSQL 비밀번호
    database=database,  # 데이터베이스 이름
)


username = os.getenv("USER") or os.getenv("USERNAME") or "default_user"
print(username)


@app.route("/")
def index():
    category1 = request.args.get("category1", "")  # URL에서 category1 가져오기
    category2 = request.args.get("category2", "")  # URL에서 category2 가져오기

    cursor = db.cursor()

    if category1 and category2:
        # category1과 category2로 필터링
        cursor.execute("""
            SELECT id, title, created_at, author, category1, category2
            FROM posts
            WHERE category1 = %s AND category2 = %s AND is_deleted = FALSE
            ORDER BY created_at DESC
        """, (category1, category2))
    elif category1:
        # category1만 필터링
        cursor.execute("""
            SELECT id, title, created_at, author, category1, category2
            FROM posts
            WHERE category1 = %s AND is_deleted = FALSE
            ORDER BY created_at DESC
        """, (category1,))
    else:
        # 모든 게시글
        cursor.execute("""
            SELECT id, title, created_at, author, category1, category2
            FROM posts WHERE is_deleted = FALSE
            ORDER BY created_at DESC
        """)

    posts = cursor.fetchall()

    # 모든 카테고리1 값 가져오기
    cursor.execute("SELECT DISTINCT category1 FROM posts WHERE is_deleted = FALSE")
    categories1 = [row[0] for row in cursor.fetchall()]

    # 선택된 category1에 따라 category2 목록 가져오기
    categories2 = []
    if category1:
        cursor.execute("SELECT DISTINCT category2 FROM posts WHERE category1 = %s AND is_deleted = FALSE", (category1,))
        categories2 = [row[0] for row in cursor.fetchall()]

    # 기본 렌더링
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
    # 선택된 category1에 해당하는 게시글만 가져오기
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, title, created_at, author, category1, category2
        FROM posts
        WHERE category1 = %s
        ORDER BY created_at DESC
    """, (category1,))
    posts = cursor.fetchall()

    # category1에 따라 category2 목록 가져오기
    cursor.execute("SELECT DISTINCT category2 FROM posts WHERE category1 = %s", (category1,))
    categories2 = [row[0] for row in cursor.fetchall()]

    # 모든 카테고리1 값 가져오기
    cursor.execute("SELECT DISTINCT category1 FROM posts")
    categories1 = [row[0] for row in cursor.fetchall()]

    return render_template("index.html", posts=posts, categories1=categories1, current_category1=category1, categories2=categories2)



@app.route("/filter/<category1>/<category2>")
def filter_by_category1_and_category2(category1, category2):
    # 선택된 category1 및 category2에 해당하는 게시글 가져오기
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, title, created_at, author, category1, category2
        FROM posts
        WHERE category1 = %s AND category2 = %s
        ORDER BY created_at DESC
    """, (category1, category2))
    posts = cursor.fetchall()

    # category1에 따라 category2 목록 가져오기
    cursor.execute("SELECT DISTINCT category2 FROM posts WHERE category1 = %s", (category1,))
    categories2 = [row[0] for row in cursor.fetchall()]

    # 모든 카테고리1 값 가져오기
    cursor.execute("SELECT DISTINCT category1 FROM posts")
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
    author = username  # 현재 Windows 사용자 이름 가져오기

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO posts (title, content, category1, category2, author, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (title, content, category1, category2, author))
    db.commit()
    return redirect("/")



@app.route("/post/<int:post_id>")
def post_detail(post_id):
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, title, content, author, created_at, updated_at, updated_by, deleted_at, deleted_by, category1, category2
        FROM posts
        WHERE id = %s
    """, (post_id,))
    post = cursor.fetchone()

    category1 = request.args.get("category1", "")
    category2 = request.args.get("category2", "")

    if not post:
        return "게시글을 찾을 수 없습니다.", 404

    return render_template(
        "post_detail.html",
        post=post,
        category1=category1,
        category2=category2
    )


@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    cursor = db.cursor()
    
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        category1 = request.form["category1"]
        category2 = request.form["category2"]
        updated_by = username  # 현재 사용자 이름 가져오기

        cursor.execute("""
            UPDATE posts
            SET title = %s, content = %s, category1 = %s, category2 = %s,
                updated_at = NOW(), updated_by = %s
            WHERE id = %s
        """, (title, content, category1, category2, updated_by, post_id))
        db.commit()
        return redirect(url_for("post_detail", post_id=post_id))

    # GET 요청: 게시글 데이터를 불러옵니다.
    cursor.execute("""
        SELECT id, title, content, category1, category2
        FROM posts WHERE id = %s
    """, (post_id,))
    post = cursor.fetchone()
    if not post:
        return "게시글을 찾을 수 없습니다.", 404

    return render_template("edit_post.html", post=post)



@app.route("/post/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    cursor = db.cursor()
    deleted_at = datetime.now()  # 현재 시간
    deleted_by = username # 현재 시스템 사용자 이름

    cursor.execute("""
        UPDATE posts
        SET is_deleted = TRUE,
            deleted_at = %s,
            deleted_by = %s
        WHERE id = %s
    """, (deleted_at, deleted_by, post_id))
    db.commit()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    # 0.0.0.0에 바인딩하여 외부에서 접근 가능하게 설정
    app.run(host="0.0.0.0", port=port, debug=True)