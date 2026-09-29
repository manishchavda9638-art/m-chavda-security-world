
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, io, uuid, datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

APP_SECRET = os.environ.get("MCSW_SECRET", "change-this-secret-in-production")
DB = os.path.join(os.path.dirname(__file__), "mcsw.db")
app = Flask(__name__)
app.secret_key = APP_SECRET

COURSES = [
    ("python", "Python Programming", "Beginner to intermediate Python with security-focused exercises."),
    ("java", "Java Programming", "Core Java, OOP, collections and secure coding."),
    ("web", "Web Development", "HTML, CSS, JavaScript, HTTP and secure web development."),
    ("cyber", "Cybersecurity Fundamentals", "CIA triad, authentication, access control, threats and defense."),
    ("ethical", "Ethical Hacking", "Authorized security testing concepts in isolated practice labs."),
    ("soc", "SOC & Blue Team", "Logs, alerts, incident response, detection and hardening."),
    ("linux", "Linux & Networking", "CLI, permissions, TCP/IP, DNS, HTTP and troubleshooting."),
    ("forensics", "Digital Forensics", "Hashes, metadata, timelines and evidence-analysis concepts."),
]
LESSONS = {
 "python":["Variables & Types","Conditions & Loops","Functions","OOP","Files & Exceptions","Security Automation Concepts"],
 "java":["Java Basics","OOP","Collections","Exceptions","Files","Secure Coding"],
 "web":["HTML/CSS","JavaScript","DOM","HTTP","Forms","Web Security Fundamentals"],
 "cyber":["CIA Triad","Threats & Vulnerabilities","Authentication","Access Control","Cryptography Concepts","Incident Basics"],
 "ethical":["Rules of Engagement","Recon Concepts","Web Testing Concepts","Input Validation","Reporting","Safe Lab Practice"],
 "soc":["Logs","Indicators","Alerts","Triage","Incident Response","Detection Rules"],
 "linux":["CLI","Files & Permissions","Processes","Networking","Services","Hardening"],
 "forensics":["Evidence","Hashes","Metadata","Timelines","Logs","Case Report"],
}
def db():
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; return con
def init_db():
    con=db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,is_admin INTEGER DEFAULT 0,created TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS progress(user_id INTEGER,course TEXT,lesson INTEGER,PRIMARY KEY(user_id,course,lesson));
    CREATE TABLE IF NOT EXISTS quiz(user_id INTEGER,course TEXT,score INTEGER,created TEXT);
    CREATE TABLE IF NOT EXISTS certificates(id TEXT PRIMARY KEY,user_id INTEGER,course TEXT,issued TEXT);
    """)
    if not con.execute("SELECT 1 FROM users WHERE email=?",("chavdamohan965@gmail.com",)).fetchone():
        con.execute("INSERT INTO users(name,email,password,is_admin,created) VALUES(?,?,?,?,?)",
                    ("M Chavda Admin","chavdamohan965@gmail.com",generate_password_hash("ChangeMe123!"),1,datetime.datetime.now().isoformat()))
    con.commit(); con.close()
def current():
    if "uid" not in session:return None
    con=db(); u=con.execute("SELECT * FROM users WHERE id=?",(session["uid"],)).fetchone(); con.close(); return u
@app.context_processor
def ctx(): return {"user":current()}

@app.route("/")
def home(): return render_template("index.html",courses=COURSES)
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form["name"].strip(); email=request.form["email"].strip().lower(); pw=request.form["password"]
        if len(pw)<8: flash("Password must be at least 8 characters."); return redirect(url_for("register"))
        try:
            con=db(); con.execute("INSERT INTO users(name,email,password,created) VALUES(?,?,?,?)",
                                  (name,email,generate_password_hash(pw),datetime.datetime.now().isoformat())); con.commit()
            uid=con.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone()["id"]; con.close()
            session["uid"]=uid; return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError: flash("Email already registered.")
    return render_template("register.html")
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        con=db(); u=con.execute("SELECT * FROM users WHERE email=?",(request.form["email"].lower(),)).fetchone(); con.close()
        if u and check_password_hash(u["password"],request.form["password"]):
            session["uid"]=u["id"]; return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")
@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if not current(): return redirect(url_for("login"))
    con=db(); p=con.execute("SELECT course,COUNT(*) n FROM progress WHERE user_id=? GROUP BY course",(session["uid"],)).fetchall()
    certs=con.execute("SELECT * FROM certificates WHERE user_id=? ORDER BY issued DESC",(session["uid"],)).fetchall(); con.close()
    return render_template("dashboard.html",progress=p,certs=certs,lessons=LESSONS)

@app.route("/course/<course>")
def course(course):
    if course not in LESSONS:return "Course not found",404
    con=db(); done={r["lesson"] for r in con.execute("SELECT lesson FROM progress WHERE user_id=? AND course=?",(session.get("uid",-1),course)).fetchall()} if session.get("uid") else set(); con.close()
    title=dict(COURSES).get(course,course.title())
    return render_template("course.html",key=course,title=title,lessons=LESSONS[course],done=done)

@app.post("/course/<course>/complete/<int:lesson>")
def complete(course,lesson):
    if not current(): return redirect(url_for("login"))
    if course not in LESSONS or lesson<0 or lesson>=len(LESSONS[course]): return "Invalid lesson",400
    con=db(); con.execute("INSERT OR IGNORE INTO progress(user_id,course,lesson) VALUES(?,?,?)",(session["uid"],course,lesson))
    count=con.execute("SELECT COUNT(*) c FROM progress WHERE user_id=? AND course=?",(session["uid"],course)).fetchone()["c"]
    if count==len(LESSONS[course]):
        exists=con.execute("SELECT 1 FROM certificates WHERE user_id=? AND course=?",(session["uid"],course)).fetchone()
        if not exists:
            cid="MCSW-"+uuid.uuid4().hex[:10].upper()
            con.execute("INSERT INTO certificates(id,user_id,course,issued) VALUES(?,?,?,?)",
                        (cid,session["uid"],course,datetime.datetime.now().date().isoformat()))
    con.commit(); con.close(); return redirect(url_for("course",course=course))

@app.route("/certificate/<cid>")
def certificate(cid):
    con=db(); c=con.execute("""SELECT certificates.*,users.name FROM certificates JOIN users ON users.id=certificates.user_id WHERE certificates.id=?""",(cid,)).fetchone(); con.close()
    if not c:return "Certificate not found",404
    return render_template("certificate.html",c=c)

@app.route("/certificate/<cid>/pdf")
def certificate_pdf(cid):
    con=db(); c=con.execute("""SELECT certificates.*,users.name FROM certificates JOIN users ON users.id=certificates.user_id WHERE certificates.id=?""",(cid,)).fetchone(); con.close()
    if not c:return "Certificate not found",404
    buf=io.BytesIO(); pdf=canvas.Canvas(buf,pagesize=A4); w,h=A4
    pdf.setTitle("M Chavda Security World Certificate")
    pdf.setFont("Helvetica-Bold",24); pdf.drawCentredString(w/2,h-130,"M CHAVDA SECURITY WORLD")
    pdf.setFont("Helvetica-Bold",20); pdf.drawCentredString(w/2,h-200,"CERTIFICATE OF COMPLETION")
    pdf.setFont("Helvetica",13); pdf.drawCentredString(w/2,h-260,"This certifies that")
    pdf.setFont("Helvetica-Bold",22); pdf.drawCentredString(w/2,h-305,c["name"])
    pdf.setFont("Helvetica",13); pdf.drawCentredString(w/2,h-350,"has successfully completed")
    pdf.setFont("Helvetica-Bold",18); pdf.drawCentredString(w/2,h-390,dict(COURSES).get(c["course"],c["course"]))
    pdf.setFont("Helvetica",11); pdf.drawCentredString(w/2,h-445,"Course completion certificate • Practice-based learning")
    pdf.drawCentredString(w/2,h-475,f"Certificate ID: {c['id']}    Date: {c['issued']}")
    pdf.setFont("Helvetica-Oblique",10); pdf.drawCentredString(w/2,80,"Verify at the M Chavda Security World certificate verification page.")
    pdf.save(); buf.seek(0)
    return send_file(buf,as_attachment=True,download_name=f"{c['id']}.pdf",mimetype="application/pdf")

@app.route("/verify",methods=["GET","POST"])
def verify():
    result=None
    if request.method=="POST":
        con=db(); result=con.execute("SELECT certificates.*,users.name FROM certificates JOIN users ON users.id=certificates.user_id WHERE certificates.id=?",(request.form["id"].strip().upper(),)).fetchone(); con.close()
    return render_template("verify.html",result=result)

@app.route("/ctf")
def ctf(): return render_template("ctf.html")
@app.route("/admin")
def admin():
    u=current()
    if not u or not u["is_admin"]: return redirect(url_for("login"))
    con=db(); users=con.execute("SELECT id,name,email,created FROM users ORDER BY id DESC").fetchall(); certs=con.execute("SELECT * FROM certificates ORDER BY issued DESC").fetchall(); con.close()
    return render_template("admin.html",users=users,certs=certs)

@app.errorhandler(404)
def notfound(e): return render_template("404.html"),404

if __name__=="__main__":
    init_db()
    app.run(debug=True)
