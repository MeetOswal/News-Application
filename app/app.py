from flask import Flask, request, jsonify, session
from recommendation_pipeline import get_recommendation
from mongo_initialization import MongoConnection
from kafka import KafkaProducer
from celeryApp import fetch_keyword_data, update_user_history, update_user_keyword_score, update_keyword_read_time
import re
import json
import bcrypt
from datetime import datetime, timedelta
from bson import ObjectId
import numpy as np
from model import Model
from qdrant_initialization import QdrantConnect
from flask_cors import CORS


app = Flask(__name__)

CORS(app, supports_credentials=True)

app.config.update(
    SESSION_COOKIE_SECURE=True,  
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_PATH = "/"
    )

app.secret_key = "1234"

producer = KafkaProducer(
    bootstrap_servers = ['localhost:9092'],
    value_serializer = lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/recommendations/', methods = ['GET'])
def generate_recommendations():
    if 'user_id' in session:
        user_id = session['user_id']
        user_id =  '675b80f0b49e0719e0ac4be5'
        prev_rec = int(request.args.get('prev_rec')) if request.args.get('prev_rec') else 0

        recommendations, rec =  get_recommendation(user_id, prev_rec)
        if rec < 0:
            fetch_keyword_data.apply_async(args=[user_id])
            rec = 0

        recommendations = [i for i in recommendations]
        for idx in range(len(recommendations)):
            recommendations[idx]['_id'] = str(recommendations[idx]['_id'])
        return jsonify({
            "loggedIn" : True,
            "page" : rec,
            "recommendations": recommendations
            }), 200
    else:
        prev_rec = int(request.args.get('prev_rec')) if request.args.get('prev_rec') else 0
        mongo = MongoConnection()
        collection = mongo.get_collection('articles')
        articles = collection.find({}, {"summary" : 1, "title" : 1, "url" : 1}).sort({ 'date': -1 }).skip(prev_rec * 10).limit(10 + (prev_rec * 10))
        recommendations = [i for i in articles]
        for idx in range(len(recommendations)):
            recommendations[idx]['_id'] = str(recommendations[idx]['_id'])
        return jsonify({
            "LoggedIn" : False,
            "page" : prev_rec + 1,
            "recommendations": recommendations,
            }), 200
        

@app.route('/login', methods = ['POST'])
def user_login():
    mongo = MongoConnection()
    user_collection = mongo.get_collection('user')
    email = request.form.get('email')
    password = request.form.get('password')
    user = user_collection.find_one({"email" : email})
    mongo.close()
    if not user:
        return jsonify({"error" : "Email / Password is incorrect"}), 404
    elif  1==1 :# bcrypt.checkpw(password.encode('utf-8'), user['password']) :
        session['user_id'] = str(user['_id'])
        return jsonify({'message' : 'Login Successful'}), 200
    else:
        return jsonify({"error" : "Email / Password is incorrect"}), 404
    
    
@app.route('/register', methods = ['POST'])
def user_registration():

    mongo = MongoConnection()
    user_collection = mongo.get_collection('user')

    email = request.form.get('email')
    password = bcrypt.hashpw(request.form.get('password').encode('utf-8'), bcrypt.gensalt())
    username = request.form.get('name')
    preferences = request.form.get('preferences')
    preference_object = [{'keyword' : pref, "score" : 0.5} for pref in preferences.split(",")]
    email_regex = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return jsonify({"error": "Invalid email format"}), 400

    if user_collection.find_one({"email": email}):
        return jsonify({"error": "Username is already taken"}), 400

    new_user = {
        "userName": username,
        "email": email,
        "password": password,
        "userSelectedPreferences" : preference_object,
        "hiddenPreferences": [],
        "userHistory" : [],
        "userVector" : [list(np.random.uniform(-1, 1, 1024))]
    }
    user_collection.insert_one(new_user)
    mongo.close()
    return jsonify({"message": "Registration successful"}), 201

@app.route("/logout", methods = ['GET'])
def logout():
    if 'user_id' in session:
        session.pop('user_id')
        return jsonify({"message" : "Logged out"}), 200
    else:
        return jsonify({"error" : "Not Logged In"}), 404

@app.route("/update-preferences", methods = ['POST'])
def update_preferences():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    mongo = MongoConnection()
    user_collection = mongo.get_collection('user')

    preferences = request.form.get('preferences')
    preference_object = [{'keyword' : pref, "score" : 0.5} for pref in preferences.split(",")]


    user_collection.update_one(
        {'_id': ObjectId(session['user_id'])},
        {
           "$addToSet": {
            "userSelectedPreferences": {"$each": preference_object}
        }
        }
    )
    mongo.close()
    return jsonify({'message' : "Preference updated"}), 200

@app.route("/search-keyword", methods = ['GET'])
def search_keywords():
    def find_similar_keywords(input_string, keyword_collection):
        pipeline = [
            {
                "$search": {
                    "index": "keywordSearch", 
                    "text": {
                        "query": input_string,
                        "path": "keyword",
                        "fuzzy": {
                            "maxEdits": 2
                        }
                    }
                }
            },
            {
                "$limit": 10 
            },
            {
                "$project": {
                    "_id": 0,  # Exclude the MongoDB ID
                    "keyword": 1 
                }
            }
        ]
        results = list(keyword_collection.aggregate(pipeline))
        return [result['keyword'] for result in results]
    
    mongo = MongoConnection()
    keyword_collection = mongo.get_collection('keywords')
    user_query = request.args.get('query')
    similar_keywords = find_similar_keywords(user_query, keyword_collection)
    mongo.close()
    return jsonify({"message" : similar_keywords}), 200

@app.route("/popular-keywords", methods = ['GET'])
def get_popular_keywords():
    mongo = MongoConnection()
    keyword_collection = mongo.get_collection('keywords')
    yesterday = datetime.combine(datetime.now().date(), datetime.min.time()) - timedelta(days=10)
    pipeline = [
            {"$unwind": "$last_24_hours"},
            {"$match": {
                "last_24_hours.date": {"$gte": yesterday}
            }},
            {"$group": {
                "_id": "$keyword",
                "total_score": {"$sum": "$last_24_hours.score"}
            }},
            {"$sort": {"total_score": -1}},
            {"$limit": 10}
        ]
    
    recommendation_keywords = keyword_collection.aggregate(pipeline)
    recommendation_keywords = [keyword['_id'] for keyword in recommendation_keywords]
    mongo.close()
    return jsonify({"message" : recommendation_keywords}), 200

@app.route('/update-user-activity', methods = ['POST'])
def update_user_activity():
    if "user_id" in session:
        user_id = session['user_id']
        array_of_objects = eval(request.form.get('activity'))
        result = []
        for object in array_of_objects:
            x = [object['article'], object['readTime'], object['reaction'], object['clickedUrl'], object['length']]
            result.append(tuple(x))

        update_user_history.apply_async(args=[result, user_id])
        update_user_keyword_score.apply_async(args=[result, user_id])
        update_keyword_read_time.apply_async(args = [result])
    return jsonify({"message" : "OK"}), 200

@app.route("/search", methods=['GET'])
def search():
    mongo = MongoConnection()
    model = Model()
    collection = mongo.get_collection('articles')
    client = QdrantConnect()
    
    try:
        # Get the query from the request
        query = request.args.get('query')
        
        # Perform the search and get the response
        response = model.search(client.getClient(), collection, query)
        
        mongo.close()  # Close MongoDB connection
        return jsonify({"response": response}), 200
    
    except Exception as e:
        mongo.close()  # Ensure MongoDB connection is closed in case of errors
        return jsonify({"error": str(e)}), 500





if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000, debug = True)
    app.run(port=5000, debug = True)