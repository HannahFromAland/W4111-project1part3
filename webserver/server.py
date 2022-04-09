
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
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



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
# DB_USER = "YOUR_DB_USERNAME_HERE"
# DB_PASSWORD = "YOUR_DB_PASSWORD_HERE"

# DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://yh3416:5933@w4111.cisxo09blonu.us-east-1.rds.amazonaws.com/proj1part2"


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
    print("uh oh, problem connecting to database")
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

@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  '''
  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  header = ["sports_name"]
  table = to_table("SELECT * FROM Sports",header)
  context = dict(data = table)

  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)
  '''
  return render_template("home.html")

def to_table(command, header):
  cursor = g.conn.execute(command)
  table = {}
  data = []
  for result in cursor:
    curr = []
    for var in header.values():
      curr.append(result[var])
    data.append(curr)
  table["data"] = data
  table['header'] = header
  cursor.close()
  return table

@app.route("/medal_table")
def medal_page():
    header = {"National Olympic Committees (NOC)":"noc_name","Gold":"gold",
    "Sliver":"silver", "Bronze":"bronze","Total Medal":"total"}
    table = to_table("SELECT * , gold+silver+bronze as total FROM NOCs ORDER BY gold+silver+bronze DESC",header)
    return render_template("entity.html", title = "Medal Table",table=table)

@app.route("/medal_table/<sort_criteria>")
def medal_page_sort(sort_criteria):
    header = {"National Olympic Committees (NOC)":"noc_name","Gold":"gold",
    "Sliver":"silver", "Bronze":"bronze"}
    table = to_table(f"SELECT * FROM NOCs ORDER BY {sort_criteria} DESC",header)
    return render_template("entity.html", title = "Medal Table",table=table)

@app.route("/sports")
def sports_page():
    header = {"Sports Name":"sports_name"}
    table = to_table("SELECT * FROM Sports",header)
    return render_template("entity.html", title = "Sports",table=table)


@app.route("/athletes")
def athletes_page():
  header = {"Name": "athlete_name"}
  table = to_table("SELECT athlete_name FROM Athletes",header)
  return render_template("entity.html", title = "Athletes",table=table)

@app.route("/events")
def teams_page():
  header = {"Events": "events_name", "Sports": "sports_name", "Date" :"event_date",
  "Start Time": "start_time" ,"End Time":"end_time", "Individual Event" :"indiv"}
  table = to_table("""select events_name, sports_name, event_date, start_time, end_time,
case when is_individual is False then 'No' else 'Yes' end as indiv
 from Events e join Sports s on e.sports_id = s.sports_id""",header)
  return render_template("entity.html", title = "Events",table=table)


  '''
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
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
    '''
app.run(host="127.0.0.1", port=8111, debug=True)
