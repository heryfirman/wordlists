from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import requests, os

app = Flask(__name__)

client = MongoClient(os.environ.get('MONGODB_URI'))
db = getattr(client, os.environ.get('DB_NAME'))

@app.route('/')
def main():
    title = "Homepage"
    word_result = db.wordlist.find({}, {'_id': False})
    words = []
    for word in word_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template("index.html", title=title, words=words, msg=msg)


@app.route('/error')
def error():
    word = request.args.get('word')
    suggestions = request.args.get('suggestions')
    status = request.args.get('status')
    
    if suggestions:
        suggestions = suggestions.split(",")    
        
    return render_template("error.html",  word=word, suggestions=suggestions, status=status)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = 'c518a916-3fa8-4763-a21c-3d4075f99955'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()
    status= request.args.get('status_give', 'new')
    
    if not definitions:
        return redirect(url_for(
            'error',
            word = keyword
        ))
    
    if type(definitions[0]) is str:
        return redirect(url_for(
            'error',
            word = keyword,
            suggestions = ",".join(definitions),
            status=status
        ))
    
    
    return render_template(
        "detail.html", 
        word=keyword, 
        definitions=definitions,
        status=status
    )

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    
    today = datetime.now()
    date = today.strftime("%Y-%m-%d")
    doc = {
        'word': word,
        'definitions': definitions,
        'date': date
    }
    db.wordlist.insert_one(doc)
    return jsonify({'result': 'success', 'msg': f'the word, {word} was saved!'})


@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.wordlist.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({'result': 'success', 'msg': f'the word, {word} was deleted!'})


@app.route('/api/get_exs', methods=["GET"])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word': word})
    examples = []
    for example in example_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id'))
        })
    
    return jsonify({'result': 'success', 'example': examples})

@app.route('/api/save_ex', methods=["POST"])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word': word,
        'example': example
    }
    
    db.examples.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'Your example, {example}, for the word {word}, was saved!'
    })

@app.route('/api/delete_ex', methods=["POST"])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg': f'Your example for the word {word}, was deleted!',
    })

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)