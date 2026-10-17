from flask import Flask, request, redirect, session, render_template_string
import sqlite3, os
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SANAD_SECRET")
DB = "sanad.db"

PAGE = """
<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>إدارة سند</title><style>body{font-family:Arial;background:#0b1933;color:#17233d;padding:18px}main{max-width:520px;margin:25px auto;background:white;padding:24px;border-radius:18px;border-top:5px solid #d7b66d}h1,h2{color:#142747}input,button{box-sizing:border-box;width:100%;padding:12px;margin:8px 0;border-radius:9px}input{border:1px solid #ccd3df}button{background:#142747;color:white;border:0;font-weight:bold}.item{background:#f4f0e5;padding:12px;border-radius:10px;margin:10px 0}</style><main><h1>📚 سند | لوحة الإدارة</h1>{% if not logged %}<p>دخول المسؤول</p><form method="post" action="/login"><input name="password" type="password" placeholder="كلمة مرور الأدمن" required><button>تسجيل الدخول</button></form>{% else %}<h2>إعدادات الاشتراكات</h2><form method="post" action="/settings"><label>اشتراك الطالب الشهري بالجنيه</label><input name="student_price" type="number" min="0" value="{{student_price}}" required><label>اشتراك المدرس الشهري بالجنيه</label><input name="teacher_price" type="number" min="0" value="{{teacher_price}}" required><label>رقم محفظة الدفع</label><input name="wallet_number" value="{{wallet_number}}" required><button>حفظ الإعدادات</button></form><div class="item">الأسعار تُحفظ محليًا في قاعدة بيانات سند.</div><form method="post" action="/logout"><button>تسجيل الخروج</button></form>{% endif %}{% if msg %}<p>{{msg}}</p>{% endif %}</main></html>
"""

def get_settings():
    with sqlite3.connect(DB) as c:
        return dict(c.execute("SELECT key,value FROM settings").fetchall())

@app.get("/")
def home():
    if not session.get("admin"):
        return render_template_string(PAGE, logged=False, msg=request.args.get("msg",""))
    s = get_settings()
    return render_template_string(PAGE, logged=True, msg=request.args.get("msg",""), **s)

@app.post("/login")
def login():
    stored = os.environ.get("SANAD_ADMIN_HASH")
    password = request.form.get("password","")
    if not stored or not app.secret_key or not check_password_hash(stored,password):
        return redirect("/?msg=تعذر تسجيل الدخول: إعداد كلمة مرور الأدمن أولًا")
    session["admin"] = True
    return redirect("/")

@app.post("/settings")
def settings():
    if not session.get("admin"):
        return "غير مصرح", 403
    values = {"student_price":request.form.get("student_price","300"),"teacher_price":request.form.get("teacher_price","750"),"wallet_number":request.form.get("wallet_number","").strip()}
    if not values["student_price"].isdigit() or not values["teacher_price"].isdigit() or not values["wallet_number"]:
        return "راجع الأسعار ورقم المحفظة", 400
    with sqlite3.connect(DB) as c:
        c.executemany("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", values.items())
    return redirect("/?msg=تم حفظ الإعدادات")

@app.post("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    if not app.secret_key:
        raise SystemExit("يجب إعداد SANAD_SECRET قبل التشغيل")
    app.run(host="127.0.0.1",port=8081,debug=False)
