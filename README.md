# GitHub Clone System - Complete Setup Guide

## Overview
This system includes:
1. **Django Models** - Complete database schema for a GitHub-like platform
2. **C++ Project Manager** - CLI tool to upload projects to GitHub

---

## Part 1: Django GitHub Clone Setup

### Prerequisites
```bash
pip install django pillow psycopg2-binary
```

### Database Setup

**For PostgreSQL:**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'github_clone',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Create Django Project
```bash
django-admin startproject github_clone
cd github_clone
python manage.py startapp core
```

### Add Models
Copy the Django models artifact into `core/models.py`

### Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Key Django Models Explained

#### User Model
- Extended from `AbstractUser`
- Includes GitHub-like profile features
- Tracks followers, repositories, organizations

#### Repository Model
- Supports public/private visibility
- Fork relationships
- Stars, watchers, issues tracking
- Language detection and topics

#### Issue & Pull Request Models
- Complete issue tracking
- PR reviews and comments
- Labels and assignees
- State management (open/closed/merged)

#### Commit & File Models
- Full commit history
- File versioning
- Branch management

---

## Part 2: C++ GitHub Project Manager

### Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install build-essential cmake
sudo apt-get install libcurl4-openssl-dev
sudo apt-get install libssl-dev
sudo apt-get install libjsoncpp-dev
```

**macOS (Homebrew):**
```bash
brew install cmake curl openssl jsoncpp
```

**Windows (vcpkg):**
```bash
vcpkg install curl openssl jsoncpp
```

### Build Instructions

1. **Create project structure:**
```bash
mkdir github-manager
cd github-manager
```

2. **Save the C++ code as `main.cpp`**

3. **Save CMakeLists.txt**

4. **Build:**
```bash
mkdir build
cd build
cmake ..
make
```

5. **Run:**
```bash
./github_manager
```

---

## Part 3: Getting GitHub Personal Access Token

### Steps to Create PAT:

1. Go to GitHub.com → Settings
2. Developer Settings → Personal Access Tokens → Tokens (classic)
3. Click "Generate new token"
4. Select scopes:
   - `repo` (full control of private repositories)
   - `workflow` (update GitHub Actions workflows)
   - `write:packages` (upload packages)
   - `delete:packages` (delete packages)
5. Copy the token (save it securely!)

---

## Part 4: Using the C++ Project Manager

### First Time Setup
When you run the program, it will ask for:
- GitHub Personal Access Token
- GitHub Username

These are saved in `github_config.json` for future use.

### Features

#### 1. Create New Repository
```
Choice: 1
Repository name: my-awesome-project
Description: A cool project
Private? (y/n): n
```

#### 2. Upload Single File
```
Choice: 2
Repository name: my-awesome-project
File path: /path/to/file.cpp
Commit message: Add main file
```

#### 3. Upload Entire Project
```
Choice: 3
Repository name: my-awesome-project
Project directory: /path/to/project/
Commit message: Initial commit
```

This will recursively upload all files maintaining directory structure.

#### 4. Delete File
```
Choice: 4
Repository name: my-awesome-project
File path: old_file.cpp
Commit message: Remove deprecated file
```

#### 5. List Repositories
Shows all your repositories with details.

#### 6. View User Info
Displays your GitHub profile information.

---

## Part 5: Advanced C++ Integration with libgit2

For local Git operations, you can extend the C++ program:

### Install libgit2
```bash
# Ubuntu/Debian
sudo apt-get install libgit2-dev

# macOS
brew install libgit2
```

### Example libgit2 Usage
```cpp
#include <git2.h>

bool initLocalRepo(const std::string& path) {
    git_repository *repo = nullptr;
    git_libgit2_init();
    
    int error = git_repository_init(&repo, path.c_str(), 0);
    if (error < 0) {
        const git_error *e = git_error_last();
        std::cerr << "Error: " << e->message << std::endl;
        return false;
    }
    
    git_repository_free(repo);
    git_libgit2_shutdown();
    return true;
}
```

---

## Part 6: Django REST API for C++ Integration

### Create API Endpoints

```python
# views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Repository, Commit, Issue
from .serializers import RepositorySerializer

class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Repository.objects.filter(owner=self.request.user)
```

### URLs
```python
# urls.py
from rest_framework.routers import DefaultRouter
from .views import RepositoryViewSet

router = DefaultRouter()
router.register(r'repositories', RepositoryViewSet)

urlpatterns = router.urls
```

---

## Part 7: Security Best Practices

### For Django:
1. **Use environment variables for secrets:**
```python
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
```

2. **Enable HTTPS only:**
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

3. **Rate limiting:**
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

### For C++:
1. **Never hardcode tokens**
2. **Use secure file permissions:**
```bash
chmod 600 github_config.json
```

3. **Encrypt stored credentials:**
```cpp
// Use OpenSSL for encryption
```

---

## Part 8: Testing

### Django Tests
```python
# tests.py
from django.test import TestCase
from .models import User, Repository

class RepositoryTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser')
        
    def test_create_repository(self):
        repo = Repository.objects.create(
            name='test-repo',
            owner=self.user
        )
        self.assertEqual(repo.name, 'test-repo')
```

Run tests:
```bash
python manage.py test
```

### C++ Tests
Use Google Test framework for unit testing.

---

## Part 9: Deployment

### Django Deployment (Heroku Example)
```bash
pip install gunicorn dj-database-url
echo "web: gunicorn github_clone.wsgi" > Procfile
git push heroku main
```

### C++ Distribution
```bash
# Create binary package
mkdir -p package/bin
cp build/github_manager package/bin/
tar -czf github-manager.tar.gz package/
```

---

## Troubleshooting

### Common Issues:

**Django Migration Errors:**
```bash
python manage.py migrate --run-syncdb
```

**C++ cURL SSL Errors:**
```bash
# Update CA certificates
sudo update-ca-certificates
```

**GitHub API Rate Limiting:**
- Authenticated requests: 5,000/hour
- Unauthenticated: 60/hour

---

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [GitHub REST API](https://docs.github.com/en/rest)
- [libgit2 Documentation](https://libgit2.org/)
- [cURL Documentation](https://curl.se/libcurl/)

---

## License
MIT License - Feel free to modify and use in your projects!