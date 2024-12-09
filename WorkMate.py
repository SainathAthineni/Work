import os
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth, initialize_app, get_app
import base64
from datetime import datetime
import googlemaps
import folium
from streamlit_folium import st_folium

# Load the Firebase JSON key from Streamlit secrets
try:
    firebase_json = st.secrets["FIREBASE_JSON"]
    firebase_config = json.loads(firebase_json)
except KeyError:
    st.error("FIREBASE_JSON not found in Streamlit secrets. Please add it.")
    st.stop()  # Stop execution if the secret is missing
except Exception as e:
    st.error(f"Error loading Firebase JSON: {e}")
    st.stop()

# Initialize Firebase Admin SDK
try:
    app = firebase_admin.get_app()  # Check if already initialized
except ValueError:
    cred = credentials.Certificate(firebase_config)
    app = firebase_admin.initialize_app(cred)

# Initialize Firestore
try:
    db = firestore.client()
except Exception as e:
    st.error(f"Error initializing Firestore: {e}")
    st.stop()

# Access Google Maps API key
google_maps_api_key = st.secrets["google_maps_api_key"]

# Initialize session state
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Login"  # Default to Login page

# Helper function to get location suggestions
# Helper function to get location suggestions
def get_location_suggestions(query):
    try:
        results = gmaps_client.places_autocomplete(input_text=query)
        suggestions = []
        for result in results:
            geocode_result = gmaps_client.geocode(result["description"])
            if geocode_result:
                location_data = geocode_result[0]
                suggestions.append({
                    "address": location_data["formatted_address"],  # Complete address including postal code
                    "lat": location_data["geometry"]["location"]["lat"],
                    "lng": location_data["geometry"]["location"]["lng"]
                })
        return suggestions
    except Exception as e:
        st.error(f"Error fetching location suggestions: {e}")
        return []
    
def admin_dashboard():
    st.title("Admin Dashboard")
    st.write(f"Welcome, {st.session_state['user_email']}!")

    # Overview Metrics
    workers_count = len(list(db.collection("workers").stream()))
    companies_count = len(list(db.collection("companies").stream()))  # Assuming companies are stored
    bookings_today = 0  # Replace with actual logic to count today's bookings

    st.metric("Total Workers", workers_count)
    st.metric("Active Companies", companies_count)
    st.metric("Bookings Today", bookings_today)

    # Workers Details
    st.subheader("All Workers")
    workers = db.collection("workers").stream()
    workers_data = []

    for worker in workers:
        data = worker.to_dict()
        workers_data.append({
            "Worker ID": worker.id,
            "Email": data.get("email", "N/A"),
            "Address": data.get("address", "N/A"),
            "Non-Working Days": ", ".join(data.get("nonWorkingDays", []))
        })

    if workers_data:
        workers_df = pd.DataFrame(workers_data)
        st.dataframe(workers_df)
    else:
        st.warning("No workers found.")

    # Companies Details
    st.subheader("All Companies")
    companies = db.collection("companies").stream()
    companies_data = []

    for company in companies:
        data = company.to_dict()
        companies_data.append({
            "Company ID": company.id,
            "Email": data.get("email", "N/A"),
            "Address": data.get("address", "N/A"),
            "Name": data.get("name", "N/A")
        })

    if companies_data:
        companies_df = pd.DataFrame(companies_data)
        st.dataframe(companies_df)
    else:
        st.warning("No companies found.")

    # Logs
    st.subheader("Activity Logs")
    logs = db.collection("logs").stream()
    logs_data = []

    for log in logs:
        logs_data.append(log.to_dict())

    if logs_data:
        logs_df = pd.DataFrame(logs_data)
        st.dataframe(logs_df)
    else:
        st.warning("No logs found.")
    
    


# Worker Dashboard
def worker_dashboard():
    st.title("Worker Dashboard")
    st.write(f"Welcome, {st.session_state['user_email']}!")
    worker_id = st.text_input("Worker ID")
    location_query = st.text_input("Enter Your Address")
    address_details = None

    if location_query:
        suggestions = get_location_suggestions(location_query)
        if suggestions:
            selected_address = st.selectbox(
                "Select Your Address",
                [s["address"] for s in suggestions],
            )
            address_details = next(s for s in suggestions if s["address"] == selected_address)

    non_working_days = st.date_input("Select Non-Working Days", [])

    if st.button("Save Availability"):
        if worker_id and address_details:
            db.collection("workers").document(worker_id).set({
                "address": address_details["address"],
                "lat": address_details["lat"],
                "lng": address_details["lng"],
                "nonWorkingDays": [day.isoformat() for day in non_working_days],
                "email": st.session_state["user_email"]
            })
            st.success("Availability saved!")
        else:
            st.error("Please provide Worker ID and select a valid address.")


# Company Dashboard
import pandas as pd

def company_dashboard():
    st.title("Company Dashboard")
    st.write(f"Welcome, {st.session_state['user_email']}!")

    location_query = st.text_input("Enter Search Location")
    center_location = None

    if location_query:
        suggestions = get_location_suggestions(location_query)
        if suggestions:
            selected_location = st.selectbox(
                "Select a Location",
                [s["address"] for s in suggestions],
            )
            center_location = next(s for s in suggestions if s["address"] == selected_location)

    radius = st.slider("Search Radius (km)", 1, 50, 10)
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    if st.button("Search Workers"):
        if center_location and start_date and end_date:
            workers = db.collection("workers").stream()
            available_workers = []

            # Generate the set of dates in the selected range
            search_dates = set(pd.date_range(start_date, end_date).date)

            for worker in workers:
                data = worker.to_dict()
                worker_lat = data.get("lat")
                worker_lng = data.get("lng")
                worker_non_working_days = set(
                    datetime.fromisoformat(day).date()
                    for day in data.get("nonWorkingDays", [])
                )

                if worker_lat and worker_lng:
                    distance = gmaps_client.distance_matrix(
                        origins=[(center_location["lat"], center_location["lng"])],
                        destinations=[(worker_lat, worker_lng)],
                        mode="driving"
                    )["rows"][0]["elements"][0]["distance"]["value"] / 1000  # Convert meters to km

                    # Check if the worker is available and within the radius
                    if distance <= radius and not worker_non_working_days.intersection(search_dates):
                        available_workers.append(data)

            if available_workers:
                st.write("### Available Workers")
                worker_locations = []

                for worker in available_workers:
                    st.write(f"**Name:** {worker.get('email')}")
                    st.write(f"**Address:** {worker.get('address')}")
                    st.write(f"**Non-Working Days:** {', '.join(worker.get('nonWorkingDays', []))}")
                    st.write("---")
                    worker_locations.append({
                        "lat": worker.get("lat"),
                        "lon": worker.get("lng"),
                        "email": worker.get("email"),
                    })

                # Show workers' locations on a map
                worker_df = pd.DataFrame(worker_locations)
                st.map(worker_df)

            else:
                st.warning("No workers available for the selected dates and location.")
        else:
            st.error("Please complete all fields for worker search.")

# Sign-Up Screen
def signup():
    st.title("Sign-Up")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    full_name = st.text_input("Full Name")
    role = st.selectbox("Role", ["Worker", "Company", "Admin"])
    address = st.text_input("Address")

    if st.button("Sign Up"):
        if password == confirm_password:
            try:
                user = auth.create_user(email=email, password=password)
                db.collection("users").document(user.uid).set({
                    "email": email,
                    "name": full_name,
                    "role": role,
                    "address": address,
                    "created_at": datetime.now()
                })
                st.success(f"Account created successfully for {email}!")
            except Exception as e:
                st.error(f"Sign-Up Failed: {e}")
        else:
            st.error("Passwords do not match!")

# Login Screen
def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            user = auth.get_user_by_email(email)
            doc = db.collection("users").where("email", "==", email).get()
            if doc:
                user_data = doc[0].to_dict()
                st.session_state["user_role"] = user_data["role"]
                st.session_state["user_email"] = email
                st.session_state["current_page"] = user_data["role"]
                st.success(f"Welcome back, {user_data['name']}!")
            else:
                st.error("User details not found in Firestore.")
        except Exception as e:
            st.error(f"Login Failed: {e}")

# Logout Button
def logout():
    if st.button("Logout"):
        st.session_state["user_email"] = None
        st.session_state["user_role"] = None
        st.session_state["current_page"] = "Login"
        st.success("You have logged out.")

# App Navigation
def main():
    if st.session_state["user_email"]:
        logout()
        if st.session_state["current_page"] == "Worker":
            worker_dashboard()
        elif st.session_state["current_page"] == "Company":
            company_dashboard()
        elif st.session_state["current_page"] == "Admin":
            admin_dashboard()
    else:
        choice = st.sidebar.radio("Go to", ["Login", "Sign Up"])
        if choice == "Sign Up":
            signup()
        elif choice == "Login":
            login()

if __name__ == "__main__":
    main()
