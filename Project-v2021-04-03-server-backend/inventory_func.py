# Flask related
from flask import Flask, request, render_template
from flask import jsonify
from flask_pymongo import PyMongo

# Standard library
import json
import datetime as dt
from bson import json_util
import uuid

def inventory_management(input_json, coll, response_json):
	dict_temp = dict({key:val for key, val in input_json.items() if (key != 'method')})
	if input_json["method"] == "add_new":
		if list(coll.find({"inventory_id": dict_temp["inventory_id"]})):
			response_json["message"] = "item already exist, please use different inventory id"
		else:
			coll.insert_one(dict_temp)
			response_json["message"] = "item added to inventory"
	elif input_json["method"] == "remove":
		if not list(coll.find({"inventory_id": dict_temp["inventory_id"]})):
			response_json["message"] = "no such item in inventory"
		else:
			coll.delete_one(dict_temp)
			response_json["message"] = "item removed from inventory"
	elif input_json["method"] == "update_qty":
		if not list(coll.find({"inventory_id": dict_temp["inventory_id"]})):
			response_json["message"] = "no such item in inventory"
		else:
			query_temp = {"inventory_id": dict_temp["inventory_id"], "quantity": {"$gte": dict_temp["quantity"]}}
			result = coll.update_one(query_temp, {"$inc": {"quantity": -dict_temp["quantity"] }})
			if not (result.modified_count):
				response_json["message"] = "not enough item in inventory"
			else:
				response_json["message"] = "inventory quantity updated"
	elif input_json["method"] == "update_price":
		if not list(coll.find({"inventory_id": dict_temp["inventory_id"]})):
			response_json["message"] = "no such item in inventory"
		else:
			query_temp = {"inventory_id": dict_temp["inventory_id"]}
			result = coll.update_one(query_temp, {"$set": {"price_one": dict_temp["price_one"] }})
			# if not (result.modified_count):
			# 	response_json["message"] = "not enough item in inventory"
			# else:
			response_json["message"] = "inventory price updated"

	elif input_json["method"] == "set_qty":
		if not list(coll.find({"inventory_id": dict_temp["inventory_id"]})):
			response_json["message"] = "no such item in inventory"
		else:
			query_temp = {"inventory_id": dict_temp["inventory_id"]}
			result = coll.update_one(query_temp, {"$set": {"quantity": dict_temp["quantity"] }})
			# if not (result.modified_count):
			# 	response_json["message"] = "not enough item in inventory"
			# else:
			response_json["message"] = "inventory quantity updated"
	else:
		response_json["message"] = "error"
	return(response_json)


if __name__== '__main__':
	print("this is inventory management function")


