"""
Notification Service Module
Handles all notification-related operations including email, SMS, push notifications,
and in-app notifications with comprehensive error handling and auditing.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

# Import local modules
from apps.core.services.audit_service import AuditService
from apps.communications.models import (
    Communication, CommunicationChannel, CommunicationTemplate,
    Notification, CommunicationPreference, Message, MessageRecipient
)
from apps.students.models import Student
from apps.academics.models import AcademicYear, SchoolClass, Section

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """
    Comprehensive notification service for handling all types of communications
    """
    
    @staticmethod
    def send_email_notification(
        recipient: Union[User, Student, str],
        subject: str,
        message: str,
        html_message: Optional[str] = None,
        sender: Optional[User] = None,
        template_code: Optional[str] = None,
        context: Optional[Dict] = None,
        attachments: Optional[List[Dict]] = None,
        tenant=None,
        priority: str = "MEDIUM"
    ) -> Dict:
        """
        Send email notification with comprehensive error handling
        
        Args:
            recipient: User, Student, or email string
            subject: Email subject
            message: Plain text message
            html_message: HTML formatted message (optional)
            sender: User sending the email
            template_code: Template code for audit logging
            context: Template context variables
            attachments: List of attachment dictionaries
            tenant: Tenant object
            priority: Notification priority
            
        Returns:
            Dict with success status and details
        """
        try:
            # Get recipient email
            recipient_email = NotificationService._get_recipient_email(recipient)
            if not recipient_email:
                logger.warning(f"No email address found for recipient: {recipient}")
                return {
                    'success': False,
                    'error': _('No email address found for recipient'),
                    'recipient': str(recipient)
                }
            
            # Check communication preferences
            if isinstance(recipient, User) and not NotificationService._can_receive_email(recipient):
                logger.info(f"Email notifications disabled for user: {recipient.email}")
                return {
                    'success': False,
                    'error': _('Email notifications disabled'),
                    'recipient': recipient_email
                }
            
            # Prepare email
            email = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
                reply_to=[sender.email] if sender else [settings.DEFAULT_REPLY_TO],
                headers={
                    'X-Priority': NotificationService._get_priority_header(priority),
                    'X-Notification-Type': 'SYSTEM',
                    'X-Template-Code': template_code or 'DIRECT_EMAIL'
                }
            )
            
            # Add HTML alternative
            if html_message:
                email.attach_alternative(html_message, "text/html")
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    email.attach(
                        filename=attachment.get('filename', 'attachment'),
                        content=attachment.get('content', b''),
                        mimetype=attachment.get('mimetype', 'application/octet-stream')
                    )
            
            # Send email
            sent_count = email.send(fail_silently=False)
            
            # Create communication record
            communication = NotificationService._create_communication_record(
                channel_type="EMAIL",
                recipient=recipient,
                subject=subject,
                content=message,
                sender=sender,
                template_code=template_code,
                context=context,
                tenant=tenant,
                status="SENT" if sent_count > 0 else "FAILED",
                priority=priority
            )
            
            # Create audit log
            AuditService.create_audit_entry(
                action='CREATE',
                resource_type='EmailNotification',
                user=sender,
                tenant=tenant,
                request=None,
                severity='INFO' if sent_count > 0 else 'ERROR',
                instance=communication,
                extra_data={
                    'recipient': recipient_email,
                    'subject': subject,
                    'template_code': template_code,
                    'sent_count': sent_count,
                    'has_html': bool(html_message),
                    'attachments_count': len(attachments) if attachments else 0
                }
            )
            
            return {
                'success': sent_count > 0,
                'sent_count': sent_count,
                'recipient': recipient_email,
                'communication_id': str(communication.id) if communication else None,
                'message': _('Email sent successfully') if sent_count > 0 else _('Failed to send email')
            }
            
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}", exc_info=True)
            
            # Create failed communication record
            NotificationService._create_communication_record(
                channel_type="EMAIL",
                recipient=recipient,
                subject=subject,
                content=message,
                sender=sender,
                template_code=template_code,
                context=context,
                tenant=tenant,
                status="FAILED",
                priority=priority,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'recipient': recipient_email if 'recipient_email' in locals() else str(recipient)
            }
    
    @staticmethod
    def send_sms_notification(
        recipient: Union[User, Student, str],
        message: str,
        sender: Optional[User] = None,
        template_code: Optional[str] = None,
        context: Optional[Dict] = None,
        tenant=None,
        priority: str = "MEDIUM"
    ) -> Dict:
        """
        Send SMS notification
        
        Args:
            recipient: User, Student, or phone number string
            message: SMS message (max 160 characters)
            sender: User sending the SMS
            template_code: Template code for audit logging
            context: Template context variables
            tenant: Tenant object
            priority: Notification priority
            
        Returns:
            Dict with success status and details
        """
        try:
            # Get recipient phone
            recipient_phone = NotificationService._get_recipient_phone(recipient)
            if not recipient_phone:
                logger.warning(f"No phone number found for recipient: {recipient}")
                return {
                    'success': False,
                    'error': _('No phone number found for recipient'),
                    'recipient': str(recipient)
                }
            
            # Check communication preferences
            if isinstance(recipient, User) and not NotificationService._can_receive_sms(recipient):
                logger.info(f"SMS notifications disabled for user: {recipient.email}")
                return {
                    'success': False,
                    'error': _('SMS notifications disabled'),
                    'recipient': recipient_phone
                }
            
            # Truncate message if too long
            if len(message) > 160:
                message = message[:157] + "..."
            
            # TODO: Integrate with SMS gateway (Twilio, MessageBird, etc.)
            # For now, log and return success for development
            logger.info(f"SMS would be sent to {recipient_phone}: {message}")
            
            # Create communication record
            communication = NotificationService._create_communication_record(
                channel_type="SMS",
                recipient=recipient,
                subject="SMS Notification",
                content=message,
                sender=sender,
                template_code=template_code,
                context=context,
                tenant=tenant,
                status="SENT",  # Assuming success for now
                priority=priority
            )
            
            # Create audit log
            AuditService.create_audit_entry(
                action='CREATE',
                resource_type='SMSNotification',
                user=sender,
                tenant=tenant,
                request=None,
                severity='INFO',
                instance=communication,
                extra_data={
                    'recipient': recipient_phone,
                    'message_length': len(message),
                    'template_code': template_code
                }
            )
            
            return {
                'success': True,
                'recipient': recipient_phone,
                'communication_id': str(communication.id) if communication else None,
                'message': _('SMS sent successfully (simulated in development)')
            }
            
        except Exception as e:
            logger.error(f"SMS sending error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'recipient': recipient_phone if 'recipient_phone' in locals() else str(recipient)
            }
    
    @staticmethod
    def send_in_app_notification(
        recipient: User,
        title: str,
        message: str,
        notification_type: str = "SYSTEM",
        sender: Optional[User] = None,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        priority: str = "MEDIUM",
        expires_in_hours: Optional[int] = None,
        related_object=None,
        tenant=None
    ) -> Notification:
        """
        Send in-app notification
        
        Args:
            recipient: User receiving the notification
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            sender: User sending the notification
            action_url: URL for action button
            action_text: Text for action button
            priority: Notification priority
            expires_in_hours: Hours until notification expires
            related_object: Related object for context
            tenant: Tenant object
            
        Returns:
            Notification object
        """
        try:
            # Check communication preferences
            if not NotificationService._can_receive_in_app(recipient):
                logger.info(f"In-app notifications disabled for user: {recipient.email}")
                return None
            
            # Calculate expiration time
            expires_at = None
            if expires_in_hours:
                expires_at = timezone.now() + timezone.timedelta(hours=expires_in_hours)
            
            # Create notification
            with transaction.atomic():
                notification = Notification.objects.create(
                    tenant=tenant,
                    recipient=recipient,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    action_url=action_url,
                    action_text=action_text,
                    expires_at=expires_at
                )
                
                # Link related object if provided
                if related_object:
                    notification.content_type = NotificationService._get_content_type(related_object)
                    notification.object_id = related_object.id
                    notification.save()
            
            # Create audit log
            AuditService.create_audit_entry(
                action='CREATE',
                resource_type='InAppNotification',
                user=sender,
                tenant=tenant,
                request=None,
                severity='INFO',
                instance=notification,
                extra_data={
                    'recipient': str(recipient),
                    'notification_type': notification_type,
                    'priority': priority,
                    'has_action': bool(action_url),
                    'expires_at': str(expires_at) if expires_at else None
                }
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"In-app notification creation error: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def send_student_registration_notification(
        student: Student,
        created_by: User,
        tenant=None
    ) -> Dict:
        """
        Send notifications for student registration
        
        Args:
            student: Registered student
            created_by: User who created the student
            tenant: Tenant object
            
        Returns:
            Dict with notification results
        """
        results = {}
        
        try:
            # 1. Send welcome email to student
            if student.personal_email:
                email_result = NotificationService.send_email_notification(
                    recipient=student,
                    subject=f"Welcome to {tenant.name or 'Our School'}!",
                    message=render_to_string('communications/emails/student_welcome.txt', {
                        'student': student,
                        'tenant': tenant,
                        'created_by': created_by,
                        'admission_number': student.admission_number
                    }),
                    html_message=render_to_string('communications/emails/student_welcome.html', {
                        'student': student,
                        'tenant': tenant,
                        'created_by': created_by,
                        'admission_number': student.admission_number
                    }),
                    sender=created_by,
                    template_code="STUDENT_WELCOME",
                    tenant=tenant,
                    priority="HIGH"
                )
                results['student_email'] = email_result
            
            # 2. Send in-app notification to student (if they have a user account)
            if hasattr(student, 'user') and student.user:
                notification = NotificationService.send_in_app_notification(
                    recipient=student.user,
                    title="Welcome!",
                    message=f"Welcome to {tenant.name or 'Our School'}. Your admission number is {student.admission_number}.",
                    notification_type="ACADEMIC",
                    sender=created_by,
                    action_url=f"/students/{student.id}/",
                    action_text="View Profile",
                    tenant=tenant
                )
                results['student_notification'] = bool(notification)
            
            # 3. Send notification to guardians
            for guardian in student.guardians.all():
                if guardian.email:
                    guardian_email_result = NotificationService.send_email_notification(
                        recipient=guardian.email,
                        subject=f"Student Registration: {student.full_name}",
                        message=render_to_string('communications/emails/guardian_registration.txt', {
                            'student': student,
                            'guardian': guardian,
                            'tenant': tenant,
                            'created_by': created_by
                        }),
                        html_message=render_to_string('communications/emails/guardian_registration.html', {
                            'student': student,
                            'guardian': guardian,
                            'tenant': tenant,
                            'created_by': created_by
                        }),
                        sender=created_by,
                        template_code="GUARDIAN_REGISTRATION",
                        tenant=tenant
                    )
                    results[f'guardian_email_{guardian.id}'] = guardian_email_result
            
            # 4. Send notification to admin users
            admin_users = User.objects.filter(
                tenant=tenant,
                groups__name__in=['Admin', 'Administrator', 'Super Admin']
            ).distinct()
            
            for admin in admin_users:
                admin_notification = NotificationService.send_in_app_notification(
                    recipient=admin,
                    title=f"New Student Registered: {student.full_name}",
                    message=f"Student {student.full_name} has been registered by {created_by.get_full_name()}.",
                    notification_type="SYSTEM",
                    sender=created_by,
                    action_url=f"/admin/students/student/{student.id}/change/",
                    action_text="View Student",
                    tenant=tenant
                )
                results[f'admin_notification_{admin.id}'] = bool(admin_notification)
            
            # 5. Create audit log for registration notification
            AuditService.create_audit_entry(
                action='CREATE',
                resource_type='StudentRegistrationNotification',
                user=created_by,
                tenant=tenant,
                request=None,
                severity='INFO',
                instance=student,
                extra_data={
                    'student_id': str(student.id),
                    'student_name': student.full_name,
                    'notifications_sent': len(results),
                    'results': results
                }
            )
            
            return {
                'success': True,
                'results': results,
                'message': _('Registration notifications sent successfully')
            }
            
        except Exception as e:
            logger.error(f"Student registration notification error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'results': results
            }
    
    @staticmethod
    def send_student_update_notification(
        student: Student,
        updated_by: User,
        changes: Dict,
        tenant=None
    ) -> Dict:
        """
        Send notifications for student updates
        
        Args:
            student: Updated student
            updated_by: User who updated the student
            changes: Dictionary of changes made
            tenant: Tenant object
            
        Returns:
            Dict with notification results
        """
        results = {}
        
        try:
            # Check if changes are significant enough to notify
            significant_changes = NotificationService._get_significant_changes(changes)
            if not significant_changes:
                return {
                    'success': True,
                    'message': _('No significant changes to notify'),
                    'results': {}
                }
            
            # Send in-app notification to student
            if hasattr(student, 'user') and student.user:
                notification = NotificationService.send_in_app_notification(
                    recipient=student.user,
                    title="Profile Updated",
                    message=f"Your profile has been updated by {updated_by.get_full_name()}.",
                    notification_type="ACADEMIC",
                    sender=updated_by,
                    action_url=f"/students/{student.id}/",
                    action_text="View Changes",
                    tenant=tenant
                )
                results['student_notification'] = bool(notification)
            
            # Send email to guardians for significant changes
            for guardian in student.guardians.all():
                if guardian.email and guardian.notify_on_changes:
                    email_result = NotificationService.send_email_notification(
                        recipient=guardian.email,
                        subject=f"Student Profile Updated: {student.full_name}",
                        message=render_to_string('communications/emails/student_update.txt', {
                            'student': student,
                            'guardian': guardian,
                            'updated_by': updated_by,
                            'changes': significant_changes,
                            'tenant': tenant
                        }),
                        html_message=render_to_string('communications/emails/student_update.html', {
                            'student': student,
                            'guardian': guardian,
                            'updated_by': updated_by,
                            'changes': significant_changes,
                            'tenant': tenant
                        }),
                        sender=updated_by,
                        template_code="STUDENT_UPDATE",
                        tenant=tenant
                    )
                    results[f'guardian_email_{guardian.id}'] = email_result
            
            return {
                'success': True,
                'results': results,
                'message': _('Update notifications sent successfully')
            }
            
        except Exception as e:
            logger.error(f"Student update notification error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'results': results
            }
    
    @staticmethod
    def send_student_deletion_notification(
        student: Student,
        deleted_by: User,
        reason: str,
        tenant=None
    ) -> Dict:
        """
        Send notifications for student deletion
        
        Args:
            student: Deleted student
            deleted_by: User who deleted the student
            reason: Reason for deletion
            tenant: Tenant object
            
        Returns:
            Dict with notification results
        """
        results = {}
        
        try:
            # Send email to guardians
            for guardian in student.guardians.all():
                if guardian.email:
                    email_result = NotificationService.send_email_notification(
                        recipient=guardian.email,
                        subject=f"Student Deletion: {student.full_name}",
                        message=render_to_string('communications/emails/student_deletion.txt', {
                            'student': student,
                            'guardian': guardian,
                            'deleted_by': deleted_by,
                            'reason': reason,
                            'tenant': tenant
                        }),
                        html_message=render_to_string('communications/emails/student_deletion.html', {
                            'student': student,
                            'guardian': guardian,
                            'deleted_by': deleted_by,
                            'reason': reason,
                            'tenant': tenant
                        }),
                        sender=deleted_by,
                        template_code="STUDENT_DELETION",
                        tenant=tenant,
                        priority="HIGH"
                    )
                    results[f'guardian_email_{guardian.id}'] = email_result
            
            # Send notification to admin users
            admin_users = User.objects.filter(
                tenant=tenant,
                groups__name__in=['Admin', 'Administrator', 'Super Admin']
            ).distinct()
            
            for admin in admin_users:
                admin_notification = NotificationService.send_in_app_notification(
                    recipient=admin,
                    title=f"Student Deleted: {student.full_name}",
                    message=f"Student {student.full_name} has been deleted by {deleted_by.get_full_name()}. Reason: {reason}",
                    notification_type="SECURITY",
                    sender=deleted_by,
                    tenant=tenant,
                    priority="HIGH"
                )
                results[f'admin_notification_{admin.id}'] = bool(admin_notification)
            
            return {
                'success': True,
                'results': results,
                'message': _('Deletion notifications sent successfully')
            }
            
        except Exception as e:
            logger.error(f"Student deletion notification error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'results': results
            }
    
    @staticmethod
    def send_guardian_added_notification(
        guardian,
        student: Student,
        added_by: User,
        tenant=None
    ) -> Dict:
        """
        Send notifications when guardian is added
        
        Args:
            guardian: Added guardian
            student: Student the guardian was added to
            added_by: User who added the guardian
            tenant: Tenant object
            
        Returns:
            Dict with notification results
        """
        try:
            # Send welcome email to guardian
            if guardian.email:
                email_result = NotificationService.send_email_notification(
                    recipient=guardian.email,
                    subject=f"Added as Guardian for {student.full_name}",
                    message=render_to_string('communications/emails/guardian_added.txt', {
                        'guardian': guardian,
                        'student': student,
                        'added_by': added_by,
                        'tenant': tenant
                    }),
                    html_message=render_to_string('communications/emails/guardian_added.html', {
                        'guardian': guardian,
                        'student': student,
                        'added_by': added_by,
                        'tenant': tenant
                    }),
                    sender=added_by,
                    template_code="GUARDIAN_ADDED",
                    tenant=tenant
                )
                
                return {
                    'success': email_result.get('success', False),
                    'email_result': email_result,
                    'message': _('Guardian added notification sent')
                }
            
            return {
                'success': True,
                'message': _('No email address for guardian, notification skipped')
            }
            
        except Exception as e:
            logger.error(f"Guardian added notification error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def send_document_uploaded_notification(
        document,
        uploaded_by: User,
        tenant=None
    ) -> Dict:
        """
        Send notifications when document is uploaded
        
        Args:
            document: Uploaded document
            uploaded_by: User who uploaded the document
            tenant: Tenant object
            
        Returns:
            Dict with notification results
        """
        try:
            student = document.student
            
            # Send notification to student
            if hasattr(student, 'user') and student.user:
                notification = NotificationService.send_in_app_notification(
                    recipient=student.user,
                    title="Document Uploaded",
                    message=f"A new document '{document.file_name}' has been uploaded to your profile.",
                    notification_type="ACADEMIC",
                    sender=uploaded_by,
                    action_url=f"/students/{student.id}/documents/",
                    action_text="View Documents",
                    tenant=tenant
                )
                
                return {
                    'success': bool(notification),
                    'notification': notification,
                    'message': _('Document uploaded notification sent')
                }
            
            return {
                'success': True,
                'message': _('No user account for student, notification skipped')
            }
            
        except Exception as e:
            logger.error(f"Document uploaded notification error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def send_student_promotion_notification(
        student: Student,
        old_class,
        new_class,
        promoted_by: User,
        tenant=None
    ) -> Dict:
        """
        Send notifications for student promotion
        
        Args:
            student: Promoted student
            old_class: Previous class
            new_class: New class
            promoted_by: User who promoted the student
            tenant: Tenant object
            
        Returns:
            Dict with notification results
        """
        results = {}
        
        try:
            # Send email to student
            if student.personal_email:
                email_result = NotificationService.send_email_notification(
                    recipient=student,
                    subject=f"Promotion to {new_class.name}",
                    message=render_to_string('communications/emails/student_promotion.txt', {
                        'student': student,
                        'old_class': old_class,
                        'new_class': new_class,
                        'promoted_by': promoted_by,
                        'tenant': tenant
                    }),
                    html_message=render_to_string('communications/emails/student_promotion.html', {
                        'student': student,
                        'old_class': old_class,
                        'new_class': new_class,
                        'promoted_by': promoted_by,
                        'tenant': tenant
                    }),
                    sender=promoted_by,
                    template_code="STUDENT_PROMOTION",
                    tenant=tenant,
                    priority="HIGH"
                )
                results['student_email'] = email_result
            
            # Send email to guardians
            for guardian in student.guardians.all():
                if guardian.email:
                    guardian_email_result = NotificationService.send_email_notification(
                        recipient=guardian.email,
                        subject=f"Student Promotion: {student.full_name}",
                        message=render_to_string('communications/emails/guardian_promotion.txt', {
                            'student': student,
                            'guardian': guardian,
                            'old_class': old_class,
                            'new_class': new_class,
                            'promoted_by': promoted_by,
                            'tenant': tenant
                        }),
                        html_message=render_to_string('communications/emails/guardian_promotion.html', {
                            'student': student,
                            'guardian': guardian,
                            'old_class': old_class,
                            'new_class': new_class,
                            'promoted_by': promoted_by,
                            'tenant': tenant
                        }),
                        sender=promoted_by,
                        template_code="GUARDIAN_PROMOTION",
                        tenant=tenant
                    )
                    results[f'guardian_email_{guardian.id}'] = guardian_email_result
            
            # Send in-app notification
            if hasattr(student, 'user') and student.user:
                notification = NotificationService.send_in_app_notification(
                    recipient=student.user,
                    title=f"Promoted to {new_class.name}",
                    message=f"Congratulations! You have been promoted from {old_class.name} to {new_class.name}.",
                    notification_type="ACADEMIC",
                    sender=promoted_by,
                    action_url=f"/students/{student.id}/",
                    action_text="View Profile",
                    tenant=tenant,
                    priority="HIGH"
                )
                results['student_notification'] = bool(notification)
            
            return {
                'success': True,
                'results': results,
                'message': _('Promotion notifications sent successfully')
            }
            
        except Exception as e:
            logger.error(f"Student promotion notification error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'results': results
            }
    
    @staticmethod
    def broadcast_to_class(
        school_class: SchoolClass,
        title: str,
        message: str,
        sender: User,
        notification_type: str = "ANNOUNCEMENT",
        include_guardians: bool = False,
        tenant=None
    ) -> Dict:
        """
        Broadcast notification to all students in a class
        
        Args:
            school_class: Target class
            title: Notification title
            message: Notification message
            sender: User sending the notification
            notification_type: Type of notification
            include_guardians: Whether to include guardians
            tenant: Tenant object
            
        Returns:
            Dict with broadcast results
        """
        try:
            students = Student.objects.filter(
                tenant=tenant,
                current_class=school_class,
                status="ACTIVE"
            ).select_related('user')
            
            results = {
                'students_notified': 0,
                'guardians_notified': 0,
                'total_students': students.count(),
                'errors': []
            }
            
            # Notify each student
            for student in students:
                try:
                    # In-app notification to student
                    if hasattr(student, 'user') and student.user:
                        notification = NotificationService.send_in_app_notification(
                            recipient=student.user,
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            sender=sender,
                            action_url=f"/classes/{school_class.id}/",
                            action_text="View Class",
                            tenant=tenant
                        )
                        if notification:
                            results['students_notified'] += 1
                    
                    # Email to student
                    if student.personal_email:
                        email_result = NotificationService.send_email_notification(
                            recipient=student,
                            subject=title,
                            message=message,
                            sender=sender,
                            tenant=tenant
                        )
                    
                    # Notify guardians if requested
                    if include_guardians:
                        for guardian in student.guardians.all():
                            if guardian.email:
                                guardian_result = NotificationService.send_email_notification(
                                    recipient=guardian.email,
                                    subject=f"Class Announcement: {title}",
                                    message=f"Message for {student.full_name}'s class:\n\n{message}",
                                    sender=sender,
                                    tenant=tenant
                                )
                                if guardian_result.get('success'):
                                    results['guardians_notified'] += 1
                                    
                except Exception as e:
                    results['errors'].append({
                        'student': str(student),
                        'error': str(e)
                    })
                    logger.error(f"Error notifying student {student}: {str(e)}")
            
            # Create audit log
            AuditService.create_audit_entry(
                action='CREATE',
                resource_type='ClassBroadcast',
                user=sender,
                tenant=tenant,
                request=None,
                severity='INFO',
                extra_data={
                    'class_id': str(school_class.id),
                    'class_name': school_class.name,
                    'title': title,
                    'results': results
                }
            )
            
            return {
                'success': True,
                'results': results,
                'message': _('Class broadcast completed successfully')
            }
            
        except Exception as e:
            logger.error(f"Class broadcast error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'results': {'errors': [str(e)]}
            }
    
    # Helper methods
    @staticmethod
    def _get_recipient_email(recipient) -> Optional[str]:
        """Extract email from recipient"""
        if isinstance(recipient, str):
            return recipient
        elif hasattr(recipient, 'email'):
            return recipient.email
        elif hasattr(recipient, 'personal_email'):
            return recipient.personal_email
        return None
    
    @staticmethod
    def _get_recipient_phone(recipient) -> Optional[str]:
        """Extract phone number from recipient"""
        if isinstance(recipient, str):
            return recipient
        elif hasattr(recipient, 'phone'):
            return recipient.phone
        elif hasattr(recipient, 'mobile'):
            return recipient.mobile
        elif hasattr(recipient, 'mobile_primary'):
            return recipient.mobile_primary
        return None
    
    @staticmethod
    def _can_receive_email(user: User) -> bool:
        """Check if user can receive email notifications"""
        try:
            prefs = CommunicationPreference.objects.get(user=user)
            return prefs.email_enabled
        except CommunicationPreference.DoesNotExist:
            return True  # Default to enabled
    
    @staticmethod
    def _can_receive_sms(user: User) -> bool:
        """Check if user can receive SMS notifications"""
        try:
            prefs = CommunicationPreference.objects.get(user=user)
            return prefs.sms_enabled
        except CommunicationPreference.DoesNotExist:
            return True  # Default to enabled
    
    @staticmethod
    def _can_receive_in_app(user: User) -> bool:
        """Check if user can receive in-app notifications"""
        try:
            prefs = CommunicationPreference.objects.get(user=user)
            return prefs.in_app_enabled
        except CommunicationPreference.DoesNotExist:
            return True  # Default to enabled
    
    @staticmethod
    def _get_priority_header(priority: str) -> str:
        """Convert priority to email header value"""
        priority_map = {
            "LOW": "3",
            "MEDIUM": "2",
            "HIGH": "1",
            "URGENT": "1"
        }
        return priority_map.get(priority, "2")
    
    @staticmethod
    def _create_communication_record(
        channel_type: str,
        recipient,
        subject: str,
        content: str,
        sender: Optional[User] = None,
        template_code: Optional[str] = None,
        context: Optional[Dict] = None,
        tenant=None,
        status: str = "DRAFT",
        priority: str = "MEDIUM",
        error_message: str = ""
    ) -> Optional[Communication]:
        """Create communication record in database"""
        try:
            # Get channel
            channel = CommunicationChannel.objects.filter(
                channel_type=channel_type,
                is_active=True
            ).first()
            
            if not channel:
                logger.warning(f"No active channel found for type: {channel_type}")
                return None
            
            # Get template if code provided
            template = None
            if template_code:
                template = CommunicationTemplate.objects.filter(
                    code=template_code,
                    is_active=True,
                    is_approved=True
                ).first()
            
            # Determine recipient information
            recipient_type = None
            recipient_id = None
            external_recipient_email = None
            external_recipient_phone = None
            
            if isinstance(recipient, User):
                recipient_type = NotificationService._get_content_type(recipient)
                recipient_id = recipient.id
            elif isinstance(recipient, Student):
                recipient_type = NotificationService._get_content_type(recipient)
                recipient_id = recipient.id
            elif '@' in str(recipient):  # Email address
                external_recipient_email = str(recipient)
            else:  # Phone number or other
                external_recipient_phone = str(recipient)
            
            # Create communication
            communication = Communication.objects.create(
                tenant=tenant,
                title=subject,
                subject=subject,
                content=content,
                channel=channel,
                template=template,
                sender=sender,
                recipient_type=recipient_type,
                recipient_id=recipient_id,
                external_recipient_email=external_recipient_email,
                external_recipient_phone=external_recipient_phone,
                status=status,
                priority=priority,
                error_message=error_message
            )
            
            return communication
            
        except Exception as e:
            logger.error(f"Error creating communication record: {str(e)}", exc_info=True)
            return None
    
    @staticmethod
    def _get_content_type(obj) -> Optional[ContentType]:
        """Get content type for object"""
        from django.contrib.contenttypes.models import ContentType
        try:
            return ContentType.objects.get_for_model(obj)
        except Exception:
            return None
    
    @staticmethod
    def _get_significant_changes(changes: Dict) -> Dict:
        """Filter significant changes for notification"""
        significant_fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'personal_email', 'mobile_primary', 'status',
            'current_class_id', 'section_id', 'academic_year_id',
            'category', 'blood_group'
        ]
        
        significant = {}
        for field, change_data in changes.items():
            if field in significant_fields:
                significant[field] = change_data
        
        return significant
    
    @staticmethod
    def get_unread_notifications(user: User, limit: int = 20) -> List[Notification]:
        """Get unread notifications for user"""
        return Notification.objects.filter(
            recipient=user,
            is_read=False,
            is_dismissed=False
        ).exclude(
            expires_at__lt=timezone.now()
        ).order_by('-priority', '-created_at')[:limit]
    
    @staticmethod
    def mark_all_as_read(user: User) -> int:
        """Mark all notifications as read for user"""
        updated = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        return updated
    
    @staticmethod
    def get_notification_stats(user: User) -> Dict:
        """Get notification statistics for user"""
        total = Notification.objects.filter(recipient=user).count()
        unread = Notification.objects.filter(
            recipient=user,
            is_read=False,
            is_dismissed=False
        ).exclude(
            expires_at__lt=timezone.now()
        ).count()
        
        by_type = Notification.objects.filter(
            recipient=user
        ).values(
            'notification_type'
        ).annotate(
            count=models.Count('id')
        )
        
        return {
            'total': total,
            'unread': unread,
            'by_type': {item['notification_type']: item['count'] for item in by_type}
        }