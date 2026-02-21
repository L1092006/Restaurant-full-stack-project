from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import environ
from pathlib import Path



# Create your views here.

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env.read_env(BASE_DIR / '.env')

ALLOWED_ORIGINS = env.list("ALLOWED_ORIGINS")

# AUTHENTICATION VIEWS
REFRESH_COOKIE = {
    "name": "refresh",
    "httpOnly": True,
    # PRODUCTION - change secure to True
    "secure": False,
    "samesite": "None",
    "path": "/api/auth/",
    # Set cookie expired time to 7 days
    "max_age": 60 * 60 * 24 * 7
}

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
            return Response({"error": "Invalid credentials"}, status.HTTP_401_UNAUTHORIZED)
        
        # Generate the refresh token
        refresh = RefreshToken.for_user(user)
        

        # Return the user email but not username because the frontend already had username
        response = Response({"message": "Info: Successfully logged in!", "access": str(refresh.access_token), "email": user.email}, status.HTTP_200_OK)


        # Save the tokens in Cookie
        response.set_cookie(
            REFRESH_COOKIE["name"],
            str(refresh),
            httponly=REFRESH_COOKIE["httpOnly"],
            secure=REFRESH_COOKIE["secure"],
            samesite=REFRESH_COOKIE["samesite"],
            path=REFRESH_COOKIE["path"],
            max_age=REFRESH_COOKIE["max_age"]
        )
         
        return response
    

class RefreshView(APIView):
    def post(self, request):

        # Check if request come from an allowed origin. Allow if there's no Origin header
        origin = request.headers.get("Origin")
        if origin and not origin in ALLOWED_ORIGINS:
            return Response({"message": "Error: Forbidden origin"}, status=status.HTTP_403_FORBIDDEN)
       
        refresh_str = request.COOKIES.get(REFRESH_COOKIE["name"])
        if not refresh_str:
            return Response({"message": "Error: Do not have refresh token in cookies, login again"}, status.HTTP_401_UNAUTHORIZED)
        
        # Validate the refresh token
        try:
            refresh = RefreshToken(refresh_str)
        except Exception:
            return Response({"message": "Error: The refresh token is invalid"}, status.HTTP_401_UNAUTHORIZED)

        

        # Get User model based on the user id in refresh token. Return 401 us the user is missing
        User = get_user_model()
        try: 
            user = User.objects.get(id=refresh["user_id"])
        except User.DoesNotExist:
            return Response({"message": "Error: User no longer exists"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Message to send back. Success by default
        message = "Info: Successfully refresh!"
        # Blacklist the old token
        try:
            refresh.blacklist()
        except Exception:
            message = "Warning: Cannot blacklist the refresh token"

        # Generate a new refresh token
        new_refresh = RefreshToken.for_user(user)

        response = Response({"message": message, "access": str(new_refresh.access_token)}, status.HTTP_200_OK)
        # Generate and save a new refresh token token in the cookies
        response.set_cookie(
            REFRESH_COOKIE["name"],
            str(new_refresh),
            httponly=REFRESH_COOKIE["httpOnly"],
            secure=REFRESH_COOKIE["secure"],
            samesite=REFRESH_COOKIE["samesite"],
            path=REFRESH_COOKIE["path"],
            max_age=REFRESH_COOKIE["max_age"]
        )
        return response
    
class LogoutView(APIView):
    def post(self, request):
        refresh_str = request.COOKIES.get(REFRESH_COOKIE["name"])
        response = None
        # Always return 200 success status code in this view, but if the refresh token is invalid or missing, or the user has issues, warn the client
        if refresh_str:
            try:
                refresh = RefreshToken(refresh_str)
                refresh.blacklist()
            except Exception:
                response = Response({"message": "Warning: Invalid refresh token. May have not logged out yet."}, status=status.HTTP_200_OK)
        else:
            response = Response({"message": "Warning: No refresh token in the cookies. May have not logged out yet."}, status=status.HTTP_200_OK)

        if not response:
            response = Response({"message": "Info: Successfully Logout!"}, status=status.HTTP_200_OK)
        response.delete_cookie(REFRESH_COOKIE["name"], path=REFRESH_COOKIE["path"])
        return response
