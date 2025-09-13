# KinAura Backend Architecture

## Overview

The KinAura backend is a production-grade healthcare platform built on Supabase, designed to support a regenerative wellness clinic with AI-powered treatment protocols, personalized skincare formulation, and comprehensive patient management.

## Technology Stack

- **Database**: PostgreSQL 15 with Row Level Security (RLS)
- **API**: Supabase Edge Functions (Deno/TypeScript)
- **Authentication**: Supabase Auth with JWT
- **Storage**: Supabase Storage with custom policies
- **Real-time**: Supabase Realtime for messaging
- **AI Integration**: Ready for external AI services
- **Observability**: Structured audit logs and metrics

## Architecture Principles

### Security First
- **Row Level Security (RLS)**: Every table has comprehensive RLS policies
- **Multi-tenant Architecture**: Organization-scoped data access
- **JWT Authentication**: Secure token-based auth with role-based permissions
- **Service Role Isolation**: Privileged operations use service role keys
- **GDPR Compliance**: Built-in consent management and data export/deletion

### Scalability & Performance
- **Postgres Optimizations**: Strategic indexes including GIN for JSONB
- **Edge Functions**: Serverless TypeScript functions for business logic
- **Efficient Queries**: Optimized for dashboard and patient lookups
- **Real-time Features**: WebSocket-based messaging and notifications

### Data Integrity
- **Strong Typing**: Zod validation on all Edge Function inputs
- **Foreign Key Constraints**: Referential integrity across all relations
- **Audit Trail**: Comprehensive logging of all sensitive operations
- **Soft Deletes**: GDPR-compliant deletion with retention policies

## Core Domains

### 1. Identity & Organizations (`profiles`, `organizations`, `clinicians`)
- Multi-tenant organization structure
- Role-based access control (admin, practitioner, member, guest)
- VIP tier system (standard, gold, platinum, elite)

### 2. Patient Management (`patients`, `patient_groups`, `patient_notes`)
- Comprehensive patient records with soft delete
- Tagging system for patient categorization
- Secure note-taking with visibility controls
- GDPR-compliant data handling

### 3. Clinical & AI (`protocols`, `protocol_sessions`, `analyses`, `longevity_scores`)
- AI-powered treatment protocol generation
- Session tracking and progress monitoring
- Multi-modal analysis storage (blood, hormonal, skin scans, etc.)
- Longevity scoring algorithm with community benchmarking

### 4. Commerce (`formulas`, `orders`)
- Personalized skincare formula creation
- Minimum €150 pricing enforcement
- Order lifecycle management
- Payment integration ready

### 5. Scheduling (`services`, `appointments`)
- Rich service catalog with categories
- Appointment booking with conflict detection
- VIP scheduling privileges
- Automated reminder system

### 6. Messaging (`threads`, `messages`, `segments`, `campaigns`)
- Patient-staff secure messaging
- Real-time message delivery
- Marketing campaign management
- Segmentation and targeting

### 7. Compliance (`audit_logs`, `consents`)
- Comprehensive audit trail
- GDPR consent management
- Data export and deletion capabilities

## Edge Functions API

### Authentication (`/auth`)
- `POST /invite-user` - Admin user invitation
- `POST /switch-org` - Multi-org access

### Patient Management (`/patients`)
- `GET /patients` - List patients with filtering
- `POST /patients` - Create new patient
- `GET /patients/{id}` - Get patient details
- `PUT /patients/{id}` - Update patient
- `DELETE /patients/{id}` - Soft delete patient
- `POST /patients/{id}/notes` - Add patient note
- `POST /patients/{id}/upload` - Generate upload URL

### Clinical (`/clinical`)
- `POST /ingest-analysis` - Store analysis results
- `POST /refresh-protocol` - AI protocol generation
- `POST /compare-prepost` - Image comparison analysis
- `POST /recompute-leaderboard` - Longevity score calculation

### Booking (`/booking`)
- `POST /available-slots` - Get available appointment slots
- `POST /book` - Book appointment
- `POST /reschedule` - Reschedule appointment
- `POST /cancel` - Cancel appointment

### Commerce (`/commerce`)
- `POST /create-formula` - Create skincare formula
- `POST /finalize-formula` - Finalize formula (€150+ validation)
- `POST /create-order` - Create order
- `POST /payment-webhook` - Payment provider webhook
- `GET /list-formulas` - List formulas
- `GET /list-orders` - List orders

### Messaging (`/messaging`)
- `POST /open-thread` - Create/get patient thread
- `POST /post-message` - Send message
- `GET /list-messages` - Get thread messages
- `POST /preview-segment` - Preview marketing segment
- `POST /send-campaign` - Send marketing campaign

### Admin (`/admin`)
- `POST /metrics` - Dashboard metrics
- `POST /audit-search` - Search audit logs
- `GET /dashboard-overview` - Admin dashboard data
- `POST /export-data` - Data export

### GDPR (`/gdpr`)
- `POST /export-patient` - Complete patient data export
- `POST /delete-patient` - GDPR deletion request
- `GET /consent-status` - Get consent status
- `POST /update-consent` - Update consent

## Database Schema Highlights

### Core Tables
- **patients**: 15+ fields including soft delete, tags, VIP tier
- **protocols**: AI-generated treatment plans with versioning
- **protocol_sessions**: Granular session tracking
- **analyses**: Multi-modal analysis results with JSONB metrics
- **formulas**: Personalized skincare with €150 minimum pricing

### Security Features
- **RLS Policies**: 40+ policies covering all access patterns
- **Multi-tenant**: Organization-scoped access throughout
- **Audit Logs**: Every sensitive operation logged
- **Consent Tracking**: GDPR-compliant consent management

### Performance Optimizations
- **Strategic Indexes**: org_id, patient_id, status combinations
- **GIN Indexes**: JSONB fields for fast analytics queries
- **Timestamp Triggers**: Automated updated_at maintenance

## Storage Architecture

### Buckets
- `patient-images`: Before/after photos, skin scans
- `patient-docs`: Lab results, medical documents
- `chat-attachments`: Message attachments

### Policies
- **Organization Scoping**: Users can only access their org's files
- **Patient Self-Access**: Patients can read their own files
- **Staff Access**: Practitioners can manage org patient files

## Real-time Features

### Messaging
- WebSocket-based chat system
- Real-time message delivery
- Typing indicators support
- Message read receipts

### Notifications
- Multi-channel delivery (push, email, SMS)
- Campaign management
- Appointment reminders
- Treatment updates

## AI Integration Points

### Protocol Generation
- Analysis ingestion endpoint
- AI refresh triggers
- Protocol versioning
- Session scheduling

### Scoring System
- Longevity score computation
- Community benchmarking
- Component-based scoring
- Historical tracking

### Image Analysis
- Before/after comparison
- Automated metrics
- Progress tracking
- Treatment correlation

## GDPR Compliance

### Data Rights
- **Right to Access**: Complete patient data export
- **Right to Rectification**: Update patient information
- **Right to Erasure**: Soft delete with scheduled purge
- **Right to Portability**: JSON export format

### Consent Management
- Granular consent types (privacy, marketing, data_use)
- Consent history tracking
- Method documentation
- Easy withdrawal

### Audit Trail
- All sensitive operations logged
- Actor identification
- Before/after diffs
- Searchable audit interface

## Deployment & Operations

### Environment Configuration
- Development: Local Supabase setup
- Staging: Supabase hosted project
- Production: Supabase Pro with backups

### Monitoring
- Supabase built-in metrics
- Custom audit log analysis
- Performance monitoring via indexes
- Error tracking in Edge Functions

### Backup Strategy
- Automated Supabase backups
- Point-in-time recovery
- Cross-region replication available
- Export tooling for compliance

## Security Checklist

- [x] Row Level Security enabled on all tables
- [x] Multi-tenant data isolation
- [x] JWT authentication with proper verification
- [x] Service role access restricted to privileged functions
- [x] Input validation with Zod schemas
- [x] SQL injection prevention via parameterized queries
- [x] File upload security with signed URLs
- [x] GDPR compliance with consent tracking
- [x] Audit logging for sensitive operations
- [x] Secure storage policies

## Development Workflow

1. **Schema Changes**: Create migration files in `/supabase/migrations/`
2. **API Changes**: Update Edge Functions with proper validation
3. **Testing**: Run test suite against local Supabase
4. **Deployment**: Deploy via Supabase CLI
5. **Monitoring**: Check metrics and audit logs

## Future Enhancements

- **AI Service Integration**: Connect to treatment recommendation AI
- **Advanced Analytics**: Custom dashboards and reports
- **Mobile App Integration**: Push notification improvements
- **Third-party Integrations**: Lab systems, payment processors
- **Advanced Scheduling**: AI-optimized appointment scheduling