from app import db
from app import User, Dataset, Document, Label, Project, AnnotatedDocument, projectlabel_association
import random

db.create_all()

def createUsers():
    # Create Users
    user1 = User(username='user1', password='user1')
    user2 = User(username='user2', password = 'user2')

    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()

    return [user1, user2]

def createDatasets():
    # Create Dataset
    dataset = Dataset(name='mnd_referral_letters')
    db.session.add(dataset)

    dataset2 = Dataset(name='some_other_project')
    db.session.add(dataset)

    db.session.commit()

    return [dataset, dataset2]

def createLabels():
    # Create Labels
    label_text = ['No Referral', 'Referral']
    labels_added_mnd = []
    for l in label_text:
        label = Label(label = l)
        labels_added_mnd.append(label)
        db.session.add(label)

    db.session.commit()

    label_text = ['conflicting reports', 'non-conflicting reports']
    labels_added_allergies = []
    for l in label_text:
        label = Label(label = l)
        labels_added_allergies.append(label)
        db.session.add(label)

    db.session.commit()

    return [labels_added_mnd, labels_added_allergies]


def createProjects(mnd_dataset, allergies_dataset, labels_added_mnd, labels_added_allergies, user1, user2):

    mnd_desc = 'annotating gp referral letters to identify patients that might need to be fast tracked to the MND clinic '
    project = Project(name = 'mnd', dataset=mnd_dataset, description=mnd_desc, labels=labels_added_mnd, users=[user1,user2])
    db.session.add(project)

    allergies_desc =  'allergies project doing some annotation'
    project2 = Project(name = 'allergies project', dataset=allergies_dataset, description=allergies_desc, labels=labels_added_allergies, users =[user2])
    db.session.add(project2)   

    db.session.commit()

    #   Associate Labels with Project
    db.session.execute(projectlabel_association.insert().values([(project.id, labels_added_mnd[0].id), (project.id, labels_added_mnd[1].id)]))



def createDocuments(mnd_dataset, allergies_dataset):

    # Create Documents
    mnd_document_texts = [' '.join(['I am an mnd document',str(i+1)]) for i in range(300)]
    mnd_documents = []
    for dt in mnd_document_texts:
        document = Document(text=dt, dataset=mnd_dataset)
        mnd_documents.append(document)
        db.session.add(document)
    
    allergies_document_texts = [' '.join(['I am an allergies document',str(i+1)]) for i in range(300)]
    allergies_documents = []
    for dt in allergies_document_texts:
        document = Document(text=dt, dataset=allergies_dataset)
        allergies_documents.append(document)
        db.session.add(document)

    db.session.commit()


users = createUsers()
print('users done')
datasets = createDatasets()
print('datasets done')
labels = createLabels()
print('labels done')
createProjects(datasets[0], datasets[1], labels[0], labels[1], users[0], users[1])
print('projects done')
createDocuments(datasets[0], datasets[1])
print('documents done')


# # Create Annotated Documents
# annotated_documents = []

# for d in documents[0:5]:
#     label_choice_user1 = random.choice([0,1])
#     annotated_documents.append(AnnotatedDocument(user = user1, label = labels_added[label_choice_user1], document = d, project=project))

#     label_choice_user2 = random.choice([0,1])
#     annotated_documents.append(AnnotatedDocument(user = user2, label = labels_added[label_choice_user2], document = d, project=project))

# annotated_documents.append(AnnotatedDocument(user = user1, label = labels[0], document = documents[0], project=project))
# annotated_documents.append(AnnotatedDocument(user = user1, label = labels[1], document = documents[1], project=project))
# annotated_documents.append(AnnotatedDocument(user = user1, label = labels[1], document = documents[2], project=project))

# # annotated_documents.append(AnnotatedDocument(user = user2, label = labels[0], document = documents[0], project=project))

# for ad in annotated_documents:
#     db.session.add(ad)

# db.session.commit()

