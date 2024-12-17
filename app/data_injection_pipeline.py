from data_source_api import APISource
from model import Model
from mongo_initialization import MongoConnection
from qdrant_initialization import QdrantConnect


def data_fetch_pipeline(concepts = None, country = "United States", maxItems = 1):

    mongo_connect = MongoConnection()
    qdrant_connect = QdrantConnect()

    articles_collection = mongo_connect.get_collection("articles")
    keywords_collection = mongo_connect.get_collection('keywords')
    print("Connection Success...")

    api = APISource()
    if concepts == None:
        _ = api.get_events() # country argument 
        _ = api.set_concepts() 
    else:
        _ = api.set_concepts(concepts) # concepts argument

    _ = api.fetch_articles() # maxItems Argument, country Arguemnt
    source = api.get_articles()

    print("data sourced...")

    llm = Model()
    llm.transform(source, articles_collection)
    llm.summarize()
    print("Summaries Generated...")
    llm.insert_to_mongo(keywords_collection, articles_collection)
    llm.insert_to_qdrant(qdrant_connect.getClient(), 'bigData_collection')
    print("Data Stored...")
    mongo_connect.close()