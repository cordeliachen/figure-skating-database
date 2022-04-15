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

tmpl_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'templates')
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

DB_SERVER = "w4111-4-14.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":" + \
    DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


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
        print("uh oh, problem connecting to database")
        import traceback
        traceback.print_exc()
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


"""
`
`
`
`
`
`
`
`
`
"""


@app.route('/home', methods=('GET', 'POST'))
def home():
    return render_template('index.html')


@app.route('/search', methods=('GET', 'POST'))
def search():
    element_attributes = ['element.skater_id', 'element.competition_id',
                          'element.order_performed', 'element.element_name', 'element.score']
    skater_attributes = ['skater.name', 'skater.age',
                         'skater.country', 'skater.discipline']
    competition_attributes = ['competition.comp_name',
                              'competition.comp_year', 'competition.comp_location']

    if request.method == 'POST':
        select = "SELECT "
        frm = " FROM Skater, Competition, skater_scoresin_competition, element"
        where = """ WHERE skater.skater_id = skater_scoresin_competition.skater_id and 
        competition.competition_id = skater_scoresin_competition.competition_id and
        skater.skater_id = element.skater_id and competition.competition_id = element.competition_id"""
        group_by = ""

        # modify SELECT
        if request.form.getlist('distinct'):
            select += " DISTINCT "

        s = request.form.getlist('column')

        if request.form['scores'] != "na":
            select += "element.skater_id AS sid, element.competition_id AS cid, SUM(element.score) AS score"
        elif not s:
            select += "*"
        else:
            for i in range(len(s) - 1):
                select += s[i] + ", "
            select += s[-1]

        # modify FROM if considering skaters and competitions not in skater_scoresin_competition
        if 'allentries' in request.form:
            where = ""
            # query from skaters
            if request.form['allentries'] == "allskaters":
                frm = " FROM Skater"
                # filter skaters
                selected_skaters = request.form['skaters'].split(", ")
                if selected_skaters[0] != "":
                    where = " WHERE (skater.name = '" + \
                        selected_skaters[0] + "'"
                    for skater in selected_skaters[1:]:
                        where += " or skater.name = '" + skater + "'"
                    where += ")"

                # filter disciplines
                selected_disciplines = request.form.getlist('disciplines')
                if selected_disciplines:
                    # check if already filtered skaters
                    if selected_skaters[0] != "":
                        where += " and (skater.discipline = '" + \
                            selected_disciplines[0] + "'"
                    else:
                        where = " WHERE (skater.discipline = '" + \
                            selected_disciplines[0] + "'"
                    for discipline in selected_disciplines[1:]:
                        where += " or skater.discipline = '" + discipline + "'"
                    where += ")"
            # query from competitions
            else:
                frm = " FROM Competition"
                selected_skaters = request.form['skaters'].split(", ")
                selected_comps = request.form['comps'].split(", ")
                if selected_comps[0] != "":
                    where = " WHERE competition.comp_name = '" + \
                        selected_comps[0] + "'"
                    for comp in selected_comps[1:]:
                        where += " or competition.comp_name = '" + comp + "'"
            query = select + frm + where + group_by
            print(query)
            results = g.conn.execute(query)
            return render_template('searchresults.html', results=results)

        # modify WHERE
        # filter elements
        selected_elements = request.form['elements'].split(", ")
        if selected_elements[0] != "":
            where += " and (element.element_name = '" + \
                selected_elements[0] + "'"
            for element in selected_elements[1:]:
                where += " or element.element_name = '" + element + "'"
            where += ")"

        # filter skaters
        selected_skaters = request.form['skaters'].split(", ")
        if selected_skaters[0] != "":
            where += " and (skater.name = '" + selected_skaters[0] + "'"
            for skater in selected_skaters[1:]:
                where += " or skater.name = '" + skater + "'"
            where += ")"

        # filter competitons
        selected_comps = request.form['comps'].split(", ")
        if selected_comps[0] != "":
            where += " and (competition.comp_name = '" + \
                selected_comps[0] + "'"
            for comp in selected_comps[1:]:
                where += " or competition.comp_name = '" + comp + "'"
            where += ")"

        # filter countries
        selected_countries = request.form['countries'].split(", ")
        if selected_countries[0] != "":
            where += " and (skater.country = '" + selected_countries[0] + "'"
            for country in selected_countries[1:]:
                where += " or skater.country = '" + country + "'"
            where += ")"

        # filter years
        selected_years = request.form['years'].split(", ")
        if selected_years[0] != "":
            where += " and (competition.comp_year = '" + \
                selected_years[0] + "'"
            for year in selected_years[1:]:
                where += " or competition.comp_year = '" + year + "'"
            where += ")"

        # filter disciplines
        selected_disciplines = request.form.getlist('disciplines')
        if selected_disciplines:
            where += " and (skater.discipline = '" + \
                selected_disciplines[0] + "'"
            for discipline in selected_disciplines[1:]:
                where += " or skater.discipline = '" + discipline + "'"
            where += ")"

        # group by program
        if request.form['scores'] != "na":
            group_by = " GROUP BY element.skater_id, element.competition_id"
            if request.form['scores'] == "sp":
                where += " and not element.in_long"
            elif request.form['scores'] == "lp":
                where += " and element.in_long"

        query = select + frm + where + group_by

        if request.form['scores'] != "na":
            query2 = """SELECT skater.name, competition.comp_name, q.score  
                        FROM (""" + query + """) q, skater, competition 
                        WHERE q.sid = skater.skater_id and
                        q.cid = competition.competition_id"""
            print(query2)
            results = g.conn.execute(query2)
        else:
            print(query)
            results = g.conn.execute(query)

        return render_template('searchresults.html', results=results)

    return render_template('search.html', element_attributes=element_attributes,
                           skater_attributes=skater_attributes,
                           competition_attributes=competition_attributes)


@app.route('/searchresults', methods=['POST'])
def searchresults():

    return render_template('searchresults.html')


"""
`
`
`
`
`
`
`
`
`
"""


@ app.route('/another')
def another():
    cmd2 = 'SELECT S.name FROM fan_favorites_skater F, Skater S WHERE S.skater_id=F.skater_id GROUP BY S.skater_id ORDER BY COUNT(*) DESC LIMIT 1'
    cursor = g.conn.execute(text(cmd2))
    faves = []
    for result in cursor:
        faves.append(result)
    cursor.close()
    context = dict(data=faves)
    return render_template("anotherfile.html", **context)


@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    print(name)
    cmd = 'SELECT * FROM SKATER S WHERE S.name= nm'
    cursor = g.conn.execute(text(cmd), nm=name)
    names = []
    for result in cursor:
        names.append(result[0])
    cursor.close()
    context = dict(data=names)
    return render_template("index.html", **context)


@app.route('/vote')
def vote():
    cmd0 = 'SELECT c.competition_id FROM poll_predicts_competition p, competition c where p.competition_id=c.competition_id'
    polls = {}
    cursor = g.conn.execute(text(cmd0))
    for result in cursor:
        cmd1 = 'SELECT c.comp_name, c.comp_location, c.comp_year FROM competition C where C.competition_id=:id'
        cursor2 = g.conn.execute(text(cmd1), id=result[0])
        temp = []
        for x in cursor2:
            temp.append(x)
        polls[result] = x
    context = dict(data=polls)
    return render_template("poll.html", **context)


@ app.route('/sort', methods=['POST'])
def sort():
    element = request.form['element']
    cmd = 'SELECT S.name, AVG(E.score) FROM Skater S, element E WHERE S.skater_id=E.skater_id and E.element_name=:ele GROUP BY S.skater_id ORDER BY AVG(E.score) DESC'
    cursor = g.conn.execute(text(cmd), ele=element)
    rankings = []
    for result in cursor:
        rankings.append(result[0])
    cursor.close()
    context = dict(data=rankings)
    return render_template("rankings.html", **context)


@app.route('/favorite', methods=['POST'])
def favorite():
    username = request.form['username']
    usercheck = 'SELECT * FROM fan F WHERE F.username=:user'
    cursor = g.conn.execute(text(usercheck), user=username)
    users = []
    for result in cursor:
        users.append(result)
    if len(users) == 0:
        context = dict(error="This is not a valid username!")
        return render_template("anotherfile.html", **context)
    skater = request.form['skater']
    cmd0 = 'SELECT S.skater_id FROM Skater S WHERE S.name=:skater'
    cursor = g.conn.execute(text(cmd0), skater=skater)
    ids = []
    for result in cursor:
        ids.append(result)

    if len(ids) == 0:
        context = dict(error="This is not a valid figure skater name!")
        return render_template("anotherfile.html", **context)
    cmd = 'INSERT INTO fan_favorites_skater VALUES (:user, :id)'
    try:
        g.conn.execute(text(cmd), user=username, id=str(ids[0])[1])
    except exc.SQLAlchemyError:
        print("Error deteced")
        context = dict(error="This person is already in your favorites!")
        return render_template("anotherfile.html", **context)


@ app.route('/favoritelist', methods=['POST'])
def generateList():
    username = request.form['username']
    cmd = 'SELECT S.name FROM Skater S, fan_favorites_skater F WHERE F.skater_id=S.skater_id and F.username=:user'
    cursor = g.conn.execute(text(cmd), user=username)
    faves = {}
    for result in cursor:
        cmd2 = 'SELECT C.comp_name, C.comp_year, C.comp_location FROM competition C, Skater S, skater_registeredfor_competition R WHERE S.name=:favorite AND S.skater_id=R.skater_id AND R.competition_id=C.competition_id'
        cursor2 = g.conn.execute(text(cmd2), favorite=result[0])
        upcoming = []
        for x in cursor2:
            upcoming.append(x)
        faves[result] = upcoming

    cursor.close()
    context = dict(list=faves)
    return render_template("anotherfile.html", **context)


@ app.route('/pollpicked', methods=['POST'])
def makePick():
    competition = (request.form['competition'])[1]
    session['competition'] = competition
    cmd = 'SELECT DISTINCT S.discipline FROM Skater S, skater_registeredfor_competition R, competition C WHERE R.skater_id=S.skater_id and :comp=R.competition_id'
    cursor = g.conn.execute(text(cmd), comp=competition)
    disciplines = {}
    for result in cursor:
        cmd2 = 'SELECT S.name FROM competition C, Skater S, skater_registeredfor_competition R WHERE S.skater_id=R.skater_id AND R.competition_id=C.competition_id AND C.competition_id=:comp AND S.discipline=:discp'
        cursor2 = g.conn.execute(text(cmd2), comp=competition, discp=result[0])
        skaters = []
        for x in cursor2:
            skaters.append(x)
            disciplines[result] = skaters
    cursor.close()
    context = dict(data=disciplines)
    return render_template("pick.html", **context)


@app.route('/predict', methods=['POST'])
def processPredictions():
    mensPick = request.form['Mens']
    find = 'SELECT S.skater_id FROM Skater S WHERE S.name=:name'
    cursor = g.conn.execute(text(find), name=mensPick)
    ids = []
    for result in cursor:
        ids.append(result)
    pairsPick = request.form['Pairs']
    cursor = g.conn.execute(text(find), name=pairsPick)
    for result in cursor:
        ids.append(result)
    womensPick = request.form['Womens']
    cursor = g.conn.execute(text(find), name=womensPick)
    for result in cursor:
        ids.append(result)
    dancePick = request.form['Dance']
    cursor = g.conn.execute(text(find), name=dancePick)
    for result in cursor:
        ids.append(result)
        
    username = request.form['username']
    usercheck = 'SELECT * FROM fan F WHERE F.username=:user'
    cursor = g.conn.execute(text(usercheck), user=username)
    users = []
    for result in cursor:
        users.append(result)
    if len(users) == 0:
        context = dict(error="This is not a valid username!")
        return render_template("pick.html", **context)
    competition = session.get('competition', None)

    cmd0 = 'SELECT S.skater_id FROM Skater S WHERE S.name=:skater'
    cursor = g.conn.execute(text(cmd0), skater=mensPick)
    ids = []
    for result in cursor:
        ids.append(result)
    cursor = g.conn.execute(text(cmd0), skater=pairsPick)
    for result in cursor:
        ids.append(result)
        cursor = g.conn.execute(text(cmd0), skater=womensPick)
    for result in cursor:
        ids.append(result)
        cursor = g.conn.execute(text(cmd0), skater=dancePick)
    for result in cursor:
        ids.append(result)

    try:
        cmdMens = 'INSERT INTO fan_votesin_poll VALUES(:user, :comp, :mens)'
        g.conn.execute(text(cmdMens), user=username,
                       mens=str(ids[0])[1], comp=competition)
        cmdPairs = 'INSERT INTO fan_votesin_poll VALUES(:user, :comp, :pairs)'
        g.conn.execute(text(cmdPairs), user=username,
                       pairs=str(ids[1])[1], comp=competition)
        cmdWomens = 'INSERT INTO fan_votesin_poll VALUES(:user, :comp, :womens)'
        g.conn.execute(text(cmdWomens), user=username,
                       womens=str(ids[2])[1], comp=competition)
    except exc.SQLAlchemyError:
        context = dict(error="Already voted")
        return render_template("pick.html", **context)
    cmdMens2 = 'SELECT S.name FROM Skater S, skater_registeredfor_competition R, Competition C, skater_scoresin_competition SC WHERE C.competition_id=:comp AND C.competition_id=R.competition_id AND R.skater_id =S.skater_id AND S.discipline=:discp AND S.skater_id = SC.skater_id GROUP BY S.skater_id ORDER BY AVG(SC.placement) ASC LIMIT 1'
    cursor = g.conn.execute(text(cmdMens2), comp=competition, discp='Mens')
    mensPredicted = []
    for result in cursor:
        mensPredicted.append(result)
    cmdPairs2 = 'SELECT S.name FROM Skater S, skater_registeredfor_competition R, Competition C, skater_scoresin_competition SC WHERE C.competition_id=:comp AND C.competition_id=R.competition_id AND R.skater_id =S.skater_id AND S.discipline=:discp AND S.skater_id = SC.skater_id GROUP BY S.skater_id ORDER BY AVG(SC.placement) ASC LIMIT 1'
    cursor = g.conn.execute(text(cmdPairs2), comp=competition, discp='Pairs')
    pairsPredicted = []
    for result in cursor:
        pairsPredicted.append(result)
    cmdWomens2 = "SELECT S.name FROM Skater S, skater_registeredfor_competition R, Competition C, skater_scoresin_competition SC WHERE C.competition_id=:comp AND C.competition_id=R.competition_id AND R.skater_id =S.skater_id AND S.discipline=:discp AND S.skater_id = SC.skater_id GROUP BY S.skater_id ORDER BY AVG(SC.placement) ASC LIMIT 1 "
    cursor = g.conn.execute(text(cmdWomens2), comp=competition, discp='Womens')
    womensPredicted = []
    for result in cursor:
        womensPredicted.append(result)
    cmdPairs3 = 'SELECT S.name FROM Skater S, skater_registeredfor_competition R, fan_votesin_poll P WHERE S.skater_id=R.skater_id and R.competition_id=:comp and S.skater_id=R.skater_id and S.discipline=:discp GROUP BY S.skater_id ORDER BY COUNT(*) DESC LIMIT 1'
    cursor = g.conn.execute(text(cmdPairs3), comp=competition, discp='Pairs')
    pairRanked = []
    for result in cursor:
        pairRanked.append(result)
    cmdMens3 = 'SELECT S.name FROM Skater S, skater_registeredfor_competition R, fan_votesin_poll P WHERE S.skater_id=R.skater_id and R.competition_id=:comp and S.skater_id=R.skater_id and S.discipline=:discp GROUP BY S.skater_id ORDER BY COUNT(*) DESC LIMIT 1'
    cursor = g.conn.execute(text(cmdMens3), comp=competition, discp='Mens')
    mensRanked = []
    for result in cursor:
        mensRanked.append(result)
    cmdWomens3 = 'SELECT S.name FROM Skater S, skater_registeredfor_competition R, fan_votesin_poll P WHERE S.skater_id=R.skater_id and R.competition_id=:comp and S.skater_id=R.skater_id and S.discipline=:discp GROUP BY S.skater_id ORDER BY COUNT(*) DESC LIMIT 1'
    cursor = g.conn.execute(text(cmdWomens3), comp=competition, discp='Womens')
    womensRanked = []
    for result in cursor:
        womensRanked.append(result)
    context = dict(mens=mensPick, pairs=pairsPick, womens=womensPick, mensP=mensPredicted, pairsP=pairsPredicted,
                   womensP=womensPredicted, pairsR=pairRanked, mensR=mensRanked, womensR=womensRanked)
    return render_template("pick.html", **context)


if __name__ == "__main__":
    import click

    @ click.command()
    @ click.option('--debug', is_flag=True)
    @ click.option('--threaded', is_flag=True)
    @ click.argument('HOST', default='0.0.0.0')
    @ click.argument('PORT', default=8111, type=int)
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
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

    run()
