from flask import Flask, render_template, jsonify, request, make_response, send_file
from flask_cors import CORS
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user, login_required, RoleMixin, Security, SQLAlchemyUserDatastore, UserMixin, utils
from flask_sqlalchemy import SQLAlchemy
from random import sample 
import pandas as pd
import os.path
from functools import wraps
from datetime import datetime, timezone, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
import time
from spacy.lang.en import English
from spacy.symbols import ORTH
from utils.nerannotationsloader import addAnnotations
from app import app, db
import ast

# Load spacy word tokenizer for sending documents as spans
nlp = English()
tokenizer = nlp.tokenizer
tokenizer.add_special_case("<br>", [{ORTH: "<br>"}])


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
    nlptasktype = db.Column(db.String(1000), nullable=True) # multiclass, multilabel, [seperate this out into its own table]
 
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
    dataset = db.relationship("Dataset", backref=db.backref('project', cascade='delete, delete-orphan'))

    labels = db.relationship("Label", secondary=projectlabel_association, backref=db.backref('project', lazy='dynamic'))
    users = db.relationship("User", secondary=projectuser_association, backref=db.backref('project', lazy='dynamic'))

class Annotation(db.Model):
    __tablename__ = 'annotation'
    
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy

    start_idx = db.Column(db.Integer)
    end_idx = db.Column(db.Integer)
    completed = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", backref=db.backref('annotation', cascade='delete, delete-orphan'))

    label_id = db.Column(db.Integer, db.ForeignKey('label.id'))
    label = db.relationship("Label", backref=db.backref('annotation', cascade='delete, delete-orphan'))

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship("Project", backref=db.backref('annotation', cascade='delete, delete-orphan'))

    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    document = db.relationship("Document", backref=db.backref('annotation', cascade='delete, delete-orphan'))

class MetaAnnotation(db.Model):
    __tablename__ = 'metaannotation'

    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy

    annotatation_id = db.Column(db.Integer, db.ForeignKey('annotation.id'))
    annotation = db.relationship("Annotation", backref=db.backref('metaannotation', cascade='delete, delete-orphan'))

    metataskvalue_id = db.Column(db.Integer, db.ForeignKey('metataskvalue.id'))
    metataskvalue = db.relationship("MetaTaskValue", backref=db.backref('metaannotation', cascade='delete, delete-orphan'))

class MetaTask(db.Model):
    __tablename__ = 'metatask'
    
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    metatask = db.Column(db.String(1000), nullable=True)  # name of metatask, e.g. negation, span selection etc
    metatasktype = db.Column(db.String(1000), nullable=True) # multiclass, span, relation, multilabel etc

class MetaTaskValue(db.Model):
    __tablename__ = 'metataskvalue'
    
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    metataskvalue = db.Column(db.Text, nullable=True)

    metatask_id = db.Column(db.Integer, db.ForeignKey('metatask.id'))
    metatask = db.relationship("MetaTask", backref=db.backref('metataskvalue', cascade='delete, delete-orphan'))


## API Endpoints ##
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

@app.route("/changelabel", methods=['POST'])
@login_required
def changelabel(user):
    
    req_data = request.get_json()
    
    document = Document.query.get(req_data['document_id'])
    label = Label.query.get(req_data['label_id'])
    project = Project.query.get(req_data['project_id'])

    if project.nlptasktype == 'multiclass':
        annotatedDocument = Annotation.query.filter_by(project_id=req_data['project_id'], document_id=req_data['document_id'], user=user).first()

        if annotatedDocument: # Document has been labelled before
            if annotatedDocument.label == label: # Document already has the same label as being assigned
                db.session.delete(annotatedDocument) # This toggles the label to delete it
            else:
                annotatedDocument.label = label
                annotatedDocument.completed = True
                
                # Remove metaannotations associated with previous label
                deletemetanns = MetaAnnotation.__table__.delete().where(MetaAnnotation.annotation == annotatedDocument)
                db.session.execute(deletemetanns)

                db.session.add(annotatedDocument)

        else: # Document has not been labelled before. Create new label and save
            annotatedDocument = Annotation(user=user, label=label, project=project, document=document, completed=True)
            db.session.add(annotatedDocument)
    
    if project.nlptasktype == 'multilabel':
        annotatedDocument = Annotation.query.filter_by(project_id=req_data['project_id'], document_id=req_data['document_id'], label_id=req_data['label_id'], user=user).first()

        if annotatedDocument:
            db.session.delete(annotatedDocument) # This means the button has already been pressed. This toggles the function to delete it

        else:
            annotatedDocument = Annotation(user=user, label=label, project=project, document=document, completed=True)   
            db.session.add(annotatedDocument)

    if project.nlptasktype == 'ner':
        label = Label.query.filter_by(label=req_data['label_id']).first() # label we want to assign
        current_entity = req_data['current_entity']
        annotatedDocument = Annotation.query.filter_by(project_id=req_data['project_id'], 
                                                        document_id=req_data['document_id'], 
                                                        start_idx=current_entity['start'],
                                                        end_idx=current_entity['end'],
                                                        user=user).first()

        if annotatedDocument: # Document has been labelled before
                annotatedDocument.label = label
                annotatedDocument.completed = True
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

    annotateddocumentsquery = Annotation.query.filter(Annotation.document_id.in_(document_ids))
    annotateddocuments = list(annotateddocumentsquery.filter_by(user=user))
    completed_documents = [ad.document.id for ad in annotateddocuments if ad.completed]

    document_ids = []
    for d in documents:
        document_ids.append(d.id)

    print('getCompleted', time.time() - start)

    return jsonify({'document_ids': document_ids, 'completed_ids': completed_documents})


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
    nlptasktype = project.nlptasktype

    return jsonify({'available_labels': available_labels, 'available_label_ids': available_label_ids, 'starting_document_id': starting_document_id, 'nlptasktype': nlptasktype})


@app.route('/getDocument', methods=['POST'])
@login_required
def getdocument(user):

    req_data = request.get_json()
    document_id = req_data['document_id']
    document_text = Document.query.get(document_id).text
    document_tokens = tokenizer(document_text).to_json()

    return jsonify({
        'document_tokens': document_tokens
    })


@app.route('/getDocumentNER', methods=['POST'])
@login_required
def getDocumentNER(user):

    req_data = request.get_json()
    document_id = req_data['document_id']
    project_id = req_data['project_id']

    annotations = Annotation.query.filter_by(user=user, project_id=project_id, document_id=document_id).all()

    document_text = Document.query.get(document_id).text
    document_tokens = tokenizer(document_text).to_json()

    annotations_cutdown = [(annotation.start_idx,annotation.end_idx,annotation.label.label) for annotation in annotations]
    
    tokens_with_annotations = addAnnotations(annotations_cutdown, document_tokens)

    return jsonify({
        'document_tokens': tokens_with_annotations,
        'document_text': document_text
    })


@app.route('/getAnnotatedDocumentMultiClassMultiLabel', methods=['POST'])
@login_required
def getAnnotatedDocumentMultiClassMultiLabel(user):

    print('getting annotated Document')
    req_data = request.get_json()
    document_id = req_data['document_id']

    document_text = Document.query.get(document_id).text
    annotateddocuments = Annotation.query.filter_by(user=user, document_id=document_id).all()

    if len(annotateddocuments) > 0:
        label_ids = [annotateddocument.label.id for annotateddocument in annotateddocuments]
    else:
        label_ids = [] # bug

    return jsonify({
        'label_ids': label_ids, # keepinng this as a list as eventually this method needs to handle multiclass labelling 
    })


@app.route('/addSpanToAnnotation', methods=['POST'])
@login_required
def addSpanToAnnotation(user):

    print('adding span to annotated Document')
    req_data = request.get_json()
    document_id = req_data['document_id']
    project_id = req_data['project_id']
    label_id = req_data['label_id']
    span_ids = req_data['span_ids']

    annotation = Annotation.query.filter_by(user=user, project_id = project_id, document_id=document_id, label_id = label_id).first()

    # convert span ids to string:
    span_ids_cleaned = [span_id.split('span_')[1] for span_id in span_ids]
    span_ids_string = ','.join(span_ids_cleaned) # join span ids into string format for storage

    # Prepare the metaannotation
    metatask = MetaTask.query.filter(MetaTask.metatasktype.contains('snippet')).first()
    newmetataskvalue = MetaTaskValue(metatask=metatask)
    newmetataskvalue.metataskvalue = span_ids_string

    db.session.add(newmetataskvalue)
    db.session.commit()

    metaannotation = MetaAnnotation(annotation=annotation, metataskvalue=newmetataskvalue)
    
    db.session.add(metaannotation)
    db.session.commit()

    return jsonify({'status': 'success'})

@app.route('/getSpansForAnnotation', methods=['POST'])
@login_required
def getSpansForAnnotation(user):

    print('getting spans for annotated document')
    req_data = request.get_json()
    document_id = req_data['document_id']
    project_id = req_data['project_id']
    label_id = req_data['label_id']

    annotation = Annotation.query.filter_by(user=user, project_id = project_id, document_id=document_id, label_id = label_id).first()
    metaannotations = MetaAnnotation.query.filter_by(annotation=annotation).all()

    snippets = [metaannotation.metataskvalue.metataskvalue for metaannotation in metaannotations]

    return jsonify({'snippets': snippets})

@app.route('/getEntityInfo', methods=['POST'])
@login_required
def getEntityInfo(user):

    req_data = request.get_json()
    cui= req_data['cui']
    unique = req_data['unique']

    es_results = elasticsearchutils.searchSnomedConcept(cui)    
    entity_information = es_results[0]['_source']

    return jsonify({'entity_information': entity_information})

# @app.route('/searchconceptinelastic', methods=['POST'])
# @login_required
# def searchconceptinelastic(user):

#     req_data = request.get_json()
#     cui = req_data['searchConceptString']
#     unique = req_data['unique']

#     searchresult = elasticsearchutils.searchSnomedConcept(cui)     
#     print(searchresult)

#     return jsonify({'searchresult': searchresult})


@app.route('/deleteEntity', methods=['POST'])
@login_required
def deleteEntity(user):

    req_data = request.get_json()
    entity = req_data['entity']
    document_id = req_data['document_id']
    project_id = req_data['project_id']

    label = Label.query.filter_by(label=entity['nlp_cuis']).all()[0]

    annotations = Annotation.query.filter_by(user=user, document_id=document_id, project_id=project_id, label=label, start_idx=entity['start'], end_idx=entity['end']).all()

    for delann in annotations:
        db.session.delete(delann)
        db.session.commit()

    return jsonify({'success': True})


@app.route('/downloadProject', methods=['POST'])
@login_required
def downloadProject(user):
    req_data = request.get_json()
    project_id = req_data['project_id']

    annotations = Annotation.query.filter_by(project_id=project_id)
    
    export_dicts = []
    for annotation in annotations:
        print(annotation.id)
        metaanns = MetaAnnotation.query.filter_by(annotatation_id=annotation.id).all()

        if len(metaanns) > 0:
            for metaann in metaanns:
                
                mv = ast.literal_eval(metaann.metataskvalue.metataskvalue)
                
                if type(mv) == int:
                    mv = [mv]

                export = {}
 
                export['start_idx'] = mv[0]
                export['end_idx'] = mv[-1]     
                export['text'] = annotation.document.text
                export['document_id'] = annotation.document_id
                export['user_id'] = annotation.user_id
                export['username'] = annotation.user.username
                export['label_id'] = annotation.label_id
                export['label'] = annotation.label.label
                export['labelDescription'] = annotation.label.labelDescription
                export['completed'] = annotation.completed
                export['project_id'] = annotation.project_id
                export['project_name'] = annotation.project.name
                export_dicts.append(export)
        
        else:
                export = {}
                export['text'] = annotation.document.text
                export['document_id'] = annotation.document_id
                export['user_id'] = annotation.user_id
                export['username'] = annotation.user.username
                export['label_id'] = annotation.label_id
                export['label'] = annotation.label.label
                export['labelDescription'] = annotation.label.labelDescription
                export['completed'] = annotation.completed
                export['project_id'] = annotation.project_id
                export['project_name'] = annotation.project.name
                export_dicts.append(export)

    
    df_export = pd.DataFrame(export_dicts)

    response = make_response(df_export.to_csv(index=False))
    response.headers["Content-Type"] = "text/json"

    return response

@app.route('/getProjectStats', methods=['POST'])
@login_required
def getProjectStats(user):

    # This has only been written to handle mutliclass/multilalbel documents!

    req_data = request.get_json()
    project_id = req_data['project_id']    

    # Get progress of each user as dict [{'username':no_of_docs_done}...]
    # Get overlap in terms of labels
    # Get overlap in terms of spans
    project_id = req_data['project_id']

    annotations = Annotation.query.filter_by(project_id=project_id)
    
    export_dicts = []
    for annotation in annotations:
        metaanns = MetaAnnotation.query.filter_by(annotatation_id=annotation.id).all()

        if len(metaanns) > 0:
            for metaann in metaanns:
                
                mv = ast.literal_eval(metaann.metataskvalue.metataskvalue)
                
                export = {}
 
                export['start_idx'] = mv[0]
                export['end_idx'] = mv[-1]     
                export['text'] = annotation.document.text
                export['document_id'] = annotation.document_id
                export['user_id'] = annotation.user_id
                export['username'] = annotation.user.username
                export['label_id'] = annotation.label_id
                export['label'] = annotation.label.label
                export['labelDescription'] = annotation.label.labelDescription
                export['completed'] = annotation.completed
                export['project_id'] = annotation.project_id
                export['project_name'] = annotation.project.name
                export_dicts.append(export)
        
        else:
                export = {}
                export['text'] = annotation.document.text
                export['document_id'] = annotation.document_id
                export['user_id'] = annotation.user_id
                export['username'] = annotation.user.username
                export['label_id'] = annotation.label_id
                export['label'] = annotation.label.label
                export['labelDescription'] = annotation.label.labelDescription
                export['completed'] = annotation.completed
                export['project_id'] = annotation.project_id
                export['project_name'] = annotation.project.name
                export_dicts.append(export)

    
    df_export = pd.DataFrame(export_dicts)

    user_ids = list(set(df_export['user_id']))


    response = make_response(df_export.to_csv(index=False))
    response.headers["Content-Type"] = "text/json"

    return response  

## Initialise the admin panel
admin = Admin(app, name='Cogstack Annotation Tool', template_mode='bootstrap3')

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Document, db.session))
admin.add_view(ModelView(Project, db.session))
admin.add_view(ModelView(Label, db.session))
admin.add_view(ModelView(Annotation, db.session))
admin.add_view(ModelView(Dataset, db.session))
admin.add_view(ModelView(MetaAnnotation, db.session))
admin.add_view(ModelView(MetaTask, db.session))
admin.add_view(ModelView(MetaTaskValue, db.session))


# class RoleAdmin(ModelView):

#     # Prevent administration of Roles unless the currently logged-in user has the "admin" role
#     def is_accessible(self):
#         return current_user.admin


# Initialize the SQLAlchemy data store and Flask-Security.
# user_datastore = SQLAlchemyUserDatastore(db, User)
# security = Security(app, user_datastore)
# admin.add_view(RoleAdmin(User, db.session))
# admin.add_view(RoleAdmin(Document, db.session))
# admin.add_view(RoleAdmin(Project, db.session))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5001')
