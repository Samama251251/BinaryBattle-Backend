from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
import os
from dotenv import load_dotenv
from .models import User, Challenge, Submission
class SubmissionAPIView(APIView):
    def post(self, request):
        try:
            load_dotenv()
            
            # Extract and validate required fields
            required_fields = {
                'code': request.data.get('code'),
                'language': request.data.get('language'),
                'challengeId': request.data.get('challengeId'),
                'userEmail': request.data.get('userEmail'),
                'testCases': request.data.get('testCases')
            }
            
            # Check for missing fields and return specific error
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                return Response({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get user and challenge with specific error handling
            try:
                user = User.objects.get(email=required_fields['userEmail'])
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found',
                    'detail': f"No user found with email {required_fields['userEmail']}"
                }, status=status.HTTP_404_NOT_FOUND)

            try:
                challenge = Challenge.objects.get(id=required_fields['challengeId'])
            except Challenge.DoesNotExist:
                return Response({
                    'error': 'Challenge not found',
                    'detail': f"No challenge found with ID {required_fields['challengeId']}"
                }, status=status.HTTP_404_NOT_FOUND)

            # Validate test cases
            test_cases = request.data.get('testCases', [])
            if not test_cases:
                return Response({
                    'error': 'Test cases are required',
                    'detail': 'At least one test case must be provided'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate test case format
            first_test = test_cases[0]
            if 'input' not in first_test or 'output' not in first_test:
                return Response({
                    'error': 'Invalid test case format',
                    'detail': 'Each test case must contain input and output fields'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Prepare Judge0 submission
            judge0_data = {
                'source_code': required_fields['code'],
                'language_id': 71,  # Python
                'stdin': first_test['input'],
                'expected_output': first_test['output']
            }

            # Send to Judge0 with error handling
            print("I am sending to judge0 with this data", judge0_data)
            try:
                judge0_response = requests.post(
                    f'{os.getenv("JUDGE0_API_URL")}/submissions?base64_encoded=false&wait=false',
                    json=judge0_data,
                    headers={
                        'X-RapidAPI-Host': os.getenv('JUDGE0_API_HOST'),
                        'X-RapidAPI-Key': os.getenv('JUDGE0_API_KEY')
                    }
                )
            except requests.exceptions.RequestException as e:
                return Response({
                    'error': 'Judge0 API connection error',
                    'detail': str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            if judge0_response.status_code != 201:
                return Response({
                    'error': 'Judge0 submission failed',
                    'detail': judge0_response.json(),
                    'status_code': judge0_response.status_code
                }, status=status.HTTP_502_BAD_GATEWAY)

            token = judge0_response.json().get('token')
            if not token:
                return Response({
                    'error': 'Invalid Judge0 response',
                    'detail': 'No token received from Judge0'
                }, status=status.HTTP_502_BAD_GATEWAY)

            # Save submission to database with error handling
            try:
                submission = Submission.objects.create(
                    user=user,
                    challenge=challenge,
                    code=required_fields['code'],
                    language=required_fields['language'],
                    judge0_token=token
                )
            except Exception as e:
                return Response({
                    'error': 'Database error',
                    'detail': f'Failed to save submission: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                'token': token,
                'submissionId': submission.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': 'Unexpected error',
                'detail': str(e),
                'type': type(e).__name__
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            load_dotenv()
            token = request.query_params.get('token')
            if not token:
                return Response({
                    'error': 'Token is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get submission status from Judge0
            response = requests.get(
                f'{os.getenv("JUDGE0_API_URL")}/submissions/{token}',
                headers={
                    'X-RapidAPI-Host': os.getenv('JUDGE0_API_HOST'),
                    'X-RapidAPI-Key': os.getenv('JUDGE0_API_KEY')
                }
            )

            if response.status_code != 200:
                raise Exception('Failed to fetch submission status')

            result = response.json()

            # Update submission in database
            submission = Submission.objects.get(judge0_token=token)
            submission.result = result
            submission.status = 'completed' if result.get('status', {}).get('id') == 3 else 'processing'
            submission.save()

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch submission status',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
