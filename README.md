# Alina J Talent Connect (CRM)

## Overview

**Alina J Talent Connect** is a custom Customer Relationship Management (CRM) system designed for an influencer marketing agency. The platform centralizes operational data, streamlines workflows, and improves visibility across talent, contracts, campaigns, and brand partnerships. It is intended to serve as a single source of truth that supports scalability and data-driven decision-making.

## Objectives

- Centralize talent, brand, and contract data
- Streamline influencer and brand relationship workflows
- Improve operational visibility and reporting
- Enable performance tracking and KPI-driven insights
- Support future AI- and API-driven enhancements

## Core Features

### Data Management

The system provides full CRUD (Create, Read, Update, Delete) capabilities for the following entities:

- Roles
- Persons
- Users
- Talent Managers
- Influencers
- Social Media Accounts
- Brands
- Brand Representatives
- Deals / Campaigns
- Contracts

### User Access & Security

- Role-based user accounts for:
  - Guests / site visitors
  - Employees
  - Clients
- Granular permission levels to control data access and actions
- Encrypted password storage

### Dashboards & Analytics

- Customizable dashboards
- KPI tracking and performance measurement
- Sales forecasting and trend analysis

### Navigation & Usability

- Seamless navigation across pages and modules
- Nested tabs and contextual hyperlinks for quick access to related records

### Relationship Tracking

- Centralized logging of interactions across channels (email, phone, social media)
- 360-degree view of influencers, brands, and partnerships

## Data Model

### Roles

| Field | Type | Description |
|------|------|-------------|
| Role_ID (PK) | Int | Unique user identifier |
| Role_name | String | Name of the role |

### Persons

| Field | Type | Description |
|------|------|-------------|
| Person_ID (PK) | Int | Unique person identifier |
| First_Name | String | First name |
| Last_Name | String | Last name |
| Full_Name | String | Full legal name |
| Display_Name | String | Preferred display name |
| Email | String | Work email address |
| Phone | String | Work phone number (XXX-XXX-XXXX) |
| Address | String | Street address |
| City | String | City |
| State | String | State |
| Zip | String | ZIP code |

### Users

| Field | Type | Description |
|------|------|-------------|
| User_ID (PK) | Int | Unique user identifier |
| Username | String | Login username |
| Password | String (encrypted) | Login password |
| Role_ID | Int | Associated role identifier |
| Person_ID | Int | Associated person record |

### Talent Managers

| Field | Type | Description |
|------|------|-------------|
| Talent_Manager_ID (PK) | Int | Unique talent manager identifier |
| Person_ID (FK) | Int | Reference to Persons |
| Position | String | Organizational position |
| Title | String | Job title |
| Manager_ID (FK) | Int | Reporting manager (Person) |
| Start_Date | Date | Hire date |
| End_Date | Date | Termination date (if applicable) |
| Is_Active | Boolean | Active employment status |

### Influencers

| Field | Type | Description |
|------|------|-------------|
| Influencer_ID (PK) | Int | Unique influencer identifier |
| Talent_Manager_ID (FK) | Int | Associated talent manager |
| Description | String | Influencer profile description |

### Social Media Accounts

| Field | Type | Description |
|------|------|-------------|
| Social_Media_ID (PK) | Int | Unique account identifier |
| Influencer_ID (FK) | Int | Associated influencer |
| Type | Enum | Platform (Instagram, YouTube, Facebook, etc.) |
| Link | String | Profile URL |

### Brands

| Field | Type | Description |
|------|------|-------------|
| Brand_ID (PK) | Int | Unique brand identifier |
| Description | String | Brand description |

### Brand Representatives

| Field | Type | Description |
|------|------|-------------|
| Brand_Representative_ID (PK) | Int | Unique representative identifier |
| Person_ID (FK) | Int | Associated person |
| Brand_ID (FK) | Int | Associated brand |
| Notes | String | Additional relevant notes |
| Is_Active | Boolean | Active status |

### Deals / Campaigns

| Field | Type | Description |
|------|------|-------------|
| Deal_ID (PK) | Int | Unique deal identifier |
| Influencer_ID (FK) | Int | Associated influencer |
| Brand_ID (FK) | Int | Associated brand |
| Brand_Representative_ID (FK) | Int | Brand contact |
| Pitch_Date | Date | Date pitched |
| Is_Active | Boolean | Active deal status |
| Is_Successful | Boolean | Outcome indicator |

### Contracts

| Field | Type | Description |
|------|------|-------------|
| Contract_ID (PK) | Int | Unique contract identifier |
| Deal_ID (FK) | Int | Associated deal |
| Details | String | Contract terms and conditions |
| Payment | Float | Total payment amount |
| Agency_Percentage | Float | Agency revenue percentage |
| Start_Date | Date | Contract start date |
| End_Date | Date | Contract end date |
| Status | Enum | Workflow state (Sent, Pending, Accepted, Rejected, etc.) |
| Is_Approved | Boolean | Final approval status |

## Potential Enhancements

- **Social Media API Integrations**  
  Integration with Instagram, Facebook, and YouTube APIs to ingest performance metrics and market trends.

- **AI & Machine Learning**  
  Application of machine learning models for predictive analytics and performance insights.

- **LLM-Powered Contract Review**  
  Automated contract analysis to summarize key terms, flag risks, and generate counterproposal recommendations aligned with agency standards.

## Status

This repository represents the foundational design and planning phase of the Alina J Talent Connect CRM system. Implementation details, architecture, and deployment instructions will be added as development progresses.

