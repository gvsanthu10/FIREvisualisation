from flask import Flask, render_template, request, redirect, url_for, flash, Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot

app = Flask(__name__)

# cofig
app.config.update(
    DEBUG=True,
    SECRET_KEY='pogothedon'
)

# defining local sqlite database
db_name = 'local_database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# flask login config
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# Creating Entry class
class Entry(db.Model):
    __tablename__ = 'montlydate'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String)
    axis = db.Column(db.Integer)
    shares = db.Column(db.Integer)
    pension = db.Column(db.Integer)
    lisa = db.Column(db.Integer)
    total = db.Column(db.Integer)

    def __init__(self, date=date, axis=axis, shares=shares, pension=pension, lisa=lisa, total=total):
        self.data = (date, axis, shares, pension, lisa, total)
        self.date = date
        self.axis = axis
        self.shares = shares
        self.pension = pension
        self.lisa = lisa
        self.total = total


# Creating user model
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.username = "123"   #Change this
        self.password = "123"   #Change this

    def __repr__(self):
        return "User"


# creating an admin user
admin_user = User(1)


# login route
@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if u == "123" and p == "123":
            user = admin_user
            login_user(user)
            return redirect(url_for("home"))
        else:
            return render_template('loginpage.html', error="Wrong username or password")
    return render_template('loginpage.html')


@app.route('/home')
@login_required
def home():
    entries = Entry.query.all()
    return render_template('home.html', entries=entries)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/insert', methods=['POST'])
@login_required
def insert():
    if request.method == "POST":
        given_date = request.form.get("date")
        axis_amont = request.form.get("axis")
        shares_amont = request.form.get("shares")
        pension_amount = request.form.get("pension")
        lisa_amont = request.form.get("lisa")
        total = int(axis_amont) + int(pension_amount) + int(shares_amont) + int(lisa_amont)

        new_entry = Entry(date=given_date, axis=axis_amont, shares=shares_amont, pension=pension_amount,
                          lisa=lisa_amont, total=total)
        db.session.add(new_entry)
        db.session.commit()

        flash("Data Added Successfully")

        return redirect(url_for('home'))


@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    if request.method == 'POST':
        my_data = Entry.query.get(request.form.get('id'))

        new_axis = request.form['axis']
        new_shares = request.form['shares']
        new_pension = request.form['pension']
        new_lisa = request.form['lisa']

        my_data.axis = new_axis
        my_data.shares = new_shares
        my_data.pension = new_pension
        my_data.lisa = new_lisa
        my_data.total = int(new_axis) + int(new_shares) + int(new_pension) + int(new_lisa)

        db.session.commit()

        flash("Data Updated Successfully")

        return redirect(url_for('home'))


@app.route('/delete/<id>/', methods=['GET', 'POST'])
@login_required
def delete(id):
    my_data = Entry.query.get(id)
    db.session.delete(my_data)
    db.session.commit()

    flash("Data Deleted Successfully")

    return redirect(url_for('home'))


def create_df():
    data = db.session.query(Entry).all()
    df = pd.DataFrame([(d.date, d.axis, d.shares, d.pension, d.lisa, d.total) for d in data],
                      columns=['Date', 'Axis', 'Shares', 'Pension', 'LISA', 'Total'])
    # Coverting string to datetime and integers
    for col in ['Axis', 'Shares', 'Pension', 'LISA', 'Total']:
        df[col] = df[col].astype('int64')
    df = df.sort_values(by='Date', ascending=True)
    return df


def line_graph_maker():
    df = create_df()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Total"]))
    fig.update_layout(title_text="Net worth ove time")
    fig.update_xaxes(title_text="Dates")
    fig.update_yaxes(title_text="Amunt in £")
    fig.update_layout(
        autosize=False,
        width=500,
        height=500,
        margin=dict(l=10, r=10, b=20, t=25, pad=10),

    )

    my_line_chart = plot(figure_or_data=fig,
                         include_plotlyjs=True,
                         output_type='div')
    return Markup(my_line_chart)


def progress_graph_maker():
    df = create_df()
    current_total = df['Total'].iloc[-1]

    fig = go.Figure()
    fig = go.Figure(go.Indicator(
        domain={'x': [0, 1], 'y': [0, 1]},
        value=current_total,
        mode="gauge+number",
        title={'text': "Progress to Lean and Fat FIRE"},
        gauge={'axis': {'range': [None, 600000]},
               'steps': [
                   {'range': [0, 450000], 'color': "lightgray"},
                   {'range': [450000, 600000], 'color': "gray"}],
               'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 600000}}))
    fig.update_layout(title_text="Progress chart")
    fig.update_layout(
        autosize=False,
        width=500,
        height=500,
        margin=dict(l=10, r=10, b=20, t=25, pad=5),
    )

    my_progress_chart = plot(figure_or_data=fig,
                             include_plotlyjs=True,
                             output_type='div')
    return Markup(my_progress_chart)


def stacked_graph_maker():
    df = create_df()

    fig = go.Figure(data=[
        go.Bar(name='Axis', x=df['Date'], y=df['Axis']),
        go.Bar(name='Shares', x=df['Date'], y=df['Shares']),
        go.Bar(name='Pension', x=df['Date'], y=df['Pension']),
        go.Bar(name='LISA', x=df['Date'], y=df['LISA']),
    ])
    fig.update_layout(barmode='stack')
    fig.update_layout(title_text="Breakdown over time")
    fig.update_layout(
        autosize=False,
        width=500,
        height=500,
        margin=dict(l=10, r=10, b=20, t=25, pad=5),
    )
    fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ))

    my_stacked_chart = plot(figure_or_data=fig,
                            include_plotlyjs=True,
                            output_type='div')
    return Markup(my_stacked_chart)


def treemap_maker():
    df = create_df()
    data = {'Name': ['Axis', 'Shares', 'Pension', 'LISA'],
            'Number': [df['Axis'].iloc[-1], df['Shares'].iloc[-1], df['Pension'].iloc[-1], df['LISA'].iloc[-1]], }
    df = pd.DataFrame.from_dict(data)

    parents = [''] * len(df['Name'])

    fig = go.Figure(go.Treemap(labels=df['Name'], values=df['Number'], parents=parents))
    fig.update_layout(title_text="Latest breakdown")
    fig.update_layout(
        autosize=False,
        width=450,
        height=500,
        margin=dict(l=10, r=10, b=20, t=25, pad=5),
    )

    my_treemap = plot(figure_or_data=fig,
                      include_plotlyjs=True,
                      output_type='div')
    return Markup(my_treemap)


@app.route('/graphs')
@login_required
def graphs():
    my_line_chart = line_graph_maker()
    my_progress_chart = progress_graph_maker()
    my_stacked_chart = stacked_graph_maker()
    my_treemap = treemap_maker()
    return render_template('graphs.html',
                           line_chart=my_line_chart, progress_chart=my_progress_chart, stacked_chart=my_stacked_chart,
                           treemap=my_treemap)


@login_manager.user_loader
def load_user(userid):
    return User(userid)


if __name__ == "__main__":
    app.run()
