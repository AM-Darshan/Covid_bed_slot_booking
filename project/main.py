from flask import Flask, json, redirect, render_template, flash, request
from flask.globals import request, session
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import login_required, logout_user, login_user, login_manager, LoginManager, current_user

from flask_mail import Mail
import json

# my database connection

local_server = True
app = Flask(__name__)
app.secret_key="abhishek"


#config file
with open('config.json', 'r') as c:
    params = json.load(c)["params"]

#configure the mail
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)


# this is for getting the unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# app.confing['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/databasename'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/covid'
db = SQLAlchemy(app)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Hospitaluser.query.get(int(user_id))

#************************** Start of data bases****************************************

#test db
class Test(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50))


#user login db
class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    srfid = db.Column(db.String(20),unique=True)
    email = db.Column(db.String(50))
    dob = db.Column(db.String(1000))

#hospital user db
class Hospitaluser(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode = db.Column(db.String(20))
    email = db.Column(db.String(50))
    password = db.Column(db.String(1000))

#hospital user db

class Hospitaldata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode=db.Column(db.String(20),unique=True)
    hname=db.Column(db.String(100))
    normalbed=db.Column(db.Integer)
    hicubed=db.Column(db.Integer)
    icubed=db.Column(db.Integer)
    vbed=db.Column(db.Integer)


#booking patient db
class Bookingpatient(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    srfid=db.Column(db.String(20),unique=True)
    bedtype=db.Column(db.String(100))
    hcode=db.Column(db.String(20))
    spo2=db.Column(db.Integer)
    pname=db.Column(db.String(100))
    pphone=db.Column(db.String(100))
    paddress=db.Column(db.String(100))

#Trigger data
class Trig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hcode=db.Column(db.String(20))
    normalbed=db.Column(db.Integer)
    hicubed=db.Column(db.Integer)
    icubed=db.Column(db.Integer)
    vbed=db.Column(db.Integer)
    querys=db.Column(db.String(50))
    date=db.Column(db.String(50))

#************************** End of data bases****************************************


#**************************Differnt pages ********************************************

#home
@app.route("/")
def home():
    return render_template("index.html")

#********************************Admin pages*********************************************\

#-------------------admin login------------------

@app.route('/admin', methods=['POST', 'GET'])
def admin():

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if(username == params['user'] and password == params['password']):
            session['user'] = username
            flash("login success", "info")
            return render_template("addHosUser.html")
        else:
            flash("Invalid Credentials", "danger")

    return render_template("admin.html")


#------------------add hospital user-------------------

@app.route('/addHospitalUser', methods=['POST', 'GET'])
def hospitalUser():

    if('user' in session and session['user'] == params['user']):

        if request.method == "POST":
            hcode = request.form.get('hcode')
            email = request.form.get('email')
            password = request.form.get('password')
            encpassword = generate_password_hash(password)
            hcode = hcode.upper()
            emailUser = Hospitaluser.query.filter_by(email=email).first()
            if emailUser:
                flash("Email or srif is already taken", "warning")

            db.engine.execute(
                f"INSERT INTO `hospitaluser` (`hcode`,`email`,`password`) VALUES ('{hcode}','{email}','{encpassword}') ")

            mail.send_message('COVID CARE CENTER', sender=params['gmail-user'], recipients=[
                              email], body=f"Welcome thanks for choosing us\nYour Login Credentials Are:\n Email Address: {email}\nPassword: {password}\n\nHospital Code {hcode}\n\n Do not share your password\n\n\nThank You...")
            flash("Data Sent and Inserted Successfully", "warning")
            return render_template("addHosUser.html")
    else:
        flash("Login and try Again", "warning")
        return render_template("addHosUser.html")



#******************************  Hospital user pages   ******************************************\


#----------------------hospital login-----------------------

@app.route('/hospitallogin', methods=['POST', 'GET'])
def hospitallogin():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = Hospitaluser.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Success", "info")
            return render_template("index.html")
        else:
            flash("Invalid Credentials", "danger")
            return render_template("hospitallogin.html")

    return render_template("hospitallogin.html")


#---------------------hospital data info----------------------

@app.route("/addhospitalinfo", methods=['POST', 'GET'])
def addhospitalinfo():
    email = current_user.email
    posts = Hospitaluser.query.filter_by(email=email).first()
    code = posts.hcode
    postsdata = Hospitaldata.query.filter_by(hcode=code).first()

    if request.method == "POST":
        hcode = request.form.get('hcode')
        hname = request.form.get('hname')
        nbed = request.form.get('normalbed')
        hbed = request.form.get('hicubeds')
        ibed = request.form.get('icubeds')
        vbed = request.form.get('ventbeds')
        hcode = hcode.upper()
        huser = Hospitaluser.query.filter_by(hcode=hcode).first()
        hduser = Hospitaldata.query.filter_by(hcode=hcode).first()
        if hduser:
            flash("Data is already Present you can update it..", "primary")
            return render_template("hospitaldata.html")
        if huser:
            db.engine.execute(
                f"INSERT INTO `hospitaldata` (`hcode`,`hname`,`normalbed`,`hicubed`,`icubed`,`vbed`) VALUES ('{hcode}','{hname}','{nbed}','{hbed}','{ibed}','{vbed}')")
            flash("Data Is Added", "primary")
        else:
            flash("Hospital Code not Exist", "warning")

    return render_template("hospitaldata.html", postsdata=postsdata)


#----------------hospital data edit-----------------------

@app.route("/hedit/<string:id>", methods=['POST', 'GET'])
@login_required
def hedit(id):
    posts = Hospitaldata.query.filter_by(id=id).first()

    if request.method == "POST":
        hcode = request.form.get('hcode')
        hname = request.form.get('hname')
        nbed = request.form.get('normalbed')
        hbed = request.form.get('hicubeds')
        ibed = request.form.get('icubeds')
        vbed = request.form.get('ventbeds')
        hcode = hcode.upper()
        db.engine.execute(
            f"UPDATE `hospitaldata` SET `hcode` ='{hcode}',`hname`='{hname}',`normalbed`='{nbed}',`hicubed`='{hbed}',`icubed`='{ibed}',`vbed`='{vbed}' WHERE `hospitaldata`.`id`={id}")
        flash("Slot Updated", "info")
        return redirect("/addhospitalinfo")

    return render_template("hedit.html", posts=posts)


#----------------------hospital data delete---------------------

@app.route("/hdelete/<string:id>", methods=['POST', 'GET'])
@login_required
def hdelete(id):
    db.engine.execute(
        f"DELETE FROM `hospitaldata` WHERE `hospitaldata`.`id`={id}")
    flash("Date Deleted", "danger")
    return redirect("/addhospitalinfo")


#*****************************   User/Patient pages *****************************************\

#-------------User signup page--------------
@app.route("/signup",methods=['POST','GET'])
def signup():
    if request.method == "POST":
        srfid = request.form.get('srf')
        email = request.form.get('email')
        dob = request.form.get('dob')
        #print(srfid,email,dob)
        encpassword = generate_password_hash(dob)

        user=User.query.filter_by(srfid=srfid).first()
        emailUser=User.query.filter_by(email=email).first()
        if user or emailUser:
            flash("Email or srif is already taken","warning")
            return render_template("userSignup.html")
        
        new_user = db.engine.execute(f"INSERT INTO `user` (`srfid`,`email`,`dob`) VALUES ('{srfid}','{email}','{encpassword}') ")
        flash("SignUp Success Please Login", "success")
        return render_template("userlogin.html")

    return render_template("userSignup.html")


#--------------------User login feedback ---------------------

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        srfid = request.form.get('srf')
        dob = request.form.get('dob')

        user = User.query.filter_by(srfid=srfid).first()
        if user and check_password_hash(user.dob,dob):
            login_user(user)
            flash("Login succesful","info")
            return render_template("index.html")
        else:
            flash("Invalid credentials","danger")
            return render_template("userlogin.html")
        
    return render_template("userlogin.html")



#----------------patient bed booking-------------

@app.route("/slotbooking", methods=['POST', 'GET'])
@login_required
def slotbooking():
    query = db.engine.execute(f"SELECT * FROM `hospitaldata` ")
    if request.method=="POST":
        srfid=request.form.get('srfid')
        bedtype=request.form.get('bedtype')
        hcode=request.form.get('hcode')
        spo2=request.form.get('spo2')
        pname=request.form.get('pname')
        pphone=request.form.get('pphone')
        paddress=request.form.get('paddress')  
        check2=Hospitaldata.query.filter_by(hcode=hcode).first()
        if not check2:
            flash("Hospital Code not exist","warning")

        code=hcode
        dbb=db.engine.execute(f"SELECT * FROM `hospitaldata` WHERE `hospitaldata`.`hcode`='{code}' ")        
        bedtype=bedtype
        if bedtype=="NormalBed":       
            for d in dbb:
                seat=d.normalbed
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.normalbed=seat-1
                db.session.commit()
                
            
        elif bedtype=="HICUBed":      
            for d in dbb:
                seat=d.hicubed
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.hicubed=seat-1
                db.session.commit()

        elif bedtype=="ICUBed":     
            for d in dbb:
                seat=d.icubed
                print(seat)
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.icubed=seat-1
                db.session.commit()

        elif bedtype=="VENTILATORBed": 
            for d in dbb:
                seat=d.vbed
                ar=Hospitaldata.query.filter_by(hcode=code).first()
                ar.vbed=seat-1
                db.session.commit()
        else:
            pass

        check=Hospitaldata.query.filter_by(hcode=hcode).first()
        if(seat>0 and check):
            res=Bookingpatient(srfid=srfid,bedtype=bedtype,hcode=hcode,spo2=spo2,pname=pname,pphone=pphone,paddress=paddress)
            db.session.add(res)
            db.session.commit()
            flash("Slot is Booked , kindly Visit Hospital for Further Procedure","success")
        else:
            flash("Something Went Wrong","danger")
    
    return render_template("booking.html",query=query)


#-----------------patient details--------------

@app.route("/pdetails",methods=['GET'])
@login_required
def pdetails():
    code=current_user.srfid
    print(code)
    data=Bookingpatient.query.filter_by(srfid=code).first()
    
    return render_template("details.html",data=data)


#-------------logout admin-----------

@app.route("/logoutadmin")
def logoutadmin():
    session.pop('user')
    flash("You are logout admin", "primary")

    return redirect('/admin')

#------------logout user--------------

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul", "warning")
    return redirect(url_for('login'))


#---------------triggered data-------------------

@app.route("/triggers")
def triggers():
    query=Trig.query.all() 
    return render_template("triggers.html",query=query)

#testing whether db is connected or not
@app.route("/test")
def test():
    
    try:
        a = Test.query.all()
        print(a)
        return 'My database is connected'
    except Exception as e:
        print(e)
        return f'database not connected {e}'

app.run(debug=True)


