
import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

APP_NAME = "MediGuide AI"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🩺",
    layout="wide"
)

# -------------------- AI CONFIGURATION --------------------

SYSTEM_PROMPT = """
You are MediGuide AI, an educational health information assistant.

Rules:
1. Never claim to diagnose a patient.
2. Do not prescribe medicines or provide medication doses.
3. Explain possible causes as possibilities, not confirmed conditions.
4. Encourage consultation with a qualified healthcare professional.
5. If symptoms suggest a potentially life-threatening emergency,
   advise immediate local emergency medical help.
6. Do not invent patient information.
7. Respond in the language requested by the user.
8. Return a valid JSON object only, using this structure:

{
  "summary": "Short symptom summary",
  "general_information": "General educational information",
  "possible_conditions": [
    {"name": "Possible cause", "reason": "Explanation"}
  ],
  "urgency_level": "LOW, MEDIUM, HIGH, or EMERGENCY",
  "recommended_next_steps": ["Step 1", "Step 2"],
  "questions_for_doctor": ["Question 1", "Question 2"],
  "warning_signs": ["Warning sign 1", "Warning sign 2"]
}
"""

# -------------------- HELPER FUNCTIONS --------------------

def get_ai_response(patient_data):
    """Send patient information to OpenAI and return parsed JSON."""

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key == "your_openai_api_key_here":
        raise ValueError(
            "OpenAI API key is missing. Add your key to the .env file."
        )

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Provide educational symptom guidance for the following "
                    "patient information. Do not diagnose.\n\n"
                    + json.dumps(patient_data, ensure_ascii=False)
                ),
            },
        ],
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The AI returned an empty response.")

    result = json.loads(content)

    required_keys = [
        "summary",
        "general_information",
        "possible_conditions",
        "urgency_level",
        "recommended_next_steps",
        "questions_for_doctor",
        "warning_signs",
    ]

    for key in required_keys:
        if key not in result:
            raise ValueError(f"The AI response is missing: {key}")

    allowed_levels = {"LOW", "MEDIUM", "HIGH", "EMERGENCY"}
    result["urgency_level"] = str(
        result["urgency_level"]
    ).upper()

    if result["urgency_level"] not in allowed_levels:
        result["urgency_level"] = "MEDIUM"

    return result


def display_list(items):
    """Display a list of AI-generated recommendations."""
    if not isinstance(items, list) or not items:
        st.write("No information provided.")
        return

    for item in items:
        if isinstance(item, dict):
            name = item.get("name", "Possible explanation")
            reason = item.get("reason", "")
            st.markdown(f"**{name}**")
            st.write(reason)
        else:
            st.markdown(f"- {item}")


# -------------------- APPLICATION INTERFACE --------------------

st.title("🩺 MediGuide AI")
st.subheader("Understand your symptoms and prepare for a healthcare visit.")

st.info(
    "This application provides educational information only. "
    "It cannot diagnose illness or replace professional medical care."
)

with st.sidebar:
    st.header("About MediGuide AI")
    st.write("AI-assisted educational symptom guidance.")
    st.write("Model:", MODEL)

    st.warning(
        "If you have severe chest pain, serious difficulty breathing, "
        "signs of stroke, loss of consciousness, or another possible "
        "medical emergency, seek emergency help immediately."
    )

st.header("Patient Information")

with st.form("patient_form"):
    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input(
            "Patient age",
            min_value=0,
            max_value=120,
            value=25,
            step=1
        )

        gender = st.selectbox(
            "Gender",
            [
                "Prefer not to say",
                "Female",
                "Male",
                "Non-binary",
                "Other"
            ]
        )

        duration = st.selectbox(
            "How long have you had symptoms?",
            [
                "Started today",
                "1–3 days",
                "4–7 days",
                "1–2 weeks",
                "More than 2 weeks",
                "Unsure"
            ]
        )

    with col2:
        severity = st.slider(
            "Symptom severity (1 = mild, 10 = severe)",
            min_value=1,
            max_value=10,
            value=3
        )

        language = st.selectbox(
            "Response language",
            ["English", "Urdu"]
        )

    symptoms = st.multiselect(
        "Select your symptoms",
        [
            "Fever",
            "Cough",
            "Runny nose",
            "Sore throat",
            "Headache",
            "Body aches",
            "Fatigue",
            "Nausea",
            "Vomiting",
            "Diarrhea",
            "Abdominal pain",
            "Chest pain",
            "Shortness of breath",
            "Dizziness",
            "Skin rash",
            "Joint pain",
            "Back pain",
            "Chills",
            "Other"
        ]
    )

    other_symptoms = st.text_area(
        "Describe other symptoms",
        placeholder="Enter any additional symptoms..."
    )

    conditions = st.text_area(
        "Existing medical conditions (optional)",
        placeholder="Enter known conditions, if any..."
    )

    medications = st.text_area(
        "Current medications (optional)",
        placeholder="Enter medication names, if relevant..."
    )

    notes = st.text_area(
        "Additional information (optional)",
        placeholder="When symptoms began or other relevant context..."
    )

    submitted = st.form_submit_button(
        "Assess Symptoms",
        type="primary",
        use_container_width=True
    )

# -------------------- PROCESS ASSESSMENT --------------------

if submitted:
    all_symptoms = list(symptoms)

    if other_symptoms.strip():
        all_symptoms.append(other_symptoms.strip())

    if not all_symptoms:
        st.error("Please select or describe at least one symptom.")

    else:
        patient_data = {
            "age": age,
            "gender": gender,
            "symptoms": all_symptoms,
            "duration": duration,
            "severity": severity,
            "existing_conditions": conditions.strip() or "Not provided",
            "current_medications": medications.strip() or "Not provided",
            "additional_notes": notes.strip() or "Not provided",
            "response_language": language,
        }

        try:
            with st.spinner("Preparing your educational guidance..."):
                result = get_ai_response(patient_data)

            st.session_state["assessment_result"] = result

        except Exception as error:
            st.error("The assessment could not be completed.")

            with st.expander("Technical details"):
                st.code(str(error))

            st.info(
                "Check your API key, internet connection, model name, "
                "and installed packages."
            )

# -------------------- DISPLAY RESULTS --------------------

result = st.session_state.get("assessment_result")

if result:
    st.divider()
    st.header("Your Guidance Dashboard")

    urgency = result["urgency_level"]

    if urgency == "EMERGENCY":
        st.error(
            "POSSIBLE EMERGENCY: Seek immediate emergency medical help. "
            "Do not wait for further AI guidance."
        )
    elif urgency == "HIGH":
        st.error(
            "Prompt professional medical assessment is recommended."
        )
    elif urgency == "MEDIUM":
        st.warning(
            "Consider consulting a healthcare professional, "
            "especially if symptoms persist or worsen."
        )
    else:
        st.success(
            "Seek professional advice if you are concerned or "
            "your symptoms change."
        )

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Urgency guidance", urgency)

    with col2:
        st.metric(
            "Possible causes listed",
            len(result.get("possible_conditions", []))
        )

    st.subheader("Symptom Summary")
    st.write(result["summary"])

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "General Information",
            "Next Steps",
            "Ask Your Doctor",
            "Warning Signs"
        ]
    )

    with tab1:
        st.subheader("Possible Causes")
        st.caption(
            "These are educational possibilities, not confirmed diagnoses."
        )
        display_list(result["possible_conditions"])

        st.subheader("General Information")
        st.write(result["general_information"])

    with tab2:
        st.subheader("Recommended Next Steps")
        display_list(result["recommended_next_steps"])

    with tab3:
        st.subheader("Questions for Your Healthcare Professional")
        display_list(result["questions_for_doctor"])

    with tab4:
        st.subheader("Warning Signs")
        display_list(result["warning_signs"])

        st.warning(
            "Seek emergency help for severe or potentially "
            "life-threatening symptoms."
        )

    st.download_button(
        label="Download Guidance as JSON",
        data=json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ),
        file_name="mediguide_guidance.json",
        mime="application/json"
    )

st.divider()

st.caption(
    "MediGuide AI | Educational prototype | "
    "Not a substitute for professional medical care."
)
