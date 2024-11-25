import streamlit as st
import paypalrestsdk
from paypalrestsdk import Payment
import firebase_admin
from firebase_admin import credentials, firestore, auth as admin_auth
import json
import os

# Set up the Streamlit page configuration (must be the first Streamlit command)
st.set_page_config(
    page_title="Edu Pro - Accelerate Your Growth",
    page_icon="🚀",
    layout="wide"
)

# Firebase Initialization
if not firebase_admin._apps:  # Avoid multiple Firebase initializations
    try:
        service_account_info = json.loads(st.secrets["firebase"]["service_account_key"])
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        db = firestore.client()  # Firestore database instance
    except Exception as e:
        st.error(f"Failed to initialize Firebase: {e}")
        st.stop()

# PayPal SDK Configuration
try:
    paypalrestsdk.configure({
        "mode": "sandbox",  # Use "live" for production
        "client_id": st.secrets["paypal"]["client_id"],
        "client_secret": st.secrets["paypal"]["client_secret"]
    })
except Exception as e:
    st.error(f"Failed to configure PayPal: {e}")
    st.stop()


def landing_page():
    """Landing Page with styling and navigation."""
    st.markdown("""
        <style>
            .stApp {
                background-color: #0D1117; /* Dark background */
                color: white; /* Light text */
                font-family: 'Arial', sans-serif;
            }
            .main-container {
                text-align: center;
                padding-top: 15%;
            }
            .header-title {
                font-size: 3.5rem;
                color: #58A6FF;
                font-weight: bold;
            }
            .sub-title {
                font-size: 1.2rem;
                color: #8B949E;
                margin-top: 20px;
            }
            .button-container {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 30px;
            }
            .btn {
                padding: 12px 30px;
                font-size: 1rem;
                font-weight: bold;
                color: #58A6FF;
                background: transparent;
                border: 2px solid #58A6FF;
                border-radius: 5px;
                text-decoration: none;
                cursor: pointer;
                transition: 0.3s;
            }
            .btn:hover {
                background: #58A6FF;
                color: #0D1117;
            }
            .footer-text {
                margin-top: 50px;
                font-size: 0.9rem;
                color: #8B949E;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="main-container">
            <h1 class="header-title">Accelerate Your Growth with Advanced AI</h1>
            <p class="sub-title">Experience the next generation of AI assistance. Process data, generate insights, and automate workflows with unparalleled speed and precision.</p>
            <div class="button-container">
                <button onclick="location.href='/signup_signin'" class="btn">Get Started</button>
                <button onclick="location.href='/demo'" class="btn">Watch Demo</button>
            </div>
            <p class="footer-text">Trusted by 150+ enterprise companies worldwide</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Get Started"):
        st.session_state["page"] = "signup_signin"
        st.experimental_rerun()


def signup_page():
    """Sign-Up and Log-In Page"""
    st.title("Sign Up or Log In")
    col1, col2 = st.columns(2)

    with col1:
        # Display an image if available
        img_path = "school.jpg"
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.image("https://via.placeholder.com/600x400?text=School+Image", use_container_width=True)

    with col2:
        option = st.radio("Are you a new or returning user?", ["Sign Up", "Sign In"])

        if option == "Sign Up":
            st.subheader("Register Your School")
            school_name = st.text_input("School Name")
            email = st.text_input("Admin Email")
            password = st.text_input("Password", type="password")

            if st.button("Proceed to Payment"):
                if school_name and email and password:
                    try:
                        payment = Payment({
                            "intent": "sale",
                            "payer": {"payment_method": "paypal"},
                            "redirect_urls": {
                                "return_url": "http://localhost:8501/success",
                                "cancel_url": "http://localhost:8501/cancel"
                            },
                            "transactions": [{
                                "item_list": {
                                    "items": [{
                                        "name": "School Pro Subscription",
                                        "sku": "subscription001",
                                        "price": "1.00",
                                        "currency": "USD",
                                        "quantity": 1
                                    }]
                                },
                                "amount": {
                                    "total": "1.00",
                                    "currency": "USD"
                                },
                                "description": "Pro subscription for School Management Portal."
                            }]
                        })

                        if payment.create():
                            st.success("Payment created successfully!")
                            for link in payment.links:
                                if link.rel == "approval_url":
                                    st.markdown(f"[Click here to pay]({link.href})")
                                    st.session_state["signup_details"] = {
                                        "school_name": school_name,
                                        "email": email,
                                        "password": password,
                                    }
                                    break
                        else:
                            st.error(f"Error while creating payment: {payment.error}")
                    except Exception as e:
                        st.error(f"Payment error: {e}")
                else:
                    st.warning("Please fill all fields.")

        elif option == "Sign In":
            st.subheader("Log In")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Log In"):
                try:
                    user = admin_auth.get_user_by_email(email)
                    school_ref = db.collection("schools").where("email", "==", email).get()
                    if school_ref:
                        school_data = school_ref[0].to_dict()
                        st.success(f"Welcome back, {school_data['name']}!")
                        st.session_state["page"] = "main_app"
                        st.experimental_rerun()
                    else:
                        st.error("School data not found.")
                except Exception as e:
                    st.error(f"Login failed: {e}")


def app_router():
    """Route Between Pages"""
    if "page" not in st.session_state:
        st.session_state["page"] = "landing"

    if st.session_state["page"] == "landing":
        landing_page()
    elif st.session_state["page"] == "signup_signin":
        signup_page()


if __name__ == "__main__":
    app_router()
