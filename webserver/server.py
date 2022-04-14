

"""
Columbia W4111 Intro to databases

To run locally

    python server.py

Go to http://localhost:8111 in your browser
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from markupsafe import escape
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

# connect to the database in project1 part2

DATABASEURI = "postgresql://yh3416:5933@w4111.cisxo09blonu.us-east-1.rds.amazonaws.com/proj1part2"
engine = create_engine(DATABASEURI)

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
  return render_template("home.html")

### Helper Functions ###

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
  table["header"] = header
  cursor.close()
  return table

### Entity pages ###

@app.route("/medal_table")
def medal_page():
    header = {"National Olympic Committees (NOC)":"noc_name","Gold":"gold",
    "Silver":"silver", "Bronze":"bronze","Total Medal":"total"}
    table = to_table("SELECT * , gold+silver+bronze as total FROM NOCs ORDER BY gold+silver+bronze DESC",header)
    return render_template("entity.html", table_name = "NOCs", title = "Medal Table",table=table)

@app.route("/sports")
def sports_page():
    header = {"Sports Name":"sports_name"}
    table = to_table("SELECT * FROM Sports",header)
    return render_template("entity.html", table_name = "Sports", title = "Sports",table=table)

@app.route("/athletes")
def athletes_page():
  header = {"Name": "athlete_name"}
  table = to_table("SELECT athlete_name FROM Athletes",header)
  return render_template("entity.html", table_name = "Athletes",title = "Athletes",table=table)

@app.route("/events")
def events_page():
  header = {"Events": "events_name", "Sports": "sports_name", "Date" :"event_date",
  "Start Time": "start_time" ,"End Time":"end_time", "Individual Event" :"indiv"}
  table = to_table("""select events_name, sports_name, event_date, start_time, end_time,
case when is_individual is False then 'No' else 'Yes' end as indiv
 from Events e join Sports s on e.sports_id = s.sports_id""",header)
  return render_template("entity.html", table_name = "Events", title = "Events",table=table)

@app.route("/teams")
def teams_page():
  header = {"Team id":"team_id"}
  table = to_table("SELECT cast(team_id as text) FROM Teams",header)
  return render_template("entity.html", table_name = "Teams", title = "Teams",table=table)


@app.route("/coaches")
def coaches_page():
  header = {"Coach Name":"coach_name"}
  table = to_table("SELECT * FROM Coaches",header)
  return render_template("entity.html", table_name = "Coaches", title = "Coaches",table=table)

### Relation pages ###

# Helper function for relation

def to_relation(attr, attr_command, rela, relation_command):
  attributes = {}
  for at in attr:
    cursor = g.conn.execute(f"select distinct {at} from " + attr_command)
    for result in cursor:
      attributes[at] = result[0]
  relations = {}
  for re in rela:
      cursor = g.conn.execute(f"select distinct {re} from "+ relation_command + f"""and {re} is not null""")
      lst = []
      for result in cursor:
        lst.append(str(result[0]))
      relations[re] = lst
  table = {}
  table["attributes"] = attributes
  table["relations"] = relations
  return table

@app.route("/relation/<entity_name>")
def athletes_page_detail(entity_name): 
  # NOC*ROC
  table_name, primary_key = entity_name.split("*")
  true_name = primary_key.replace("_"," ")
  if table_name == "Athletes":
    attr =["athlete_name","age","athlete_gender","noc_name","coach_name"] 
    rela = ["team_id", "events_name"]
    attr_command = f"""
      (select athlete_name,
      age,
      case when gender = 0 then 'Female' when gender = 1 then 'Male' end as athlete_gender,
      noc_name,
      coach_name
      from ({escape(table_name)} a 
      join Participants p
      on p.athlete_id = a.athlete_id
      left outer join participant_represents_noc	prn
      on p.pat_id = prn.pat_id 
      left outer join NOCs n 
      on n.noc_id = prn.noc_id 
      left outer join coach_supervise_participant csp
      on p.pat_id = csp.pat_id 
      left outer join (select coach_id, coach_name from coaches) c
      on csp.coach_id = c.coach_id)agg) t
      where {attr[0]} = '{escape(true_name)}' """
    rela_command = f"""
      {escape(table_name)} a 
      left outer join 
      athlete_form_team	aft
      on a.athlete_id = aft.athlete_id
      left outer join athlete_participate_event ape
      on a.athlete_id = ape.athlete_id
      left outer join events e
      on ape.events_id = e.events_id
      where {attr[0]} = '{escape(true_name)}' """
    table = to_relation(attr,attr_command, rela,rela_command)
  elif table_name == "NOCs":
    attr = ["noc_name","gold","silver","bronze"]
    rela = ["athlete_name","sports_name"]
    command = f"""(select noc_name, gold,silver,bronze,sports_name,athlete_name
                from participant_represents_noc prn
                left outer join nocs n
                on prn.noc_id = n.noc_id
                left outer join
                participant_register_sports prs
                on prn.pat_id = prs.pat_id
                left outer join sports s
                on prs.sports_id = s.sports_id
                left outer join participants p
                on prn.pat_id = p.pat_id
                left outer join athletes a
                on p.athlete_id = a.athlete_id)agg
                where {attr[0]} = '{true_name.replace("'","''")}'"""
    table = to_relation(attr,command,rela, command)
  elif table_name == "Sports":
    attr = ["sports_name"]
    attr_command = f""" Sports where {attr[0]} = '{true_name.replace("'","''")}' """
    rela = ["events_name","athlete_name","team_id"]
    rela_command = f""" (select events_name, athlete_name,aft.team_id,sports_name
                    from events e
                    left outer join sports s
                    on e.sports_id = s.sports_id
                    left outer join
                    participant_register_sports prs
                    on s.sports_id = prs.sports_id
                    left outer join participants p
                    on prs.pat_id = p.pat_id
                    left outer join athletes a
                    on p.athlete_id = a.athlete_id
                    left outer join teams t
                    on p.team_id = t.team_id
                    left outer join athlete_form_team aft
                    on a.athlete_id = aft.athlete_id)agg
                    where {attr[0]} = '{true_name.replace("'","''")}'"""
    table = to_relation(attr,attr_command, rela,rela_command)
  elif table_name == "Events":
    attr =["events_name","sports_name","event_date","start_time","end_time","event_type"] 
    rela = ["athlete_name","team_id"]
    attr_command = f"""(select sports_name,events_name, event_date, start_time, end_time,
       case when is_individual = True then 'individual event' else 'team event' end as event_type
        from Events e
        join Sports s
        on e.sports_id = s.sports_id) agg
        where {attr[0]} = '{true_name.replace("'","''")}' """
    rela_command = f"""(select events_name,athlete_name, team_id
        from events e
        left outer join athlete_participate_event ape
        on e.events_id = ape.events_id
        left outer join team_participate_event tpe
        on e.events_id = tpe.events_id
        left outer join Athletes a
        on ape.athlete_id = a.athlete_id)agg 
        where {attr[0]} = '{true_name.replace("'","''")}' """
    table = to_relation(attr,attr_command, rela,rela_command)
  elif table_name == "Teams":
    attr =["team_id","maximum_participants", "sports_name"]
    attr_command = f"""(select t.team_id, max_num as maximum_participants, sports_name
        from teams t
        left outer join athlete_form_team aft
        on t.team_id = aft.team_id 
        left outer join team_participate_event tpe
        on t.team_id = tpe.team_id
        left outer join (select events_id, sports_id from events) e
        on tpe.events_id = e.events_id 
        left outer join Sports s
        on e.sports_id = s.sports_id)agg
        where {attr[0]} = '{true_name}'"""
    rela = ["athlete_name","events_name"]
    rela_command = f"""(select t.team_id, athlete_name, events_name
        from athlete_form_team aft 
        left outer join teams t
        on aft.team_id = t.team_id
        left outer join Athletes a
        on aft.athlete_id = a.athlete_id
        left outer join team_participate_event tpe
        on t.team_id =tpe.team_id 
        left outer join (select events_name, events_id from events) e
        on tpe.events_id = e.events_id)agg
        where {attr[0]} = '{true_name}'"""
    table = to_relation(attr,attr_command,rela,rela_command)
  elif table_name == "Coaches":
    attr = ["coach_name","gender","age","noc_name"]
    attr_command = f"""(select coach_name, 
                  case when gender = 0 then 'Female' when gender = 1 then 'Male' end as gender,
                  age,
                  noc_name,
                  sports_name
                  from coaches c
                  left outer join coach_supervise_participant csp
                  on c.coach_id = csp.coach_id
                  left outer join participant_represents_noc prn 
                  on csp.pat_id = prn.pat_id
                  left outer join NOCs n
                  on n.noc_id = prn.noc_id
                  left outer join participant_register_sports prs
                  on prn.pat_id = prs.pat_id
                  left outer join sports s
                  on prs.sports_id = s.sports_id)agg
                  where {attr[0]} = '{true_name}'"""
    rela = ["athlete_name","team_id"]
    rela_command = f"""(select coach_name, aft.team_id, a.athlete_name
                        from coaches c
                        left outer join coach_supervise_participant csp
                        on c.coach_id = csp.coach_id
                        left outer join participants p
                        on p.pat_id = csp.pat_id
                        left outer join athlete_form_team aft
                        on p.athlete_id = aft.athlete_id
                        left outer join athletes a 
                        on p.athlete_id = a.athlete_id)agg
                        where {attr[0]} = '{true_name}'"""
    table = to_relation(attr,attr_command,rela,rela_command)
  else:
    raise ValueError()
    
  return render_template("relation.html", title = true_name,table=table)

### Extra functionality pages ###

@app.route("/medal_table/<sort_criteria>")
def medal_page_sort(sort_criteria):
    header = {"National Olympic Committees (NOC)":"noc_name","Gold":"gold",
    "Silver":"silver", "Bronze":"bronze","Total Medal":"total"}
    table = to_table(f"SELECT * , gold+silver+bronze as total FROM NOCs ORDER BY {escape(sort_criteria)} DESC",header)
    return render_template("entity.html", table_name = "NOCs", title = "Medal Table",table=table)



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
app.run(host="0.0.0.0", port=8111, debug=True)
