"""
Django management command to seed database with realistic GitHub-like data.

Usage:
    python manage.py seed_data [--users N] [--repos N] [--flush]
    
Options:
    --users N    Number of users to create (default: 20)
    --repos N    Number of repositories to create (default: 50)
    --flush      Delete existing data before seeding
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta, datetime
import random
import uuid
import hashlib
import pytz
from faker import Faker

# Import all models
from github_application.models import (
    User, UserFollow, Organization, OrganizationMember,
    Repository, RepositoryCollaborator, Branch, Commit, File,
    Issue, Label, IssueLabel, Comment, PullRequest, PullRequestLabel,
    Review, ReviewComment, Star, Watch, Release, ReleaseAsset,
    Webhook, Notification, Activity, SSHKey, AccessToken
)

fake = Faker()

# Get UTC timezone
UTC = pytz.UTC


class Command(BaseCommand):
    help = 'Seeds the database with realistic GitHub-like data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create'
        )
        parser.add_argument(
            '--repos',
            type=int,
            default=50,
            help='Number of repositories to create'
        )
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete existing data before seeding'
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write('Flushing existing data...')
            self.flush_data()
        
        num_users = options['users']
        num_repos = options['repos']
        
        self.stdout.write(self.style.SUCCESS(f'Starting data seeding...'))
        self.stdout.write(f'Creating {num_users} users and {num_repos} repositories')
        
        # Seed data in order of dependencies
        users = self.create_users(num_users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))
        
        self.create_user_follows(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created user follow relationships'))
        
        orgs = self.create_organizations(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(orgs)} organizations'))
        
        repos = self.create_repositories(users, orgs, num_repos)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(repos)} repositories'))
        
        self.create_repository_collaborators(repos, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created repository collaborators'))
        
        branches = self.create_branches(repos)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(branches)} branches'))
        
        commits = self.create_commits(repos, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(commits)} commits'))
        
        self.create_files(repos, branches, commits)
        self.stdout.write(self.style.SUCCESS(f'✓ Created files'))
        
        labels = self.create_labels(repos)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(labels)} labels'))
        
        issues = self.create_issues(repos, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(issues)} issues'))
        
        self.create_issue_labels(issues, labels)
        self.stdout.write(self.style.SUCCESS(f'✓ Created issue labels'))
        
        prs = self.create_pull_requests(repos, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(prs)} pull requests'))
        
        self.create_pr_labels(prs, labels)
        self.stdout.write(self.style.SUCCESS(f'✓ Created PR labels'))
        
        self.create_comments(issues, prs, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created comments'))
        
        self.create_reviews(prs, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created reviews'))
        
        self.create_stars(repos, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created stars'))
        
        self.create_watches(repos, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created watches'))
        
        releases = self.create_releases(repos, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(releases)} releases'))
        
        self.create_webhooks(repos)
        self.stdout.write(self.style.SUCCESS(f'✓ Created webhooks'))
        
        self.create_notifications(users, repos)
        self.stdout.write(self.style.SUCCESS(f'✓ Created notifications'))
        
        self.create_activities(users, repos)
        self.stdout.write(self.style.SUCCESS(f'✓ Created activities'))
        
        self.create_ssh_keys(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created SSH keys'))
        
        self.create_access_tokens(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created access tokens'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Database seeding completed successfully!'))

    def flush_data(self):
        """Delete all existing data"""
        models = [
            AccessToken, SSHKey, Activity, Notification, Webhook,
            ReleaseAsset, Release, Watch, Star, ReviewComment, Review,
            PullRequestLabel, Comment, IssueLabel, Label, PullRequest,
            Issue, File, Commit, Branch, RepositoryCollaborator,
            Repository, OrganizationMember, Organization, UserFollow, User
        ]
        for model in models:
            model.objects.all().delete()

    def create_users(self, count):
        """Create users with realistic data"""
        users = []
        
        # Create admin user
        admin = User.objects.create(
            username='admin',
            email='admin@github.com',
            password=make_password('admin123'),
            first_name='Admin',
            last_name='User',
            bio='System administrator',
            is_staff=True,
            is_superuser=True,
            followers_count=100,
            following_count=50
        )
        users.append(admin)
        
        # Create regular users
        for i in range(count - 1):
            username = fake.user_name()
            user = User.objects.create(
                username=f"{username}_{i}" if User.objects.filter(username=username).exists() else username,
                email=fake.email(),
                password=make_password('password123'),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                bio=fake.text(max_nb_chars=200) if random.random() > 0.5 else '',
                location=fake.city() if random.random() > 0.6 else '',
                website=fake.url() if random.random() > 0.7 else '',
                company=fake.company() if random.random() > 0.5 else '',
                twitter_username=fake.user_name() if random.random() > 0.6 else '',
                followers_count=random.randint(0, 1000),
                following_count=random.randint(0, 500),
                public_repos_count=random.randint(0, 50),
                private_repos_count=random.randint(0, 10)
            )
            users.append(user)
        
        return users

    def create_user_follows(self, users):
        """Create follow relationships between users"""
        follows = []
        for user in users:
            # Each user follows 3-10 random users
            num_following = random.randint(3, min(10, len(users) - 1))
            following_users = random.sample([u for u in users if u != user], num_following)
            
            for followed in following_users:
                follows.append(UserFollow(
                    follower=user,
                    following=followed,
                    created_at=fake.date_time_between(start_date='-2y', end_date='now', tzinfo=UTC)
                ))
        
        UserFollow.objects.bulk_create(follows, ignore_conflicts=True)

    def create_organizations(self, users):
        """Create organizations"""
        orgs = []
        org_names = ['TechCorp', 'DevTeam', 'OpenSource Inc', 'CodeFactory', 'DataLabs']
        
        for name in org_names:
            org = Organization.objects.create(
                name=name.lower().replace(' ', '-'),
                display_name=name,
                description=fake.text(max_nb_chars=200),
                website=fake.url(),
                location=fake.city(),
                email=fake.company_email(),
                owner=random.choice(users)
            )
            orgs.append(org)
            
            # Add members to organization
            members_count = random.randint(3, 10)
            for user in random.sample(users, min(members_count, len(users))):
                OrganizationMember.objects.create(
                    organization=org,
                    user=user,
                    role=random.choice(['owner', 'admin', 'member'])
                )
        
        return orgs

    def create_repositories(self, users, orgs, count):
        """Create repositories"""
        repos = []
        languages = ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'Java', 'C++', 'Ruby', 'PHP', 'Swift']
        licenses = ['MIT', 'Apache-2.0', 'GPL-3.0', 'BSD-3-Clause', 'ISC']
        
        for i in range(count):
            owner = random.choice(users)
            org = random.choice(orgs) if random.random() > 0.7 else None
            
            name = fake.slug()
            repo = Repository.objects.create(
                name=f"{name}-{i}" if Repository.objects.filter(owner=owner, name=name).exists() else name,
                description=fake.sentence(nb_words=10),
                owner=owner,
                organization=org,
                visibility=random.choice(['public', 'private']),
                is_fork=random.random() < 0.2,
                default_branch=random.choice(['main', 'master', 'develop']),
                language=random.choice(languages),
                stars_count=random.randint(0, 10000),
                forks_count=random.randint(0, 1000),
                watchers_count=random.randint(0, 500),
                open_issues_count=random.randint(0, 50),
                size=random.randint(100, 100000),
                homepage=fake.url() if random.random() > 0.7 else '',
                topics=[fake.word() for _ in range(random.randint(1, 5))],
                has_issues=random.random() > 0.2,
                has_projects=random.random() > 0.5,
                has_wiki=random.random() > 0.5,
                has_downloads=random.random() > 0.5,
                archived=random.random() < 0.1,
                license=random.choice(licenses) if random.random() > 0.5 else '',
                created_at=fake.date_time_between(start_date='-3y', end_date='now', tzinfo=UTC),
                pushed_at=fake.date_time_between(start_date='-1m', end_date='now', tzinfo=UTC)
            )
            repos.append(repo)
        
        # Create some fork relationships
        for repo in repos:
            if repo.is_fork:
                potential_parents = [r for r in repos if r != repo and not r.is_fork]
                if potential_parents:
                    repo.parent = random.choice(potential_parents)
                    repo.save()
        
        return repos

    def create_repository_collaborators(self, repos, users):
        """Create repository collaborators"""
        collaborators = []
        for repo in repos:
            # Add 1-5 collaborators per repo
            num_collaborators = random.randint(1, min(5, len(users)))
            collab_users = random.sample([u for u in users if u != repo.owner], num_collaborators)
            
            for user in collab_users:
                collaborators.append(RepositoryCollaborator(
                    repository=repo,
                    user=user,
                    permission=random.choice(['read', 'write', 'admin'])
                ))
        
        RepositoryCollaborator.objects.bulk_create(collaborators, ignore_conflicts=True)

    def create_branches(self, repos):
        """Create branches for repositories"""
        branches = []
        branch_names = ['main', 'develop', 'feature/new-feature', 'bugfix/fix-issue', 'release/v1.0']
        
        for repo in repos:
            for branch_name in random.sample(branch_names, random.randint(2, 4)):
                branches.append(Branch(
                    repository=repo,
                    name=branch_name,
                    commit_sha=fake.sha1(),
                    protected=branch_name in ['main', 'master']
                ))
        
        Branch.objects.bulk_create(branches, ignore_conflicts=True)
        return Branch.objects.all()

    def create_commits(self, repos, users):
        """Create commits"""
        commits = []
        for repo in repos:
            num_commits = random.randint(10, 100)
            for _ in range(num_commits):
                author = random.choice(users)
                commits.append(Commit(
                    repository=repo,
                    sha=fake.sha1(),
                    author=author,
                    author_name=f"{author.first_name} {author.last_name}",
                    author_email=author.email,
                    committer_name=f"{author.first_name} {author.last_name}",
                    committer_email=author.email,
                    message=fake.sentence(nb_words=8),
                    parent_shas=[fake.sha1()],
                    tree_sha=fake.sha1(),
                    additions=random.randint(1, 500),
                    deletions=random.randint(0, 200),
                    total_changes=random.randint(1, 700),
                    committed_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=UTC)
                ))
        
        Commit.objects.bulk_create(commits, ignore_conflicts=True)
        return Commit.objects.all()

    def create_files(self, repos, branches, commits):
        """Create files in repositories"""
        files = []
        file_extensions = ['.py', '.js', '.ts', '.go', '.java', '.cpp', '.rb', '.md', '.txt', '.json']
        
        for repo in repos[:20]:  # Only for first 20 repos to save time
            repo_branches = branches.filter(repository=repo)
            repo_commits = commits.filter(repository=repo)
            
            if not repo_branches.exists() or not repo_commits.exists():
                continue
            
            for _ in range(random.randint(5, 20)):
                ext = random.choice(file_extensions)
                files.append(File(
                    repository=repo,
                    path=f"src/{fake.file_name(extension=ext[1:])}",
                    name=fake.file_name(extension=ext[1:]),
                    size=random.randint(100, 100000),
                    sha=fake.sha1(),
                    content_type='text/plain' if ext != '.json' else 'application/json',
                    is_binary=False,
                    branch=random.choice(repo_branches),
                    last_commit=random.choice(repo_commits)
                ))
        
        File.objects.bulk_create(files, ignore_conflicts=True)

    def create_labels(self, repos):
        """Create labels for repositories"""
        labels = []
        label_data = [
            ('bug', 'FF0000', 'Something isn\'t working'),
            ('enhancement', '00FF00', 'New feature or request'),
            ('documentation', '0000FF', 'Improvements or additions to documentation'),
            ('good first issue', 'FFFF00', 'Good for newcomers'),
            ('help wanted', 'FF00FF', 'Extra attention is needed'),
            ('wontfix', '808080', 'This will not be worked on'),
        ]
        
        for repo in repos:
            for name, color, desc in random.sample(label_data, random.randint(3, 6)):
                labels.append(Label(
                    repository=repo,
                    name=name,
                    color=color,
                    description=desc
                ))
        
        Label.objects.bulk_create(labels, ignore_conflicts=True)
        return Label.objects.all()

    def create_issues(self, repos, users):
        """Create issues"""
        issues = []
        for repo in repos:
            num_issues = random.randint(5, 30)
            for i in range(1, num_issues + 1):
                issue = Issue(
                    repository=repo,
                    number=i,
                    title=fake.sentence(nb_words=8),
                    body=fake.text(max_nb_chars=500),
                    author=random.choice(users),
                    state=random.choice(['open', 'closed']),
                    locked=random.random() < 0.05,
                    comments_count=random.randint(0, 50),
                    created_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=UTC)
                )
                if issue.state == 'closed':
                    issue.closed_at = fake.date_time_between(start_date=issue.created_at, end_date='now', tzinfo=UTC)
                issues.append(issue)
        
        Issue.objects.bulk_create(issues)
        
        # Add assignees
        for issue in Issue.objects.all()[:100]:  # First 100 to save time
            assignees = random.sample(list(users), random.randint(0, 3))
            issue.assignees.set(assignees)
        
        return Issue.objects.all()

    def create_issue_labels(self, issues, labels):
        """Create issue label relationships"""
        issue_labels = []
        for issue in issues:
            repo_labels = labels.filter(repository=issue.repository)
            if repo_labels.exists():
                selected_labels = random.sample(list(repo_labels), min(random.randint(1, 3), repo_labels.count()))
                for label in selected_labels:
                    issue_labels.append(IssueLabel(
                        issue=issue,
                        label=label
                    ))
        
        IssueLabel.objects.bulk_create(issue_labels, ignore_conflicts=True)

    def create_pull_requests(self, repos, users):
        """Create pull requests"""
        prs = []
        for repo in repos:
            num_prs = random.randint(3, 20)
            for i in range(1, num_prs + 1):
                state = random.choice(['open', 'closed', 'merged'])
                pr = PullRequest(
                    repository=repo,
                    number=i,
                    title=fake.sentence(nb_words=8),
                    body=fake.text(max_nb_chars=500),
                    author=random.choice(users),
                    head_branch=random.choice(['feature/new', 'bugfix/issue', 'develop']),
                    base_branch='main',
                    head_repo=repo,
                    head_sha=fake.sha1(),
                    base_sha=fake.sha1(),
                    state=state,
                    merged=state == 'merged',
                    draft=random.random() < 0.2,
                    locked=random.random() < 0.05,
                    comments_count=random.randint(0, 30),
                    commits_count=random.randint(1, 50),
                    additions=random.randint(10, 1000),
                    deletions=random.randint(0, 500),
                    changed_files=random.randint(1, 20),
                    created_at=fake.date_time_between(start_date='-6m', end_date='now', tzinfo=UTC)
                )
                
                if state in ['closed', 'merged']:
                    pr.closed_at = fake.date_time_between(start_date=pr.created_at, end_date='now', tzinfo=UTC)
                
                if state == 'merged':
                    pr.merged_by = random.choice(users)
                    pr.merged_at = pr.closed_at
                    pr.merge_commit_sha = fake.sha1()
                
                prs.append(pr)
        
        PullRequest.objects.bulk_create(prs)
        
        # Add assignees and reviewers
        for pr in PullRequest.objects.all()[:100]:
            assignees = random.sample(list(users), random.randint(0, 2))
            reviewers = random.sample(list(users), random.randint(0, 3))
            pr.assignees.set(assignees)
            pr.reviewers.set(reviewers)
        
        return PullRequest.objects.all()

    def create_pr_labels(self, prs, labels):
        """Create PR label relationships"""
        pr_labels = []
        for pr in prs:
            repo_labels = labels.filter(repository=pr.repository)
            if repo_labels.exists():
                selected_labels = random.sample(list(repo_labels), min(random.randint(1, 2), repo_labels.count()))
                for label in selected_labels:
                    pr_labels.append(PullRequestLabel(
                        pull_request=pr,
                        label=label
                    ))
        
        PullRequestLabel.objects.bulk_create(pr_labels, ignore_conflicts=True)

    def create_comments(self, issues, prs, users):
        """Create comments on issues and PRs"""
        comments = []
        
        # Issue comments
        for issue in list(issues)[:50]:
            for _ in range(random.randint(0, 5)):
                comments.append(Comment(
                    issue=issue,
                    author=random.choice(users),
                    body=fake.text(max_nb_chars=300),
                    created_at=fake.date_time_between(start_date=issue.created_at, end_date='now', tzinfo=UTC)
                ))
        
        # PR comments
        for pr in list(prs)[:50]:
            for _ in range(random.randint(0, 5)):
                comments.append(Comment(
                    pull_request=pr,
                    author=random.choice(users),
                    body=fake.text(max_nb_chars=300),
                    created_at=fake.date_time_between(start_date=pr.created_at, end_date='now', tzinfo=UTC)
                ))
        
        Comment.objects.bulk_create(comments)

    def create_reviews(self, prs, users):
        """Create PR reviews"""
        reviews = []
        review_comments = []
        
        for pr in list(prs)[:50]:
            for _ in range(random.randint(0, 3)):
                review = Review(
                    pull_request=pr,
                    reviewer=random.choice(users),
                    body=fake.text(max_nb_chars=200),
                    state=random.choice(['approved', 'changes_requested', 'commented']),
                    commit_sha=pr.head_sha,
                    submitted_at=fake.date_time_between(start_date=pr.created_at, end_date='now', tzinfo=UTC)
                )
                reviews.append(review)
        
        Review.objects.bulk_create(reviews)
        
        # Add review comments
        for review in Review.objects.all()[:30]:
            for _ in range(random.randint(1, 3)):
                review_comments.append(ReviewComment(
                    review=review,
                    pull_request=review.pull_request,
                    author=review.reviewer,
                    body=fake.sentence(),
                    path='src/main.py',
                    position=random.randint(1, 100),
                    line=random.randint(1, 100),
                    commit_sha=review.commit_sha
                ))
        
        ReviewComment.objects.bulk_create(review_comments)

    def create_stars(self, repos, users):
        """Create repository stars"""
        stars = []
        for user in users:
            num_stars = random.randint(5, 20)
            starred_repos = random.sample(list(repos), min(num_stars, len(repos)))
            
            for repo in starred_repos:
                stars.append(Star(
                    repository=repo,
                    user=user,
                    created_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=UTC)
                ))
        
        Star.objects.bulk_create(stars, ignore_conflicts=True)

    def create_watches(self, repos, users):
        """Create repository watches"""
        watches = []
        for user in users:
            num_watches = random.randint(3, 15)
            watched_repos = random.sample(list(repos), min(num_watches, len(repos)))
            
            for repo in watched_repos:
                watches.append(Watch(
                    repository=repo,
                    user=user,
                    created_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=UTC)
                ))
        
        Watch.objects.bulk_create(watches, ignore_conflicts=True)

    def create_releases(self, repos, users):
        """Create releases"""
        releases = []
        for repo in list(repos)[:30]:
            num_releases = random.randint(1, 5)
            for i in range(1, num_releases + 1):
                releases.append(Release(
                    repository=repo,
                    tag_name=f"v{i}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                    target_commitish='main',
                    name=f"Release {i}.0",
                    body=fake.text(max_nb_chars=300),
                    draft=random.random() < 0.1,
                    prerelease=random.random() < 0.2,
                    author=random.choice(users),
                    published_at=fake.date_time_between(start_date='-1y', end_date='now', tzinfo=UTC)
                ))
        
        Release.objects.bulk_create(releases, ignore_conflicts=True)
        return Release.objects.all()

    def create_webhooks(self, repos):
        """Create webhooks"""
        webhooks = []
        for repo in list(repos)[:20]:
            webhooks.append(Webhook(
                repository=repo,
                url=fake.url(),
                content_type='application/json',
                events=['push', 'pull_request', 'issues'],
                active=random.random() > 0.2
            ))
        
        Webhook.objects.bulk_create(webhooks)

    def create_notifications(self, users, repos):
        """Create notifications"""
        notifications = []
        for user in list(users)[:15]:
            for _ in range(random.randint(5, 20)):
                notifications.append(Notification(
                    user=user,
                    repository=random.choice(repos),
                    notification_type=random.choice(['issue', 'pull_request', 'commit', 'release', 'mention']),
                    subject=fake.sentence(),
                    reason=random.choice(['subscribed', 'mentioned', 'author', 'comment']),
                    unread=random.random() > 0.3,
                    url=fake.url(),
                    created_at=fake.date_time_between(start_date='-1m', end_date='now', tzinfo=UTC)
                ))
        
        Notification.objects.bulk_create(notifications)

    def create_activities(self, users, repos):
        """Create user activities"""
        activities = []
        for user in list(users)[:15]:
            for _ in range(random.randint(10, 30)):
                activities.append(Activity(
                    user=user,
                    event_type=random.choice(['push', 'create', 'fork', 'star', 'watch', 'issue', 'pull_request']),
                    repository=random.choice(repos),
                    payload={'action': 'created', 'ref': 'main'},
                    public=random.random() > 0.2,
                    created_at=fake.date_time_between(start_date='-3m', end_date='now', tzinfo=UTC)
                ))
        
        Activity.objects.bulk_create(activities)

    def create_ssh_keys(self, users):
        """Create SSH keys"""
        ssh_keys = []
        for user in list(users)[:10]:
            for i in range(random.randint(1, 3)):
                key_data = fake.sha256()
                fingerprint = hashlib.sha256(key_data.encode()).hexdigest()[:32]
                ssh_keys.append(SSHKey(
                    user=user,
                    title=f"{fake.word()}-key-{i}",
                    key=f"ssh-rsa {key_data}",
                    fingerprint=fingerprint,
                    last_used=fake.date_time_between(start_date='-1m', end_date='now', tzinfo=UTC) if random.random() > 0.5 else None
                ))
        
        SSHKey.objects.bulk_create(ssh_keys, ignore_conflicts=True)

    def create_access_tokens(self, users):
        """Create access tokens"""
        tokens = []
        for user in list(users)[:10]:
            for i in range(random.randint(1, 3)):
                tokens.append(AccessToken(
                    user=user,
                    name=f"{fake.word()}-token-{i}",
                    token=fake.sha256(),
                    scopes=['repo', 'user', 'gist'],
                    last_used=fake.date_time_between(start_date='-1w', end_date='now', tzinfo=UTC) if random.random() > 0.5 else None,
                    expires_at=fake.date_time_between(start_date='+1m', end_date='+1y', tzinfo=UTC) if random.random() > 0.3 else None
                ))
        
        AccessToken.objects.bulk_create(tokens, ignore_conflicts=True)