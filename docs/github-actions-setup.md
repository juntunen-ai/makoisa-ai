# GitHub Actions CI/CD Setup Guide

This guide explains how to set up the GitHub Actions CI/CD pipeline for the S-kaupat scraper.

## 🔧 Prerequisites

### 1. Google Cloud Setup
- Google Cloud Project with billing enabled
- Service account with appropriate permissions
- Cloud Run, BigQuery, and Container Registry APIs enabled

### 2. GitHub Repository Secrets

You need to add these secrets to your GitHub repository:

#### Required Secrets

1. **`GCP_PROJECT_ID`**
   - Your Google Cloud Project ID
   - Example: `my-project-123456`

2. **`GCP_SA_KEY`**
   - Service account JSON key with the following roles:
     - Cloud Run Admin
     - BigQuery Admin
     - Storage Admin
     - Container Registry Service Agent
   
   To create this:
   ```bash
   # Create service account
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions CI/CD"
   
   # Grant necessary roles
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/bigquery.admin"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   
   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"
   
   # Create and download key
   gcloud iam service-accounts keys create github-actions-key.json \
     --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com
   ```
   
   Then copy the entire content of `github-actions-key.json` into the GitHub secret.

### 3. Adding Secrets to GitHub

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add both secrets mentioned above

## 🚀 Workflows Overview

### 1. **CI/CD Pipeline** (`.github/workflows/ci-cd.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`

**Jobs:**
- **Test**: Runs unit tests, linting, and code quality checks
- **Security**: Vulnerability scanning with Trivy
- **Build**: Builds and pushes Docker image
- **Deploy**: Deploys to Cloud Run (only on main branch)

### 2. **Pull Request Checks** (`.github/workflows/pr-checks.yml`)

**Triggers:**
- Pull requests to `main` or `develop`

**Jobs:**
- **Code Quality**: Black formatting, flake8 linting
- **Test Suite**: Unit and integration tests
- **Docker Build**: Test Docker image builds
- **Security Scan**: Vulnerability scanning
- **API Contract**: Validates API endpoints

### 3. **Dependency Updates** (`.github/workflows/dependency-updates.yml`)

**Triggers:**
- Weekly schedule (Mondays at 9 AM UTC)
- Manual trigger

**Jobs:**
- **Update**: Updates Poetry dependencies and creates PR if changes

### 4. **Release** (`.github/workflows/release.yml`)

**Triggers:**
- Git tags starting with `v` (e.g., `v1.0.0`)

**Jobs:**
- **Release**: Builds, tests, deploys, and creates GitHub release

## 📋 Workflow Process

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make Changes**
   - Code changes
   - Add/update tests
   - Update documentation

3. **Push and Create PR**
   ```bash
   git push origin feature/new-feature
   # Create pull request on GitHub
   ```

4. **Automated Checks**
   - PR checks workflow runs automatically
   - Code quality, tests, security scans
   - Review required for merge

5. **Merge to Main**
   - Automatic deployment to production
   - Full CI/CD pipeline runs

### Release Workflow

1. **Create Release Tag**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Automatic Release**
   - Release workflow triggers
   - Builds production image
   - Deploys to Cloud Run
   - Creates GitHub release

## 🔍 Monitoring and Debugging

### Checking Workflow Status

1. Go to **Actions** tab in your GitHub repository
2. Click on any workflow run to see details
3. Each job shows logs and status

### Common Issues

#### **Authentication Errors**
- Check `GCP_SA_KEY` secret is correct
- Verify service account has required permissions
- Ensure project ID matches

#### **Test Failures**
- Check test logs in Actions tab
- Run tests locally: `poetry run pytest tests/ -v`
- Verify Playwright dependencies

#### **Docker Build Failures**
- Check Dockerfile syntax
- Verify all dependencies in pyproject.toml
- Test local build: `docker build -t test .`

#### **Deployment Failures**
- Verify Cloud Run service exists
- Check region settings
- Ensure APIs are enabled

## 🛡️ Security Features

### Automated Security Scanning
- **Trivy**: Scans for vulnerabilities in dependencies and container
- **GitHub Security**: SARIF reports uploaded to Security tab
- **Dependabot**: Automated security updates (if enabled)

### Safe Deployment Practices
- **No secrets in code**: All sensitive data in GitHub secrets
- **Minimal permissions**: Service accounts with least privilege
- **Health checks**: Deployment verification before completion
- **Rollback ready**: Tagged images for easy rollback

## 📊 Performance Optimization

### Caching
- **Poetry dependencies**: Cached between runs
- **Docker layers**: Multi-stage builds for efficiency
- **Playwright browsers**: Cached installation

### Parallel Execution
- **Matrix builds**: Multiple Python versions (if needed)
- **Parallel jobs**: Independent test/build/scan jobs
- **Conditional execution**: Deploy only on main branch

## 🎯 Best Practices

### Branch Protection
Set up branch protection rules on `main`:
- Require PR reviews
- Require status checks to pass
- Require branches to be up to date

### Environment Separation
- **Development**: Deploy from `develop` branch
- **Production**: Deploy from `main` branch
- **Staging**: Use git tags for releases

### Monitoring
- Monitor workflow success rates
- Set up notifications for failures
- Regular dependency updates

## ✅ Setup Checklist

- [ ] Google Cloud project set up
- [ ] Service account created with proper roles
- [ ] GitHub secrets configured (`GCP_PROJECT_ID`, `GCP_SA_KEY`)
- [ ] Initial deployment script run manually
- [ ] Branch protection rules enabled
- [ ] Workflows tested with sample PR

## 🚀 Ready to Deploy!

Once setup is complete, your workflow will be:

1. **Push code** → Automatic testing and deployment
2. **Create PR** → Comprehensive checks and reviews
3. **Merge to main** → Production deployment
4. **Create tag** → Release with GitHub release notes

The CI/CD pipeline ensures consistent, reliable deployments with comprehensive testing and security scanning.
