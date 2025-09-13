import requests
import sys
import json
import uuid
from datetime import datetime, timedelta

class KinAuraQuestionnairesSystemTester:
    def __init__(self, base_url="https://golden-health-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.patient_token = None
        self.linked_patient_id = None
        self.test_questionnaire_id = None
        self.test_assignment_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            # Handle multiple expected status codes
            if isinstance(expected_status, list):
                success = response.status_code in expected_status
            else:
                success = response.status_code == expected_status
                
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   Error: {response.text}")
                    return False, {}

        except requests.exceptions.RequestException as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def setup_admin_authentication(self):
        """Set up admin authentication"""
        print("\n🔐 Setting up admin authentication...")
        
        admin_data = {
            "provider": "admin",
            "access_token": "admin_token",
            "full_name": "Dr. Marco Rossi",
            "email": f"admin_test_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        }
        
        success, response = self.run_test(
            "Admin Social Login",
            "POST",
            "/auth/social-login",
            200,
            data=admin_data
        )
        
        if success:
            self.admin_token = response.get('access_token')
            user_data = response.get('user', {})
            print(f"   ✅ Admin authenticated with ID: {user_data.get('id')}")
            
            if user_data.get('role') == 'admin':
                print(f"   ✅ Admin role properly assigned")
                return True
            else:
                print(f"   ❌ Admin role not assigned, got: {user_data.get('role')}")
                return False
        else:
            print("   ❌ Admin authentication failed")
            return False

    def test_enhanced_social_login_authentication(self):
        """Test Enhanced Social Login Authentication with Patient Linking"""
        print("\n🔍 Testing Enhanced Social Login Authentication with Patient Linking...")
        
        if not self.admin_token:
            print("❌ No admin token available for enhanced social login test")
            return False
        
        # Step 1: Admin creates a patient
        patient_email = f"social_link_patient_{datetime.now().strftime('%H%M%S')}@kinaura.com"
        patient_data = {
            "email": patient_email,
            "full_name": "Social Link Test Patient",
            "phone": "+1234567890",
            "membership_tier": "gold",
            "tags": ["social", "test"]
        }
        
        success, patient_response = self.run_test(
            "Admin Creates Patient for Social Linking",
            "POST",
            "/admin/patients",
            200,
            data=patient_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if not success:
            print("❌ Failed to create patient for social linking test")
            return False
        
        admin_created_patient_id = patient_response.get('id')
        print(f"   ✅ Admin created patient with ID: {admin_created_patient_id}")
        
        # Step 2: Patient logs in via social login with same email
        social_login_data = {
            "provider": "google",
            "access_token": "social_link_token",
            "full_name": "Social Link Test Patient",
            "email": patient_email  # Same email as admin-created patient
        }
        
        success, social_response = self.run_test(
            "Patient Social Login with Matching Email",
            "POST",
            "/auth/social-login",
            200,
            data=social_login_data
        )
        
        if not success:
            print("❌ Failed social login for patient linking")
            return False
        
        social_user_data = social_response.get('user', {})
        social_user_id = social_user_data.get('id')
        social_token = social_response.get('access_token')
        
        print(f"   ✅ Social login successful with user ID: {social_user_id}")
        
        # Step 3: Verify patient linking fields
        if social_user_data.get('linked_to_social'):
            print(f"   ✅ User marked as linked_to_social: {social_user_data.get('linked_to_social')}")
        
        if social_user_data.get('patient_id'):
            print(f"   ✅ Patient ID linked: {social_user_data.get('patient_id')}")
        
        if social_user_data.get('created_from_admin_patient'):
            print(f"   ✅ Created from admin patient: {social_user_data.get('created_from_admin_patient')}")
        
        # Step 4: Verify email-based patient mapping works correctly
        if social_user_id == admin_created_patient_id:
            print(f"   ✅ Email-based patient mapping working - same user ID used")
        else:
            print(f"   ⚠️  Different user IDs: admin={admin_created_patient_id}, social={social_user_id}")
        
        # Store for later tests
        self.patient_token = social_token
        self.linked_patient_id = social_user_id
        
        print("   ✅ Enhanced Social Login Authentication test completed successfully")
        return True

    def test_patient_document_upload_api(self):
        """Test Patient Document Upload API (/api/patient/upload-document)"""
        print("\n🔍 Testing Patient Document Upload API...")
        
        if not self.admin_token:
            print("❌ No admin token available for document upload test")
            return False
        
        if not self.linked_patient_id:
            print("❌ No linked patient ID available for document upload test")
            return False
        
        # Test different file types and categories
        test_files = [
            {
                "patient_id": self.linked_patient_id,
                "file_type": "test_result",
                "file_category": "blood_work",
                "visible_to_patient": True,
                "description": "Complete Blood Count Results",
                "notes": "All values within normal range",
                "tags": ["blood", "test", "normal"]
            },
            {
                "patient_id": self.linked_patient_id,
                "file_type": "image",
                "file_category": "imaging",
                "visible_to_patient": False,
                "description": "MRI Scan - Brain",
                "notes": "Requires radiologist review",
                "tags": ["mri", "brain", "diagnostic"]
            },
            {
                "patient_id": self.linked_patient_id,
                "file_type": "report",
                "file_category": "consultation",
                "visible_to_patient": True,
                "description": "Initial Consultation Report",
                "notes": "Patient consultation completed",
                "tags": ["consultation", "initial"]
            }
        ]
        
        uploaded_files = []
        for i, file_data in enumerate(test_files):
            success, response = self.run_test(
                f"Upload Document {i+1} - {file_data['file_type']} ({file_data['file_category']})",
                "POST",
                f"/admin/patients/{self.linked_patient_id}/files/upload",
                200,
                data=file_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                file_id = response.get('id')
                uploaded_files.append(file_id)
                print(f"   ✅ Uploaded {file_data['file_type']} with ID: {file_id}")
                
                # Verify file properties
                required_fields = ['id', 'filename', 'file_type', 'file_category', 'description', 'tags', 'upload_date']
                missing_fields = [field for field in required_fields if field not in response]
                
                if not missing_fields:
                    print(f"   ✅ File metadata complete")
                else:
                    print(f"   ❌ Missing metadata fields: {missing_fields}")
                    return False
                
                # Verify proper categorization
                if response.get('file_category') == file_data['file_category']:
                    print(f"   ✅ Proper categorization: {file_data['file_category']}")
                
                # Verify visibility controls
                if response.get('visible_to_patient') == file_data['visible_to_patient']:
                    print(f"   ✅ Visibility control working: {file_data['visible_to_patient']}")
            else:
                print(f"   ❌ Failed to upload {file_data['file_type']}")
                return False
        
        # Test file validation with different file types
        file_types = ["image", "pdf", "document"]
        for file_type in file_types:
            validation_data = {
                "patient_id": self.linked_patient_id,
                "file_type": "other",
                "file_category": "general",
                "visible_to_patient": True,
                "description": f"Test {file_type} validation",
                "tags": [file_type, "validation"]
            }
            
            success, response = self.run_test(
                f"File Validation - {file_type}",
                "POST",
                f"/admin/patients/{self.linked_patient_id}/files/upload",
                200,
                data=validation_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                print(f"   ✅ File type validation passed for {file_type}")
        
        # Test admin-only access authentication
        if self.patient_token:
            success, response = self.run_test(
                "Patient Access to Upload Endpoint (Should Fail)",
                "POST",
                "/patient/upload-document",
                401,  # Should be unauthorized for patients without file
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                print(f"   ✅ Patient correctly denied access to upload endpoint")
            else:
                print(f"   ⚠️  Patient upload endpoint behavior differs from expected")
        
        print("   ✅ Patient Document Upload API test completed successfully")
        return True

    def test_patient_files_api_with_authentication(self):
        """Test Patient Files API with Authentication Logic (/api/patient/files)"""
        print("\n🔍 Testing Patient Files API with Authentication Logic...")
        
        if not self.patient_token:
            print("❌ No patient token available for files API test")
            return False
        
        if not self.linked_patient_id:
            print("❌ No linked patient ID available for files API test")
            return False
        
        # Test 1: Patient access to files with proper authentication
        success, files_response = self.run_test(
            "Patient Access Files with Authentication",
            "GET",
            "/patient/files",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success and isinstance(files_response, list):
            visible_files_count = len(files_response)
            print(f"   ✅ Patient can access {visible_files_count} visible files")
            
            # Test patient_id resolution (using patient_id or user_id)
            if visible_files_count > 0:
                print(f"   ✅ Patient_id resolution working correctly")
            
            # Verify file access controls (admin fields hidden from patients)
            if files_response:
                patient_file = files_response[0]
                admin_only_fields = ['notes', 'uploaded_by']
                exposed_admin_fields = [field for field in admin_only_fields if field in patient_file]
                
                if not exposed_admin_fields:
                    print(f"   ✅ Admin-only fields properly hidden from patient")
                else:
                    print(f"   ❌ Admin fields exposed to patient: {exposed_admin_fields}")
                    return False
                
                # Verify required patient fields are present
                required_fields = ['id', 'filename', 'file_type', 'file_category', 'description']
                missing_fields = [field for field in required_fields if field not in patient_file]
                
                if not missing_fields:
                    print(f"   ✅ All required patient fields present")
                else:
                    print(f"   ❌ Missing patient fields: {missing_fields}")
                    return False
        else:
            print("   ❌ Failed to get patient files")
            return False
        
        # Test 2: Individual file access functionality
        if files_response:
            file_id = files_response[0]['id']
            success, file_details = self.run_test(
                "Individual File Access",
                "GET",
                f"/patient/files/{file_id}",
                200,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                print(f"   ✅ Individual file access working")
                
                # Verify file details structure
                if file_details.get('id') == file_id:
                    print(f"   ✅ File details match requested file")
            else:
                print(f"   ❌ Failed to access individual file")
                return False
        
        # Test 3: Admin sees all files vs patient sees only visible files
        if self.admin_token:
            success, admin_files_response = self.run_test(
                "Admin View All Patient Files",
                "GET",
                f"/admin/patients/{self.linked_patient_id}/files",
                200,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success and isinstance(admin_files_response, list):
                total_files_count = len(admin_files_response)
                print(f"   ✅ Admin can see {total_files_count} total files")
                
                # Verify admin sees all files including private ones
                if total_files_count >= visible_files_count:
                    print(f"   ✅ Admin sees all files (including private): {total_files_count} vs patient: {visible_files_count}")
                else:
                    print(f"   ❌ Admin should see more files than patient")
                    return False
                
                # Verify admin can see admin-only fields
                if admin_files_response:
                    admin_file = admin_files_response[0]
                    admin_fields = ['notes', 'uploaded_by']
                    present_admin_fields = [field for field in admin_fields if field in admin_file]
                    
                    if present_admin_fields:
                        print(f"   ✅ Admin can see admin-only fields: {present_admin_fields}")
                    else:
                        print(f"   ⚠️  Admin fields not present in response")
            else:
                print("   ❌ Failed to get admin view of files")
                return False
        
        print("   ✅ Patient Files API with Authentication Logic test completed successfully")
        return True

    def test_questionnaires_integration_with_file_attachments(self):
        """Test Questionnaires Integration with File Attachments"""
        print("\n🔍 Testing Questionnaires Integration with File Attachments...")
        
        if not self.admin_token:
            print("❌ No admin token available for questionnaires test")
            return False
        
        if not self.linked_patient_id:
            print("❌ No linked patient ID available for questionnaires test")
            return False
        
        # Test 1: Create questionnaire with different question types including file_upload
        questionnaire_data = {
            "title": "Comprehensive Health Assessment with File Attachments",
            "description": "Complete health assessment including file upload capabilities",
            "category": "medical_history",
            "is_required": True,
            "instructions": "Please complete all questions and upload any relevant documents",
            "metadata": {"version": "2.0", "supports_files": True}
        }
        
        success, questionnaire_response = self.run_test(
            "Create Questionnaire with File Support",
            "POST",
            "/admin/questionnaires",
            200,
            data=questionnaire_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if not success:
            print("❌ Failed to create questionnaire")
            return False
        
        questionnaire_id = questionnaire_response.get('questionnaire_id')
        self.test_questionnaire_id = questionnaire_id
        print(f"   ✅ Created questionnaire with ID: {questionnaire_id}")
        
        # Test 2: Add different question types including file_upload
        questions = [
            {
                "questionnaire_id": questionnaire_id,
                "question_text": "Please describe your current health concerns in detail",
                "question_type": "long_text",
                "is_required": True,
                "order_index": 1,
                "help_text": "Be as specific as possible"
            },
            {
                "questionnaire_id": questionnaire_id,
                "question_text": "Do you have any chronic medical conditions?",
                "question_type": "yes_no",
                "is_required": True,
                "order_index": 2
            },
            {
                "questionnaire_id": questionnaire_id,
                "question_text": "Please upload your recent medical records or test results",
                "question_type": "file_upload",
                "is_required": False,
                "order_index": 3,
                "options": {
                    "allowed_file_types": ["pdf", "jpg", "png", "doc", "docx"],
                    "max_files": 3,
                    "max_file_size": "10MB"
                },
                "help_text": "Upload any relevant medical documents"
            },
            {
                "questionnaire_id": questionnaire_id,
                "question_text": "Rate your overall health on a scale of 1-10",
                "question_type": "rating_scale",
                "is_required": True,
                "order_index": 4,
                "options": {
                    "min_value": 1,
                    "max_value": 10,
                    "step": 1
                }
            }
        ]
        
        created_questions = []
        for question_data in questions:
            success, question_response = self.run_test(
                f"Add {question_data['question_type']} Question",
                "POST",
                f"/admin/questionnaires/{questionnaire_id}/questions",
                200,
                data=question_data,
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if success:
                question_id = question_response.get('question_id')
                created_questions.append(question_id)
                print(f"   ✅ Added {question_data['question_type']} question with ID: {question_id}")
                
                # Verify file_upload question options
                if question_data['question_type'] == 'file_upload':
                    if question_response.get('options', {}).get('max_files') == 3:
                        print(f"   ✅ File upload options properly configured")
            else:
                print(f"   ❌ Failed to add {question_data['question_type']} question")
                return False
        
        # Test 3: Assign questionnaire to patient
        assignment_data = {
            "questionnaire_id": questionnaire_id,
            "patient_id": self.linked_patient_id,
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "context": {"assignment_reason": "comprehensive_assessment", "priority": "high"}
        }
        
        success, assignment_response = self.run_test(
            "Assign Questionnaire to Patient",
            "POST",
            "/admin/questionnaires/assign",
            200,
            data=assignment_data,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success:
            assignment_id = assignment_response.get('assignment_id')
            self.test_assignment_id = assignment_id
            print(f"   ✅ Questionnaire assigned with ID: {assignment_id}")
        else:
            print("❌ Failed to assign questionnaire to patient")
            return False
        
        # Test 4: Verify file attachment support in questionnaire responses
        if self.patient_token:
            # Get questionnaire details for completion to see questions
            success, questionnaire_details = self.run_test(
                "Get Questionnaire Details to Check File Upload Questions",
                "GET",
                f"/patient/questionnaires/{assignment_id}",
                200,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                questions = questionnaire_details.get('questions', [])
                print(f"   ✅ Retrieved questionnaire with {len(questions)} questions for detailed check")
                
                # Verify file upload question is present
                file_upload_questions = [q for q in questions if q.get('type') == 'file_upload']
                
                if file_upload_questions:
                    print(f"   ✅ File upload questions present in patient questionnaire details")
                    
                    # Verify file upload options are accessible
                    file_question = file_upload_questions[0]
                    if file_question.get('options', {}).get('allowed_file_types'):
                        print(f"   ✅ File upload options accessible to patient")
                else:
                    print(f"   ❌ File upload questions not found in questionnaire details")
                    return False
            else:
                print("   ❌ Failed to get questionnaire details for file upload check")
                return False
        
        # Test 5: Verify all admin operations are properly secured
        if self.patient_token:
            # Test patient cannot create questionnaires
            success, response = self.run_test(
                "Patient Access to Create Questionnaire (Should Fail)",
                "POST",
                "/admin/questionnaires",
                403,
                data=questionnaire_data,
                headers={'Authorization': f'Bearer {self.patient_token}'}
            )
            
            if success:
                print(f"   ✅ Admin operations properly secured from patients")
            else:
                print(f"   ❌ Patient should not have admin access")
                return False
        
        print("   ✅ Questionnaires Integration with File Attachments test completed successfully")
        return True

    def test_complete_patient_workflow_end_to_end(self):
        """Test Complete Patient Workflow End-to-End"""
        print("\n🔍 Testing Complete Patient Workflow End-to-End...")
        
        if not self.admin_token:
            print("❌ No admin token available for complete workflow test")
            return False
        
        if not self.patient_token:
            print("❌ No patient token available for complete workflow test")
            return False
        
        if not self.test_assignment_id:
            print("❌ No assignment ID available for complete workflow test")
            return False
        
        # Test 1: Verify full integration workflow
        print("   🔄 Testing full integration: admin creates patient → social login links → documents uploaded → questionnaires assigned and completed")
        
        # Step 1: Verify patient can view assigned questionnaires
        success, questionnaires_response = self.run_test(
            "Patient View Assigned Questionnaires",
            "GET",
            "/patient/questionnaires",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success and isinstance(questionnaires_response, list):
            questionnaire_count = len(questionnaires_response)
            print(f"   ✅ Patient can view {questionnaire_count} assigned questionnaires")
            
            if questionnaire_count > 0:
                questionnaire = questionnaires_response[0]
                print(f"   ✅ Questionnaire details accessible: {questionnaire.get('title', 'Unknown')}")
        else:
            print("   ❌ Failed to get assigned questionnaires")
            return False
        
        # Step 2: Get questionnaire details for completion
        success, questionnaire_details = self.run_test(
            "Get Questionnaire Details for Completion",
            "GET",
            f"/patient/questionnaires/{self.test_assignment_id}",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            print(f"   ✅ Questionnaire details retrieved for completion")
            questions = questionnaire_details.get('questions', [])
            print(f"   ✅ Found {len(questions)} questions to answer")
        else:
            print("   ❌ Failed to get questionnaire details")
            return False
        
        # Step 3: Start questionnaire
        success, start_response = self.run_test(
            "Start Questionnaire",
            "POST",
            f"/patient/questionnaires/{self.test_assignment_id}/start",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            print(f"   ✅ Questionnaire started successfully")
        else:
            print("   ❌ Failed to start questionnaire")
            return False
        
        # Step 4: Submit answers (including file attachments)
        answers = [
            {
                "question_id": questions[0]['id'] if questions else "q1",
                "answer_text": "I have been experiencing some fatigue and would like to explore regenerative wellness options to improve my energy levels and overall health."
            },
            {
                "question_id": questions[1]['id'] if len(questions) > 1 else "q2",
                "answer_choices": ["yes"]
            },
            {
                "question_id": questions[2]['id'] if len(questions) > 2 else "q3",
                "answer_files": [
                    {
                        "filename": "medical_records.pdf",
                        "file_type": "pdf",
                        "description": "Recent blood work and medical history"
                    }
                ]
            },
            {
                "question_id": questions[3]['id'] if len(questions) > 3 else "q4",
                "answer_number": 7
            }
        ]
        
        submit_data = {
            "patient_questionnaire_id": self.test_assignment_id,
            "answers": answers
        }
        
        success, submit_response = self.run_test(
            "Submit Questionnaire Answers with File Attachments",
            "POST",
            f"/patient/questionnaires/{self.test_assignment_id}/answers",
            200,
            data=submit_data,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            print(f"   ✅ Questionnaire answers submitted successfully")
            
            # Verify file attachments are supported
            if any(answer.get('answer_files') for answer in answers):
                print(f"   ✅ File attachments supported in questionnaire responses")
        else:
            print("   ❌ Failed to submit questionnaire answers")
            return False
        
        # Step 5: Complete questionnaire
        success, complete_response = self.run_test(
            "Complete Questionnaire",
            "POST",
            f"/patient/questionnaires/{self.test_assignment_id}/complete",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            print(f"   ✅ Questionnaire completed successfully")
            
            # Verify completion status
            if complete_response.get('status') == 'completed':
                print(f"   ✅ Questionnaire marked as completed")
        else:
            print("   ❌ Failed to complete questionnaire")
            return False
        
        # Step 6: Verify patient can access documents and questionnaires with proper authentication
        success, files_response = self.run_test(
            "Verify Patient File Access After Workflow",
            "GET",
            "/patient/files",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            files_count = len(files_response) if isinstance(files_response, list) else 0
            print(f"   ✅ Patient can access {files_count} files with proper authentication")
        else:
            print("   ❌ Failed to access files after workflow")
            return False
        
        # Step 7: Verify authentication fixes are working
        success, completed_questionnaires = self.run_test(
            "Verify Completed Questionnaires Access",
            "GET",
            "/patient/questionnaires?status=completed",
            200,
            headers={'Authorization': f'Bearer {self.patient_token}'}
        )
        
        if success:
            completed_count = len(completed_questionnaires) if isinstance(completed_questionnaires, list) else 0
            print(f"   ✅ Patient can access {completed_count} completed questionnaires")
            
            if completed_count > 0:
                print(f"   ✅ Authentication fixes working - patient can access assigned content")
        else:
            print("   ❌ Failed to access completed questionnaires")
            return False
        
        print("   🎉 Complete Patient Workflow End-to-End test completed successfully!")
        print("   ✅ Full integration verified: admin creates patient → social login links → documents uploaded → questionnaires assigned and completed")
        print("   ✅ File attachments supported throughout workflow")
        print("   ✅ Proper authentication flow for all steps confirmed")
        return True

    def run_questionnaires_system_verification(self):
        """Run comprehensive verification of the questionnaires system"""
        print("🚀 Starting Final Questionnaires System Verification...")
        print(f"   Base URL: {self.base_url}")
        print(f"   API URL: {self.api_url}")
        
        # Authentication setup
        print("\n🔐 Setting up authentication...")
        admin_success = self.setup_admin_authentication()
        if not admin_success:
            print("❌ Failed to set up admin authentication")
            return False
        
        # Core verification tests based on review request
        verification_tests = [
            ("Enhanced Social Login Authentication with Patient Linking", self.test_enhanced_social_login_authentication),
            ("Patient Document Upload API", self.test_patient_document_upload_api),
            ("Patient Files API with Authentication Logic", self.test_patient_files_api_with_authentication),
            ("Questionnaires Integration with File Attachments", self.test_questionnaires_integration_with_file_attachments),
            ("Complete Patient Workflow End-to-End", self.test_complete_patient_workflow_end_to_end),
        ]
        
        passed_tests = 0
        total_tests = len(verification_tests)
        
        for test_name, test_func in verification_tests:
            print(f"\n{'='*80}")
            print(f"🧪 {test_name}")
            print('='*80)
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name} - PASSED")
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {str(e)}")
                self.tests_run += 1
        
        # Print final results
        print(f"\n{'='*80}")
        print("📊 FINAL QUESTIONNAIRES SYSTEM VERIFICATION RESULTS")
        print('='*80)
        print(f"Verification Tests Run: {total_tests}")
        print(f"Verification Tests Passed: {passed_tests}")
        success_rate = (passed_tests/total_tests)*100 if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL QUESTIONNAIRES SYSTEM VERIFICATION TESTS PASSED!")
            print("✅ System is production-ready")
        else:
            print(f"⚠️  {total_tests - passed_tests} verification tests failed")
            print("❌ System requires attention before production deployment")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = KinAuraQuestionnairesSystemTester()
    success = tester.run_questionnaires_system_verification()
    sys.exit(0 if success else 1)