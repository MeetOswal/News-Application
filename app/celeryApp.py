# Command to Run : celery -A celeryApp worker --loglevel INFO --pool=solo
# Command to Run : celery -A celeryApp beat --loglevel INFO
from celery import Celery
from data_injection_pipeline import data_fetch_pipeline
from update_quries import MongoUpdates
from mongo_initialization import MongoConnection
from celery.schedules import crontab
from bson import ObjectId
import time
import logging

celery = Celery('tasks', broker='kafka://localhost:9092')
celery.conf.broker_connection_retry_on_startup = True
celery.config_from_object(__name__)

celery.conf.beat_schedule = {
    'run-every-5-minute' : {
        'task' : 'celeryApp.fetch_data',
        'schedule' : crontab(minute=0, hour= "*/5")
    }
}
celery.conf.timezone = 'UTC'

logger = logging.getLogger(__name__)

updater = MongoUpdates()

@celery.task
def fetch_data():
    data_fetch_pipeline()

@celery.task
def fetch_keyword_data(user_id):
    mongo = MongoConnection()
    user_collection = mongo.get_collection('user')
    pipeline = [
            { 
                '$match': { '_id': ObjectId(user_id) }
            },
            { 
                '$project': {
                    'userSelectedPreferences': {
                        '$slice': [{ '$sortArray': { 'input': '$userSelectedPreferences', 'sortBy': { 'score': -1 } } }, 10]
                    },
                    'hiddenPreferences': {
                        '$slice': [{ '$sortArray': { 'input': '$hiddenPreferences', 'sortBy': { 'score': -1 } } }, 10]
                    }
                }
            }
        ]

    result = user_collection.aggregate(pipeline)
    top_user_keyword_list = []
    for doc in result:
        top_user_keyword_list.extend([idx['keyword'] for idx in doc['userSelectedPreferences']])
        top_user_keyword_list.extend([idx['keyword'] for idx in doc['hiddenPreferences']])
    
    # data_fetch_pipeline(concepts = top_user_keyword_list)
    print("got user data")

@celery.task
def update_user_history(articles_details, user_id):
    updater.update_user_history(articles_details, user_id)

@celery.task
def update_keyword_read_time(articles_details):
    updater.update_keyword_read_time(articles_details)

@celery.task
def update_user_keyword_score(articles_details, user_id):
    updater.update_user_keyword_score(articles_details, user_id)


