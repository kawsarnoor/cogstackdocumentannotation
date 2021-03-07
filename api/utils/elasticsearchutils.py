from elasticsearch import Elasticsearch

es = Elasticsearch([{'host':'localhost','port':9200}])

def searchSnomedConcept(cui):
    
    query = [{"index":'snomed_uk'},
        {"query":{"bool":
                    {"must":[{"query_string":
                                {"query": cui + '*',
                                "analyze_wildcard":True,
                                "default_field":"*"}}],
                    "filter":[],
                    "should":[],
                    "must_not":[]}}}]

    results = es.msearch(query)['responses'][0]

    return results['hits']['hits']