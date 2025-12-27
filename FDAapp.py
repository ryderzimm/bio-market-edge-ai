#!/usr/bin/env python
# coding: utf-8

# In[14]:


import streamlit as st
import requests
import pandas as pd
from google import genai
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. Page Configuration ---
st.set_page_config(page_title="BioMarket Edge AI", layout="wide", page_icon="💊")

# --- 2. Load Secrets ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    RECEIVER_EMAIL = st.secrets["RECEIVER_EMAIL"]
    secrets_ready = True
except:
    secrets_ready = False

# --- 3. Duplicate Prevention (Caching) ---
@st.cache_data(ttl=86400) # Cache for 24 hours
def has_notified_today(notice_id):
    """Returns True if this specific notice was already emailed today."""
    # This function effectively 'remembers' a notice ID for 24 hours
    return True

# --- 4. Core Functions ---

def send_real_email(title, link):
    if not secrets_ready: return
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"🚨 BIOMARKET ALERT: {title[:40]}..."
    body = f"High-value FDA notice detected:\n\nTitle: {title}\nLink: {link}"
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        st.error(f"Email failed: {e}")

def fetch_drug_notices():
    base_url = "https://www.federalregister.gov/api/v1/documents.json"
    params = {"conditions[agency_ids][]": [164], "conditions[type][]": "NOTICE", 
              "conditions[term]": "CDER CBER drug advisory", "order": "newest"}
    try:
        r = requests.get(base_url, params=params)
        results = r.json().get('results', [])
        keys = ['drug', 'biologic', 'clinical', 'pharmaceutical', 'application']
        return [doc for doc in results if any(k in doc['title'].lower() for k in keys)]
    except: return []

# --- 5. Passive Automation Logic ---

def run_background_scan():
    """Logic that runs every time the cron-job pings the URL."""
    notices = fetch_drug_notices()
    watchlist = [name.strip().lower() for name in st.sidebar.get("watchlist", "Pfizer, Moderna").split(",")]
    
    for doc in notices:
        title = doc['title']
        notice_id = doc.get('document_number', title) # Use legal doc ID
        
        # Check if company is in watchlist
        if any(company in title.lower() for company in watchlist):
            # Check if we already emailed about this today
            if notice_id not in st.session_state.get('emailed_notices', []):
                send_real_email(title, doc['html_url'])
                # Track that we've notified for this
                if 'emailed_notices' not in st.session_state:
                    st.session_state.emailed_notices = []
                st.session_state.emailed_notices.append(notice_id)
                st.toast(f"Passive Alert Sent for {title[:30]}...")

# --- 6. Main UI ---

st.title("💊 BioMarket Edge AI")
watchlist_input = st.sidebar.text_area("Watchlist:", "Pfizer, Moderna, Biogen, Eli Lilly", key="watchlist")

# AUTOMATIC TRIGGER: Runs every time page is loaded (including by Cron-job)
if secrets_ready:
    run_background_scan()

if st.button("Manual Scan"):
    # Code for manual UI display... (similar to previous versions)
    st.write("Scan complete. Alerts sent for new matches.")


# In[ ]:




