# 🎯 Task Graph Example: Deploy Code to Kubernetes

## Real-World Example Using OPS Bot Intelligent Planner

This document shows a complete example of how OPS Bot analyzes available MCPs and creates an optimal task graph for deploying code to Kubernetes.

---

## 📋 Scenario

**User Command**: `"Deploy the code to Kubernetes production"`

**Available MCPs**:
- Jenkins MCP (CI/CD)
- SonarQube MCP (Quality Analysis)
- Docker Hub MCP (Container Registry)
- Kubernetes MCP (Orchestration)

---

## 🧠 Step 1: Intent Analysis

```python
User Input: "Deploy the code to Kubernetes production"

OPS Bot Analyzes:
{
  "action": "deploy",
  "target": "code",
  "environment": "production",
  "platform": "kubernetes",
  "urgency": "normal"
}
```

---

## 🔍 Step 2: Available Tools Discovery

```python
Scanning Running MCP Servers...

┌─────────────────────────────────────────────────────────────┐
│ Jenkins MCP - 15 Tools Available                            │
├─────────────────────────────────────────────────────────────┤
│ • trigger_build          : Trigger a Jenkins build          │
│ • get_build_status       : Get build status                 │
│ • get_build_logs         : Retrieve build logs              │
│ • run_tests              : Execute test suite               │
│ • get_test_results       : Get test results                 │
│ ... (10 more tools)                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SonarQube MCP - 10 Tools Available                          │
├─────────────────────────────────────────────────────────────┤
│ • analyze_project        : Run code analysis                │
│ • get_quality_gate       : Get quality gate status          │
│ • get_code_coverage      : Get code coverage metrics        │
│ • get_vulnerabilities    : Check security vulnerabilities   │
│ • get_code_smells        : Get code quality issues          │
│ ... (5 more tools)                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Docker Hub MCP - 8 Tools Available                          │
├─────────────────────────────────────────────────────────────┤
│ • push_image             : Push image to registry           │
│ • pull_image             : Pull image from registry         │
│ • tag_image              : Tag a Docker image               │
│ • verify_image           : Verify image exists              │
│ • get_image_metadata     : Get image metadata               │
│ ... (3 more tools)                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Kubernetes MCP - 12 Tools Available                         │
├─────────────────────────────────────────────────────────────┤
│ • apply_deployment       : Deploy application               │
│ • get_pods               : List pods                        │
│ • get_pod_logs           : Get pod logs                     │
│ • scale_deployment       : Scale deployment                 │
│ • rollback_deployment    : Rollback to previous version     │
│ • get_service            : Get service details              │
│ ... (6 more tools)                                          │
└─────────────────────────────────────────────────────────────┘

Total: 45 tools across 4 MCP servers
```

---

## 🎯 Step 3: Pattern Matching & Tool Selection

```python
Environment: production
Action: deploy
Pattern Selected: "production_deployment"

Required Steps:
1. build          → Jenkins MCP: trigger_build ✓
2. test           → Jenkins MCP: run_tests ✓
3. quality_scan   → SonarQube MCP: analyze_project ✓
4. security_scan  → SonarQube MCP: get_vulnerabilities ✓
5. build_image    → Docker Hub MCP: push_image ✓
6. verify_image   → Docker Hub MCP: verify_image ✓
7. deploy         → Kubernetes MCP: apply_deployment ✓
8. verify_pods    → Kubernetes MCP: get_pods ✓
9. check_health   → Kubernetes MCP: get_pod_logs ✓
10. monitor       → Kubernetes MCP: get_service ✓
```

---

## 📊 Step 4: Generated Task Graph

### Visual Representation

```
┌─────────────────────────────────────────────────────────────────┐
│                     TASK GRAPH                                   │
│           Deploy Code to Kubernetes Production                   │
└─────────────────────────────────────────────────────────────────┘

                        START
                          │
                          ▼
              ┌───────────────────────┐
              │   Step 1: BUILD       │
              │   Jenkins MCP         │
              │   trigger_build       │
              │   Risk: MEDIUM 🟡     │
              │   Duration: 2-5 min   │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Step 2: TEST        │
              │   Jenkins MCP         │
              │   run_tests           │
              │   Risk: MEDIUM 🟡     │
              │   Duration: 3-7 min   │
              └───────────┬───────────┘
                          │
                          ▼
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────────┐           ┌───────────────────┐
│ Step 3: QUALITY   │           │ Step 4: SECURITY  │
│ SonarQube MCP     │           │ SonarQube MCP     │
│ analyze_project   │           │ get_vulns         │
│ Risk: MEDIUM 🟡   │           │ Risk: MEDIUM 🟡   │
│ Duration: 2-4 min │           │ Duration: 2-3 min │
└─────────┬─────────┘           └─────────┬─────────┘
          │                               │
          └───────────────┬───────────────┘
                          │
                    [GATE: Both Pass?]
                          │
                          ▼
              ┌───────────────────────┐
              │ Step 5: BUILD IMAGE   │
              │ Docker Hub MCP        │
              │ push_image            │
              │ Risk: MEDIUM 🟡       │
              │ Duration: 3-5 min     │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Step 6: VERIFY IMAGE  │
              │ Docker Hub MCP        │
              │ verify_image          │
              │ Risk: LOW 🟢          │
              │ Duration: < 1 min     │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Step 7: DEPLOY K8S    │
              │ Kubernetes MCP        │
              │ apply_deployment      │
              │ Risk: HIGH 🟠         │
              │ Duration: 2-3 min     │
              │ ⚠️  APPROVAL REQUIRED │
              └───────────┬───────────┘
                          │
                          ▼
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────────┐           ┌───────────────────┐
│ Step 8: VERIFY    │           │ Step 9: HEALTH    │
│ Kubernetes MCP    │           │ Kubernetes MCP    │
│ get_pods          │           │ get_pod_logs      │
│ Risk: LOW 🟢      │           │ Risk: LOW 🟢      │
│ Duration: < 1 min │           │ Duration: 1-2 min │
└─────────┬─────────┘           └─────────┬─────────┘
          │                               │
          └───────────────┬───────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Step 10: MONITOR      │
              │ Kubernetes MCP        │
              │ get_service           │
              │ Risk: LOW 🟢          │
              │ Duration: < 1 min     │
              └───────────┬───────────┘
                          │
                          ▼
                        END
                 (Deployment Complete)
```

---

## 📋 Step 5: Complete Generated Plan

```
================================================================================
📋 INTELLIGENT TASK PLAN: plan_deploy_production_1737354243
================================================================================

🎯 Task: Deploy code to production Kubernetes
⚡ Priority: HIGH
⚠️  Overall Risk: HIGH
⏱️  Estimated Duration: 20-35 minutes
📊 Total Steps: 10

⚠️  APPROVAL REQUIRED - High-risk operation in production environment

📜 Compliance Requirements:
  ✓ quality_gate_passed
  ✓ security_scan_passed
  ✓ approval_required
  ✓ backup_verified
  ✓ rollback_plan_ready
  ✓ monitoring_enabled

🔄 Rollback Strategy:
  Automatic rollback available for 3 critical steps. Previous version 
  maintained as backup. Kubernetes deployment supports instant rollback 
  to previous ReplicaSet.

✅ Success Criteria:
  • All steps completed without errors
  • Health checks passed
  • No error logs in monitoring
  • Zero user-facing errors
  • Response time within SLA
  • All pods running and ready (2/2)
  • Service endpoint accessible
  • No memory leaks detected

🚨 Failure Handling:
  Automatic rollback to previous stable version with immediate notification
  to team via Slack/Email. All logs archived for post-mortem analysis.

================================================================================
EXECUTION STEPS
================================================================================

📍 Step 1: Build application code
   Server: Jenkins MCP
   Tool: trigger_build
   Risk: MEDIUM 🟡
   Duration: 2-5 minutes
   Dependencies: None
   Arguments:
     • job_name: production-build-pipeline
     • branch: main
     • parameters: {"environment": "production", "clean_build": true}
   
   What this does: Compiles source code, resolves dependencies, creates 
   build artifacts

---

📍 Step 2: Run automated test suite
   Server: Jenkins MCP
   Tool: run_tests
   Risk: MEDIUM 🟡
   Duration: 3-7 minutes
   Dependencies: Step 1
   Arguments:
     • test_suite: all
     • coverage_required: 80
     • fail_on_error: true
   
   What this does: Executes unit tests, integration tests, generates 
   coverage report

---

📍 Step 3: Code quality analysis
   Server: SonarQube MCP
   Tool: analyze_project
   Risk: MEDIUM 🟡
   Duration: 2-4 minutes
   Dependencies: Step 2
   Compliance: quality_gate_passed
   Arguments:
     • project_key: my-application
     • branch: main
     • quality_gate: production-gate
   
   What this does: Analyzes code quality, detects code smells, measures 
   technical debt, checks quality gate

---

📍 Step 4: Security vulnerability scan
   Server: SonarQube MCP
   Tool: get_vulnerabilities
   Risk: MEDIUM 🟡
   Duration: 2-3 minutes
   Dependencies: Step 3
   Compliance: security_scan_passed
   Arguments:
     • project_key: my-application
     • severity: ["HIGH", "CRITICAL"]
     • block_on_critical: true
   
   What this does: Scans for security vulnerabilities, checks dependencies 
   for known CVEs

---

📍 Step 5: Build and push Docker image
   Server: Docker Hub MCP
   Tool: push_image
   Risk: MEDIUM 🟡
   Duration: 3-5 minutes
   Dependencies: Steps 3, 4
   Arguments:
     • image_name: myorg/my-application
     • tag: v1.0.0-prod
     • dockerfile: Dockerfile.prod
     • build_args: {"ENV": "production"}
   
   What this does: Builds Docker image from Dockerfile, tags it, pushes 
   to Docker Hub registry

---

📍 Step 6: Verify Docker image
   Server: Docker Hub MCP
   Tool: verify_image
   Risk: LOW 🟢
   Duration: < 1 minute
   Dependencies: Step 5
   Arguments:
     • image_name: myorg/my-application:v1.0.0-prod
     • check_layers: true
     • verify_signature: true
   
   What this does: Confirms image exists in registry, verifies integrity, 
   checks image layers

---

📍 Step 7: Deploy to Kubernetes
   Server: Kubernetes MCP
   Tool: apply_deployment
   Risk: HIGH 🟠
   Duration: 2-3 minutes
   Dependencies: Step 6
   ⚠️  Manual validation required after this step
   Compliance: quality_gate_passed, security_scan_passed, approval_required, 
               backup_verified, rollback_plan_ready, monitoring_enabled
   Arguments:
     • deployment_name: my-application
     • namespace: production
     • image: myorg/my-application:v1.0.0-prod
     • replicas: 2
     • strategy: RollingUpdate
     • max_unavailable: 0
     • max_surge: 1
   
   What this does: Applies Kubernetes deployment manifest, creates/updates 
   deployment, performs rolling update with zero downtime

---

📍 Step 8: Verify pods are running
   Server: Kubernetes MCP
   Tool: get_pods
   Risk: LOW 🟢
   Duration: < 1 minute
   Dependencies: Step 7
   Arguments:
     • namespace: production
     • label_selector: app=my-application
     • field_selector: status.phase=Running
   
   What this does: Lists pods, checks if all replicas are running, 
   verifies pod health

---

📍 Step 9: Check application health
   Server: Kubernetes MCP
   Tool: get_pod_logs
   Risk: LOW 🟢
   Duration: 1-2 minutes
   Dependencies: Step 8
   Arguments:
     • namespace: production
     • pod_selector: app=my-application
     • tail_lines: 100
     • check_errors: true
   
   What this does: Retrieves recent logs, checks for errors, validates 
   application started successfully

---

📍 Step 10: Monitor service endpoint
   Server: Kubernetes MCP
   Tool: get_service
   Risk: LOW 🟢
   Duration: < 1 minute
   Dependencies: Step 9
   Arguments:
     • service_name: my-application-service
     • namespace: production
     • verify_endpoints: true
   
   What this does: Verifies service is accessible, checks endpoint 
   configuration, validates traffic routing

================================================================================
Would you like to proceed with this plan? (yes/no)
================================================================================

💡 To execute this plan, use the 'execute_approved_plan' tool with approval=true
💡 To cancel this plan, use the 'cancel_pending_plan' tool
💡 To review again, use the 'show_pending_plan' tool
```

---

## ⚡ Step 6: Execution Flow (After Approval)

```python
User: execute_approved_plan(approval=true)

🚀 Starting execution of plan: plan_deploy_production_1737354243
📊 Total steps: 10

▶️  Executing Step 1: Build application code
    [Jenkins MCP] Triggering build job: production-build-pipeline
    [Jenkins MCP] Build started: #142
    [Jenkins MCP] Compiling source code...
    [Jenkins MCP] Resolving dependencies...
    [Jenkins MCP] Creating artifacts...
    ✅ Step 1 completed in 3.24s
    Output: {"build_number": 142, "status": "SUCCESS", "artifacts": 5}

▶️  Executing Step 2: Run automated test suite
    [Jenkins MCP] Running test suite: all
    [Jenkins MCP] Unit tests: 145/145 passed
    [Jenkins MCP] Integration tests: 32/32 passed
    [Jenkins MCP] Code coverage: 87% (target: 80%)
    ✅ Step 2 completed in 5.89s
    Output: {"tests_passed": 177, "tests_failed": 0, "coverage": "87%"}

▶️  Executing Step 3: Code quality analysis
    [SonarQube MCP] Analyzing project: my-application
    [SonarQube MCP] Scanning 1,234 files...
    [SonarQube MCP] Quality gate: PASSED ✓
    [SonarQube MCP] Bugs: 0, Vulnerabilities: 0, Code Smells: 12
    ✅ Step 3 completed in 3.45s
    Output: {"quality_gate": "PASSED", "bugs": 0, "vulnerabilities": 0}

▶️  Executing Step 4: Security vulnerability scan
    [SonarQube MCP] Scanning for vulnerabilities...
    [SonarQube MCP] Checking 87 dependencies...
    [SonarQube MCP] No critical or high vulnerabilities found
    ✅ Step 4 completed in 2.67s
    Output: {"vulnerabilities": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 2}}

▶️  Executing Step 5: Build and push Docker image
    [Docker Hub MCP] Building image: myorg/my-application:v1.0.0-prod
    [Docker Hub MCP] Step 1/8: FROM node:18-alpine
    [Docker Hub MCP] Step 2/8: WORKDIR /app
    [Docker Hub MCP] Step 3/8: COPY package*.json ./
    [Docker Hub MCP] Step 4/8: RUN npm ci --production
    [Docker Hub MCP] Step 5/8: COPY . .
    [Docker Hub MCP] Step 6/8: EXPOSE 3000
    [Docker Hub MCP] Step 7/8: CMD ["node", "server.js"]
    [Docker Hub MCP] Successfully built image
    [Docker Hub MCP] Pushing to registry...
    [Docker Hub MCP] Push complete: sha256:a3f2b1...
    ✅ Step 5 completed in 4.12s
    Output: {"image": "myorg/my-application:v1.0.0-prod", "size": "156MB"}

▶️  Executing Step 6: Verify Docker image
    [Docker Hub MCP] Verifying image: myorg/my-application:v1.0.0-prod
    [Docker Hub MCP] Image found in registry ✓
    [Docker Hub MCP] Layers verified ✓
    [Docker Hub MCP] Signature valid ✓
    ✅ Step 6 completed in 0.89s
    Output: {"verified": true, "layers": 8, "signature": "valid"}

▶️  Executing Step 7: Deploy to Kubernetes
    [Kubernetes MCP] Applying deployment: my-application
    [Kubernetes MCP] Namespace: production
    [Kubernetes MCP] Creating deployment...
    [Kubernetes MCP] Waiting for rollout...
    [Kubernetes MCP] Rollout status: 1/2 pods ready
    [Kubernetes MCP] Rollout status: 2/2 pods ready
    [Kubernetes MCP] Deployment successful ✓
    ✅ Step 7 completed in 2.87s
    Output: {"deployment": "my-application", "replicas": "2/2", "status": "Ready"}

▶️  Executing Step 8: Verify pods are running
    [Kubernetes MCP] Listing pods in namespace: production
    [Kubernetes MCP] Found 2 pods matching app=my-application
    [Kubernetes MCP] Pod 1: my-application-7d9c4b8f-xk2p4 - Running ✓
    [Kubernetes MCP] Pod 2: my-application-7d9c4b8f-zm7q1 - Running ✓
    [Kubernetes MCP] All pods healthy ✓
    ✅ Step 8 completed in 0.45s
    Output: {"pods": 2, "running": 2, "healthy": 2}

▶️  Executing Step 9: Check application health
    [Kubernetes MCP] Retrieving logs from pods...
    [Kubernetes MCP] Pod 1 logs: Server started on port 3000 ✓
    [Kubernetes MCP] Pod 2 logs: Server started on port 3000 ✓
    [Kubernetes MCP] No errors detected ✓
    [Kubernetes MCP] Application healthy ✓
    ✅ Step 9 completed in 1.23s
    Output: {"errors": 0, "warnings": 0, "health": "healthy"}

▶️  Executing Step 10: Monitor service endpoint
    [Kubernetes MCP] Checking service: my-application-service
    [Kubernetes MCP] Service type: NodePort
    [Kubernetes MCP] External port: 30001
    [Kubernetes MCP] Endpoints: 2 ready
    [Kubernetes MCP] Service accessible ✓
    ✅ Step 10 completed in 0.34s
    Output: {"service": "my-application-service", "port": 30001, "endpoints": 2}

✅ Plan execution completed successfully!
⏱️  Total duration: 25.15s

================================================================================
📊 EXECUTION SUMMARY
================================================================================

Plan ID: plan_deploy_production_1737354243
Status: COMPLETED
Duration: 25.15s
Steps Completed: 10
Steps Failed: 0

--------------------------------------------------------------------------------
STEP RESULTS:
--------------------------------------------------------------------------------

✅ Step 1: Build application code
   Duration: 3.24s
   Output: Build #142 - SUCCESS - 5 artifacts created

✅ Step 2: Run automated test suite
   Duration: 5.89s
   Output: 177 tests passed, 0 failed - Coverage: 87%

✅ Step 3: Code quality analysis
   Duration: 3.45s
   Output: Quality Gate PASSED - 0 bugs, 0 vulnerabilities

✅ Step 4: Security vulnerability scan
   Duration: 2.67s
   Output: No critical/high vulnerabilities - 2 medium

✅ Step 5: Build and push Docker image
   Duration: 4.12s
   Output: Image pushed - myorg/my-application:v1.0.0-prod (156MB)

✅ Step 6: Verify Docker image
   Duration: 0.89s
   Output: Image verified - 8 layers, signature valid

✅ Step 7: Deploy to Kubernetes
   Duration: 2.87s
   Output: Deployment successful - 2/2 replicas ready

✅ Step 8: Verify pods are running
   Duration: 0.45s
   Output: All 2 pods running and healthy

✅ Step 9: Check application health
   Duration: 1.23s
   Output: Application healthy - No errors detected

✅ Step 10: Monitor service endpoint
   Duration: 0.34s
   Output: Service accessible - 2 endpoints ready on port 30001

================================================================================

🎉 Deployment to Kubernetes production completed successfully!

📊 Summary:
  • Build: SUCCESS (#142)
  • Tests: 177/177 passed (87% coverage)
  • Quality: PASSED (0 bugs, 0 vulnerabilities)
  • Security: No critical issues
  • Docker Image: myorg/my-application:v1.0.0-prod (156MB)
  • Kubernetes: 2/2 pods running
  • Service: Accessible on NodePort 30001
  • Total Time: 25.15 seconds

✅ All success criteria met!
```

---

## 🎯 Key Takeaways

### 1. **Automatic Tool Discovery**
OPS Bot scanned 4 MCPs and found 45 available tools without any manual configuration.

### 2. **Intelligent Pattern Matching**
Recognized "deploy to production" and applied the appropriate deployment pattern with 10 orchestrated steps.

### 3. **Cross-MCP Coordination**
Seamlessly coordinated tools across:
- Jenkins (build & test)
- SonarQube (quality & security)
- Docker Hub (containerization)
- Kubernetes (deployment & monitoring)

### 4. **Risk-Based Planning**
- Medium risk: Build, test, quality, security, Docker operations
- High risk: Kubernetes deployment (requires approval)
- Low risk: Verification and monitoring steps

### 5. **Built-in Safety**
- Quality gates prevent bad code from deploying
- Security scans block vulnerable code
- Approval required for production deployment
- Automatic rollback on failure
- Zero-downtime rolling updates

### 6. **Complete Observability**
- Real-time progress updates
- Detailed logs from each step
- Comprehensive execution summary
- Success/failure tracking

---

## 📈 Comparison

### Manual Approach (Without OPS Bot):
```
Time: 2-3 hours
Steps: 30+ manual actions
Errors: Common (human mistakes)
Coordination: Manual between teams
Documentation: Often incomplete
Rollback: Manual process
Compliance: Easy to miss checks
```

### OPS Bot Automated Approach:
```
Time: 25 seconds (99% faster)
Steps: 10 automated, orchestrated
Errors: Rare (automated validation)
Coordination: Automatic across MCPs
Documentation: Complete audit trail
Rollback: Automatic on failure
Compliance: Always enforced
```

---

## 🚀 How to Use This

### Create the Plan:
```python
create_intelligent_task_plan("Deploy the code to Kubernetes production")
```

### Review the Generated Plan:
```python
show_pending_plan()
```

### Execute After Approval:
```python
execute_approved_plan(approval=true)
```

### Or Cancel:
```python
cancel_pending_plan()
```

---

## 🔄 Failure Scenario & Backup Mechanism

### What If Step 7 (Kubernetes Deployment) Fails?

```python
▶️  Executing Step 7: Deploy to Kubernetes
    [Kubernetes MCP] Applying deployment: my-application
    [Kubernetes MCP] Namespace: production
    [Kubernetes MCP] Creating deployment...
    [Kubernetes MCP] Rollout status: 1/2 pods ready
    [Kubernetes MCP] Rollout status: 1/2 pods ready (waiting...)
    [Kubernetes MCP] Error: Pod my-application-7d9c4b8f-xk2p4 CrashLoopBackOff
    [Kubernetes MCP] Container failed to start: Error loading config
    ❌ Step 7 failed: Deployment health check failed
    Duration: 5.34s
    Error: Pod crash loop detected - Container startup failure

🚨 FAILURE DETECTED - Initiating automatic recovery...
```

---

## 🛡️ Automatic Backup & Rollback Mechanism

### Phase 1: Immediate Rollback

```
🔄 AUTOMATIC ROLLBACK INITIATED

Reason: Step 7 (Deploy to Kubernetes) failed
Failure Type: Pod CrashLoopBackOff
Root Cause: Container startup failure - Config file error

📊 Rollback Actions:

✅ Action 1: Stop new deployment
   [Kubernetes MCP] Scaling new deployment to 0 replicas
   Status: SUCCESS (0.5s)

✅ Action 2: Restore previous version
   [Kubernetes MCP] Rolling back to previous ReplicaSet
   [Kubernetes MCP] Previous version: my-application-6c8a3f2e
   [Kubernetes MCP] Scaling previous deployment to 2 replicas
   Status: SUCCESS (1.2s)

✅ Action 3: Verify rollback success
   [Kubernetes MCP] Checking pod status...
   [Kubernetes MCP] Pod 1: my-application-6c8a3f2e-abc12 - Running ✓
   [Kubernetes MCP] Pod 2: my-application-6c8a3f2e-def34 - Running ✓
   Status: SUCCESS (0.8s)

✅ Action 4: Verify service health
   [Kubernetes MCP] Service endpoints: 2/2 healthy
   [Kubernetes MCP] Previous version restored and stable
   Status: SUCCESS (0.4s)

✅ Action 5: Clean up failed resources
   [Kubernetes MCP] Removing failed ReplicaSet
   [Kubernetes MCP] Cleaning up failed pods
   Status: SUCCESS (0.6s)

✅ Action 6: Notify team
   [Notification] Slack: #deployments channel
   [Notification] Email: devops-team@company.com
   Message: "Deployment failed, automatically rolled back to previous version"
   Status: SUCCESS (0.3s)

Total Rollback Time: 3.8 seconds
System Status: STABLE (Previous version restored)

```

---

## 🔧 Phase 2: Root Cause Analysis

```
🔍 AUTOMATED ROOT CAUSE ANALYSIS

Failure Analysis:
├─ Failed Step: Step 7 (Deploy to Kubernetes)
├─ Error Type: CrashLoopBackOff
├─ Container Exit Code: 1
├─ Last Log Lines:
│   "Error: Cannot find module './config/production.json'"
│   "    at Function.Module._resolveFilename"
│   "    at Function.Module._load"
│   "Failed to load configuration file"
│
└─ Root Cause: Missing configuration file in Docker image

Affected Components:
✓ Code build: SUCCESSFUL
✓ Tests: PASSED
✓ Quality scan: PASSED
✓ Security scan: PASSED
✓ Docker image: BUILT & PUSHED
✗ Kubernetes deployment: FAILED (missing config file)

Recommendation:
📝 The build succeeded but the Docker image is missing the 
   'config/production.json' file. This needs to be added to the 
   repository and the pipeline re-run.

Next Steps:
1. Add config/production.json to repository
2. Commit and push to GitHub
3. OPS Bot will automatically re-trigger the full pipeline
```

---

## 🔄 Phase 3: Fix & Re-Deploy Workflow

### Step 1: Code Fix (Manual)

```bash
# Developer fixes the issue
$ echo '{"port": 3000, "env": "production"}' > config/production.json
$ git add config/production.json
$ git commit -m "fix: Add missing production config file"
$ git push origin main
```

### Step 2: Automatic Re-Trigger

```python
🔔 GITHUB WEBHOOK RECEIVED

Event: push
Branch: main
Commit: a7f3b2c "fix: Add missing production config file"
Author: john@company.com
Files Changed: 1 (config/production.json added)

🤖 OPS Bot Analysis:
├─ Detected: Configuration file added
├─ Previous deployment: FAILED (missing config)
├─ Action: Auto re-trigger deployment pipeline
└─ Confidence: HIGH (exact fix for previous failure)

📋 Creating new deployment plan...
```

### Step 3: Automatic Plan Re-Generation

```
📋 AUTO-GENERATED TASK PLAN: plan_deploy_production_1737354500

🎯 Task: Re-deploy code to production (Auto-triggered by git push)
⚡ Priority: HIGH
⚠️  Overall Risk: MEDIUM (Previous attempt learned from)
⏱️  Estimated Duration: 20-35 minutes
📊 Total Steps: 10 (same as before)

🔍 Changes Detected:
  • config/production.json ADDED
  • This fixes the previous deployment failure ✓

📜 Optimizations Applied:
  • Skipping redundant quality scans (code unchanged)
  • Fast-tracking build (only config changed)
  • Enhanced validation for config file presence
  • Extra monitoring on startup

🔄 Rollback Strategy:
  Previous stable version (6c8a3f2e) maintained as backup
  
EXECUTION STEPS (Optimized)

📍 Step 1: Incremental build
   Server: Jenkins MCP
   Tool: trigger_build
   Risk: LOW 🟢 (only config changed)
   Duration: 1-2 minutes
   Optimization: Cached dependencies, only rebuilding affected parts

📍 Step 2: Config validation tests
   Server: Jenkins MCP
   Tool: run_tests
   Risk: LOW 🟢
   Duration: 1-2 minutes
   Focus: Testing config file loading specifically

📍 Step 3: Quick quality check
   Server: SonarQube MCP
   Tool: analyze_project
   Risk: LOW 🟢
   Duration: 1-2 minutes
   Optimization: Incremental analysis (only new file)

📍 Step 4: Build Docker image (with config)
   Server: Docker Hub MCP
   Tool: push_image
   Risk: MEDIUM 🟡
   Duration: 2-3 minutes
   Verification: Ensures config/production.json is included

📍 Step 5: Verify image contains config
   Server: Docker Hub MCP
   Tool: verify_image
   Risk: LOW 🟢
   Duration: < 1 minute
   Extra Check: Validates config file exists in image layers

📍 Step 6: Deploy to Kubernetes (Retry)
   Server: Kubernetes MCP
   Tool: apply_deployment
   Risk: MEDIUM 🟡 (risk reduced due to targeted fix)
   Duration: 2-3 minutes
   Enhanced Monitoring: Extra checks on config file loading

📍 Step 7-10: Standard verification steps...

```

### Step 4: Successful Re-Deployment

```
🚀 Starting execution of plan: plan_deploy_production_1737354500
📊 Total steps: 10

▶️  Executing Step 1: Incremental build
    [Jenkins MCP] Build started: #143
    [Jenkins MCP] Using cached dependencies ✓
    [Jenkins MCP] New config file detected ✓
    [Jenkins MCP] Build complete
    ✅ Step 1 completed in 1.45s

▶️  Executing Step 2: Config validation tests
    [Jenkins MCP] Running config-specific tests
    [Jenkins MCP] Config loading test: PASSED ✓
    [Jenkins MCP] Config validation test: PASSED ✓
    ✅ Step 2 completed in 1.67s

▶️  Executing Step 3: Quick quality check
    [SonarQube MCP] Incremental analysis
    [SonarQube MCP] New file: config/production.json ✓
    [SonarQube MCP] No issues found
    ✅ Step 3 completed in 1.23s

▶️  Executing Step 4: Build Docker image
    [Docker Hub MCP] Building with config file
    [Docker Hub MCP] COPY config/production.json ./config/ ✓
    [Docker Hub MCP] Image built and pushed
    ✅ Step 4 completed in 2.89s

▶️  Executing Step 5: Verify image contains config
    [Docker Hub MCP] Checking image layers...
    [Docker Hub MCP] Found: config/production.json ✓
    [Docker Hub MCP] File size: 45 bytes ✓
    ✅ Step 5 completed in 0.56s

▶️  Executing Step 6: Deploy to Kubernetes
    [Kubernetes MCP] Applying deployment with new image
    [Kubernetes MCP] Rollout started...
    [Kubernetes MCP] Pod 1 starting... Config loaded ✓
    [Kubernetes MCP] Pod 2 starting... Config loaded ✓
    [Kubernetes MCP] Both pods running ✓
    ✅ Step 6 completed in 2.34s

▶️  Executing Step 7-10: Verification steps
    ... All successful ...

✅ Plan execution completed successfully!
⏱️  Total duration: 15.67s (faster due to optimizations)

🎉 DEPLOYMENT SUCCESSFUL - Second attempt successful!
   Previous failure resolved by adding config file.
```

---

## 📊 Complete Failure & Recovery Flow

### Visual Representation

```
┌─────────────────────────────────────────────────────────────────┐
│            FAILURE & RECOVERY WORKFLOW                           │
└─────────────────────────────────────────────────────────────────┘

ATTEMPT 1:
  START → Build → Test → Quality → Security → Docker → 
  Deploy ❌ FAILED (Missing config)
    │
    ├─ Automatic Rollback (3.8s)
    │   ├─ Stop new deployment ✓
    │   ├─ Restore previous version ✓
    │   ├─ Verify rollback ✓
    │   └─ Notify team ✓
    │
    └─ Root Cause Analysis
        ├─ Error: Missing config/production.json
        ├─ Recommendation: Add file and push
        └─ Waiting for fix...

DEVELOPER FIXES:
  $ git add config/production.json
  $ git commit -m "fix: Add missing config"
  $ git push origin main
    │
    └─ GitHub Webhook → OPS Bot

ATTEMPT 2 (Auto-triggered):
  START → Incremental Build → Config Tests → Quick Quality →
  Docker (with config) → Verify Config → Deploy ✓ SUCCESS
    │
    └─ All pods running, config loaded, service healthy ✓

RESULT: System recovered and deployed successfully!
```

---

## 🎯 Detailed Backup Mechanism

### 1. Pre-Deployment Backup

```python
Before Step 7 (Deploy to Kubernetes):

📦 Automatic Backup Actions:

✅ Backup 1: Current Kubernetes State
   [Kubernetes MCP] Exporting current deployment YAML
   [Kubernetes MCP] Saved: backup-my-app-20260120-110000.yaml
   Location: /backups/kubernetes/

✅ Backup 2: Current Image Tag
   Stored: my-application:v0.9.5-prod (previous version)
   ReplicaSet: my-application-6c8a3f2e (2/2 running)

✅ Backup 3: Service Configuration
   [Kubernetes MCP] Exporting service YAML
   [Kubernetes MCP] Saved: backup-my-app-svc-20260120-110000.yaml

✅ Backup 4: ConfigMaps & Secrets
   [Kubernetes MCP] Backing up configmaps
   [Kubernetes MCP] Backing up secrets (encrypted)
   Status: All backed up ✓

Backups Complete: 4 items backed up in 1.2 seconds
Rollback Ready: Can restore in < 5 seconds if deployment fails
```

### 2. During Deployment Failure

```python
📍 Step 7: Deploy to Kubernetes
    [Kubernetes MCP] Applying new deployment...
    [Kubernetes MCP] New ReplicaSet: my-application-7d9c4b8f
    [Kubernetes MCP] Pod 1 starting...
    [Kubernetes MCP] Pod 1: CrashLoopBackOff ❌
    [Kubernetes MCP] Error detected within 30 seconds
    
🚨 FAILURE THRESHOLD REACHED
    Criteria: Pod failed 3 restart attempts
    Action: Triggering automatic rollback

🔄 ROLLBACK SEQUENCE:

Step 1: Immediate Traffic Protection
├─ [Kubernetes MCP] Preventing traffic to failed pods
├─ [Kubernetes MCP] All traffic routed to old version
└─ Status: ✅ Users unaffected (zero downtime)

Step 2: Restore Previous Deployment
├─ [Kubernetes MCP] Loading backup: backup-my-app-20260120-110000.yaml
├─ [Kubernetes MCP] Applying previous deployment
├─ [Kubernetes MCP] ReplicaSet 6c8a3f2e scaled to 2/2
└─ Status: ✅ Previous version restored

Step 3: Cleanup Failed Deployment
├─ [Kubernetes MCP] Deleting failed ReplicaSet 7d9c4b8f
├─ [Kubernetes MCP] Removing failed pods
├─ [Kubernetes MCP] Cleanup complete
└─ Status: ✅ No orphaned resources

Step 4: Verify System Stability
├─ [Kubernetes MCP] All pods: 2/2 Running ✓
├─ [Kubernetes MCP] Service: Healthy ✓
├─ [Kubernetes MCP] Endpoints: 2 ready ✓
└─ Status: ✅ System stable on previous version

Step 5: Archive Failure Logs
├─ [Kubernetes MCP] Saving failed pod logs
├─ Location: /logs/failures/deploy-failure-20260120-110500.log
├─ Includes: Pod logs, events, describe output
└─ Status: ✅ Logs archived for analysis

Step 6: Notify Team
├─ [Notification] Slack: #deployments
├─ [Notification] Email: devops-team@company.com
├─ [Notification] PagerDuty: Incident created
├─ Message: "Deployment failed and rolled back. Config file missing."
└─ Status: ✅ Team notified

Rollback Complete: 3.8 seconds
System Status: STABLE (Previous version v0.9.5-prod)
User Impact: ZERO (No downtime)

```

---

## 🔧 Phase 3: Guided Fix & Re-Deploy

### OPS Bot Provides Fix Guidance

```
🛠️ AUTOMATED FIX RECOMMENDATIONS

Based on failure analysis, here's what needs to be fixed:

📝 Issue Identified:
   Error: "Cannot find module './config/production.json'"
   Location: src/app.js:line 15
   Severity: CRITICAL

💡 Recommended Fix:

1. Create the missing file:
   
   File: config/production.json
   Content:
   {
     "port": 3000,
     "environment": "production",
     "database": {
       "host": "prod-db.internal",
       "port": 5432
     },
     "logging": {
       "level": "info"
     }
   }

2. Update Dockerfile to include config:
   
   Add this line to Dockerfile.prod:
   COPY config/ ./config/

3. Commit and push:
   
   $ git add config/production.json Dockerfile.prod
   $ git commit -m "fix: Add missing production config file"
   $ git push origin main

🤖 Once you push, OPS Bot will automatically:
   ✅ Detect the commit
   ✅ Create a new optimized deployment plan
   ✅ Run the pipeline again
   ✅ Deploy with the fix
   ✅ Verify it works this time

Would you like me to create the fix for you? (yes/no)
```

---

## 🔄 Phase 4: Automatic Re-Trigger

### GitHub Webhook Integration

```python
📡 GITHUB WEBHOOK EVENT RECEIVED

Event Type: push
Repository: myorg/my-application
Branch: main
Commit: a7f3b2c
Message: "fix: Add missing production config file"
Author: john@company.com
Timestamp: 2026-01-20 11:06:00 UTC

Files Changed:
✅ config/production.json (ADDED) - 45 bytes
✅ Dockerfile.prod (MODIFIED) - Added COPY config/ line

🤖 OPS Bot Automatic Actions:

1. ✅ Detected: Fix for previous deployment failure
2. ✅ Validated: Config file now present
3. ✅ Analyzed: Changes match recommended fix
4. ✅ Confidence: HIGH (95%) this will resolve the issue
5. ✅ Action: Auto-triggering new deployment plan

📋 Creating optimized re-deployment plan...

📋 NEW INTELLIGENT TASK PLAN: plan_deploy_production_1737354600

🎯 Task: Deploy code to production (Auto-retry with fix)
⚡ Priority: HIGH  
⚠️  Overall Risk: LOW (Targeted fix applied)
⏱️  Estimated Duration: 15-20 minutes (Optimized)
📊 Total Steps: 10

🔍 Optimizations Applied:
  ✓ Incremental build (only config changed)
  ✓ Focused testing (config-related tests)
  ✓ Cached quality analysis
  ✓ Enhanced config validation
  ✓ Extra deployment monitoring

📜 Learnings from Previous Failure:
  ✓ Added config file presence check
  ✓ Docker image validation includes config verification
  ✓ Enhanced pod startup monitoring
  ✓ Faster failure detection (if it happens again)

🔄 Enhanced Rollback:
  Previous stable version (6c8a3f2e) still available
  This attempt uses same rollback mechanism as before
  Rollback time: < 5 seconds if needed

EXECUTION STEPS (Optimized for Re-Deploy)

📍 Step 1: Incremental build with config
   Server: Jenkins MCP
   Tool: trigger_build
   Risk: LOW 🟢
   Duration: 1-2 minutes
   NEW CHECK: Verify config/production.json exists in workspace ✓

📍 Step 2: Config-focused test suite
   Server: Jenkins MCP
   Tool: run_tests
   Risk: LOW 🟢
   Duration: 2-3 minutes
   NEW TESTS: Config loading, Config validation

📍 Step 3: Skip quality scan (code unchanged)
   Optimization: Reusing previous scan results
   Quality Gate: PASSED (from previous attempt)
   Security: NO NEW VULNERABILITIES (from previous attempt)

📍 Step 4: Build Docker image with config
   Server: Docker Hub MCP
   Tool: push_image
   Risk: MEDIUM 🟡
   Duration: 2-3 minutes
   NEW VALIDATION: Confirms COPY config/ command executed
   Tag: v1.0.1-prod (incremented)

📍 Step 5: Enhanced image verification
   Server: Docker Hub MCP
   Tool: verify_image
   Risk: LOW 🟢
   Duration: < 1 minute
   NEW CHECK: Confirms config/production.json present in layers ✓

📍 Step 6: Deploy to Kubernetes (with confidence)
   Server: Kubernetes MCP
   Tool: apply_deployment
   Risk: LOW 🟢 (confidence increased with fix)
   Duration: 2-3 minutes
   ENHANCED: Extra monitoring on container startup

📍 Step 7: Verify pods with config check
   Server: Kubernetes MCP
   Tool: get_pods
   Risk: LOW 🟢
   Duration: < 1 minute
   NEW CHECK: Verifies pods loaded config successfully

📍 Step 8-10: Standard health checks...

```

---

## ✅ Phase 5: Successful Re-Deployment

```
🚀 Starting execution of plan: plan_deploy_production_1737354600

▶️  Step 1: Incremental build with config
    [Jenkins MCP] Build #143 started
    [Jenkins MCP] Config file found: ✓
    [Jenkins MCP] Build successful
    ✅ Completed in 1.45s

▶️  Step 2: Config-focused tests
    [Jenkins MCP] Config loading test: PASSED ✓
    [Jenkins MCP] Config validation test: PASSED ✓
    ✅ Completed in 2.12s

▶️  Step 3: Quality check (optimized)
    [SonarQube MCP] Using cached results
    [SonarQube MCP] New file validated ✓
    ✅ Completed in 0.78s

▶️  Step 4: Build Docker image
    [Docker Hub MCP] Building v1.0.1-prod
    [Docker Hub MCP] COPY config/ executed ✓
    [Docker Hub MCP] Config file present in image ✓
    ✅ Completed in 2.67s

▶️  Step 5: Enhanced image verification
    [Docker Hub MCP] Verifying layers...
    [Docker Hub MCP] Layer 5: config/production.json FOUND ✓
    [Docker Hub MCP] Image verified ✓
    ✅ Completed in 0.45s

▶️  Step 6: Deploy to Kubernetes
    [Kubernetes MCP] Deploying v1.0.1-prod
    [Kubernetes MCP] Pod 1 starting...
    [Kubernetes MCP] Pod 1: Config loaded successfully ✓
    [Kubernetes MCP] Pod 1: Server started on port 3000 ✓
    [Kubernetes MCP] Pod 2 starting...
    [Kubernetes MCP] Pod 2: Config loaded successfully ✓
    [Kubernetes MCP] Pod 2: Server started on port 3000 ✓
    [Kubernetes MCP] Deployment successful! ✓
    ✅ Completed in 2.98s

▶️  Step 7-10: All verification steps
    ✅ All successful

✅ Re-deployment completed successfully!
⏱️  Total duration: 15.67s

🎉 DEPLOYMENT RECOVERED & SUCCESSFUL!

Deployment History:
├─ Attempt 1: FAILED (Missing config) → Rolled back in 3.8s
├─ Developer Fix: Added config file (30 seconds)
└─ Attempt 2: SUCCESS (Fix applied) → Deployed in 15.67s

Total Recovery Time: 50 seconds (from failure to success)
User Impact: ZERO (No downtime during entire process)

📊 Final Status:
  • Build: #143 - SUCCESS
  • Tests: ALL PASSED (including new config tests)
  • Quality: PASSED
  • Security: NO VULNERABILITIES
  • Docker Image: myorg/my-application:v1.0.1-prod
  • Kubernetes: 2/2 pods running with config loaded
  • Service: Accessible on NodePort 30001
  • Config File: Present and validated ✓

Lessons Learned:
  ✓ Config files must be in repo before deployment
  ✓ Dockerfile must COPY all required configs
  ✓ OPS Bot detected, rolled back, and recovered automatically
  ✓ Fix applied in < 1 minute, re-deployed successfully
  ✓ Zero user impact throughout entire process

```

---

## 🎯 Key Takeaways from Backup & Recovery

### 1. **Automatic Rollback** (3.8 seconds)
- Detected failure instantly
- Rolled back to previous stable version
- Zero user downtime
- Complete cleanup of failed resources

### 2. **Root Cause Analysis** (Automatic)
- Analyzed logs and errors
- Identified exact issue
- Provided specific fix recommendations
- Saved team hours of debugging

### 3. **GitHub Integration** (Automatic)
- Webhook triggers new pipeline
- Detects fix-related commits
- Auto-creates optimized re-deploy plan
- No manual intervention needed

### 4. **Intelligent Retry** (Optimized)
- Incremental build (faster)
- Focused testing (config-specific)
- Enhanced validation (config presence)
- Risk reduced (confident fix)

### 5. **Complete Recovery** (50 seconds total)
- Failure detected: 5s
- Rollback: 3.8s
- Developer fix: 30s
- Re-deploy: 15.67s
- Total: 54.47s from failure to success

### 6. **Zero User Impact**
- Old version kept running during fix
- Traffic never interrupted
- No data loss
- No service disruption

---

## 🎉 Summary

This example demonstrates OPS Bot's **complete failure recovery workflow**:

✅ **Discovered** 45 tools across 4 MCPs automatically
✅ **Created** 10-step optimized deployment plan
✅ **Coordinated** Jenkins → SonarQube → Docker → Kubernetes
✅ **Detected** failure instantly (CrashLoopBackOff)
✅ **Rolled back** automatically in 3.8 seconds
✅ **Analyzed** root cause and provided fix
✅ **Detected** GitHub push with fix
✅ **Re-triggered** optimized pipeline automatically
✅ **Deployed** successfully on second attempt
✅ **Completed** full recovery in 50 seconds
✅ **Achieved** zero user downtime throughout

**From failure to recovery to success - all automated!** 🎯

---

## 💡 What This Means

### Without OPS Bot:
```
Failure Detection: 10-15 minutes (manual monitoring)
Rollback: 20-30 minutes (manual process)
Root Cause: 1-2 hours (debugging)
Fix: 30 minutes (developer time)
Re-deploy: 30 minutes (manual pipeline)
Total: 3-4 hours + potential downtime
```

### With OPS Bot:
```
Failure Detection: 5 seconds (automatic)
Rollback: 3.8 seconds (automatic)
Root Cause: 2 seconds (AI analysis)
Fix: 30 seconds (developer time)
Re-deploy: 15.67 seconds (automatic optimized)
Total: 56.47 seconds + ZERO downtime
```

**Result: 300x faster recovery with zero user impact!** 🚀
