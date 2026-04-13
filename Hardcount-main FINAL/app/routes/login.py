import os
from flask import Blueprint, render_template, request, session, flash, redirect, url_for

login_bp = Blueprint('login', __name__)

@login_bp.route("/login", methods=['GET', 'POST'])
def login():
        if request.method == 'POST':
            password = request.form.get('password', '').strip()
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin')  
            if password == admin_password:
                session['admin'] = True
                session.permanent = True
                flash('Successfully logged in as administrator.', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Invalid password. Please try again.', 'error')
        
        return render_template('login.html')


@login_bp.route("/logout")
def logout():
        session.clear()
        flash('You have been logged out.', 'success')
        return redirect(url_for('main.index'))


