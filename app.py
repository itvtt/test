from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime, timedelta
import pytz
import requests
import subprocess
from flask import Flask, request, render_template, redirect, url_for
import psycopg2
from psycopg2 import OperationalError
from datetime import datetime
import os
from flask import Flask, request, jsonify, render_template, send_from_directory, make_response, redirect, url_for
from datetime import datetime, timedelta
import re

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


@app.template_filter('regex_search')
def regex_search(value, pattern):
    """Finds all matches of a regex pattern in a string."""
    if not value:
        return []
    matches = re.findall(pattern, value)
    return matches

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr
    return ip
def get_category_mapping():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # SQL 쿼리 실행
            sql = """
            SELECT category1, GROUP_CONCAT(category2) AS category2_list
            FROM code_posts
            WHERE is_deleted = FALSE
            GROUP BY category1
            """
            cursor.execute(sql)
            result = cursor.fetchall()
        
        # category_mapping 생성
        category_mapping = {
            row['category1']: row['category2_list'].split(',')
            for row in result
        }
        return category_mapping
    finally:
        connection.close()


def get_category1_list():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # DISTINCT로 category1만 가져오기
            sql = """
            SELECT DISTINCT category1
            FROM code_posts
            WHERE is_deleted = FALSE
            ORDER BY category1
            """
            cursor.execute(sql)
            result = cursor.fetchall()
        
        # category1 목록 생성
        return [row['category1'] for row in result]
    finally:
        connection.close()

def get_category2_list(category1):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 중복 제거를 위한 DISTINCT 쿼리
            sql = """
            SELECT DISTINCT category2
            FROM code_posts
            WHERE category1 = %s
            AND is_deleted = FALSE
            ORDER BY category2
            """
            cursor.execute(sql, (category1,))
            result = cursor.fetchall()

        # Python에서 중복 제거
        category2_set = set(row['category2'] for row in result)  # Set으로 변환
        return sorted(category2_set)  # 정렬된 리스트 반환
    finally:
        connection.close()



# 타임존 설정
seoul_tz = pytz.timezone('Asia/Seoul')


@app.route("/")
def home():
    return redirect("/abs")

@app.route('/cal')
def cal():
    return render_template("cal.html")

@app.route('/home')
def homes():
    return render_template("home.html")




@app.route("/abs")
def index():
    query = request.args.get("query", "").strip()  # 검색어 가져오기
    category1 = request.args.get("category1", "")  # URL에서 category1 가져오기
    category2 = request.args.get("category2", "")  # URL에서 category2 가져오기

    print(f"DEBUG: query={query}, category1={category1}, category2={category2}")  # 디버깅용 출력

    category_mapping = get_category_mapping()
    category1_list = get_category1_list()  # category1 리스트
    category2_list = get_category2_list(category1) if category1 else []

    page = int(request.args.get("page", 1))  # 현재 페이지 번호, 기본값은 1
    posts_per_page = 12  # 페이지당 표시할 게시물 수
    offset = (page - 1) * posts_per_page  # OFFSET 계산

    conn = get_db_connection()
    cursor = conn.cursor()

    # 검색 조건 구성
    query_condition = ""
    query_params = []

    if query:
        query_condition += """
            AND (title LIKE %s OR 
                REGEXP_REPLACE(content, '<[^>]+>', '') LIKE %s)
        """
        query_params += [f"%{query}%", f"%{query}%"]

    if category1:
        query_condition += " AND category1 = %s"
        query_params.append(category1)

    if category2:
        query_condition += " AND category2 = %s"
        query_params.append(category2)

    # 게시글 가져오기
    cursor.execute(f"""
        SELECT id, title, created_at, author, category1, category2, content, content2
        FROM code_posts
        WHERE is_deleted = FALSE {query_condition}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """, query_params + [posts_per_page, offset])
    posts = cursor.fetchall()

    # 총 게시물 수 계산
    cursor.execute(f"""
        SELECT COUNT(*) FROM code_posts
        WHERE is_deleted = FALSE {query_condition}
    """, query_params)
    total_posts = cursor.fetchone()[0]
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page

    # 카테고리 데이터
    cursor.execute("SELECT DISTINCT category1 FROM code_posts WHERE is_deleted = FALSE")
    categories1 = [row[0] for row in cursor.fetchall()]

    categories2 = []
    if category1:
        cursor.execute("SELECT DISTINCT category2 FROM code_posts WHERE category1 = %s AND is_deleted = FALSE", (category1,))
        categories2 = [row[0] for row in cursor.fetchall()]

    response = make_response(render_template(
        "abs_index.html",
        posts=posts,
        categories1=categories1,
        categories2=categories2,
        current_category1=category1,
        current_category2=category2,
        category_mapping=category_mapping,
        category1_list=category1_list,
        category2_list=category2_list,
        current_page=page,
        total_pages=total_pages,
        query=query  # 검색어 전달
    ))

    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response






@app.route("/filter/<category1>")
def filter_by_category1(category1):
    # 선택된 category1에 해당하는 게시글만 가져오기
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, created_at, author, category1, category2
        FROM code_posts
        WHERE category1 = %s
        ORDER BY created_at DESC
    """, (category1,))
    posts = cursor.fetchall()

    # category1에 따라 category2 목록 가져오기
    cursor.execute("SELECT DISTINCT category2 FROM code_posts WHERE category1 = %s", (category1,))
    categories2 = [row['category2'] for row in cursor.fetchall()]

    # 모든 카테고리1 값 가져오기
    cursor.execute("SELECT DISTINCT category1 FROM code_posts")
    categories1 = [row['category1'] for row in cursor.fetchall()]

    return render_template("abs_index.html", posts=posts, categories1=categories1, current_category1=category1, categories2=categories2)



@app.route("/filter/<category1>/<category2>")
def filter_by_category1_and_category2(category1, category2):
    # 선택된 category1 및 category2에 해당하는 게시글 가져오기
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, created_at, author, category1, category2
        FROM code_posts
        WHERE category1 = %s AND category2 = %s
        ORDER BY created_at DESC
    """, (category1, category2))
    posts = cursor.fetchall()

    # category1에 따라 category2 목록 가져오기
    cursor.execute("SELECT DISTINCT category2 FROM code_posts WHERE category1 = %s", (category1,))
    categories2 = [row['category2'] for row in cursor.fetchall()]

    # 모든 카테고리1 값 가져오기
    cursor.execute("SELECT DISTINCT category1 FROM code_posts")
    categories1 = [row['category1'] for row in cursor.fetchall()]

    return render_template("abs_index.html", posts=posts, categories1=categories1, current_category1=category1, categories2=categories2, current_category2=category2)


@app.route("/editor", methods=["GET"])
def editor():
    category1 = request.args.get("category1", "")
    category2 = request.args.get("category2", "")
    category_mapping = get_category_mapping()  # category1과 category2 매핑
    category1_list = get_category1_list()  # category1 리스트

    # category1에 따른 category2 불러오기
    category2_list = get_category2_list(category1) if category1 else []
    for key in category_mapping:
        category_mapping[key] = list(set(category_mapping[key]))  # 중복 제거

    return render_template(
        "abs_editor.html",
        category1=category1,
        category2=category2,
        category_mapping=category_mapping,
        category1_list=category1_list,
        category2_list=category2_list,
    )



@app.route("/submit", methods=["POST"])
def submit():
    title = request.form["title"]
    content = request.form["content"]
    category1 = request.form["category1"]
    category2 = request.form["category2"]
    author = os.getlogin()  # 현재 Windows 사용자 이름 가져오기

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO code_posts (title, content, category1, category2, author, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (title, content, category1, category2, author))
    conn.commit()
    return redirect("/abs")

# @app.route("/post/<int:post_id>")
# def post_detail(post_id):
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     # 게시글 데이터 가져오기
#     cursor.execute("""
#         SELECT id, title, content, content2, author, created_at, updated_at, updated_by,
#                deleted_at, deleted_by, category1, category2
#         FROM code_posts
#         WHERE id = %s
#     """, (post_id,))
#     post = cursor.fetchone()

#     # print(post)
#     category1 = request.args.get("category1", "")
#     category2 = request.args.get("category2", "")
#     page = request.args.get("page", "1") 
#     category_mapping = get_category_mapping() 
#     category1_list = get_category1_list()  # category1 리스트

#     # category1에 따른 category2 불러오기
#     category2_list = get_category2_list(category1) if category1 else []
#     for key in category_mapping:
#         category_mapping[key] = list(set(category_mapping[key]))  # 중복 제거
#     # print(category1)
#     if not post:
#         return "게시글을 찾을 수 없습니다.", 404

#     if not post:
#         return "게시글을 찾을 수 없습니다.", 404

#     # show_code 값에 따라 content 또는 content2 선택
#     show_code = request.args.get("show_code", "false").lower() == "true"
#     content_to_display = post["content2"] if show_code else post["content"]

#     # 디버깅용 출력
#     print(f"Post ID: {post_id}, Show Code: {show_code}")
#     print(f"Content to Display: {content_to_display}")

#     return render_template(
#         "abs_post_detail.html",
#         post=post,
#         content_to_display=content_to_display,
#         show_code=show_code,
#         category1=category1,
#         category2=category2,
#         category_mapping=category_mapping,
#         category1_list=category1_list,
#         category2_list=category2_list,
#         current_page=page
#     )


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def post_detail(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 게시글 데이터 가져오기
    cursor.execute("""
        SELECT id, title, content, content2, author, created_at, updated_at, updated_by,
               deleted_at, deleted_by, category1, category2
        FROM code_posts
        WHERE id = %s
    """, (post_id,))
    post = cursor.fetchone()

    if not post:
        return "게시글을 찾을 수 없습니다.", 404
    # 댓글 데이터 가져오기
    cursor.execute("""
        SELECT id, comment, author, created_at, updated_at
        FROM comments
        WHERE post_id = %s
        ORDER BY created_at asc
    """, (post_id,))
    comments = cursor.fetchall()
    for comment in comments:
        comment['created_at'] = comment['created_at'].strftime("%Y-%m-%d")
        if comment['updated_at']:
            comment['updated_at'] = comment['updated_at'].strftime("%Y-%m-%d")

    
    # 대댓글 데이터 가져오기
    cursor.execute("""
        SELECT r.id AS reply_id, r.comment_id, r.reply, r.author AS reply_author,
               r.created_at AS reply_created_at, r.updated_at AS reply_updated_at
        FROM replies r
        INNER JOIN comments c ON r.comment_id = c.id
        WHERE c.post_id = %s
        ORDER BY r.created_at ASC
    """, (post_id,))
    replies = cursor.fetchall()

    # 댓글에 대댓글 추가하기
    comment_dict = {comment["id"]: comment for comment in comments}
    for reply in replies:
        # 날짜 포맷 변경
        if reply["reply_created_at"]:
            reply["reply_created_at"] = reply["reply_created_at"].strftime('%Y-%m-%d')
        if reply["reply_updated_at"]:
            reply["reply_updated_at"] = reply["reply_updated_at"].strftime('%Y-%m-%d')


    # 댓글에 대댓글 추가하기
    comment_dict = {comment["id"]: comment for comment in comments}
    for reply in replies:
        comment_id = reply["comment_id"]
        if "replies" not in comment_dict[comment_id]:
            comment_dict[comment_id]["replies"] = []
   
        comment_dict[comment_id]["replies"].append(reply)


    # 게시글 카테고리 관련 데이터 가져오기
    category1 = request.args.get("category1", "")
    category2 = request.args.get("category2", "")
    page = request.args.get("page", "1")
    category_mapping = get_category_mapping()
    category1_list = get_category1_list()
    category2_list = get_category2_list(category1) if category1 else []
    for key in category_mapping:
        category_mapping[key] = list(set(category_mapping[key]))  # 중복 제거

    # show_code 값에 따라 content 또는 content2 선택
    show_code = request.args.get("show_code", "false").lower() == "true"
    content_to_display = post["content2"] if show_code else post["content"]

    # 디버깅용 출력
    print(f"Post ID: {post_id}, Show Code: {show_code}")
    print(f"Content to Display: {content_to_display}")

    # 댓글 작성 처리
    if request.method == "POST":
        new_comment = request.form.get("comment")
        author = username

        if not new_comment or not author:
            return "댓글과 작성자를 입력해주세요.", 400

        cursor.execute("""
            INSERT INTO comments (post_id, comment, author)
            VALUES (%s, %s, %s)
        """, (post_id, new_comment, author))
        conn.commit()

        return redirect(f"/post/{post_id}")

    conn.close()

    return render_template(
        "abs_post_detail.html",
        post=post,
        comments=comments,
        content_to_display=content_to_display,
        show_code=show_code,
        category1=category1,
        category2=category2,
        category_mapping=category_mapping,
        category1_list=category1_list,
        category2_list=category2_list,
        current_page=page
    )


@app.route("/post/<int:post_id>/comment/<int:comment_id>/edit", methods=["POST"])
def edit_comment(post_id, comment_id):
    new_comment = request.form.get("comment")

    if not new_comment:
        return "수정할 댓글을 입력해주세요.", 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE comments
        SET comment = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s AND post_id = %s
    """, (new_comment, comment_id, post_id))
    conn.commit()
    conn.close()

    return redirect(f"/post/{post_id}")



@app.route("/post/<int:post_id>/comment/<int:comment_id>/delete", methods=["POST"])
def delete_comment(post_id, comment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM comments
        WHERE id = %s AND post_id = %s
    """, (comment_id, post_id))
    conn.commit()
    conn.close()

    return redirect(f"/post/{post_id}")



# @app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
# def edit_post(post_id):
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     category_mapping = get_category_mapping() or {}
#     category1_list = get_category1_list()

#     # GET 파라미터에서 기존 목록 정보를 가져옴
#     category1_param = request.args.get("category1", "")
#     category2_param = request.args.get("category2", "")
#     page_param = request.args.get("page", 1)
#     show_code = request.args.get("show_code", "false").lower() == "true"

#     if request.method == "POST":
#         # POST 요청: 데이터 업데이트
#         title = request.form["title"]
#         content = request.form["content"]
#         category1 = request.form["category1"]
#         category2 = request.form["category2"]

#         # show_code 값에 따라 content와 content2를 업데이트
#         content_field = "content2" if show_code else "content"

#         cursor.execute(f"""
#             UPDATE code_posts
#             SET title = %s, {content_field} = %s, category1 = %s, category2 = %s,
#                 updated_at = NOW(), updated_by = %s
#             WHERE id = %s
#         """, (title, content, category1, category2, os.getlogin(), post_id))
#         conn.commit()

#         # 수정 후 상세 페이지로 리다이렉트 (카테고리, 페이지 정보 포함)
#         return redirect(url_for(
#             "post_detail",
#             post_id=post_id,
#             show_code=show_code,
#             category1=category1_param,
#             category2=category2_param,
#             page=page_param,
#         ))

#     # GET 요청: 게시글 데이터 불러오기
#     cursor.execute("""
#         SELECT id, title, content, content2, category1, category2
#         FROM code_posts
#         WHERE id = %s
#     """, (post_id,))
#     post = cursor.fetchone()

#     if not post:
#         return "게시글을 찾을 수 없습니다.", 404

#     # show_code 값에 따라 적절한 내용 불러오기
#     content_to_edit = post["content2"] if show_code else post["content"]

#     # Deduplicated category2 list based on the selected category1
#     category2_list = get_category2_list(post["category1"])
#     for key in category_mapping:
#         category_mapping[key] = list(set(category_mapping[key]))  # 중복 제거

#     return render_template(
#         "abs_edit_post.html",
#         post=post,
#         category_mapping=category_mapping,
#         category1_list=category1_list,
#         current_category1=post["category1"],
#         current_category2=post["category2"],
#         category2_list=category2_list,
#         content_to_edit=content_to_edit,
#         show_code=show_code,
#         category1_param=category1_param,  # 목록 페이지 정보 전달
#         category2_param=category2_param,
#         page_param=page_param,
#     )

@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        # POST 요청: 데이터 업데이트
        title = request.form["title"]
        content = request.form["content"]
        category1 = request.form["category1"]  # 카테고리 1 값
        category2 = request.form["category2"]  # 카테고리 2 값
        page = request.form.get("page", 1)  # 페이지 값 (기본값 1)
        show_code = request.args.get("show_code", "false").lower() == "true"

    # 디버깅 로그
        print(f"DEBUG: category1={category1}, category2={category2}")
        if not category1 or not category2:
            return "카테고리 정보가 누락되었습니다.", 400
        # show_code 값에 따라 content와 content2를 업데이트
        content_field = "content2" if show_code else "content"

        cursor.execute(f"""
            UPDATE code_posts
            SET title = %s, {content_field} = %s, category1 = %s, category2 = %s,
                updated_at = NOW(), updated_by = %s
            WHERE id = %s
        """, (title, content, category1, category2, os.getlogin(), post_id))
        conn.commit()

        # 수정 후 상세 페이지로 리다이렉트 (카테고리 및 페이지 정보 포함)
        return redirect(url_for(
            "post_detail",
            post_id=post_id,
            show_code=show_code,
            category1=category1,
            category2=category2,
            page=page
        ))

    # GET 요청 처리
    cursor.execute("""
        SELECT id, title, content, content2, category1, category2
        FROM code_posts
        WHERE id = %s
    """, (post_id,))
    post = cursor.fetchone()

    if not post:
        return "게시글을 찾을 수 없습니다.", 404

    # show_code 값에 따라 적절한 내용 불러오기
    show_code = request.args.get("show_code", "false").lower() == "true"
    content_to_edit = post["content2"] if show_code else post["content"]

    category_mapping = get_category_mapping() or {}
    category1_list = get_category1_list()
    category2_list = get_category2_list(post["category1"])

    # 카테고리 데이터 가져오기
    category1_list = get_category1_list()  # 모든 category1 리스트
    category_mapping = get_category_mapping()  # category1과 category2 매핑

    # 중복 제거
    category1_list = list(set(category1_list))
    for key in category_mapping:
        category_mapping[key] = list(set(category_mapping[key]))

    return render_template(
        "abs_edit_post.html",
        post=post,
        category_mapping=category_mapping,
        category1_list=category1_list,
        current_category1=post["category1"],
        current_category2=post["category2"],
        category2_list=category2_list,
        content_to_edit=content_to_edit,
        show_code=show_code,
        page=request.args.get("page", 1),  # 페이지 정보 전달
    )







@app.route("/post/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    deleted_at = datetime.now()  # 현재 시간
    deleted_by = os.getlogin()  # 현재 시스템 사용자 이름

    cursor.execute("""
        UPDATE code_posts
        SET is_deleted = TRUE,
            deleted_at = %s,
            deleted_by = %s
        WHERE id = %s
    """, (deleted_at, deleted_by, post_id))
    conn.commit()
    return redirect("/abs")



# 대댓글 버젼
@app.route("/post/<int:post_id>/comment/<int:comment_id>/reply", methods=["POST"])
def add_reply(post_id, comment_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # JSON 데이터 가져오기
    data = request.get_json()
    new_reply = data.get("reply")
    author = username  # 현재 로그인한 사용자 이름 가져오기

    if not new_reply:
        return jsonify({"error": "대댓글 내용을 입력해주세요."}), 400

    # 대댓글 삽입
    cursor.execute("""
        INSERT INTO replies (comment_id, reply, author)
        VALUES (%s, %s, %s)
    """, (comment_id, new_reply, author))
    conn.commit()
    conn.close()

    return jsonify({"message": "대댓글이 작성되었습니다."}), 201

@app.route("/reply/<int:reply_id>/edit", methods=["POST"])
def edit_reply(reply_id):
    data = request.get_json()
    new_reply = data.get("reply")
    updated_at = datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE replies
            SET reply = %s, updated_at = %s
            WHERE id = %s
        """, (new_reply, updated_at, reply_id))
        conn.commit()

        # 날짜를 원하는 형식으로 포맷
        formatted_date = updated_at.strftime('%Y-%m-%d')
        return jsonify({"message": "대댓글이 수정되었습니다.", "updated_at": formatted_date}), 200
    except Exception as e:
        print(f"Error updating reply: {e}")
        conn.rollback()
        return jsonify({"error": "대댓글 수정 중 오류가 발생했습니다."}), 500
    finally:
        conn.close()


@app.route("/reply/<int:reply_id>/delete", methods=["DELETE"])
def delete_reply(reply_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM replies WHERE id = %s", (reply_id,))
        conn.commit()
        return jsonify({"message": "대댓글이 삭제되었습니다."}), 200
    except Exception as e:
        print(f"Error deleting reply: {e}")
        conn.rollback()
        return jsonify({"error": "대댓글 삭제 중 오류가 발생했습니다."}), 500
    finally:
        conn.close()



if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)