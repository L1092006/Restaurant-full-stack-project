from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.
class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username:
            return Response({"error": "Missing username"}, status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"error": "Missing password"}, status.HTTP_400_BAD_REQUEST)
        

        # Authenticate
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status.HTTP_400_BAD_REQUEST)
        
        # Generate the refresh token
        refresh = RefreshToken.for_user(user)
        

        # Return the user email but not username because the frontend already had username
        response = Response({"message": "Successfully logged in!", "email": user.email}, status.HTTP_200_OK)


        # Save the tokens in Cookie
        response.set_cookie(
            "access_token",
            # Generate the access token
            str(refresh.access_token),
            httponly=True,
            # Set secure to True in production
            secure=False,
            samesite="None"
        )
        response.set_cookie(
            "refresh_token",
            str(refresh),
            httponly=True,
            # Set secure to True in production
            secure=False,
            samesite="None"
        )
         
        return response
    

class RefreshView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"message": "Do not have refresh token in cookies, login again"}, status.HTTP_400_BAD_REQUEST)
        
        # Validate the refresh token
        try:
            new_refresh = RefreshToken(refresh_token)
        except Exception:
            return Response({"message": "The refresh token is invalid"}, status.HTTP_400_BAD_REQUEST)

        response = Response({"message": "Successfully refresh!"}, status.HTTP_200_OK)
        # Generate and save a new access token in the cookies
        response.set_cookie(
            "access_token",
            new_refresh.access_token,
            httponly=True,
            # Set secure to True in production
            secure=False,
            samesite="None"
        )

        return response
    
class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Successfully Logout!"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
