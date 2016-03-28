import datetime
import json
import logging
import os

from flask.app import Flask
from flask.globals import request
from flask.json import jsonify
from flask.templating import render_template
from flask_login import login_required, LoginManager

from database import dataaccess
from database.database import db
from utils.gen_utils import jsonify_sql_alchemy_model
from cherrypy._cpreqbody import Part
from utils import perf_utils


app = Flask(__name__)
app.logger_name = 'arctic'
app.logger.setLevel(logging.INFO)
# Set secret key required for creating sessions.
# The user can view the contents of the cookie but cannot edit it without knowing this secret key
app.secret_key = os.environ['SESSION_SECRET_KEY']
# The session will expire after 1 hour of inactivity
app.permanent_session_lifetime = datetime.timedelta(minutes=60)

login_manager = LoginManager()
login_manager.init_app(app)
# This callback is used to reload the user object from the user id stored in the session.
@login_manager.user_loader
def load_user(user_id):
    #return UserService().retrieve_entity_by_id(user_id)
    pass

@app.route("/", methods=['GET'])
#@login_required
def home():
    
    context = {}

    return render_template('home.html', **context)

@app.route("/pickconfig", methods=['GET'])
#@login_required
def pickconfig():
    
    context = {}

    return render_template('pickconfig.html', **context)

@app.route("/preset", methods=['GET'])
#@login_required
def preset():
    
    context = {}

    return render_template('preset.html', **context)

@app.route("/custom", methods=['GET'])
#@login_required
def custom():
    
    context = {}

    return render_template('custom.html', **context)

@app.route("/bench", methods=['GET'])
#@login_required
def bench():
    
    context = {}

    return render_template('bench.html', **context)

@app.route("/namecube", methods=['GET'])
#@login_required
def namecube():
    
    context = {}

    return render_template('namecube.html', **context)

@app.route("/cubetemp", methods=['GET'])
#@login_required
def cubetemp():
    
    cpus = dataaccess.get_all_cpus()
    for cpu in cpus:
        print 'cpus: ' + str(cpu.id)
    
    context = {'cpus' : cpus}
    print context
    return render_template('cube-temp.html', **context)

@app.route("/cube", methods=['GET'])
#@login_required
def cube():
    
    cpus = dataaccess.get_all_cpus()
    for cpu in cpus:
        print 'cpus: ' + str(cpu.id)
    
    context = {'cpus' : cpus}
    print context
    return render_template('cube.html', **context)

@app.route("/getparts", methods=['GET'])
#@login_required
def get_parts():
    
    """
    get compatible parts
    """
    compat_parts = dataaccess.get_compatible_parts(**request.args.to_dict())
    
    """
    get all parts
    """
    all_parts = dataaccess.get_compatible_parts(target=request.args.get('target'))
    
    """
    join the lists (and remove duplicates)!
    """
    render_parts = []
    added = set()
    for part in compat_parts:
        added.add(part.id)
        part.compatible = True
        render_parts.append(part)
    
    for part in all_parts:
        if part.id not in added:
            part.compatible = False
            render_parts.append(part)
            
    """
    set performance color for parts
    """
    perf_utils.set_performance_color_for_parts(render_parts)
    
    render_parts = json.dumps(render_parts, cls=jsonify_sql_alchemy_model(), check_circular=False)
    
    return jsonify({'compatible':render_parts})    

        

@app.route("/saverig", methods=['POST'])
#@login_required
def save_rig():
    """
    rig_json = request.get_json().get('rig')
    comment_id = CustomerCommentService().create_entity_from_dict(comment_json)
    return jsonify({'response':comment_id})
    """
    rig = dataaccess.save_rig(request.get_json().get('rig'), 2) ### <-- hardcoded user id for now
    
    return jsonify({'response' : rig.id})

@app.route("/getrig", methods=['GET'])
#@login_required
def get_rig():
    cpus = dataaccess.get_rig(request.args.get('rig_id', None))
    return jsonify(compatible = cpus)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session().close()

@app.after_request
def commit_session(response):
    db.session().commit()
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
