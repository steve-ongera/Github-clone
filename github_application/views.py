from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.core.paginator import Paginator
from .models import (
    User, Repository, Issue, PullRequest, Commit, Star, Watch,
    UserFollow, Organization, OrganizationMember, Branch, Comment,
    Label, Review, Release, Notification, Activity, RepositoryCollaborator
)


# ============================================================================
# HOME & DASHBOARD
# ============================================================================

def home(request):
    """Homepage - shows trending repos and recent activity"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    trending_repos = Repository.objects.filter(
        visibility='public'
    ).order_by('-stars_count')[:8]
    
    recent_repos = Repository.objects.filter(
        visibility='public'
    ).order_by('-created_at')[:8]
    
    context = {
        'trending_repos': trending_repos,
        'recent_repos': recent_repos,
    }
    return render(request, 'home.html', context)


@login_required
def dashboard(request):
    """User dashboard with personalized feed"""
    # Get user's repositories
    user_repos = Repository.objects.filter(owner=request.user).order_by('-updated_at')[:5]
    
    # Get repositories from followed users
    following_ids = request.user.following.values_list('following_id', flat=True)
    following_activity = Activity.objects.filter(
        user_id__in=following_ids,
        public=True
    ).select_related('user', 'repository').order_by('-created_at')[:20]
    
    # Get user's recent activity
    user_activity = Activity.objects.filter(
        user=request.user
    ).select_related('repository').order_by('-created_at')[:10]
    
    # Get starred repositories
    starred_repos = Repository.objects.filter(
        stars__user=request.user
    ).order_by('-stars__created_at')[:5]
    
    # Get unread notifications
    notifications = Notification.objects.filter(
        user=request.user,
        unread=True
    ).order_by('-created_at')[:10]
    
    context = {
        'user_repos': user_repos,
        'following_activity': following_activity,
        'user_activity': user_activity,
        'starred_repos': starred_repos,
        'notifications': notifications,
    }
    return render(request, 'dashboard.html', context)


# ============================================================================
# USER AUTHENTICATION
# ============================================================================

def signup(request):
    """User registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('signup')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('dashboard')
    
    return render(request, 'auth/signup.html')


def login_view(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('home')


# ============================================================================
# USER PROFILE
# ============================================================================

def profile(request, username):
    """User profile page"""
    user = get_object_or_404(User, username=username)
    repos = Repository.objects.filter(owner=user, visibility='public').order_by('-updated_at')
    starred = Repository.objects.filter(stars__user=user).order_by('-stars__created_at')[:6]
    
    is_following = False
    if request.user.is_authenticated:
        is_following = UserFollow.objects.filter(
            follower=request.user, following=user
        ).exists()
    
    context = {
        'profile_user': user,
        'repos': repos,
        'starred': starred,
        'is_following': is_following,
    }
    return render(request, 'users/profile.html', context)


@login_required
def profile_edit(request):
    """Edit user profile"""
    if request.method == 'POST':
        request.user.bio = request.POST.get('bio', '')
        request.user.location = request.POST.get('location', '')
        request.user.website = request.POST.get('website', '')
        request.user.company = request.POST.get('company', '')
        request.user.twitter_username = request.POST.get('twitter_username', '')
        
        if 'avatar' in request.FILES:
            request.user.avatar = request.FILES['avatar']
        
        request.user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile', username=request.user.username)
    
    return render(request, 'users/profile_edit.html')


@login_required
def follow_user(request, username):
    """Follow/unfollow a user"""
    user_to_follow = get_object_or_404(User, username=username)
    
    if user_to_follow == request.user:
        messages.error(request, 'You cannot follow yourself')
        return redirect('profile', username=username)
    
    follow_obj, created = UserFollow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if not created:
        follow_obj.delete()
        user_to_follow.followers_count -= 1
        request.user.following_count -= 1
        messages.success(request, f'Unfollowed {username}')
    else:
        user_to_follow.followers_count += 1
        request.user.following_count += 1
        messages.success(request, f'Following {username}')
    
    user_to_follow.save()
    request.user.save()
    
    return redirect('profile', username=username)


def followers(request, username):
    """User followers list"""
    user = get_object_or_404(User, username=username)
    followers = UserFollow.objects.filter(following=user).select_related('follower')
    
    context = {
        'profile_user': user,
        'followers': followers,
    }
    return render(request, 'users/followers.html', context)


def following(request, username):
    """User following list"""
    user = get_object_or_404(User, username=username)
    following = UserFollow.objects.filter(follower=user).select_related('following')
    
    context = {
        'profile_user': user,
        'following': following,
    }
    return render(request, 'users/following.html', context)


# ============================================================================
# REPOSITORY VIEWS
# ============================================================================

def explore(request):
    """Explore public repositories"""
    repos = Repository.objects.filter(visibility='public')
    
    # Filter by language
    language = request.GET.get('language')
    if language:
        repos = repos.filter(language=language)
    
    # Sort options
    sort = request.GET.get('sort', 'stars')
    if sort == 'stars':
        repos = repos.order_by('-stars_count')
    elif sort == 'forks':
        repos = repos.order_by('-forks_count')
    elif sort == 'updated':
        repos = repos.order_by('-updated_at')
    else:
        repos = repos.order_by('-created_at')
    
    # Get available languages
    languages = Repository.objects.filter(
        visibility='public'
    ).exclude(language='').values_list('language', flat=True).distinct()
    
    paginator = Paginator(repos, 20)
    page = request.GET.get('page')
    repos = paginator.get_page(page)
    
    context = {
        'repos': repos,
        'languages': languages,
        'current_language': language,
        'current_sort': sort,
    }
    return render(request, 'repos/explore.html', context)


def search(request):
    """Search repositories and users"""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'repositories')
    
    context = {'query': query, 'search_type': search_type}
    
    if query:
        if search_type == 'repositories':
            results = Repository.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                visibility='public'
            ).order_by('-stars_count')
            paginator = Paginator(results, 20)
            page = request.GET.get('page')
            context['results'] = paginator.get_page(page)
        
        elif search_type == 'users':
            results = User.objects.filter(
                Q(username__icontains=query) | Q(bio__icontains=query)
            ).order_by('-followers_count')
            paginator = Paginator(results, 20)
            page = request.GET.get('page')
            context['results'] = paginator.get_page(page)
    
    return render(request, 'search.html', context)


@login_required
def repo_create(request):
    """Create new repository"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        visibility = request.POST.get('visibility', 'public')
        
        if Repository.objects.filter(owner=request.user, name=name).exists():
            messages.error(request, 'Repository with this name already exists')
            return redirect('repo_create')
        
        repo = Repository.objects.create(
            name=name,
            description=description,
            owner=request.user,
            visibility=visibility
        )
        
        request.user.public_repos_count += 1
        request.user.save()
        
        messages.success(request, f'Repository {name} created successfully!')
        return redirect('repo_detail', username=request.user.username, repo_name=name)
    
    return render(request, 'repos/repo_create.html')


def repo_detail(request, username, repo_name):
    """Repository detail page"""
    user = get_object_or_404(User, username=username)
    repo = get_object_or_404(Repository, owner=user, name=repo_name)
    
    # Check visibility
    if repo.visibility == 'private':
        if not request.user.is_authenticated or (
            request.user != repo.owner and 
            not repo.collaborators.filter(user=request.user).exists()
        ):
            return HttpResponseForbidden('This repository is private')
    
    branches = repo.branches.all()
    recent_commits = repo.commits.order_by('-committed_at')[:10]
    
    is_starred = False
    is_watching = False
    if request.user.is_authenticated:
        is_starred = Star.objects.filter(repository=repo, user=request.user).exists()
        is_watching = Watch.objects.filter(repository=repo, user=request.user).exists()
    
    context = {
        'repo': repo,
        'branches': branches,
        'recent_commits': recent_commits,
        'is_starred': is_starred,
        'is_watching': is_watching,
    }
    return render(request, 'repos/repo_detail.html', context)


@login_required
def repo_edit(request, username, repo_name):
    """Edit repository settings"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    
    if repo.owner != request.user:
        return HttpResponseForbidden('You do not have permission to edit this repository')
    
    if request.method == 'POST':
        repo.description = request.POST.get('description', '')
        repo.homepage = request.POST.get('homepage', '')
        repo.visibility = request.POST.get('visibility', repo.visibility)
        repo.has_issues = 'has_issues' in request.POST
        repo.has_wiki = 'has_wiki' in request.POST
        repo.has_projects = 'has_projects' in request.POST
        repo.save()
        
        messages.success(request, 'Repository updated successfully!')
        return redirect('repo_detail', username=username, repo_name=repo_name)
    
    context = {'repo': repo}
    return render(request, 'repos/repo_edit.html', context)


@login_required
def repo_delete(request, username, repo_name):
    """Delete repository"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    
    if repo.owner != request.user:
        return HttpResponseForbidden('You do not have permission to delete this repository')
    
    if request.method == 'POST':
        repo.delete()
        request.user.public_repos_count -= 1
        request.user.save()
        messages.success(request, f'Repository {repo_name} deleted successfully!')
        return redirect('profile', username=username)
    
    context = {'repo': repo}
    return render(request, 'repos/repo_delete.html', context)


@login_required
def star_repo(request, username, repo_name):
    """Star/unstar repository"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    
    star_obj, created = Star.objects.get_or_create(repository=repo, user=request.user)
    
    if not created:
        star_obj.delete()
        repo.stars_count -= 1
        messages.success(request, 'Repository unstarred')
    else:
        repo.stars_count += 1
        messages.success(request, 'Repository starred!')
    
    repo.save()
    return redirect('repo_detail', username=username, repo_name=repo_name)


@login_required
def watch_repo(request, username, repo_name):
    """Watch/unwatch repository"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    
    watch_obj, created = Watch.objects.get_or_create(repository=repo, user=request.user)
    
    if not created:
        watch_obj.delete()
        repo.watchers_count -= 1
        messages.success(request, 'Repository unwatched')
    else:
        repo.watchers_count += 1
        messages.success(request, 'Repository watched!')
    
    repo.save()
    return redirect('repo_detail', username=username, repo_name=repo_name)


def repo_stargazers(request, username, repo_name):
    """List of users who starred the repository"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    stars = Star.objects.filter(repository=repo).select_related('user').order_by('-created_at')
    
    paginator = Paginator(stars, 30)
    page = request.GET.get('page')
    stars = paginator.get_page(page)
    
    context = {'repo': repo, 'stars': stars}
    return render(request, 'repos/stargazers.html', context)


def repo_forks(request, username, repo_name):
    """List of repository forks"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    forks = Repository.objects.filter(parent=repo).order_by('-created_at')
    
    context = {'repo': repo, 'forks': forks}
    return render(request, 'repos/forks.html', context)


# ============================================================================
# ISSUES
# ============================================================================

def issue_list(request, username, repo_name):
    """List repository issues"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    
    state = request.GET.get('state', 'open')
    issues = Issue.objects.filter(repository=repo, state=state).order_by('-created_at')
    
    # Filter by label
    label = request.GET.get('label')
    if label:
        issues = issues.filter(issue_labels__label__name=label)
    
    paginator = Paginator(issues, 25)
    page = request.GET.get('page')
    issues = paginator.get_page(page)
    
    labels = repo.labels.all()
    
    context = {
        'repo': repo,
        'issues': issues,
        'current_state': state,
        'labels': labels,
    }
    return render(request, 'issues/issue_list.html', context)


def issue_detail(request, username, repo_name, issue_number):
    """Issue detail page"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    issue = get_object_or_404(Issue, repository=repo, number=issue_number)
    comments = issue.comments.select_related('author').order_by('created_at')
    
    context = {
        'repo': repo,
        'issue': issue,
        'comments': comments,
    }
    return render(request, 'issues/issue_detail.html', context)


@login_required
def issue_create(request, username, repo_name):
    """Create new issue"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body', '')
        
        # Get next issue number
        last_issue = Issue.objects.filter(repository=repo).order_by('-number').first()
        number = (last_issue.number + 1) if last_issue else 1
        
        issue = Issue.objects.create(
            repository=repo,
            number=number,
            title=title,
            body=body,
            author=request.user
        )
        
        repo.open_issues_count += 1
        repo.save()
        
        messages.success(request, f'Issue #{number} created successfully!')
        return redirect('issue_detail', username=username, repo_name=repo_name, issue_number=number)
    
    context = {'repo': repo}
    return render(request, 'issues/issue_create.html', context)


@login_required
def issue_close(request, username, repo_name, issue_number):
    """Close an issue"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    issue = get_object_or_404(Issue, repository=repo, number=issue_number)
    
    if issue.state == 'open':
        issue.state = 'closed'
        issue.closed_at = timezone.now()
        issue.save()
        
        repo.open_issues_count -= 1
        repo.save()
        
        messages.success(request, f'Issue #{issue_number} closed')
    
    return redirect('issue_detail', username=username, repo_name=repo_name, issue_number=issue_number)


@login_required
def issue_comment(request, username, repo_name, issue_number):
    """Add comment to issue"""
    if request.method == 'POST':
        repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
        issue = get_object_or_404(Issue, repository=repo, number=issue_number)
        
        body = request.POST.get('body')
        if body:
            Comment.objects.create(
                issue=issue,
                author=request.user,
                body=body
            )
            issue.comments_count += 1
            issue.save()
            messages.success(request, 'Comment added successfully!')
    
    return redirect('issue_detail', username=username, repo_name=repo_name, issue_number=issue_number)


# ============================================================================
# PULL REQUESTS
# ============================================================================

def pr_list(request, username, repo_name):
    """List repository pull requests"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    
    state = request.GET.get('state', 'open')
    prs = PullRequest.objects.filter(repository=repo, state=state).order_by('-created_at')
    
    paginator = Paginator(prs, 25)
    page = request.GET.get('page')
    prs = paginator.get_page(page)
    
    context = {
        'repo': repo,
        'prs': prs,
        'current_state': state,
    }
    return render(request, 'pulls/pr_list.html', context)


def pr_detail(request, username, repo_name, pr_number):
    """Pull request detail page"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    pr = get_object_or_404(PullRequest, repository=repo, number=pr_number)
    comments = pr.comments.select_related('author').order_by('created_at')
    reviews = pr.reviews.select_related('reviewer').order_by('-created_at')
    
    context = {
        'repo': repo,
        'pr': pr,
        'comments': comments,
        'reviews': reviews,
    }
    return render(request, 'pulls/pr_detail.html', context)


@login_required
def pr_create(request, username, repo_name):
    """Create new pull request"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('body', '')
        head_branch = request.POST.get('head_branch')
        base_branch = request.POST.get('base_branch', repo.default_branch)
        
        # Get next PR number
        last_pr = PullRequest.objects.filter(repository=repo).order_by('-number').first()
        number = (last_pr.number + 1) if last_pr else 1
        
        pr = PullRequest.objects.create(
            repository=repo,
            number=number,
            title=title,
            body=body,
            author=request.user,
            head_branch=head_branch,
            base_branch=base_branch,
            head_sha='',  # Would be populated from git
            base_sha=''   # Would be populated from git
        )
        
        messages.success(request, f'Pull request #{number} created successfully!')
        return redirect('pr_detail', username=username, repo_name=repo_name, pr_number=number)
    
    branches = repo.branches.all()
    context = {'repo': repo, 'branches': branches}
    return render(request, 'pulls/pr_create.html', context)


@login_required
def pr_merge(request, username, repo_name, pr_number):
    """Merge pull request"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    pr = get_object_or_404(PullRequest, repository=repo, number=pr_number)
    
    if repo.owner != request.user:
        return HttpResponseForbidden('Only repository owner can merge pull requests')
    
    if request.method == 'POST' and pr.state == 'open':
        pr.state = 'merged'
        pr.merged = True
        pr.merged_by = request.user
        pr.merged_at = timezone.now()
        pr.save()
        
        messages.success(request, f'Pull request #{pr_number} merged successfully!')
    
    return redirect('pr_detail', username=username, repo_name=repo_name, pr_number=pr_number)


# ============================================================================
# RELEASES
# ============================================================================

def release_list(request, username, repo_name):
    """List repository releases"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    releases = repo.releases.order_by('-created_at')
    
    context = {'repo': repo, 'releases': releases}
    return render(request, 'releases/release_list.html', context)


def release_detail(request, username, repo_name, tag_name):
    """Release detail page"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    release = get_object_or_404(Release, repository=repo, tag_name=tag_name)
    
    context = {'repo': repo, 'release': release}
    return render(request, 'releases/release_detail.html', context)


@login_required
def release_create(request, username, repo_name):
    """Create new release"""
    repo = get_object_or_404(Repository, owner__username=username, name=repo_name)
    
    if repo.owner != request.user:
        return HttpResponseForbidden('Only repository owner can create releases')
    
    if request.method == 'POST':
        tag_name = request.POST.get('tag_name')
        name = request.POST.get('name')
        body = request.POST.get('body', '')
        prerelease = 'prerelease' in request.POST
        
        release = Release.objects.create(
            repository=repo,
            tag_name=tag_name,
            name=name,
            body=body,
            author=request.user,
            prerelease=prerelease,
            target_commitish=repo.default_branch,
            published_at=timezone.now()
        )
        
        messages.success(request, f'Release {tag_name} created successfully!')
        return redirect('release_detail', username=username, repo_name=repo_name, tag_name=tag_name)
    
    context = {'repo': repo}
    return render(request, 'releases/release_create.html', context)


# ============================================================================
# NOTIFICATIONS
# ============================================================================

@login_required
def notifications(request):
    """User notifications page"""
    unread = request.GET.get('unread', 'true') == 'true'
    
    notifs = Notification.objects.filter(user=request.user)
    if unread:
        notifs = notifs.filter(unread=True)
    
    notifs = notifs.order_by('-created_at')
    
    paginator = Paginator(notifs, 30)
    page = request.GET.get('page')
    notifs = paginator.get_page(page)
    
    context = {'notifications': notifs, 'show_unread': unread}
    return render(request, 'notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notif = get_object_or_404(Notification, id=notification_id, user=request.user)
    notif.unread = False
    notif.save()
    return redirect('notifications')


# ============================================================================
# ORGANIZATIONS
# ============================================================================

def organization_detail(request, org_name):
    """Organization profile page"""
    org = get_object_or_404(Organization, name=org_name)
    repos = Repository.objects.filter(organization=org).order_by('-updated_at')
    members = org.members.select_related('user').order_by('role', 'joined_at')
    
    context = {
        'organization': org,
        'repos': repos,
        'members': members,
    }
    return render(request, 'orgs/organization_detail.html', context)


@login_required
def organization_create(request):
    """Create new organization"""
    if request.method == 'POST':
        name = request.POST.get('name')
        display_name = request.POST.get('display_name')
        description = request.POST.get('description', '')
        
        if Organization.objects.filter(name=name).exists():
            messages.error(request, 'Organization with this name already exists')
            return redirect('organization_create')
        
        org = Organization.objects.create(
            name=name,
            display_name=display_name,
            description=description,
            owner=request.user
        )
        
        # Add creator as owner
        OrganizationMember.objects.create(
            organization=org,
            user=request.user,
            role='owner'
        )
        
        messages.success(request, f'Organization {name} created successfully!')
        return redirect('organization_detail', org_name=name)
    
    return render(request, 'orgs/organization_create.html', context)


# ============================================================================
# SETTINGS
# ============================================================================

@login_required
def settings(request):
    """User settings page"""
    return render(request, 'settings/settings.html')


@login_required
def settings_profile(request):
    """Profile settings"""
    return render(request, 'settings/profile.html')


@login_required
def settings_account(request):
    """Account settings"""
    if request.method == 'POST':
        email = request.POST.get('email')
        request.user.email = email
        request.user.save()
        messages.success(request, 'Account settings updated!')
        return redirect('settings_account')
    
    return render(request, 'settings/account.html')


@login_required
def settings_security(request):
    """Security settings"""
    ssh_keys = request.user.ssh_keys.all()
    access_tokens = request.user.access_tokens.all()
    
    context = {
        'ssh_keys': ssh_keys,
        'access_tokens': access_tokens,
    }
    return render(request, 'settings/security.html', context)