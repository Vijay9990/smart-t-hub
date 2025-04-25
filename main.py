import os
import base64
import random
from datetime import datetime
from flask import Flask, render_template, request, session, redirect
from pymongo import MongoClient
from bson import ObjectId
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from Google import Create_Service  # Make sure you have this module set up correctly

# ===== Flask App Setup =====
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'ride_sharing'

# ===== MongoDB Setup (Cloud-Ready for Render) =====
mongo_uri = os.environ.get("MONGO_URI")  # Add this in your Render environment variables
client = MongoClient("mongodb+srv://vijaykoppula:vijaykoppula@cluster0.boazmhb.mongodb.net/ride-booking?retryWrites=true&w=majority&appName=Cluster0")
db = client["ride-booking"]   # ✅ Your actual database name

# ===== Collection Shortcuts =====
rider_collection = db['rider']
driver_collection = db['driver']
location_collection = db['location']
rides_collection = db['rides']
booking_collection = db['booking']
payment_collection = db['payment']
review_collection = db['review']

# ===== Static Folder Paths =====
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT_VEHICLE = os.path.join(APP_ROOT, "static/vehicle")
APP_ROOT_PASSENGER = os.path.join(APP_ROOT, "static/passenger")

# ===== Gmail API Email Function =====
def send_email(subject, message, to):
    CLIENT_SECRET_FILE = 'credentials.json'  # Must be present on the Render server
    API_NAME = 'gmail'
    API_VERSION = 'v1'
    SCOPES = ['https://mail.google.com/']

    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

    mimeMessage = MIMEMultipart()
    mimeMessage['to'] = to
    mimeMessage['subject'] = subject
    mimeMessage.attach(MIMEText(message, 'plain'))

    raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw_string}).execute()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/admin_login")
def admin_Login():
    return render_template("admin_login.html")


@app.route("/admin_login_action", methods=['post'])
def admin_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    if email == "admin@gmail.com" and password == "admin":
        session["role"] = "admin"
        return redirect("admin_home")
    return render_template("message.html", message="invalid login credentials")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")


@app.route("/rider_registration")
def rider_registration():
    return render_template("rider_registration.html")


@app.route("/rider_registration_action", methods=['post'])
def rider_registration_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    state = request.form.get("state")
    city = request.form.get("city")
    zip_code = request.form.get("zip_code")
    rider = rider_collection.count_documents({"email": email})
    if rider:
        return render_template("message.html", message="this email is already exist")
    rider = rider_collection.count_documents({"phone": phone})
    if rider:
        return render_template("message.html", message="this  phone number  is already exist")
    new_rider = {"first_name": first_name, "last_name": last_name, "email": email, "phone": phone, "password": password,
                 "state": state, "city": city, "zip_code": zip_code}
    rider_collection.insert_one(new_rider)
    return render_template("message.html", message="Data Inserted Successfully")


@app.route("/rider_login")
def rider_login():
    return render_template("rider_login.html")


@app.route("/rider_login_action", methods=['post'])
def rider_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    rider = rider_collection.find_one({"email": email, "password": password})
    if rider:
        session['rider_id'] = str(rider["_id"])
        session['role'] = 'rider'
        return redirect("rider_home")
    else:
        return render_template("message.html", message="invalid login credentials")


@app.route("/rider_home")
def rider_home():
    return render_template("rider_home.html")


@app.route("/driver_registration")
def driver_registration():
    return render_template("driver_registration.html")


from werkzeug.security import generate_password_hash

@app.route("/driver_registration_action", methods=['POST'])
def driver_registration_action():
    # Get the form data
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")
    state = request.form.get("state")
    city = request.form.get("city")
    zip_code = request.form.get("zip_code")
    image = request.files.get("driver_image")
    
    # Check if the image is provided
    if not image:
        return render_template("message.html", message="Please upload an image")

    # Define the file saving path (make sure APP_ROOT_VEHICLE is defined properly)
    path = os.path.join(APP_ROOT_VEHICLE, image.filename)
    
    # Save the image
    image.save(path)

    # Get additional vehicle details
    car_number = request.form.get("car_number")
    vehicle_make = request.form.get("vehicle_make")
    model = request.form.get("model")
    year = request.form.get("year")
    driver_license_number = request.form.get("driver_license_number")

    # Check if email or phone already exists
    if driver_collection.count_documents({"email": email}) > 0:
        return render_template("message.html", message="This email is already registered.")
    
    if driver_collection.count_documents({"phone": phone}) > 0:
        return render_template("message.html", message="This phone number is already registered.")

    # Hash the password before saving
    hashed_password = generate_password_hash(password)

    # Prepare the new driver data
    new_driver = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "image": image.filename,
        "password": hashed_password,
        "state": state,
        "city": city,
        "zip_code": zip_code,
        "car_number": car_number,
        "vehicle_make": vehicle_make,
        "model": model,
        "year": year,
        "driver_license_number": driver_license_number,
        "status": "UnAuthorized"
    }

    # Insert the new driver into the database
    driver_collection.insert_one(new_driver)

    return render_template("message.html", message="Driver registered successfully!")



@app.route("/driver_login")
def driver_login():
    return render_template("driver_login.html")


@app.route('/driver_login_action', methods=['POST'])
def driver_login_action():
    email = request.form.get("email")
    password = request.form.get("password")

    driver = driver_collection.find_one({"email": email})
    if driver:
        import bcrypt
        if bcrypt.checkpw(password.encode('utf-8'), driver["password"].encode('utf-8')):
            if driver["status"] == "UnAuthorized":
                return render_template("message.html", message="Your Account Not Verified")
            else:
                session['driver_id'] = str(driver["_id"])
                session['role'] = 'driver'
                return redirect("/driver_home")
        else:
            return render_template("message.html", message="Invalid Password")
    else:
        return render_template("message.html", message="Driver Not Found")


@app.route("/driver_home")
def driver_home():
    return render_template("driver_home.html")


@app.route("/logout")
def logout():
    session.clear()
    return render_template("home.html")


@app.route("/add_locations")
def add_locations():
    locations = location_collection.find({})
    locations = list(locations)
    return render_template("locations.html", locations=locations)


@app.route("/locations_action", methods=['post'])
def locations_action():
    location_name = request.form.get("location_name")
    query = {"$or": [{"location_name": location_name}]}
    count = location_collection.count_documents(query)
    if count == 0:
        query = {"location_name": location_name}
        location_collection.insert_one(query)
        return redirect("/add_locations")
    else:
        return render_template("message_action.html", message="This Location Details Already Existed")


@app.route("/view_driver")
def view_drivers():
    drivers = driver_collection.find()
    drivers = list(drivers)
    return render_template("view_drivers.html", drivers=drivers)


@app.route("/active_driver")
def authorized_action():
    driver_id = request.args.get("driver_id")
    query1 = {"_id": ObjectId(driver_id)}
    query2 = {"$set": {"status": "Authorized"}}
    driver_collection.update_one(query1, query2)
    return redirect("/view_driver")


@app.route("/deactivate_driver")
def deactivate_driver():
    driver_id = request.args.get("driver_id")
    result = driver_collection.update_one(
        {"_id": ObjectId(driver_id)},
        {"$set": {"status": "UnAuthorized"}}
    )
    return redirect("/view_driver")


@app.route("/post_ride")
def post_ride():
    locations = location_collection.find()
    locations = list(locations)
    driver_id = session['driver_id']
    query = {"driver_id": ObjectId(driver_id)}
    rides = rides_collection.find(query)
    rides = list(rides)
    rides.reverse()
    return render_template("post_ride.html", locations=locations, rides=rides,
                           get_location_by_location_id=get_location_by_location_id)


@app.route("/post_ride_action", methods=['post'])
def post_ride_action():
    ride_type = request.form.get("ride_type")
    ride_start_location_id = request.form.get("ride_start_location_id")
    ride_end_location_id = request.form.get("ride_end_location_id")
    start_date_time = request.form.get("start_date_time")
    start_date_time = datetime.strptime(start_date_time, '%Y-%m-%dT%H:%M')
    end_date_time = request.form.get("end_date_time")
    end_date_time = datetime.strptime(end_date_time, '%Y-%m-%dT%H:%M')
    price = request.form.get("price")
    capacity = request.form.get("capacity")
    driver_id = session['driver_id']
    ride_date = start_date_time.strftime("%Y-%m-%d")
    ride_date = datetime.strptime(ride_date, "%Y-%m-%d")
    new_ride = {"ride_start_location_id": ObjectId(ride_start_location_id),
                "ride_end_location_id": ObjectId(ride_end_location_id), "start_date_time": start_date_time,
                "end_date_time": end_date_time, "price": price, "capacity": capacity, "driver_id": ObjectId(driver_id),
                "ride_date": ride_date,"ride_type":ride_type}
    rides_collection.insert_one(new_ride)
    return render_template("message_action.html", message="Data inserted successfully")


def get_location_by_location_id(location_id):
    query = {"_id": location_id}
    location = location_collection.find_one(query)
    return location


@app.route("/search_rides")
def search_rides():
    source_location_id = request.args.get("source_location_id")
    destination_location_id = request.args.get("destination_location_id")
    ride_type = request.args.get("ride_type")
    ride_date = request.args.get("ride_date")
    if source_location_id == None:
        source_location_id = ""
    if destination_location_id == None:
        destination_location_id = ""
    if ride_type==None:
        ride_type = ""
    if ride_date == None:
        ride_date2 = datetime.now()
        ride_date = ride_date2.strftime("%Y-%m-%d")
    else:
        ride_date2 = datetime.strptime(ride_date, '%Y-%m-%d')
    query = {"abc": "abc"}
    rides = []
    if source_location_id != "" and destination_location_id != "" and ride_type!="":
        query = {"ride_start_location_id": ObjectId(source_location_id),
                 "ride_end_location_id": ObjectId(destination_location_id), "ride_date": ride_date2,"ride_type":ride_type}
    rides = rides_collection.find(query)
    rides = list(rides)
    locations = location_collection.find()
    locations = list(locations)
    return render_template("search_rides.html", locations=locations, rides=rides, source_location_id=source_location_id,
                           destination_location_id=destination_location_id, ride_date=ride_date, str=str,
                           get_location_by_location_id=get_location_by_location_id,
                           get_driver_name_by_driver_id=get_driver_name_by_driver_id,
                           get_number_of_booked_seats_ride_id=get_number_of_booked_seats_ride_id,
                           get_rating_by_ride_id=get_rating_by_ride_id)


def get_driver_name_by_driver_id(driver_id):
    query = {"_id": driver_id}
    driver = driver_collection.find_one(query)
    return driver


@app.route("/book_ride")
def book_ride():
    ride_id = request.args.get("ride_id")
    number_of_seats = request.args.get("number_of_seats")
    query = {"_id": ObjectId(ride_id)}
    ride = rides_collection.find_one(query)
    total_price = int(ride['price']) * int(number_of_seats)
    return render_template("book_ride.html", ride_id=ride_id, total_price=total_price, number_of_seats=number_of_seats,
                           ride=ride, int=int)


@app.route("/book_ride_action" ,methods=['post'])
def book_ride_action():
    ride_id = request.form.get("ride_id")
    rider_id = session.get('rider_id')
    address = request.form.get("address")
    booking_date = datetime.now()
    payment_date = datetime.now()
    number_of_seats = request.form.get("number_of_seats")
    total_price = request.form.get("total_price")
    card_type = request.form.get("card_type")
    card_number = request.form.get("card_number")
    card_holder_name = request.form.get("card_holder_name")
    cvv = request.form.get("cvv")
    expiry_date = request.form.get("expiry_date")
    admin_commission = int(total_price) * 0.1
    driver_price = int(total_price) * 0.9
    admin_commission_str = str(admin_commission)
    driver_price_str = str(driver_price)
    passengers = []
    for i in range(1, int(number_of_seats) + 1):
        passenger_first_name = request.form.get("passenger_first_name" + str(i))
        passenger_last_name = request.form.get("passenger_last_name" + str(i))
        gender = request.form.get("gender" + str(i))
        dob = request.form.get("dob" + str(i))
        passenger_details = request.form.get("passenger_details" + str(i))
        image = request.files.get("passenger_image" + str(i))
        path = APP_ROOT_PASSENGER + "/" + image.filename
        image.save(path)
        passenger = {"passenger_first_name": passenger_first_name,"passenger_last_name": passenger_last_name,"dob": dob,"passenger_details": passenger_details, "gender": gender, "image": image.filename}
        passengers.append(passenger)
    query = {"rider_id": ObjectId(rider_id), "ride_id": ObjectId(ride_id), "booking_date": booking_date,
             "total_price": total_price, "admin_commission": admin_commission_str, "number_of_seats": number_of_seats,
             "driver_price": driver_price_str, "passengers": passengers, "status": "Ride Requested"}
    result = booking_collection.insert_one(query)
    booking_id = result.inserted_id
    query = {"rider_id": ObjectId(rider_id), "booking_id": ObjectId(booking_id), "payment_date": payment_date,
             "total_price": total_price, "card_type": card_type, "card_number": card_number,
             "card_holder_name": card_holder_name, "cvv": cvv, "expiry_date": expiry_date,
             "status": "Payment Successfully Completed"}
    payment_collection.insert_one(query)
    return render_template("message_action.html", message="Ride Booked successfully")


@app.route("/bookings")
def bookings():
    query = ''
    if session['role'] == 'rider':
        rider_id = session['rider_id']
        query = {"rider_id": ObjectId(rider_id)}
    elif session['role'] == 'driver':
        driver_id = session['driver_id']
        ride_id = request.args.get("ride_id")
        if ride_id is not None:
            query = {"ride_id": ObjectId(ride_id)}
        else:
            rides = rides_collection.find({"driver_id": ObjectId(driver_id)})
            ride_ids = [ride["_id"] for ride in rides]
            query = {"ride_id": {"$in": ride_ids}}
    bookings = booking_collection.find(query)
    bookings = list(bookings)
    return render_template("bookings.html", bookings=bookings, ride_by_ride_id=ride_by_ride_id,
                           get_driver_name_by_driver_id=get_driver_name_by_driver_id,
                           rider_by_rider_id=rider_by_rider_id, get_location_by_location_id=get_location_by_location_id,
                           str=str)


def ride_by_ride_id(ride_id):
    query = {"_id": ride_id}
    ride = rides_collection.find_one(query)
    return ride


def rider_by_rider_id(rider_id):
    query = {"_id": rider_id}
    rider = rider_collection.find_one(query)
    return rider


@app.route("/cancel_ride")
def cancel_ride():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    update = {"$set": {"status": "cancelled"}}
    booking_collection.update_one(query, update)
    return redirect("/bookings")


@app.route("/cancel_booked_ride")
def cancel_booked_ride():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    update = {"$set": {"status": "Cancelled Booked Ride"}}
    booking_collection.update_one(query, update)
    return redirect("/bookings")


def get_number_of_booked_seats_ride_id(ride_id):
    query = {"$or": [{"ride_id": ride_id, "status": "Ride Booked"}, {"ride_id": ride_id, "status": "Picked Up"},
                     {"ride_id": ride_id, "status": "Dropped"}]}
    bookings = booking_collection.find(query)
    bookings = list(bookings)
    number_of_seats_booked = 0;
    for booking in bookings:
        number_of_seats_booked = number_of_seats_booked + int(booking['number_of_seats'])
    return number_of_seats_booked


@app.route("/pick_up_ride")
def pick_up_ride():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    update = {"$set": {"status": "Picked Up"}}
    result = booking_collection.update_one(query, update)
    return redirect("/bookings")


@app.route("/drop_ride")
def drop_ride():
    booking_id = request.args.get("booking_id")
    query = {"_id": ObjectId(booking_id)}
    update = {"$set": {"status": "Dropped"}}
    result = booking_collection.update_one(query, update)
    return redirect("/bookings")


@app.route("/accept_action")
def accept_action():
    booking_id = request.args.get("booking_id")
    query1 = {"_id": ObjectId(booking_id)}
    query2 = {"$set": {"status": "Ride Booked"}}
    booking_collection.update_one(query1, query2)
    return render_template("message_action.html", message="Request Accepted")


@app.route("/view_payments")
def view_payments():
    booking_id = request.args.get("booking_id")
    query = {"booking_id": ObjectId(booking_id)}
    payments = payment_collection.find(query)
    payments = list(payments)
    return render_template("view_payments.html", booking_id=booking_id, payments=payments,
                           get_commission_by_booking_id=get_commission_by_booking_id)


@app.route("/give_review_rating")
def give_review_rating():
    booking_id = request.args.get("booking_id")
    return render_template("give_review_rating.html", booking_id=booking_id)


@app.route("/give_review_rating_to_passenger")
def give_review_rating_to_passenger():
    booking_id = request.args.get("booking_id")
    passenger_first_name = request.args.get("passenger_first_name")
    return render_template("give_review_rating_to_passenger.html", booking_id=booking_id,passenger_first_name=passenger_first_name)


@app.route("/give_review_action")
def give_review_action():
    booking_id = request.args.get("booking_id")
    review = request.args.get("review")
    rating = request.args.get("rating")
    rider_id = session['rider_id']
    current_time = datetime.now()
    query = {"booking_id": ObjectId(booking_id), "review": review, "rating": rating,
             "date": current_time, "rider_id": ObjectId(rider_id)}
    review_collection.insert_one(query)
    return render_template("message_action.html", message="Review Submitted successfully")


@app.route("/give_review_rating_to_passenger_action")
def give_review_rating_to_passenger_action():
    booking_id = request.args.get("booking_id")
    review = request.args.get("review")
    rating = request.args.get("rating")
    passenger_first_name = request.args.get("passenger_first_name")
    current_time = datetime.now()
    query = {"booking_id": ObjectId(booking_id), "review": review, "rating": rating,
             "date": current_time, "passenger_first_name": passenger_first_name}
    review_collection.insert_one(query)
    return render_template("message_action.html", message="Review Submitted successfully")


def get_rating_by_ride_id(ride_id):
    query = {"ride_id": ride_id}
    bookings = booking_collection.find(query)
    booking_ids = []
    for booking in bookings:
        booking_ids.append(booking['_id'])
    query = {"booking_id": {"$in": booking_ids}}
    reviews = review_collection.find(query)
    reviews = list(reviews)
    rating = 0
    for review in reviews:
        rating = rating + int(review['rating'])
    if len(reviews) == 0:
        return "No Reviews"
    rating = round(rating / len(reviews), 2)
    return rating


@app.route("/view_reviews")
def view_reviews():
    ride_id = request.args.get("ride_id")
    query = {"ride_id": ObjectId(ride_id)}
    bookings = booking_collection.find(query)
    booking_ids = []
    for booking in bookings:
        booking_ids.append(booking['_id'])
    query = {"booking_id": {"$in": booking_ids}}
    reviews = review_collection.find(query)
    reviews = list(reviews)
    return render_template("view_reviews.html", reviews=reviews, get_rider_by_rider_id=get_rider_by_rider_id)


def get_rider_by_rider_id(rider_id):
    query = {"_id": rider_id}
    rider = rider_collection.find_one(query)
    return rider


def get_commission_by_booking_id(booking_id):
    query = {"_id": booking_id}
    commission = booking_collection.find_one(query)
    return commission


@app.route("/edit_location")
def edit_location():
    location_id = request.args.get("location_id")
    query = {"_id": ObjectId(location_id)}
    location = location_collection.find_one(query)
    return render_template("edit_location.html",location=location,location_id=location_id)


@app.route("/edit_locations_action")
def edit_locations_action():
    location_id = request.args.get("location_id")
    location_name = request.args.get("location_name")
    query = {"$set": {"location_name": location_name}}
    location_collection.update_one({"_id": ObjectId(location_id)}, query)
    return redirect("/add_locations")

@app.route("/forgot_driver_password")
def forgot_driver_password():
    return render_template("forgot_driver_password.html")


@app.route("/for_got_password_action",methods=['post'])
def for_got_password_action():
    email = request.form.get("email")
    count = driver_collection.count_documents({"email":email})
    if count>0:
        otp = random.randint(1000,10000)
        send_email("Verification Code","Hello your  Verification Code For Reset Password : "+str(otp)+"",email)
        return render_template("for_got_password_action1.html",otp=otp,email=email)
    else:
        return render_template("message.html", message="Invalid Email To verify")

@app.route("/for_got_password_action2",methods=['post'])
def for_got_password_action2():
    email = request.form.get("email")
    otp = request.form.get("otp")
    otp2 = request.form.get("otp2")
    password2 = request.form.get("password2")
    password = request.form.get("password")
    if otp2!=otp:
        return render_template("message.html", message="Invalid OTP")
    if password!=password2:
        return render_template("message.html", message="Invalid New and confirm password")
    query = {"$set":{"password":password}}
    driver_collection.update_one({"email":email},query)
    return render_template("message.html", message="Password Reset Successfully")

@app.route("/forgot_rider_password")
def forgot_rider_password():
    return render_template("forgot_rider_password.html")

@app.route("/for_got_password_rider_action",methods=['post'])
def for_got_password_rider_action():
    email = request.form.get("email")
    count = rider_collection.count_documents({"email":email})
    if count>0:
        otp = random.randint(1000,10000)
        send_email("Verification Code","Hello your  Verification Code For Reset Password : "+str(otp)+"",email)
        return render_template("for_got_password_rider_action1.html",otp=otp,email=email)
    else:
        return render_template("message.html", message="Invalid Email To verify")

@app.route("/for_got_password_rider_action2",methods=['post'])
def for_got_password_rider_action2():
    email = request.form.get("email")
    otp = request.form.get("otp")
    otp2 = request.form.get("otp2")
    password2 = request.form.get("password2")
    password = request.form.get("password")
    if otp2!=otp:
        return render_template("message.html", message="Invalid OTP")
    if password!=password2:
        return render_template("message.html", message="Invalid New and confirm password")
    query = {"$set":{"password":password}}
    rider_collection.update_one({"email":email},query)
    return render_template("message.html", message="Password Reset Successfully")



# ===== Run the App =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

