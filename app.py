from flask import Flask, render_template, jsonify, request, session, redirect, url_for
app = Flask(__name__)

import certifi
ca=certifi.where()

from pymongo import MongoClient
#client = MongoClient("mongodb+srv://sparta:test@cluster0.mcd1ews.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=ca)
#db = client.dbsparta_plus_week4
client = MongoClient("mongodb+srv://sparta:test@cluster0.vfkdbnv.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=ca)
db = client.sparta

# JWT 토큰을 만들 때 필요한 비밀문자열입니다. 아무거나 입력해도 괜찮습니다.
# 이 문자열은 서버만 알고있기 때문에, 내 서버에서만 토큰을 인코딩(=만들기)/디코딩(=풀기) 할 수 있습니다.
SECRET_KEY = 'SPARTA'

# JWT 패키지를 사용합니다. (설치해야할 패키지 이름: PyJWT)
import jwt

# 토큰에 만료시간을 줘야하기 때문에, datetime 모듈도 사용합니다.
import datetime

# 회원가입 시엔, 비밀번호를 암호화하여 DB에 저장해두는 게 좋습니다.
# 그렇지 않으면, 개발자(=나)가 회원들의 비밀번호를 볼 수 있으니까요.^^;
import hashlib

import requests
from bs4 import BeautifulSoup

@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        pw = hashlib.sha256(user_info['pw'].encode('utf-8')).hexdigest()
        return render_template('index.html', nickname=user_info["nickname"], password=pw)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route("/main", methods=["POST"])
def main_post():
    urlimage_receive = request.form['url_give']
    name_receive = request.form['name_give']
    star_receive = request.form['star_give']


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
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        nickname = user_info['nickname']
        print(nickname)
        for i in range(len(all_restaurant)):
            total_star = 0
            count = 0

            all_comment = list(db.comment.find({'num':all_restaurant[i]['num']},{'_id':False}))
        
            total_star = total_star + all_restaurant[i]['star']
            count+= 1
            
            for j in range(len(all_comment)):
                total_star = total_star + int(all_comment[j]['star'])
                count+= 1
            all_restaurant[i]['total_star'] = round(total_star/count,1)
            
        return jsonify({'result':all_restaurant, 'nickname':nickname})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/detail/<rest_id>')
def detail(rest_id):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})
        pw = hashlib.sha256(user_info['pw'].encode('utf-8')).hexdigest()
        return render_template('detail.html', nickname=user_info["nickname"], password=pw, rest_id=rest_id)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/api/comment', methods=["POST"])
def comment_post():
    token_receive = request.cookies.get('mytoken')
    comment_receive = request.form['comment_give']
    star_receive = request.form['star_give']
    num_receive = request.form['num_give']

    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    userId = payload['id']
    
    doc = {
            'comment' : comment_receive,
            'star' : int(star_receive),
            'id' : userId,
            'num' : int(num_receive)
        }
    db.comment.insert_one(doc)
    
    return jsonify({'result': 'success', 'msg': '맛있다!'})
@app.route('/modify')
def modify():      
    return render_template('modify.html')

@app.route('/modify/<Num>')
def firstmodify(Num):
    return redirect(url_for('modify', num = Num))

@app.route('/modify_user')
def modify_use():
    return render_template('modify_user.html')


@app.route("/search")
def search_page():
    return render_template("search.html")


#################################
##  로그인을 위한 API            ##
#################################

# [회원가입 API]
# id, pw, nickname을 받아서, mongoDB에 저장합니다.
# 저장하기 전에, pw를 sha256 방법(=단방향 암호화. 풀어볼 수 없음)으로 암호화해서 저장합니다.
@app.route('/api/register', methods=['POST'])
def api_register():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    nickname_receive = request.form['nickname_give']
    pw_check = request.form['pw_check']
    print(request.form)
    if pw_check != pw_receive:
       return jsonify({'result': 'fail'})
    

    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    db.user.insert_one({'id': id_receive, 'pw': pw_hash, 'nickname': nickname_receive})

    return jsonify({'result': 'success'})

# [로그인 API]
# id, pw를 받아서 맞춰보고, 토큰을 만들어 발급합니다.
@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # 회원가입 때와 같은 방법으로 pw를 암호화합니다.
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    # id, 암호화된pw을 가지고 해당 유저를 찾습니다.
    result = db.user.find_one({'id': id_receive, 'pw': pw_hash})
    # 찾으면 JWT 토큰을 만들어 발급합니다.
    if result is not None:
        # JWT 토큰에는, payload와 시크릿키가 필요합니다.
        # 시크릿키가 있어야 토큰을 디코딩(=풀기) 해서 payload 값을 볼 수 있습니다.
        # 아래에선 id와 exp를 담았습니다. 즉, JWT 토큰을 풀면 유저ID 값을 알 수 있습니다.
        # exp에는 만료시간을 넣어줍니다. 만료시간이 지나면, 시크릿키로 토큰을 풀 때 만료되었다고 에러가 납니다.
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=600)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        # token을 줍니다.
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# [유저 정보 확인 API]
# 로그인된 유저만 call 할 수 있는 API입니다.
# 유효한 토큰을 줘야 올바른 결과를 얻어갈 수 있습니다.
# (그렇지 않으면 남의 장바구니라든가, 정보를 누구나 볼 수 있겠죠?)
@app.route('/api/nick', methods=['GET'])
def api_valid():
    token_receive = request.cookies.get('mytoken')

    # try / catch 문?
    # try 아래를 실행했다가, 에러가 있으면 except 구분으로 가란 얘기입니다.

    try:
        # token을 시크릿키로 디코딩합니다.
        # 보실 수 있도록 payload를 print 해두었습니다. 우리가 로그인 시 넣은 그 payload와 같은 것이 나옵니다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        print(payload)
        # payload 안에 id가 들어있습니다. 이 id로 유저정보를 찾습니다.
        # 여기에선 그 예로 닉네임을 보내주겠습니다.
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        print(userinfo)
        return jsonify({'result': 'success', 'nickname': userinfo['nickname']})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    
@app.route('/api/detail/<restid>', methods=['GET'])
def api_detail(restid):
    id_receive = restid
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        restinfo = db.restaurant.find_one({'num':int(id_receive)}, {'_id':0})
        print(restinfo)
        mentinfo = list(db.comment.find({'num':int(id_receive)}, {'_id':0}))
        userid = userinfo['id']
        for i in range(len(mentinfo)) :
            nickname = db.user.find_one({'id':mentinfo[i]["id"]}, {'_id':0})["nickname"]
            mentinfo[i]["nickname"] = nickname
        return jsonify({'result': 'success', 'restinfo':restinfo, 'mentinfo':mentinfo, 'userinfo':userid})
    
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})


@app.route('/modify/<num>', methods=['POST'])
def food_modify(num):
    Num = num
    #Num = request.form['num']
    db.restaurant.update_one({'num' : int(Num)}, {'$set':
        {'name' : request.form['name'], 
        'region' : int(request.form['region']),
        'image' : request.form['image'],
        'star' : int(request.form['star']),
        'recommend' : request.form['recommend'],
        'comment' : request.form['comment'],}})
    return jsonify({'result' : "수정 완료"})


@app.route('/init', methods=['GET'])
def restaurant_get():
    all_restaurant = list(db.restaurant.find({},{'_id':False}))
    print("hello")
    return jsonify({'result' : all_restaurant})

@app.route('/update_user', methods=["POST"])
def update_user():
    pw = request.form['pw']
    after = request.form['after']
    token_receive = request.cookies.get('mytoken')
    print(after)
    try :
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        userinfo = db.user.find_one({'id': payload['id']}, {'_id': 0})
        print(userinfo)

        user_pw = userinfo['pw']
        pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()

        if(user_pw == pw_hash):
            db.user.update_one({'id':payload['id']},{'$set':{'nickname': after }})
            print(payload['id'])
            print(after)
            return jsonify({'result' : "변경완료되었습니다."})
        else:
            return jsonify({'result' : "비밀번호 입력이 틀렸습니다."})
        
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})
    

# [게시물 등록 API]
# 게시글을 등록하고, 토큰을 만들어 발급합니다.

@app.route('/make', methods=['POST'])
def food_save():
    token_receive = request.cookies.get('mytoken')
    food_receive = request.form['name']
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        food_list = list(db.restaurant.find({}, {'_id': False}))
        count = len(food_list) + 1
        doc = {
            'id':payload['id'],
            'num' :count,
            'name' : food_receive,
            'region' : int(request.form['region']),
            'image' : request.form['image'],
            'star' : int(request.form['star']), # 평균 내기 위해 숫자로
            'recommend' : request.form['recommend'],
            'comment' : request.form['comment'],
        }
        db.restaurant.insert_one(doc)
        return jsonify({'result' : "저장완료"})
    except jwt.ExpiredSignatureError:
        # 위를 실행했는데 만료시간이 지났으면 에러가 납니다.
        return jsonify({'result': 'fail', 'msg': '로그인 시간이 만료되었습니다.'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': 'fail', 'msg': '로그인 정보가 존재하지 않습니다.'})

@app.route('/make')
def save():
    return render_template('post.html')


# [게시물 검색 API]
# 등록된 게시글을 검색합니다.

@app.route('/search2/<keyword>', methods=["GET"])
def food_search(keyword):
    # keyword = request.form['keyword']
    matching_foods = list(db.restaurant.find({'name': {'$regex': keyword}}))
    print(keyword)
    print(matching_foods)
    # print(keyword)

    if matching_foods:
        restaurant = [{'name': food['name'], 'region': food['region'], 
                       'recommend': food['recommend'], 'comment': food['comment'], 'num':food['num']} 
                       for food in matching_foods]
    else:
        restaurant = 0
    
    return jsonify({'result':restaurant})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)