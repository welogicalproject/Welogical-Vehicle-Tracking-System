# Repository Maintenance & Release Checklist

This document serves as the permanent checklist for maintaining codebase quality, security, and documentation standards in the Vehicle Tracking System (VTS) repository.

---

## 1. Before Every Push
- [ ] **Build Check:** Verify that the FastAPI backend starts without syntax or import errors, and the Next.js dashboard compiles successfully (`npm run build`).
- [ ] **Telemetry Test:** Run the `telemetry_simulator.py` script locally to confirm that telemetry packages are parsed and recorded.
- [ ] **Git Check:** Run `git status` to verify that no untracked `.env` files, build directories (`node_modules`, `.next`), or local logs are staged.
- [ ] **Environment Check:** Verify that any new variables introduced in the code are documented in `.env.example`.
- [ ] **Secrets Check:** Verify that no credentials, passwords, or API keys are committed in cleartext.

---

## 2. Before Every Release
- [ ] **Changelog:** Update `CHANGELOG.md` following the *Keep a Changelog* format, capturing all changes under the new version header.
- [ ] **Readme Review:** Verify that installation steps in `README.md` and `docs/LOCAL_SETUP.md` are aligned with any dependency upgrades.
- [ ] **API Reference:** Update `docs/API_REFERENCE.md` if any endpoint routes, parameters, or response structures have changed.
- [ ] **Database Schema:** Generate and verify Alembic migrations if SQLAlchemy models were modified, and update `docs/DATABASE.md` to reflect schema additions.
- [ ] **Version Numbers:** Update version fields in `app/main.py` and `dashboard/package.json`.

---

## 3. Security Checklist
- [ ] **No Committed Keys:** Verify that no private SSL/TLS certificates, SSH keys, or cloud platform API keys are in the codebase.
- [ ] **Dependency Audit:** Audit Python (`requirements.txt`) and Node.js (`package.json`) dependencies for known security vulnerabilities.
- [ ] **No Local Secrets:** Ensure all `.env` files are ignored by git in the root and in the frontend subfolders.

---

## 4. Repository Quality Checklist
- [ ] **Link Verification:** Ensure all relative Markdown links (`docs/` and `internal/`) resolve correctly.
- [ ] **Diagrams:** Confirm that all Mermaid diagrams render without syntax errors.
- [ ] **Structure Integrity:** Keep the repository root clean. Technical guides must live in `docs/` and audit logs in `internal/`.
- [ ] **Cache Clearance:** Ensure no `__pycache__` or compilation logs are present.

---

## 5. Deployment Checklist
- [ ] **Migration Check:** Confirm that `alembic upgrade head` executes cleanly against a clean target database.
- [ ] **Environment Setup:** Verify all required production variables are configured in the cloud host platform environment.
- [ ] **Connection Checks:** Confirm database pool configurations and query timeouts are optimized for the target load.
- [ ] **Database Backups:** Confirm the persistent storage backup and disaster recovery policy is active.

---

## 6. Handover Checklist
- [ ] **Onboarding Guides:** Ensure `docs/LOCAL_SETUP.md` and `docs/DEVELOPER_GUIDE.md` allow a new developer to configure the project independently.
- [ ] **System Architecture:** Confirm that `docs/ARCHITECTURE.md` accurately describes the current components and telemetry flows.
- [ ] **Database Schema:** Confirm `docs/DATABASE.md` includes the correct ER diagram mapping and column definitions.
- [ ] **Handover Package:** Confirm `HANDOVER.md` is complete and serves as an accurate status report for the team.
