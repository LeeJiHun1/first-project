from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('mongodb+srv://sparta:test@cluster0.fkv61re.mongodb.net/?retryWrites=true&w=majority')
db = client.dbsparta

import requests
from bs4 import BeautifulSoup

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/main", methods=["POST"])
def main_post():
    urlimage_receive = request.form['url_give']
    name_receive = request.form['name_give']
    star_receive = request.form['star_give']
    num_receive = request.form['num_give']
    comment_receive = request.form['comment_give']
    region_receive = request.form['region_give']
    recommend_receive = request.form['recommend_give']
    comment_receive = request.form['comment_give']

    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
    data = requests.get(urlimage_receive,headers=headers)
    soup = BeautifulSoup(data.text, 'html.parser')
    
    ogimage = soup.select_one('meta[property="og:image"]')['content']

    doc = {
        'urlimage' : ogimage,
        'name' : name_receive,
        'star' : star_receive
         }
    db.restaurant.insert_one(doc)

    return jsonify({'msg':'저장 완료!'})

@app.route("/main", methods=["GET"])
def main_get():

    all_restaurant = list(db.restaurant.find({},{'_id':False}))

    for i in range(len(all_restaurant)):
        total_star = 0
        count = 0

        all_comment = list(db.comment.find({'num':all_restaurant[i]['num']},{'_id':False}))
      
        total_star = total_star + all_restaurant[i]['star']
        count+= 1
        
        for j in range(len(all_comment)):
            total_star = total_star + all_comment[j]['star']
            count+= 1
        all_restaurant[i]['total_star'] = round(total_star/count,1)
        
    return jsonify({'result':all_restaurant})
    
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)