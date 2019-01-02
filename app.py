# -*- coding: utf-8 -*-

from scripts import tabledef
from scripts import forms
from scripts import helpers
from flask import Flask, redirect, url_for, render_template, request, session
from pandas import DataFrame,concat
from flask_csv import send_csv
import json
import sys
import os


app = Flask(__name__)


# ======== Routing =========================================================== #
# -------- Login ------------------------------------------------------------- #
@app.route('/', methods=['GET', 'POST'])
def login():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = request.form['password']
            if form.validate():
                if helpers.credentials_valid(username, password):
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Login successful'})
                return json.dumps({'status': 'Invalid user/pass'})
            return json.dumps({'status': 'Both fields required'})
        return render_template('login.html', form=form)
    user = helpers.get_user()
    return render_template('home.html', user=user)


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))


# -------- Signup ---------------------------------------------------------- #
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = helpers.hash_password(request.form['password'])
            email = request.form['email']
            if form.validate():
                if not helpers.username_taken(username):
                    helpers.add_user(username, password, email)
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Signup successful'})
                return json.dumps({'status': 'Username taken'})
            return json.dumps({'status': 'User/Pass required'})
        return render_template('login.html', form=form)
    return redirect(url_for('login'))


# -------- Settings ---------------------------------------------------------- #
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('logged_in'):
        if request.method == 'POST':
            password = request.form['password']
            if password != "":
                password = helpers.hash_password(password)
            email = request.form['email']
            helpers.change_user(password=password, email=email)
            return json.dumps({'status': 'Saved'})
        user = helpers.get_user()
        return render_template('settings.html', user=user)
    return redirect(url_for('login'))

@app.route("/results", methods=['GET', 'POST'])
def results():

   if request.method == 'POST':
    
    io_physical = request.values.getlist('physical')
    io_financial = request.form.getlist('financial')
    io_social = request.form.getlist('social')
    io_cultural = request.form.getlist('cultural')
    io_human = request.form.getlist('human')
    io_enviromental = request.form.getlist('enviromental')

    factor = DataFrame(data={'factor':[1.4, 0.8, 1.2, 1.2, 1.1, -1.4]})

    for i in range(0,6): 
        io_physical[i] = float(io_physical[i])
        io_financial[i] = float(io_financial[i])
        io_social[i] = float(io_social[i])
        io_cultural[i] = float(io_cultural[i])
        io_human[i] = float(io_human[i])
        io_enviromental[i] = float(io_enviromental[i])

    io_table = DataFrame(
    {'Physical': io_physical, 
    'Financial': io_financial, 
    'Social': io_social, 
    'Cultural': io_cultural, 
    'Human': io_human, 
    'Enviromental': io_enviromental})

    def formation(table):
        c_sum = table.sum(axis=0)
        r_sum = table.sum(axis=1)
        total=table.values.sum()
        #Append the new row (which is the sum per column)
        table=table.append(c_sum, ignore_index=True)
        #Append the new column (which is the sum per row)
        table=concat([table, r_sum], axis=1, ignore_index=True)
        #Calculate and assign the sum of the whole table to the last cell
        table.iloc[-1,-1]=total
        #Connect the factor column to the rest of the table
        table=concat([table, factor], axis=1)
        table.iloc[-1,-1]=''
        table.rename(columns={0:'Physical',1:'Financial',2:'Social',3:'Cultural',4:'Human',5:'Enviromental', 6:'Total Row'},
        index={0:'Physical',1:'Financial',2:'Social',3:'Cultural',4:'Human',5:'Enviromental', 6:'Total Col'},
        inplace=True)
        return table

    option = request.form.getlist('model')
    if option == ['mdl1']:
        mdl1_t=DataFrame(io_table.values + factor.values, columns=io_table.columns, index=io_table.index)
        mdl1_t=formation(mdl1_t)
        io_table=formation(io_table)
        return render_template('/results.html', io_table=io_table.to_html(), mdl1_t=mdl1_t.to_html())
    elif option == ['mdl2']:
        mdl2_t=DataFrame(abs(io_table.values * factor.values), columns=io_table.columns, index=io_table.index)
        mdl2_t=formation(mdl2_t)
        io_table=formation(io_table)
        return render_template('/results.html', io_table=io_table.to_html(), mdl2_t=mdl2_t.to_html())
    elif option == ['mdl1','mdl2']:
        mdl1_t=DataFrame(io_table.values + factor.values, columns=io_table.columns, index=io_table.index)
        mdl2_t=DataFrame(abs(io_table.values * factor.values), columns=io_table.columns, index=io_table.index)
        mdl1_t=formation(mdl1_t)
        mdl2_t=formation(mdl2_t)
        io_table=formation(io_table)
        return render_template('/results.html', io_table=io_table.to_html(), mdl1_t=mdl1_t.to_html(), mdl2_t=mdl2_t.to_html())
    else:
        io_table=formation(io_table)
        return render_template('/results.html', io_table=io_table.to_html())


# ======== Main ============================================================== #
if __name__ == "__main__":
    app.secret_key = os.urandom(12)  # Generic key for dev purposes only
    app.run(debug=True, use_reloader=True)
