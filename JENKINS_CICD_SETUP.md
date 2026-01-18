# Jenkins CI/CD Pipeline Setup for Microservices

## Overview
This document provides complete instructions for the CI/CD pipelines created for both microservices.

## Pipelines Created

### 1. Microservice_One_Pipeline
- **Jenkins URL**: http://localhost:8080/job/Microservice_One_Pipeline
- **GitHub Repository**: https://github.com/wak75/Microservice_One
- **DockerHub Image**: was24/microservice-one

### 2. Microservice_two_Pipeline
- **Jenkins URL**: http://localhost:8080/job/Microservice_two_Pipeline
- **GitHub Repository**: https://github.com/wak75/Microservice_two
- **DockerHub Image**: was24/microservice-two

## Pipeline Stages

Each pipeline includes the following automated stages:

1. **Checkout**: Clones the code from GitHub repository (main branch)
2. **Install Dependencies**: Runs `npm install` to install Node.js dependencies
3. **Run Tests**: Executes `npm test` to run all test cases
4. **SonarQube Analysis**: Performs code quality and security analysis
5. **Quality Gate**: Waits for SonarQube quality gate to pass (aborts if fails)
6. **Build Docker Image**: Creates Docker image with build number and latest tags
7. **Push to DockerHub**: Pushes the Docker image to DockerHub repository

## Required Jenkins Credentials

You need to configure the following credentials in Jenkins:

### 1. DockerHub Credentials
- **ID**: `dockerhub-credentials`
- **Type**: Username with password
- **Username**: was24
- **Password**: Your DockerHub password/access token

**Setup Steps**:
```
1. Go to Jenkins → Manage Jenkins → Credentials
2. Click on "System" → "Global credentials"
3. Click "Add Credentials"
4. Kind: Username with password
5. Scope: Global
6. Username: was24
7. Password: [Your DockerHub password]
8. ID: dockerhub-credentials
9. Description: DockerHub credentials for pushing images
10. Click "Create"
```

### 2. SonarQube Token
- **ID**: `sonarqube-token`
- **Type**: Secret text
- **Secret**: Your SonarQube authentication token

**Setup Steps**:
```
1. First, generate a token in SonarQube:
   - Log in to SonarQube at http://localhost:9000
   - Go to My Account → Security
   - Generate a new token and copy it

2. In Jenkins:
   - Go to Jenkins → Manage Jenkins → Credentials
   - Click on "System" → "Global credentials"
   - Click "Add Credentials"
   - Kind: Secret text
   - Scope: Global
   - Secret: [Paste your SonarQube token]
   - ID: sonarqube-token
   - Description: SonarQube authentication token
   - Click "Create"
```

## Required Jenkins Plugins

Ensure the following plugins are installed:

1. **Git Plugin** - For Git repository integration
2. **Pipeline Plugin** - For pipeline support
3. **GitHub Plugin** - For GitHub integration
4. **Docker Pipeline Plugin** - For Docker commands
5. **SonarQube Scanner Plugin** - For SonarQube integration
6. **Credentials Plugin** - For credentials management

**Installation Steps**:
```
1. Go to Jenkins → Manage Jenkins → Plugins
2. Click "Available plugins"
3. Search for each plugin and install
4. Restart Jenkins after installation
```

## SonarQube Configuration in Jenkins

### Configure SonarQube Server
```
1. Go to Jenkins → Manage Jenkins → System
2. Scroll to "SonarQube servers" section
3. Click "Add SonarQube"
4. Name: SonarQube
5. Server URL: http://sonarqube:9000
6. Server authentication token: Select "sonarqube-token" credential
7. Click "Save"
```

### Configure SonarQube Scanner
```
1. Go to Jenkins → Manage Jenkins → Tools
2. Scroll to "SonarQube Scanner" section
3. Click "Add SonarQube Scanner"
4. Name: SonarScanner
5. Install automatically: Check this option
6. Version: Select latest version
7. Click "Save"
```

## GitHub Webhook Configuration

To enable automatic pipeline triggers on code commits:

### For Microservice_One:
```
1. Go to https://github.com/wak75/Microservice_One/settings/hooks
2. Click "Add webhook"
3. Payload URL: http://your-jenkins-url:8080/github-webhook/
   (Replace 'your-jenkins-url' with your actual Jenkins URL)
4. Content type: application/json
5. Which events: Select "Just the push event"
6. Active: Check this box
7. Click "Add webhook"
```

### For Microservice_two:
```
1. Go to https://github.com/wak75/Microservice_two/settings/hooks
2. Click "Add webhook"
3. Payload URL: http://your-jenkins-url:8080/github-webhook/
4. Content type: application/json
5. Which events: Select "Just the push event"
6. Active: Check this box
7. Click "Add webhook"
```

**Note**: If Jenkins is running on localhost, you'll need to:
- Either expose Jenkins using a tunneling service (ngrok, localtunnel)
- Or use GitHub polling instead of webhooks

### Alternative: Use Polling Instead of Webhooks
If webhooks are not feasible, enable polling in Jenkins:
```
1. Open each pipeline configuration
2. Under "Build Triggers"
3. Check "Poll SCM"
4. Schedule: H/5 * * * * (polls every 5 minutes)
5. Save
```

## Docker Repository Setup

The pipelines will automatically create repositories in DockerHub when first run. However, you can pre-create them:

### Create DockerHub Repositories (Optional)
```
1. Log in to https://hub.docker.com
2. Click "Create Repository"
3. For Microservice_One:
   - Name: microservice-one
   - Visibility: Public (or Private as needed)
4. For Microservice_two:
   - Name: microservice-two
   - Visibility: Public (or Private as needed)
```

## Testing the Pipelines

### Manual Build Test
```
1. Go to Jenkins dashboard
2. Click on "Microservice_One_Pipeline"
3. Click "Build Now"
4. Monitor the build progress in "Build History"
5. Check console output for any issues
6. Repeat for "Microservice_two_Pipeline"
```

### Automated Trigger Test
```
1. Make a change to any file in Microservice_One repository
2. Commit and push to GitHub:
   git add .
   git commit -m "Test CI/CD pipeline"
   git push origin main
3. Check Jenkins - the pipeline should automatically trigger
4. Verify the build completes successfully
5. Check DockerHub for the new image
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Docker Login Fails
- Verify DockerHub credentials are correct in Jenkins
- Check if Docker is running on Jenkins agent
- Ensure credential ID matches 'dockerhub-credentials'

#### 2. SonarQube Analysis Fails
- Verify SonarQube server is running
- Check SonarQube token is valid
- Ensure SonarQube server URL is correct
- Check network connectivity between Jenkins and SonarQube

#### 3. Tests Fail
- Review test output in Jenkins console
- Ensure all npm dependencies are installed
- Check if test files are properly configured

#### 4. GitHub Webhook Not Triggering
- Verify webhook URL is correct and accessible
- Check webhook delivery history in GitHub
- Ensure Jenkins GitHub plugin is installed
- Try using polling as an alternative

#### 5. Docker Image Push Fails
- Check DockerHub credentials
- Verify Docker daemon is running
- Ensure sufficient disk space
- Check network connectivity to DockerHub

## Pipeline Environment Variables

Both pipelines use the following environment variables:

```groovy
DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
DOCKERHUB_USERNAME = 'was24'
IMAGE_NAME = 'microservice-one' or 'microservice-two'
SONAR_HOST_URL = 'http://sonarqube:9000'
SONAR_TOKEN = credentials('sonarqube-token')
```

## Build Artifacts

Each successful build produces:
- Docker image tagged with build number (e.g., was24/microservice-one:5)
- Docker image tagged as latest (e.g., was24/microservice-one:latest)
- SonarQube analysis report (available in SonarQube dashboard)
- Test results (available in Jenkins build logs)

## Monitoring and Notifications

### View Build History
```
1. Go to Jenkins dashboard
2. Click on the pipeline name
3. View "Build History" on the left sidebar
4. Click on any build number to see details
```

### Console Output
```
1. Click on a build number
2. Click "Console Output" to see detailed logs
3. Look for any errors or warnings
```

## Next Steps

After completing the setup:

1. ✅ Configure Jenkins credentials (DockerHub, SonarQube)
2. ✅ Install required Jenkins plugins
3. ✅ Configure SonarQube integration
4. ✅ Set up GitHub webhooks
5. ✅ Run manual test builds
6. ✅ Verify Docker images in DockerHub
7. ✅ Test automated triggers with code commits

## Security Best Practices

1. Use access tokens instead of passwords for DockerHub
2. Rotate SonarQube tokens regularly
3. Use Jenkins credentials for sensitive data
4. Enable HTTPS for Jenkins in production
5. Restrict webhook payload URLs
6. Use secret scanning in SonarQube
7. Enable Docker Content Trust for image signing

## Additional Resources

- Jenkins Documentation: https://www.jenkins.io/doc/
- SonarQube Documentation: https://docs.sonarqube.org/
- Docker Documentation: https://docs.docker.com/
- GitHub Webhooks: https://docs.github.com/webhooks

## Support

For issues or questions:
1. Check Jenkins console logs
2. Review SonarQube analysis reports
3. Verify all credentials are configured correctly
4. Check Docker daemon status
5. Review GitHub webhook delivery history
