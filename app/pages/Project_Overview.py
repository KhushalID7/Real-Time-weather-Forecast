import streamlit as st

st.set_page_config(
    page_title="Project Overview | Weather ML",
    layout="wide"
)

st.title("Project Overview — Real-Time Weather Forecasting System")

st.markdown("""
##  What This System Does

This project is a **real-time machine learning system** that predicts  
**temperature one hour into the future** using live weather data.

It is built with:
- Kafka for streaming
- MongoDB for storage
- Continuous model retraining
- Drift monitoring
- Streamlit for observability


##  Why Some Pages May Look Empty Sometimes

This system performs **true forecasting**, not instant prediction.

That means:

1. A prediction is generated for a *future timestamp*
2. The real temperature is only known **after that time passes**
3. Evaluation metrics (MAE, actual vs predicted) appear later

This delay is **intentional and correct**.



##  Live Monitoring Page

Shows:
- System activity
- Prediction generation
- Health indicators

It may **not** show evaluation metrics immediately.


##  Historical Performance Page

Shows:
- Only predictions that already have ground truth
- Prediction vs Actual graphs
- Rolling MAE

This page always reflects **validated performance**.


##  Why This Design Matters

This separation:
- Prevents misleading metrics
- Mirrors real production ML systems
- Makes system behavior transparent

Many demo systems fake evaluation.
This system does **not**.


##  Production-Readiness

The system includes:
- Automatic backfilling of ground truth
- Drift detection
- Retraining triggers
- Data retention for MongoDB free tier


###  Status
If you see predictions but no MAE yet —  
**the system is working exactly as intended.**
""")
