import streamlit as st
import pandas as pd
import io
import json
from ocr_engine import extract_text_from_file
from parser import parse_blood_report
from validator import validate_parameters
from interpreter import interpret_results
from csv_converter import json_to_ml_csv

st.set_page_config(page_title="Blood Report Analyzer", layout="wide")

st.title("Blood Report Analyzer – Milestone 1")
st.markdown("Analyzes blood test reports and provides interpretations.")

st.divider()

uploaded_file = st.file_uploader(
    "Upload your medical report",
    type=["pdf", "png", "jpg", "jpeg", "json", "csv"],
    help="Supported: PDF, PNG, JPG, JPEG, JSON, CSV"
)

if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    with st.spinner("Processing..."):
        try:
            # Data Ingestion - Format-specific processing
            st.subheader("📄 Step 1: Data Ingestion")
            ingestion_result = extract_text_from_file(uploaded_file)
            
            # Parse ingestion result
            try:
                result_data = json.loads(ingestion_result)
                
                # Handle different file types
                if "file_type" in result_data:
                    file_type = result_data["file_type"]
                    
                    if file_type == "CSV":
                        st.success("✅ CSV file detected - returned as-is")
                        st.text_area("CSV Content", result_data["csv_content"], height=200)
                        st.info(result_data["message"])
                        
                        # Skip further processing for CSV
                        st.stop()
                        
                    elif file_type == "JSON":
                        st.success("✅ JSON file detected - parsed directly")
                        st.json(result_data["data"])
                        st.info(result_data["message"])
                        
                        # Skip further processing for JSON
                        st.stop()
                
                # For OCR-processed files with structured format
                if "medical_parameters" in result_data:
                    st.success("✅ OCR and document structuring completed")
                    
                    # Display patient info
                    patient_info = result_data.get("patient_info", {})
                    if any(patient_info.values()):
                        st.subheader("👤 Patient Information")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.write(f"**Name:** {patient_info.get('name', 'N/A')}")
                        with col2:
                            st.write(f"**Age:** {patient_info.get('age', 'N/A')}")
                        with col3:
                            st.write(f"**Sex:** {patient_info.get('sex', 'N/A')}")
                        with col4:
                            st.write(f"**Place:** {patient_info.get('place', 'N/A')}")
                    
                    # Display ignored fields
                    ignored_fields = result_data.get("ignored_fields", [])
                    if ignored_fields:
                        with st.expander(f"📋 Ignored Fields ({len(ignored_fields)} items)"):
                            for field in ignored_fields[:10]:  # Show first 10
                                st.text(field)
                            if len(ignored_fields) > 10:
                                st.caption(f"... and {len(ignored_fields) - 10} more")
                    
                    # Convert medical parameters to parser format
                    extracted_params = result_data["medical_parameters"]
                    parsed_data = {}
                    for param in extracted_params:
                        parsed_data[param["name"]] = {
                            "value": param["value"],
                            "unit": param["unit"],
                            "reference_range": param["reference_range"],
                            "confidence": param["confidence"]
                        }
                
                # For OCR-processed files (old format)
                elif "parameters" in result_data:
                    st.success("✅ OCR and extraction completed")
                    extracted_params = result_data["parameters"]
                    
                    if "raw_text" in result_data:
                        st.text_area("Extracted Text", result_data["raw_text"], height=200)
                    
                    # Convert to parser format
                    parsed_data = {}
                    for param in extracted_params:
                        parsed_data[param["name"]] = {
                            "value": param["value"],
                            "unit": param["unit"],
                            "reference_range": param["reference_range"],
                            "confidence": param["confidence"]
                        }
                else:
                    # Fallback to old format
                    st.text_area("Extracted Text", ingestion_result, height=200)
                    parsed_data = parse_blood_report(ingestion_result)
                    
            except json.JSONDecodeError:
                # Fallback for plain text
                st.text_area("Extracted Text", ingestion_result, height=200)
                parsed_data = parse_blood_report(ingestion_result)
            
            st.caption(f"Processing completed")
            
            st.divider()
            
            # Parse data
            st.subheader("🔍 Step 2: Extracted Parameters")
            if not parsed_data:
                st.warning("No parameters detected. Check if the report format is supported.")
            st.json(parsed_data)
            
            st.divider()
            
            # Validate
            st.subheader("✅ Step 3: Validation")
            validated_data = validate_parameters(parsed_data)
            st.json(validated_data)
            
            st.divider()
            
            # Results
            st.subheader("📊 Step 4: Results")
            interpretation = interpret_results(validated_data)
            
            summary = interpretation["summary"]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", summary["total_parameters"])
            with col2:
                st.metric("Normal", summary["normal"], delta="✓" if summary["normal"] > 0 else None)
            with col3:
                st.metric("Low", summary["low"], delta="⚠" if summary["low"] > 0 else None, delta_color="inverse")
            with col4:
                st.metric("High", summary["high"], delta="⚠" if summary["high"] > 0 else None, delta_color="inverse")
            
            if interpretation["abnormal_parameters"]:
                st.warning("**Abnormal Parameters:**")
                for param in interpretation["abnormal_parameters"]:
                    status_emoji = "🔻" if param["status"] == "LOW" else "🔺"
                    st.write(f"{status_emoji} **{param['parameter']}**: {param['value']} ({param['status']}) - Normal: {param['reference']}")
            
            st.info("**Recommendations:**")
            for rec in interpretation["recommendations"]:
                st.write(f"• {rec}")
            
            st.divider()
            
            # ML-Ready CSV Export Section
            st.subheader("📊 ML-Ready CSV Export")
            
            # Convert OCR JSON to ML CSV format
            ml_csv = json_to_ml_csv(ingestion_result)
            
            # Display CSV preview
            st.write("**ML-Ready CSV Preview:**")
            try:
                df_preview = pd.read_csv(io.StringIO(ml_csv))
                st.dataframe(df_preview, use_container_width=True)
                
                # Download button
                st.download_button(
                    label="📥 Download ML-Ready CSV",
                    data=ml_csv,
                    file_name=f"ml_ready_{uploaded_file.name.split('.')[0]}.csv",
                    mime="text/csv"
                )
                
                # Show raw CSV text
                with st.expander("View Raw ML CSV Data"):
                    st.text(ml_csv)
                    
            except Exception as e:
                st.error(f"Error creating ML CSV: {str(e)}")
                st.text(ml_csv)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please upload a valid blood report.")
else:
    st.info("👆 Upload a report to begin.")
    st.markdown("""
    ### How to use:
    1. Click **Browse files**
    2. Select your blood report
    3. Wait for analysis
    4. Review results
    """)
