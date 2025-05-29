"""
Email notification service for sending external communications.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import base64

from jinja2 import Environment, DictLoader
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.core.telemetry import monitoring

settings = get_settings()
logger = get_logger(__name__)


class EmailNotificationService:
    """Service for sending email notifications."""
    
    def __init__(self):
        self.sendgrid_client = None
        self.smtp_config = None
        self.template_env = None
        self._setup_email_client()
        self._setup_templates()
    
    def _setup_email_client(self):
        """Setup email client (SendGrid or SMTP)."""
        if settings.SENDGRID_API_KEY:
            try:
                self.sendgrid_client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
                logger.info("SendGrid client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}")
        
        # Fallback to SMTP if configured
        elif all([
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD
        ]):
            self.smtp_config = {
                "host": settings.SMTP_HOST,
                "port": settings.SMTP_PORT,
                "username": settings.SMTP_USERNAME,
                "password": settings.SMTP_PASSWORD,
                "use_tls": getattr(settings, 'SMTP_USE_TLS', True)
            }
            logger.info("SMTP client configured")
        else:
            logger.warning("No email service configured")
    
    def _setup_templates(self):
        """Setup email templates."""
        templates = {
            'trip_invitation': '''
            <html>
            <body>
                <h2>You're Invited to Join a Trip!</h2>
                <p>Hello!</p>
                <p>You've been invited to join the trip "<strong>{{ trip_name }}</strong>" to {{ destination }}.</p>
                
                <div style="background: #f5f5f5; padding: 20px; margin: 20px 0;">
                    <h3>Trip Details:</h3>
                    <ul>
                        <li><strong>Destination:</strong> {{ destination }}</li>
                        <li><strong>Dates:</strong> {{ start_date }} to {{ end_date }}</li>
                        <li><strong>Organizer:</strong> {{ organizer_name }}</li>
                        {% if trip_description %}
                        <li><strong>Description:</strong> {{ trip_description }}</li>
                        {% endif %}
                    </ul>
                </div>
                
                <p>Click the link below to accept the invitation and start planning:</p>
                <p><a href="{{ invitation_link }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Accept Invitation</a></p>
                
                <p>Best regards,<br>The Pathfinder Team</p>
            </body>
            </html>
            ''',
            
            'itinerary_ready': '''
            <html>
            <body>
                <h2>Your Trip Itinerary is Ready!</h2>
                <p>Hello!</p>
                <p>Great news! The AI-generated itinerary for your trip "<strong>{{ trip_name }}</strong>" is now ready for review.</p>
                
                <div style="background: #f5f5f5; padding: 20px; margin: 20px 0;">
                    <h3>Trip Summary:</h3>
                    <ul>
                        <li><strong>Destination:</strong> {{ destination }}</li>
                        <li><strong>Duration:</strong> {{ duration_days }} days</li>
                        <li><strong>Activities Planned:</strong> {{ activity_count }}</li>
                        <li><strong>Estimated Budget:</strong> ${{ estimated_budget }}</li>
                    </ul>
                </div>
                
                <p>Click below to view and customize your itinerary:</p>
                <p><a href="{{ itinerary_link }}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Itinerary</a></p>
                
                <p>You can make changes, add preferences, and collaborate with other families to make this the perfect trip for everyone!</p>
                
                <p>Happy travels,<br>The Pathfinder Team</p>
            </body>
            </html>
            ''',
            
            'trip_reminder': '''
            <html>
            <body>
                <h2>Trip Reminder: {{ trip_name }}</h2>
                <p>Hello!</p>
                <p>This is a friendly reminder about your upcoming trip to <strong>{{ destination }}</strong>.</p>
                
                <div style="background: #fff3cd; padding: 20px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h3>Trip Details:</h3>
                    <ul>
                        <li><strong>Departure:</strong> {{ start_date }}</li>
                        <li><strong>Days Until Trip:</strong> {{ days_until }}</li>
                        <li><strong>Completion Status:</strong> {{ completion_percentage }}%</li>
                    </ul>
                </div>
                
                {% if action_items %}
                <h3>Action Items:</h3>
                <ul>
                {% for item in action_items %}
                    <li>{{ item }}</li>
                {% endfor %}
                </ul>
                {% endif %}
                
                <p><a href="{{ trip_link }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Trip Details</a></p>
                
                <p>Safe travels,<br>The Pathfinder Team</p>
            </body>
            </html>
            ''',
            
            'cost_alert': '''
            <html>
            <body>
                <h2>Cost Alert: Budget Threshold Reached</h2>
                <p>Hello Administrator,</p>
                <p>This is an automated alert regarding budget usage for the Pathfinder platform.</p>
                
                <div style="background: #f8d7da; padding: 20px; margin: 20px 0; border-left: 4px solid #dc3545;">
                    <h3>Alert Details:</h3>
                    <ul>
                        <li><strong>Service:</strong> {{ service }}</li>
                        <li><strong>Usage:</strong> {{ usage_percentage }}% of limit</li>
                        <li><strong>Current Usage:</strong> {{ current_usage }}</li>
                        <li><strong>Limit:</strong> {{ limit }}</li>
                        <li><strong>Severity:</strong> {{ severity }}</li>
                        <li><strong>Time:</strong> {{ timestamp }}</li>
                    </ul>
                </div>
                
                <p>Please review the usage and take appropriate action if necessary.</p>
                
                <p>Pathfinder Monitoring System</p>
            </body>
            </html>
            ''',
            
            'family_invitation': '''
            <html>
            <body>
                <h2>You're Invited to Join a Family on Pathfinder!</h2>
                <p>Hello!</p>
                <p><strong>{{ inviter_name }}</strong> has invited you to join the "<strong>{{ family_name }}</strong>" family on Pathfinder.</p>
                
                {% if message %}
                <div style="background: #e7f3ff; padding: 15px; margin: 20px 0; border-left: 4px solid #007bff;">
                    <h4>Personal Message:</h4>
                    <p style="font-style: italic;">"{{ message }}"</p>
                </div>
                {% endif %}
                
                <div style="background: #f5f5f5; padding: 20px; margin: 20px 0;">
                    <h3>About Family Groups on Pathfinder:</h3>
                    <ul>
                        <li>Plan amazing trips together with your family</li>
                        <li>Get AI-powered itinerary suggestions tailored to your family's preferences</li>
                        <li>Collaborate on trip planning with real-time updates</li>
                        <li>Keep track of everyone's dietary restrictions and accessibility needs</li>
                        <li>Share memories and photos from your adventures</li>
                    </ul>
                </div>
                
                <p>Click the link below to accept the invitation and start planning your next family adventure:</p>
                <p><a href="{{ invitation_link }}" style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Accept Family Invitation</a></p>
                
                <p style="color: #666; font-size: 14px;">This invitation will expire in 7 days. If you don't have a Pathfinder account yet, you'll be guided through creating one during the acceptance process.</p>
                
                <p>Best regards,<br>The Pathfinder Team</p>
            </body>
            </html>
            '''
        }
        
        self.template_env = Environment(loader=DictLoader(templates))
    
    async def send_trip_invitation(
        self,
        recipient_email: str,
        recipient_name: str,
        trip_data: Dict[str, Any],
        organizer_name: str,
        invitation_link: str
    ) -> bool:
        """Send trip invitation email."""
        
        try:
            # Track the operation
            await monitoring.track_ai_operation("email_invitation", 0)
            
            template = self.template_env.get_template('trip_invitation')
            html_content = template.render(
                trip_name=trip_data.get('name', 'Unnamed Trip'),
                destination=trip_data.get('destination', 'Unknown'),
                start_date=trip_data.get('start_date', 'TBD'),
                end_date=trip_data.get('end_date', 'TBD'),
                organizer_name=organizer_name,
                trip_description=trip_data.get('description', ''),
                invitation_link=invitation_link
            )
            
            subject = f"Trip Invitation: {trip_data.get('name', 'Unnamed Trip')}"
            
            success = await self._send_email(
                to_email=recipient_email,
                to_name=recipient_name,
                subject=subject,
                html_content=html_content,
                email_type="trip_invitation"
            )
            
            if success:
                logger.info(f"Trip invitation sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send trip invitation: {e}")
            return False
    
    async def send_family_invitation(
        self,
        recipient_email: str,
        family_name: str,
        inviter_name: str,
        invitation_link: str,
        message: Optional[str] = None
    ) -> bool:
        """Send family invitation email."""
        
        try:
            # Track the operation (fixed to not use await)
            monitoring.track_ai_operation("email_family_invitation", 0)
            
            if self.template_env:
                template = self.template_env.get_template('family_invitation')
                html_content = template.render(
                    family_name=family_name,
                    inviter_name=inviter_name,
                    invitation_link=invitation_link,
                    message=message
                )
                
                subject = f"Family Invitation: Join {family_name} on Pathfinder"
                
                success = await self._send_email(
                    to_email=recipient_email,
                    to_name="",  # We may not have the recipient's name yet
                    subject=subject,
                    html_content=html_content,
                    email_type="family_invitation"
                )
                
                if success:
                    logger.info(f"Family invitation sent to {recipient_email} for family {family_name}")
                
                return success
            else:
                logger.error("Email templates not initialized")
                return False
            
        except Exception as e:
            logger.error(f"Failed to send family invitation: {e}")
            return False

    async def send_itinerary_ready_notification(
        self,
        recipient_email: str,
        recipient_name: str,
        trip_data: Dict[str, Any],
        itinerary_summary: Dict[str, Any],
        itinerary_link: str
    ) -> bool:
        """Send notification when itinerary is ready."""
        
        try:
            await monitoring.track_ai_operation("email_itinerary_ready", 0)
            
            template = self.template_env.get_template('itinerary_ready')
            html_content = template.render(
                trip_name=trip_data.get('name', 'Your Trip'),
                destination=trip_data.get('destination', 'Unknown'),
                duration_days=itinerary_summary.get('duration_days', 'Unknown'),
                activity_count=itinerary_summary.get('activity_count', 0),
                estimated_budget=itinerary_summary.get('estimated_budget', 0),
                itinerary_link=itinerary_link
            )
            
            subject = f"Itinerary Ready: {trip_data.get('name', 'Your Trip')}"
            
            success = await self._send_email(
                to_email=recipient_email,
                to_name=recipient_name,
                subject=subject,
                html_content=html_content,
                email_type="itinerary_ready"
            )
            
            if success:
                logger.info(f"Itinerary ready notification sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send itinerary ready notification: {e}")
            return False
    
    async def send_trip_reminder(
        self,
        recipient_email: str,
        recipient_name: str,
        trip_data: Dict[str, Any],
        days_until: int,
        completion_percentage: float,
        action_items: List[str],
        trip_link: str
    ) -> bool:
        """Send trip reminder email."""
        
        try:
            await monitoring.track_ai_operation("email_trip_reminder", 0)
            
            template = self.template_env.get_template('trip_reminder')
            html_content = template.render(
                trip_name=trip_data.get('name', 'Your Trip'),
                destination=trip_data.get('destination', 'Unknown'),
                start_date=trip_data.get('start_date', 'TBD'),
                days_until=days_until,
                completion_percentage=int(completion_percentage),
                action_items=action_items,
                trip_link=trip_link
            )
            
            subject = f"Trip Reminder: {trip_data.get('name', 'Your Trip')} - {days_until} days to go!"
            
            success = await self._send_email(
                to_email=recipient_email,
                to_name=recipient_name,
                subject=subject,
                html_content=html_content,
                email_type="trip_reminder"
            )
            
            if success:
                logger.info(f"Trip reminder sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send trip reminder: {e}")
            return False
    
    async def send_cost_alert_email(
        self,
        admin_emails: List[str],
        alert_data: Dict[str, Any]
    ) -> bool:
        """Send cost alert email to administrators."""
        
        try:
            await monitoring.track_ai_operation("email_cost_alert", 0)
            
            template = self.template_env.get_template('cost_alert')
            html_content = template.render(
                service=alert_data.get('service', 'Unknown'),
                usage_percentage=f"{alert_data.get('usage_percentage', 0):.1f}",
                current_usage=alert_data.get('current_usage', 0),
                limit=alert_data.get('limit', 0),
                severity=alert_data.get('severity', 'medium').upper(),
                timestamp=alert_data.get('timestamp', datetime.now().isoformat())
            )
            
            subject = f"ALERT: {alert_data.get('service', 'Service')} Budget Threshold Reached"
            
            success_count = 0
            for admin_email in admin_emails:
                success = await self._send_email(
                    to_email=admin_email,
                    to_name="Administrator",
                    subject=subject,
                    html_content=html_content,
                    email_type="cost_alert"
                )
                if success:
                    success_count += 1
            
            logger.info(f"Cost alert sent to {success_count}/{len(admin_emails)} administrators")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send cost alert email: {e}")
            return False
    
    async def send_email_with_attachment(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        html_content: str,
        attachment_data: bytes,
        attachment_filename: str,
        attachment_type: str = "application/octet-stream"
    ) -> bool:
        """Send email with attachment (PDF, Excel, etc.)."""
        
        try:
            await monitoring.track_ai_operation("email_with_attachment", 0)
            
            if self.sendgrid_client:
                return await self._send_sendgrid_email_with_attachment(
                    recipient_email,
                    recipient_name,
                    subject,
                    html_content,
                    attachment_data,
                    attachment_filename,
                    attachment_type
                )
            elif self.smtp_config:
                return await self._send_smtp_email_with_attachment(
                    recipient_email,
                    recipient_name,
                    subject,
                    html_content,
                    attachment_data,
                    attachment_filename,
                    attachment_type
                )
            else:
                logger.error("No email service configured for attachment sending")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email with attachment: {e}")
            return False
    
    async def _send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        email_type: str = "general"
    ) -> bool:
        """Send email using configured service."""
        
        try:
            if self.sendgrid_client:
                return await self._send_sendgrid_email(to_email, to_name, subject, html_content)
            elif self.smtp_config:
                return await self._send_smtp_email(to_email, to_name, subject, html_content)
            else:
                logger.error(f"No email service configured for {email_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send {email_type} email: {e}")
            return False
    
    async def _send_sendgrid_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str
    ) -> bool:
        """Send email using SendGrid."""
        
        try:
            from_email = settings.FROM_EMAIL or "noreply@pathfinder.com"
            from_name = settings.FROM_NAME or "Pathfinder"
            
            message = Mail(
                from_email=(from_email, from_name),
                to_emails=[(to_email, to_name)],
                subject=subject,
                html_content=html_content
            )
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid send error: {e}")
            return False
    
    async def _send_smtp_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str
    ) -> bool:
        """Send email using SMTP."""
        
        try:
            from_email = settings.FROM_EMAIL or "noreply@pathfinder.com"
            from_name = settings.FROM_NAME or "Pathfinder"
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = f"{to_name} <{to_email}>"
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return False
    
    async def _send_sendgrid_email_with_attachment(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        attachment_data: bytes,
        attachment_filename: str,
        attachment_type: str
    ) -> bool:
        """Send email with attachment using SendGrid."""
        
        try:
            from_email = settings.FROM_EMAIL or "noreply@pathfinder.com"
            from_name = settings.FROM_NAME or "Pathfinder"
            
            message = Mail(
                from_email=(from_email, from_name),
                to_emails=[(to_email, to_name)],
                subject=subject,
                html_content=html_content
            )
            
            # Add attachment
            encoded_file = base64.b64encode(attachment_data).decode()
            
            attachment = Attachment(
                FileContent(encoded_file),
                FileName(attachment_filename),
                FileType(attachment_type),
                Disposition('attachment')
            )
            
            message.attachment = attachment
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                return True
            else:
                logger.error(f"SendGrid attachment error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid attachment send error: {e}")
            return False
    
    async def _send_smtp_email_with_attachment(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        attachment_data: bytes,
        attachment_filename: str,
        attachment_type: str
    ) -> bool:
        """Send email with attachment using SMTP."""
        
        try:
            from_email = settings.FROM_EMAIL or "noreply@pathfinder.com"
            from_name = settings.FROM_NAME or "Pathfinder"
            
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = f"{to_name} <{to_email}>"
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachment
            attachment_part = MIMEBase('application', 'octet-stream')
            attachment_part.set_payload(attachment_data)
            encoders.encode_base64(attachment_part)
            attachment_part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment_filename}'
            )
            msg.attach(attachment_part)
            
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"SMTP attachment send error: {e}")
            return False
    
    async def send_family_invitation(
        self,
        recipient_email: str,
        family_name: str,
        inviter_name: str,
        invitation_link: str,
        message: Optional[str] = None
    ) -> bool:
        """Send family invitation email."""
        
        try:
            # Track the operation
            await monitoring.track_ai_operation("email_family_invitation", 0)
            
            template = self.template_env.get_template('family_invitation')
            html_content = template.render(
                family_name=family_name,
                inviter_name=inviter_name,
                invitation_link=invitation_link,
                message=message
            )
            
            subject = f"Family Invitation: Join {family_name} on Pathfinder"
            
            success = await self._send_email(
                to_email=recipient_email,
                to_name="",  # We may not have the recipient's name yet
                subject=subject,
                html_content=html_content,
                email_type="family_invitation"
            )
            
            if success:
                logger.info(f"Family invitation sent to {recipient_email} for family {family_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send family invitation: {e}")
            return False


# Global email service instance
email_service = EmailNotificationService()
