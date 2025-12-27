#!/usr/bin/env python
# coding: utf-8

# In[15]:


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
except Exception:
    secrets_ready = False

# --- 3. Core Functions ---

def send_real_email(title, link):
    """Sends a real email alert via Gmail SMTP."""
    if not secrets_ready: 
        return
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
        st.error(f"Email delivery failed: {e}")

def fetch_drug_notices():
    """Fetches official drug-related notices from Federal Register."""
    base_url = "https://www.federalregister.gov/api/v1/documents.json"
    params = {
        "conditions[agency_ids][]": [164], 
        "conditions[type][]": "NOTICE", 
        "conditions[term]": "CDER CBER drug advisory", 
        "order": "newest"
    }
    try:
        r = requests.get(base_url, params=params)
        results = r.json().get('results', [])
        keys = ['drug', 'biologic', 'clinical', 'pharmaceutical', 'application']
        return [doc for doc in results if any(k in doc['title'].lower() for k in keys)]
    except:
        return []

def get_ai_insight(client, title):
    """AI analysis using Gemini SDK."""
    prompt = f"Analyze FDA notice: '{title}'. 1. Market Impact (1-10) 2. Key Ticker 3. Trader's Edge (1 sentence)."
    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"AI Analysis paused: {e}"

# --- 4. Automation & Background Scan ---

def run_background_scan():
    """Logic that executes on every page load (for Cron-job automation)."""
    # Access watchlist from session state (assigned by the widget key)
    raw_watchlist = st.session_state.get("watchlist_key", "Pfizer, Moderna, Biogen, Eli Lilly")
    watchlist = [name.strip().lower() for name in raw_watchlist.split(",")]
    
    notices = fetch_drug_notices()
    
    # Track sent notifications in a set to avoid duplicates during one session
    if 'sent_notifications' not in st.session_state:
        st.session_state.sent_notifications = set()

    for doc in notices:
        title = doc['title']
        doc_id = doc.get('document_number', title)
        
        # Check if company is in watchlist
        if any(company in title.lower() for company in watchlist):
            # Check if already notified in the last 24h (via cache logic)
            if doc_id not in st.session_state.sent_notifications:
                send_real_email(title, doc['html_url'])
                st.session_state.sent_notifications.add(doc_id)
                st.toast(f"Passive Alert Sent: {title[:30]}...")

# --- 5. User Interface ---

st.title("💊 BioMarket Edge AI")
st.sidebar.title("🛠️ Control Panel")

# Assign widget to a key so it's accessible via session_state
st.sidebar.text_area(
    "Watchlist (comma separated):", 
    "Pfizer, Moderna, Biogen, Eli Lilly", 
    key="watchlist_key"
)

test_mode = st.sidebar.toggle("🧪 Enable Test Mode")

# AUTO-SCAN: This runs every time the cron-job (or a user) pings the URL
if secrets_ready:
    run_background_scan()
else:
    st.sidebar.error("Secrets missing! Check Streamlit Dashboard Settings.")

# MANUAL VIEW: Display for the user
if st.button("Manual Refresh Dashboard"):
    notices = fetch_drug_notices()
    if test_mode:
        notices = [{"title": "Advisory Committee Meeting: Pfizer Alzheimer Drug NDA", "publication_date": "2025-12-27", "html_url": "https://example.com"}]
    
    if notices:
        client = genai.Client(api_key=API_KEY) if secrets_ready else None
        for doc in notices:
            with st.expander(f"📋 {doc['title']}"):
                st.write(f"**Date:** {doc.get('publication_date')}")
                st.link_button("View Document", doc['html_url'])
                if client:
                    st.info(get_ai_insight(client, doc['title']))
    else:
        st.info("No current notices found.")


# In[ ]:




