from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import UserProfile, Like, Match, Message, MediaGallery, Post
from .forms import UserProfileForm, UserRegisterForm, MediaUploadForm

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

@login_required
def dashboard(request):
    # Get user statistics with optimized queries
    profile = request.user.profile
    
    # Count matches (optimized)
    matches_count = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user2').count()
    
    # Count likes received
    likes_received = Like.objects.filter(to_user=request.user).count()
    
    # Count likes given
    likes_given = Like.objects.filter(from_user=request.user).count()
    
    # Count unread messages (optimized)
    unread_messages = Message.objects.filter(
        match__in=Match.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        ),
        read=False
    ).exclude(sender=request.user).select_related('match', 'sender').count()
    
    # Get recent matches with prefetch
    recent_matches = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user2').order_by('-created_at')[:3]
    
    # Get recent posts with pagination
    recent_posts = Post.objects.select_related('user').order_by('-created_at')[:5]
    
    # Get recent chats (matches with unread messages)
    recent_chats = []
    matches_with_messages = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).prefetch_related('messages').order_by('-messages__created_at')[:5]
    
    for match in matches_with_messages:
        other_user = match.user2 if match.user1 == request.user else match.user1
        last_message = match.messages.last()
        if last_message:
            recent_chats.append({
                'match': match,
                'other_user': other_user,
                'last_message': last_message,
                'unread_count': match.messages.filter(sender=other_user, read=False).count()
            })
    
    # Handle post creation
    if request.method == 'POST' and 'create_post' in request.POST:
        content = request.POST.get('content')
        if content:
            Post.objects.create(user=request.user, content=content)
            messages.success(request, 'Post created successfully!')
            return redirect('dashboard')
    
    context = {
        'profile': profile,
        'matches_count': matches_count,
        'likes_received': likes_received,
        'likes_given': likes_given,
        'unread_messages': unread_messages,
        'recent_matches': recent_matches,
        'recent_posts': recent_posts,
        'recent_chats': recent_chats,
    }
    
    return render(request, 'dating/dashboard.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('profile_edit')
    else:
        form = UserRegisterForm()
    return render(request, 'dating/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'dating/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile_edit(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    media_gallery = MediaGallery.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        media_form = MediaUploadForm(request.POST, request.FILES)
        
        if 'upload_media' in request.POST:
            if media_form.is_valid():
                media = media_form.save(commit=False)
                media.user = request.user
                media.save()
                messages.success(request, 'Media uploaded successfully!')
                return redirect('profile_edit')
        elif form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile_view')
    else:
        form = UserProfileForm(instance=profile)
        media_form = MediaUploadForm()
    
    return render(request, 'dating/profile_edit.html', {
        'form': form,
        'media_form': media_form,
        'media_gallery': media_gallery
    })

@login_required
def profile_view(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    media_gallery = MediaGallery.objects.filter(user=request.user)
    return render(request, 'dating/profile_view.html', {'profile': profile, 'media_gallery': media_gallery})

@login_required
def browse(request):
    profile = request.user.profile
    users = User.objects.exclude(id=request.user.id)
    search_query = request.GET.get('search', '').strip()
    
    # Filter out users who hide from search
    users = users.exclude(profile__hide_from_search=True)
    
    # Search by username if query provided
    if search_query:
        users = users.filter(username__icontains=search_query)
    
    # Filter by gender preference if set and no search query
    if not search_query and profile.looking_for and profile.looking_for != 'both':
        users = users.filter(profile__gender=profile.looking_for)
    
    # Exclude already liked users
    liked_users = Like.objects.filter(from_user=request.user).values_list('to_user', flat=True)
    users = users.exclude(id__in=liked_users)
    
    # Get first user
    user = users.first()
    
    # Check if user is matched with current user
    is_matched = False
    if user:
        is_matched = Match.objects.filter(
            Q(user1=request.user, user2=user) | Q(user1=user, user2=request.user)
        ).exists()
    
    return render(request, 'dating/browse.html', {
        'user': user,
        'is_matched': is_matched,
        'search_query': search_query
    })

@login_required
def like_user(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    
    if to_user == request.user:
        return redirect('browse')
    
    # Create like
    Like.objects.get_or_create(from_user=request.user, to_user=to_user)
    
    # Check for match
    if Like.objects.filter(from_user=to_user, to_user=request.user).exists():
        # Create match
        match, created = Match.objects.get_or_create(
            user1=min(request.user, to_user, key=lambda u: u.id),
            user2=max(request.user, to_user, key=lambda u: u.id)
        )
        if created:
            messages.success(request, f'You matched with {to_user.username}!')
    
    return redirect('browse')

@login_required
def dislike_user(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    Like.objects.filter(from_user=request.user, to_user=to_user).delete()
    return redirect('browse')

@login_required
def matches(request):
    matches = Match.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user2').prefetch_related('messages__sender')
    
    return render(request, 'dating/matches.html', {'matches': matches})

@login_required
def chat(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    
    # Verify user is part of the match
    if match.user1 != request.user and match.user2 != request.user:
        return redirect('matches')
    
    other_user = match.user2 if match.user1 == request.user else match.user1
    messages_list = match.messages.all().order_by('created_at')
    
    # Mark messages as read
    match.messages.filter(sender=other_user).update(read=True)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                match=match,
                sender=request.user,
                content=content
            )
            return redirect('chat', match_id=match.id)
    
    return render(request, 'dating/chat.html', {
        'match': match,
        'other_user': other_user,
        'messages': messages_list
    })

@login_required
def delete_media(request, media_id):
    media = get_object_or_404(MediaGallery, id=media_id, user=request.user)
    media.delete()
    messages.success(request, 'Media deleted successfully!')
    return redirect('profile_edit')

@login_required
def view_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check if user is matched with current user
    is_matched = Match.objects.filter(
        Q(user1=request.user, user2=user) | Q(user1=user, user2=request.user)
    ).exists()
    
    # Check if viewing own profile
    is_own_profile = (user == request.user)
    
    # Get media gallery
    media_gallery = MediaGallery.objects.filter(user=user)
    
    return render(request, 'dating/view_profile.html', {
        'profile': profile, 
        'user': user, 
        'is_matched': is_matched,
        'is_own_profile': is_own_profile,
        'media_gallery': media_gallery
    })