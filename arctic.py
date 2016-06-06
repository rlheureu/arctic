import datetime
from functools import wraps
import json
import logging
import os

from cherrypy._cpreqbody import Part
from flask.app import Flask
from flask.globals import request
from flask.json import jsonify
from flask.templating import render_template
from flask.wrappers import Response
from flask_login import login_required, LoginManager, login_user, current_user, \
    logout_user
from flask_mail import Mail
from flask_security.core import Security
from flask_security.datastore import SQLAlchemyUserDatastore

from action import fbauth, arctic_auth, new_user
from database import dataaccess
from database.database import db
from models.models import User, Rig
from utils import perf_utils
from utils.gen_utils import jsonify_sql_alchemy_model
from werkzeug.utils import redirect


app = Flask(__name__)
app.logger_name = 'arctic'
app.logger.setLevel(logging.INFO)



"""
Session configuration
"""
# Set secret key required for creating sessions.
# The user can view the contents of the cookie but cannot edit it without knowing this secret key
app.secret_key = os.environ['SESSION_SECRET_KEY']
# The session will expire after 1 hour of inactivity
app.permanent_session_lifetime = datetime.timedelta(minutes=60)

"""
Initialize Login Manager
"""
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "register"

"""
FLASK MAIL SETTINGS
"""
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

# This callback is used to reload the user object from the user id stored in the session.
@login_manager.user_loader
def load_user(user_id):
    """
    return None if the user_id is invalid
    """
    return arctic_auth.load_user_by_id(user_id)


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    
    uname = os.environ.get('ARCTIC_DEV_UNAME')
    pwd = os.environ.get('ARCTIC_DEV_PWD')
    
    return username == uname and password == pwd

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=['GET'])
@requires_auth
def home():
    
    context = {}
    context['show_get_started'] = True

    return render_template('home.html', **context)


@app.route("/sharecube", methods=['GET'])
@requires_auth
@login_required
def sharecube():
    context = {}
    return render_template('sharecube.html', **context)

@app.route("/loginuser", methods=['POST'])
@requires_auth
def loginuser():
    
    """
    TODO CSRF!!!!!
    """
    
    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        user = arctic_auth.authenticate(email, password)
        
        if user:
            login_user(user)
            return jsonify({'authenticated' : True})
        else:
            return jsonify({'authenticated' : False,
                            'reason' : 'Invalid username or password'})
    except AttributeError as e:
        return jsonify({'authenticated' : False,
                        'reason' : e.message})

@app.route("/logoutuser", methods=['GET'])
@requires_auth
def logoutuser():
    logout_user()
    return redirect('/')

@app.route("/createuser", methods=['POST'])
@requires_auth
def createuser():
    
    """
    TODO CSRF!!!!!
    """
    
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')
    howheard = request.form.get('howheard')
    
    try:
        user = new_user.create_user(username, email, password, howheard)
        
        if user:
            login_user(user)
            return jsonify({'success' : True})
        else:
            return jsonify({'success' : False,
                            'reason' : 'Unable to create user.'}), 500
    except AttributeError as e:
        return jsonify({'success' : False,
                        'reason' : e.message}), 400

@app.route("/isloggedin", methods=['GET'])
@requires_auth
def isloggedin():
    
    loggedin = current_user.is_authenticated
    
    return jsonify({'loggedin' : True}) if loggedin else jsonify({'loggedin' : False})
    

@app.route("/loginfbuser", methods=['POST'])
@requires_auth
def loginfbuser():
    
    fbtoken = request.form.get('token')
    fbid = request.form.get('fbid')
    
    fbauth.login_fb_user(fbid, fbtoken)

    return jsonify({'authenticated' : True})

def valid_next_url(next):
    """ TODO IMPLEMENT THIS """
    return True

@app.route("/fbregister", methods=['GET'])
@requires_auth
def isfbregistered():
    
    fb_userid = request.args.get('fbid')
    reg = fbauth.is_fb_user_registered(fb_userid)
    
    return jsonify({'registered' : reg})

@app.route("/fbregister", methods=['POST'])
@requires_auth
def fbregisternew():
    fb_userid = request.form.get('fbid')
    fbtoken = request.form.get('fbtoken')
    profilename = request.form.get('profilename')
    howhearabout = request.form.get('howhearabout')
    
    errormsg = None
    try:
        fbauth.registernew(fb_userid, fbtoken, profilename, howhearabout)
        fbauth.login_fb_user(fb_userid, fbtoken)
    except ValueError as e:
        errormsg = e.message
    
    
    return jsonify({'registered' : errormsg != None,
                    'error' : errormsg})

@app.route("/preset", methods=['GET'])
@requires_auth
def preset():
    rig_presets = dataaccess.get_rig_presets()
    context = {'rig_presets' : rig_presets}

    return render_template('preset.html', **context)

@app.route("/custom", methods=['GET'])
@requires_auth
def custom():
    
    context = {}

    return render_template('custom.html', **context)

@app.route("/bench", methods=['GET'])
@requires_auth
def bench():
    
    context = {}
    
    """
    If a RIG is being requested it will take precedence over other
    arguments which would have instead continued the wizard
    """
    rig_id = request.args.get('rig', None)
    if rig_id:
        rig = dataaccess.get_rig(rig_id)
        context['rig'] = rig
        context['cube_name'] = rig.name
        context['my_rig'] = (current_user!= None and current_user.is_authenticated and current_user.id == rig.user.id)
        return render_template('bench.html', **context)
    
    
    """
    Rig not being requested, this must be the wizard then:
    """
    cube_name = request.args.get('name', None)
    preset = request.args.get('preset', None)
    
    if cube_name: context['cube_name'] = cube_name
    if preset: context['preset'] = preset

    return render_template('bench.html', **context)

@app.route("/namecube", methods=['GET'])
@requires_auth
def namecube():
    
    context = {}
    
    preset = request.args.get('preset', None)
    
    if preset: context['preset'] = preset
    

    return render_template('namecube.html', **context)

@app.route("/cubetemp", methods=['GET'])
@requires_auth
def cubetemp():
    
    cpus = dataaccess.get_all_cpus()
    for cpu in cpus:
        print 'cpus: ' + str(cpu.id)
    
    context = {'cpus' : cpus}
    print context
    return render_template('cube-temp.html', **context)

@app.route("/cube", methods=['GET'])
@requires_auth
def cube():
    
    cpus = dataaccess.get_all_cpus()
    for cpu in cpus:
        print 'cpus: ' + str(cpu.id)
    
    context = {'cpus' : cpus}
    print context
    return render_template('cube.html', **context)

@app.route("/getparts", methods=['GET'])
@requires_auth
def get_parts():
    
    render_parts = []
    reqdict = request.args.to_dict()
    
    if reqdict.get('ids'):
        """
        list of IDs provided for explicit parts
        """
        
        ids = reqdict.get('ids')
        
        for cid in ids.split(','):
            render_parts.append(dataaccess.get_component(cid))
        
    else:
    
        getpartsparams = ['motherboard_id', 'gpu_id', 'memory_id', 'display_id', 'cpu_id', 'target']
        for k in reqdict.keys():
            if k not in getpartsparams:
                del reqdict[k]
            
        
        """
        get compatible parts
        """
        compat_parts = dataaccess.get_compatible_parts(**reqdict)
        
        """
        get all parts
        """
        all_parts = dataaccess.get_compatible_parts(target=reqdict.get('target'))
        
        """
        join the lists (and remove duplicates)!
        """
        
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
    
    """
    sort by sort order
    """
    render_parts = sorted(render_parts, key=lambda part: part.sort_order, reverse=True)
    
    render_parts = json.dumps(render_parts, cls=jsonify_sql_alchemy_model(), check_circular=False)
    
    return jsonify({'parts':render_parts})    

        

@app.route("/savecube", methods=['POST'])
@requires_auth
def save_cube():
    """
    
    get the data from the form
    
    """
    print 'posted rig: {}'.format(str(request.form)) 
    
    rig = dataaccess.save_rig(request.form, current_user.get_id())
    
    
    return jsonify({'rig_id' : rig.id})

@app.route("/getrig", methods=['GET'])
@requires_auth
def get_rig():
    rig = dataaccess.get_rig(request.args.get('rig_id', None))
    print rig.id
    return jsonify({'rig':json.dumps(rig, cls=jsonify_sql_alchemy_model(), check_circular=False)})


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session().close()

@app.after_request
def commit_session(response):
    db.session().commit()
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
