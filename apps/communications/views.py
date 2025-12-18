import logging
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib import messages

from apps.core.views import (
    BaseView, BaseTemplateView, BaseListView, BaseDetailView, 
    BaseCreateView, BaseUpdateView, BaseDeleteView
)
from .models import (
    CommunicationChannel, CommunicationTemplate, 
    CommunicationCampaign, Communication, Notification
)
from .forms import (
    CommunicationChannelForm, CommunicationTemplateForm, 
    CommunicationCampaignForm, CommunicationComposeForm
)
from apps.core.utils.tenant import get_current_tenant

logger = logging.getLogger(__name__)

# ============================================================================
# DASHBOARD VIEW
# ============================================================================

class CommunicationDashboardView(BaseTemplateView):
    """
    Dashboard for all communications-related stats and quick actions
    """
    template_name = 'communications/dashboard.html'
    permission_required = 'communications.view_dashboard'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.tenant
        
        # Stats summary
        context['total_communications'] = Communication.objects.filter(tenant=tenant).count()
        context['total_sent'] = Communication.objects.filter(tenant=tenant, status='SENT').count()
        context['total_failed'] = Communication.objects.filter(tenant=tenant, status='FAILED').count()
        
        # Channel stats
        context['channels'] = CommunicationChannel.objects.filter(tenant=tenant).annotate(
            comm_count=Count('communications')
        )
        
        # Recent communications
        context['recent_comms'] = Communication.objects.filter(tenant=tenant).order_by('-created_at')[:5]
        
        # Active campaigns
        context['active_campaigns'] = CommunicationCampaign.objects.filter(
            tenant=tenant, status='RUNNING'
        ).count()
        
        # Unread notifications for current user
        if self.request.user.is_authenticated:
            context['unread_notifications'] = Notification.objects.filter(
                recipient=self.request.user, is_read=False
            ).count()
            
        return context

# ============================================================================
# CHANNEL VIEWS
# ============================================================================

class ChannelListView(BaseListView):
    model = CommunicationChannel
    template_name = 'communications/channel/list.html'
    context_object_name = 'channels'
    permission_required = 'communications.view_communicationchannel'
    search_fields = ['name', 'code', 'channel_type']

class ChannelCreateView(BaseCreateView):
    model = CommunicationChannel
    form_class = CommunicationChannelForm
    template_name = 'communications/channel/form.html'
    permission_required = 'communications.add_communicationchannel'
    success_url = reverse_lazy('communications:channel_list')

class ChannelUpdateView(BaseUpdateView):
    model = CommunicationChannel
    form_class = CommunicationChannelForm
    template_name = 'communications/channel/form.html'
    permission_required = 'communications.change_communicationchannel'
    success_url = reverse_lazy('communications:channel_list')

class ChannelDeleteView(BaseDeleteView):
    model = CommunicationChannel
    template_name = 'communications/common/confirm_delete.html'
    permission_required = 'communications.delete_communicationchannel'
    success_url = reverse_lazy('communications:channel_list')

# ============================================================================
# TEMPLATE VIEWS
# ============================================================================

class TemplateListView(BaseListView):
    model = CommunicationTemplate
    template_name = 'communications/template/list.html'
    context_object_name = 'templates'
    permission_required = 'communications.view_communicationtemplate'
    search_fields = ['name', 'code', 'subject']

class TemplateCreateView(BaseCreateView):
    model = CommunicationTemplate
    form_class = CommunicationTemplateForm
    template_name = 'communications/template/form.html'
    permission_required = 'communications.add_communicationtemplate'
    success_url = reverse_lazy('communications:template_list')

class TemplateUpdateView(BaseUpdateView):
    model = CommunicationTemplate
    form_class = CommunicationTemplateForm
    template_name = 'communications/template/form.html'
    permission_required = 'communications.change_communicationtemplate'
    success_url = reverse_lazy('communications:template_list')

class TemplateDeleteView(BaseDeleteView):
    model = CommunicationTemplate
    template_name = 'communications/common/confirm_delete.html'
    permission_required = 'communications.delete_communicationtemplate'
    success_url = reverse_lazy('communications:template_list')

# ============================================================================
# CAMPAIGN VIEWS
# ============================================================================

class CampaignListView(BaseListView):
    model = CommunicationCampaign
    template_name = 'communications/campaign/list.html'
    context_object_name = 'campaigns'
    permission_required = 'communications.view_communicationcampaign'
    search_fields = ['name', 'campaign_type']

class CampaignCreateView(BaseCreateView):
    model = CommunicationCampaign
    form_class = CommunicationCampaignForm
    template_name = 'communications/campaign/form.html'
    permission_required = 'communications.add_communicationcampaign'
    success_url = reverse_lazy('communications:campaign_list')

class CampaignUpdateView(BaseUpdateView):
    model = CommunicationCampaign
    form_class = CommunicationCampaignForm
    template_name = 'communications/campaign/form.html'
    permission_required = 'communications.change_communicationcampaign'
    success_url = reverse_lazy('communications:campaign_list')

class CampaignDeleteView(BaseDeleteView):
    model = CommunicationCampaign
    template_name = 'communications/common/confirm_delete.html'
    permission_required = 'communications.delete_communicationcampaign'
    success_url = reverse_lazy('communications:campaign_list')

# ============================================================================
# INDIVIDUAL COMMUNICATION VIEWS
# ============================================================================

class CommunicationListView(BaseListView):
    model = Communication
    template_name = 'communications/communication/list.html'
    context_object_name = 'communications'
    permission_required = 'communications.view_communication'
    search_fields = ['title', 'subject', 'external_recipient_name', 'external_recipient_email']
    paginate_by = 20

class CommunicationDetailView(BaseDetailView):
    model = Communication
    template_name = 'communications/communication/detail.html'
    context_object_name = 'communication'
    permission_required = 'communications.view_communication'

class CommunicationCreateView(BaseCreateView):
    """
    Compose a new communication
    """
    model = Communication
    form_class = CommunicationComposeForm
    template_name = 'communications/communication/form.html'
    permission_required = 'communications.add_communication'
    success_url = reverse_lazy('communications:communication_list')
    
    def form_valid(self, form):
        form.instance.sender = self.request.user
        return super().form_valid(form)
