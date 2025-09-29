from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Extended user model with GitHub-like features"""
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    company = models.CharField(max_length=100, blank=True)
    twitter_username = models.CharField(max_length=50, blank=True)
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    public_repos_count = models.IntegerField(default=0)
    private_repos_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_organization = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]


class UserFollow(models.Model):
    """Follow relationships between users"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_follows'
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
        ]


class Organization(models.Model):
    """GitHub-style organizations"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='org_avatars/', null=True, blank=True)
    website = models.URLField(max_length=200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_organizations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'


class OrganizationMember(models.Model):
    """Organization membership"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'organization_members'
        unique_together = ('organization', 'user')


class Repository(models.Model):
    """Main repository model"""
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repositories')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, related_name='repositories')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    is_fork = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='forks')
    default_branch = models.CharField(max_length=100, default='main')
    language = models.CharField(max_length=50, blank=True)
    stars_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    watchers_count = models.IntegerField(default=0)
    open_issues_count = models.IntegerField(default=0)
    size = models.BigIntegerField(default=0)  # in KB
    homepage = models.URLField(max_length=200, blank=True)
    topics = models.JSONField(default=list, blank=True)
    has_issues = models.BooleanField(default=True)
    has_projects = models.BooleanField(default=True)
    has_wiki = models.BooleanField(default=True)
    has_downloads = models.BooleanField(default=True)
    archived = models.BooleanField(default=False)
    disabled = models.BooleanField(default=False)
    license = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pushed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'repositories'
        unique_together = ('owner', 'name')
        indexes = [
            models.Index(fields=['owner', 'name']),
            models.Index(fields=['visibility', 'created_at']),
            models.Index(fields=['language']),
        ]


class RepositoryCollaborator(models.Model):
    """Repository collaborators and permissions"""
    PERMISSION_CHOICES = [
        ('read', 'Read'),
        ('write', 'Write'),
        ('admin', 'Admin'),
    ]
    
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='collaborators')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collaborating_repos')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='read')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'repository_collaborators'
        unique_together = ('repository', 'user')


class Branch(models.Model):
    """Repository branches"""
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=100)
    commit_sha = models.CharField(max_length=40)
    protected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'branches'
        unique_together = ('repository', 'name')


class Commit(models.Model):
    """Git commits"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='commits')
    sha = models.CharField(max_length=40, unique=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='authored_commits')
    author_name = models.CharField(max_length=200)
    author_email = models.EmailField()
    committer_name = models.CharField(max_length=200)
    committer_email = models.EmailField()
    message = models.TextField()
    parent_shas = models.JSONField(default=list)
    tree_sha = models.CharField(max_length=40)
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    total_changes = models.IntegerField(default=0)
    committed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'commits'
        indexes = [
            models.Index(fields=['repository', 'committed_at']),
            models.Index(fields=['sha']),
        ]


class File(models.Model):
    """Files in repository"""
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='files')
    path = models.TextField()
    name = models.CharField(max_length=255)
    size = models.BigIntegerField()
    sha = models.CharField(max_length=40)
    content_type = models.CharField(max_length=100)
    is_binary = models.BooleanField(default=False)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='files')
    last_commit = models.ForeignKey(Commit, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'files'
        unique_together = ('repository', 'branch', 'path')


class Issue(models.Model):
    """GitHub issues"""
    STATE_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]
    
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='issues')
    number = models.IntegerField()
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_issues')
    assignees = models.ManyToManyField(User, related_name='assigned_issues', blank=True)
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default='open')
    locked = models.BooleanField(default=False)
    comments_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'issues'
        unique_together = ('repository', 'number')
        indexes = [
            models.Index(fields=['repository', 'state', 'created_at']),
        ]


class Label(models.Model):
    """Issue and PR labels"""
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=6)  # Hex color
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'labels'
        unique_together = ('repository', 'name')


class IssueLabel(models.Model):
    """Many-to-many relationship between issues and labels"""
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='issue_labels')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='labeled_issues')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'issue_labels'
        unique_together = ('issue', 'label')


class Comment(models.Model):
    """Comments on issues and pull requests"""
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    pull_request = models.ForeignKey('PullRequest', on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='comments')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comments'
        indexes = [
            models.Index(fields=['issue', 'created_at']),
            models.Index(fields=['pull_request', 'created_at']),
        ]


class PullRequest(models.Model):
    """Pull requests"""
    STATE_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('merged', 'Merged'),
    ]
    
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='pull_requests')
    number = models.IntegerField()
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_prs')
    head_branch = models.CharField(max_length=100)
    base_branch = models.CharField(max_length=100)
    head_repo = models.ForeignKey(Repository, on_delete=models.SET_NULL, null=True, related_name='head_prs')
    head_sha = models.CharField(max_length=40)
    base_sha = models.CharField(max_length=40)
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default='open')
    merged = models.BooleanField(default=False)
    merged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='merged_prs')
    merged_at = models.DateTimeField(null=True, blank=True)
    merge_commit_sha = models.CharField(max_length=40, blank=True)
    assignees = models.ManyToManyField(User, related_name='assigned_prs', blank=True)
    reviewers = models.ManyToManyField(User, related_name='reviewing_prs', blank=True)
    draft = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    comments_count = models.IntegerField(default=0)
    commits_count = models.IntegerField(default=0)
    additions = models.IntegerField(default=0)
    deletions = models.IntegerField(default=0)
    changed_files = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'pull_requests'
        unique_together = ('repository', 'number')
        indexes = [
            models.Index(fields=['repository', 'state', 'created_at']),
        ]


class PullRequestLabel(models.Model):
    """Labels for pull requests"""
    pull_request = models.ForeignKey(PullRequest, on_delete=models.CASCADE, related_name='pr_labels')
    label = models.ForeignKey(Label, on_delete=models.CASCADE, related_name='labeled_prs')
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pull_request_labels'
        unique_together = ('pull_request', 'label')


class Review(models.Model):
    """Pull request reviews"""
    STATE_CHOICES = [
        ('pending', 'Pending'),
        ('commented', 'Commented'),
        ('approved', 'Approved'),
        ('changes_requested', 'Changes Requested'),
        ('dismissed', 'Dismissed'),
    ]
    
    pull_request = models.ForeignKey(PullRequest, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviews')
    body = models.TextField(blank=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='pending')
    commit_sha = models.CharField(max_length=40)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews'


class ReviewComment(models.Model):
    """Inline code review comments"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='review_comments')
    pull_request = models.ForeignKey(PullRequest, on_delete=models.CASCADE, related_name='review_comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    body = models.TextField()
    path = models.TextField()
    position = models.IntegerField()
    line = models.IntegerField()
    commit_sha = models.CharField(max_length=40)
    in_reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'review_comments'


class Star(models.Model):
    """Repository stars"""
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='stars')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='starred_repos')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stars'
        unique_together = ('repository', 'user')
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]


class Watch(models.Model):
    """Repository watchers"""
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='watchers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watched_repos')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'watches'
        unique_together = ('repository', 'user')


class Release(models.Model):
    """Repository releases"""
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='releases')
    tag_name = models.CharField(max_length=100)
    target_commitish = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    draft = models.BooleanField(default=False)
    prerelease = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='releases')
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'releases'
        unique_together = ('repository', 'tag_name')


class ReleaseAsset(models.Model):
    """Release assets/downloads"""
    release = models.ForeignKey(Release, on_delete=models.CASCADE, related_name='assets')
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    download_count = models.IntegerField(default=0)
    file = models.FileField(upload_to='release_assets/')
    uploader = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'release_assets'


class Webhook(models.Model):
    """Repository webhooks"""
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='webhooks')
    url = models.URLField(max_length=500)
    content_type = models.CharField(max_length=50, default='application/json')
    secret = models.CharField(max_length=200, blank=True)
    events = models.JSONField(default=list)  # ['push', 'pull_request', etc.]
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'webhooks'


class Notification(models.Model):
    """User notifications"""
    TYPE_CHOICES = [
        ('issue', 'Issue'),
        ('pull_request', 'Pull Request'),
        ('commit', 'Commit'),
        ('release', 'Release'),
        ('mention', 'Mention'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    subject = models.CharField(max_length=500)
    reason = models.CharField(max_length=50)
    unread = models.BooleanField(default=True)
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'unread', 'created_at']),
        ]


class Activity(models.Model):
    """User activity feed"""
    EVENT_TYPES = [
        ('push', 'Push'),
        ('create', 'Create'),
        ('delete', 'Delete'),
        ('fork', 'Fork'),
        ('star', 'Star'),
        ('watch', 'Watch'),
        ('issue', 'Issue'),
        ('pull_request', 'Pull Request'),
        ('release', 'Release'),
        ('follow', 'Follow'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, null=True, blank=True)
    payload = models.JSONField(default=dict)
    public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'activities'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['repository', 'created_at']),
        ]


class SSHKey(models.Model):
    """User SSH keys"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ssh_keys')
    title = models.CharField(max_length=200)
    key = models.TextField()
    fingerprint = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ssh_keys'


class AccessToken(models.Model):
    """Personal access tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_tokens')
    name = models.CharField(max_length=200)
    token = models.CharField(max_length=200, unique=True)
    scopes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'access_tokens'