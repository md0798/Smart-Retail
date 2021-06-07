Smart Retail System
Smart Retail System is a practical system using cameras that leverages existing infrastructure and devices to enable cashier-free shopping.

We aim to build a system that can improve customer in-store shopping experience, but without requiring significant store re-design for the store owners, by only implementing cheap cameras. The system will also help direct labor cost savings, integrate inventory management, reduce instances of theft, and provide retailers with rich behavioral analytics.
The system needs to accurately identify and track customers,and associate each shopper with items he or she retrieves from shelves. To do this, we use cameras for facial recognition and object detection, and also develop algorithms for associating and tracking object movements with current face of customer. We use a probabilistic framework to fuse readings from object detection camera and face recognition camera in order to accurately assess which shopper picks up which item.

The video for the project can be viewwed here https://www.youtube.com/watch?v=-Rj5U5PwPYQ

Motivation

The retail industry has existed arguably since the start of human civilization and has evolved significantly throughout centuries. We can also see the digitalization of many conventional daily human activities like the use of robotic automation or financial technologies for payment. It would be no surprise that the physical retail industry would soon have a digital transformation. While electronic commerce continues to make great strides, in-store purchases are likely to continue to be important in the coming years as 91% of purchases are still made in physical stores in 2014 and 82% of millennials prefer to shop in these stores. [1,2] However, a significant pain point for in-store shopping is the checkout queue: customer satisfaction drops significantly when queuing delays exceed more than four minutes. [3] This is why we decided to create a smart retail system for small to large scale physical retail stores. We wanted to create an AI powered system which can model a fully automated grocery store with the following features:

Cashier-less payment
Face detection to detect new/existing customers
Object detection to detect the items
Dashboard analytics for the store owner

System
Smart retail system enables cashier-free shopping by creating a system that automatically determines, for every customer in a shop, what items the customer has picked from the shelves, and directly bills each customer for those items. The system is implemented using a networked system containing multiple cameras that together perform two distinct functions: identifying each customer, and identifying every item that is picked up from or put back to the shelves by the customer to determine which items the customer leaves the store with.

Architecture

To implement the features of this project, we combine:

1. Embedded Systems:
  - Raspberry Pi with Pi Camera
2. Cloud Computing:
  - Deploying Flask web server to AWS EC2
  - Setup MongoDB Database
  - Creating backend system for interaction with embedded systems
  - Deploying frontend in AWS S3
3. Analytics & Machine Learning:
  - Creating frontend dashboard for store owner by aggregating transaction data
  - Implement facial recognition algorithm and saving the face encodings to database in the cloud to detect new and existing customer
  - Implement object detection algorithm to detect which item the customer picked up or put back

Technical Components
The technical components of our system can be divided into:

Raspberry Pi Camera Streaming
The Raspberry Pi and Pi Camera was used to transfer video wirelessly for object detection. The Raspberry Pi runs a python script in order to create a HTTP server on its local IP address and transfers a video from the Pi Camera on port 8000 as stream.mjpg. The video can be accessed wirelessly by anyone, in the same network as the Raspberry Pi. The video runs at a very low frame rate so that the lag is as less as possible during object detection.

Object Detection
The object detection part of the project utilizes existing Tensorflow's Object Detection API. [4] The API has many different models and all of them have a trade-off between accuracy and speed. We had to try out many different models in order to strike that perfect balance between accuracy and speed. We found that "ssdlite_mobilenet_v2_coco" was a very good match for our project. As object detection requires a lot of computation power. Due to which the object detection lags when the frame rate was set very high. That was the reason we kept the frame rate to 2 frames per second. This also provided enough time to remove any jitters and also prevented false positives. The TensorFlow API can detect more than 20 different objects. The object detection also takes care of counting the number of items currently on the shelf. To ensure consistency, we also create several buffer frames so that any consistent changes are immediately posted on the database hosted on the cloud using a POST request.

Face Recognition
The face recognition in this project is implemented based on face recognition algorithm developed by Adam Geitgey on dlib library. [5] The flow of the face recognition is as follows:
1. Initialize known faces from database by sending GET request to Flask Web Server
2. Detect faces and recognize whose face is it by comparing to the known face. Face recognition is done by calculating distance of the face to the known face. If it is a new face, generate new customer_id and send the customer_id and face encodings to the database
3. Keep track of time when the face enter the frame and save it as time in
4. When the customer is not present in the frame for several frames, then set the current timestamp as the time out
5. Currently the system constraint is that we are able to detect 1 customer at the shelf. If there are multiple faces detected, this implies that probably the previous customer is already finished and we have new customer on the shelf, so the current customer is updated with the new frame with the time in and the previous customer is updated with the time out

Front End
This project has two main frontend aspects, one for the customer and one for the store owner. For the customer frontend, this is a single web page where the customer can input their login/registration information, update payment information, see his/her cart, and checkout (manual option). For the store owner, the website has multiple pages to check current sales performance, transaction history, and managing inventory.
All the data in this web page is fetched from the MongoDB server by communicating with the Flask Web Server. A simple HTML, CSS, and JS web page was selected to design the web page, which was then deployed in S3. A web page was selected to make it cross-platform between iOS, Android, and web browsers.

Back End
To ensure communications between each module and connection to the database, we use Amazon Web Services (AWS) with a Linux operating system EC2 Virtual Server instance as the primary medium for Cloud Computing. The implementation of the web server is using Flask Python and the database is using MongoDB.


