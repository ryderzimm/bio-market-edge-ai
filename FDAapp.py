#!/usr/bin/env python
# coding: utf-8

# In[11]:


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

# --- 2. Sidebar: Auth & Notifications ---
st.sidebar.title("🛠️ Control Panel")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

with st.sidebar.expander("📧 Notification Settings"):
    enable_email = st.checkbox("Enable Email Alerts")
    sender_email = st.text_input("Sender Gmail", placeholder="yourbot@gmail.com")
    app_password = st.text_input("Gmail App Password", type="password")
    receiver_email = st.text_input("Alert Recipient", placeholder="you@example.com")

st.sidebar.divider()
st.sidebar.subheader("🎯 Watchlist")
watchlist_input = st.sidebar.text_area("Alert on these names:", "Pfizer, Moderna, Biogen, Eli Lilly")
watchlist = [name.strip().lower() for name in watchlist_input.split(",")]
test_mode = st.sidebar.toggle("🧪 Enable Test Mode")

# --- 3. Notification Logic ---

def send_real_email(title, link):
    """Sends a real email alert via Gmail SMTP."""
    if not (sender_email and app_password and receiver_email):
        st.error("Email settings incomplete!")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"🚨 BIOMARKET HIT: {title[:30]}..."
    
    body = f"A high-value FDA notice was detected:\n\nTitle: {title}\nLink: {link}\n\nCheck your prediction market odds immediately."
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        st.toast("Email Alert Sent Successfully!", icon="📧")
    except Exception as e:
        st.error(f"Email failed: {e}")

# --- 4. Main UI Logic ---

def fetch_notices():
    if test_mode:
        return [{"title": "Advisory Committee: New Drug Application for Pfizer Oncology", "publication_date": "2025-12-27", "html_url": "https://www.federalregister.gov"}]
    
    # Real API Fetch logic
    params = {"conditions[agency_ids][]": [164], "conditions[type][]": "NOTICE", "conditions[term]": "CDER drug advisory", "order": "newest"}
    try:
        r = requests.get("https://www.federalregister.gov/api/v1/documents.json", params=params)
        return r.json().get('results', [])
    except: return []

st.title("💊 BioMarket Edge AI")
if st.button("🔎 Scan & Alert"):
    notices = fetch_notices()
    if notices:
        client = genai.Client(api_key=api_key) if api_key else None
        for doc in notices[:5]:
            title = doc['title']
            is_hit = any(company in title.lower() for company in watchlist)
            
            if is_hit:
                st.toast(f"🚨 Watchlist Hit: {title[:40]}", icon="🔥")
                if enable_email: send_real_email(title, doc['html_url'])
            
            with st.expander(f"{'🚨 ' if is_hit else '📋 '}{title}"):
                st.write(f"**Date:** {doc['publication_date']}")
                st.link_button("View Document", doc['html_url'])
    else:
        st.info("No current notices found. Use Test Mode to verify your alerts.")


# In[ ]:




