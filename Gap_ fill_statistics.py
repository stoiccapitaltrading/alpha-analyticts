
import base64
import streamlit as st

import streamlit as st
import base64

# Function to inject a sidebar logo at the top
def inject_sidebar_logo(image_path="logo.png"):
    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode()

    # Inject custom CSS with the base64 logo
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebarNav"]::before {{
            content: "";
            display: block;
            margin-top: -60px;  /* Moves logo closer to top */
            margin-bottom: 20px;
            height: 180px;       /* Adjust logo size here */
            background-image: url("data:image/png;base64,{encoded_logo}");
            background-repeat: no-repeat;
            background-size: contain;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Call the function
inject_sidebar_logo()


