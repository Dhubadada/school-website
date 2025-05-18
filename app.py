from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Database Models
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    education = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100))

class Admission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    father = db.Column(db.String(100), nullable=False)
    mother = db.Column(db.String(100), nullable=False)
    job = db.Column(db.String(100))
    address = db.Column(db.String(200), nullable=False)
    nid = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.String(100))

# Create tables
with app.app_context():
    db.create_all()

# Main Routes
@app.route('/')
def index():
    latest_news = News.query.order_by(News.date.desc()).limit(3).all()
    featured_teachers = Teacher.query.order_by(db.func.random()).limit(4).all()
    return render_template('index.html', news=latest_news, teachers=featured_teachers)

@app.route('/teachers')
def teachers():
    all_teachers = Teacher.query.all()
    return render_template('teacher.html', teachers=all_teachers)

@app.route('/teacher/<int:id>')
def teacher_details(id):
    teacher = Teacher.query.get_or_404(id)
    return render_template('teacher_details.html', teacher=teacher)

@app.route('/admission', methods=['GET', 'POST'])
def admission():
    if request.method == 'POST':
        try:
            data = Admission(
                name=request.form['name'],
                father=request.form['father'],
                mother=request.form['mother'],
                job=request.form['job'],
                address=request.form['address'],
                nid=request.form['nid'],
                dob=request.form['dob']
            )
            db.session.add(data)
            db.session.commit()
            flash('Admission application submitted successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Error submitting application. Please try again.', 'danger')
    return render_template('admission.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            msg = Message(
                name=request.form['name'],
                email=request.form['email'],
                message=request.form['message']
            )
            db.session.add(msg)
            db.session.commit()
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Error sending message. Please try again.', 'danger')
    return render_template('contact.html')

@app.route('/news')
def news():
    all_news = News.query.order_by(News.date.desc()).all()
    return render_template('news.html', news=all_news)

# Admin Routes
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'dhruba' and request.form['password'] == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    teachers_count = Teacher.query.count()
    admissions_count = Admission.query.count()
    messages_count = Message.query.count()
    news_count = News.query.count()
    pending_admissions = Admission.query.filter_by(status='Pending').count()
    unread_messages = Message.query.filter_by(read=False).count()
    
    return render_template('admin/dashboard.html',
                         teachers_count=teachers_count,
                         admissions_count=admissions_count,
                         messages_count=messages_count,
                         news_count=news_count,
                         pending_admissions=pending_admissions,
                         unread_messages=unread_messages)

@app.route('/admin/teachers', methods=['GET', 'POST'])
def admin_teachers():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            image_file = request.files.get('image')
            image_filename = None
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_filename = filename
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            teacher = Teacher(
                name=request.form['name'],
                education=request.form['education'],
                subject=request.form['subject'],
                image=image_filename
            )
            db.session.add(teacher)
            db.session.commit()
            flash('Teacher added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding teacher. Please try again.', 'danger')
    
    teachers = Teacher.query.all()
    return render_template('admin/teachers.html', teachers=teachers)

@app.route('/admin/teacher/delete/<int:id>')
def delete_teacher(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        teacher = Teacher.query.get_or_404(id)
        if teacher.image:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], teacher.image))
            except:
                pass
        db.session.delete(teacher)
        db.session.commit()
        flash('Teacher deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting teacher.', 'danger')
    
    return redirect(url_for('admin_teachers'))

@app.route('/admin/admissions')
def admin_admissions():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    admissions = Admission.query.order_by(Admission.date_applied.desc()).all()
    return render_template('admin/admissions.html', admissions=admissions)

@app.route('/admin/admission/update/<int:id>', methods=['POST'])
def update_admission(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        admission = Admission.query.get_or_404(id)
        admission.status = request.form['status']
        db.session.commit()
        flash('Admission status updated!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating admission.', 'danger')
    
    return redirect(url_for('admin_admissions'))

@app.route('/admin/messages')
def admin_messages():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    messages = Message.query.order_by(Message.date.desc()).all()
    for message in messages:
        if not message.read:
            message.read = True
            db.session.commit()
    
    return render_template('admin/messages.html', messages=messages)

@app.route('/admin/message/delete/<int:id>')
def delete_message(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        message = Message.query.get_or_404(id)
        db.session.delete(message)
        db.session.commit()
        flash('Message deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting message.', 'danger')
    
    return redirect(url_for('admin_messages'))

@app.route('/admin/news', methods=['GET', 'POST'])
def admin_news():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            image_file = request.files.get('image')
            image_filename = None
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_filename = filename
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            news = News(
                title=request.form['title'],
                content=request.form['content'],
                image=image_filename
            )
            db.session.add(news)
            db.session.commit()
            flash('News added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding news. Please try again.', 'danger')
    
    all_news = News.query.order_by(News.date.desc()).all()
    return render_template('admin/news.html', news=all_news)

@app.route('/admin/news/delete/<int:id>')
def delete_news(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        news = News.query.get_or_404(id)
        if news.image:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], news.image))
            except:
                pass
        db.session.delete(news)
        db.session.commit()
        flash('News deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting news.', 'danger')
    
    return redirect(url_for('admin_news'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)