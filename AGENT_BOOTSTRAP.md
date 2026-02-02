# Agent Thread Recovery - Bootstrap Guide

## 🚀 Quick Start for New Thread

When starting a new thread, immediately run:

```bash
./thread_restart.sh --update --session-id "your_session_name"
```

This will:
1. Read current status from `AGENT_STATUS.yaml`
2. Check git state and recent commits
3. Display next immediate steps
4. Update timestamps and create session log
5. Generate quick reference in `.agent/quick_ref.txt`

## 📁 File Structure

### Core Tracking Files
- **`AGENT_STATUS.yaml`** - Primary status tracking (committed to git)
  - Current task, progress, blockers, next steps
  - Git commit history and project metrics
  - Performance benchmarks and automation status

- **`thread_restart.sh`** - Thread restart protocol script
  - Prepares context for new agent sessions
  - Creates session logs and quick references
  - Detects blockers and uncommitted changes

### Runtime Artifacts (not committed)
- **`.agent/session_logs/`** - Timestamped session logs
- **`.agent/quick_ref.txt`** - Current quick reference
- **`AGENT_STATUS.yaml.backup.*`** - Auto-backups

## 🔄 Thread Restart Protocol

### Standard Workflow
1. **Read Status**: `./thread_restart.sh` (shows current state)
2. **Update & Start**: `./thread_restart.sh --update --session-id "session_$(date +%Y%m%d_%H%M%S)"`
3. **Review Output**: Check "AGENT THREAD RESTART - READY FOR NEXT SESSION" section
4. **Execute Next**: Follow immediate next steps from output

### What the Script Provides
- ✅ Project context (goal, phase, progress)
- ✅ Git status (branch, last commit, changes)
- ✅ Current task and status
- ✅ Blockers (if any)
- ✅ Next immediate steps (1h horizon)
- ✅ Session log location

## 📊 Understanding AGENT_STATUS.yaml

### Key Sections
```yaml
metadata:          # Project and agent info
git_status:        # Git repository state  
current_work:      # Active task and subtasks
project_status:    # Exchange integration progress
next_steps:        # Immediate and short-term actions
performance_metrics: # Efficiency benchmarks
commit_recommendations: # Suggested next commits
```

### Status Values
- `completed`: Task finished successfully
- `in_progress`: Actively working on task
- `blocked`: Blocked (needs investigation/fix)
- `pending`: Not yet started

## 🛠️ Agent Workflow

### Typical Session Flow
```
1. Thread Restart → 2. Review Status → 3. Execute Next Step → 4. Commit Progress → 5. Update Status
```

### Exchange Integration Pattern
```bash
# 1. Setup new exchange (automated)
python3 add_exchange.py --name exchange_name \
  --base-url BASE_URL --ws-url WS_URL \
  --docs DOCS_URL --product-endpoint ENDPOINT

# 2. Implement adapter logic
#    - Edit src/adapters/{exchange}_adapter.py
#    - Test: python3 main.py discover --vendor {exchange}

# 3. Create field mappings
python3 src/scripts/create_{exchange}_mappings.py --dry-run
python3 src/scripts/create_{exchange}_mappings.py

# 4. Test coverage
python3 src/scripts/test_exchange_coverage.py {exchange}

# 5. Update tracking
#    - Update AI-EXCHANGE-TODO-LIST.txt
#    - Update AGENT_STATUS.yaml
#    - Git commit with semantic message
```

## 📝 Essential Commands Reference

### Status & Context
```bash
# Quick status check
./thread_restart.sh

# Start new session with updates
./thread_restart.sh --update --session-id "session_$(date +%Y%m%d_%H%M%S)"

# View quick reference
cat .agent/quick_ref.txt

# View latest session log
ls -lt .agent/session_logs/ | head -5
```

### Project Operations
```bash
# Discover exchange API
python3 main.py discover --vendor {exchange_name}

# Export specification
python3 main.py export --vendor {exchange_name} --format snake_case

# Query database
python3 main.py query "SELECT COUNT(*) FROM products WHERE vendor_id = ..."

# List all vendors
python3 main.py list-vendors
```

### Git Operations
```bash
# Check status
git status

# View recent commits
git log --oneline -10

# Commit with semantic message
git commit -m "type(scope): description

- Bullet point 1
- Bullet point 2
- Bullet point 3"

# Push to remote
git push origin main
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Thread Restart Shows Old Next Steps
```bash
# Update AGENT_STATUS.yaml with current state
# Check YAML formatting for next_steps section
# Ensure no duplicate immediate_1h entries
```

#### Git Shows Uncommitted Changes
```bash
# Review changes
git status --porcelain

# Decide: commit or stash
git add . && git commit -m "..."   # OR
git stash                          # Temporary save
```

#### Blocked Status Persists
1. **Verify locally**: Test API endpoints with `curl`
2. **Check documentation**: Review exchange API docs
3. **Alternative approaches**: Try different endpoints/parameters
4. **Document findings**: Update AGENT_STATUS.yaml blockers section

#### Automation Script Issues
```bash
# Test add_exchange.py with dry run
python3 add_exchange.py --name test --base-url http://test.com \
  --ws-url ws://test.com --docs http://docs.test.com \
  --product-endpoint /api/products --dry-run

# Check script permissions
chmod +x add_exchange.py thread_restart.sh
```

## 🔮 Future Enhancements (Planned)

### SQLite Context Database
```
.agent/agent_context.db
├── agent_sessions
├── exchange_integrations  
├── git_commits
└── performance_metrics
```

### Benefits
- **Structured querying**: `SELECT * FROM exchange_integrations WHERE status = 'completed'`
- **Cross-session analytics**: Performance trends over time
- **Predictive estimation**: Time-to-completion based on history
- **Knowledge retention**: Learnings from previous integrations

### Implementation Notes
- Will maintain backward compatibility with YAML
- AGENT_STATUS.yaml will remain as human-readable summary
- SQLite will provide detailed historical analytics

## ✅ Success Criteria

A successful thread restart means you can answer:

1. **What's the project goal?** → Expand from 11 to 25 exchanges
2. **Current progress?** → X/25 exchanges complete (check AGENT_STATUS.yaml)
3. **What am I working on?** → Current task from status
4. **What's next?** → Immediate next steps from output
5. **Any blockers?** → Check blockers section

## 📞 Quick Reference Creation

After thread restart, always check:
```bash
cat .agent/quick_ref.txt
```

This file contains the minimal context needed to continue work.

---

**Last Updated**: See `AGENT_STATUS.yaml` → `metadata.last_updated`
**System Version**: 1.0.0 (YAML-based with script automation)
**Next Enhancement**: SQLite context database for advanced analytics

---
*Remember: Always run `./thread_restart.sh --update` at thread start, and commit progress regularly.*