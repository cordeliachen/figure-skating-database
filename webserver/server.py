#!/usr/bin/env python2.7
from sqlalchemy import exc
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
from flask import Flask, request, render_template, g, redirect, Response, flash, session, abort

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
DB_USER = "cc4655"
DB_PASSWORD = "061602"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
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
  return render_template("index.html")
#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/fave')
def another():
  cmd2='SELECT S.name FROM fan_favorites_skater F, Skater S WHERE S.skater_id=F.skater_id GROUP BY S.skater_id ORDER BY COUNT(*) DESC LIMIT 1'
  cursor=g.conn.execute(text(cmd2))
  faves=[]
  for result in cursor:
    faves.append(result)
  cursor.close()
  context = dict(data = faves)
  return render_template("anotherfile.html", **context)

@app.route('/add', methods=['POST'])
def add():
  name=request.form['name']
  print(name)
  cmd = 'SELECT * FROM SKATER S WHERE S.name=:nm'
  cursor=g.conn.execute(text(cmd),nm=name)
  names = []
  for result in cursor:
    names.append(result[0])
  cursor.close()
  context = dict(data = names)
  return render_template("index.html", **context)

@app.route('/vote')
def vote():
  cmd0='SELECT c.comp_name FROM poll_predicts_competition p, competition c where p.competition_id=c.competition_id'
  polls=[]
  cursor=g.conn.execute(text(cmd0))
  for result in cursor:
      polls.append(result[0])
  context = dict(data = polls)
  return render_template("poll.html", **context)

@app.route('/sort', methods=['POST'])
def sort():
  element=request.form['element']
  cmd='SELECT S.name, AVG(E.score) FROM Skater S, element E WHERE S.skater_id=E.skater_id and E.element_name=:ele GROUP BY S.skater_id ORDER BY AVG(E.score) DESC'
  cursor=g.conn.execute(text(cmd),ele=element)
  rankings = []
  for result in cursor:
    rankings.append(result[0])
  cursor.close()
  context=dict(data=rankings)
  return render_template("rankings.html", **context)


@app.route('/favorite', methods=['POST'])
def favorite():
  username=request.form['username']
  usercheck='SELECT * FROM fan F WHERE F.username=:user'
  cursor=g.conn.execute(text(usercheck),user=username)
  users=[]
  for result in cursor:
    users.append(result)
  if len(users)==0:
    context=dict(error="This is not a valid figure username!")
    return render_template("anotherfile.html", **context)
  skater=request.form['skater']
  cmd0='SELECT S.skater_id FROM Skater S WHERE S.name=:skater'
  cursor=g.conn.execute(text(cmd0), skater=skater)
  ids = []
  for result in cursor:
    ids.append(result)
  if len(ids)==0:
    context=dict(error="This is not a valid figure skater name!")
    return render_template("anotherfile.html", **context)
  cmd='INSERT INTO fan_favorites_skater VALUES (:user, :id)'
  try:
    g.conn.execute(text(cmd), user=username, id=str(ids[0])[1])
  except exc.SQLAlchemyError:
    context=dict(error="This person is already in your favorites!")
    return render_template("anotherfile.html", **context)
  cmd2='SELECT S.name FROM fan_favorites_skater F, Skater S WHERE S.skater_id=F.skater_id GROUP BY S.skater_id ORDER BY COUNT(*) DESC LIMIT 1'
  cursor=g.conn.execute(text(cmd2))
  faves=[]
  for result in cursor:
    faves.append(result)
  cursor.close()
  context = dict(data = faves)
  return render_template("anotherfile.html", **context)
  
@app.route('/favoritelist', methods=['POST'])
def generateList():
  username=request.form['username']
  cmd='SELECT S.name FROM Skater S, fan_favorites_skater F WHERE F.skater_id=S.skater_id and F.username=:user'
  cursor=g.conn.execute(text(cmd), user=username)
  faves={}
  for result in cursor:
    cmd2='SELECT C.comp_name, C.comp_year, C.comp_location FROM competition C, Skater S, skater_registeredfor_competition R WHERE S.name=:favorite AND S.skater_id=R.skater_id AND R.competition_id=C.competition_id'
    cursor2=g.conn.execute(text(cmd2), favorite=result[0])
    upcoming=[]
    for x in cursor2:
      upcoming.append(x)
    faves[result]=upcoming

  cursor.close()
  context = dict(list = faves)
  return render_template("anotherfile.html", **context)

@app.route('/pollpicked', methods=['POST'])
def makePick():
  competition=request.form['competition']
  cmd='SELECT DISTINCT S.discipline FROM Skater S, skater_registeredfor_competition R, competition C WHERE R.skater_id=S.skater_id and C.comp_name=:comp and C.competition_id=R.competition_id'
  cursor=g.conn.execute(text(cmd), comp=competition)
  disciplines={}
  for result in cursor:
    cmd2='SELECT S.name FROM competition C, Skater S, skater_registeredfor_competition R WHERE S.skater_id=R.skater_id AND R.competition_id=C.competition_id AND C.comp_name=:comp AND S.discipline=:discp'
    cursor2=g.conn.execute(text(cmd2), comp=competition, discp=result[0])
    skaters=[]
    for x in cursor2:
      skaters.append(x)
    disciplines[result]=skaters
  cursor.close()
  context = dict(data = disciplines)
  return render_template("pick.html", **context)
'''
cmd0='SELECT S.name FROM Skater S, skater_registeredfor_competition R, competition C WHERE S.skater_id=R.skater_id and C.comp_name=:comp and C.competition_id=R.competition_id'
  cursor=g.conn.execute(text(cmd0), comp=competition)


  ids = []
  for result in cursor:
    ids.append(result)
  cmd='INSERT INTO fan_votes_in_poll VALUES (:username, :poll, :sktr)'
  g.conn.execute(text(cmd), username=username, poll=poll_id, sktr=str(ids[0][1]))
  cmd='SELECT S.name, count(*) FROM fan_votes_in_poll F, Skater S WHERE F.poll_id=:poll AND F.skater_id=S.skater_id GROUP BY S.skater_id ORDER BY COUNT(*) DESC'
  cursor=g.conn.execute(text(cmd), poll=poll_id)
  poll_results = []
  for result in cursor:
    poll_results.append(result)
  cursor.close()
  context = dict(data = poll_results)
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
    app.secret_key = os.urandom(12)
    HOST, PORT = host, port
    print ("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
