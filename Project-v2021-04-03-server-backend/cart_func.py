# Flask related
from flask import Flask, request, render_template
from flask import jsonify
from flask_pymongo import PyMongo

# Standard library
import json
import datetime as dt
from bson import json_util
import uuid

from inventory_func import inventory_management

def cart_management(input_json, used_db, response_json):
	dict_temp = dict({key:val for key, val in input_json.items() if (key != '_id') & (key != 'event')})
	dict_temp["last_modified"] = dict_temp.pop("event_timestamp")
	dict_temp["payment_status"] = 0
	
	coll = used_db["shopping_cart"]

	query_temp = {"customer_id": dict_temp["customer_id"], "payment_status": dict_temp["payment_status"] }
	
	# Check current customer's cart
	check_existing = coll.find_one(query_temp)

	if input_json["event"] == "get_item":

		dict_temp["cart"] = [dict_temp.pop("item")]

		result = 0

		if not check_existing:
			# Add new cart when customer is not flagged yet
			result = coll.insert_one(dict_temp)
		else: # Existing cart
			# Loop cart item
			for i in dict_temp["cart"]:
				for j in check_existing["cart"]:
					# If existing item is found, add quantity
					if (i["inventory_id"] == j["inventory_id"]):
						query_temp["cart.inventory_id"] = i["inventory_id"]
						result = coll.update_one(query_temp, { "$set": { "last_modified": dict_temp["last_modified"]}, "$inc": {"cart.$.quantity": i["quantity"]} })
			if not (result):
				# if no existing item, add item to cart
				result = coll.update_one(query_temp, { "$set": { "last_modified": dict_temp["last_modified"]}, "$push": {"cart": i} })

		if (result):
			response_json["message"] = "item added to cart"
		else:
			response_json["message"] = "error"

	elif input_json["event"] == "put_back":

		dict_temp["cart"] = [dict_temp.pop("item")]
		
		result = 0

		if not check_existing:
			response_json["message"] = "cart error/do not exist"
		else:
			# Loop cart item
			for i in dict_temp["cart"]:
				for j in check_existing["cart"]:
					# If existing item is found, reduce quantity
					if (i["inventory_id"] == j["inventory_id"]):
						# Check if there is enough item on cart
						if (j["quantity"]) > (i["quantity"]):
							query_temp["cart.inventory_id"] = i["inventory_id"]
							result = coll.update_one(query_temp, { "$set": { "last_modified": dict_temp["last_modified"]}, "$inc": {"cart.$.quantity": -i["quantity"]} })
							response_json["message"] = "item quantity reduced from cart"
						elif (j["quantity"]) == (i["quantity"]):
							result = coll.update_one(query_temp, { "$set": { "last_modified": dict_temp["last_modified"]}, "$pull": {"cart": {"inventory_id": i["inventory_id"]} } })
							response_json["message"] = "item removed from cart"
						else:
							response_json["message"] = "not enough item in inventory"
			if not (result):
				# if no existing item, error message
				response_json["message"] = "no such item in cart"
		

	elif input_json["event"] == "pay_item":

		result = 0

		if not check_existing:
			response_json["message"] = "cart error/do not exist"
		else:
			# Loop cart item to be removed from inventory
			for i in check_existing["cart"]:
				inv_payload = i
				inv_payload["method"] = "update_qty"
				coll2 = used_db.product_inventory
				response_json = {}
				response_json = inventory_management(inv_payload, coll2, response_json)
			#query_temp = {key:val for key, val in dict_temp.items() if (key != 'time_out')}
			#coll.update_one(query_temp, {"$set": dict_temp})
			result = coll.update_one(query_temp, { "$set": { "last_modified": dt.datetime(dict_temp["last_modified"]), "payment_status": 1}})
			response_json["payment"] = "item paid, inventory updated"

	else:
		response_json["message"] = "error"

	return(response_json)


if __name__== '__main__':
	print("this is cart management function")


