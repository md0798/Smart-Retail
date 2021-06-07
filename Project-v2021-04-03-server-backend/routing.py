# Flask related
from flask import Flask, request, render_template
from flask import jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS

from waitress import serve

# Standard library
import json
import datetime as dt
from bson import json_util
import uuid

#from bson import ObjectId
#import joblib


'''
class JSONEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, ObjectId):
			return(str(o))
		return(json.JSONEncoder.default(self, o))
'''

from inventory_func import inventory_management
from cart_func import cart_management
from dashboard_func import dashboard_agg

db_credentials = {
	"DB_USERNAME": "smart_retail",
	"DB_PASSWORD": "smart_retail", 
	"DB_HOST": "localhost",
	#"DB_HOST": "18.224.8.222",
	"DB_PORT": "27017",
	"DB_NAME": "iot_project"
}

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "*"}}, headers='Content-Type')
CORS(app, resources=r"/*", headers="Content-Type", supports_credentials=True)

#app.config['CORS_HEADERS'] = 'Content-Type'

app.config['MONGO_DBNAME']= db_credentials["DB_NAME"]
app.config['MONGO_URI']= "mongodb://{}:{}@{}:{}/{}".format(
	db_credentials["DB_USERNAME"],
	db_credentials["DB_PASSWORD"],
	db_credentials["DB_HOST"],
	db_credentials["DB_PORT"],
	db_credentials["DB_NAME"]
)

mongo = PyMongo(app)


@app.route('/')
def hello_world():
	response_json = {"print_message": "Hello World"}
	return(jsonify(response_json))


@app.route('/show_dashboard/', methods=['GET'])
def show_dashboard():
	coll1 = mongo.db.shopping_cart
	coll2 = mongo.db.product_inventory
	agg = request.args.get('agg')
	date_start = request.args.get('date_start')
	date_end = request.args.get('date_end')

	if agg: 
		if date_start and date_end:
			response_json = dashboard_agg(coll1, coll2, agg, dt.datetime.strptime(date_start, "%Y-%m-%d"), dt.datetime.strptime(date_end, "%Y-%m-%d"))
		else:
			response_json = dashboard_agg(coll1, coll2, agg)
	else:
		if date_start and date_end:
			response_json = dashboard_agg(coll1, coll2, date_start=dt.datetime.strptime(date_start, "%Y-%m-%d"), date_end=dt.datetime.strptime(date_end, "%Y-%m-%d"))
		else:
			response_json = dashboard_agg(coll1, coll2)
	
	return(jsonify(response_json))


@app.route('/update_cart/', methods=['POST'])
def add_to_cart():
	input_json = json.loads(str(request.json).replace("'", '"'), object_hook=json_util.object_hook)
	
	# Get current customer in front of shelf
	#input_json["customer_id"] = "Obama" #Dummy data
	if input_json["event"] != "pay_item":
		# input_json["customer_id"] = "dummy_test"
		res = mongo.db.detect_customer_visit.find_one({"time_out": ""},{ "customer_id": 1, "_id": 0 })
		if res:
			input_json["customer_id"] = res["customer_id"]
	
	# Update inventory log
	mongo.db.inventory_log.insert_one(input_json)

	## Updating Shopping Cart
	response_json = {}
	used_db = mongo.db
	response_json = cart_management(input_json, used_db, response_json)
	return(jsonify(response_json))

@app.route('/show_cart/', methods=['GET'])
def show_cart():
	coll = mongo.db.shopping_cart
	id_of_interest = request.args.get('customer_id')
	payment_status = request.args.get('payment_status')
	query_temp = {}
	if id_of_interest: 
		query_temp["customer_id"] = id_of_interest
	if payment_status: 
		query_temp["payment_status"] = int(payment_status)
	response_json = list(coll.find(query_temp,{ "customer_id": 1, "payment_status":1, "last_modified": 1, "cart": 1, "_id": 0 }))
	return(jsonify(response_json))

@app.route('/show_inv_log/', methods=['GET'])
def show_inv_log():
	coll = mongo.db.inventory_log
	query_temp = {}
	response_json = list(coll.find(query_temp,{ "customer_id": 1, "event_timestamp": 1, "event": 1, "item": 1,  "_id": 0 }))
	return(jsonify(response_json))


@app.route('/update_inventory/', methods=['POST'])
def update_inventory():
	input_json = request.json
	coll = mongo.db.product_inventory
	response_json = {}
	response_json = inventory_management(input_json, coll, response_json)
	return(jsonify(response_json))

@app.route('/show_inventory/', methods=['GET'])
def show_inventory():
	coll = mongo.db.product_inventory
	id_of_interest = request.args.get('inventory_id')
	query_temp = {}
	if id_of_interest: 
		query_temp["inventory_id"] = id_of_interest
	response_json = list(coll.find(query_temp,{ "inventory_id": 1, "product_name": 1, "quantity": 1, "price_one":1, "_id": 0 }))
	return(jsonify(response_json))


@app.route('/submit_payment/', methods=['POST'])
def submit_payment():
	input_json = request.json

	input_json["last_modified"] = dt.datetime.utcnow()

	coll = mongo.db.payment_data

	query_temp = {"customer_id": input_json["customer_id"]}
	check_existing = coll.find_one(query_temp)

	result = 0

	if not check_existing:
		result = coll.insert_one(input_json)
		response_json = {"message": "inserting customer data", "save_payment": "success"}
	else:
		result = coll.update_one(query_temp, { "$set": { "last_modified": input_json["last_modified"], "customer_name": input_json["customer_name"], "payment_data": input_json["payment_data"] } })
		response_json = {"message": "updating customer data", "save_payment": "success"}

	return(jsonify(response_json))

@app.route('/get_payment/', methods=['GET'])
def get_payment():
	coll = mongo.db.payment_data
	# curr_customer = mongo.db.detect_customer_visit.find_one({"time_out": ""},{ "customer_id": 1, "time_in": 1, "time_out": 1,  "_id": 0 })["customer_id"]
	# query_temp = {"customer_id": curr_customer}

	id_of_interest = request.args.get('customer_id')
	query_temp = {}
	if id_of_interest: 
		query_temp["customer_id"] = id_of_interest
	
	response_json = list(coll.find(query_temp,{ "customer_id": 1, "customer_name": 1, "payment_data": 1, "last_modified": 1, "_id": 0 }))
	return(jsonify(response_json))


@app.route('/detect_face/', methods=['POST'])
def detect_face():
	#input_json = request.json
	#input_json = json_util.loads(str(request.json).replace("'", '"'))
	#response_json = json.loads(str(request.json).replace("'", '"'), object_hook=json_util.object_hook)
	input_json = json.loads(str(request.json).replace("'", '"'), object_hook=json_util.object_hook)
	response_json = {}
	coll = mongo.db.detect_customer_visit
	dict_temp = dict({key:val for key, val in input_json.items() if (key != 'method')})
	if input_json["method"] == "insert":
		coll.insert_one(dict_temp)
		response_json["message"] = "customer detected"
		#response_json = {key:val for key, val in input_json.items() if (key != 'method') and (key != 'time_out')}
	elif input_json["method"] == "update":
		query_temp = {key:val for key, val in dict_temp.items() if (key != 'time_out')}
		coll.update_one(query_temp, {"$set": dict_temp})
		response_json["message"] = "no customer"
		#response_json = {key:val for key, val in input_json.items() if key != 'method'}
	else:
		response_json["message"] = "error"
	return(jsonify(response_json))

@app.route('/show_visit/', methods=['GET'])
def show_visit():
	coll = mongo.db.detect_customer_visit
	
	id_of_interest = request.args.get('current')
	query_temp = {}
	if id_of_interest:
		if int(id_of_interest):
			query_temp["time_out"] = ""
	
	response_json = list(coll.find(query_temp,{ "customer_id": 1, "time_in": 1, "time_out": 1,  "_id": 0 }))
	return(jsonify(response_json))


@app.route('/submit_face/', methods=['POST'])
def submit_face():
	input_json = request.json
	coll = mongo.db.face_encodings
	coll.insert_one(input_json)
	response_json = {"message": "new customer arrived", "save_face": "success"}
	return(jsonify(response_json))

@app.route('/get_face/', methods=['GET'])
def get_face():
	coll = mongo.db.face_encodings
	query_temp = {}
	response_json = list(coll.find(query_temp,{ "customer_id": 1, "face_encoding": 1,  "_id": 0 }))
	return(jsonify(response_json))


if __name__== '__main__':
	# serve(app, host='0.0.0.0', port=5000)
	# serve(app, host='0.0.0.0', port=5000,url_scheme='https')
	app.run(debug=True, host="0.0.0.0", port=5000)
	# app.run(debug=True)


