from flask import Flask, request, jsonify, render_template, send_from_directory
import pymysql
from datetime import datetime, timedelta
import pytz
import requests
import subprocess
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
app = Flask(__name__)

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


# # MySQL 데이터베이스 연결 설정
# def get_db_connection():
#     return pymysql.connect(host='localhost',
#                            user='root',
#                            password='1234',
#                            database='imp_db',
#                            cursorclass=pymysql.cursors.DictCursor)

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr
    return ip



# 타임존 설정
seoul_tz = pytz.timezone('Asia/Seoul')




@app.route("/")
def home():
    return render_template("index.html")

@app.route('/cal')
def cal():
    return render_template("cal.html")

@app.route('/home')
def homes():
    return render_template("home.html")

# 이벤트 추가
@app.route('/events', methods=['POST'])
def add_event():
    data = request.json

    start = datetime.strptime(data['start'], '%Y-%m-%d').date()
    end = datetime.strptime(data['end'], '%Y-%m-%d').date()
    end += timedelta(days=1)  # 종료 날짜 포함되도록 조정
    cate = data.get('cate', '기타')
    text = data.get('text', '')
    # ip_address = get_client_ip()  # IP 주소 가져오기
    ip_address = request.remote_addr

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (title, start, endd, cate, text, created_ip) VALUES (%s, %s, %s, %s, %s, %s)",
        (data['title'], start, end, cate, text, ip_address)  # created_ip와 updated_ip에 IP 저장
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'Event added successfully', 'ip': ip_address})


# 이벤트 수정
@app.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.json

    start = datetime.strptime(data['start'], '%Y-%m-%d').date()
    end = datetime.strptime(data['end'], '%Y-%m-%d').date()
    end += timedelta(days=1)  # 종료 날짜 포함되도록 조정
    cate = data.get('cate', '기타')
    text = data.get('text', '')
    # ip_address = get_client_ip()  # IP 주소 가져오기
    ip_address = request.remote_addr
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE events
        SET title = %s, start = %s, endd = %s, cate = %s, text = %s, updated_ip = %s
        WHERE id = %s
        """,
        (data['title'], start, end, cate, text, ip_address, event_id)  # updated_ip에 IP 저장
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'Event updated successfully', 'ip': ip_address})


@app.route('/events', methods=['GET'])
def get_events():
    conn = get_db_connection()
    cursor = conn.cursor()

    # events 테이블과 ip_table을 조인하여 이름을 가져옵니다.
    cursor.execute("""
        SELECT e.id, e.title, e.start, e.endd, e.cate, e.text, 
               e.created_ip, e.updated_ip,
               ci.name AS created_by, ui.name AS updated_by
        FROM events e
        LEFT JOIN ip_table ci ON e.created_ip = ci.ip
        LEFT JOIN ip_table ui ON e.updated_ip = ui.ip
    """)
    
    events = cursor.fetchall()
    conn.close()

    for event in events:
        event['start'] = event['start'].isoformat()
        event['end'] = event['end'].isoformat()
    
    return jsonify(events)





@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id=%s", (event_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'Event deleted successfully'})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200  # 정상 동작일 때 HTTP 200 반환


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

