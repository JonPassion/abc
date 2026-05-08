from rest_framework import status, generics, permissions, pagination
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db import models
from django.core.cache import cache
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .pagination import StandardResultsSetPagination, LargeResultsSetPagination, SmallResultsSetPagination

from .models import UserProfile, Like, Match, Message, MediaGallery, Post
from .serializers import (
    UserSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    UserRegisterSerializer, LikeSerializer, MatchSerializer, MessageSerializer,
    MediaGallerySerializer, PostSerializer, BrowseUserSerializer, DashboardStatsSerializer
)


# Custom Pagination for better performance
class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# Media Gallery View with pagination
class MediaGalleryView(generics.ListCreateAPIView):
    serializer_class = MediaGallerySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return MediaGallery.objects.filter(
            user=self.request.user
        ).select_related('user').order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Posts View with pagination
class PostListView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LargeResultsSetPagination
    
    def get_queryset(self):
        return Post.objects.select_related('user').prefetch_related('likes').order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Authentication Views
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Clear any cached user data
            cache.delete(f'user_profile_{user.id}')
            return Response({
                'user': UserSerializer(user).data,
                'message': 'User created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data['username'])
            response.data['user'] = UserSerializer(user).data
        return response


# User Profile Views
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Try to get from cache first
        cache_key = f'user_profile_{self.request.user.id}'
        cached_profile = cache.get(cache_key)
        if cached_profile:
            return cached_profile
        
        profile = self.request.user.profile
        # Cache for 5 minutes
        cache.set(cache_key, profile, 300)
        return profile


class UserProfileDetailView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = UserProfile.objects.select_related('user').all()
    lookup_field = 'user_id'
    lookup_url_kwarg = 'user_id'
    pagination_class = StandardResultsSetPagination


# Dashboard Stats
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@cache_page(60)  # Cache for 1 minute
def dashboard_stats(request):
    user = request.user
    cache_key = f'dashboard_stats_{user.id}'
    cached_stats = cache.get(cache_key)
    
    if cached_stats:
        return Response(cached_stats)
    
    matches_count = Match.objects.filter(
        models.Q(user1=user) | models.Q(user2=user)
    ).count()
    
    likes_received = Like.objects.filter(to_user=user).count()
    likes_given = Like.objects.filter(from_user=user).count()
    
    unread_messages = Message.objects.filter(
        match__in=Match.objects.filter(models.Q(user1=user) | models.Q(user2=user)),
        read=False
    ).exclude(sender=user).count()
    
    data = {
        'matches_count': matches_count,
        'likes_received': likes_received,
        'likes_given': likes_given,
        'unread_messages': unread_messages
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, data, 300)
    serializer = DashboardStatsSerializer(data)
    return Response(serializer.data)


# Browse & Matching Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@cache_page(30)  # Cache for 30 seconds
def browse_users(request):
    user = request.user
    profile = user.profile
    
    # Use select_related for better performance
    users = User.objects.select_related('profile').exclude(id=user.id)
    search_query = request.query_params.get('search', '').strip()
    
    # Filter hidden users
    users = users.exclude(profile__hide_from_search=True)
    
    # Search by username
    if search_query:
        users = users.filter(username__icontains=search_query)
    elif profile.looking_for and profile.looking_for != 'both':
        users = users.filter(profile__gender=profile.looking_for)
    
    # Exclude already liked (optimized query)
    liked_users = Like.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    users = users.exclude(id__in=liked_users)
    
    # Get single user for swipe-style browsing
    next_user = users.first()
    
    if next_user:
        serializer = BrowseUserSerializer(next_user, context={'request': request})
        return Response({'user': serializer.data})
    
    return Response({'user': None})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_user(request, user_id):
    try:
        to_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if to_user == request.user:
        return Response({'error': 'Cannot like yourself'}, status=status.HTTP_400_BAD_REQUEST)
    
    like, created = Like.objects.get_or_create(from_user=request.user, to_user=to_user)
    
    # Clear relevant caches
    cache.delete(f'dashboard_stats_{request.user.id}')
    cache.delete(f'dashboard_stats_{to_user.id}')
    
    is_match = False
    if Like.objects.filter(from_user=to_user, to_user=request.user).exists():
        match, match_created = Match.objects.get_or_create(
            user1=min(request.user, to_user, key=lambda u: u.id),
            user2=max(request.user, to_user, key=lambda u: u.id)
        )
        is_match = True
        
        # Clear match caches for both users
        cache.delete(f'matches_{request.user.id}')
        cache.delete(f'matches_{to_user.id}')
    
    return Response({
        'like': LikeSerializer(like).data,
        'is_match': is_match
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def dislike_user(request, user_id):
    Like.objects.filter(from_user=request.user, to_user_id=user_id).delete()
    return Response({'disliked': True})


# Matches & Chat Views
class MatchListView(generics.ListAPIView):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        ).order_by('-created_at')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class MessageListView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        match_id = self.kwargs.get('match_id')
        return Message.objects.filter(match_id=match_id).order_by('created_at')
    
    def perform_create(self, serializer):
        match_id = self.kwargs.get('match_id')
        serializer.save(match_id=match_id, sender=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_messages(request, match_id):
    try:
        match = Match.objects.get(id=match_id)
        if match.user1 != request.user and match.user2 != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    except Match.DoesNotExist:
        return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    
    messages = Message.objects.filter(match=match).order_by('created_at')
    
    # Mark messages as read
    messages.filter(read=False).exclude(sender=request.user).update(read=True)
    
    serializer = MessageSerializer(messages, many=True)
    
    other_user = match.user2 if match.user1 == request.user else match.user1
    
    return Response({
        'messages': serializer.data,
        'other_user': UserSerializer(other_user).data,
        'match_id': match.id
    })


# Posts Views
class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Post.objects.all().order_by('-created_at')[:20]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        return Response({'liked': False, 'like_count': post.likes.count()})
    else:
        post.likes.add(request.user)
        return Response({'liked': True, 'like_count': post.likes.count()})


# Media Gallery Views
class MediaGalleryListCreateView(generics.ListCreateAPIView):
    serializer_class = MediaGallerySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MediaGallery.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MediaGalleryDeleteView(generics.DestroyAPIView):
    serializer_class = MediaGallerySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MediaGallery.objects.filter(user=self.request.user)
