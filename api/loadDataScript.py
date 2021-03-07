import pandas as pd
from app import db
from app import User, Dataset, Document, Label, Project, projectlabel_association

## Load data in texts
data_path = '~/Desktop/annotationTexts.csv'  # Expect a csv with columns id,text
df = pd.read_csv(data_path)
texts = list(df['text'])

db.create_all()


def createUsers():
    # Create Users
    admin = User(username='admin', password='admin', admin=True)
    user1 = User(username='user1', password='user1')
    user2 = User(username='user2', password = 'user2')
    
    db.session.add(admin)
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()

    return [user1, user2]

def createDatasets():
    # Create Dataset
    dataset = Dataset(name='mnd_referral_letters')
    db.session.add(dataset)

    db.session.commit()

    return dataset

def createLabels():
    # Create Labels
    label_text = ['Referral']
    label_description = ['']
    label_type = ['sentence']
    labels_added_mnd = []
    for i, l in enumerate(label_text):
        label = Label(label = l, labelDescription = label_description[i], labelType = label_type[i])
        labels_added_mnd.append(label)
        db.session.add(label)

    db.session.commit()

    return labels_added_mnd


def createProjects(mnd_dataset, labels_added_mnd, user1, user2):

    mnd_desc = 'annotating gp referral letters to identify patients that might need to be fast tracked to the MND clinic '
    project = Project(name = 'mnd', nlptasktype = 'multiclass', dataset=mnd_dataset, description=mnd_desc, labels=labels_added_mnd, users=[user1,user2])
    db.session.add(project)

    db.session.commit()

    #   Associate Labels with Project
    db.session.execute(projectlabel_association.insert().values([(project.id, labels_added_mnd[0].id)]))


def createDocuments(mnd_dataset, texts):

    # Create Documents
    mnd_document_texts = texts
    mnd_documents = []
    for dt in mnd_document_texts[0:5]:
        document = Document(text=dt, dataset=mnd_dataset)
        mnd_documents.append(document)
        db.session.add(document)
    
    db.session.commit()


users = createUsers()
print('users done')
dataset = createDatasets()
print('datasets done')
labels = createLabels()
print('labels done')
createProjects(dataset, labels, users[0], users[1])
print('projects done')

createDocuments(dataset, texts)
print('documents done')

