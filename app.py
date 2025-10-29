from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'students_2025'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Students(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(25), nullable=False)
    lastname = db.Column(db.String(25), nullable=False)
    group = db.Column(db.String(25))
    birth = db.Column(db.Date, nullable=False)


@app.route('/')
def index():
    return render_template('index.html', title="Bosh sahifa")


@app.route('/students')
def all_students():
    if 'user_id' not in session:
        flash("Iltimos, tizimga kiring", "warning")
        return redirect(url_for('login'))

    students = Students.query.all()
    return render_template('students.html', students=students)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        confirm = request.form.get('confirm').strip()

        if not username or not password or not confirm:
            flash("Barcha maydonlarni toldiring!", "warning")
            return render_template('register.html')

        if password != confirm:
            flash("Parollar mos emas!", "danger")
            return render_template('register.html')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Bu foydalanuvchi allaqachon mavjud!", "danger")
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Royxatdan otish muvaffaqiyatli!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Login yoki parol notogri!", "danger")
            return render_template('login.html')

        session['user_id'] = user.id
        flash(f"Xush kelibsiz, {username}!", "success")
        return redirect(url_for('all_students'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Tizimdan chiqdingiz", "info")
    return redirect(url_for('login'))


@app.route('/student/add', methods=['GET', 'POST'])
def student_add():
    if 'user_id' not in session:
        flash("Iltimos, tizimga kiring", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        firstname = " ".join(el.capitalize() for el in request.form.get('firstname').strip().split())
        lastname = " ".join(el.capitalize() for el in request.form.get('lastname').strip().split())
        group = request.form.get('group').strip()
        birth = request.form.get('birth').strip()

        if not firstname or not lastname or not birth:
            flash("Barcha maydonlar toldirilishi kerak!", "warning")
            return render_template('add_student.html')
        

        birth_date = datetime.strptime(birth, "%Y-%m-%d").date()
        new_student = Students(firstname=firstname, lastname=lastname, group=group or None, birth=birth_date)
        db.session.add(new_student)
        db.session.commit()
        flash("Talaba muvaffaqiyatli qoshildi", "success")
        return redirect(url_for('all_students'))

    return render_template('add_student.html')


@app.route('/student/update/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    if 'user_id' not in session:
        flash("Iltimos, tizimga kiring", "warning")
        return redirect(url_for('login'))

    student = Students.query.get_or_404(id)

    if request.method == 'POST':
        firstname = " ".join(el.capitalize() for el in request.form.get('firstname').strip().split())
        lastname = " ".join(el.capitalize() for el in request.form.get('lastname').strip().split())
        group = request.form.get('group').strip()
        birth = request.form.get('birth').strip()

        if not firstname or not lastname or not birth:
            flash("Barcha maydonlar toldirilishi kerak!", "warning")
            return render_template('update_student.html', student=student)

        try:
            birth_date = datetime.strptime(birth, "%Y-%m-%d").date()
        except ValueError:
            flash("Tugilgan sana formati notogri!", "danger")
            return render_template('update_student.html', student=student)
        
        existing_student = Students.query.filter_by(
            firstname=firstname,
            lastname=lastname,
            birth=birth
        ).filter(Students.id != id).first

        if existing_student:
            flash("Bu talaba allaqachon mavjud!", "warning")
            return render_template('update_student.html', student=student)

        student.firstname = firstname
        student.lastname = lastname
        student.group = group or None
        student.birth = birth_date

        db.session.commit()
        flash("Talaba muvaffaqiyatli yangilandi", "success")
        return redirect(url_for('all_students'))

    return render_template('update_student.html', student=student)


@app.route('/students/delete/<int:id>')
def delete_student(id):
    if 'user_id' not in session:
        flash("Iltimos, tizimga kiring", "warning")
        return redirect(url_for('login'))

    student = Students.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("Talaba ochirildi", "info")
    return redirect(url_for('all_students'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
