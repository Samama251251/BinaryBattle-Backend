from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User

class UpdateScoreView(APIView):
    def post(self, request):
        try:
            print("I came here to update score")
            username = request.data.get('username')
            
            if not username:
                return Response({
                    'error': 'Username is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(username=username)
                user.score += 1
                user.save()
                
                return Response({
                    'message': 'Score updated successfully',
                    'new_score': user.score
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'error': f'User {username} not found'
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'error': 'Unexpected error occurred',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get(self, request):
        try:
            # Get all users ordered by score in descending order
            users = User.objects.all().order_by('-score')
            
            # Create list of user scores
            user_scores = []
            for user in users:
                user_scores.append({
                    'username': user.username,
                    'score': user.score,
                })
            
            return Response(user_scores, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Unexpected error occurred',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

