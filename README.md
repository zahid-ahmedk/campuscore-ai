# CampusCore AI Management System (v2.0)

An AI-integrated Student Information, Batch Fee Reconciliation, and Predictive Academic Risk Management System built for **QUEST Nawabshah (Department of Information Technology)**.

## Core Architecture & Features
* **Role-Based Access Control (RBAC):** Dedicated portals for **Admin**, **Chairman**, **Clerk**, and **Student**.
* **ML Early-Warning Risk Predictor (scikit-learn):** Random Forest model evaluating attendance, midterm/sessional scores, and fee clearance to flag at-risk students early.
* **Batch-Wise Fee Reconciliation:** Real-time filtering by student batch with Paid, Partial, and Pending tracking.
* **AI Study Advisor & Admin Copilot:** Generates personalized recovery plans for students and answers natural-language institutional queries for administrators.

## Quick Start (Windows)
1. Install backend dependencies: pip install -r backend/requirements.txt
2. Seed the local SQLite database: python backend/seed.py and move campuscore.db into ackend/
3. Install frontend packages: cd frontend && npm install
4. Run backend (cd backend && uvicorn main:app --reload) and frontend (cd frontend && npm run dev).

## Demo Credentials
| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | dmin@campuscore.edu | dmin123 |
| **Chairman** | chairman@campuscore.edu | chair123 |
| **Clerk** | clerk@campuscore.edu | clerk123 |
| **Student** | 21it95@student.campuscore.edu | student123 |
