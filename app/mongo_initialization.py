from pymongo import MongoClient

class MongoConnection:
    def __init__(self):
        connection_string = "mongodb+srv://meetoswal:2912@cluster0.i9o30.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        self.client = MongoClient(connection_string)
        self.db = self.client['bigData']
        self.collection = None

    def get_collection(self, collection = "articles"): # 'user', 'keywords'
        self.collection = self.db[collection]
        return self.collection
    
    def close(self):
        self.client.close()
    
# connect = MongoConnection()
# user = connect.get_collection("articles")

