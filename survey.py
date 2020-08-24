from flask import Flask,request
# from flask_restful import Api,Resource,abort
from flask import jsonify
from flask_cors import CORS
from flask_cors import cross_origin
import json
from bson import json_util
from user import authenticate,identity
from flask_jwt import JWT, jwt_required, current_identity
import pymongo
from pymongo import MongoClient
client=MongoClient("mongodb+srv://analytics:analytics-password@cluster0.labxu.mongodb.net/Ipl?retryWrites=true&w=majority")

def get_client():
    return client
app=Flask(__name__)
app.config['SECRET_KEY'] = 'app@123!'
jwt=JWT(app,authenticate,identity)
# api=Api(app)
cors=CORS(app, resources={
    r"/surveydata": {"origins": "*"},
    r"/qdata":{"origins":"*"},
    r"/qdata/delete/":{"origins":"*"},
     r"/qdata/edit/":{"origins":"*"},
     r"/auth":{"origins":"*"}
    })
app.config['CORS_HEADERS'] = 'Content-Type'
Survey = get_client().SurveyData.survey
Questions=get_client().SurveyData.questions


@app.route("/surveydata",methods=['GET', 'POST'])
@cross_origin(origin='*',headers=['Content-Type'])
def post_sd():
    json_data=request.get_json()
    print(json_data)
    Survey.insert_one(json_data)
    return {"message":"data added succesfully"}

@app.route("/qdata",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def checkconnection():
    return {"message":"Connection Okay"}

@app.route("/qdata/<string:tid>",methods=['POST'])
@cross_origin(origin='*',headers=['Content-Type'])
def post_questions(tid):
    json_data=request.get_json()
    print(json_data)
    Questions.update({"topicID":tid},{"$push":{"data":json_data}})
    # Questions.insert_one(json_data)
    return {"message":"data added succesfully"}

@app.route("/qdata/<string:tid>",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def getqbytid(tid):
    pipeline=[
    {
        '$project': {
            '_id': 0
        }
    }, {
        '$match': {
            'topicID': tid
        }
    }
    ]

    docs=[doc for doc in Questions.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    return jsonify(json.loads(details))
@app.route("/qdata/edit/<string:ref>",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def giveqtoedit(ref):
    pipeline=[
    {
        '$unwind': {
            'path': '$data'
        }
    }, {
        '$match': {
            'data.ref': ref
        }
    }, {
        '$project': {
            '_id': 0
        }
    }
    ]
    docs=[doc for doc in Questions.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    return jsonify(json.loads(details))

@app.route("/qdata/edit",methods=['POST'])
@cross_origin(origin='*',headers=['Content-Type'])
def addequestion():
    json_data=request.get_json()
    print(json_data['data'])
    tid=json_data['topicID']
    ref=json_data['data']['ref']
    Questions.update_one({"topicID":tid},{"$pull":{"data":{"ref":ref}}})
    Questions.update_one({"topicID":tid},{"$push":{"data":json_data['data']}})
    Questions.update_one({"topicID":tid},{  "$push":{"data":{"$each":[],"$sort":{"ref":1}} }   })
    return {"message":"Edited q received"}

@app.route("/qdata/delete/<string:ref>",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def deleteQ(ref):  
    pipeline=[
    {
        '$unwind': {
            'path': '$data', 
            'includeArrayIndex': 'index'
        }
    }, {
        '$match': {
            'data.ref':ref
        }
    }, {
        '$project': {
            'data': 0, 
            '_id': 0
        }
    }
    ]
    docs=[doc for doc in Questions.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    details=(json.loads(details))
    tid=details[0]['topicID']
    # Questions.update({"topicID":tid},{"$unset":{matchstr:1}})
    Questions.update({"topicID":tid},{"$pull":{"data":{"ref":ref}}})
    return {"message":"connection okay"}

@app.route("/surveydata/<string:tid>/<string:ref>/<string:question>",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def getcountbyIdRef(tid, ref,question):
    count = {}
    pipeline = [
        {
            '$project': {
                '_id': 0
            }
        }, {
            '$unwind': {
                'path': '$survey'
            }
        }, {
            '$match': {
                'survey.topicid': tid
            }
        }, {
            '$unwind': {
                'path': '$survey.data'
            }
        }, {
            '$match': {
                'survey.data.ref': ref
            }
        }, {
            '$unwind': {
                'path': '$survey.data.response.mcq'
            }
        }, {
            '$match': {
                'survey.data.response.mcq.question': question, 
                'survey.data.response.mcq.answer': '0'
            }
        }, {
            '$count': 'count'
        }
    ]
    docs=[doc for doc in Survey.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    if(len(details)>2):
        count["0"] = details[11]
    else:
        count["0"] = "0"
        
    pipeline = [
        {
            '$project': {
                '_id': 0
            }
        }, {
            '$unwind': {
                'path': '$survey'
            }
        }, {
            '$match': {
                'survey.topicid': tid
            }
        }, {
            '$unwind': {
                'path': '$survey.data'
            }
        }, {
            '$match': {
                'survey.data.ref': ref
            }
        }, {
            '$unwind': {
                'path': '$survey.data.response.mcq'
            }
        }, {
            '$match': {
                'survey.data.response.mcq.question': question, 
                'survey.data.response.mcq.answer': '1'
            }
        }, {
            '$count': 'count'
        }
    ]
    docs=[doc for doc in Survey.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    if(len(details)>2):
        count["1"] = details[11]
    else:
        count["1"] = "0"

    pipeline = [
        {
            '$project': {
                '_id': 0
            }
        }, {
            '$unwind': {
                'path': '$survey'
            }
        }, {
            '$match': {
                'survey.topicid': tid
            }
        }, {
            '$unwind': {
                'path': '$survey.data'
            }
        }, {
            '$match': {
                'survey.data.ref': ref
            }
        }, {
            '$unwind': {
                'path': '$survey.data.response.mcq'
            }
        }, {
            '$match': {
                'survey.data.response.mcq.question': question, 
                'survey.data.response.mcq.answer': '2'
            }
        }, {
            '$count': 'count'
        }
    ]
    docs=[doc for doc in Survey.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    if(len(details)>2):
        count["2"] = details[11]
    else:
        count["2"] = "0"

    return jsonify(count)


@app.route("/qdataTID/<string:topicId>",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def getRefByTopicid(topicId):
    pipeline = [
        {
            '$match': {
                'topicID': topicId
            }
        }, {
            '$unwind': {
                'path': '$data'
            }
        }, {
            '$project': {
                'data.ref': 1, 
                '_id': 0
            }
        }
    ]

    docs=[doc for doc in Questions.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    return jsonify(json.loads(details))

@app.route("/qdataTID/<string:topicId>/<string:ref>",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def getQuestions(topicId,ref):
    pipeline = [
        {
            '$match': {
                'topicID': topicId
            }
        }, {
            '$unwind': {
                'path': '$data'
            }
        }, {
            '$match': {
                'data.ref': ref
            }
        }, {
            '$unwind': {
                'path': '$data.questions'
            }
        }, {
            '$project': {
                'data.questions.question': 1, 
                '_id': 0
            }
        }
    ]

    docs=[doc for doc in Questions.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    return jsonify(json.loads(details))


@app.route("/surveydata/question/<string:tid>/<string:ref>/<string:question>",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def getOptions(tid,ref,question):
    pipeline = [
        {
            '$match': {
                'topicID': tid
            }
        }, {
            '$unwind': {
                'path': '$data'
            }
        }, {
            '$match': {
                'data.ref': ref
            }
        }, {
            '$unwind': {
                'path': '$data.questions'
            }
        }, {
            '$match': {
                'data.questions.question': question
            }
        }, {
            '$unwind': {
                'path': '$data.questions.options'
            }
        }, {
            '$project': {
                'data.questions.options': 1, 
                '_id': 0
            }
        }
    ]

    docs=[doc for doc in Questions.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    return jsonify(json.loads(details))


@app.route("/qdataTID",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def getTid():
    pipeline = [
        {
            '$project': {
                'topicName': 1,
                'topicID':1, 
                '_id': 0
            }
        }
    ]
    docs=[doc for doc in Questions.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    return jsonify(json.loads(details))

@app.route("/surveydata/suggestions/<string:tid>/<string:ref>",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def getSuggestions(tid,ref):
    pipeline = [
        {
            '$unwind': {
                'path': '$survey'
            }
        }, {
            '$match': {
                'survey.topicid': tid
            }
        }, {
            '$unwind': {
                'path': '$survey.data'
            }
        }, {
            '$match': {
                'survey.data.ref': ref
            }
        }, {
            '$group': {
                '_id': 0, 
                'fieldN': {
                    '$push': '$survey.data.response.suggestion'
                }
            }
        }, {
            '$project': {
                '_id': 0
            }
        }
    ]

    docs=[doc for doc in Survey.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    return jsonify(json.loads(details))

@app.route("/surveydata/suggestions/<string:tid>/<string:ref>/<string:question>",methods=['GET'])
@cross_origin(origin='*',headers=['Content-Type'])
def getTextAnswers(tid,ref,question):
    pipeline = [
        {
            '$unwind': {
                'path': '$survey'
            }
        }, {
            '$match': {
                'survey.topicid': tid
            }
        }, {
            '$unwind': {
                'path': '$survey.data'
            }
        }, {
            '$match': {
                'survey.data.ref': ref
            }
        }, {
            '$unwind': {
                'path': '$survey.data.response.mcq'
            }
        }, {
            '$match': {
                'survey.data.response.mcq.question': question
            }
        }, {
            '$group': {
                '_id': 0, 
                'fieldN': {
                    '$push': '$survey.data.response.mcq.textanswer'
                }
            }
        }, {
            '$project': {
                '_id': 0
            }
        }
    ]

    docs=[doc for doc in Survey.aggregate(pipeline)]
    details=json.dumps(docs,default=json_util.default)
    return jsonify(json.loads(details))
@app.route('/')
def index():
    return "<h1>Welcome to our app!</h1>"
# if __name__=='__main__':
#     app.run(threaded=True,port=5000)