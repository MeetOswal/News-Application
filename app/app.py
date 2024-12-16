from flask import Flask, request, jsonify
from recommendation_pipeline import get_recommendation
from kafka import KafkaProducer
from celery import Celery
import json

app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

producer = KafkaProducer(
    bootstrap_servers = ['localhost:9092'],
    value_serializer = lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/recommendations', methods = ['GET'])
def generate_recommendations():
    user_id = request.args.get('user_id')
    user_id =  '675b80f0b49e0719e0ac4be5'
    recommendations =  get_recommendation(user_id)
    recommendations = [str(i[0]) for i in recommendations]

    return jsonify({"recommendations": recommendations}), 200

@celery.task
def process_feedback(feedback_data):
    # Simulate processing feedback
    print(f"Processing feedback: {feedback_data}")
    
if __name__ == "__main__":
    app.run(debug = True)