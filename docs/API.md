# KinAura API Documentation

## Overview

The KinAura API is built on Supabase Edge Functions using TypeScript/Deno. All endpoints use REST principles with JSON payloads and include comprehensive input validation using Zod schemas.

**Base URL**: `https://your-project.supabase.co/functions/v1/`

**Authentication**: Bearer token in Authorization header
```
Authorization: Bearer <jwt_token>
```

## Common Response Formats

### Success Response
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-20T12:00:00Z"
  }
}
```

### Error Response
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": { ... }
}
```

### Paginated Response
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "pages": 8
  }
}
```

## Authentication Endpoints

### Invite User
Invite a new user to the organization (Admin only).

**POST** `/auth/invite-user`

```json
{
  "email": "doctor@kinaura.it",
  "role": "practitioner",
  "org_id": "018c5c37-...",
  "full_name": "Dr. Sofia Bianchi"
}
```

**Response**:
```json
{
  "success": true,
  "user_id": "018c5c37-..."
}
```

### Switch Organization
Switch user's active organization.

**POST** `/auth/switch-org`

```json
{
  "org_id": "018c5c37-..."
}
```

## Patient Management Endpoints

### List Patients
Get paginated list of patients with filtering.

**GET** `/patients?page=1&limit=20&search=elena&tags=anti-aging,wellness`

**Response**:
```json
{
  "data": [
    {
      "id": "018c5c37-...",
      "code": "KA-001001",
      "full_name": "Elena Verdi",
      "email": "elena.verdi@example.com",
      "phone": "+39 347 123 4567",
      "vip_tier": "platinum",
      "tags": ["anti-aging", "wellness"],
      "memberships": [
        {
          "status": "active",
          "plan": {
            "name": "Platinum Membership",
            "tier": "platinum"
          }
        }
      ],
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "pages": 1
  }
}
```

### Create Patient
Create a new patient record.

**POST** `/patients`

```json
{
  "full_name": "Marco Rossi",
  "email": "marco.rossi@example.com",
  "phone": "+39 349 555 1234",
  "dob": "1980-05-15",
  "gender": "male",
  "country": "IT",
  "tags": ["longevity", "performance"]
}
```

**Response**:
```json
{
  "id": "018c5c37-...",
  "code": "KA-001003",
  "full_name": "Marco Rossi",
  "org_id": "018c5c37-...",
  "created_at": "2024-01-20T12:00:00Z"
}
```

### Get Patient Details
Get detailed patient information with related data.

**GET** `/patients/{patient_id}`

**Response**:
```json
{
  "id": "018c5c37-...",
  "full_name": "Elena Verdi",
  "memberships": [...],
  "protocols": [
    {
      "id": "018c5c37-...",
      "name": "Platinum Anti-Aging Protocol",
      "status": "active",
      "goals": {
        "inflammation": "reduce",
        "skin_texture": "improve"
      },
      "sessions": [
        {
          "idx": 1,
          "title": "Initial Assessment",
          "status": "done",
          "completed_at": "2024-01-10T10:15:00Z"
        }
      ]
    }
  ],
  "longevity_scores": [
    {
      "score_numeric": 78,
      "components": {
        "adherence": 85,
        "biomarkers": 72
      },
      "computed_at": "2024-01-18T08:00:00Z"
    }
  ]
}
```

### Add Patient Note
Add a note to patient record.

**POST** `/patients/{patient_id}/notes`

```json
{
  "content": "Patient shows excellent progress after initial treatment cycle.",
  "visibility": "practitioner_only",
  "attachments": [
    {
      "name": "progress_photo.jpg",
      "url": "patient-images/...",
      "type": "image/jpeg"
    }
  ]
}
```

### Request File Upload
Generate pre-signed URL for file upload.

**POST** `/patients/{patient_id}/upload`

```json
{
  "filename": "blood_test_results.pdf",
  "content_type": "application/pdf",
  "folder": "docs"
}
```

**Response**:
```json
{
  "upload_url": "https://...",
  "file_path": "018c5c37-.../1642680000-blood_test_results.pdf",
  "bucket": "patient-docs"
}
```

## Clinical Endpoints

### Ingest Analysis
Store lab results or diagnostic analysis.

**POST** `/clinical/ingest-analysis`

```json
{
  "patient_id": "018c5c37-...",
  "kind": "blood",
  "metrics": {
    "hemoglobin": 13.5,
    "vitamin_d": 32,
    "inflammatory_markers": {
      "crp": 1.2,
      "esr": 15
    }
  },
  "source": "clinic",
  "document_ids": ["blood_analysis_elena_20240110.pdf"]
}
```

### Refresh Protocol
Trigger AI-powered protocol update.

**POST** `/clinical/refresh-protocol`

```json
{
  "patient_id": "018c5c37-...",
  "force_regenerate": false
}
```

**Response**:
```json
{
  "protocol_id": "018c5c37-...",
  "ai_version": "v2024.1.20",
  "sessions_updated": 3
}
```

### Compare Before/After Images
Store and analyze treatment progress images.

**POST** `/clinical/compare-prepost`

```json
{
  "patient_id": "018c5c37-...",
  "treatment_context": "Ozone Therapy - Skin Assessment",
  "before_image": "patient-images/.../before_20240110.jpg",
  "after_image": "patient-images/.../after_20240117.jpg",
  "notes": "Significant improvement in skin texture"
}
```

### Recompute Longevity Scores
Calculate longevity scores for patients.

**POST** `/clinical/recompute-leaderboard`

```json
{
  "patient_ids": ["018c5c37-...", "018c5c37-..."]
}
```

**Response**:
```json
{
  "processed": 2,
  "average_score": 81.5
}
```

## Booking Endpoints

### Get Available Slots
Find available appointment slots.

**POST** `/booking/available-slots`

```json
{
  "service_id": "018c5c37-...",
  "practitioner_id": "018c5c37-...",
  "date": "2024-01-25",
  "timezone": "Europe/Rome"
}
```

**Response**:
```json
{
  "slots": [
    {
      "starts_at": "2024-01-25T09:00:00Z",
      "ends_at": "2024-01-25T10:15:00Z",
      "available": true
    },
    {
      "starts_at": "2024-01-25T10:30:00Z",
      "ends_at": "2024-01-25T11:45:00Z",
      "available": true
    }
  ]
}
```

### Book Appointment
Create a new appointment.

**POST** `/booking/book`

```json
{
  "service_id": "018c5c37-...",
  "patient_id": "018c5c37-...",
  "starts_at": "2024-01-25T09:00:00Z",
  "practitioner_id": "018c5c37-...",
  "notes": "First NAD+ therapy session"
}
```

**Response**:
```json
{
  "id": "018c5c37-...",
  "starts_at": "2024-01-25T09:00:00Z",
  "ends_at": "2024-01-25T12:00:00Z",
  "status": "scheduled",
  "service": {
    "name": "NAD+ IV Therapy",
    "duration_min": 180
  },
  "patient": {
    "full_name": "Elena Verdi"
  }
}
```

### Reschedule Appointment
Reschedule an existing appointment.

**POST** `/booking/reschedule`

```json
{
  "appointment_id": "018c5c37-...",
  "new_starts_at": "2024-01-26T14:00:00Z",
  "reason": "Patient requested different time"
}
```

## Commerce Endpoints

### Create Formula
Create a personalized skincare formula.

**POST** `/commerce/create-formula`

```json
{
  "patient_id": "018c5c37-...",
  "analysis_id": "018c5c37-...",
  "name": "Elena Custom Anti-Aging Serum",
  "actives": {
    "retinoid_complex": true,
    "vitamin_c": true,
    "peptides": true
  },
  "concentration": {
    "retinoid": "0.5%",
    "vitamin_c": "15%",
    "peptides": "5%"
  },
  "fragrance": "Rose & Neroli",
  "packaging": "serum_bottle"
}
```

### Finalize Formula
Finalize formula with pricing (minimum €150).

**POST** `/commerce/finalize-formula`

```json
{
  "formula_id": "018c5c37-...",
  "price_cents": 18500
}
```

### Create Order
Create an order for formulas.

**POST** `/commerce/create-order`

```json
{
  "patient_id": "018c5c37-...",
  "formula_id": "018c5c37-...",
  "channel": "app"
}
```

**Response**:
```json
{
  "order": {
    "id": "018c5c37-...",
    "total_cents": 18500,
    "status": "pending"
  },
  "payment": {
    "payment_url": "https://checkout.stripe.com/...",
    "session_id": "cs_mock_..."
  }
}
```

## Messaging Endpoints

### Open Thread
Create or get existing patient thread.

**POST** `/messaging/open-thread`

```json
{
  "patient_id": "018c5c37-..."
}
```

### Post Message
Send a message in a thread.

**POST** `/messaging/post-message`

```json
{
  "thread_id": "018c5c37-...",
  "body": "Your lab results look excellent! Let's schedule your next session.",
  "attachments": [
    {
      "name": "lab_summary.pdf",
      "url": "chat-attachments/.../lab_summary.pdf",
      "type": "application/pdf",
      "size": 245760
    }
  ]
}
```

### List Messages
Get messages from a thread.

**GET** `/messaging/list-messages?thread_id=018c5c37-...&limit=50&offset=0`

**Response**:
```json
[
  {
    "id": "018c5c37-...",
    "sender_role": "admin",
    "body": "Your lab results look excellent!",
    "attachments": [],
    "created_at": "2024-01-18T15:30:00Z",
    "sender": {
      "full_name": "Dr. Marco Rossi"
    }
  }
]
```

### Send Campaign
Send marketing campaign to segment.

**POST** `/messaging/send-campaign`

```json
{
  "campaign_id": "018c5c37-...",
  "test_mode": false
}
```

**Response**:
```json
{
  "sent_to": 156,
  "test_mode": false,
  "campaign_id": "018c5c37-..."
}
```

## Admin Endpoints

### Dashboard Metrics
Get admin dashboard metrics.

**POST** `/admin/metrics`

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "metrics": ["new_patients", "revenue", "avg_longevity_score"]
}
```

**Response**:
```json
{
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "metrics": {
    "new_patients": 23,
    "revenue": {
      "total_cents": 458900,
      "total_euros": 4589.00
    },
    "avg_longevity_score": 76.8
  }
}
```

### Search Audit Logs
Search audit trail.

**POST** `/admin/audit-search`

```json
{
  "actor_id": "018c5c37-...",
  "action": "create_patient",
  "start_date": "2024-01-01",
  "limit": 50
}
```

### Export Data
Export organization data.

**POST** `/admin/export-data`

```json
{
  "table": "patients",
  "format": "json"
}
```

## GDPR Endpoints

### Export Patient Data
Complete patient data export for GDPR compliance.

**POST** `/gdpr/export-patient`

```json
{
  "patient_id": "018c5c37-...",
  "include_files": true
}
```

**Response**: Complete JSON export with all patient data and file references.

### Delete Patient Data
GDPR deletion request.

**POST** `/gdpr/delete-patient`

```json
{
  "patient_id": "018c5c37-...",
  "confirmation": "DELETE_ALL_DATA",
  "retention_days": 30
}
```

### Update Consent
Update patient consent settings.

**POST** `/gdpr/update-consent`

```json
{
  "patient_id": "018c5c37-...",
  "kind": "marketing",
  "granted": false,
  "method": "patient_request"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `UNAUTHORIZED` | Invalid or missing authentication |
| `FORBIDDEN` | Insufficient permissions |
| `VALIDATION_ERROR` | Input validation failed |
| `NOT_FOUND` | Resource not found |
| `CONFLICT` | Resource conflict (e.g., appointment slot taken) |
| `PAYMENT_REQUIRED` | Payment or subscription required |
| `RATE_LIMITED` | Too many requests |
| `SERVER_ERROR` | Internal server error |

## Rate Limits

- **General API**: 100 requests per minute per user
- **File Upload**: 10 uploads per minute per user
- **Campaign Send**: 5 campaigns per hour per organization
- **Export Data**: 3 exports per hour per user

## Webhooks

### Payment Webhook
Handle payment provider callbacks.

**POST** `/commerce/payment-webhook`

```json
{
  "session_id": "cs_...",
  "status": "paid",
  "order_id": "018c5c37-..."
}
```

## Real-time Subscriptions

### Message Updates
Subscribe to real-time message updates using Supabase Realtime:

```javascript
supabase
  .channel(`thread-${threadId}`)
  .on('broadcast', { event: 'new-message' }, (payload) => {
    console.log('New message:', payload)
  })
  .subscribe()
```

### Appointment Reminders
Automatic notifications sent:
- 24 hours before appointment
- 2 hours before appointment
- When appointment is rescheduled or cancelled

This API provides comprehensive access to all KinAura platform features with proper authentication, validation, and error handling.