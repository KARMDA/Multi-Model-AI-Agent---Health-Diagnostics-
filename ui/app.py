"""
Health Diagnostics UI - Streamlit Application
Refactored to use FastAPI endpoints only via httpx, no direct pipeline imports.
"""

import streamlit as st
import httpx
import json
import time
import os
import uuid
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px

# ============================================================================
# Configuration
# ============================================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
POLLING_INTERVAL = 3  # seconds
MAX_POLLING_ATTEMPTS = 60  # 3 minutes max


# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state keys."""
    if "report_id" not in st.session_state:
        st.session_state.report_id = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "current_report" not in st.session_state:
        st.session_state.current_report = None
    if "user_context" not in st.session_state:
        st.session_state.user_context = {
            "age": None,
            "gender": None,
            "lifestyle": None,
            "medical_history": None,
        }


init_session_state()


# ============================================================================
# API Client Functions
# ============================================================================

def upload_report(file_content: bytes, filename: str, user_id: Optional[str] = None) -> Optional[str]:
    """
    Upload and analyze a blood report file.

    Args:
        file_content: Binary file content
        filename: Original filename
        user_id: Optional user identifier

    Returns:
        Report ID if successful, None on error
    """
    try:
        with st.spinner("📤 Uploading file..."):
            files = {"file": (filename, file_content)}
            params = {}
            if user_id:
                params["user_id"] = user_id

            response = httpx.post(
                f"{API_BASE_URL}/analyze",
                files=files,
                params=params,
                timeout=60.0,
            )

            if response.status_code == 200:
                data = response.json()
                report_id = data.get("report_id")
                st.success(f"✓ File uploaded successfully! Report ID: {report_id}")
                return report_id
            else:
                error_msg = response.json().get("detail", "Unknown error")
                st.error(f"❌ Upload failed: {error_msg}")
                return None

    except httpx.ConnectError:
        st.error("❌ Cannot connect to API server. Is it running on " + API_BASE_URL + "?")
        return None
    except httpx.TimeoutException:
        st.error("❌ Upload timed out. Please try again with a smaller file.")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error during upload: {str(e)}")
        return None


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a report by ID.

    Args:
        report_id: UUID of the report

    Returns:
        Report data if found, None on error or not found
    """
    try:
        response = httpx.get(f"{API_BASE_URL}/report/{report_id}", timeout=10.0)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            st.warning(f"⚠ Server error: {response.json().get('detail', 'Unknown error')}")
            return None

    except httpx.ConnectError:
        st.warning("⚠ Cannot connect to API server")
        return None
    except httpx.TimeoutException:
        st.warning("⚠ Request timed out")
        return None
    except Exception as e:
        st.warning(f"⚠ Error retrieving report: {str(e)}")
        return None


def poll_report_completion(report_id: str, max_attempts: int = MAX_POLLING_ATTEMPTS) -> Optional[Dict[str, Any]]:
    """
    Poll for report completion every POLLING_INTERVAL seconds.

    Args:
        report_id: UUID of the report
        max_attempts: Maximum polling attempts

    Returns:
        Completed report data, None if max attempts exceeded
    """
    attempt = 0
    progress_bar = st.progress(0)

    while attempt < max_attempts:
        report = get_report(report_id)

        if report:
            progress = min((attempt / max_attempts) * 100, 99)
            progress_bar.progress(progress)
            return report

        attempt += 1
        progress = (attempt / max_attempts) * 100
        progress_bar.progress(min(progress, 99))

        if attempt < max_attempts:
            time.sleep(POLLING_INTERVAL)

    st.error(f"❌ Report processing timed out after {max_attempts * POLLING_INTERVAL} seconds")
    return None


def send_chat_message(report_id: str, message: str, user_id: Optional[str] = None) -> Optional[str]:
    """
    Send a chat message about a report.

    Args:
        report_id: UUID of the report
        message: Chat message content
        user_id: Optional user identifier

    Returns:
        AI response if successful, None on error
    """
    try:
        payload = {
            "report_id": report_id,
            "message": message,
        }
        if user_id:
            payload["user_id"] = user_id

        response = httpx.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("message")
        else:
            error_msg = response.json().get("detail", "Unknown error")
            st.error(f"❌ Chat failed: {error_msg}")
            return None

    except httpx.ConnectError:
        st.error("❌ Cannot connect to API server")
        return None
    except httpx.TimeoutException:
        st.error("❌ Chat request timed out")
        return None
    except Exception as e:
        st.error(f"❌ Chat error: {str(e)}")
        return None


def get_user_reports(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Retrieve all reports for a user.

    Args:
        user_id: UUID of the user

    Returns:
        List of reports if successful, None on error
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/reports/user/{user_id}",
            timeout=10.0,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("reports", [])
        else:
            st.warning(f"⚠ Error retrieving reports: {response.json().get('detail', 'Unknown error')}")
            return None

    except httpx.ConnectError:
        st.warning("⚠ Cannot connect to API server")
        return None
    except httpx.TimeoutException:
        st.warning("⚠ Request timed out")
        return None
    except Exception as e:
        st.warning(f"⚠ Error: {str(e)}")
        return None


# ============================================================================
# Report Formatting Functions
# ============================================================================

def format_report_markdown(report: Dict[str, Any]) -> str:
    """
    Format report data as Markdown for display.

    Args:
        report: Report data dictionary

    Returns:
        Formatted Markdown string
    """
    lines = []

    # Header
    lines.append("# 📋 Blood Report Analysis")
    lines.append("")

    # Metadata
    analysis = report.get("analysis", {})
    lines.append("## Report Information")
    lines.append(f"- **Report ID:** `{report.get('report_id', 'N/A')}`")
    lines.append(f"- **File:** {report.get('file_name', 'N/A')}")
    lines.append(f"- **Analysis Date:** {report.get('created_at', 'N/A')}")
    lines.append("")

    # Summary
    summary = analysis.get("summary", {})
    if summary:
        lines.append("## Summary")
        for key, value in summary.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    # Parameters
    parameters = analysis.get("parameters", {})
    if parameters:
        lines.append("## Blood Parameters")
        lines.append("| Parameter | Value | Unit | Status | Reference Range |")
        lines.append("|-----------|-------|------|--------|-----------------|")

        for param_name, param_data in parameters.items():
            if isinstance(param_data, dict):
                value = param_data.get("value", "N/A")
                unit = param_data.get("unit", "")
                status = param_data.get("status", "UNKNOWN")
                ref_range = param_data.get("reference_range", "N/A")
                lines.append(f"| {param_name} | {value} | {unit} | {status} | {ref_range} |")

        lines.append("")

    # Abnormal Parameters
    abnormal = analysis.get("abnormal_parameters", [])
    if abnormal:
        lines.append("## ⚠ Abnormal Parameters")
        for item in abnormal:
            param = item.get("parameter", "Unknown")
            status = item.get("status", "Unknown")
            lines.append(f"- **{param}:** {status}")
        lines.append("")

    # Recommendations
    recommendations = analysis.get("recommendations", [])
    if recommendations:
        lines.append("## 💡 Recommendations")
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    # Risk Assessment
    risks = report.get("risks", [])
    if risks:
        lines.append("## 🔴 Health Risks")
        for risk in risks:
            if isinstance(risk, dict):
                condition = risk.get("condition", "Unknown")
                level = risk.get("risk_level", "Unknown")
                confidence = risk.get("confidence", 0)
                lines.append(f"- **{condition}:** {level} (Confidence: {confidence*100:.0f}%)")
        lines.append("")

    return "\n".join(lines)


def create_parameters_chart(report: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Create a chart of blood parameters.

    Args:
        report: Report data dictionary

    Returns:
        Plotly figure or None if no data
    """
    try:
        parameters = report.get("analysis", {}).get("parameters", {})

        if not parameters:
            return None

        param_names = []
        param_values = []
        param_status = []
        status_colors = {"NORMAL": "green", "UNKNOWN": "gray", "LOW": "orange", "HIGH": "red", "CRITICAL": "darkred"}

        for name, data in parameters.items():
            if isinstance(data, dict):
                param_names.append(name)
                param_values.append(data.get("value", 0))
                status = data.get("status", "UNKNOWN")
                param_status.append(status_colors.get(status, "gray"))

        fig = go.Figure(
            data=[
                go.Bar(
                    x=param_names,
                    y=param_values,
                    marker=dict(color=param_status),
                    text=param_values,
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title="Blood Parameters Overview",
            xaxis_title="Parameter",
            yaxis_title="Value",
            hovermode="x unified",
            height=400,
        )

        return fig

    except Exception as e:
        st.warning(f"Could not create chart: {str(e)}")
        return None


def create_trends_chart(reports: List[Dict[str, Any]], parameter: str) -> Optional[go.Figure]:
    """
    Create a time-series chart for a specific parameter across reports.

    Args:
        reports: List of report dictionaries
        parameter: Parameter name to track

    Returns:
        Plotly figure or None if no data
    """
    try:
        dates = []
        values = []

        for report in reports:
            created_at = report.get("created_at")
            analysis = report.get("analysis", {})
            parameters = analysis.get("parameters", {})

            for param_name, param_data in parameters.items():
                if parameter.lower() in param_name.lower():
                    if isinstance(param_data, dict):
                        try:
                            dates.append(datetime.fromisoformat(created_at.replace("Z", "+00:00")))
                            values.append(param_data.get("value", 0))
                        except Exception:
                            pass

        if not dates or not values:
            return None

        # Sort by date
        sorted_data = sorted(zip(dates, values), key=lambda x: x[0])
        dates, values = zip(*sorted_data)

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=dates,
                    y=values,
                    mode="lines+markers",
                    name=parameter,
                    line=dict(color="steelblue", width=2),
                    marker=dict(size=8),
                )
            ]
        )

        fig.update_layout(
            title=f"{parameter} Trend Over Time",
            xaxis_title="Date",
            yaxis_title="Value",
            hovermode="x unified",
            height=400,
        )

        return fig

    except Exception as e:
        st.warning(f"Could not create trend chart: {str(e)}")
        return None


# ============================================================================
# Page Functions
# ============================================================================

def page_upload():
    """Upload page - file upload and user context collection."""
    st.title("📤 Upload Blood Report")

    with st.form("upload_form"):
        st.subheader("Blood Report File")
        uploaded_file = st.file_uploader(
            "Choose a file (PDF, PNG, JPG, JSON, CSV)",
            type=["pdf", "png", "jpg", "jpeg", "json", "csv", "txt"],
        )

        st.subheader("Demographic Information (Optional)")
        age = st.number_input("Age", min_value=0, max_value=150, value=None)
        gender = st.selectbox("Gender", ["Not specified", "Male", "Female", "Other"])
        lifestyle = st.multiselect(
            "Lifestyle",
            ["Sedentary", "Light Exercise", "Moderate Exercise", "Very Active", "Athlete"],
        )
        medical_history = st.text_area(
            "Medical History",
            placeholder="Any relevant medical conditions, allergies, or medications...",
        )

        submitted = st.form_submit_button("🔍 Analyze Report", use_container_width=True)

        if submitted:
            if not uploaded_file:
                st.error("❌ Please select a file")
            else:
                # Store user context
                st.session_state.user_context = {
                    "age": age,
                    "gender": gender if gender != "Not specified" else None,
                    "lifestyle": lifestyle,
                    "medical_history": medical_history if medical_history else None,
                }

                # Upload file
                file_content = uploaded_file.read()
                report_id = upload_report(
                    file_content,
                    uploaded_file.name,
                    user_id=st.session_state.user_id,
                )

                if report_id:
                    st.session_state.report_id = report_id
                    st.success("✓ Report uploaded! Navigating to results...")
                    st.balloons()
                    time.sleep(1)
                    st.switch_page("pages/02_Results.py")


def page_results():
    """Results page - display report with polling for completion."""
    st.title("📊 Analysis Results")

    if not st.session_state.report_id:
        st.warning("⚠ No report selected. Please upload a report first.")
        if st.button("← Back to Upload"):
            st.switch_page("pages/01_Upload.py")
        return

    report_id = st.session_state.report_id

    # Display report info
    st.info(f"Report ID: `{report_id}`")

    # Try to get report
    with st.spinner("⏳ Fetching report..."):
        report = get_report(report_id)

    if not report:
        st.warning("⚠ Report not found. It may still be processing...")
        if st.button("🔄 Refresh"):
            st.rerun()
        return

    # Store in session
    st.session_state.current_report = report

    # Display formatted report
    markdown_report = format_report_markdown(report)
    st.markdown(markdown_report)

    # Display chart
    chart = create_parameters_chart(report)
    if chart:
        st.plotly_chart(chart, use_container_width=True)

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💬 Chat About This Report"):
            st.switch_page("pages/03_Chat.py")
    with col2:
        if st.button("📈 View Trends"):
            st.switch_page("pages/04_Trends.py")
    with col3:
        if st.button("📤 Upload Another Report"):
            st.session_state.report_id = None
            st.switch_page("pages/01_Upload.py")


def page_chat():
    """Chat page - interactive Q&A about the current report."""
    st.title("💬 Chat About Your Report")

    if not st.session_state.report_id:
        st.warning("⚠ No report selected. Please upload a report first.")
        if st.button("← Back to Upload"):
            st.switch_page("pages/01_Upload.py")
        return

    # Display current report summary
    with st.expander("📄 Report Summary", expanded=False):
        if st.session_state.current_report:
            analysis = st.session_state.current_report.get("analysis", {})
            summary = analysis.get("summary", {})
            if summary:
                for key, value in summary.items():
                    st.write(f"**{key}:** {value}")
            else:
                st.write("No summary available")

    # Chat history display
    st.subheader("Conversation")
    chat_container = st.container(height=400, border=True)

    with chat_container:
        for msg in st.session_state.chat_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                st.markdown(f"**🧑 You:** {content}")
            else:
                st.markdown(f"**🤖 Assistant:** {content}")

    # Chat input
    st.subheader("Ask a Question")
    user_message = st.text_input(
        "Your question (minimum 3 characters):",
        placeholder="What does my hemoglobin level mean?",
        label_visibility="collapsed",
    )

    if st.button("Send Message", use_container_width=True):
        if not user_message or len(user_message.strip()) < 3:
            st.error("❌ Please enter at least 3 characters")
        else:
            with st.spinner("⏳ Getting response..."):
                response = send_chat_message(
                    st.session_state.report_id,
                    user_message,
                    user_id=st.session_state.user_id,
                )

            if response:
                # Add to chat history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                st.rerun()

    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Results"):
            st.switch_page("pages/02_Results.py")
    with col2:
        if st.button("📈 View Trends →"):
            st.switch_page("pages/04_Trends.py")


def page_trends():
    """Trends page - view parameter trends over time."""
    st.title("📈 Your Report Trends")

    user_id = st.session_state.user_id

    # Fetch user reports
    with st.spinner("⏳ Loading your reports..."):
        reports = get_user_reports(user_id)

    if not reports:
        st.warning("⚠ No reports found for your account")
        if st.button("← Upload a Report"):
            st.switch_page("pages/01_Upload.py")
        return

    st.info(f"📊 You have {len(reports)} report(s)")

    # Reports table
    st.subheader("Your Reports")

    # Convert to DataFrame for display
    table_data = []
    for report in reports:
        table_data.append({
            "Report ID": report.get("report_id", "N/A")[:8] + "...",
            "File": report.get("file_name", "Unknown"),
            "Created": report.get("created_at", "N/A")[:10],
            "Abnormal Count": report.get("abnormal_count", 0),
            "Total Parameters": report.get("total_parameters", 0),
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Parameter trend selection
    st.subheader("Parameter Trends")

    # Extract all unique parameters from reports
    parameters = set()
    for report in reports:
        analysis = report.get("analysis", {})
        params = analysis.get("parameters", {})
        for param_name in params.keys():
            parameters.add(param_name)

    parameters = sorted(list(parameters))

    if not parameters:
        st.warning("⚠ No parameters found in your reports")
    else:
        selected_param = st.selectbox(
            "Select a parameter to view trends:",
            parameters,
        )

        if selected_param:
            chart = create_trends_chart(reports, selected_param)
            if chart:
                st.plotly_chart(chart, use_container_width=True)
            else:
                st.info("ℹ Not enough data to display trend for this parameter")

    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Results"):
            st.switch_page("pages/02_Results.py")
    with col2:
        if st.button("📤 Upload New Report →"):
            st.session_state.report_id = None
            st.switch_page("pages/01_Upload.py")


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Health Diagnostics",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar
    st.sidebar.title("🏥 Health Diagnostics AI")
    st.sidebar.markdown("---")

    # User info
    st.sidebar.info(f"👤 User ID: `{st.session_state.user_id[:8]}...`")

    # API status
    try:
        response = httpx.get(f"{API_BASE_URL.rsplit('/api', 1)[0]}/health", timeout=2.0)
        status = "✓ Online" if response.status_code == 200 else "⚠ Error"
        st.sidebar.success(f"🔗 API: {status}")
    except Exception:
        st.sidebar.warning("🔗 API: ⚠ Offline")

    st.sidebar.markdown("---")

    # Report info
    if st.session_state.report_id:
        st.sidebar.write(f"**Current Report:** `{st.session_state.report_id[:8]}...`")
    else:
        st.sidebar.write("**No active report**")

    # Navigation
    st.sidebar.markdown("---")
    st.sidebar.subheader("Navigation")

    page = st.sidebar.radio(
        "Go to page:",
        ["Upload", "Results", "Chat", "Trends"],
        label_visibility="collapsed",
    )

    # Route to page
    if page == "Upload":
        page_upload()
    elif page == "Results":
        if st.session_state.report_id:
            page_results()
        else:
            st.warning("⚠ No report selected. Please upload a report first.")
            st.switch_page("pages/01_Upload.py")
    elif page == "Chat":
        if st.session_state.report_id:
            page_chat()
        else:
            st.warning("⚠ No report selected. Please upload a report first.")
            st.switch_page("pages/01_Upload.py")
    elif page == "Trends":
        page_trends()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.write("**API Base URL:**")
    st.sidebar.code(API_BASE_URL)


if __name__ == "__main__":
    main()
