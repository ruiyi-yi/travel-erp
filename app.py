# -*- coding: utf-8 -*-
"""
悠享假期 — 旅行社订单财务管理系统
Travel Agency Order & Financial Management ERP

Flask-based full-stack web application with multi-tenant support.
"""
import os
import random
import string
import io
import hashlib
from datetime import datetime, date, timedelta
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, send_file, make_response)
from flask_cors import CORS
import sqlite3

# ── App Initialization ────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'travel-erp-dev-key-change-in-production')
CORS(app)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'system.db')

# ── Database Utilities ────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    """Initialize database tables and demo data on first run."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # ── Table Definitions ─────────────────────────────────────────
    tables = {
        'tenants': '''CREATE TABLE IF NOT EXISTS tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            contact VARCHAR(100), phone VARCHAR(50),
            status INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''',

        'users': '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            username VARCHAR(50) NOT NULL, password VARCHAR(100) NOT NULL,
            real_name VARCHAR(100), role VARCHAR(20) DEFAULT 'staff',
            phone VARCHAR(50), email VARCHAR(100),
            status INTEGER DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id),
            UNIQUE(tenant_id, username))''',

        'customers': '''CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            name VARCHAR(200), phone VARCHAR(50), email VARCHAR(100),
            id_type VARCHAR(50), id_number VARCHAR(100),
            gender VARCHAR(10), birthday DATE, nationality VARCHAR(50),
            address TEXT, notes TEXT, status INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id))''',

        'orders': '''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            order_no VARCHAR(50) NOT NULL,
            customer_id INTEGER, customer_name VARCHAR(200),
            product_name VARCHAR(200), destination VARCHAR(200),
            departure_date DATE, return_date DATE,
            people_count INTEGER DEFAULT 1,
            adult_count INTEGER DEFAULT 1, child_count INTEGER DEFAULT 0,
            unit_price DECIMAL(12,2) DEFAULT 0,
            total_amount DECIMAL(12,2) DEFAULT 0,
            discount DECIMAL(12,2) DEFAULT 0,
            paid_amount DECIMAL(12,2) DEFAULT 0,
            balance DECIMAL(12,2) DEFAULT 0,
            payment_status VARCHAR(20) DEFAULT 'unpaid',
            order_status VARCHAR(20) DEFAULT 'pending',
            contact_phone VARCHAR(50),
            emergency_contact VARCHAR(50), emergency_phone VARCHAR(50),
            insurance_info TEXT, special_requirements TEXT,
            sales_person VARCHAR(100), notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            UNIQUE(tenant_id, order_no))''',

        'finances': '''CREATE TABLE IF NOT EXISTS finances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            order_id INTEGER,
            type VARCHAR(20) NOT NULL,
            category VARCHAR(50), amount DECIMAL(12,2) NOT NULL,
            description TEXT, payment_method VARCHAR(50),
            operator VARCHAR(100),
            record_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id),
            FOREIGN KEY (order_id) REFERENCES orders(id))''',

        'suppliers': '''CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            name VARCHAR(200), phone VARCHAR(100),
            address TEXT, recorder VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id))''',

        'products': '''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            name VARCHAR(200), type VARCHAR(100),
            meeting_point VARCHAR(300), days INTEGER DEFAULT 0,
            specialist VARCHAR(100), operator VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id))''',

        'employees': '''CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER NOT NULL,
            real_name VARCHAR(100), position VARCHAR(100),
            username VARCHAR(50), phone VARCHAR(50),
            mobile VARCHAR(50), qq VARCHAR(50),
            login_count INTEGER DEFAULT 0, last_login VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants(id))''',
    }

    for sql in tables.values():
        cursor.execute(sql)

    # ── Seed Demo Data ────────────────────────────────────────────
    cursor.execute("SELECT id FROM tenants WHERE code = 'demo'")
    if not cursor.fetchone():
        _seed_demo_data(cursor)

    conn.commit()
    conn.close()

def _seed_demo_data(cursor):
    """Generate realistic demo data for portfolio showcase."""
    import random as r

    # Tenant
    cursor.execute(
        "INSERT INTO tenants (code, name, contact, phone) VALUES (?, ?, ?, ?)",
        ('demo', '悠享假期旅行社(演示)', '张经理', '400-888-9999'))
    tid = cursor.lastrowid

    # Users
    cursor.execute(
        "INSERT INTO users (tenant_id, username, password, real_name, role) VALUES (?, ?, ?, ?, ?)",
        (tid, 'admin', hashlib.md5('admin888'.encode()).hexdigest(), '系统管理员', 'admin'))
    cursor.execute(
        "INSERT INTO users (tenant_id, username, password, real_name, role) VALUES (?, ?, ?, ?, ?)",
        (tid, 'staff', hashlib.md5('123456'.encode()).hexdigest(), '李四', 'staff'))

    # Customers (Chinese demo names)
    surnames = '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜'
    names_list = ['伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '洋', '勇',
                  '军', '杰', '娟', '艳', '涛', '明', '超', '秀英', '华', '桂英']
    destinations = ['三亚', '丽江', '张家界', '桂林', '厦门', '泰国曼谷', '日本东京',
                    '巴厘岛', '普吉岛', '长白山', '青海湖', '敦煌', '九寨沟', '香格里拉']
    products = ['自由行', '跟团游', '半自助', '定制游', '亲子游', '蜜月游', '夕阳红', '研学游']
    pay_methods = ['银行转账', '微信', '支付宝', '现金']

    # Generate customers
    cust_ids = []
    for i in range(80):
        name = r.choice(surnames) + r.choice(names_list)
        phone = f'138{random.randint(10000000,99999999)}'
        cursor.execute(
            "INSERT INTO customers (tenant_id, name, phone, gender, nationality) VALUES (?,?,?,?,?)",
            (tid, name, phone, r.choice(['男', '女']), '中国'))
        cust_ids.append(cursor.lastrowid)

    # Generate orders
    statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
    pay_statuses = ['paid', 'partial', 'unpaid']

    for i in range(200):
        dest = r.choice(destinations)
        prod = r.choice(products)
        dept = date.today() + timedelta(days=r.randint(-90, 90))
        ret = dept + timedelta(days=r.randint(3, 12))
        adult = r.randint(1, 10)
        child = r.randint(0, 4)
        people = adult + child
        unit_price = r.randint(1500, 12000)
        total = unit_price * (adult + child * 0.6)
        discount = r.randint(0, 500)
        paid = r.randint(0, int(total - discount))
        order_no = f'YX{datetime.now().strftime("%Y%m%d")}{i+1:05d}'
        cust = cust_ids[r.randint(0, len(cust_ids)-1)]

        cursor.execute('''INSERT INTO orders (tenant_id, order_no, customer_id,
            customer_name, product_name, destination, departure_date, return_date,
            people_count, adult_count, child_count, unit_price, total_amount,
            discount, paid_amount, balance, payment_status, order_status,
            contact_phone, sales_person, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (tid, order_no, cust, '', prod, dest, str(dept), str(ret),
             people, adult, child, unit_price, total, discount, paid,
             total - discount - paid,
             r.choice(pay_statuses), r.choice(statuses),
             f'138{random.randint(10000000,99999999)}',
             r.choice(['张萌', '王红', '赵磊', 'admin']),
             f'{r.choice(["含保险", "不含机票", "升级海景房", "含接送机", ""])}'))

    # Generate finance records
    for i in range(80):
        ftype = r.choice(['income', 'expense'])
        cat = r.choice(['团费收入', '机票收入', '签证收入'] if ftype == 'income' else ['地接成本', '机票成本', '办公费用'])
        amount = r.randint(500, 50000)
        rec_date = str(date.today() - timedelta(days=r.randint(0, 90)))
        cursor.execute('''INSERT INTO finances (tenant_id, order_id, type, category,
            amount, description, payment_method, record_date)
            VALUES (?,?,?,?,?,?,?,?)''',
            (tid, r.randint(1, 200) if r.random() > 0.5 else None,
             ftype, cat, amount, f'{cat} - {datetime.now().strftime("%Y年%m月")}',
             r.choice(pay_methods), rec_date))

    # Suppliers
    for i in range(15):
        cursor.execute("INSERT INTO suppliers (tenant_id, name, phone, address) VALUES (?,?,?,?)",
                       (tid, f"{r.choice(['北京','上海','广州','三亚','丽江'])}{r.choice(['阳光','蓝天','海景','环球'])}旅行社",
                        f'139{random.randint(10000000,99999999)}',
                        f"{r.choice(['北京市朝阳区','上海市浦东新区','广州市天河区'])}XX路{random.randint(1,999)}号"))

    # Products
    product_list = [
        ('三亚5天4晚自由行', '三亚凤凰机场', 5), ('丽江古城+玉龙雪山6日跟团游', '丽江三义机场', 6),
        ('张家界森林公园+天门山4日游', '张家界荷花机场', 4), ('厦门鼓浪屿+土楼5日游', '厦门高崎机场', 5),
        ('泰国曼谷+芭提雅7日游', '曼谷素万那普机场', 7), ('日本东京+富士山6日游', '东京成田机场', 6),
        ('巴厘岛蜜月7天自由行', '巴厘岛努拉莱伊机场', 7), ('长白山滑雪+温泉4日游', '长白山机场', 4),
        ('青海湖+茶卡盐湖5日环线', '西宁曹家堡机场', 5), ('桂林漓江+阳朔4日游', '桂林两江机场', 4),
        ('九寨沟+黄龙5日游', '九寨黄龙机场', 5), ('香格里拉+梅里雪山7日', '迪庆香格里拉机场', 7),
    ]
    for name, meeting, days in product_list:
        cursor.execute("INSERT INTO products (tenant_id, name, meeting_point, days, specialist) VALUES (?,?,?,?,?)",
                       (tid, name, meeting, days, r.choice(['张萌', '王红', '赵磊'])))

    # Employees
    emp_data = [
        ('张萌', '销售经理', 'zhangmeng', '13900001111', '15888881111'),
        ('王红', '操作计调', 'wanghong', '13900002222', '15888882222'),
        ('赵磊', '销售员', 'zhaolei', '13900003333', '15888883333'),
        ('李婷', '财务', 'liting', '13900004444', '15888884444'),
    ]
    for name, pos, uname, phone, mobile in emp_data:
        cursor.execute("INSERT INTO employees (tenant_id, real_name, position, username, phone, mobile) VALUES (?,?,?,?,?,?)",
                       (tid, name, pos, uname, phone, mobile))
    return tid

# ── CAPTCHA Generation ────────────────────────────────────────────
def generate_captcha():
    """Generate a 4-digit CAPTCHA image with noise."""
    code = ''.join(random.choices(string.digits, k=4))
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        width, height = 80, 30
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        for x in range(width):
            for y in range(height):
                if random.random() < 0.1:
                    draw.point((x, y), fill=(random.randint(0, 200),) * 3)
        try:
            font = ImageFont.truetype('arial.ttf', 22)
        except:
            font = ImageFont.load_default()
        for i, char in enumerate(code):
            x = 10 + i * 16 + random.randint(-3, 3)
            y = random.randint(2, 8)
            draw.text((x, y), char, font=font,
                      fill=(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)))
        for _ in range(2):
            x1 = random.randint(0, width); y1 = random.randint(0, height)
            x2 = random.randint(0, width); y2 = random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill=(200, 200, 200), width=1)
        image = image.filter(ImageFilter.SMOOTH)
        return code, image
    except ImportError:
        return code, None

# ── Authentication Middleware ──────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            ym = request.args.get('ym', 'demo')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Unauthorized', 'redirect': url_for('login', ym=ym)}), 401
            return redirect(url_for('login', ym=ym))
        return f(*args, **kwargs)
    return decorated

# ── Routes: Authentication ────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('login', ym='demo'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    ym = request.args.get('ym', 'demo')
    if request.method == 'POST':
        username = request.form.get('uid', '').strip()
        password = request.form.get('pwd', '').strip()
        captcha_input = request.form.get('vpwd', '').strip()

        captcha_code = session.get('captcha', '')
        if captcha_input.upper() != captcha_code.upper() or not captcha_code:
            return render_template('login.html', ym=ym, error='验证码不对，请重新填写!')

        conn = get_db()
        tenant = conn.execute(
            "SELECT id FROM tenants WHERE code = ? AND status = 1", (ym,)).fetchone()
        if not tenant:
            conn.close()
            return render_template('login.html', ym=ym, error='系统不存在!')

        user = conn.execute(
            "SELECT * FROM users WHERE tenant_id = ? AND username = ? AND status = 1",
            (tenant['id'], username)).fetchone()

        if user and user['password'] == hashlib.md5(password.encode()).hexdigest():
            session['user_id'] = user['id']
            session['tenant_id'] = tenant['id']
            session['username'] = user['username']
            session['real_name'] = user['real_name']
            session['role'] = user['role']
            session['ym'] = ym
            session.pop('captcha', None)
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?",
                         (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id']))
            conn.commit(); conn.close()
            return redirect(url_for('dashboard', ym=ym))
        conn.close()
        return render_template('login.html', ym=ym, error='用户名或密码错误!')
    return render_template('login.html', ym=ym)

@app.route('/captcha')
def captcha():
    code, image = generate_captcha()
    session['captcha'] = code
    if image:
        buf = io.BytesIO(); image.save(buf, format='PNG'); buf.seek(0)
        resp = make_response(send_file(buf, mimetype='image/png'))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
    return code

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login', ym=request.args.get('ym', 'demo')))

# ── Routes: Dashboard ─────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db(); tid = session['tenant_id']
    today = date.today(); month_start = today.replace(day=1)

    stats = {
        'total_orders': conn.execute("SELECT COUNT(*) FROM orders WHERE tenant_id=?",(tid,)).fetchone()[0],
        'pending_orders': conn.execute("SELECT COUNT(*) FROM orders WHERE tenant_id=? AND order_status='pending'",(tid,)).fetchone()[0],
        'today_orders': conn.execute("SELECT COUNT(*) FROM orders WHERE tenant_id=? AND date(departure_date)=?",(tid,str(today))).fetchone()[0],
        'monthly_income': conn.execute("SELECT COALESCE(SUM(amount),0) FROM finances WHERE tenant_id=? AND type='income' AND date(record_date)>=?",(tid,str(month_start))).fetchone()[0],
        'monthly_expense': conn.execute("SELECT COALESCE(SUM(amount),0) FROM finances WHERE tenant_id=? AND type='expense' AND date(record_date)>=?",(tid,str(month_start))).fetchone()[0],
        'total_receivable': conn.execute("SELECT COALESCE(SUM(balance),0) FROM orders WHERE tenant_id=? AND balance>0",(tid,)).fetchone()[0],
        'customer_count': conn.execute("SELECT COUNT(*) FROM customers WHERE tenant_id=? AND status=1",(tid,)).fetchone()[0],
    }
    stats['monthly_profit'] = stats['monthly_income'] - stats['monthly_expense']

    recent_orders = conn.execute(
        "SELECT * FROM orders WHERE tenant_id=? ORDER BY departure_date DESC LIMIT 10", (tid,)).fetchall()

    monthly_data = []
    for i in range(5, -1, -1):
        m = today.month - i; y = today.year
        if m <= 0: m += 12; y -= 1
        ml = f'{y}-{m:02d}'
        inc = conn.execute("SELECT COALESCE(SUM(amount),0) FROM finances WHERE tenant_id=? AND type='income' AND strftime('%Y-%m',record_date)=?",(tid,ml)).fetchone()[0]
        exp = conn.execute("SELECT COALESCE(SUM(amount),0) FROM finances WHERE tenant_id=? AND type='expense' AND strftime('%Y-%m',record_date)=?",(tid,ml)).fetchone()[0]
        monthly_data.append({'month': ml, 'income': inc, 'expense': exp})
    conn.close()
    return render_template('dashboard.html', stats=stats, recent_orders=recent_orders, monthly_data=monthly_data, ym=session['ym'])

# ── Routes: Orders ────────────────────────────────────────────────
@app.route('/orders')
@login_required
def order_list():
    conn = get_db(); tid = session['tenant_id']
    search = request.args.get('search', ''); status = request.args.get('status', '')
    pay_status = request.args.get('pay_status', '')
    page = request.args.get('page', 1, type=int); per_page = 15

    query = "SELECT * FROM orders WHERE tenant_id = ?"; params = [tid]
    if search:
        query += " AND (order_no LIKE ? OR customer_name LIKE ? OR destination LIKE ? OR product_name LIKE ?)"
        params.extend([f'%{search}%']*4)
    if status: query += " AND order_status = ?"; params.append(status)
    if pay_status: query += " AND payment_status = ?"; params.append(pay_status)

    total = conn.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
    query += " ORDER BY departure_date DESC, order_no DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    orders = conn.execute(query, params).fetchall(); conn.close()
    return render_template('orders.html', orders=orders, search=search, status=status, pay_status=pay_status,
                           page=page, total=total, per_page=per_page, ym=session['ym'])

@app.route('/order/add', methods=['GET', 'POST'])
@login_required
def order_add():
    if request.method == 'POST':
        conn = get_db(); tid = session['tenant_id']
        today_str = datetime.now().strftime('%Y%m%d')
        count = conn.execute("SELECT COUNT(*) FROM orders WHERE tenant_id=? AND date(created_at)=date('now')",(tid,)).fetchone()[0]
        order_no = f'YX{today_str}{count+1:05d}'
        total = float(request.form.get('total_amount', 0) or 0)
        discount = float(request.form.get('discount', 0) or 0)
        paid = float(request.form.get('paid_amount', 0) or 0)
        conn.execute('''INSERT INTO orders (tenant_id, order_no, customer_name, product_name,
            destination, departure_date, return_date, people_count, adult_count, child_count,
            unit_price, total_amount, discount, paid_amount, balance, payment_status,
            order_status, contact_phone, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (tid, order_no, request.form.get('customer_name',''), request.form.get('product_name',''),
             request.form.get('destination',''), request.form.get('departure_date',''),
             request.form.get('return_date',''), int(request.form.get('people_count',1)),
             int(request.form.get('adult_count',1)), int(request.form.get('child_count',0)),
             float(request.form.get('unit_price',0) or 0), total, discount, paid,
             total - discount - paid, request.form.get('payment_status','unpaid'),
             request.form.get('order_status','pending'), request.form.get('contact_phone',''),
             request.form.get('notes','')))
        conn.commit(); conn.close()
        return redirect(url_for('order_list', ym=session['ym']))
    return render_template('order_form.html', order=None, ym=session['ym'])

@app.route('/order/edit/<int:oid>', methods=['GET', 'POST'])
@login_required
def order_edit(oid):
    conn = get_db(); tid = session['tenant_id']
    if request.method == 'POST':
        total = float(request.form.get('total_amount', 0) or 0)
        discount = float(request.form.get('discount', 0) or 0)
        paid = float(request.form.get('paid_amount', 0) or 0)
        conn.execute('''UPDATE orders SET customer_name=?, product_name=?, destination=?,
            departure_date=?, return_date=?, people_count=?, unit_price=?, total_amount=?,
            discount=?, paid_amount=?, balance=?, payment_status=?, order_status=?,
            contact_phone=?, notes=?, updated_at=? WHERE id=? AND tenant_id=?''',
            (request.form.get('customer_name',''), request.form.get('product_name',''),
             request.form.get('destination',''), request.form.get('departure_date',''),
             request.form.get('return_date',''), int(request.form.get('people_count',1)),
             float(request.form.get('unit_price',0) or 0), total, discount, paid,
             total - discount - paid, request.form.get('payment_status','unpaid'),
             request.form.get('order_status','pending'), request.form.get('contact_phone',''),
             request.form.get('notes',''), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             oid, tid))
        conn.commit(); conn.close()
        return redirect(url_for('order_list', ym=session['ym']))
    order = conn.execute("SELECT * FROM orders WHERE id=? AND tenant_id=?",(oid,tid)).fetchone(); conn.close()
    return render_template('order_form.html', order=order, ym=session['ym'])

@app.route('/order/view/<int:oid>')
@login_required
def order_view(oid):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE id=? AND tenant_id=?",(oid,session['tenant_id'])).fetchone()
    conn.close()
    if not order: return redirect(url_for('order_list', ym=session['ym']))
    return render_template('order_view.html', order=order, ym=session['ym'])

@app.route('/order/delete/<int:oid>', methods=['POST'])
@login_required
def order_delete(oid):
    conn = get_db()
    conn.execute("DELETE FROM orders WHERE id=? AND tenant_id=?",(oid,session['tenant_id']))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ── Routes: Customers ─────────────────────────────────────────────
@app.route('/customers')
@login_required
def customer_list():
    conn = get_db(); tid = session['tenant_id']
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int); per_page = 20
    query = "SELECT * FROM customers WHERE tenant_id = ? AND status=1"; params = [tid]
    if search:
        query += " AND (name LIKE ? OR phone LIKE ?)"; params.extend([f'%{search}%']*2)
    total = conn.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"; params.extend([per_page, (page-1)*per_page])
    customers = conn.execute(query, params).fetchall(); conn.close()
    return render_template('customers.html', customers=customers, search=search,
                           page=page, total=total, per_page=per_page, ym=session['ym'])

@app.route('/customer/add', methods=['GET', 'POST'])
@login_required
def customer_add():
    if request.method == 'POST':
        conn = get_db()
        conn.execute('''INSERT INTO customers (tenant_id, name, phone, email, id_type, id_number,
            gender, birthday, nationality, address, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (session['tenant_id'], request.form.get('name',''), request.form.get('phone',''),
             request.form.get('email',''), request.form.get('id_type',''), request.form.get('id_number',''),
             request.form.get('gender',''), request.form.get('birthday',''), request.form.get('nationality',''),
             request.form.get('address',''), request.form.get('notes','')))
        conn.commit(); conn.close()
        return redirect(url_for('customer_list', ym=session['ym']))
    return render_template('customer_form.html', customer=None, ym=session['ym'])

@app.route('/customer/edit/<int:cid>', methods=['GET', 'POST'])
@login_required
def customer_edit(cid):
    conn = get_db(); tid = session['tenant_id']
    if request.method == 'POST':
        conn.execute('''UPDATE customers SET name=?,phone=?,email=?,id_type=?,id_number=?,
            gender=?,birthday=?,nationality=?,address=?,notes=?,updated_at=? WHERE id=? AND tenant_id=?''',
            (request.form.get('name',''), request.form.get('phone',''), request.form.get('email',''),
             request.form.get('id_type',''), request.form.get('id_number',''), request.form.get('gender',''),
             request.form.get('birthday',''), request.form.get('nationality',''), request.form.get('address',''),
             request.form.get('notes',''), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), cid, tid))
        conn.commit(); conn.close()
        return redirect(url_for('customer_list', ym=session['ym']))
    customer = conn.execute("SELECT * FROM customers WHERE id=? AND tenant_id=?",(cid,tid)).fetchone(); conn.close()
    return render_template('customer_form.html', customer=customer, ym=session['ym'])

# ── Routes: Finances ──────────────────────────────────────────────
@app.route('/finances')
@login_required
def finance_list():
    conn = get_db(); tid = session['tenant_id']
    ftype = request.args.get('type', '')
    page = request.args.get('page', 1, type=int); per_page = 20
    query = "SELECT * FROM finances WHERE tenant_id = ?"; params = [tid]
    if ftype: query += " AND type = ?"; params.append(ftype)
    total = conn.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
    query += " ORDER BY record_date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page-1)*per_page])
    records = conn.execute(query, params).fetchall()
    total_income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM finances WHERE tenant_id=? AND type='income'",(tid,)).fetchone()[0]
    total_expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM finances WHERE tenant_id=? AND type='expense'",(tid,)).fetchone()[0]
    conn.close()
    return render_template('finances.html', records=records, ftype=ftype, total_income=total_income,
                           total_expense=total_expense, profit=total_income-total_expense,
                           page=page, total=total, per_page=per_page, ym=session['ym'])

@app.route('/finance/add', methods=['POST'])
@login_required
def finance_add():
    conn = get_db()
    conn.execute('''INSERT INTO finances (tenant_id, order_id, type, category, amount, description,
        payment_method, operator, record_date) VALUES (?,?,?,?,?,?,?,?,?)''',
        (session['tenant_id'], request.form.get('order_id') or None, request.form.get('type','income'),
         request.form.get('category',''), float(request.form.get('amount',0) or 0),
         request.form.get('description',''), request.form.get('payment_method',''),
         session.get('real_name',''), request.form.get('record_date', str(date.today()))))
    conn.commit(); conn.close()
    return redirect(url_for('finance_list', ym=session['ym']))

# ── Routes: Debts ─────────────────────────────────────────────────
@app.route('/debts')
@login_required
def debt_check():
    conn = get_db(); tid = session['tenant_id']
    customer_debts = conn.execute('''SELECT order_no, customer_name, contact_phone, total_amount,
        paid_amount, balance, departure_date, product_name
        FROM orders WHERE tenant_id=? AND balance>0 ORDER BY balance DESC LIMIT 100''',(tid,)).fetchall()
    total_customer_debt = conn.execute("SELECT COALESCE(SUM(balance),0) FROM orders WHERE tenant_id=? AND balance>0",(tid,)).fetchone()[0]
    conn.close()
    return render_template('debts.html', customer_debts=customer_debts, total_customer_debt=total_customer_debt, ym=session['ym'])

# ── Routes: Reports ───────────────────────────────────────────────
@app.route('/reports')
@login_required
def reports():
    conn = get_db(); tid = session['tenant_id']
    order_status_data = conn.execute("SELECT order_status, COUNT(*) as count FROM orders WHERE tenant_id=? GROUP BY order_status",(tid,)).fetchall()
    payment_data = conn.execute("SELECT payment_status, COUNT(*) as count, COALESCE(SUM(balance),0) as total_balance FROM orders WHERE tenant_id=? GROUP BY payment_status",(tid,)).fetchall()
    top_dest = conn.execute("SELECT destination, COUNT(*) as count, COALESCE(SUM(total_amount),0) as revenue FROM orders WHERE tenant_id=? GROUP BY destination ORDER BY count DESC LIMIT 10",(tid,)).fetchall()
    monthly = conn.execute("SELECT strftime('%Y-%m',record_date) as month, SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income, SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense, SUM(CASE WHEN type='income' THEN amount ELSE -amount END) as profit FROM finances WHERE tenant_id=? GROUP BY month ORDER BY month DESC LIMIT 12",(tid,)).fetchall()
    sales_data = conn.execute("SELECT sales_person, COUNT(*) as count, COALESCE(SUM(total_amount),0) as revenue, COALESCE(SUM(balance),0) as receivable FROM orders WHERE tenant_id=? AND sales_person IS NOT NULL GROUP BY sales_person ORDER BY revenue DESC",(tid,)).fetchall()
    conn.close()
    return render_template('reports.html', order_status_data=order_status_data, payment_data=payment_data,
                           top_dest=top_dest, monthly=monthly, sales_data=sales_data, ym=session['ym'])

# ── Routes: Resource Management ───────────────────────────────────
@app.route('/suppliers')
@login_required
def supplier_list():
    conn = get_db()
    suppliers = conn.execute("SELECT * FROM suppliers WHERE tenant_id=? ORDER BY id DESC",(session['tenant_id'],)).fetchall()
    conn.close()
    return render_template('suppliers.html', suppliers=suppliers, ym=session['ym'])

@app.route('/products')
@login_required
def product_list():
    conn = get_db()
    products = conn.execute("SELECT * FROM products WHERE tenant_id=? ORDER BY id DESC",(session['tenant_id'],)).fetchall()
    conn.close()
    return render_template('products.html', products=products, ym=session['ym'])

@app.route('/employees')
@login_required
def employee_list():
    conn = get_db()
    employees = conn.execute("SELECT * FROM employees WHERE tenant_id=? ORDER BY id",(session['tenant_id'],)).fetchall()
    conn.close()
    return render_template('employees.html', employees=employees, ym=session['ym'])

@app.route('/blacklist')
@login_required
def blacklist():
    return render_template('blacklist.html', ym=session['ym'])

# ── Routes: User Management ───────────────────────────────────────
@app.route('/users')
@login_required
def user_list():
    if session.get('role') != 'admin':
        return redirect(url_for('dashboard', ym=session['ym']))
    conn = get_db()
    users = conn.execute("SELECT * FROM users WHERE tenant_id=? ORDER BY created_at DESC",(session['tenant_id'],)).fetchall()
    conn.close()
    return render_template('users.html', users=users, ym=session['ym'])

@app.route('/user/add', methods=['POST'])
@login_required
def user_add():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (tenant_id, username, password, real_name, role, phone, email) VALUES (?,?,?,?,?,?,?)",
            (session['tenant_id'], request.form.get('username',''),
             hashlib.md5(request.form.get('password','123456').encode()).hexdigest(),
             request.form.get('real_name',''), request.form.get('role','staff'),
             request.form.get('phone',''), request.form.get('email','')))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close(); return jsonify({'error': '用户名已存在'}), 400
    conn.close()
    return redirect(url_for('user_list', ym=session['ym']))

@app.route('/user/reset_password/<int:uid>', methods=['POST'])
@login_required
def user_reset_password(uid):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    conn.execute("UPDATE users SET password=? WHERE id=? AND tenant_id=?",
                 (hashlib.md5('123456'.encode()).hexdigest(), uid, session['tenant_id']))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'message': '密码已重置为123456'})

# ── Entry Point ────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 56)
    print("  Travel ERP System v2.0")
    print("  悠享假期 - 旅行社订单财务管理系统")
    print("=" * 56)
    init_db()
    print("  Database initialized.")
    print("  URL: http://localhost:5000")
    print("  Login: admin / admin888")
    print("=" * 56)
    app.run(host='0.0.0.0', port=5000, debug=False)
