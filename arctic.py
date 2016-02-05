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
    
    cpus = dataaccess.get_all_cpus()
    for cpu in cpus:
        print 'cpus: ' + str(cpu.id)
    
    context = {'cpus' : cpus}
    print context
    return render_template('home.html', **context)

@app.route("/getparts", methods=['GET'])
#@login_required
def get_parts():
    
    
    compat_parts = dataaccess.get_compatible_parts(**request.args.to_dict())
    compat_parts = json.dumps(compat_parts, cls=jsonify_sql_alchemy_model(), check_circular=False)
    
    return jsonify({'compatible':compat_parts})    

        

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
