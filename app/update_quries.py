from mongo_initialization import MongoConnection
from bson import ObjectId
from datetime import datetime
import numpy as np

class MongoUpdates:
    def __init__(self) -> None:
        self.mongo = MongoConnection()
        self.user_collection = self.mongo.get_collection('user')
        self.article_collection = self.mongo.get_collection('articles')
        self.keywords_collection = self.mongo.get_collection('keywords')

    # internal function 
    def calcuate_user_feedback(self, articles_details, w1 = 0.35, w2 = 0.20, w3 = 0.45):
            result = []
            for article, read_time, reaction, clicked_url, length in articles_details:            

                min_time = (10 * (length / 100)) / 60
                max_time = (40 * (length / 100)) / 60
                
                if read_time < min_time:
                    f_readtime = -1
                elif read_time > max_time:
                    f_readtime = 1
                else:
                    f_readtime = 2 * ((read_time - min_time) / (max_time - min_time + 1**-7)) - 1
                
                f_reaction = reaction
                f_url_click = clicked_url

                feedback_score = (
                    w1 * f_readtime + 
                    w2 * f_reaction + 
                    w3 * f_url_click
                )

                feedback_score = max(-1, min(1, feedback_score))

                result.append({ 'article_id' :ObjectId(article), 'feedback_score': feedback_score})

            return result
    
    def update_user_history(self, articles_details, user_id):

        def update_user_embeddings(user_embeddings, article_embeddings, feedback_score, alpha = 0.1):
            user_embeddings = np.array(user_embeddings)
            for article, embedding  in article_embeddings:
                adjusted_article_embedding = np.array(embedding) * feedback_score[article]
                user_embeddings = ((1 - alpha) * user_embeddings) + (alpha * adjusted_article_embedding)
            return user_embeddings.tolist()
        
        result = self.calcuate_user_feedback(articles_details)

        feedback = {}
        for idx in result: 
            feedback[idx['article_id']] = idx['feedback_score']

        user = self.user_collection.find_one({'_id' : ObjectId(user_id)})
        articles = self.article_collection.find({'_id' : { "$in" : [idx['article_id'] for idx in result]}}, {"embedding" : 1})

        embeddings = [(article["_id"] ,article['embedding'][0]) for article in articles]
        
        history_push = [{
            'article_id' : i['article_id'],
            'feedback_score' : i['feedback_score'],
            'date' : datetime.now()
            } for i in result]
        
        self.user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$pull": {
                    "userHistory": {"$in": history_push}  # Remove items already in history_push
                }
            }
        )

        self.user_collection.update_one({
            "_id" : ObjectId(user_id)
        },{
            "$set": {
                'userVector' : update_user_embeddings(user['userVector'] ,embeddings, feedback)
            },
            "$push" : {"userHistory" : {"$each": history_push }}
        })

    def update_keyword_read_time(self, articles_details):

        for article, read_time, _, _, _ in articles_details:
            result = self.article_collection.find_one({"_id" : ObjectId(article)}, {"keywords" : 1})
            current_time = datetime.now().hour
            keywords = result['keywords']
            
            self.keywords_collection.update_many(
                {"keyword" : {"$in" : keywords}},
                {
                    "$set" : {
                        f"last_24_hours.{current_time}.date" : datetime.combine(datetime.now().date(), datetime.min.time())
                    },
                    "$inc" : {
                        f"last_24_hours.{current_time}.score" : read_time
                    }                           
                })

    def update_user_keyword_score(self, articles_details, user_id):

        feedback = self.calcuate_user_feedback(articles_details)
        articles = [idx['article_id'] for idx in feedback]
        feedback = [idx['feedback_score'] for idx in feedback]

        def getKeywords(articles = articles, feedback = feedback):
            articles = self.article_collection.find({
                '_id' : {
                    "$in": articles
                } 
            },{'_id' : 0, 'keywords' : 1})

            keywords = []
            keyword_feedback = []
            for idx, keyword in enumerate(articles):
                keywords.extend(keyword['keywords'])
                keyword_feedback.extend([feedback[idx]] * len(keyword['keywords']))

            return (keywords, keyword_feedback)
        
        def update_score(prev_score, update, alpha = 10**-3):
            new_score = prev_score + alpha * update
            normalized_score  = min(1, new_score)
            return normalized_score
        
        def update_user_hidden_keywords(user_id, keywords):
            self.user_collection.update_one(
                { "_id": ObjectId(user_id) },  # Match the user document by their userId
                [
                {
                    "$set": {
                    'hiddenPreferences': {
                        "$concatArrays": [
                        "$hiddenPreferences",  # Existing user preferences
                        {
                            "$filter": {
                            "input": keywords,
                            'as': "newKeyword",
                            "cond": {
                                "$and" : [
                                    {
                                    "$not": {
                                        "$in": [
                                        "$$newKeyword",  # Keyword to check
                                        "$hiddenPreferences.keyword"  # Existing keywords in userSelectedPreferences
                                        ]
                                    }
                                    },{
                                    "$not" : {
                                        "$in" : [
                                            "$$newKeyword",
                                            "$userSelectedPreferences.keyword"
                                        ]
                                    }
                                    }
                                ]
                            }
                            }
                        }
                        ]
                    }
                    }
                },
                {
                    "$set": {
                    'hiddenPreferences': {
                        "$map": {
                        "input": "$hiddenPreferences",
                        "as": "item",
                        "in": {
                            "$cond": {
                            "if": { 
                                "$eq": [{ "$type": "$$item" }, "object"]  # Check if it's already an object
                            },
                            "then": "$$item",  # Keep the existing object as is
                            "else": { 
                                "keyword": "$$item",  # For strings, create the object
                                "score": 0.5
                            }
                            }
                        }
                        }
                    }
                    }
                }
                ]
            )

            self.user_collection.update_one(
            { "_id": ObjectId(user_id) },  # Match the user document by their userId
            [
                {
                "$set": {
                    "hiddenPreferences": {
                    "$filter": {
                        "input": "$hiddenPreferences",  # Existing array
                        "as": "item",
                        "cond": { 
                        "$gte": ["$$item.score", 0.3]  # Filter out objects where score < 0.3
                        }
                    }
                    }
                }
                }
            ]
            )

        def update_keyword_scores(user_id, articles, feedback):
    
            article_keywords, keyword_score = getKeywords(articles, feedback)

            update_user_hidden_keywords(user_id, article_keywords)

            user = self.user_collection.find_one({"_id" : ObjectId(user_id)})
            user_keywords = user['hiddenPreferences']
            user_selected_keywords = user['userSelectedPreferences']

            updated_preferences = []
            user_selected_preference = []

            for keyword in user_keywords:
                for idx, concept in enumerate(article_keywords):
                    if keyword['keyword'] == concept:
                        updated_preferences.append({
                            'keyword' : keyword['keyword'],
                            'score' : update_score(keyword['score'], keyword_score[idx])
                        })
                        break
                else:
                    updated_preferences.append(keyword)

            for keyword in user_selected_keywords:
                for idx, concept in enumerate(article_keywords):
                    if keyword['keyword'] == concept:
                        user_selected_preference.append({
                            'keyword' : keyword['keyword'],
                            'score' : update_score(keyword['score'], keyword_score[idx])
                        })
                        break
                else:
                    user_selected_preference.append(keyword) 
                    
            updated_preferences = [obj for obj in updated_preferences if obj['score'] >= 0.3] 
            updated_preferences = sorted(updated_preferences, key = lambda x : x['score'])[:40]   

            self.user_collection.update_one(
                { "_id": ObjectId(user_id) }, 
                { "$set": { 
                "hiddenPreferences": updated_preferences,
                "userSelectedPreferences" : user_selected_preference
                    } }  
            )
            return 
        
        update_keyword_scores(user_id, articles, feedback)

    def close_connection(self):
        self.mongo.close()

# obj = MongoUpdates()
# articles_details = [
#     ('675ac0b610a4574847b8f347', 3, 1, 0, 277),
#     ('675ac0b610a4574847b8f346', 10, 1, 0, 1005)
# ]
# user = '675baa4fb49e0719e0ac4bf3'
# # obj.update_user_history(articles_details, user)
# # obj.update_keyword_read_time(articles_details)
# obj.update_user_keyword_score(articles_details, user)
