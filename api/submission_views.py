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
            print("I came here")
            # Extract data from request
            code = request.data.get('code')
            language_id = request.data.get('language')
            challenge_id = request.data.get('challengeId')
            user_email = request.data.get('userEmail')
            print(code, language_id, challenge_id, user_email)

            if not all([code, language_id, challenge_id, user_email]):
                return Response({
                    'error': 'Missing required fields'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get user and challenge
            user = User.objects.get(email=user_email)
            challenge = Challenge.objects.get(id=challenge_id)

            # Extract test cases from request
            test_cases = request.data.get('testCases', [])
            if not test_cases:
                return Response({
                    'error': 'Test cases are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # For now, let's test with the first test case
            first_test = test_cases[0]
            print(first_test['input'])
            print("I am here after first_test['input']")
            print(first_test['output'])
            print("I am here after first_test['output']")
            print(code)
            judge0_data = {
                'source_code': code,
                'language_id': 71,  # Python
                'stdin': first_test['input'],  # Use the input from test case
                'expected_output': first_test['output']  # Use the expected output from test case
            }
            print(judge0_data)

            # Send to Judge0
            judge0_response = requests.post(
                f'{os.getenv("JUDGE0_API_URL")}/submissions?base64_encoded=false&wait=false',
                json=judge0_data,
                headers={
                    'X-RapidAPI-Host': os.getenv('JUDGE0_API_HOST'),
                    'X-RapidAPI-Key': os.getenv('JUDGE0_API_KEY')
                }
            )
            print(f"Response Status Code: {judge0_response.status_code}")
            if judge0_response.status_code == 200:
                print("Response JSON:", judge0_response.json())
            else:
                print("Error Response:", judge0_response.json()) 
            print("Here is the judge0_response")
            print(judge0_response)  
            print("After judge0_response")
            print("I came after judge0_response")
            if judge0_response.status_code != 201:
                print("I came after judge0_response error")
                raise Exception('Failed to create Judge0 submission')

            token = judge0_response.json().get('token')
            print("i am before try ")

            # Save submission to database
            try:
                submission = Submission.objects.create(
                    user=user,
                    challenge=challenge,
                    code=code,
                    language=language_id,
                    judge0_token=token
                )
                print("I came after submission")
            except Exception as e:
                print("I came after submission error")
                print(e)
            return Response({
                'token': token,
                'submissionId': submission.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': 'Failed to process submission',
                'detail': str(e)
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
