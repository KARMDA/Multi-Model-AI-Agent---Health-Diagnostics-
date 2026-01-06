'''from utils.table_extractor import extract_from_lab_table

def extract_parameters_node(state):
    text = state.raw_text or ""
    if not text.strip():
        return {
            "extracted_params": {},
            "errors": state.errors + ["No text to extract from."]
        }

    extracted = extract_from_lab_table(text)

    return {
        "extracted_params": extracted,
        "patient_info": {}
    }'''
