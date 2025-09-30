from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('explore/', views.explore, name='explore'),
    path('search/', views.search, name='search'),

    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('users/<str:username>/', views.profile, name='profile'),
    path('users/<str:username>/followers/', views.followers, name='followers'),
    path('users/<str:username>/following/', views.following, name='following'),
    path('settings/profile/', views.profile_edit, name='profile_edit'),
    path('users/<str:username>/follow/', views.follow_user, name='follow_user'),

    path('settings/', views.settings, name='settings'),
    path('settings/account/', views.settings_account, name='settings_account'),
    path('settings/security/', views.settings_security, name='settings_security'),

    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    path('organizations/new/', views.organization_create, name='organization_create'),
    path('orgs/<str:org_name>/', views.organization_detail, name='organization_detail'),
    
    path('new/', views.repo_create, name='repo_create'),
    path('<str:username>/<str:repo_name>/', views.repo_detail, name='repo_detail'),
    path('<str:username>/<str:repo_name>/settings/', views.repo_edit, name='repo_edit'),
    path('<str:username>/<str:repo_name>/delete/', views.repo_delete, name='repo_delete'),

    path('<str:username>/<str:repo_name>/star/', views.star_repo, name='star_repo'),
    path('<str:username>/<str:repo_name>/watch/', views.watch_repo, name='watch_repo'),
    path('<str:username>/<str:repo_name>/stargazers/', views.repo_stargazers, name='repo_stargazers'),
    path('<str:username>/<str:repo_name>/forks/', views.repo_forks, name='repo_forks'),
    
    path('<str:username>/<str:repo_name>/issues/', views.issue_list, name='issue_list'),
    path('<str:username>/<str:repo_name>/issues/new/', views.issue_create, name='issue_create'),
    path('<str:username>/<str:repo_name>/issues/<int:issue_number>/', views.issue_detail, name='issue_detail'),
    path('<str:username>/<str:repo_name>/issues/<int:issue_number>/close/', views.issue_close, name='issue_close'),
    path('<str:username>/<str:repo_name>/issues/<int:issue_number>/comment/', views.issue_comment, name='issue_comment'),
    
    path('<str:username>/<str:repo_name>/pulls/', views.pr_list, name='pr_list'),
    path('<str:username>/<str:repo_name>/pulls/new/', views.pr_create, name='pr_create'),
    path('<str:username>/<str:repo_name>/pulls/<int:pr_number>/', views.pr_detail, name='pr_detail'),
    path('<str:username>/<str:repo_name>/pulls/<int:pr_number>/merge/', views.pr_merge, name='pr_merge'),
    
    path('<str:username>/<str:repo_name>/releases/', views.release_list, name='release_list'),
    path('<str:username>/<str:repo_name>/releases/new/', views.release_create, name='release_create'),
    path('<str:username>/<str:repo_name>/releases/tag/<str:tag_name>/', views.release_detail, name='release_detail'),
]