# WeLink - Evelyn Hone College Lost & Found System

## Overview
WeLink is a web-based lost and found management system for Evelyn Hone College. It allows students to report lost items, submit found items, and search a centralized database for their belongings. Administrators can manage submissions and monitor system activity. The system features a futuristic, clean interface with real-time notifications, email alerts, and image upload capabilities, aiming to streamline the process of reuniting lost items with their owners within the college community.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
The frontend uses Jinja2 for templating, custom CSS with a futuristic design, and vanilla JavaScript. It incorporates Font Awesome for icons and Google Fonts (Poppins). The design features a template inheritance pattern with electric blue (#00BFFF) as the primary accent against a dark background (#121212). Key UI features include responsive navigation, a flash message system, card-based layouts for items, and robust form validation.

### Technical Implementations
**Backend:**
- **Framework:** Flask.
- **Authentication:** Flask-Login for session-based authentication with Werkzeug for password hashing. Supports two-tier user roles (regular users and administrators).
- **File Upload:** Local storage (`uploads/`) with validation for image types (png, jpg, jpeg, gif) and size (16MB max). Secure filename sanitization is used.
- **Notification System:** Dual approach with database-backed in-app notifications and email alerts via Flask-Mail for timely updates.
- **Security:** CSRF protection via Flask-WTF, password hashing, environment-configurable session secret key, and file upload restrictions.

**Feature Specifications:**
- **Item Matching:** Automated system to detect similar lost and found items based on name and location (case-insensitive partial name matching and exact location). Users receive in-app and email notifications for potential matches.
- **User Management:** Students can delete their own lost/found items.
- **Admin Management:**
    - Single admin policy: Ensures only one protected admin account.
    - Student Approval: New student registrations require admin approval before login.
    - Student Account Management: Admins can delete student accounts (with cascade deletion of associated data) and edit student information, including optional password resets.
    - Separate Login Pages: Dedicated login pages for students (`/login`) and admins (`/admin/login`) with role-specific branding and access control.
- **Mobile Responsiveness:** Comprehensive responsive CSS for various screen sizes, including mobile-friendly navigation, optimized layouts, and touch-optimized elements.

### System Design Choices
- **Database:** SQLite with SQLAlchemy ORM for simplicity and zero-configuration, ideal for development and small-to-medium deployments.
- **Schema:** Includes `Users` (authentication, roles), `LostItem`, `FoundItem` (item details, user relationships), and `Notification` tables, all with cascade delete for data integrity.

## External Dependencies

### Services
- **Email Service:** SMTP (defaulting to Gmail, configurable) via Flask-Mail for sending notifications. Requires environment variables for `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, and `MAIL_DEFAULT_SENDER`.

### Third-Party CDNs
- **Font Awesome 6.4.0:** For icons.
- **Google Fonts:** For the Poppins typeface.

### Python Packages
- `Flask`: Web framework.
- `Flask-Login`: User session management.
- `Flask-Mail`: Email functionality.
- `Flask-WTF`: CSRF protection.
- `Flask-SQLAlchemy`: Database ORM.
- `Werkzeug`: Utilities for password hashing and secure filenames.
### October 16, 2025 - Admin Email Communication Feature

**Custom Email Sending:**
- Admins can now send custom emails to specific students directly from the admin dashboard
- "Send Email" button added to both Student Management and Pending Student Approvals sections
- Email form includes recipient information, subject field, and message body
- Uses existing email infrastructure (Flask-Mail) for delivery

**Route Added:**
- `/admin/send-email/<user_id>` - Send custom email to specific student (GET/POST)

**Features:**
- Email composition form shows student details (name, email, student number)
- Required field validation for subject and message
- Success/error flash messages for user feedback
- CSRF protection on all submissions
- Admin-only access control

**Template Created:**
- `admin_send_email.html` - Email composition interface with recipient preview

### October 28, 2025 - Social Feed Feature

**Student Social Feed:**
- Students can now create and share posts with other students, similar to Facebook
- Feed displays all student posts in reverse chronological order (newest first)
- Posts support text content and optional image uploads
- Interactive features include likes and comments on posts
- Students can only delete their own posts
- Comments are hidden by default and only shown when comment icon is clicked

**Student Profiles:**
- Students can upload and manage profile pictures
- Profile pictures display throughout the feed on posts and comments
- Profile page shows account information and member since date
- One-click profile picture upload with automatic replacement of old picture

**Database Models Added:**
- `Post` - Stores student posts with content, optional image, and timestamp
- `Comment` - Stores comments on posts with user relationship (includes reaction support)
- `PostLike` - Tracks which users liked which posts (prevents duplicate likes)
- `CommentReaction` - Tracks thumbs-up reactions on comments (prevents duplicate reactions)
- `User.profile_picture` - New field for storing profile picture path

**Routes Added:**
- `/feed` (GET) - View all student posts in the social feed
- `/feed/create` (POST) - Create a new post with text and optional image
- `/feed/post/<post_id>/like` (POST) - Like/unlike a post (returns JSON)
- `/feed/post/<post_id>/comment` (POST) - Add a comment to a post (returns JSON)
- `/feed/post/<post_id>/delete` (POST) - Delete a post (author only)
- `/feed/comment/<comment_id>/react` (POST) - React to a comment with thumbs-up (returns JSON)
- `/profile` (GET/POST) - View and update student profile with picture upload

**Features:**
- Facebook-like user interface with post cards, profile pictures, and timestamps
- Real-time like, comment, and reaction updates using JavaScript fetch API
- Image upload support for posts and profile pictures (stored in uploads/ folder)
- Comments hidden by default - click "Comment" to reveal comment section
- Like counter and comment counter on each post
- Reaction counter on each comment with thumbs-up button
- Visual feedback for liked posts (red heart icon) and reacted comments (blue thumb)
- Profile pictures displayed in circular avatars with blue borders
- Responsive design matching the existing WeLink aesthetic
- "Feed" and "Profile" navigation links added to student dashboard sidebar

**Templates Created:**
- `feed.html` - Social feed interface with post creation form and post display
- `profile.html` - Student profile page with picture upload and account information

### November 11, 2025 - Form Validation Enhancement

**Enhanced Security and User Experience:**
- Implemented comprehensive form validation system using Flask-WTF forms with custom validators
- Created reusable validation logic to ensure consistent security standards across all user-facing forms
- Both server-side and client-side validation for immediate user feedback

**Validation Rules:**
- **Password Requirements:**
  - Minimum 8 characters (previously was 6)
  - Must include at least one uppercase letter
  - Must include at least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\/;~`)
- **Student Number Requirements:**
  - Must be between 10-12 characters in length
  - Enforced on registration and admin account creation

**New Module Created:**
- `forms.py` - Contains Flask-WTF form classes and custom validators:
  - `validate_password_strength()` - Custom validator for password complexity
  - `validate_student_number()` - Custom validator for student number length
  - `RegisterForm` - Student registration form with validations and password confirmation
  - `AdminCreateStudentForm` - Admin student creation form with validations
  - `ChangePasswordForm` - Password change form with validations and password matching

**Routes Updated:**
- `/register` - Now uses RegisterForm with enhanced validations
- `/admin/create-student` - Now uses AdminCreateStudentForm with enhanced validations
- `/change-password` - Now uses ChangePasswordForm with enhanced validations and password matching

**Templates Updated:**
- `register.html` - Added validation error display, HTML5 pattern validation, and confirm password field
- `admin_create_student.html` - Added validation error display and HTML5 pattern validation
- `change_password.html` - Added validation error display and HTML5 pattern validation
- All forms now display helpful hints about requirements below password fields
- Password confirmation fields ensure users enter their password correctly
- Error messages shown in red with exclamation icon for visibility

**CSS Enhancements:**
- Added `.form-errors` styling for validation error display
- Added `.error-text` styling with red color (#ff6b6b) and icons
- Added `.form-hint` styling for helpful requirement hints
- Error states visually highlight problematic fields

### November 11, 2025 - Enhanced Lost & Found Item Forms

**Structured Item Submission:**
- Added detailed structured fields to both "Report Lost Item" and "Submit Found Item" forms
- New optional fields help categorize and describe items more precisely
- Better matching potential with consistent, structured data
- Improved user experience with guided input and helpful placeholders

**New Database Fields:**
- `category` (VARCHAR 50) - Item category selection from predefined list
- `color` (VARCHAR 50) - Item color description
- `model` (VARCHAR 100) - Model number or brand name (especially for electronics)
- `size` (VARCHAR 50) - Item size description
- All new fields are optional (nullable) to maintain backwards compatibility

**Category Options:**
- Electronics (Phone, Laptop, Tablet, etc.)
- Bags & Backpacks
- Clothing & Accessories
- Documents & IDs
- Books & Notebooks
- Keys & Keychains
- Jewelry & Watches
- Sports Equipment
- Other

**Database Migration:**
- Successfully applied SQLite schema migration
- Added 8 new columns (4 to `lost_items`, 4 to `found_items`)
- All existing data preserved and unaffected
- Migration approach: Direct ALTER TABLE commands via Python script

**Form Enhancements:**
- Category dropdown with descriptive options guides user selection
- Color, size, and model fields with helpful placeholders
- Reorganized form layout with Font Awesome icons for visual clarity
- "Description" field relabeled as "Additional Description" for better context
- Smart field grouping (color/size in same row for compact layout)
- Helpful hints throughout forms improve data quality

**Routes Updated:**
- `/report-lost` - Now captures and stores all new structured fields
- `/submit-found` - Now captures and stores all new structured fields

**Templates Updated:**
- `report_lost.html` - Enhanced with category dropdown and structured fields
- `submit_found.html` - Enhanced with category dropdown and structured fields

**Benefits:**
- More consistent data entry across all submissions
- Better item identification with structured attributes
- Easier future implementation of advanced search/filter features
- Optional fields don't force users to fill unnecessary information
- Improved item matching potential with detailed metadata
