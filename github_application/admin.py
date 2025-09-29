from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, UserFollow, Organization, OrganizationMember, Repository,
    RepositoryCollaborator, Branch, Commit, File, Issue, Label, IssueLabel,
    Comment, PullRequest, PullRequestLabel, Review, ReviewComment, Star,
    Watch, Release, ReleaseAsset, Webhook, Notification, Activity,
    SSHKey, AccessToken
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 
                    'followers_count', 'following_count', 'public_repos_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_organization')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'bio')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('GitHub Profile', {
            'fields': ('bio', 'avatar', 'location', 'website', 'company', 
                      'twitter_username', 'is_organization')
        }),
        ('Statistics', {
            'fields': ('followers_count', 'following_count', 'public_repos_count', 
                      'private_repos_count')
        }),
    )


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'following__username')
    date_hierarchy = 'created_at'
    raw_id_fields = ('follower', 'following')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'owner', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'display_name', 'description', 'email')
    date_hierarchy = 'created_at'
    raw_id_fields = ('owner',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('organization__name', 'user__username')
    date_hierarchy = 'joined_at'
    raw_id_fields = ('organization', 'user')


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'visibility', 'stars_count', 'forks_count', 
                    'language', 'created_at')
    list_filter = ('visibility', 'language', 'is_fork', 'archived', 'disabled', 
                   'has_issues', 'has_wiki', 'created_at')
    search_fields = ('name', 'description', 'owner__username')
    date_hierarchy = 'created_at'
    raw_id_fields = ('owner', 'organization', 'parent')
    readonly_fields = ('id', 'created_at', 'updated_at', 'pushed_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'owner', 'organization', 'visibility')
        }),
        ('Repository Settings', {
            'fields': ('default_branch', 'language', 'homepage', 'license', 'topics')
        }),
        ('Fork Information', {
            'fields': ('is_fork', 'parent')
        }),
        ('Statistics', {
            'fields': ('stars_count', 'forks_count', 'watchers_count', 
                      'open_issues_count', 'size')
        }),
        ('Features', {
            'fields': ('has_issues', 'has_projects', 'has_wiki', 'has_downloads')
        }),
        ('Status', {
            'fields': ('archived', 'disabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'pushed_at')
        }),
    )


@admin.register(RepositoryCollaborator)
class RepositoryCollaboratorAdmin(admin.ModelAdmin):
    list_display = ('repository', 'user', 'permission', 'added_at')
    list_filter = ('permission', 'added_at')
    search_fields = ('repository__name', 'user__username')
    date_hierarchy = 'added_at'
    raw_id_fields = ('repository', 'user')


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'repository', 'protected', 'updated_at')
    list_filter = ('protected', 'created_at')
    search_fields = ('name', 'repository__name', 'commit_sha')
    date_hierarchy = 'created_at'
    raw_id_fields = ('repository',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Commit)
class CommitAdmin(admin.ModelAdmin):
    list_display = ('sha', 'repository', 'author_name', 'committed_at', 
                    'additions', 'deletions')
    list_filter = ('committed_at', 'created_at')
    search_fields = ('sha', 'message', 'author_name', 'author_email')
    date_hierarchy = 'committed_at'
    raw_id_fields = ('repository', 'author')
    readonly_fields = ('id', 'created_at')


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'repository', 'branch', 'size', 'is_binary', 'updated_at')
    list_filter = ('is_binary', 'content_type', 'created_at')
    search_fields = ('name', 'path', 'repository__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('repository', 'branch', 'last_commit')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'repository', 'author', 'state', 
                    'comments_count', 'created_at')
    list_filter = ('state', 'locked', 'created_at', 'closed_at')
    search_fields = ('title', 'body', 'repository__name', 'author__username')
    date_hierarchy = 'created_at'
    raw_id_fields = ('repository', 'author')
    filter_horizontal = ('assignees',)
    readonly_fields = ('created_at', 'updated_at', 'closed_at')


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'repository', 'color', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'repository__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('repository',)


@admin.register(IssueLabel)
class IssueLabelAdmin(admin.ModelAdmin):
    list_display = ('issue', 'label', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('issue__title', 'label__name')
    date_hierarchy = 'added_at'
    raw_id_fields = ('issue', 'label')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'get_target', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('body', 'author__username')
    date_hierarchy = 'created_at'
    raw_id_fields = ('issue', 'pull_request', 'author')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_target(self, obj):
        if obj.issue:
            return f"Issue #{obj.issue.number}"
        elif obj.pull_request:
            return f"PR #{obj.pull_request.number}"
        return "N/A"
    get_target.short_description = 'Target'


@admin.register(PullRequest)
class PullRequestAdmin(admin.ModelAdmin):
    list_display = ('number', 'title', 'repository', 'author', 'state', 
                    'merged', 'created_at')
    list_filter = ('state', 'merged', 'draft', 'locked', 'created_at')
    search_fields = ('title', 'body', 'repository__name', 'author__username')
    date_hierarchy = 'created_at'
    raw_id_fields = ('repository', 'author', 'head_repo', 'merged_by')
    filter_horizontal = ('assignees', 'reviewers')
    readonly_fields = ('created_at', 'updated_at', 'merged_at', 'closed_at')


@admin.register(PullRequestLabel)
class PullRequestLabelAdmin(admin.ModelAdmin):
    list_display = ('pull_request', 'label', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('pull_request__title', 'label__name')
    date_hierarchy = 'added_at'
    raw_id_fields = ('pull_request', 'label')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('pull_request', 'reviewer', 'state', 'submitted_at', 'created_at')
    list_filter = ('state', 'submitted_at', 'created_at')
    search_fields = ('pull_request__title', 'reviewer__username', 'body')
    date_hierarchy = 'created_at'
    raw_id_fields = ('pull_request', 'reviewer')
    readonly_fields = ('created_at',)


@admin.register(ReviewComment)
class ReviewCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'pull_request', 'path', 'line', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('body', 'author__username', 'path')
    date_hierarchy = 'created_at'
    raw_id_fields = ('review', 'pull_request', 'author', 'in_reply_to')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Star)
class StarAdmin(admin.ModelAdmin):
    list_display = ('user', 'repository', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'repository__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('repository', 'user')


@admin.register(Watch)
class WatchAdmin(admin.ModelAdmin):
    list_display = ('user', 'repository', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'repository__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('repository', 'user')


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('tag_name', 'name', 'repository', 'author', 'prerelease', 
                    'draft', 'published_at')
    list_filter = ('prerelease', 'draft', 'created_at', 'published_at')
    search_fields = ('tag_name', 'name', 'body', 'repository__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('repository', 'author')
    readonly_fields = ('created_at',)


@admin.register(ReleaseAsset)
class ReleaseAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'release', 'content_type', 'size', 'download_count', 
                    'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('name', 'label', 'release__tag_name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('release', 'uploader')
    readonly_fields = ('created_at',)


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ('repository', 'url', 'active', 'created_at')
    list_filter = ('active', 'content_type', 'created_at')
    search_fields = ('url', 'repository__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('repository',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'notification_type', 'unread', 'created_at')
    list_filter = ('notification_type', 'unread', 'created_at')
    search_fields = ('subject', 'user__username', 'repository__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'repository')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(unread=False)
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(unread=True)
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'repository', 'public', 'created_at')
    list_filter = ('event_type', 'public', 'created_at')
    search_fields = ('user__username', 'repository__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'repository')
    readonly_fields = ('created_at',)


@admin.register(SSHKey)
class SSHKeyAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'fingerprint', 'created_at', 'last_used')
    list_filter = ('created_at', 'last_used')
    search_fields = ('title', 'user__username', 'fingerprint')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'fingerprint')


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'last_used', 'expires_at')
    list_filter = ('created_at', 'last_used', 'expires_at')
    search_fields = ('name', 'user__username')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'token')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('token',)
        return self.readonly_fields