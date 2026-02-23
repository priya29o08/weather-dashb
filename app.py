from flask import Flask,jsonify,request
from flask_cors import CORS
import requests
import sqlite3
from datetime import datetime




app = Flask(__name__)
CORS(app)

API_KEY = 'e8db29a082f5ec8a40693c0d21485c93'
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

#database setup

def init_db():
    conn=sqlite3.connect('weather.db')
    cursor=conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS favorites(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   city TEXT NOT NULL UNIQUE,
                   added_at TEXT
                   )
                   ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return jsonify({"message":"Weather dashboard api","status":"running"})

#get weather for a city

@app.route('/weather/<city>', methods=['GET'])
def get_weather(city):
    try:
        #calling weather api
        params={
            'q': city,
            'appid' : API_KEY,
            'units': 'metric' #celcius

        }  

        response = requests.get(BASE_URL,params=params)
        data=response.json()

        if response.status_code !=200:
            return jsonify({"error":"city not found"}),404
        
        weather_data = {
            "city": data['name'],
            "country": data['sys']['country'],
            "temp": round(data['main']['temp']),
            "feels_like": round(data['main']['feels_like']),
            "description": data['weather'][0]['description'],
            "icon": data['weather'][0]['icon'],
            "humidity": data['main']['humidity'],
            "wind_speed": data['wind']['speed']
        }
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({"error": str(e)}),500
    

#get all fav

@app.route('/favorites', methods=['GET'])
def get_favorites():
    conn=sqlite3.connect('weather.db')
    conn.row_factory=sqlite3.Row
    cursor=conn.cursor()
    cursor.execute('SELECT * FROM favorites ORDER BY added_at DESC')
    favorites=[dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"favorites":favorites})

#add favorite
@app.route('/favorites', methods=['POST'])
def add_fav():
    data = request.json
    city=data.get('city')

    if not city:
        return jsonify({"error":"city not found"}),400
    
    try:
        conn=sqlite3.connect('weather.db')
        cursor=conn.cursor()
        cursor.execute('''
            INSERT INTO favorites(city,added_at)VALUES (?,?)
                       ''',(city,datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({"message":"favorite added"})
    
    except sqlite3.integrityerror:
        return jsonify({"error":"City already in favorites"}),400
    

    #delete fav
@app.route('/favorites/<int:id>',methods = ['DELETE'])
def delete_fav(id):
    conn=sqlite3.connect('weather.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorites WHERE id =?',(id,))
    conn.commit()

    if cursor.rowcount==0:
        conn.close()
        return jsonify({"error":"Fav not found"})
    conn.close()
    return jsonify({"message":"Favorite deleted"})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0',port=port,debug = True)