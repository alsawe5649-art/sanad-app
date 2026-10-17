from flask import Flask, request, redirect, url_for, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os, uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SANAD_SECRET", os.urandom(32))
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

DB = "sanad.db"
UPLOAD_DIR = "private_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

with db() as con:
    con.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'غير مشترك'
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'قيد المراجعة'
    )""")

PAGE = """
<!doctype html>
<html lang="ar" dir="rtl">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>سند</title>
<style>
body{font-family:Arial;background:#f1f5f9;margin:0;padding:18px}
main{max-width:480px;margin:auto;background:white;padding:20px;border-radius:14px}
input,select,button{box-sizing:border-box;width:100%;padding:12px;margin:7px 0}
button{background:#176b50;color:white;border:0;border-radius:8px}
a{color:#176b50} .note{color:#555;font-size:14px}
</style>
<main>
<h1>سند 📚</h1>
<p>منصة تعليمية للطلاب والمدرسين</p>
{% if msg %}<p>{{msg}}</p>{% endif %}
{% if not user %}
<h2>إنشاء حساب</h2>
<form method="post" action="/register">
<input name="name" placeholder="الاسم" required maxlength="80">
<input name="phone" placeholder="رقم الهاتف" required maxlength="20">
<input name="password" type="password" placeholder="كلمة المرور (8 أحرف على الأقل)" required minlength="8">
<select name="role"><option value="student">طالب</option><option value="teacher">مدرس</option></select>
<button>تسجيل</button>
</form>
<h2>تسجيل الدخول</h2>
<form method="post" action="/login">
<input name="phone" placeholder="رقم الهاتف" required>
<input name="password" type="password" placeholder="كلمة المرور" required>
<button>دخول</button>
</form>
{% else %}
<h2>أهلًا {{user["name"]}}</h2>
<p>نوع الحساب: {{ "طالب" if user["role"]=="student" else "مدرس" }}</p>
<p>حالة الاشتراك: {{user["status"]}}</p>
{% if user["status"] != "نشط" %}
<h3>طلب مراجعة الدفع</h3>
<p>سعر الطالب 300 جنيه شهريًا. سعر المدرس يحدده المسؤول ويبدأ من 750 جنيهًا.</p>
<p>رقم محفظة الدفع يظهر بعد التأكد من إعدادات الإدارة.</p>
<form method="post" action="/payment" enctype="multipart/form-data">
<label>ارفع صورة إثبات التحويل (JPG أو PNG أو WEBP، بحد أقصى 5 ميجابايت)</label>
<input type="file" name="proof" accept=".jpg,.jpeg,.png,.webp" required>
<button>إرسال للمراجعة</button>
</form>
<p class="note">رفع الصورة لا يفعّل الاشتراك. الإدارة هي التي تراجع الطلب.</p>
{% endif %}
<form method="post" action="/logout"><button>تسجيل الخروج</button></form>
{% endif %}
</main>
</html>
"""

@app.route("/")
def home():
    user = None
    if "uid" in session:
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE id=?", (session["uid"],)).fetchone()
    return render_template_string(PAGE, user=user, msg=request.args.get("msg", ""))

@app.post("/register")
def register():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "")
    if not name or not phone or len(password) < 8 or role not in ("student", "teacher"):
        return redirect(url_for("home", msg="راجع البيانات وكلمة المرور"))
    try:
        with db() as con:
            con.execute("INSERT INTO users(name,phone,password,role) VALUES(?,?,?,?)",
                        (name, phone, generate_password_hash(password), role))
    except sqlite3.IntegrityError:
        return redirect(url_for("home", msg="رقم الهاتف مسجل بالفعل"))
    return redirect(url_for("home", msg="تم إنشاء الحساب. سجل الدخول الآن."))

@app.post("/login")
def login():
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    with db() as con:
        user = con.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
    if not user or not check_password_hash(user["password"], password):
        return redirect(url_for("home", msg="بيانات الدخول غير صحيحة"))
    session.clear()
    session["uid"] = user["id"]
    return redirect(url_for("home"))

@app.post("/payment")
def payment():
    if "uid" not in session:
        return redirect(url_for("home", msg="سجل الدخول أولًا"))
    f = request.files.get("proof")
    if not f or not f.filename:
        return redirect(url_for("home", msg="اختر صورة إثبات الدفع"))
    ext = os.path.splitext(secure_filename(f.filename))[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        return redirect(url_for("home", msg="نوع الصورة غير مسموح"))
    filename = uuid.uuid4().hex + ext
    f.save(os.path.join(UPLOAD_DIR, filename))
    with db() as con:
        con.execute("INSERT INTO payments(user_id,filename) VALUES(?,?)",
                    (session["uid"], filename))
    return redirect(url_for("home", msg="وصل طلبك للمراجعة التجريبية. الاشتراك لم يتفعّل."))

@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
