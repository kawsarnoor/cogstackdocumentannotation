from flask import Flask, jsonify, request, json
from flask_cors import CORS
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from random import sample 
import os.path
from functools import wraps
from datetime import datetime, timezone, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import time


# instantiate the app
# DEBUG = True
app = Flask(__name__)
app.config['SECRET_KEY'] = 'randomsecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

# load database
db = SQLAlchemy(app)

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

## Model Definitions
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    username = db.Column(db.String(1000), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    admin = db.Column(db.Boolean, default=True, nullable=False)

    @classmethod
    def authenticate(cls, **kwargs):
        username = kwargs.get('username')
        password = kwargs.get('password')

        if not username or not password:
            return None

        user = cls.query.filter_by(username=username, password=password).first()
        # password_valid = check_password_hash(user.password, password)

        if not user :
            return None
        
        print('user found', user)

        return user

    def to_dict(self):
        return dict(id=self.id, username=self.username)


class Dataset(db.Model):
    __tablename__ = 'dataset'

    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy 
    name = db.Column(db.String(1000), unique=True, nullable=False) 


class Document(db.Model):
    __tablename__ = 'document'

    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy  
    text = db.Column(db.Text, nullable=False)

    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship("Dataset", backref=db.backref('document', cascade='delete, delete-orphan'))


projectlabel_association = db.Table('projectlabel_association', db.Model.metadata,
                        db.Column('project_id', db.Integer(), db.ForeignKey('project.id')),
                        db.Column('label_id', db.Integer(), db.ForeignKey('label.id')))

projectuser_association = db.Table('projectuser_association', db.Model.metadata,
                        db.Column('project_id', db.Integer(), db.ForeignKey('project.id')),
                        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')))

class Label(db.Model):
    __tablename__ = 'label'

    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy  
    label = db.Column(db.String(1000), nullable=False) 
    labelDescription = db.Column(db.String(1000)) # some meta information for a label - description (e.g: negation)
    labelType = db.Column(db.String(1000)) # sentence annotation or document annotation


class Project(db.Model):
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy   
    name = db.Column(db.String(1000), unique=True, nullable=False) 
    description = db.Column(db.Text, nullable=True)
    nlptasktype = db.Column(db.String(1000), nullable=True) # multiclass, multilabel,
 
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship("Dataset", backref=db.backref('project', cascade='delete, delete-orphan'))

    labels = db.relationship("Label", secondary=projectlabel_association, backref=db.backref('project', lazy='dynamic'))
    users = db.relationship("User", secondary=projectuser_association, backref=db.backref('project', lazy='dynamic'))


class AnnotatedDocument(db.Model):
    __tablename__ = 'annotateddocument'
    
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", backref=db.backref('annotateddocument', cascade='delete, delete-orphan'))

    label_id = db.Column(db.Integer, db.ForeignKey('label.id'))
    label = db.relationship("Label", backref=db.backref('annotateddocument', cascade='delete, delete-orphan'))

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship("Project", backref=db.backref('annotateddocument', cascade='delete, delete-orphan'))

    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    document = db.relationship("Document", backref=db.backref('annotateddocument', cascade='delete, delete-orphan'))
    
## API Endpoints
def login_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get('Authorization', '').split()
        print('validating token')
        invalid_msg = {
            'message': 'Invalid token. Registeration and / or authentication required',
            'authenticated': False
        }
        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }

        try:
            token = auth_headers[0]
            data = jwt.decode(token, app.config['SECRET_KEY'])
            user = User.query.filter_by(username=data['user']).first()
            if not user:
                raise RuntimeError('User not found')
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return jsonify(invalid_msg), 401

    return _verify


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.authenticate(**data)

    if not user:
        return jsonify({'message': 'login error', 'authenticated': False}), 401
    
    token = jwt.encode({'user': user.username, 'iat': datetime.now(timezone.utc),
                        'exp': datetime.now(timezone.utc) + timedelta(minutes=360)},
                        app.config['SECRET_KEY'])
    
    

    print('printing token')

    return jsonify({'token':token.decode('UTF-8'), 'isAdmin': user.admin})             
    

@app.route('/refreshtoken', methods=['POST'])
def refreshtoken():

    start = time.time()

    auth_headers = request.headers.get('Authorization', '').split()
    username = request.get_json()['user']

    newtoken = jwt.encode({'user': username, 'iat': datetime.now(timezone.utc),
                        'exp': datetime.now(timezone.utc) + timedelta(minutes=60)},
                        app.config['SECRET_KEY'])

    try:
        token = auth_headers[0]

        print(time.time() - start)

        data = jwt.decode(token, app.config['SECRET_KEY'])
        user = User.query.filter_by(username=data['user']).first()
        if not user:
            raise RuntimeError('User not found')
        return jsonify({'token':newtoken.decode('UTF-8')}) 
    except jwt.ExpiredSignatureError:
        return jsonify({'token':newtoken.decode('UTF-8')})
    except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return jsonify(invalid_msg), 401

@app.route("/testendpoint", methods=['POST'])
@login_required
def testendpoint():
    print('arrived at endpoint')
    return 'succesfully reached endpoint'


@app.route('/getnextdocument', methods=['GET'])
def getnextdocument():
    # Here we implement active learning
    return jsonify({
        'status': 'success',
        'labels': LABELS[COMPLETED[-1]],
        'spans': SPANS[COMPLETED[-1]],
        'span_values': getspanvalueslist(-1)
    })


@app.route('/getpreviousdocument', methods=['GET'])
def getpreviousdocument():
    return jsonify({
        'status': 'success',
        'labels': LABELS[COMPLETED[-1]]
    })


@app.route('/updateSpans', methods=['POST'])
def updateSpans():
    response_object = {'status': 'success'}
    req_data = request.get_json()
    spans = req_data['newspans']
    category = req_data['category']
    label = req_data['label']     
    id = req_data['id'] 
    combinedspans = list(set(spans + SPANS[id][category][label])) 

    print('updating span:', 'id:', id, ',label:', label, ',category:', category)

    SPANS[id][category][label] = combinedspans
    saveProgress()
    return response_object


@app.route('/changelabel', methods=['POST'])
@login_required
def changelabel(user):
    
    req_data = request.get_json()
    label_id = req_data['label_id']
    document_id = req_data['document_id']
    project_id = req_data['project_id']
    
    document = Document.query.get(document_id)
    label = Label.query.get(label_id)
    project = Project.query.get(project_id)


    if project.nlptasktype == 'multiclass':
        annotatedDocument = AnnotatedDocument.query.filter_by(project_id=project_id, document_id=document_id, user=user).first()

        if annotatedDocument:
            annotatedDocument.label = label
        else:
            annotatedDocument = AnnotatedDocument(user=user, label=label, project=project, document=document)
    
    if project.nlptasktype == 'multilabel':
        annotatedDocument = AnnotatedDocument.query.filter_by(project_id=project_id, document_id=document_id, label_id=label_id, user=user).first()

        if annotatedDocument:
            annotatedDocument.label = label
        else:
            annotatedDocument = AnnotatedDocument(user=user, label=label, project=project, document=document)   


    db.session.add(annotatedDocument)
    db.session.commit()


    return jsonify({'status': 'success'})


@app.route("/getCompleted", methods=['POST'])
@login_required
def getCompleted(user):

    start = time.time()

    req_data = request.get_json()
    project_id = req_data['project_id']
    dataset = Project.query.get(project_id).dataset
    nlptasktype = Project.query.get(project_id).nlptasktype

    documents = Document.query.filter_by(dataset=dataset)
    documents = list(documents)
    document_ids = [d.id for d in documents]

    annotateddocumentsquery = AnnotatedDocument.query.filter(AnnotatedDocument.document_id.in_(document_ids))
    annotateddocuments = list(annotateddocumentsquery.filter_by(user=user))
    completed_documents = [ad.document.id for ad in annotateddocuments]

    document_ids = []
    for d in documents:
        document_ids.append(d.id)

    print('getCompleted', time.time() - start)

    return jsonify({'document_ids': document_ids, 'completed_ids': completed_documents, 'nlptasktype': nlptasktype})


@app.route("/getProjects", methods=['POST']) # This returns projects to the project page
@login_required
def getProjects(user):

    projects = Project.query.join(User.project).filter(User.id == user.id).all()

    projects_data = []
    for project in projects:
        project_data = {}
        project_data['id'] = project.id
        project_data['name'] = project.name
        project_data['description'] = project.description
        project_data['dataset'] = project.dataset.name
        project_data['users'] = [user.id for user in project.users]
        
        projects_data.append(project_data)

    return jsonify({'projects': projects_data})

@app.route("/getProject", methods=['POST']) # change name!
@login_required
def getProject(user):
    req_data = request.get_json()
    project_id = req_data['project_id']
    project = Project.query.get(project_id)
    available_labels = [label.label for label in project.labels]
    available_label_ids = [label.id for label in project.labels]
    starting_document_id = project.dataset.document[0].id

    return jsonify({'available_labels': available_labels, 'available_label_ids': available_label_ids, 'starting_document_id': starting_document_id})


@app.route('/getDocument', methods=['POST'])
@login_required
def getdocument(user):

    start = time.time()

    req_data = request.get_json()
    document_id = req_data['document_id']

    document_text = Document.query.get(document_id).text
    
    print('getDocument:', time.time() - start)

    return jsonify({
        'document_text': document_text
    })


@app.route('/getAnnotatedDocument', methods=['POST'])
@login_required
def getAnnotatedDocument(user):

    print('getting annotated Document')
    req_data = request.get_json()
    document_id = req_data['document_id']

    document_text = Document.query.get(document_id).text
    annotateddocuments = AnnotatedDocument.query.filter_by(user=user, document_id=document_id).all()

    if len(annotateddocuments) > 0:
        label_ids = [annotateddocument.label.id for annotateddocument in annotateddocuments]
    else:
        label_ids = [1]



    return jsonify({
        'label_ids': label_ids, # keepinng this as a list as eventually this method needs to handle multiclass labelling 
    })

## Initialise the admin panel
admin = Admin(app, name='Cogstack Annotation Tool', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Document, db.session))
admin.add_view(ModelView(Project, db.session))
admin.add_view(ModelView(Label, db.session))
admin.add_view(ModelView(AnnotatedDocument, db.session))
admin.add_view(ModelView(Dataset, db.session))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5001')
    # app.run(host='0.0.0.0')
