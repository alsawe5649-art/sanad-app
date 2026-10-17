from flask import Flask, request, redirect, session
import sqlite3
app = Flask(__name__)
app.secret_key = "sanad2026"

ADMIN_CODE = "Z$9!_S@N@D#ADMIN_2026*^XqW7&Lp2$Vn4!K8pT_z0_0115#SECURE!"
TEACHER_CODE = "TEACHER2026"

# عدل هنا 👇
ETISALAT_NUMBER = "01112345678"  # حط رقمك بتاع اتصالات كاش
PRICE = 150  # سعر الاشتراك

def db():
    c=sqlite3.connect("sanad.db")
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, phone TEXT UNIQUE, pass TEXT, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY, title TEXT, link TEXT, teacher TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS pays (id INTEGER PRIMARY KEY, student TEXT, phone TEXT, trans_id TEXT, status TEXT)")
    return c

CSS = """<style>*{box-sizing:border-box;font-family:Tahoma}body{margin:0;min-height:100vh;background: linear-gradient(rgba(11,77,46,0.88), rgba(11,77,46,0.88)), url('https://images.unsplash.com/photo-1522202176988-66273c2fd55f');background-size:cover;display:flex;flex-direction:column;align-items:center;padding:15px}
.card{background:white;width:100%;max-width:480px;border-radius:18px;padding:20px;box-shadow:0 10px 30px rgba(0,0,0,.3);margin:12px 0}
input,select{width:100%;padding:14px;margin:6px 0;border:1.5px solid #ddd;border-radius:10px;font-size:16px}
button{width:100%;padding:14px;background:#0b4d2e;color:white;border:none;border-radius:10px;font-size:17px;font-weight:bold;margin-top:6px}
.logo{text-align:center;color:white;font-size:30px;font-weight:900}
.paybox{background:#fff3cd;border:2px dashed #e6a800;padding:12px;border-radius:10px;margin:10px 0;text-align:center}
table{width:100%;border-collapse:collapse}th,td{border:1px solid #ddd;padding:6px;font-size:12px}th{background:#0b4d2e;color:white}
</style>"""

HOME = CSS + """<div class=logo>📚 منصة سند</div><div style="color:white;margin-bottom:10px">التعليم ببساطة</div>
<div class=card><h2 style="text-align:center;color:#0b4d2e">تسجيل جديد</h2>
<form method=post action=/reg><input name=name placeholder=الاسم required><input name=phone placeholder=رقم الهاتف required><input name=pw type=password placeholder="كلمة المرور (8 حروف)" required>
<select name=role onchange="tcode.style.display=this.value=='مدرس'?'block':'none';acode.style.display=this.value=='ادمن'?'block':'none'"><option>طالب</option><option>مدرس</option><option>ادمن</option></select>
<input id=tcode name=tcode placeholder="كود المدرس" style=display:none><input id=acode name=acode placeholder="كود الادمن" style=display:none><button>تسجيل</button></form></div>
<div class=card><h2 style="text-align:center;color:#0b4d2e">دخول</h2><form method=post action=/log><input name=phone placeholder=رقم الهاتف required><input name=pw type=password placeholder=كلمة المرور required><button style="background:#1a7a4a">دخول</button></form></div>"""

@app.route("/")
def home():
    if 'role' not in session: return HOME
    if session['role']=='ادمن':
        con=db(); cur=con.cursor(); cur.execute("SELECT * FROM users"); users=cur.fetchall(); cur.execute("SELECT * FROM pays"); pays=cur.fetchall(); con.close()
        rows="".join([f"<tr><td>{u[1]}</td><td>{u[2]}</td><td>{u[4]}</td></tr>" for u in users])
        prow="".join([f"<tr><td>{p[1]}</td><td>{p[2]}</td><td>{p[3]}</td><td>{p[4]}</td><td><a href=/approve/{p[0]} style='background:green;color:white;padding:5px;border-radius:5px;text-decoration:none'>تأكيد</a></td></tr>" for p in pays])
        return CSS+f"<div class=card style='max-width:700px'><h2>لوحة الأدمن</h2><a href=/logout>خروج</a><h3>المستخدمين</h3><table><tr><th>الاسم</th><th>الهاتف</th><th>الدور</th></tr>{rows}</table><h3>طلبات الدفع - اتصالات كاش</h3><table><tr><th>الطالب</th><th>رقمه</th><th>كود العملية</th><th>الحالة</th><th>تأكيد</th></tr>{prow}</table></div>"
    if session['role']=='مدرس':
        con=db(); cur=con.cursor(); cur.execute("SELECT * FROM videos WHERE teacher=?",(session['name'],)); vids=cur.fetchall(); con.close()
        vrows="".join([f"<li>{v[1]} - {v[2]}</li>" for v in vids])
        return CSS+f"<div class=card><h2>لوحة المدرس {session['name']}</h2><a href=/logout>خروج</a><form method=post action=/add_video><input name=title placeholder=عنوان الدرس required><input name=link placeholder=رابط يوتيوب required><button>رفع</button></form><ul>{vrows}</ul></div>"
    # طالب
    con=db(); cur=con.cursor(); cur.execute("SELECT status FROM pays WHERE phone=? ORDER BY id DESC LIMIT 1",(session.get('phone'),)); pay=cur.fetchone()
    cur.execute("SELECT * FROM videos"); vids=cur.fetchall(); con.close()
    is_paid = pay and pay[0]=='مقبول'
    if not is_paid:
        return CSS+f"""<div class=card><h2>أهلا {session['name']}</h2>
        <div class=paybox>💳 للاشتراك حول <b>{PRICE} جنيه</b> على اتصالات كاش<br><b style='font-size:20px'>{ETISALAT_NUMBER}</b><br>وبعد التحويل اكتب كود العملية</div>
        <form method=post action=/pay><input name=trans_id placeholder="رقم العملية / Transaction ID" required><button>تأكيد الدفع</button></form>
        <p style='text-align:center;font-size:13px'>حالتك: {pay[0] if pay else 'لم تدفع بعد'} - في انتظار موافقة الأدمن</p><a href=/logout>خروج</a></div>"""
    vrows="".join([f"<div style='border:1px solid #ddd;padding:10px;border-radius:10px;margin:8px 0'><b>{v[1]}</b><br><small>المدرس: {v[3]}</small><br><a href={v[2]} target=_blank style='color:#0b4d2e'>▶️ شاهد</a></div>" for v in vids])
    return CSS+f"<div class=card><h2>أهلا {session['name']} ✅ مشترك</h2><a href=/logout>خروج</a><h3>دروسك</h3>{vrows}</div>"

@app.route("/reg", methods=["POST"])
def reg():
    r=request.form["role"]; pw=request.form["pw"]
    if len(pw)<8: return "الباسورد 8 حروف <a href=/>رجوع</a>"
    if r=="مدرس" and request.form.get("tcode")!=TEACHER_CODE: return "كود المدرس غلط"
    if r=="ادمن" and request.form.get("acode")!=ADMIN_CODE: return "كود الادمن غلط"
    try:
        con=db(); con.execute("INSERT INTO users (name,phone,pass,role) VALUES (?,?,?,?)",(request.form["name"],request.form["phone"],pw,r)); con.commit(); con.close()
        return "✅ اتسجلت <a href=/>دخول</a>"
    except: return "الرقم متسجل"

@app.route("/log", methods=["POST"])
def log():
    con=db(); cur=con.cursor(); cur.execute("SELECT name,role,phone FROM users WHERE phone=? AND pass=?",(request.form["phone"],request.form["pw"])); u=cur.fetchone(); con.close()
    if u: session['name']=u[0]; session['role']=u[1]; session['phone']=u[2]; return redirect("/")
    return "غلط <a href=/>رجوع</a>"

@app.route("/pay", methods=["POST"])
def pay():
    con=db(); con.execute("INSERT INTO pays (student,phone,trans_id,status) VALUES (?,?,?,?)",(session['name'],session['phone'],request.form["trans_id"],"بانتظار التأكيد")); con.commit(); con.close()
    return redirect("/")

@app.route("/approve/<int:id>")
def approve(id):
    if session.get('role')!='ادمن': return redirect("/")
    con=db(); con.execute("UPDATE pays SET status='مقبول' WHERE id=?",(id,)); con.commit(); con.close()
    return redirect("/")

@app.route("/add_video", methods=["POST"])
def add_vid():
    con=db(); con.execute("INSERT INTO videos (title,link,teacher) VALUES (?,?,?)",(request.form["title"],request.form["link"],session['name'])); con.commit(); con.close()
    return redirect("/")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080)
