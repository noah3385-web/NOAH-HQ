# Noah OS Manual Setup Checklist

Use this after `python build_clickup_noah_os.py --apply` completes.

## Native custom fields

Create these fields where useful across the sandbox lists: Domain, Module, Object Type, Related Customer / Borrower, Related Lead, Related Loan File, Related Realtor, Related Realtor Team, Related Brokerage, Related Loan Officer, Related Internal Employee, Related Vendor, Related Event, Related Partner, State / Market, Stage, Follow-Up Date, Last Contact Date, Next Contact Date, Waiting On, Blocked Reason, Source / Capture Method, Original Capture Text, AI Confidence, Needs Review, Note Only / No Action, Relationship Health, Revenue Impact, Deadline Risk, Follow-Up Required, and Last Reviewed Date.

## Tags

Create tags: lead, loan, borrower, realtor, realtor-team, brokerage, referral-partner, loan-officer, partner-management, new-business-development, existing-partner, event, marketing, content, vendor, budget, roi, ap, ar, reporting, business-planning, sales-coaching, performance-management, compensation, internal-team, operations, manager-feedback, business-coach, career-planning, customer-service, complaint, qualification-issue, underwriting, closing, post-closing, refinance-opportunity, waiting-on-client, waiting-on-realtor, waiting-on-operations, blocked, needs-review, personal-finance, savings, retirement, taxes, home, home-maintenance, medical, health, travel, personal-event, personal-relationship, hobby, creative, note-only, memory, archive.

## Dashboards/views

Create native dashboards or saved views for Noah Command Center, Mortgage Pipeline Dashboard, Active Loan Risk Dashboard, Partner Dashboard, Business Development Dashboard, Internal Team Dashboard, Reporting ROI Dashboard, and Personal OS Dashboard.

## Automations

Create automations for new lead follow-up, three-attempt lead contact sequence, daily follow-up for pending lead/customer items, realtor update reminders, partner touchpoint reminders, ROI review reminders, event follow-up, employee coaching follow-up, personal budget review, home maintenance reminders, medical reminders, and Capture Inbox review.

## Recurring tasks

Configure recurring rules for Morning Briefing every weekday at 8:30 AM Eastern, Evening Wrap-Up every weekday at 5:00 PM Eastern, Weekly Review every Friday at 3:00 PM Eastern, Monthly Business Review, Monthly Personal Finance Review, Quarterly Planning Review, and Annual Planning Review.

## Native templates

Convert the `TEMPLATE - ...` tasks into native ClickUp templates if the workspace plan supports templates.

## Relationship fields

Create relationships for Lead to borrower, Borrower to realtor, Realtor to team, Team to brokerage, Partner to events, Partner to ROI records, and Employee to coaching/performance records.

## Stage/status configuration

Start with default statuses for the MVP. Later configure statuses or dropdown fields for mortgage stages from `REFERENCE - Mortgage Pipeline Stages`, partner/business-development stages, event statuses, internal coaching statuses, and personal operating statuses.
