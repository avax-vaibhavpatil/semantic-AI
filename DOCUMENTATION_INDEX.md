# Documentation Index

Welcome to the Auto Semantic Project documentation! This index helps you find the right documentation for your needs.

## 🚀 Getting Started

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [QUICKSTART.md](QUICKSTART.md) | Get up and running in 5 minutes | First time setup |
| [README.md](README.md) | Complete project documentation | Understanding the project |

## 📚 Detailed Guides

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md) | Learn how to create and customize semantic layers | Setting up your data model |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guidelines for contributing code | Want to contribute |

## 🚀 Production Readiness Guides

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [PRODUCTION_READINESS_GUIDE.md](PRODUCTION_READINESS_GUIDE.md) | **Beginner-friendly guide** to making project production-ready | Understanding what needs to be fixed and why |
| [CRITICAL_ISSUES_SUMMARY.md](CRITICAL_ISSUES_SUMMARY.md) | Quick reference of critical issues | Quick overview of problems |
| [ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md) | Visual before/after architecture comparison | Understanding the refactoring visually |
| [PRODUCTION_REFACTORING_PLAN.md](PRODUCTION_REFACTORING_PLAN.md) | Technical refactoring plan with detailed steps | Planning the refactoring |
| [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) | Quick summary of refactoring plan | Quick overview of refactoring |

## 📋 Quick Reference

### For First-Time Users
1. Start with [QUICKSTART.md](QUICKSTART.md)
2. Follow the 3-step setup
3. Test with example queries
4. Read [README.md](README.md) for deeper understanding

### For Data Teams
1. Read [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md)
2. Understand column types and derived measures
3. Create your semantic layer JSON
4. Test with your database

### For Developers
1. Read [README.md](README.md) - Architecture section
2. Review [CONTRIBUTING.md](CONTRIBUTING.md)
3. Check project structure
4. Set up development environment

### For Making It Production-Ready
1. **Start here**: [PRODUCTION_READINESS_GUIDE.md](PRODUCTION_READINESS_GUIDE.md) - Complete beginner-friendly guide
2. **Quick overview**: [CRITICAL_ISSUES_SUMMARY.md](CRITICAL_ISSUES_SUMMARY.md) - Top issues at a glance
3. **Visual understanding**: [ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md) - See before/after
4. **Technical details**: [PRODUCTION_REFACTORING_PLAN.md](PRODUCTION_REFACTORING_PLAN.md) - Detailed plan

## 📁 Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `.env` | `backend/.env` | Environment variables (API keys, database) |
| `semantic.json` | `backend/metadata/semantic.json` | Semantic layer definition |
| `semantic.json.example` | `backend/metadata/semantic.json.example` | Example semantic layer |

## 🛠️ Helper Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `start_backend.sh` | `backend/start_backend.sh` | Start backend server |
| `start_frontend.sh` | `frontend/start_frontend.sh` | Start frontend server |
| `Makefile` | Root directory | Automated tasks |

## 📖 Documentation Sections

### Quick Start Guide
**File:** [QUICKSTART.md](QUICKSTART.md)
- Prerequisites checklist
- 3-step installation
- Running the project
- Testing and verification
- Troubleshooting basics

### Main README
**File:** [README.md](README.md)
- Project overview and architecture
- Detailed installation instructions
- Configuration guide
- API documentation
- Comprehensive troubleshooting
- Security notes

### Semantic Layer Guide
**File:** [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md)
- What is a semantic layer
- Column types (dimensions, measures, dates)
- Derived measures and calculations
- Quality rules
- Complete examples
- Best practices
- Auto-generation from DBT

### Contributing Guide
**File:** [CONTRIBUTING.md](CONTRIBUTING.md)
- Development setup
- Code style guidelines
- Pull request process
- Areas for contribution
- Testing guidelines

## 🎯 Common Tasks

### I want to...

**...get started quickly**
→ Read [QUICKSTART.md](QUICKSTART.md)

**...understand how it works**
→ Read [README.md](README.md) Architecture section

**...set up my database schema**
→ Read [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md)

**...add a new feature**
→ Read [CONTRIBUTING.md](CONTRIBUTING.md)

**...make it production-ready**
→ Read [PRODUCTION_READINESS_GUIDE.md](PRODUCTION_READINESS_GUIDE.md) (start here!)
→ Quick reference: [CRITICAL_ISSUES_SUMMARY.md](CRITICAL_ISSUES_SUMMARY.md)

**...understand current issues**
→ Read [CRITICAL_ISSUES_SUMMARY.md](CRITICAL_ISSUES_SUMMARY.md)
→ See visual comparison: [ARCHITECTURE_COMPARISON.md](ARCHITECTURE_COMPARISON.md)

**...troubleshoot an issue**
→ Check [README.md](README.md) Troubleshooting section

**...run the project**
→ Use scripts in [QUICKSTART.md](QUICKSTART.md) or Makefile commands

**...customize SQL generation**
→ Edit `backend/prompts.py` (see [README.md](README.md))

**...add more tables**
→ Update `backend/metadata/semantic.json` (see [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md))

## 🔍 Key Concepts

### Semantic Layer
A JSON file that defines what data is accessible and how it should be interpreted.
- See: [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md)

### Dimensions vs Measures
- **Dimensions**: Categories for grouping (e.g., customer_name, region)
- **Measures**: Numbers for aggregation (e.g., amount, quantity)
- See: [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md) - Column Types

### Derived Measures
Calculated metrics using SQL expressions (e.g., ratios, averages).
- See: [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md) - Derived Measures

### SQL Validation
Safety checks to ensure only authorized queries run.
- See: [README.md](README.md) - Security Notes

## 📞 Getting Help

1. **Quick issues**: Check [QUICKSTART.md](QUICKSTART.md) Troubleshooting
2. **Detailed issues**: Check [README.md](README.md) Troubleshooting
3. **Semantic layer issues**: Check [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md) Troubleshooting
4. **Still stuck**: Open a GitHub issue

## 🔄 Update History

This documentation was created to help you understand and use the Auto Semantic Project effectively. If you find any gaps or have suggestions, please contribute!

---

**Start here:** [QUICKSTART.md](QUICKSTART.md) → [README.md](README.md) → [SEMANTIC_LAYER_GUIDE.md](SEMANTIC_LAYER_GUIDE.md)

**Making it production-ready?** Start with [PRODUCTION_READINESS_GUIDE.md](PRODUCTION_READINESS_GUIDE.md)



