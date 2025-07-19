from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Stock
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        else:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('portfolio'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()  # should clear the session!
    return redirect(url_for('index'))


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_stock():
    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        name = request.form['name']
        price = float(request.form['price'])  # User enters price in INR
        quantity = int(request.form['quantity'])
        stock = Stock(symbol=symbol, name=name, price=price, quantity=quantity, owner=current_user)
        db.session.add(stock)
        db.session.commit()
        flash(f"{symbol} added to portfolio!", "success")
        return redirect(url_for('portfolio'))
    return render_template('add_stock.html')

@app.route('/portfolio')
@login_required
def portfolio():
    stocks = current_user.stocks
    total_value = sum(s.price * s.quantity for s in stocks)
    return render_template('portfolio.html', stocks=stocks, total=total_value)

# 🚩 DELETE route to remove old/wrong data directly from web app!
@app.route('/delete/<int:stock_id>')
@login_required
def delete_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    if stock.owner != current_user:
        flash('Unauthorized', 'danger')
        return redirect(url_for('portfolio'))
    db.session.delete(stock)
    db.session.commit()
    flash('Stock deleted!', 'success')
    return redirect(url_for('portfolio'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


