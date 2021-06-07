# Flask related
from flask import Flask, request, render_template
from flask import jsonify
from flask_pymongo import PyMongo

# Standard library
import json
import datetime as dt
from bson import json_util
import uuid

import pandas as pd
import numpy as np

def dashboard_agg(cart_coll, inv_coll, aggregation="item", date_start=(dt.datetime.utcnow()-dt.timedelta(weeks=52)), date_end=dt.datetime.utcnow()):
	
	df = list(cart_coll.find({"last_modified": {"$gte":date_start,"$lt":date_end}, "payment_status": 1},{ "customer_id": 1, "payment_status":1, "last_modified": 1, "cart": 1, "_id": 0 }))
	df = pd.DataFrame(df)

	df2 = list(inv_coll.find({},{ "inventory_id": 1, "product_name": 1, "quantity": 1, "price_one":1, "_id": 0 }))
	df2 = pd.DataFrame(df2)

	df = df.explode('cart')
	df = pd.concat([df, df['cart'].apply(pd.Series)], axis=1)

	df = df.drop("cart", axis=1).merge( df2.drop("quantity", axis=1), how="left", on=["inventory_id"])
	df["last_modified"] = pd.to_datetime(df["last_modified"])
	df["day"] = df["last_modified"].dt.strftime("%Y-%m-%d")
	df["month"] = df["last_modified"].dt.strftime("%Y-%m")
	df["year"] = df["last_modified"].dt.strftime("%Y")

	df["subtotal"] = df["quantity"]*df["price_one"].astype(np.float64)
	df["tax"] = np.round(df["subtotal"]*0.1, decimals=2)
	df["total_price"] = np.round(df["subtotal"]+df["tax"], decimals=2)

	if aggregation == "day":
		df = df.groupby(["day"]).agg(total_txn=('last_modified', 'nunique'), daily_revenue=('total_price', 'sum'),unique_customer=('customer_id', 'nunique'),total_item_sold=('quantity', 'sum'),unique_item_sold=('inventory_id', 'nunique')).reset_index()
		df["daily_revenue"] = np.round(df["daily_revenue"], decimals=2)
		df = df.sort_values(by=["day"],ascending=[False])
	elif aggregation == "month":
		df = df.groupby(["month"]).agg(total_txn=('last_modified', 'nunique'), daily_revenue=('total_price', 'sum'),unique_customer=('customer_id', 'nunique'),total_item_sold=('quantity', 'sum'),unique_item_sold=('inventory_id', 'nunique')).reset_index()
		df["daily_revenue"] = np.round(df["daily_revenue"], decimals=2)
		df = df.sort_values(by=["month"],ascending=[False])
	elif aggregation == "year":
		df = df.groupby(["year"]).agg(total_txn=('last_modified', 'nunique'), daily_revenue=('total_price', 'sum'),unique_customer=('customer_id', 'nunique'),total_item_sold=('quantity', 'sum'),unique_item_sold=('inventory_id', 'nunique')).reset_index()
		df["daily_revenue"] = np.round(df["daily_revenue"], decimals=2)
		df = df.sort_values(by=["year"],ascending=[False])
	elif aggregation == "item":
		df = df.groupby(["day","inventory_id"]).agg(total_txn=('last_modified', 'nunique'), daily_revenue=('total_price', 'sum'),unique_customer=('customer_id', 'nunique'),total_item_sold=('quantity', 'sum')).reset_index()
		df["daily_revenue"] = np.round(df["daily_revenue"], decimals=2)
	elif aggregation == "customer":
		df = df.groupby(["customer_id"]).agg(total_txn=('last_modified', 'nunique'), txn_days=('days', 'nunique'), daily_revenue=('total_price', 'sum'),total_item_sold=('quantity', 'sum'),unique_item_sold=('inventory_id', 'nunique')).reset_index()
		df["daily_revenue"] = np.round(df["daily_revenue"], decimals=2)
	else:
		df = df

	
	response_json = df.to_dict("records")

	return(response_json)


if __name__== '__main__':
	print("this is dashboard management function")
	
	import requests

	get_data = requests.get("http://18.224.8.222:5000/show_dashboard/?agg=day")

	df = pd.DataFrame(get_data.json())

	

	print(df)
	print()
	print(df.columns)

