
"""
Columbia W4111 Intro to databases
Example webserver
To run locally
    python server.py
Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, abort, url_for, flash
from random import randint
from datetime import datetime, timezone

from sqlalchemy.sql.functions import user
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = ("b'\xb9\xdc1\x2f\xfc\x1b\xb9\xa9\xb5d\xadr\xb0'" +
                           "b'\x96\xdc\xfb\xf5B\xd7\x0e\x17.\xe7'")



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "jvp2118"
DB_PASSWORD = "8260"

#DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DB_SERVER = "w4111project1part2db.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print ("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:
  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2
  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  #print (request.args)

  # check if user is logged in
  if 'logname' not in session:
    return redirect(url_for('login'))
  cursor = g.conn
  # Get the real name of the logged in user
  name = cursor.execute("""
    SELECT users.name,sid
    FROM users
    WHERE email = %(email)s;
    """, {
      'email': session['logname']
    })
  name = name.fetchone()
  display=True
  if name[1]==None:
    display=False
  print(display)
  # example of a database query
  #
  #cursor = g.conn.execute("SELECT name FROM test")
  #names = []
  #for result in cursor:
  #  names.append(result['name'])  # can also be accessed using result[0]
  #cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = [name[0],display])


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/cart', methods=['GET', 'POST'])
def cart():
# check if user is logged in
  if 'logname' not in session:
    return redirect(url_for('login'))
  if request.method == 'GET':
    cursor = g.conn
    # Get the real name of the logged in user
    cart_data = cursor.execute("""
      select sell_item.name,condition,price,users.name as seller_name,category.name as category 
      from has,sell_item,users,belong,Category 
      where has.usr_email = %(email)s and sell_item.iid = has.iid and has.sid=users.sid and sell_item.iid=belong.iid and category.caid=belong.caid
      """, {
        'email': session['logname']
      })
    cart_data = cart_data.fetchall()
  context = dict(cart_data = cart_data)
  return render_template("cart.html",**context)


@app.route('/browse_items', methods=['GET', 'POST'])
def browse_items():
  if 'logname' not in session:
    return redirect(url_for('login'))
  #Sort by price-a - default
  cursor = g.conn
  # Get the real name of the logged in user
  selector = list(request.form.values()) or ['0']
  if selector[0] == '0':
    item_data = cursor.execute("""
      select sell_item.name,price,condition,users.name as seller_name,Category.name as category 
      from sell_item,users,belong,Category 
      where sell_item.sid=users.sid and sell_item.iid=belong.iid and category.caid=belong.caid
      except
      select sell_item.name,price,condition,users.name as seller_name,Category.name as category 
      from sell_item,users,belong,Category,buy 
      where sell_item.sid=users.sid and sell_item.iid=belong.iid and category.caid=belong.caid and sell_item.iid=buy.iid 
      order by price asc 
      limit 15
      """)
    rows = 5
  if selector[0] == '1':
    item_data = cursor.execute("""
      select sell_item.name,price,condition,users.name as seller_name,Category.name as category 
      from sell_item,users,belong,Category 
      where sell_item.sid=users.sid and sell_item.iid=belong.iid and category.caid=belong.caid 
      except
      select sell_item.name,price,condition,users.name as seller_name,Category.name as category 
      from sell_item,users,belong,Category,buy
      where sell_item.sid=users.sid and sell_item.iid=belong.iid and category.caid=belong.caid and sell_item.iid=buy.iid 
      order by price desc 
      limit 15
      """)
    rows = 5
  if selector[0] == '3':
    item_data = cursor.execute("""
    select sell_item.name,price,condition,users.name as seller_name,Category.name as category,counts.pop as followers
    from (
      select count(*)as pop,usr2_email from follow group by usr2_email) as counts,sell_item,users,belong,Category 
    where counts.usr2_email=users.email and users.sid=sell_item.sid and sell_item.iid=belong.iid and category.caid=belong.caid 
    except
    select sell_item.name,price,condition,users.name as seller_name,Category.name as category,counts.pop as followers
    from (
      select count(*)as pop,usr2_email from follow group by usr2_email) as counts,sell_item,users,belong,Category,buy 
    where counts.usr2_email=users.email and users.sid=sell_item.sid and sell_item.iid=belong.iid and category.caid=belong.caid and sell_item.iid=buy.iid 
    order by followers desc 
    limit 15
    """)
    rows = 6
  if selector[0] == '2':
    item_data = cursor.execute("""
    CREATE OR REPLACE FUNCTION custom_sort(anyarray, anyelement)
    RETURNS INT AS 
    $$
     SELECT i FROM (
     SELECT generate_series(array_lower($1,1),array_upper($1,1))
     ) g(i)
    WHERE $1[i] = $2
    LIMIT 1;
    $$ LANGUAGE SQL IMMUTABLE;

      SELECT *
   FROM (
     SELECT sell_item.name,price,condition,users.name as seller_name,Category.name as category
   FROM sell_item,users,belong,Category
   WHERE sell_item.sid=users.sid and sell_item.iid=belong.iid and category.caid=belong.caid
   except
   SELECT sell_item.name,price,condition,users.name as seller_name,Category.name as category
   FROM sell_item,users,belong,Category,buy
   WHERE sell_item.sid=users.sid and sell_item.iid=belong.iid and category.caid=belong.caid and sell_item.iid=buy.iid) as tmp
   ORDER BY custom_sort(ARRAY['Like New', 'Good', 'Fair', 'Bad'], tmp.condition)
   LIMIT 15
   """)
    rows = 5
    print(item_data)
  context = dict(item_data = item_data)
  return render_template("browse_items.html",**context)

@app.route('/sellitems',methods=['GET', 'POST'])
def sellitems():
  if 'logname' not in session:
    return redirect(url_for('index'))
  if 'logsid' not in session:
    return redirect(url_for('index'))
  cursor = g.conn
  sell_data = cursor.execute("""
    select name,price,condition from sell_item where sid=%(sid)s
    except
    select name,price,condition from sell_item,buy where sell_item.iid=buy.iid and sell_item.sid=%(sid)s
    """,{
    'sid':session['logsid']
    })
  context = dict(sell_data = sell_data)
  return render_template("sellitems.html",**context)

@app.route('/solditems',methods=['GET', 'POST'])
def solditems():
  if 'logname' not in session:
    return redirect(url_for('index'))
  if 'logsid' not in session:
    return redirect(url_for('index'))
  cursor = g.conn
  sold_data = cursor.execute("""
    select name,price,condition from sell_item,buy where sell_item.iid=buy.iid and sell_item.sid=%(sid)s
    """,{
    'sid':session['logsid']
    })
  context = dict(sold_data = sold_data)
  return render_template("solditems.html",**context)

@app.route('/bought_item')
def bought_item():
  if 'logname' not in session:
    return redirect(url_for('index'))
  if request.method == 'GET':
    cursor = g.conn
    bought_data = cursor.execute("""
    select name,price,condition,carrier,eta,status 
    from buy,sell_item,Delivery,logistics 
    where usr_email=%(email)s and delivery.did=logistics.did and logistics.iid=buy.iid and sell_item.iid=buy.iid
    """,{
      'email': session['logname']})
  context = dict(bought_data = bought_data)
  return render_template("bought_item.html",**context)

# Password page
@app.route('/password', methods=['GET', 'POST'])
def password():
  if 'logname' not in session:
    return redirect(url_for('index'))
  if request.method == 'POST':
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    cursor = g.conn
    exists = cursor.execute("""
    SELECT users.email AS email FROM users
    WHERE email = %(email)s
    AND password = %(password)s;
    """, {
      'email': session['logname'],
      'password': old_password
    })
    exists = exists.fetchall()
    # Throw error 403 if no such email/password combination
    if not exists:
      cursor.close()
      abort(403)
    
    cursor.execute("""
    UPDATE users
    SET password = %(password)s
    WHERE email = %(email)s;
    """, {
      'password': new_password,
      'email': session['logname']
    })
    return redirect(url_for('index'))
  return render_template("password.html")
  

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
  if 'logname' in session:
    return redirect(url_for('index'))
  
  # Check whether email/password combination can be found
  if request.method == 'POST':
    exists = None
    input_email = request.form['email']
    input_password = request.form['password']
    input_sid = request.form['sid']
    cursor = g.conn

    if input_sid != '':
      exists = cursor.execute("""
      SELECT users.email AS email FROM users
      WHERE email = %(email)s
      AND password = %(password)s
      AND sid = %(sid)s;
      """, {
        'email': input_email,
        'password': input_password,
        'sid':input_sid
      })
    else:
      exists = cursor.execute("""
      SELECT users.email AS email FROM users
      WHERE email = %(email)s
      AND password = %(password)s
      """, {
        'email': input_email,
        'password': input_password,
      })
    exists = exists.fetchall()
    print(exists)
    # Throw error 403 if no such email/password combination
    if not exists:
      cursor.close()
      abort(403)
    
    # Create cookie if log in is successful
    session['logname'] = input_email
    if input_sid != '':
      session['logsid'] = input_sid
    cursor.close()
    return redirect(url_for('index'))
  return render_template("login.html")

# Example of adding new data to the database
@app.route('/additem', methods=['POST'])
def additem():
  if 'logname' not in session:
    return redirect(url_for('index'))
  if 'logsid' not in session:
    return redirect(url_for('index'))
  name = request.form['name']
  price = request.form['price']
  condition = request.form['condition']
  print (name)
  cursor = g.conn
  exist = cursor.execute("""
      SELECT distinct iid FROM sell_item
      """)
  exist = exist.fetchall()
  iid = iid = randint(100000,999999)
  while iid in exist : iid = randint(100000,999999)
  cmd = 'INSERT INTO sell_item VALUES (:iid1,:name1,:price1,:condition1,:img1,:sid1)';
  g.conn.execute(text(cmd), iid1 = iid,name1=name,price1=int(price),condition1=condition,img1='image12',sid1=int(session['logsid']));
  return redirect('/')



# Lougout
@app.route('/logout/', methods=['POST','GET'])
def logout():
  session.clear()
  return render_template("login.html")


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
