# This is your AMSKU scoring endpoint - copy and paste this EXACTLY into main.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# Create the web application
app = Flask(__name__)
CORS(app)  # This lets ElevenLabs talk to your endpoint

# This is the main page - just to test if it's working


@app.route('/')
def home():
    return "<h1>AMSKU Scoring Endpoint is Running!</h1><p>If you see this, everything is working correctly.</p>"

# This is the endpoint that ElevenLabs will call

@app.route('/redirect', methods=['POST'])
def redirect_to_booking():
    try:
        data = request.json
        booking_url = data.get('booking_url')
        
        if not booking_url:
            return jsonify({'error': 'No booking URL provided'}), 400
        
        # Return a redirect response
        return jsonify({
            'redirect': True,
            'url': booking_url,
            'message': 'Redirecting you to book your discovery call...'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calculate_lead_score', methods=['POST'])
def calculate_lead_score():
    try:
        # Get the data sent from ElevenLabs
        data = request.json
        print("Received data:", data)  # This helps you see what's coming in

        # Extract information from the conversation
        profession = str(data.get('profession', '')).lower()
        position = str(data.get('position', '')).lower()
        company = str(data.get('company', '')).lower()
        conversation = str(data.get('conversation_text', '')).lower()

        # Start calculating the score
        score = 0
        factors = []

        # RULE 1: Professional Base Score (1-5 points)
        if any(word in profession or word in conversation for word in ['physical therapist', 'pt', 'dpt', 'physical therapy']):
            score += 5
            factors.append('Physical Therapist (+5 points)')
        elif any(word in profession or word in conversation for word in ['physician', 'doctor', 'md', 'do']):
            score += 4
            factors.append('Physician (+4 points)')
        elif any(word in profession or word in conversation for word in ['physician assistant', 'pa']):
            score += 4
            factors.append('Physician Assistant (+4 points)')
        elif 'therapist' in profession or 'therapist' in conversation:
            score += 3
            factors.append('Other Therapist (+3 points)')
        else:
            score += 1
            factors.append('Other Profession (+1 point)')

        # RULE 2: Purchase Authority (0-4 points)
        if any(word in position or word in conversation for word in ['owner', 'founder', 'ceo', 'president', 'medical director']):
            score += 4
            factors.append('High Authority - Owner/CEO (+4 points)')
        elif any(word in position or word in conversation for word in ['partner', 'director', 'department head']):
            score += 3
            factors.append('Medium Authority - Partner/Director (+3 points)')
        elif any(word in position or word in conversation for word in ['associate', 'senior']):
            score += 2
            factors.append('Some Authority - Associate/Senior (+2 points)')

        # RULE 3: Practice Relevance (0-3 points)
        if any(word in position or word in conversation for word in ['sports medicine', 'orthopedic', 'pain management']):
            score += 3
            factors.append(
                'High Relevance - Sports Medicine/Ortho (+3 points)')
        elif any(word in position or word in conversation for word in ['musculoskeletal', 'rehabilitation', 'physical therapy']):
            score += 2
            factors.append('Medium Relevance - MSK/Rehab (+2 points)')
        elif any(word in position or word in conversation for word in ['primary care', 'family medicine']):
            score += 1
            factors.append('Some Relevance - Primary Care (+1 point)')

        # RULE 4: Financial Capacity (0-3 points)
        if any(word in company or word in conversation for word in ['pc', 'pllc', 'llc', 'associates']):
            score += 3
            factors.append('Private Practice (+3 points)')
        elif any(word in company or word in conversation for word in ['clinic', 'center']) and 'medical center' not in company:
            score += 2
            factors.append('Independent Clinic (+2 points)')

        # RULE 5: Negative Factors
        if any(word in company or word in conversation for word in ['health system', 'medical center', 'hospital']):
            score -= 5
            factors.append('Large Health System (-5 points)')

        # Make sure score is between 1 and 10
        final_score = max(1, min(10, score))

        # Determine what happens next based on score
       # Updated code - score 7+ gets booking link
       if final_score >= 7:
            qualification = 'highly_qualified'
            next_step = 'direct_booking'
            message = "Excellent! Based on your background, you'd be a perfect fit for our program. I'm going to direct you to book a discovery call with Dr. Martin or Dr. Rigney right now."
            booking_url = 'https://calendly.com/amskucenter/residency-discovery-call'
        elif final_score >= 5:
            qualification = 'qualified'
            next_step = 'follow_up'
            message = "Great! You seem like a good potential fit for our program. I'd like to have someone from our team follow up with you about the next steps."
            booking_url = None
        elif final_score >= 4:
            qualification = 'marginal'
            next_step = 'nurture'
            message = "Thank you for your interest! I'd like to share some helpful resources as you explore MSK ultrasound training options."
            booking_url = None
        else:
            qualification = 'unqualified'
            next_step = 'redirect'
            message = "Thank you for your interest in AMSKU. Let me direct you to some educational resources about MSK ultrasound that might be helpful."
            booking_url = None

        # Send back the results
        response = {
            'score': final_score,
            'factors': factors,
            'qualification': qualification,
            'next_step': next_step,
            'message': message,
            'booking_url': booking_url
        }

        print("Sending back:", response)  # So you can see what's being sent
        return jsonify(response)

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({'error': 'Something went wrong: ' + str(e)}), 500


# This starts the web server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
