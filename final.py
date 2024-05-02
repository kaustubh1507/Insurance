import streamlit as st
import pickle
import pandas as pd
import lime
from lime.lime_tabular import LimeTabularExplainer

# Load the models and data
with open('pages/linear_regr_model.pkl', 'rb') as f:
    linear_regr_model = pickle.load(f)
with open('pages/decision_tree_pipeline_pre_1.2.2', 'rb') as f1:
    fraud_detection = pickle.load(f1)
with open('pages/encoded_values.pkl', 'rb') as file:
    encoded_values = pickle.load(file)
with open('pages/gb_model.pkl', 'rb') as file:
    gbpipeline = pickle.load(file)
with open('pages/flagel.pkl', 'rb') as f:
    flagel = pickle.load(f)


feature_names_mapping = {
    'premium': 'Premium',
    'AgeOfVehicle': 'Age of Vehicle',
    'AgentType': 'Agent Type',
    'PastNumberOfClaims': 'Past Number of Claims',
    'VehiclePrice': 'Vehicle Price',
    'DriverRating': 'Driver Rating',
    'NumberOfSuppliments': 'Number of Suppliments',
    'Fault': 'Fault',
    'AddressChange_Claim': 'Address Change (Claim)',
    'vehicle_cat_n': 'Vehicle Category',
}

insr_type_mapping = {
            1201: 'Private: 1201',
            1202: 'Commercial: 1202',
            1204: 'Motor Trade Road Risk : 1204'
        }

def convert_except_last(string):
    words = string.split()
    result = ' '.join(words[:-2])
    return result

# Streamlit web app
def main():
    st.title("AIFinTech")

    if 'step' not in st.session_state:
        st.session_state.step = 1  # Initial step

    if st.session_state.step == 1:
        create_customer_profile()
    elif st.session_state.step == 2:
        recommended_premium()
    elif st.session_state.step == 3:
        purchase()
    elif st.session_state.step == 4:
        policy_issued()

# Workflow step functions

def create_customer_profile():
    st.subheader("Create Customer Profile")
    # Input fields for customer profile
    gender = st.selectbox('Gender', ['Male', 'Female'])
    driving_license = st.radio('Driving License', ['Yes', 'No'])
    previously_insured = st.radio('Previously Insured', ['Yes', 'No'])
    vehicle_age = st.selectbox("Vehicle Age", ["0 years", "1 year", "2 years", "3 years", "4 years", "5 years", "6 years", "7 years", "More than 7 years"])
    policy_sales_channel = st.selectbox("Policy Sales Channel", ["Internal", "External"])
    vehicle_price_range = st.selectbox("Vehicle Price",
                        ["Less than 20000", "20000 - 29999", "30000 - 39999", "40000 - 49999", "50000 - 59999",
                        "60000 - 69999", "More than 70000"])
    vehicle_category = st.selectbox("Vehicle Category", ["Sport", "Utility", "Sedan"])
    num_supplements = st.selectbox("Number of Supplements", ["0", "1 to 2", "3 to 5", "More than 5"])
    fault_type = st.selectbox("Fault Type", ["Policy Holder", "Third Party"])
    address_change_duration = st.selectbox("Address Change Duration", ["None", "1 year", "2 to 3 years", "4 to 8 years", "More than 8 years"])

    customer_lifespan = st.slider('Customer Lifespan in days', min_value=0, max_value=365, value=180)

    insurance_type = st.selectbox('Insurance Type', options=list(insr_type_mapping.values()), index=1)
    insured_value_amount = st.slider('Insured Value Amount', min_value=0, max_value=100000, value=0)

    usage_type = st.selectbox('Usage Type', list(encoded_values['USAGE'].keys()))
    make_type = st.selectbox('Make Type', list(encoded_values['MAKE'].keys()))
    vehicle_type = st.selectbox('Vehicle Type', list(encoded_values['TYPE_VEHICLE'].keys()))


    # Store all form data in session_state
    st.session_state.customer_profile = {
        'gender': gender,
        'driving_license': driving_license,
        'previously_insured': previously_insured,
        'vehicle_age': vehicle_age,
        'policy_sales_channel': policy_sales_channel,
        'vehicle_price_range': vehicle_price_range,
        'vehicle_category': vehicle_category,
        'num_supplements': num_supplements,
        'fault_type': fault_type,
        'address_change_duration': address_change_duration,
        'customer_lifespan': customer_lifespan,
        'insurance_type': insurance_type,
        'insured_value_amount': insured_value_amount,
        'usage_type': usage_type,
        'make_type': make_type,
        'vehicle_type': vehicle_type,
    }

    if st.button('Submit'):
        st.session_state.step += 1  # Move to the next step

def recommended_premium():
    #st.subheader("Recommended Premium")
    # Retrieve relevant data from session_state
    gender_code = 1 if st.session_state.customer_profile['gender'] == 'Male' else 0
    driving_license_code = 1 if st.session_state.customer_profile['driving_license'] == 'Yes' else 0
    previously_insured_code = 1 if st.session_state.customer_profile['previously_insured'] == 'Yes' else 0
    vehicle_age_code = 0 if st.session_state.customer_profile['vehicle_age'] == '0 years' else (1 if st.session_state.customer_profile['vehicle_age'] in ['1 year', '2 years'] else 2)
    policy_sales_channel_code = 1 if st.session_state.customer_profile['policy_sales_channel'] == 'External' else 0
    # Predict annual premium using the model
    premium = linear_regr_model.predict([[gender_code, driving_license_code, previously_insured_code, vehicle_age_code, policy_sales_channel_code]])

    # Display recommended premium
    st.write(f"Recommended Annual Premium: {premium[0]}")

    acceptable_premium = st.number_input('If the premium is not acceptable then update the Acceptable Premium', value=premium[0])
    if st.button('Proceed to Purchase'):
        st.session_state.acceptable_premium = acceptable_premium
        st.session_state.step += 1  # Move to the next step


def purchase():
    #st.subheader("Purchase")
    # Calculate probabilities, show explanations if fraud probability > 50%

    gender_code = 1 if st.session_state.customer_profile['gender'] == 'Male' else 0
    driving_license_code = 1 if st.session_state.customer_profile['driving_license'] == 'Yes' else 0
    previously_insured_code = 1 if st.session_state.customer_profile['previously_insured'] == 'Yes' else 0
    vehicle_age_code = 0 if st.session_state.customer_profile['vehicle_age'] == '0 years' else (1 if st.session_state.customer_profile['vehicle_age'] in ['1 year', '2 years'] else 2)
    policy_sales_channel_code = 1 if st.session_state.customer_profile['policy_sales_channel'] == 'External' else 0
    acceptable_premium = st.session_state.acceptable_premium

    # Predict probabilities using the model
    prediction_proba = flagel.predict_proba([[gender_code, driving_license_code, previously_insured_code, vehicle_age_code, acceptable_premium,policy_sales_channel_code]])

    # Display prediction result
    claim_probability = prediction_proba[0][1]
    st.write(f"Probability of making a claim: {claim_probability:.2f}")

    vehicle_price_mapping = {
    "Less than 20000": 0,
    "20000 - 29999": 1,
    "30000 - 39999": 2,
    "40000 - 49999": 3,
    "50000 - 59999": 4,
    "60000 - 69999": 5,
    "More than 70000": 6
    }

    vehicle_price = vehicle_price_mapping.get(st.session_state.customer_profile['vehicle_price_range'], 1)

    vehicle_category_mapping = {"Sport": 1, "Sedan": 0, "Utility": 2}
    vehicle_category_m = vehicle_category_mapping.get(st.session_state.customer_profile['vehicle_category'], 2)

    number_suppliments_mapping = {"0": 0, "1 to 2": 1, "3 to 5": 2}
    number_suppliments = number_suppliments_mapping.get(st.session_state.customer_profile['num_supplements'], 3)

    address_change_mapping = {"None": 0, "1 year": 1, "2 to 3 years": 2, "4 to 8 years": 3}
    address_change = address_change_mapping.get(st.session_state.customer_profile['address_change_duration'], 4)

    fault = 1 if st.session_state.customer_profile['fault_type'] == "Policy Holder" else 0

    input_data = pd.DataFrame({
        'premium': [acceptable_premium],
        'AgeOfVehicle': [vehicle_age_code],
        'AgentType': [policy_sales_channel_code],
        'PastNumberOfClaims': [previously_insured_code],
        'VehiclePrice': [vehicle_price],  # Retrieve from session state
        'DriverRating': [driving_license_code],
        'NumberOfSuppliments': [number_suppliments],  # Retrieve from session state
        'Fault': [fault],  # Retrieve from session state
        'AddressChange_Claim': [address_change],  # Retrieve from session state
        'vehicle_cat_n': [vehicle_category_m]  # Retrieve from session state
    })

    fraud_detected = fraud_detection.predict_proba(input_data)
    fraud_probability = fraud_detected[0][0]
    st.write(f"Probability of making a fraud: {fraud_probability:.2f}")

    if fraud_probability > 0.5:
        st.subheader("Reasons why person is likely to commit a fraud")
        explainer = lime.lime_tabular.LimeTabularExplainer(input_data.values,
                                                           feature_names=list(map(lambda x: feature_names_mapping[x], input_data.columns)),
                                                           class_names=['Fraudulent', 'Not Fraudulent'],
                                                           discretize_continuous=True)
        exp = explainer.explain_instance(input_data.iloc[0], fraud_detection.predict_proba, num_features=3)
        for feature, weight in exp.as_list():
            feature_name = convert_except_last(feature)
            st.write(f"- {feature_name}")

    if st.button('Issue Policy'):
        st.session_state.claim_probability = claim_probability
        st.session_state.step += 1  # Move to the next page where policy details can be shown
    elif st.button("Decline Policy"):
        st.session_state.step = 2  # Go back to the previous step (Recommended Premium page)

def policy_issued():
    st.subheader("Policy Issued Successfully")
    days = st.session_state.customer_profile['customer_lifespan']
    years = int(days/365)
    vehicle_age_code = 0 if st.session_state.customer_profile['vehicle_age'] == '0 years' else (1 if st.session_state.customer_profile['vehicle_age'] in ['1 year', '2 years'] else 2)
    claim_flag = 1 if st.session_state.claim_probability > 0.5 else 0
    insr_type= next(
        key for key, value in insr_type_mapping.items() if value == st.session_state.customer_profile['insurance_type'])
    user_data = {
    'SEX': st.session_state.customer_profile['gender'],
    'PREMIUM': st.session_state.acceptable_premium,
    'Age': vehicle_age_code,
    'CUSTOMER_LIFESPAN': st.session_state.customer_profile['customer_lifespan'],
    'INSR_TYPE': insr_type ,
    'USAGE': st.session_state.customer_profile['usage_type'],
    'MAKE': st.session_state.customer_profile['make_type'],
    'TYPE_VEHICLE': st.session_state.customer_profile['vehicle_type'],
    'Claim_Flag': claim_flag,
    'Sales_Channel': st.session_state.customer_profile['policy_sales_channel']
}

    user_data_df = pd.DataFrame([user_data])
    
    clv = gbpipeline.predict(user_data_df)
    acquired_value = st.session_state.acceptable_premium
    clv = clv * 100000  # Placeholder calculation, update as needed

    st.write(f"Customer Lifetime Value (CLV): {clv}")

    unrealized_value = st.session_state.acceptable_premium - (st.session_state.customer_profile["insured_value_amount"] * days)
    unrealized_status = "Unrealized Profit" if unrealized_value > 0 else "Unrealized Loss"
    st.write(f'Unrealized value: {unrealized_value}')
    st.write(f'**The status is: {unrealized_status}**')

    if st.button('Restart Workflow'):
        st.session_state.step = 1  # Reset the workflow

if __name__ == "__main__":
    main()
