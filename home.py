import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import secrets
import subprocess
from streamlit.components.v1 import html
import webbrowser

def nav_page(page_name, timeout_secs=3):
    nav_script = """
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        links[i].click();
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_nav_page, 100, page_name, start_time, timeout_secs);
                } else {
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_nav_page("%s", new Date(), %d);
            });
        </script>
    """ % (page_name, timeout_secs)
    html(nav_script)

user_data = pd.read_csv('aa.csv')
def main():
    global user_data 
    st.title("Welcome to AIFinTech")
    page = st.selectbox("Choose a page", ["Home", "Register", "Login", "Forgot Password"])
    
    if page == "Home":
        st.header("Welcome to the Home Page")
        st.write("Choose 'Register', 'Login', or 'Forgot Password' from the sidebar.")

    elif page == "Register":
        st.header("User Registration")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        email = st.text_input("Email")

        if st.button("Register"):
            if username not in user_data['Username'].values:
                user_data = user_data.append({'Username': username, 'Password': password, 'Email': email, 'ResetToken': ''}, ignore_index=True)
                user_data.to_csv('aa.csv', index=False)  
                st.success("Registration successful! Please go to the 'Login' page.")
            else:
                st.error("Username already exists. Choose a different one.")

    elif page == "Login":
        st.header("User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')

        if st.button("Login"):
            if check_credentials(username, password):
                st.success(f"Welcome back, {username}!")
                # nav_page('./userdetails.py')
                # st.markdown("(/userdetails)")
                # url = "http://localhost:8501/"
                # url = "userdetails.py"
                # webbrowser.open_new_tab(url)
                subprocess.Popen(["streamlit", "run", "userdetails.py"])
                
            else:
                st.error("Invalid username or password. Please try again.")

    elif page == "Forgot Password":
        st.header("Forgot Password")
        email = st.text_input("Enter your email:", key="email", help="Enter your email for sending reset instructions")

        if st.button("Reset Password"):
            if email in user_data['Email'].values:
                reset_token = generate_reset_token()
                send_reset_email(email, reset_token)
                st.success(f"Password reset instructions sent to {email}. Check your email.")
            else:
                st.error("Email not found. Please enter a registered email.")

def check_credentials(username, password):
    return any((user_data['Username'] == username) & (user_data['Password'] == password))

def generate_reset_token():
    return secrets.token_urlsafe(32)

def send_reset_email(email, reset_token):
    sender_email = "kashish.mahajan_comp21@pccoer.in"
    sender_password = "yccf vvhs jfvm aquz"
    subject = "Password Reset Request"
   
    body = f"""
    Click the following link to reset your password: http://your-reset-link/wAvt1yrDJtD25OjBMmAg
    """

    message = MIMEMultipart()
    message.attach(MIMEText(body, 'plain'))
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())

if __name__ == "__main__":
    main()
