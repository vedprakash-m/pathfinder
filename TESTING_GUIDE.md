# Family Invitation System - Manual Testing Guide

## Prerequisites
1. Apply database migration: `alembic upgrade head`
2. Start the backend server: `uvicorn app.main:app --reload`
3. Configure email service (optional for testing)

## Test Cases

### 1. Create Family Invitation
```bash
# POST /families/{family_id}/invite
curl -X POST "http://localhost:8000/families/{family_id}/invite" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {jwt_token}" \
  -d '{
    "email": "newmember@example.com",
    "role": "adult",
    "message": "Welcome to our family!"
  }'
```

**Expected Response:**
- Status: 201 Created
- Returns invitation object with token
- Email sent to recipient (if email service configured)

### 2. List Family Invitations
```bash
# GET /families/{family_id}/invitations
curl -X GET "http://localhost:8000/families/{family_id}/invitations" \
  -H "Authorization: Bearer {jwt_token}"
```

**Expected Response:**
- Status: 200 OK
- Returns array of invitation objects
- Shows pending, accepted, declined, expired invitations

### 3. Accept Family Invitation
```bash
# POST /families/accept-invitation
curl -X POST "http://localhost:8000/families/accept-invitation" \
  -H "Content-Type: application/json" \
  -d '{
    "invitation_token": "{invitation_token}",
    "user_email": "newmember@example.com"
  }'
```

**Expected Response:**
- Status: 200 OK
- Creates new family member
- Updates invitation status to ACCEPTED
- Returns success message

### 4. Decline Family Invitation
```bash
# POST /families/decline-invitation
curl -X POST "http://localhost:8000/families/decline-invitation" \
  -H "Content-Type: application/json" \
  -d '{
    "invitation_token": "{invitation_token}",
    "user_email": "newmember@example.com"
  }'
```

**Expected Response:**
- Status: 200 OK
- Updates invitation status to DECLINED
- Returns success message

## Database Verification

### Check invitation was created:
```sql
SELECT * FROM family_invitations WHERE email = 'newmember@example.com';
```

### Check family member was created (after acceptance):
```sql
SELECT * FROM family_members WHERE user_id = '{user_id}';
```

### Check invitation status updates:
```sql
SELECT status, accepted_at FROM family_invitations WHERE invitation_token = '{token}';
```

## Email Verification (if configured)

1. Check email service logs for successful sending
2. Verify email received with correct family name and inviter
3. Confirm invitation link contains valid token
4. Test that email template renders correctly

## Error Scenarios to Test

### 1. Duplicate Invitation
- Try inviting the same email twice
- Should return 409 Conflict

### 2. Permission Denied
- Try inviting as non-admin family member
- Should return 403 Forbidden

### 3. Invalid Token
- Try accepting with invalid/expired token
- Should return 400 Bad Request

### 4. Email Mismatch
- Try accepting with different email than invited
- Should return 400 Bad Request

### 5. Expired Invitation
- Wait 7 days or manually update expires_at
- Try accepting expired invitation
- Should return 400 Bad Request with "expired" message

## Frontend Integration Testing

1. Test familyService.ts methods:
   - `inviteMember()`
   - `acceptInvitation()`
   - `declineInvitation()`
   - `getInvitations()`

2. Verify TypeScript types match API responses
3. Test error handling in UI components
4. Verify invitation email links work with frontend routes

## Performance Testing

1. Test inviting multiple members simultaneously
2. Test with large family sizes
3. Monitor database query performance
4. Check email sending latency

## Security Testing

1. Verify JWT token validation on all endpoints
2. Test invitation token uniqueness and randomness
3. Confirm permission checks work correctly
4. Test rate limiting on invitation sending (if implemented)

---

**✅ Success Criteria:**
- All API endpoints respond correctly
- Database records created/updated properly
- Email sent successfully (if configured)
- Frontend integration works seamlessly
- Error handling is robust and user-friendly

**🎯 This completes the family invitation feature implementation!**
