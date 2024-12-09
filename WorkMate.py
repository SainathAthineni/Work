import os
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth, initialize_app, get_app
import base64
from datetime import datetime
import googlemaps
import folium
from streamlit_folium import st_folium

# Decode Base64 Firebase key from Streamlit secrets
firebase_key_path = "firebase-key.json"

# Check if Firebase key file already exists, otherwise create it
if not os.path.exists(firebase_key_path):
    try:
        with open(firebase_key_path, "wb") as json_file:
            json_file.write(base64.b64decode(st.secrets["ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAid29ya21hdGUtNjQzZGIiLAogICJwcml2YXRlX2tleV9pZCI6ICI2Yzg4OWM3ODFiYjcwN2RhMDRlOGI2YWE2N2FiOGMyODUzM2MyNzk3IiwKICAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tXG5NSUlFdlFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLY3dnZ1NqQWdFQUFvSUJBUURLRDBNSVZXQzd4NEZqXG5UMGpnYnRoVW90V28wVlpuVklEUWFCUDBlV002OTFIWWkyamZ6NTY2UkZGdkZCMit1eWZpWEx4OGEvTWhyQWlUXG5hZGt5SE9TSWdTdkVxL0Z0YTBROVBra2JiNW9PVThtTFQyMW5LSm1tMzA1NTZDK0l5RUtRbjVQYUVIT0lxMFc5XG5ybm9Wb1NGWUt6N2VTTDRjK3FhTUYveVQwdWJxQXJTRmhkaGdheW1LdlZ5aEJBd1JyVGNOM1NGR0dBM0lzcHRRXG5rMGU4YVB4ditNYytxeHVNNitNR0lFbDk2Ym5UTUhLWE1zWkdISDJBVVFmdGhzbHNrUmRQU3Z2S05FM0hTaFRMXG5RYVMyWHo2TmpFUmdNbGhzcGRwRGZlTWlnbi8xMjdVWGZYdlJZV0NtQzc0R0xnR3pFcUFoZjF1VjNMSyszcjExXG5FL1luOVFBakFnTUJBQUVDZ2dFQVNZUjJDa0V1T2dSajBtTlZpN3NvNE5xQ1RMTWw4ZUN3SWFQTXB1WEhzZnVzXG5mdEp5YlFSWXAwTVdNZ2txcld2aEhoNUp3aWR3eGU2WERETzEvK0s5VCtGWHNHNHpJSEduMlhTaEd1ZG5NUkZSXG5RbXU2elk3YklQa2N6NFFvVDJjMXVQTW0wMitxNmE0UGFPMWpwQjBGU2RRcVFxeEs1N1pYQkoveG1VTmlHd0FOXG5OcC9OenpnOEJNQUUrSU9SZmlOQ0RESWFlenk2Zlpqc04zajgyWjJMYkRGU3NQV0cxckR5UUc1NzhrN2EzMWhyXG5IRGd5MnNrbGVLRWszYmkvK25KS25lOUd0Z1BmcDNLVnlKZzR5U0hTaTh3cUpPV3QzTUFoaXZTdkJRayttb2dkXG5hN3ZWWVNrdHM2UTFTTW5UZGFUS1pTV0U1UU5la2tQa1p2MEllUzdlQVFLQmdRRHdaQ3NDWGQzeWtKczVnNE04XG5oRTRMOWZuMDVPN09KY1NodWJHNC9yeE9CQWVmdDNBMkZtUGpXVzI2dXhIQmF3RmlXUGZkT1FxUGF6Zjlpcno4XG5RQXcvcE5QOFhFbytTdXJUajRSWHh2cUJxVjdyMWc4M3NON2Q0RUJCSUhxYVNEWUJURGhSRTg0a0MybXVMcmVSXG40WkFrNnNBaDk5TVhPd0FiUlRRdmg5YlRBUUtCZ1FEWExlL3UxTk9XTWVLUHdnUVJyYTNXKzRyd0IxK3BYSEY3XG5kV1N2QklHbXFZOEVrWndFTXFaWm15V2ZRUHVxWmFManFRelBKUzdmRzZ3aEZVK0lSMk5qYkx2ay9vTGhYRXBUXG43dnphaElyU2FReU1TVllyWGtjS3NxUk5MNDgwOTFJY3dEV1pPWXhydksyS0duR0JuUmdGemp1ZmFSQXhiOFJTXG51eXRKdUhFbkl3S0JnUURGc1JyTnIzUS9ienk0WjdjZHBaQ3B0WGdDTmVOT0ZURkg3dmFCTkx5WFRDa1k2RHFYXG53SUlWRGc1M2FqQ0g2QUFUYVNjdC95TDRIeXpFamJ3dGxsNThXSWtkR0tqVjRiYU1sWkk0dmFKMXoxd0lodG1zXG42di9kWi9adm1NNDY0dmZHeVcvbS9XcWhxZUVYSmNSQmJFYW1sWWU4WjVwcG1GUFdHV3Q1U3pVWUFRS0JnR0tWXG56MW15OUlYWnNSMkFISEVsQzRKMW1NQkVBSllObm9pYnpsZEpUMFZXWmdvSDFGMHYvM3NLVkFCVXUzamtPKzdtXG5JdEk5RE81M05UT3JHZGNzTGVMOWpGQnNNdmFoWEFSOGVDaDlsVVMxa0dRdHJXY05PS3MwRVlhemhYOFUyUEFIXG5PQWROa0lKRDNaWnFheHFoS01Kd0xHenFxOXFhaEc0TEJ0Z3R3dG5WQW9HQU1YY0Y4bEJoOE9BZlpCc014VWFrXG52ZTYrWGdQc2Q1bXV2Mk41d0g5NFJ2TkVYUndBMmdGdzRSVm9USllocXVhU2ZYaEdyVlIwR0xMcmlDd1NPRG1qXG5Pc0FwY0llV1BoYXFIaDlzVFdweFU3OE94QVRKaVlWUWRaODJPenBCaU1pTFFmQUFiTDBIMGNMUnVyYUh6WUI0XG45QlVqcVZBYnNaTWlYbHZzL096dUtyRT1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsCiAgImNsaWVudF9lbWFpbCI6ICJmaXJlYmFzZS1hZG1pbnNkay13cGI2NEB3b3JrbWF0ZS02NDNkYi5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMDA1NzM0MDc3NDU2MDY4MTI2MTkiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2ZpcmViYXNlLWFkbWluc2RrLXdwYjY0JTQwd29ya21hdGUtNjQzZGIuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLAogICJ1bml2ZXJzZV9kb21haW4iOiAiZ29vZ2xlYXBpcy5jb20iCn0="]))
    except KeyError:
        st.error("FIREBASE_KEY not found in Streamlit secrets. Please add it.")
        st.stop()  # Stop execution if the secret is missing

# Initialize Firebase Admin SDK
try:
    app = firebase_admin.get_app()  # Check if already initialized
except ValueError:
    try:
        cred = credentials.Certificate(firebase_key_path)
        app = firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Failed to initialize Firebase: {e}")
        st.stop()  # Stop execution if Firebase initialization fails

# Initialize Firestore
try:
    db = firestore.client()
except Exception as e:
    st.error(f"Failed to initialize Firestore: {e}")
    st.stop()  # Stop execution if Firestore initialization fails


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
