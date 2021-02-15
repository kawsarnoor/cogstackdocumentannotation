#### NOT BEING USED.NEED TO REFACTOR APP STUFF HERE

def changeLabelDocumentClassification(annotatedDocument, project, user, label, document):

    if project.nlptasktype == 'multiclass':
        annotatedDocument = changeLabelMulticlass(annotatedDocument, project, user, label, document)

    if project.nlptasktype == 'multilabel':
        annotatedDocument = changeLabelMultilabel(project, user, label, document)

    return annotatedDocument


## Multiclass projects can only have one label per annotated document
def changeLabelMulticlass(annotatedDocument, project, user, label, document):

    # check if annotated document exists. If it does overwrite the associated label
    if annotatedDocument:
        annotatedDocument.label = label
    else:
        annotatedDocument = AnnotatedDocument(user=user, label=label, project=project, document=document)

    return annotatedDocument

## Multilabel projects can have multiple labels per annotated document
def changeLabelMultilabel(project, user, label, document):

    annotatedDocument = AnnotatedDocument.query.filter_by(document=document,user=user,project=project,label=label).first()

    if annotatedDocument:
        annotatedDocument.label = label
    else:
        annotatedDocument = AnnotatedDocument(user=user, label=label, project=project, document=document)

    return annotatedDocument