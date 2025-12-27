#!/usr/bin/env python
# coding: utf-8

# In[13]:


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

# Custom CSS for Watchlist Highlighting
st.markdown("""
    <style>
    .watchlist-hit { border: 2px solid #ff4b4b; background-color: #fff1f1; padding: 10px; border-radius: 10px; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Security: Access Secrets ---
# These must be set in your Streamlit Cloud Settings -> Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    RECEIVER_EMAIL = st.secrets["RECEIVER_EMAIL"]
    secrets_loaded = True
except Exception:
    secrets_loaded = False

# --- 3. Sidebar: Settings & Watchlist ---
st.sidebar.title("🛠️ BioMarket Control")

# Watchlist Management
st.sidebar.subheader("🎯 Company Watchlist")
watchlist_input = st.sidebar.text_area("Alert on these (comma separated):", "Pfizer, Moderna, Biogen, Eli Lilly")
watchlist = [name.strip().lower() for name in watchlist_input.split(",")]

# Testing & Alerts
st.sidebar.divider()
test_mode = st.sidebar.toggle("🧪 Enable Test Mode", help="Simulates a Pfizer notice to verify alerts.")
enable_email = st.sidebar.toggle("📧 Enable Email Alerts", value=True)

if not secrets_loaded:
    st.sidebar.warning("⚠️ Secrets not found in Streamlit Cloud Settings. Alerts will fail.")

# --- 4. Core Functions ---

def send_real_email(title, link):
    """Sends a real email alert via Gmail SMTP using Secrets."""
    if not secrets_loaded: return
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"🚨 BIOMARKET HIT: {title[:40]}..."
    
    body = f"High-value FDA notice detected:\n\nTitle: {title}\nLink: {link}\n\nReview prediction markets immediately."
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        st.toast("Email Alert Sent!", icon="📧")
    except Exception as e:
        st.error(f"Email Error: {e}")

def fetch_drug_notices():
    """Fetches FDA sub-agency notices (CDER/CBER)."""
    if test_mode:
        return [{"title": "Advisory Committee: New Drug Application for Pfizer's Oncology Pipeline", 
                 "publication_date": "2025-12-27", 
                 "html_url": "https://www.federalregister.gov"}]
    
    base_url = "https://www.federalregister.gov/api/v1/documents.json"
    params = {"conditions[agency_ids][]": [164], "conditions[type][]": "NOTICE", 
              "conditions[term]": "CDER CBER drug advisory", "order": "newest"}
    try:
        r = requests.get(base_url, params=params)
        data = r.json()
        results = data.get('results', [])
        # Final keyword safety gate
        keys = ['drug', 'biologic', 'clinical', 'pharmaceutical', 'application']
        return [doc for doc in results if any(k in doc['title'].lower() for k in keys)]
    except: return []

def get_ai_insight(client, title):
    """AI analysis using Gemini 2.0 Flash."""
    prompt = f"Analyze FDA notice: '{title}'. 1. Market Impact (1-10) 2. Key Ticker 3. Trader's Edge (1 sentence)."
    try:
        # 2025 Google GenAI SDK syntax
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"AI Analysis paused: {e}"

# --- 5. Main UI Logic ---

st.title("💊 BioMarket Edge AI")
st.caption("Monitoring Federal Register for mispriced Biotech milestones.")

if st.button("🔎 Scan for Milestones"):
    notices = fetch_drug_notices()
    
    if notices:
        # Initialize Gemini Client if API key exists
        client = genai.Client(api_key=API_KEY) if secrets_loaded else None
        
        for doc in notices[:5]:
            title = doc['title']
            is_hit = any(company in title.lower() for company in watchlist)
            
            box_style = "watchlist-hit" if is_hit else ""
            
            if is_hit:
                st.toast(f"🚨 Watchlist Match: {title[:50]}", icon="🔥")
                if enable_email and secrets_loaded:
                    send_real_email(title, doc['html_url'])
            
            st.markdown(f'<div class="{box_style}">', unsafe_allow_html=True)
            with st.expander(f"{'🚨 WATCHLIST: ' if is_hit else '📋 '}{title}"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.write(f"**Published:** {doc['publication_date']}")
                    st.link_button("View Legal Document", doc['html_url'])
                with c2:
                    if client:
                        time.sleep(1) # Rate limiting
                        st.info(get_ai_insight(client, title))
            st.markdown('</div>', unsafe_allow_html=True)
            st.write("")
    else:
        st.info("No drug notices found today. Try 'Test Mode' to verify your alerts.")


# In[ ]:




