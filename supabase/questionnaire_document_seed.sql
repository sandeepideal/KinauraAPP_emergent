-- =====================================================
-- KinAura Questionnaire and Document Management System
-- Comprehensive Seed Data
-- =====================================================

-- This file populates the questionnaire and document system with realistic sample data
-- for development, testing, and demonstration purposes.

-- Insert Sample Questionnaires
-- ============================

-- Medical History Questionnaire
INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata) VALUES
('med-history-001', 
 'Comprehensive Medical History Assessment', 
 'Detailed medical history questionnaire to understand your health background and current conditions',
 'medical_history',
 true,
 true,
 'Please answer all questions thoroughly and honestly. This information is crucial for providing you with the best possible care. If you are unsure about any answer, please consult your medical records or contact your primary healthcare provider.',
 '[
   {
     "id": "mh-001",
     "question_text": "Do you have any known allergies to medications, foods, or environmental factors?",
     "question_type": "yes_no",
     "is_required": true,
     "order_index": 1,
     "options": {},
     "validation": {},
     "help_text": "Include all known allergies, even mild reactions"
   },
   {
     "id": "mh-002", 
     "question_text": "If yes, please list all your allergies and describe the reactions:",
     "question_type": "long_text",
     "is_required": false,
     "order_index": 2,
     "options": {},
     "validation": {"max_length": 1000},
     "help_text": "Describe the type of reaction (rash, swelling, difficulty breathing, etc.)"
   },
   {
     "id": "mh-003",
     "question_text": "Please select all medications you are currently taking:",
     "question_type": "multiple_choice", 
     "is_required": true,
     "order_index": 3,
     "options": {
       "choices": [
         "Blood pressure medications (ACE inhibitors, beta blockers, etc.)",
         "Diabetes medications (insulin, metformin, etc.)",
         "Heart medications (statins, blood thinners, etc.)",
         "Thyroid medications",
         "Antidepressants or anxiety medications",
         "Pain medications (NSAIDs, opioids, etc.)",
         "Hormone replacement therapy",
         "Supplements and vitamins",
         "Over-the-counter medications",
         "None of the above"
       ],
       "allow_multiple": true
     },
     "validation": {},
     "help_text": "Select all that apply. Include prescription and over-the-counter medications."
   },
   {
     "id": "mh-004",
     "question_text": "Have you had any surgeries or major medical procedures?",
     "question_type": "yes_no",
     "is_required": true,
     "order_index": 4,
     "options": {},
     "validation": {},
     "help_text": "Include any surgical procedures, even minor ones"
   },
   {
     "id": "mh-005",
     "question_text": "If yes, please list your surgeries with approximate dates:",
     "question_type": "long_text",
     "is_required": false,
     "order_index": 5,
     "options": {},
     "validation": {"max_length": 800},
     "help_text": "Example: Appendectomy (2015), Knee surgery (2020)"
   },
   {
     "id": "mh-006",
     "question_text": "Do you have any chronic health conditions?",
     "question_type": "multiple_choice",
     "is_required": true,
     "order_index": 6,
     "options": {
       "choices": [
         "Diabetes (Type 1 or 2)",
         "High blood pressure",
         "Heart disease",
         "Arthritis",
         "Thyroid disorders",
         "Kidney disease",
         "Liver disease",
         "Autoimmune conditions",
         "Mental health conditions",
         "Cancer history",
         "None of the above"
       ],
       "allow_multiple": true
     },
     "validation": {},
     "help_text": "Select all chronic conditions you have been diagnosed with"
   },
   {
     "id": "mh-007",
     "question_text": "On a scale of 1-10, how would you rate your current overall health?",
     "question_type": "rating_scale",
     "is_required": true,
     "order_index": 7,
     "options": {
       "min": 1,
       "max": 10,
       "labels": {
         "1": "Very Poor",
         "5": "Average", 
         "10": "Excellent"
       }
     },
     "validation": {},
     "help_text": "1 = Very poor health, 10 = Excellent health"
   },
   {
     "id": "mh-008",
     "question_text": "What is your date of birth?",
     "question_type": "date",
     "is_required": true,
     "order_index": 8,
     "options": {},
     "validation": {
       "min_age": 18,
       "max_age": 120
     },
     "help_text": "Required for age-appropriate treatment recommendations"
   }
 ]',
 'admin-001',
 '2024-12-15T09:00:00Z',
 '2024-12-15T09:00:00Z',
 '{
   "estimated_minutes": 15,
   "department": "Clinical Assessment",
   "version": "1.0",
   "review_required": true
 }');

-- Pre-Treatment Wellness Assessment
INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata) VALUES
('wellness-001',
 'Pre-Treatment Wellness Assessment',
 'Comprehensive wellness evaluation to customize your regenerative treatment plan',
 'wellness_assessment',
 true,
 false,
 'This assessment helps us understand your current wellness goals, lifestyle, and treatment expectations. Your responses will help us create a personalized treatment plan that aligns with your health objectives.',
 '[
   {
     "id": "wa-001",
     "question_text": "What are your primary health and wellness goals?",
     "question_type": "multiple_choice",
     "is_required": true,
     "order_index": 1,
     "options": {
       "choices": [
         "Increase energy and vitality",
         "Improve cognitive function and mental clarity",
         "Enhance physical performance and recovery",
         "Support healthy aging and longevity",
         "Boost immune system function",
         "Improve sleep quality",
         "Reduce inflammation and pain",
         "Weight management and metabolism",
         "Stress reduction and mental wellness",
         "Overall health optimization"
       ],
       "allow_multiple": true
     },
     "validation": {},
     "help_text": "Select all goals that are important to you"
   },
   {
     "id": "wa-002",
     "question_text": "How would you describe your current energy level throughout the day?",
     "question_type": "single_choice",
     "is_required": true,
     "order_index": 2,
     "options": {
       "choices": [
         "High energy most of the day",
         "Good energy with occasional dips",
         "Moderate energy, some fatigue",
         "Low energy, frequent fatigue",
         "Very low energy, chronic fatigue"
       ]
     },
     "validation": {},
     "help_text": "Choose the option that best describes your typical day"
   },
   {
     "id": "wa-003",
     "question_text": "How many hours of sleep do you typically get per night?",
     "question_type": "number",
     "is_required": true,
     "order_index": 3,
     "options": {
       "min": 0,
       "max": 24,
       "step": 0.5
     },
     "validation": {
       "min_value": 3,
       "max_value": 12
     },
     "help_text": "Enter average hours including naps"
   },
   {
     "id": "wa-004",
     "question_text": "How would you rate your sleep quality?",
     "question_type": "rating_scale",
     "is_required": true,
     "order_index": 4,
     "options": {
       "min": 1,
       "max": 10,
       "labels": {
         "1": "Very Poor",
         "5": "Average",
         "10": "Excellent"
       }
     },
     "validation": {},
     "help_text": "1 = Very poor sleep, 10 = Excellent, refreshing sleep"
   },
   {
     "id": "wa-005",
     "question_text": "How often do you exercise or engage in physical activity?",
     "question_type": "single_choice",
     "is_required": true,
     "order_index": 5,
     "options": {
       "choices": [
         "Daily",
         "5-6 times per week",
         "3-4 times per week", 
         "1-2 times per week",
         "Rarely or never"
       ]
     },
     "validation": {},
     "help_text": "Include all forms of physical activity"
   },
   {
     "id": "wa-006",
     "question_text": "What types of physical activities do you regularly participate in?",
     "question_type": "multiple_choice",
     "is_required": false,
     "order_index": 6,
     "options": {
       "choices": [
         "Cardiovascular exercise (running, cycling, swimming)",
         "Strength training / weight lifting",
         "Yoga or Pilates",
         "Walking or hiking",
         "Sports activities",
         "Dancing",
         "Martial arts",
         "Other fitness classes",
         "None of the above"
       ],
       "allow_multiple": true
     },
     "validation": {},
     "help_text": "Select all activities you do regularly"
   },
   {
     "id": "wa-007",
     "question_text": "How would you describe your current stress level?",
     "question_type": "rating_scale",
     "is_required": true,
     "order_index": 7,
     "options": {
       "min": 1,
       "max": 10,
       "labels": {
         "1": "Very Low Stress",
         "5": "Moderate Stress",
         "10": "Very High Stress"
       }
     },
     "validation": {},
     "help_text": "Consider work, personal, and health-related stress"
   },
   {
     "id": "wa-008",
     "question_text": "What are your main sources of stress?",
     "question_type": "multiple_choice",
     "is_required": false,
     "order_index": 8,
     "options": {
       "choices": [
         "Work and career pressures",
         "Financial concerns",
         "Family and relationship issues",
         "Health concerns",
         "Time management",
         "Social situations",
         "Major life changes",
         "None significant",
         "Prefer not to answer"
       ],
       "allow_multiple": true
     },
     "validation": {},
     "help_text": "Select all that apply to your current situation"
   }
 ]',
 'admin-001',
 '2024-12-15T10:30:00Z',
 '2024-12-15T10:30:00Z',
 '{
   "estimated_minutes": 12,
   "department": "Wellness Center",
   "version": "1.0",
   "customizable": true
 }');

-- Treatment Consent Form
INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata) VALUES
('consent-001',
 'Regenerative Treatment Consent Form',
 'Informed consent questionnaire for regenerative wellness treatments',
 'treatment_consent',
 true,
 true,
 'This consent form ensures you understand the treatments you will receive, their benefits, potential risks, and your responsibilities. Please read each question carefully and provide honest answers.',
 '[
   {
     "id": "tc-001",
     "question_text": "I understand that regenerative treatments are designed to optimize health and wellness, but individual results may vary",
     "question_type": "yes_no",
     "is_required": true,
     "order_index": 1,
     "options": {},
     "validation": {},
     "help_text": "Acknowledgment of treatment variability"
   },
   {
     "id": "tc-002",
     "question_text": "I have disclosed all current medications, supplements, and health conditions to my healthcare provider",
     "question_type": "yes_no",
     "is_required": true,
     "order_index": 2,
     "options": {},
     "validation": {},
     "help_text": "Complete disclosure is essential for safe treatment"
   },
   {
     "id": "tc-003",
     "question_text": "I understand the potential risks and benefits of my prescribed treatment plan",
     "question_type": "yes_no",
     "is_required": true,
     "order_index": 3,
     "options": {},
     "validation": {},
     "help_text": "Informed consent regarding treatment risks and benefits"
   },
   {
     "id": "tc-004",
     "question_text": "Which treatments have been explained to you and you consent to receive?",
     "question_type": "multiple_choice",
     "is_required": true,
     "order_index": 4,
     "options": {
       "choices": [
         "IV Nutrient Therapy",
         "NAD+ IV Therapy", 
         "Ozone Therapy",
         "Hyperbaric Oxygen Therapy",
         "Peptide Therapy",
         "IV Laser Therapy",
         "PEMF Therapy",
         "Exosome Therapy",
         "Detoxification Protocols"
       ],
       "allow_multiple": true
     },
     "validation": {},
     "help_text": "Select all treatments you consent to receive"
   },
   {
     "id": "tc-005",
     "question_text": "I agree to follow all pre and post-treatment instructions provided by my healthcare team",
     "question_type": "yes_no",
     "is_required": true,
     "order_index": 5,
     "options": {},
     "validation": {},
     "help_text": "Compliance with treatment protocols is essential for safety and efficacy"
   },
   {
     "id": "tc-006",
     "question_text": "I will notify my healthcare provider immediately if I experience any adverse reactions or complications",
     "question_type": "yes_no",
     "is_required": true,
     "order_index": 6,
     "options": {},
     "validation": {},
     "help_text": "Immediate reporting of adverse events is crucial"
   },
   {
     "id": "tc-007",
     "question_text": "Emergency contact information - Full name:",
     "question_type": "text",
     "is_required": true,
     "order_index": 7,
     "options": {},
     "validation": {"min_length": 2, "max_length": 100},
     "help_text": "Person to contact in case of emergency during treatment"
   },
   {
     "id": "tc-008",
     "question_text": "Emergency contact phone number:",
     "question_type": "text",
     "is_required": true,
     "order_index": 8,
     "options": {},
     "validation": {"pattern": "^[+]?[0-9\\s\\-\\(\\)]{10,15}$"},
     "help_text": "Include area code and country code if international"
   }
 ]',
 'admin-001',
 '2024-12-15T11:00:00Z',
 '2024-12-15T11:00:00Z',
 '{
   "estimated_minutes": 8,
   "department": "Legal/Clinical",
   "version": "2.1",
   "legal_required": true,
   "retention_years": 7
 }');

-- Post-Treatment Follow-up
INSERT INTO questionnaires (_id, title, description, category, is_active, is_required, instructions, questions, created_by, created_at, updated_at, metadata) VALUES
('followup-001',
 'Post-Treatment Assessment & Follow-up',
 'Evaluation of treatment effectiveness and planning for ongoing care',
 'post_treatment',
 true,
 false,
 'This follow-up assessment helps us evaluate how well your treatment is working and plan your ongoing care. Your feedback is valuable for optimizing your treatment protocol.',
 '[
   {
     "id": "pt-001",
     "question_text": "How long ago did you complete your last treatment session?",
     "question_type": "single_choice",
     "is_required": true,
     "order_index": 1,
     "options": {
       "choices": [
         "1-3 days ago",
         "4-7 days ago",
         "1-2 weeks ago",
         "2-4 weeks ago",
         "1-2 months ago",
         "More than 2 months ago"
       ]
     },
     "validation": {},
     "help_text": "Select the timeframe that best matches your last treatment"
   },
   {
     "id": "pt-002",
     "question_text": "Overall, how satisfied are you with your treatment experience?",
     "question_type": "rating_scale",
     "is_required": true,
     "order_index": 2,
     "options": {
       "min": 1,
       "max": 10,
       "labels": {
         "1": "Very Dissatisfied",
         "5": "Neutral",
         "10": "Very Satisfied"
       }
     },
     "validation": {},
     "help_text": "Rate your overall satisfaction with the treatment process"
   },
   {
     "id": "pt-003",
     "question_text": "Which of your wellness goals have you noticed improvement in?",
     "question_type": "multiple_choice",
     "is_required": false,
     "order_index": 3,
     "options": {
       "choices": [
         "Increased energy and vitality",
         "Better cognitive function and mental clarity",
         "Enhanced physical performance",
         "Improved sleep quality",
         "Reduced inflammation or pain",
         "Better mood and emotional well-being",
         "Improved immune function",
         "Better stress management",
         "None yet - too early to tell",
         "No noticeable improvements"
       ],
       "allow_multiple": true
     },
     "validation": {},
     "help_text": "Select all areas where you have noticed positive changes"
   },
   {
     "id": "pt-004",
     "question_text": "On a scale of 1-10, how would you rate your current energy level compared to before treatment?",
     "question_type": "rating_scale",
     "is_required": true,
     "order_index": 4,
     "options": {
       "min": 1,
       "max": 10,
       "labels": {
         "1": "Much Worse",
         "5": "No Change",
         "10": "Much Better"
       }
     },
     "validation": {},
     "help_text": "Compare your energy now to before starting treatments"
   },
   {
     "id": "pt-005",
     "question_text": "Have you experienced any side effects or concerns since your treatment?",
     "question_type": "yes_no",
     "is_required": true,
     "order_index": 5,
     "options": {},
     "validation": {},
     "help_text": "Include any physical, emotional, or other concerns"
   },
   {
     "id": "pt-006",
     "question_text": "If yes, please describe any side effects or concerns:",
     "question_type": "long_text",
     "is_required": false,
     "order_index": 6,
     "options": {},
     "validation": {"max_length": 500},
     "help_text": "Describe the nature, timing, and severity of any side effects"
   },
   {
     "id": "pt-007",
     "question_text": "Are you interested in continuing with additional treatment sessions?",
     "question_type": "single_choice",
     "is_required": true,
     "order_index": 7,
     "options": {
       "choices": [
         "Yes, definitely interested",
         "Yes, but want to discuss modifications",
         "Undecided, need more time to evaluate",
         "No, satisfied with current results",
         "No, not satisfied with treatment"
       ]
     },
     "validation": {},
     "help_text": "Your interest in continued treatment"
   },
   {
     "id": "pt-008",
     "question_text": "Would you recommend our regenerative treatments to friends or family?",
     "question_type": "rating_scale",
     "is_required": true,
     "order_index": 8,
     "options": {
       "min": 0,
       "max": 10,
       "labels": {
         "0": "Would Not Recommend",
         "5": "Neutral",
         "10": "Highly Recommend"
       }
     },
     "validation": {},
     "help_text": "Net Promoter Score - likelihood to recommend (0-10)"
   }
 ]',
 'admin-001',
 '2024-12-15T14:00:00Z',
 '2024-12-15T14:00:00Z',
 '{
   "estimated_minutes": 10,
   "department": "Clinical Follow-up",
   "version": "1.0",
   "triggers_review": true,
   "follow_up_days": [7, 30, 90]
 }');

-- Insert Sample Documents
-- =======================

-- Privacy Notice Document
INSERT INTO documents (_id, title, document_type, content, version, is_active, requires_signature, settings, created_by, created_at, updated_at) VALUES
('doc-privacy-001',
 'Privacy Notice and Data Protection Policy',
 'privacy_notice',
 '<div class="document-content">
<h1>KinAura Institute - Privacy Notice</h1>
<p><strong>Effective Date:</strong> December 15, 2024</p>
<p><strong>Last Updated:</strong> December 15, 2024</p>

<h2>Introduction</h2>
<p>At KinAura Institute for Regenerative Wellness, we are committed to protecting your privacy and ensuring the security of your personal health information. This Privacy Notice explains how we collect, use, disclose, and safeguard your information when you receive our services.</p>

<h2>Information We Collect</h2>
<h3>Personal Health Information (PHI)</h3>
<ul>
<li>Medical history and current health conditions</li>
<li>Treatment records and clinical notes</li>
<li>Laboratory test results and diagnostic information</li>
<li>Medication lists and allergy information</li>
<li>Treatment plans and progress notes</li>
</ul>

<h3>Personal Information</h3>
<ul>
<li>Contact information (name, address, phone, email)</li>
<li>Insurance information and billing details</li>
<li>Emergency contact information</li>
<li>Demographic information (age, gender)</li>
</ul>

<h2>How We Use Your Information</h2>
<p>We use your information for the following purposes:</p>
<ul>
<li><strong>Treatment:</strong> To provide, coordinate, and manage your healthcare</li>
<li><strong>Payment:</strong> To obtain reimbursement for services provided</li>
<li><strong>Healthcare Operations:</strong> For quality improvement, staff training, and business operations</li>
<li><strong>Legal Requirements:</strong> To comply with applicable laws and regulations</li>
</ul>

<h2>Information Sharing and Disclosure</h2>
<p>We may share your information with:</p>
<ul>
<li>Healthcare providers involved in your care</li>
<li>Insurance companies for payment purposes</li>
<li>Laboratory and diagnostic service providers</li>
<li>Legal authorities when required by law</li>
<li>Business associates who help us operate (under strict confidentiality agreements)</li>
</ul>

<h2>Your Rights</h2>
<p>You have the right to:</p>
<ul>
<li>Request access to your medical records</li>
<li>Request corrections to your information</li>
<li>Request restrictions on use or disclosure</li>
<li>Request confidential communications</li>
<li>File a complaint about our privacy practices</li>
<li>Obtain a copy of this Privacy Notice</li>
</ul>

<h2>Data Security</h2>
<p>We implement appropriate technical, administrative, and physical safeguards to protect your information against unauthorized access, use, or disclosure. This includes:</p>
<ul>
<li>Encrypted electronic storage systems</li>
<li>Secure transmission protocols</li>
<li>Access controls and user authentication</li>
<li>Regular security audits and updates</li>
<li>Staff training on privacy and security practices</li>
</ul>

<h2>Data Retention</h2>
<p>We retain your health information as required by law and professional standards, typically for a minimum of 7 years after your last treatment or as required by applicable regulations.</p>

<h2>Contact Information</h2>
<p>If you have questions about this Privacy Notice or wish to exercise your rights, please contact our Privacy Officer:</p>
<p>
<strong>KinAura Institute Privacy Officer</strong><br>
Email: privacy@kinaura.com<br>
Phone: +1 (555) 123-4567<br>
Address: 123 Wellness Boulevard, Health City, HC 12345
</p>

<h2>Changes to This Notice</h2>
<p>We reserve the right to modify this Privacy Notice. Any changes will be posted on our website and made available at our facility. The effective date at the top of this notice indicates when it was last updated.</p>

<p><strong>Acknowledgment:</strong> By signing below, you acknowledge that you have received and reviewed this Privacy Notice and understand your rights regarding your personal health information.</p>
</div>',
 '2.0',
 true,
 true,
 '{
   "signature_required": true,
   "legal_document": true,
   "retention_years": 7,
   "language": "en-US"
 }',
 'admin-001',
 '2024-12-15T08:00:00Z',
 '2024-12-15T08:00:00Z');

-- Treatment Information Document
INSERT INTO documents (_id, title, document_type, content, version, is_active, requires_signature, settings, created_by, created_at, updated_at) VALUES
('doc-treatment-001',
 'Regenerative Wellness Treatment Information',
 'treatment_info',
 '<div class="document-content">
<h1>Regenerative Wellness Treatment Information</h1>
<p><strong>KinAura Institute for Regenerative Wellness</strong></p>

<h2>Overview of Regenerative Treatments</h2>
<p>Our regenerative wellness treatments are designed to optimize your body''s natural healing and regenerative processes. These advanced therapies work at the cellular level to enhance vitality, improve function, and support healthy aging.</p>

<h2>Available Treatments</h2>

<h3>IV Nutrient Therapy</h3>
<p><strong>Description:</strong> Direct intravenous delivery of essential vitamins, minerals, and nutrients to optimize cellular function and energy production.</p>
<p><strong>Benefits:</strong> Increased energy, improved immune function, enhanced hydration, better nutrient absorption</p>
<p><strong>Duration:</strong> 30-60 minutes per session</p>
<p><strong>Frequency:</strong> Weekly or bi-weekly as recommended</p>

<h3>NAD+ IV Therapy</h3>
<p><strong>Description:</strong> Intravenous nicotinamide adenine dinucleotide (NAD+) to support cellular energy production and DNA repair.</p>
<p><strong>Benefits:</strong> Enhanced cognitive function, increased energy, improved mood, anti-aging effects</p>
<p><strong>Duration:</strong> 2-4 hours per session</p>
<p><strong>Frequency:</strong> 1-2 times per week for initial protocol</p>

<h3>Ozone Therapy</h3>
<p><strong>Description:</strong> Medical ozone administered intravenously to enhance oxygen utilization and support immune function.</p>
<p><strong>Benefits:</strong> Improved circulation, enhanced immune response, increased energy, detoxification support</p>
<p><strong>Duration:</strong> 45-90 minutes per session</p>
<p><strong>Frequency:</strong> 2-3 times per week initially</p>

<h3>Hyperbaric Oxygen Therapy (HBOT)</h3>
<p><strong>Description:</strong> Breathing pure oxygen in a pressurized chamber to increase oxygen delivery to tissues.</p>
<p><strong>Benefits:</strong> Accelerated healing, reduced inflammation, improved brain function, enhanced recovery</p>
<p><strong>Duration:</strong> 60-90 minutes per session</p>
<p><strong>Frequency:</strong> Daily or every other day</p>

<h3>Peptide Therapy</h3>
<p><strong>Description:</strong> Targeted peptide compounds to support specific biological functions and optimize health.</p>
<p><strong>Benefits:</strong> Varies by peptide - may include improved sleep, enhanced recovery, hormone optimization</p>
<p><strong>Duration:</strong> Self-administered or clinical injection</p>
<p><strong>Frequency:</strong> As prescribed by healthcare provider</p>

<h3>IV Laser Therapy</h3>
<p><strong>Description:</strong> Low-level laser therapy delivered intravenously to stimulate cellular repair and regeneration.</p>
<p><strong>Benefits:</strong> Enhanced cellular energy, improved circulation, reduced inflammation</p>
<p><strong>Duration:</strong> 30-45 minutes per session</p>
<p><strong>Frequency:</strong> 2-3 times per week</p>

<h2>Treatment Process</h2>
<ol>
<li><strong>Initial Consultation:</strong> Comprehensive health assessment and goal setting</li>
<li><strong>Personalized Protocol:</strong> Customized treatment plan based on your needs</li>
<li><strong>Treatment Sessions:</strong> Regular therapy sessions with monitoring</li>
<li><strong>Progress Evaluation:</strong> Ongoing assessment and protocol adjustments</li>
<li><strong>Maintenance Program:</strong> Long-term optimization strategy</li>
</ol>

<h2>What to Expect</h2>
<h3>Before Treatment</h3>
<ul>
<li>Complete medical questionnaires and consent forms</li>
<li>Follow any pre-treatment instructions (fasting, hydration, etc.)</li>
<li>Arrive well-rested and hydrated</li>
<li>Bring a list of current medications and supplements</li>
</ul>

<h3>During Treatment</h3>
<ul>
<li>Comfortable treatment environment with monitoring</li>
<li>Healthcare provider supervision throughout</li>
<li>Opportunity to rest, read, or use mobile devices</li>
<li>Regular vital sign monitoring as appropriate</li>
</ul>

<h3>After Treatment</h3>
<ul>
<li>Brief observation period to ensure you feel well</li>
<li>Post-treatment instructions and recommendations</li>
<li>Scheduling of follow-up sessions</li>
<li>Contact information for questions or concerns</li>
</ul>

<h2>Potential Benefits</h2>
<p>While individual results vary, patients commonly report:</p>
<ul>
<li>Increased energy and vitality</li>
<li>Improved mental clarity and focus</li>
<li>Enhanced physical performance</li>
<li>Better sleep quality</li>
<li>Improved mood and well-being</li>
<li>Faster recovery from illness or injury</li>
<li>Overall sense of improved health</li>
</ul>

<h2>Potential Risks and Side Effects</h2>
<p>Regenerative treatments are generally well-tolerated, but may include:</p>
<ul>
<li>Mild discomfort at injection sites</li>
<li>Temporary fatigue (as body adjusts)</li>
<li>Mild detoxification symptoms</li>
<li>Rare allergic reactions</li>
<li>Individual responses may vary</li>
</ul>

<h2>Important Notes</h2>
<ul>
<li>These treatments are not intended to diagnose, treat, cure, or prevent any disease</li>
<li>Results are not guaranteed and may vary between individuals</li>
<li>Treatments should complement, not replace, conventional medical care</li>
<li>Inform your provider of any changes in health status</li>
<li>Follow all pre and post-treatment instructions</li>
</ul>

<h2>Questions or Concerns</h2>
<p>Please discuss any questions or concerns with your healthcare provider. We are committed to ensuring you have a safe, comfortable, and beneficial treatment experience.</p>

<p><strong>Emergency Contact:</strong> If you experience any adverse reactions after treatment, contact us immediately at +1 (555) 123-4567 or seek emergency medical care if symptoms are severe.</p>
</div>',
 '1.5',
 true,
 false,
 '{
   "signature_required": false,
   "informational_only": true,
   "review_required": true,
   "language": "en-US"
 }',
 'admin-001',
 '2024-12-15T09:30:00Z',
 '2024-12-15T09:30:00Z');

-- Financial Agreement Document
INSERT INTO documents (_id, title, document_type, content, version, is_active, requires_signature, settings, created_by, created_at, updated_at) VALUES
('doc-financial-001',
 'Financial Agreement and Payment Policy',
 'financial_agreement',
 '<div class="document-content">
<h1>Financial Agreement and Payment Policy</h1>
<p><strong>KinAura Institute for Regenerative Wellness</strong></p>
<p><strong>Effective Date:</strong> December 15, 2024</p>

<h2>Payment Policy</h2>
<p>Thank you for choosing KinAura Institute for your regenerative wellness needs. This agreement outlines our financial policies and your payment responsibilities.</p>

<h2>Payment Options</h2>
<p>We accept the following forms of payment:</p>
<ul>
<li>Cash</li>
<li>Credit Cards (Visa, MasterCard, American Express, Discover)</li>
<li>Debit Cards</li>
<li>Electronic Bank Transfers (ACH)</li>
<li>Healthcare Financing Plans (CareCredit, etc.)</li>
<li>Health Savings Account (HSA) and Flexible Spending Account (FSA) cards</li>
</ul>

<h2>Treatment Packages and Pricing</h2>
<h3>Individual Session Rates</h3>
<ul>
<li>IV Nutrient Therapy: €179 - €229 per session</li>
<li>NAD+ IV Therapy: €390 - €450 per session</li>
<li>Ozone Therapy: €229 - €279 per session</li>
<li>Hyperbaric Oxygen Therapy: €150 - €200 per session</li>
<li>Peptide Therapy: €120 - €300 per month (varies by peptide)</li>
<li>IV Laser Therapy: €180 - €230 per session</li>
</ul>

<h3>Package Discounts</h3>
<p>Multi-session packages offer significant savings:</p>
<ul>
<li>3-session package: 5% discount</li>
<li>6-session package: 10% discount</li>
<li>12-session package: 15% discount</li>
</ul>

<h3>Membership Programs</h3>
<p>Monthly membership options available with exclusive benefits:</p>
<ul>
<li><strong>Gold Membership:</strong> €299/month - includes 1 IV therapy session, 20% discount on additional services</li>
<li><strong>Platinum Membership:</strong> €499/month - includes 2 IV therapy sessions, 25% discount on additional services</li>
<li><strong>Elite Membership:</strong> €799/month - includes 3 IV therapy sessions, 30% discount on additional services, priority scheduling</li>
</ul>

<h2>Payment Terms</h2>
<h3>Individual Sessions</h3>
<ul>
<li>Payment is due at the time of service</li>
<li>We require a credit card on file for scheduling</li>
<li>Prepayment is required for first-time patients</li>
</ul>

<h3>Treatment Packages</h3>
<ul>
<li>Full payment due upon package purchase</li>
<li>Package sessions must be used within 12 months of purchase</li>
<li>Unused sessions are non-refundable after 12 months</li>
</ul>

<h3>Membership Programs</h3>
<ul>
<li>Monthly membership fees are automatically charged on the enrollment date each month</li>
<li>First month payment due upon enrollment</li>
<li>Unused monthly sessions do not roll over</li>
<li>30-day written notice required for membership cancellation</li>
</ul>

<h2>Cancellation and Refund Policy</h2>
<h3>Appointment Cancellations</h3>
<ul>
<li>24-hour advance notice required for cancellations</li>
<li>Late cancellations (less than 24 hours) may incur a €50 fee</li>
<li>No-shows will be charged the full session fee</li>
<li>Emergency situations will be considered on a case-by-case basis</li>
</ul>

<h3>Package Refunds</h3>
<ul>
<li>Unused package sessions may be refunded within 30 days of purchase</li>
<li>After 30 days, refunds will be prorated based on unused sessions</li>
<li>A €25 processing fee applies to all refunds</li>
<li>Medical necessity cancellations require physician documentation</li>
</ul>

<h3>Membership Cancellations</h3>
<ul>
<li>30-day written notice required</li>
<li>Cancellation effective at the end of the current billing cycle</li>
<li>No refunds for partial months</li>
<li>Membership benefits cease immediately upon cancellation</li>
</ul>

<h2>Insurance and HSA/FSA</h2>
<p><strong>Insurance Coverage:</strong> Most regenerative wellness treatments are not covered by traditional health insurance. We provide detailed receipts for your records and potential reimbursement claims.</p>

<p><strong>HSA/FSA:</strong> Many treatments may qualify for HSA or FSA reimbursement. We recommend consulting with your benefits administrator or tax advisor.</p>

<h2>Financial Hardship Assistance</h2>
<p>We understand that healthcare costs can be challenging. We offer:</p>
<ul>
<li>Payment plans for treatment packages (subject to approval)</li>
<li>Healthcare financing options through third-party providers</li>
<li>Limited scholarship programs for qualifying patients</li>
<li>Sliding scale fees in exceptional circumstances</li>
</ul>

<h2>Late Payment Policy</h2>
<ul>
<li>Accounts not paid within 30 days may incur a €25 late fee</li>
<li>Accounts over 60 days past due may be suspended from scheduling</li>
<li>Accounts over 90 days past due may be sent to collection</li>
<li>Collection accounts may incur additional fees and interest</li>
</ul>

<h2>Price Changes</h2>
<p>Treatment prices may be adjusted periodically. Current patients will receive 30-day advance notice of any price changes. Existing packages and memberships will honor original pricing through their terms.</p>

<h2>Agreement Acknowledgment</h2>
<p>By signing this agreement, I acknowledge that:</p>
<ul>
<li>I have read and understand the financial policies</li>
<li>I agree to the payment terms and cancellation policies</li>
<li>I understand that I am responsible for all charges incurred</li>
<li>I authorize KinAura Institute to charge my payment method on file</li>
<li>I will provide updated payment information as needed</li>
</ul>

<h2>Contact Information</h2>
<p>Questions about billing or financial policies should be directed to:</p>
<p>
<strong>Billing Department</strong><br>
Phone: +1 (555) 123-4567 ext. 2<br>
Email: billing@kinaura.com<br>
Hours: Monday-Friday, 9:00 AM - 5:00 PM
</p>

<p><strong>Patient Signature Required</strong></p>
<p>Your signature below indicates that you have read, understood, and agree to these financial terms and policies.</p>
</div>',
 '1.0',
 true,
 true,
 '{
   "signature_required": true,
   "financial_document": true,
   "retention_years": 7,
   "language": "en-US"
 }',
 'admin-001',
 '2024-12-15T12:00:00Z',
 '2024-12-15T12:00:00Z');

-- Sample Patient Questionnaire Assignments
-- ========================================

-- Assuming we have some sample patient IDs from existing data
-- We'll assign questionnaires to demonstrate the assignment system

-- Elena Verdi - Medical History (completed)
INSERT INTO patient_questionnaires (_id, patient_id, questionnaire_id, assigned_by, assigned_at, due_date, started_at, completed_at, status, context) VALUES
('pq-001',
 'patient-elena-001', 
 'med-history-001',
 'admin-001',
 '2024-12-10T09:00:00Z',
 '2024-12-17T23:59:59Z',
 '2024-12-11T14:30:00Z',
 '2024-12-11T15:15:00Z',
 'completed',
 '{
   "assigned_for": "Initial consultation preparation",
   "priority": "high",
   "completion_bonus": 50
 }');

-- Elena Verdi - Wellness Assessment (in progress)
INSERT INTO patient_questionnaires (_id, patient_id, questionnaire_id, assigned_by, assigned_at, due_date, started_at, status, context) VALUES
('pq-002',
 'patient-elena-001',
 'wellness-001', 
 'admin-001',
 '2024-12-11T16:00:00Z',
 '2024-12-18T23:59:59Z',
 '2024-12-12T10:00:00Z',
 'in_progress',
 '{
   "assigned_for": "Pre-treatment wellness evaluation",
   "priority": "medium",
   "estimated_completion": "2024-12-13"
 }');

-- Francesco Neri - Treatment Consent (assigned)
INSERT INTO patient_questionnaires (_id, patient_id, questionnaire_id, assigned_by, assigned_at, due_date, status, context) VALUES
('pq-003',
 'patient-francesco-001',
 'consent-001',
 'admin-001',
 '2024-12-12T08:00:00Z',
 '2024-12-19T23:59:59Z',
 'assigned',
 '{
   "assigned_for": "Treatment preparation - NAD+ IV Therapy",
   "priority": "urgent",
   "treatment_date": "2024-12-20"
 }');

-- Sample Patient Document Assignments
-- ===================================

-- Elena Verdi - Privacy Notice (signed)
INSERT INTO patient_documents (_id, patient_id, document_id, assigned_by, assigned_at, viewed_at, signed_at, status, context) VALUES
('pd-001',
 'patient-elena-001',
 'doc-privacy-001',
 'admin-001',
 '2024-12-10T08:30:00Z',
 '2024-12-10T14:00:00Z',
 '2024-12-10T14:05:00Z',
 'signed',
 '{
   "assignment_reason": "New patient onboarding",
   "priority": "required"
 }');

-- Francesco Neri - Treatment Information (viewed)
INSERT INTO patient_documents (_id, patient_id, document_id, assigned_by, assigned_at, viewed_at, status, context) VALUES
('pd-002',
 'patient-francesco-001',
 'doc-treatment-001',
 'admin-001',
 '2024-12-11T09:00:00Z',
 '2024-12-12T11:30:00Z',
 'viewed',
 '{
   "assignment_reason": "Treatment education before NAD+ therapy",
   "priority": "high"
 }');

-- Francesco Neri - Financial Agreement (assigned)
INSERT INTO patient_documents (_id, patient_id, document_id, assigned_by, assigned_at, expires_at, status, context) VALUES
('pd-003',
 'patient-francesco-001',
 'doc-financial-001',
 'admin-001',
 '2024-12-12T10:00:00Z',
 '2024-12-26T23:59:59Z',
 'assigned',
 '{
   "assignment_reason": "Payment terms for treatment package",
   "priority": "medium",
   "package_value": 149900
 }');

-- Sample Patient Answers (for completed questionnaire)
-- ===================================================

-- Elena Verdi's Medical History answers
INSERT INTO patient_answers (_id, patient_questionnaire_id, question_id, answer_text, answer_choices, answered_at) VALUES
('pa-001', 'pq-001', 'mh-001', 'Yes', NULL, '2024-12-11T14:35:00Z'),
('pa-002', 'pq-001', 'mh-002', 'Penicillin - causes skin rash and hives. Shellfish - mild digestive upset.', NULL, '2024-12-11T14:37:00Z'),
('pa-003', 'pq-001', 'mh-003', NULL, '["Supplements and vitamins", "Over-the-counter medications"]', '2024-12-11T14:40:00Z'),
('pa-004', 'pq-001', 'mh-004', 'No', NULL, '2024-12-11T14:42:00Z'),
('pa-005', 'pq-001', 'mh-006', NULL, '["None of the above"]', '2024-12-11T14:45:00Z');

-- Add a rating scale answer
INSERT INTO patient_answers (_id, patient_questionnaire_id, question_id, answer_number, answered_at) VALUES
('pa-006', 'pq-001', 'mh-007', 8, '2024-12-11T14:47:00Z');

-- Add date answer  
INSERT INTO patient_answers (_id, patient_questionnaire_id, question_id, answer_date, answered_at) VALUES
('pa-007', 'pq-001', 'mh-008', '1985-03-15', '2024-12-11T14:50:00Z');

-- Sample Patient Signatures
-- =========================

-- Elena Verdi's Privacy Notice signature
INSERT INTO patient_signatures (_id, patient_document_id, patient_id, signature_data, signature_type, ip_address, user_agent, timestamp, verification_data) VALUES
('ps-001',
 'pd-001',
 'patient-elena-001',
 'Elena Maria Verdi',
 'typed',
 '192.168.1.100',
 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
 '2024-12-10T14:05:00Z',
 '{
   "location": "Milan, Italy",
   "session_id": "sess_elena_001",
   "consent_checkboxes": ["privacy_understood", "data_processing_agreed", "communications_consent"]
 }');

-- Create indexes for better performance
-- ====================================

-- These would typically be in a separate migration, but included here for completeness
-- CREATE INDEX IF NOT EXISTS idx_questionnaires_category ON questionnaires(category);
-- CREATE INDEX IF NOT EXISTS idx_questionnaires_active ON questionnaires(is_active);
-- CREATE INDEX IF NOT EXISTS idx_patient_questionnaires_patient ON patient_questionnaires(patient_id);
-- CREATE INDEX IF NOT EXISTS idx_patient_questionnaires_status ON patient_questionnaires(status);
-- CREATE INDEX IF NOT EXISTS idx_patient_questionnaires_due ON patient_questionnaires(due_date);
-- CREATE INDEX IF NOT EXISTS idx_patient_documents_patient ON patient_documents(patient_id);
-- CREATE INDEX IF NOT EXISTS idx_patient_documents_status ON patient_documents(status);
-- CREATE INDEX IF NOT EXISTS idx_patient_answers_questionnaire ON patient_answers(patient_questionnaire_id);
-- CREATE INDEX IF NOT EXISTS idx_patient_signatures_document ON patient_signatures(patient_document_id);

-- Summary Statistics View (for reporting)
-- =======================================

-- This would create a view to get questionnaire statistics
-- CREATE OR REPLACE VIEW questionnaire_stats AS
-- SELECT 
--     q._id,
--     q.title,
--     q.category,
--     q.is_required,
--     COUNT(pq._id) as total_assignments,
--     COUNT(CASE WHEN pq.status = 'completed' THEN 1 END) as completed_assignments,
--     COUNT(CASE WHEN pq.status = 'in_progress' THEN 1 END) as in_progress_assignments,
--     COUNT(CASE WHEN pq.status = 'assigned' THEN 1 END) as pending_assignments,
--     AVG(CASE WHEN pq.completed_at IS NOT NULL AND pq.started_at IS NOT NULL 
--         THEN EXTRACT(EPOCH FROM (pq.completed_at - pq.started_at))/60 END) as avg_completion_minutes
-- FROM questionnaires q
-- LEFT JOIN patient_questionnaires pq ON q._id = pq.questionnaire_id
-- WHERE q.is_active = true
-- GROUP BY q._id, q.title, q.category, q.is_required;

COMMIT;

-- End of Questionnaire and Document Seed Data
-- ===========================================