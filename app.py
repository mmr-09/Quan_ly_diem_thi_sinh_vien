# app.py - Flask Backend API - ĐỒNG BỘ VỚI FRONTEND
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
import mysql.connector
from mysql.connector import Error
import jwt
from datetime import datetime, timedelta, date, time
from functools import wraps
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# ✅ CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ===============================
# DATABASE CONFIG
# ===============================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'felis0208',  # ⚠️ ĐỔI PASSWORD NÀY THEO DATABASE CỦA BẠN
    'database': 'quan_ly_diem_thi'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"❌ Database Connection Error: {e}")
        return None

# ===============================
# HELPER FUNCTION - Serialize datetime
# ===============================
def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, time):
        return obj.strftime('%H:%M:%S')
    elif isinstance(obj, timedelta):
        total_seconds = int(obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return obj

def convert_query_result(data):
    if isinstance(data, list):
        return [convert_query_result(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_datetime(value) for key, value in data.items()}
    return data

# ===============================
# TOKEN AUTHENTICATION
# ===============================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({
            'message': f'Upload thành công {success_count} bản ghi',
            'errors': error_list
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Upload Excel Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 400

# ===============================
# 6️⃣ TÌM KIẾM & THỐNG KÊ
# ===============================
@app.route('/api/thong-ke/sinh-vien-gioi', methods=['GET'])
@token_required
def get_sinh_vien_gioi(current_user):
    """Danh sách sinh viên giỏi (GPA > 3.0)"""
    try:
        lop_id = request.args.get('lop_id')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                sv.id,
                sv.ma_sinh_vien,
                nd.ho_ten,
                l.ma_lop,
                l.ten_lop,
                sv.gpa,
                sv.tong_tin_chi,
                nd.email
            FROM sinh_vien sv
            JOIN nguoi_dung nd ON sv.nguoi_dung_id = nd.id
            JOIN lop l ON sv.lop_id = l.id
            WHERE sv.gpa > 3.0
        """
        
        params = []
        if lop_id:
            query += " AND sv.lop_id = %s"
            params.append(lop_id)
        
        query += " ORDER BY sv.gpa DESC"
        
        cursor.execute(query, params)
        sinh_vien = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(convert_query_result(sinh_vien)), 200
        
    except Exception as e:
        print(f"❌ Get Sinh Vien Gioi Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/thong-ke/lop', methods=['GET'])
@token_required
def get_thong_ke_lop(current_user):
    """Thống kê theo lớp"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM view_thong_ke_lop")
        thong_ke = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(convert_query_result(thong_ke)), 200
        
    except Exception as e:
        print(f"❌ Get Thong Ke Lop Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/lop', methods=['GET'])
@token_required
def get_lop(current_user):
    """Danh sách lớp"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lop ORDER BY khoa_hoc DESC, ma_lop")
        lop = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(convert_query_result(lop)), 200
        
    except Exception as e:
        print(f"❌ Get Lop Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ===============================
# 7️⃣ SOCKET.IO - REAL-TIME
# ===============================
@socketio.on('connect')
def handle_connect():
    print(f"✅ Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"❌ Client disconnected: {request.sid}")

@socketio.on('join_hoc_phan')
def handle_join_hoc_phan(data):
    hoc_phan_id = data.get('hoc_phan_id')
    if hoc_phan_id:
        room = f"hoc_phan_{hoc_phan_id}"
        join_room(room)
        print(f"🚪 Client {request.sid} joined room: {room}")

# ===============================
# 🚀 START SERVER
# ===============================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 HỆ THỐNG QUẢN LÝ SINH VIÊN & ĐIỂM THI")
    print("=" * 60)
    print(f"📡 Server: http://localhost:5000")
    print(f"🔌 Socket.IO: Enabled")
    print(f"📊 Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
    print("=" * 60)
    print("\n💡 Demo accounts:")
    print("   👨‍🏫 Giảng viên: gv001 / 123456")
    print("   👨‍🎓 Sinh viên: sv001 / 123456")
    print("=" * 60)
    print("\n✅ KIỂM TRA KẾT NỐI:")
    print("   1. Test database: http://localhost:5000/api/test/db")
    print("   2. Mở trình duyệt và truy cập: http://localhost:5000")
    print("=" * 60)
    print("\n⚠️  LƯU Ý:")
    print("   - Đảm bảo MySQL đang chạy")
    print("   - Kiểm tra DB_CONFIG trong app.py")
    print("   - Frontend phải chạy trên cùng domain hoặc enable CORS")
    print("=" * 60 + "\n")
    
    # Kiểm tra kết nối database ngay khi start
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM nguoi_dung")
            count = cursor.fetchone()[0]
            print(f"✅ Database connected! Found {count} users.\n")
            cursor.close()
            conn.close()
        else:
            print("❌ WARNING: Cannot connect to database! Check DB_CONFIG.\n")
    except Exception as e:
        print(f"❌ Database error: {e}\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split()[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except Exception as e:
            return jsonify({'message': f'Token is invalid: {str(e)}'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# ===============================
# ✅ TEST ENDPOINT - PHẢI TEST ĐẦU TIÊN
# ===============================
@app.route('/api/test/db', methods=['GET'])
def test_db():
    """Kiểm tra kết nối database"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'status': 'error',
                'message': 'Cannot connect to database. Check DB_CONFIG in app.py'
            }), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Test queries
        cursor.execute("SELECT COUNT(*) as count FROM nguoi_dung")
        users = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as count FROM sinh_vien")
        students = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as count FROM giang_vien")
        teachers = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'message': 'Database connected successfully ✅',
            'database': DB_CONFIG['database'],
            'stats': {
                'users': users['count'],
                'students': students['count'],
                'teachers': teachers['count']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500

# ===============================
# 1️⃣ AUTHENTICATION - ✅ ĐỒNG BỘ VỚI FRONTEND
# ===============================
@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint - đồng bộ với frontend expectations"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500

        cursor = conn.cursor(dictionary=True)
        
        # Tìm người dùng
        cursor.execute("SELECT * FROM nguoi_dung WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user or user['password'] != password:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Invalid username or password'}), 401
        
        # Lấy thông tin chi tiết
        user_detail = None
        
        if user['vai_tro'] == 'sinh_vien':
            cursor.execute("""
                SELECT sv.*, l.ten_lop, l.ma_lop 
                FROM sinh_vien sv 
                JOIN lop l ON sv.lop_id = l.id 
                WHERE sv.nguoi_dung_id = %s
            """, (user['id'],))
            user_detail = cursor.fetchone()
        elif user['vai_tro'] == 'giang_vien':
            cursor.execute("""
                SELECT * FROM giang_vien WHERE nguoi_dung_id = %s
            """, (user['id'],))
            user_detail = cursor.fetchone()
        
        cursor.close()
        conn.close()

        # ✅ Tạo JWT token
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'vai_tro': user['vai_tro'],
            'detail_id': user_detail['id'] if user_detail else None,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        # ✅ QUAN TRỌNG: Response format phải khớp với frontend
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username'],
                'ho_ten': user['ho_ten'],
                'full_name': user['ho_ten'],  # ✅ Thêm alias
                'email': user['email'],
                'role': 'teacher' if user['vai_tro'] == 'giang_vien' else 'student',  # ✅ Frontend mapping
                'vai_tro': user['vai_tro'],  # ✅ Giữ original
                'detail': convert_query_result(user_detail) if user_detail else {'id': user['id']},
                'user_id': user['id']  # ✅ Thêm cho frontend
            },
            'token': token
        }), 200
        
    except Exception as e:
        print(f"❌ Login Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Server error: {str(e)}'}), 500

# ===============================
# 2️⃣ SINH VIÊN - XEM ĐIỂM
# ===============================
@app.route('/api/sinh-vien/bang-diem/<int:sinh_vien_id>', methods=['GET'])
@token_required
def get_bang_diem(current_user, sinh_vien_id):
    """Lấy bảng điểm sinh viên"""
    try:
        # Kiểm tra quyền
        if current_user['vai_tro'] == 'sinh_vien' and current_user.get('detail_id') != sinh_vien_id:
            return jsonify({'message': 'Unauthorized'}), 403
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                dt.id,
                mh.ma_mon,
                mh.ten_mon,
                mh.so_tin_chi,
                hp.hoc_ky,
                hp.nam_hoc,
                dt.diem_chuyen_can,
                dt.diem_giua_ky,
                dt.diem_cuoi_ky,
                dt.diem_tong_ket,
                dt.diem_chu,
                dt.ghi_chu,
                gv.ma_giang_vien,
                nd.ho_ten AS ten_giang_vien
            FROM diem_thi dt
            JOIN hoc_phan hp ON dt.hoc_phan_id = hp.id
            JOIN mon_hoc mh ON hp.mon_hoc_id = mh.id
            JOIN giang_vien gv ON hp.giang_vien_id = gv.id
            JOIN nguoi_dung nd ON gv.nguoi_dung_id = nd.id
            WHERE dt.sinh_vien_id = %s
            ORDER BY hp.nam_hoc DESC, hp.hoc_ky DESC, mh.ma_mon
        """, (sinh_vien_id,))
        
        diem = cursor.fetchall()
        
        # Lấy GPA
        cursor.execute("SELECT gpa, tong_tin_chi FROM sinh_vien WHERE id = %s", (sinh_vien_id,))
        gpa_info = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # ✅ Response format khớp frontend
        return jsonify({
            'diem': convert_query_result(diem),
            'gpa': float(gpa_info['gpa']) if gpa_info and gpa_info['gpa'] else 0.0,
            'tong_tin_chi': gpa_info['tong_tin_chi'] if gpa_info else 0
        }), 200
        
    except Exception as e:
        print(f"❌ Get Bang Diem Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/sinh-vien/thong-ke/<int:sinh_vien_id>', methods=['GET'])
@token_required
def get_thong_ke_sinh_vien(current_user, sinh_vien_id):
    """Thống kê học tập sinh viên"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Thống kê điểm theo học kỳ
        cursor.execute("""
            SELECT 
                hp.hoc_ky,
                hp.nam_hoc,
                COUNT(*) AS so_mon,
                ROUND(AVG(dt.diem_tong_ket), 2) AS diem_trung_binh,
                SUM(mh.so_tin_chi) AS tong_tin_chi
            FROM diem_thi dt
            JOIN hoc_phan hp ON dt.hoc_phan_id = hp.id
            JOIN mon_hoc mh ON hp.mon_hoc_id = mh.id
            WHERE dt.sinh_vien_id = %s
            GROUP BY hp.hoc_ky, hp.nam_hoc
            ORDER BY hp.nam_hoc DESC, hp.hoc_ky DESC
        """, (sinh_vien_id,))
        
        thong_ke_hoc_ky = cursor.fetchall()
        
        # Phân loại điểm chữ
        cursor.execute("""
            SELECT 
                diem_chu,
                COUNT(*) AS so_luong
            FROM diem_thi
            WHERE sinh_vien_id = %s
            GROUP BY diem_chu
            ORDER BY 
                CASE diem_chu
                    WHEN 'A+' THEN 1
                    WHEN 'A' THEN 2
                    WHEN 'B+' THEN 3
                    WHEN 'B' THEN 4
                    WHEN 'C+' THEN 5
                    WHEN 'C' THEN 6
                    WHEN 'D+' THEN 7
                    WHEN 'D' THEN 8
                    ELSE 9
                END
        """, (sinh_vien_id,))
        
        phan_loai = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'thong_ke_hoc_ky': convert_query_result(thong_ke_hoc_ky),
            'phan_loai_diem': convert_query_result(phan_loai)
        }), 200
        
    except Exception as e:
        print(f"❌ Get Thong Ke Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ===============================
# 3️⃣ GIẢNG VIÊN - QUẢN LÝ HỌC PHẦN
# ===============================
@app.route('/api/giang-vien/hoc-phan', methods=['GET'])
@token_required
def get_hoc_phan_giang_day(current_user):
    """Lấy danh sách học phần giảng dạy"""
    try:
        if current_user['vai_tro'] != 'giang_vien':
            return jsonify({'message': 'Chỉ giảng viên mới có quyền truy cập'}), 403
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                hp.id,
                hp.ma_hoc_phan,
                hp.hoc_ky,
                hp.nam_hoc,
                hp.si_so_toi_da,
                mh.ma_mon,
                mh.ten_mon,
                mh.so_tin_chi,
                COUNT(DISTINCT dk.sinh_vien_id) AS si_so_thuc_te
            FROM hoc_phan hp
            JOIN mon_hoc mh ON hp.mon_hoc_id = mh.id
            LEFT JOIN dang_ky_hoc_phan dk ON hp.id = dk.hoc_phan_id
            WHERE hp.giang_vien_id = %s
            GROUP BY hp.id
            ORDER BY hp.nam_hoc DESC, hp.hoc_ky DESC
        """, (current_user['detail_id'],))
        
        hoc_phan = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # ✅ Frontend expects direct array or { data: [...] }
        return jsonify(convert_query_result(hoc_phan)), 200
        
    except Exception as e:
        print(f"❌ Get Hoc Phan Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/api/giang-vien/hoc-phan/<int:hoc_phan_id>/sinh-vien', methods=['GET'])
@token_required
def get_danh_sach_sinh_vien(current_user, hoc_phan_id):
    """Lấy danh sách sinh viên trong học phần"""
    try:
        if current_user['vai_tro'] != 'giang_vien':
            return jsonify({'message': 'Unauthorized'}), 403
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Kiểm tra quyền
        cursor.execute("SELECT giang_vien_id FROM hoc_phan WHERE id = %s", (hoc_phan_id,))
        hp = cursor.fetchone()
        
        if not hp or hp['giang_vien_id'] != current_user['detail_id']:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Unauthorized'}), 403
        
        # Lấy danh sách sinh viên
        cursor.execute("""
            SELECT 
                sv.id AS sinh_vien_id,
                sv.ma_sinh_vien,
                nd.ho_ten,
                nd.email,
                l.ma_lop,
                l.ten_lop,
                dt.id AS diem_id,
                dt.diem_chuyen_can,
                dt.diem_giua_ky,
                dt.diem_cuoi_ky,
                dt.diem_tong_ket,
                dt.diem_chu,
                dt.ghi_chu
            FROM dang_ky_hoc_phan dk
            JOIN sinh_vien sv ON dk.sinh_vien_id = sv.id
            JOIN nguoi_dung nd ON sv.nguoi_dung_id = nd.id
            JOIN lop l ON sv.lop_id = l.id
            LEFT JOIN diem_thi dt ON dt.sinh_vien_id = sv.id AND dt.hoc_phan_id = %s
            WHERE dk.hoc_phan_id = %s
            ORDER BY l.ma_lop, sv.ma_sinh_vien
        """, (hoc_phan_id, hoc_phan_id))
        
        sinh_vien = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(convert_query_result(sinh_vien)), 200
        
    except Exception as e:
        print(f"❌ Get Danh Sach Sinh Vien Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

# ===============================
# 4️⃣ GIẢNG VIÊN - NHẬP/SỬA ĐIỂM
# ===============================
@app.route('/api/giang-vien/diem', methods=['POST'])
@token_required
def nhap_diem(current_user):
    """Nhập hoặc cập nhật điểm sinh viên"""
    try:
        if current_user['vai_tro'] != 'giang_vien':
            return jsonify({'message': 'Unauthorized'}), 403
        
        data = request.json
        sinh_vien_id = data.get('sinh_vien_id')
        hoc_phan_id = data.get('hoc_phan_id')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Kiểm tra quyền
        cursor.execute("SELECT giang_vien_id FROM hoc_phan WHERE id = %s", (hoc_phan_id,))
        hp = cursor.fetchone()
        
        if not hp or hp['giang_vien_id'] != current_user['detail_id']:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Unauthorized'}), 403
        
        # Kiểm tra đã có điểm chưa
        cursor.execute("""
            SELECT id FROM diem_thi 
            WHERE sinh_vien_id = %s AND hoc_phan_id = %s
        """, (sinh_vien_id, hoc_phan_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update
            cursor.execute("""
                UPDATE diem_thi
                SET diem_chuyen_can = %s, 
                    diem_giua_ky = %s, 
                    diem_cuoi_ky = %s,
                    ghi_chu = %s
                WHERE id = %s
            """, (
                data.get('diem_chuyen_can', 0),
                data.get('diem_giua_ky', 0),
                data.get('diem_cuoi_ky', 0),
                data.get('ghi_chu'),
                existing['id']
            ))
        else:
            # Insert
            cursor.execute("""
                INSERT INTO diem_thi 
                (sinh_vien_id, hoc_phan_id, diem_chuyen_can, diem_giua_ky, diem_cuoi_ky, ghi_chu)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                sinh_vien_id,
                hoc_phan_id,
                data.get('diem_chuyen_can', 0),
                data.get('diem_giua_ky', 0),
                data.get('diem_cuoi_ky', 0),
                data.get('ghi_chu')
            ))
        
        conn.commit()
        
        # Cập nhật GPA
        cursor.callproc('cap_nhat_gpa', [sinh_vien_id])
        conn.commit()
        
        # Real-time notification
        socketio.emit('diem_updated', {
            'sinh_vien_id': sinh_vien_id,
            'hoc_phan_id': hoc_phan_id,
            'timestamp': datetime.now().isoformat()
        }, room=f"hoc_phan_{hoc_phan_id}")
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Cập nhật điểm thành công'}), 200
        
    except Error as e:
        if conn:
            conn.rollback()
        print(f"❌ Nhap Diem Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 400

@app.route('/api/giang-vien/diem/<int:diem_id>', methods=['DELETE'])
@token_required
def xoa_diem(current_user, diem_id):
    """Xóa điểm sinh viên"""
    try:
        if current_user['vai_tro'] != 'giang_vien':
            return jsonify({'message': 'Unauthorized'}), 403
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Kiểm tra quyền
        cursor.execute("""
            SELECT dt.sinh_vien_id, hp.giang_vien_id 
            FROM diem_thi dt
            JOIN hoc_phan hp ON dt.hoc_phan_id = hp.id
            WHERE dt.id = %s
        """, (diem_id,))
        
        diem = cursor.fetchone()
        
        if not diem or diem['giang_vien_id'] != current_user['detail_id']:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Unauthorized'}), 403
        
        cursor.execute("DELETE FROM diem_thi WHERE id = %s", (diem_id,))
        conn.commit()
        
        # Cập nhật GPA
        cursor.callproc('cap_nhat_gpa', [diem['sinh_vien_id']])
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Xóa điểm thành công'}), 200
        
    except Error as e:
        if conn:
            conn.rollback()
        print(f"❌ Xoa Diem Error: {e}")
        return jsonify({'message': f'Error: {str(e)}'}), 400

# ===============================
# 5️⃣ UPLOAD EXCEL
# ===============================
@app.route('/api/giang-vien/upload-excel/<int:hoc_phan_id>', methods=['POST'])
@token_required
def upload_excel(current_user, hoc_phan_id):
    """Upload bảng điểm từ Excel"""
    try:
        if current_user['vai_tro'] != 'giang_vien':
            return jsonify({'message': 'Unauthorized'}), 403
        
        if 'file' not in request.files:
            return jsonify({'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'message': 'Database connection error'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Kiểm tra quyền
        cursor.execute("SELECT giang_vien_id FROM hoc_phan WHERE id = %s", (hoc_phan_id,))
        hp = cursor.fetchone()
        
        if not hp or hp['giang_vien_id'] != current_user['detail_id']:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Unauthorized'}), 403
        
        # Đọc Excel
        df = pd.read_excel(file)
        
        # Validate columns
        required_cols = ['ma_sinh_vien', 'diem_chuyen_can', 'diem_giua_ky', 'diem_cuoi_ky']
        if not all(col in df.columns for col in required_cols):
            return jsonify({'message': 'Invalid Excel format. Required columns: ' + ', '.join(required_cols)}), 400
        
        success_count = 0
        error_list = []
        
        for index, row in df.iterrows():
            try:
                # Tìm sinh viên
                cursor.execute("SELECT id FROM sinh_vien WHERE ma_sinh_vien = %s", (row['ma_sinh_vien'],))
                sv = cursor.fetchone()
                
                if not sv:
                    error_list.append(f"Row {index+2}: Không tìm thấy sinh viên {row['ma_sinh_vien']}")
                    continue
                
                sinh_vien_id = sv['id']
                
                # Kiểm tra đã có điểm chưa
                cursor.execute("""
                    SELECT id FROM diem_thi 
                    WHERE sinh_vien_id = %s AND hoc_phan_id = %s
                """, (sinh_vien_id, hoc_phan_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute("""
                        UPDATE diem_thi
                        SET diem_chuyen_can = %s, 
                            diem_giua_ky = %s, 
                            diem_cuoi_ky = %s,
                            ghi_chu = %s
                        WHERE id = %s
                    """, (
                        float(row['diem_chuyen_can']),
                        float(row['diem_giua_ky']),
                        float(row['diem_cuoi_ky']),
                        row.get('ghi_chu', ''),
                        existing['id']
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO diem_thi 
                        (sinh_vien_id, hoc_phan_id, diem_chuyen_can, diem_giua_ky, diem_cuoi_ky, ghi_chu)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        sinh_vien_id,
                        hoc_phan_id,
                        float(row['diem_chuyen_can']),
                        float(row['diem_giua_ky']),
                        float(row['diem_cuoi_ky']),
                        row.get('ghi_chu', '')
                    ))
                
                # Cập nhật GPA
                cursor.callproc('cap_nhat_gpa', [sinh_vien_id])
                success_count += 1
                
            except Exception as e:
                error_list.append(f"Row {index+2}: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify