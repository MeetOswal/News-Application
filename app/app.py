from flask import Flask, request, jsonify
from recommendation_pipeline import get_recommendation
from update_quries import MongoUpdates
from kafka import KafkaProducer
from celeryApp import fetch_keyword_data, update_user_history, update_user_keyword_score, update_keyword_read_time
import json

app = Flask(__name__)

producer = KafkaProducer(
    bootstrap_servers = ['localhost:9092'],
    value_serializer = lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/recommendations/<user_id>', methods = ['GET'])
def generate_recommendations(user_id):
    user_id =  '675b80f0b49e0719e0ac4be5'
    prev_rec = request.args.get('prev_rec') if request.args.get('prev_rec') else 0

    recommendations, rec =  get_recommendation(user_id, prev_rec)
    if rec < 0:
        fetch_keyword_data.apply_async(args=[user_id])
        rec = 0

    recommendations = [i for i in recommendations]

    return jsonify({
        "page" : rec,
        "recommendations": recommendations
        }), 200

@app.route('/fetch-data/<keyword>', methods=['GET'])
def fetch_data_for_keyword(keyword):
    task = fetch_keyword_data.apply_async([keyword])
    print(f"Processing feedback:")
    return jsonify({"task_id": task.id, "status": "Task submitted successfully"})

@app.route('update-user-activity/<user_id>', methods = ['POST'])
def update_user_activity(user_id):
    update_user_history.apply_async(request.form.get('activity'), user_id)
    update_user_keyword_score.apply_async(request.form.get('activity'), user_id)
    update_keyword_read_time.apply_async(request.form.get('activity'))

if __name__ == "__main__":
    app.run(debug = True)