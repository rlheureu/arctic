import datetime
from functools import wraps
import json
import logging
from operator import attrgetter
import os
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

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

from action import fbauth, arctic_auth, new_user, account_claims, \
    recommendations, price_grabber, jobs
from action.price_grabber import AmazonExtractor
from database import dataaccess
from database.database import db
from models.models import User, Rig, BaseComponent
from utils import perf_utils, retaildata_utils, sort_utils
from utils.exception import ClaimInvalidException
from utils.gen_utils import jsonify_sql_alchemy_model
import time


app = Flask(__name__)
app.logger_name = 'app'
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

"""
init logger
"""
LOG = logging.getLogger('app')

"""
initialize jobs
"""
jobs.start_scheduler()

"""
appstart time
"""
APPSTART_TIME = "{:.0f}".format(time.time())

# This callback is used to reload the user object from the user id stored in the session.
@login_manager.user_loader
def load_user(user_id):
    """
    return None if the user_id is invalid
    """
    return arctic_auth.load_user_by_id(user_id)


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/')


@app.route("/", methods=['GET'])
def home():
    
    LOG.info('homepage requested')
    
    context = {}
    context['show_get_started'] = True

    return render_template('home.html', **context)


@app.route("/sharecube", methods=['GET'])
@login_required
def sharecube():
    context = {}
    return render_template('sharecube.html', **context)

@app.route("/loginuser", methods=['POST'])
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
def logoutuser():
    logout_user()
    return redirect('/')

@app.route("/createuser", methods=['POST'])
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
def isloggedin():
    
    loggedin = current_user.is_authenticated
    
    return jsonify({'loggedin' : True}) if loggedin else jsonify({'loggedin' : False})
    

@app.route("/loginfbuser", methods=['POST'])
def loginfbuser():
    
    fbtoken = request.form.get('token')
    fbid = request.form.get('fbid')
    
    fbauth.login_fb_user(fbid, fbtoken)

    return jsonify({'authenticated' : True})

def valid_next_url(next):
    """ TODO IMPLEMENT THIS """
    return True

@app.route("/fbregister", methods=['GET'])
def isfbregistered():
    
    fb_userid = request.args.get('fbid')
    reg = fbauth.is_fb_user_registered(fb_userid)
    
    return jsonify({'registered' : reg})

@app.route("/fbregister", methods=['POST'])
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


def super_admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        elif not current_user.is_super_admin():
            return login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view

@app.route("/superadmin", methods=['GET'])
@super_admin_login_required
def superadmin():
    
    context = {'all_cpus' : dataaccess.get_all_cpus(active_only=False),
               'all_chassis' : dataaccess.get_all_chassis(active_only=False),
               'all_displays' : dataaccess.get_all_displays(active_only=False),
               'all_gpus' : dataaccess.get_all_gpus(active_only=False),
               'all_memory' : dataaccess.get_all_memory(active_only=False),
               'all_mobos' : dataaccess.get_all_mobos(active_only=False),
               'all_power' : dataaccess.get_all_power(active_only=False),
               'all_storage' : dataaccess.get_all_storage(active_only=False)}
    
    return render_template('superadmin/main.html', **context)

@app.route("/superadmin/savecomponents", methods=['POST'])
@super_admin_login_required
def superadmin_savecomponents():
    
    """
    Get data from the form to save
    """
    
    print 'posted data: {}'.format(str(request.get_json())) 
    
    dataaccess.superadmin_save_components(current_user, request.get_json())
    #rig = dataaccess.save_rig(request.form, current_user.get_id())
    
    return jsonify({'success' : True})

@app.route("/selectrig", methods=['GET'])
def selectrig():
    
    rigs = dataaccess.get_rigs_by_user_id(current_user.id)

    perf_utils.set_performance_color_for_rigs(rigs)

    rigs.sort(key=lambda rig: rig.perf_color_coded, reverse=True)

    context = {'rigs':rigs, 'currpagenav' : 'bench'}

    return render_template('selectrig.html', **context)

@app.route("/preset", methods=['GET'])
def preset():
    
    rig_presets = dataaccess.get_rig_presets()
    
    context = {'rig_presets' : rig_presets, 
               'currpagenav':'recommendedrigs'}
    
    if request.args.get('use', None): context['use'] = request.args.get('use')
    
    return render_template('preset.html', **context)

@app.route("/use", methods=['GET'])
def use():
    context = {'currpagenav':'bench',
               'logged_in' : True if current_user.is_authenticated else False}

    return render_template('use.html', **context)

@app.route("/use/modify", methods=['POST'])
def use_modify():
    
    print request.form
    
    rig = dataaccess.modify_use(request.form, current_user.get_id())

    return jsonify({'rig_use' : rig.use}) if rig else jsonify({})

@app.route("/removepart", methods=['POST'])
def remove_part():
    
    print request.form.get('part_id')
    part_id = request.form.get('part_id')
    
    dataaccess.remove_part(part_id, current_user.get_id())

    return jsonify({'part_id' : part_id})

@app.route("/faq", methods=['GET'])
def faq():
    
    context = {'currpagenav' : 'faq'}

    return render_template('faq.html', **context)

@app.route("/account", methods=['GET'])
@login_required
def account():
    
    context = {'currpagenav' : 'account'}

    return render_template('account.html', **context)

@app.route("/componentfps", methods=['GET'])
def get_component_fps():
    
    fpsdata = dataaccess.get_component_fps_data('CPU')

    return jsonify({'fps_data' : perf_utils.get_fps_map(fpsdata)})

@app.route("/forgotpwd", methods=['GET'])
def forgotpwd():
    
    context = {}

    return render_template('forgotpwd.html', **context)

@app.route("/resetpassword", methods=['POST'])
def resetpassword():
    
    email = request.form.get('email')
    
    account_claims.initiate_password_reset(email)

    return jsonify({'success' : True})

@app.route("/bench", methods=['GET'])
def bench():
    
    context = {}
    context['currpagenav'] = 'build'
    
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
        if rig.upgrade_from_id:
            context['upgrade'] = rig.upgrade_from_id
            context['upgrade_name'] = rig.upgrade_from.name
        return render_template('bench.html', **context)
    
    
    """
    Rig not being requested, this must be the wizard then:
    """
    
    if request.args.get('name', None): context['cube_name'] = request.args.get('name')
    if request.args.get('preset', None): context['preset'] = request.args.get('preset')
    if request.args.get('use', None): context['use'] = request.args.get('use')
    upgrade = request.args.get('upgrade', None)
    if upgrade:
        context['upgrade'] = upgrade
        upgradeobj = dataaccess.get_rig(upgrade)
        if upgradeobj: context['upgrade_name'] = upgradeobj.name
        
    context['app_start_time'] = APPSTART_TIME
    return render_template('bench.html', **context)

@app.route("/showcase", methods=['GET'])
@login_required
def showcase():

    rigs = dataaccess.get_rigs_by_user_id(current_user.id)

    perf_utils.set_performance_color_for_rigs(rigs)

    rigs.sort(key=lambda rig: rig.perf_color_coded, reverse=True)
    
    owned_rigs = []
    exp_rigs = []
    all_parts = []
    for rig in rigs:
        if rig.use == 'owned': owned_rigs.append(rig)
        else: exp_rigs.append(rig)
    
    all_parts.extend(current_user.owned_parts)
    all_parts.sort(key=lambda part: part.component.adjusted_display_name, reverse=True)
    
    owned_cpu = []
    owned_gpu = []
    owned_memory = []
    owned_display = []
    owned_power = []
    owned_chassis = []
    owned_motherboard = []
    owned_storage = []
    
    for owned_part in all_parts:
        if owned_part.component.type == 'CPU': owned_cpu.append(owned_part)
        elif owned_part.component.type == 'GPU': owned_gpu.append(owned_part)
        elif owned_part.component.type == 'CHASSIS': owned_chassis.append(owned_part)
        elif owned_part.component.type == 'STORAGE': owned_storage.append(owned_part)
        elif owned_part.component.type == 'POWER': owned_power.append(owned_part)
        elif owned_part.component.type == 'MEMORY': owned_memory.append(owned_part)
        elif owned_part.component.type == 'MOTHERBOARD': owned_motherboard.append(owned_part)
        elif owned_part.component.type == 'DISPLAY': owned_display.append(owned_part)
    
    """ include datetime for usage on static files that should not be cached """
    
    
    context = {'exp_rigs':exp_rigs, 'owned_rigs': owned_rigs,
               'currpagenav' : 'showcase',
               'all_parts': all_parts,
               'owned_cpu' : owned_cpu,
               'owned_gpu' : owned_gpu,
               'owned_memory' :owned_memory,
               'owned_display' : owned_display,
               'owned_power' : owned_power,
               'owned_chassis' : owned_chassis,
               'owned_motherboard' : owned_motherboard,
               'owned_storage' : owned_storage}
    
    return render_template('showcase.html', **context)

@app.route("/showcasenew", methods=['GET'])
@login_required
def showcasenew():

    rigs = dataaccess.get_rigs_by_user_id(current_user.id)

    perf_utils.set_performance_color_for_rigs(rigs)

    rigs.sort(key=lambda rig: rig.perf_color_coded, reverse=True)

    context = {'rigs':rigs, 'currpagenav' : 'showcase'}
    return render_template('showcase.html', **context)

@app.route("/namecube", methods=['GET'])
def namecube():
    
    context = {'currpagenav':'build'}
    
    if request.args.get('preset', None): context['preset'] = request.args.get('preset')
    if request.args.get('use', None): context['use'] = request.args.get('use')
    if request.args.get('upgrade', None): context['upgrade'] = request.args.get('upgrade')

    return render_template('namecube.html', **context)

@app.route("/manufacturers/get", methods=['GET'])
def manufacturers_get():
    target = request.args.get('target')
    return json.dumps(dataaccess.get_manufacturers(target))

@app.route("/fpstable", methods=['GET'])
def get_combined_fps_table():

    cpu_id = request.args.get('cpu_id')
    gpu_id = request.args.get('gpu_id')
    
    cpu = dataaccess.get_component(cpu_id)
    gpu = dataaccess.get_component(gpu_id)
    
    fpstable = perf_utils.generate_combined_fps_table(cpu, gpu)
    fpstable = json.dumps(fpstable)
    return fpstable, 200, {'Content-Type': 'application/json'}    

@app.route("/parts/search", methods=['GET'])
def parts_search():

    render_parts = []
    search_string = request.args.get('q')
    target = request.args.get('target')
    motherboard_id = request.args.get('motherboard_id')
    gpu_id = request.args.get('gpu_id')
    memory_id = request.args.get('memory_id')
    display_id = request.args.get('display_id')
    cpu_id = request.args.get('cpu_id')
    chassis_id = request.args.get('chassis_id')
    compat_only = request.args.get('compat') == 'true'
    rank = request.args.get('rank')
    manufacturer = request.args.get('manufacturer')

    compat_parts = dataaccess.search_parts(search_string, target, motherboard_id, gpu_id, memory_id, display_id, cpu_id, chassis_id, manufacturer)

    added = set()
    for part in compat_parts:
        added.add(part.id)
        part.compatible = True
        render_parts.append(part)

    if not compat_only:

        all_parts = dataaccess.search_parts(search_string, target, manufacturer=manufacturer)
    
        for part in all_parts:
            if part.id not in added:
                part.compatible = False
                render_parts.append(part)

    """
    set performance color for parts
    """
    perf_utils.set_performance_color_for_parts(render_parts)
    if rank:
        render_parts = [part for part in render_parts if part.perf_color_coded == int(rank)]
    
    retaildata_utils.populate_prices(render_parts)
    
    """
    populate fps table
    """
    [perf_utils.populate_fps_display_table(part) for part in render_parts]
    
    """
    sort by sort order
    """
    render_parts = sorted(render_parts, cmp=sort_utils.sort_by_available_and_recommended, reverse=True)
    render_parts = json.dumps(render_parts, cls=jsonify_sql_alchemy_model(), check_circular=False)

    return render_parts, 200, {'Content-Type': 'application/json'}    

@app.route("/getparts", methods=['GET'])
def get_parts():
    
    render_parts = []
    reqdict = request.args.to_dict()
    
    if reqdict.get('ids'):
        """
        list of IDs provided for explicit parts
        """
        
        ids = reqdict.get('ids')
        
        for cid in ids.split(','):
            comp = dataaccess.get_component(cid, active=None)
            if comp: render_parts.append(comp)
        
    else:
    
        getpartsparams = ['motherboard_id', 'gpu_id', 'memory_id', 'display_id', 'cpu_id', 'target', 'chassis_id']
        for k in reqdict.keys():
            if k not in getpartsparams:
                del reqdict[k]
            
        
        """
        get compatible parts
        """
        compat_parts = dataaccess.get_compatible_parts(**reqdict)
        compat_parts = [] if not compat_parts else compat_parts # default to empty list
        
        """
        get all parts
        """
        all_parts = dataaccess.get_compatible_parts(target=reqdict.get('target'))
        all_parts = [] if not all_parts else all_parts # default to empty list
        
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
    populate prices
    """
    retaildata_utils.populate_prices(render_parts)
    
    """
    populate fps table
    """
    [perf_utils.populate_fps_display_table(part) for part in render_parts]
    
    """
    sort by sort order
    """
    render_parts = sorted(render_parts, cmp=sort_utils.sort_by_available_and_recommended, reverse=True)
    render_parts = json.dumps(render_parts, cls=jsonify_sql_alchemy_model(), check_circular=False)
    return render_parts, 200, {'Content-Type': 'application/json'}

        

@app.route("/savecube", methods=['POST'])
@login_required
def save_cube():
    """
    
    get the data from the form
    
    """
    print 'posted rig: {}'.format(str(request.form)) 
    
    rig = dataaccess.save_rig(request.form, current_user.get_id())
    
    
    return jsonify({'rig_id' : rig.id})

@app.route("/deletecube", methods=['POST'])
@login_required
def delete_cube():
    """
    get the data from the form
    """
    
    rig_id = request.form.get('cube_id')
    
    print 'delete cube requests for ID {}'.format(rig_id) 
    
    dataaccess.delete_rig(rig_id)
    
    
    return jsonify({'status': 'success'})

@app.route("/getrig", methods=['GET'])
def get_rig():
    rig = dataaccess.get_rig(request.args.get('rig_id', None))
    print rig.id
    return jsonify({'rig':json.dumps(rig, cls=jsonify_sql_alchemy_model(), check_circular=False)})


@app.route("/verifyemail", methods=['GET'])
def email_verification_claimget():
    context = {}

    claimtoken = request.args.get('c', None)

    if account_claims.is_valid_token(claimtoken):
        account_claims.verify_email(claimtoken)
        
    context['email_verified'] = True
    return render_template('claimacct.html', **context)

@app.route("/claimserv/claim", methods=['GET'])
def claimget():
    context = {}

    claimtoken = request.args.get('c', None)

    if account_claims.is_valid_token(claimtoken):
        """ claim exists """
        context['init'] = True
        context['token'] = claimtoken
        context['claim'] = account_claims.retrieve_claim(claimtoken)

    return render_template('claimacct.html', **context)

@app.route("/claimserv/claim", methods=['POST'])
def claimpost():
    context = {}

    password = request.form.get('password', None)
    repeatpass = request.form.get('repeat_password', None)
    claimtoken = request.form.get('token', None)

    if not claimtoken:
        LOG.warn('Account claim attempt failed. No token provided.')
        abort(404)

    if account_claims.is_valid_token(claimtoken):
        """ claim exists """
        context['token'] = claimtoken
        context['claim'] = account_claims.retrieve_claim(claimtoken)
    else:
        """ Invalid! """
        return render_template('claimacct.html', **context)

    valid_request = True
    if not password or not repeatpass:
        context['init'] = True
        context['token'] = claimtoken
        context['errormsg'] = 'All fields are required!'
        valid_request = False

    if password != repeatpass:
        context['init'] = True
        context['token'] = claimtoken
        context['errormsg'] = 'Passwords do not match!'
        valid_request = False

    if len(password) < 4:
        context['init'] = True
        context['token'] = claimtoken
        context['errormsg'] = 'Password must be at least 4 characters.'
        valid_request = False

    if valid_request:
        try:
            account_claims.reset_password(claimtoken, password)
            context['success'] = True
        except ClaimInvalidException: pass

    return render_template('claimacct.html', **context)

@app.route("/recommendcpu", methods=['GET'])
def recommendcpu():
    
    return render_template('recommendations.html')

@app.route("/recommendcpu/json", methods=['GET'])
def recommendcpujson():
    context = {}

    cpu_id = request.args.get('id', None)
    LOG.info('recommend CPU for input {}'.format(cpu_id))
    cpu = dataaccess.get_component(cpu_id)
    results = recommendations.recommend_a_cpu(cpu)
    results['input_cpu'] = cpu
    
    expandfields = ['recommendedmobo', 'recommendedmemory4gb', 'recommendedmemory8gb', 'memrecs', 'fpsgains', 'price']
    resultstr = json.dumps(results, cls=jsonify_sql_alchemy_model(fields_to_expand=expandfields), check_circular=False)
    
    return resultstr, 200, {'Content-Type': 'application/json'}

@app.route("/fetchprices", methods=['GET'])
@super_admin_login_required
def invoke_price_fetch():
    
    LOG.info('running sync prices')
    price_grabber.sync_prices()
    
    return 'Done'  

@app.route("/approvaltool", methods=['GET'])
@super_admin_login_required
def approvaltool():
    context = {}
    
    mobos = dataaccess.get_all_mobos(active_only=False, use_status = BaseComponent.Status.CREATED)
    
    mobosforapproval = []
    
    
    count=0
    
    for mobo in mobos:
        
        count += 1
        if count > 20: break
        
        iteminfo = AmazonExtractor().fetch_3p_item_info(mobo.asin)
        if iteminfo:
            mobo.title_3p = iteminfo.title
            mobo.url_3p = iteminfo.url
            
            mobosforapproval.append(mobo)
            
    context['motherboards'] = mobosforapproval
    
    return render_template('approvaltool.html', **context)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session().close()

@app.after_request
def commit_session(response):
    db.session().commit()
    return response

if __name__ == "__main__":
    
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
