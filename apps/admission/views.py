from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, FormView, DetailView, ListView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import AdmissionCycle, AdmissionProgram, OnlineApplication
from .forms import AdmissionApplicationForm, AdmissionStatusCheckForm
from apps.core.utils.tenant import get_current_tenant


class AdmissionLandingView(TemplateView):
    template_name = 'admission/public/landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context['open_cycles'] = AdmissionCycle.objects.filter(
            status='ACTIVE',
            start_date__lte=now,
            end_date__gte=now,
            is_active=True
        )
        return context


class AdmissionApplyView(CreateView):
    model = OnlineApplication
    form_class = AdmissionApplicationForm
    template_name = 'admission/public/apply.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        tenant = getattr(self.request, 'tenant', None)
        kwargs['tenant'] = tenant
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        # Get cycle from URL parameter
        cycle_id = self.request.GET.get('cycle')
        tenant = getattr(self.request, 'tenant', None)
        
        if cycle_id and tenant:
            try:
                cycle = AdmissionCycle.objects.get(
                    id=cycle_id,
                    tenant=tenant,
                    is_active=True
                )
                initial['admission_cycle'] = cycle
            except AdmissionCycle.DoesNotExist:
                pass
        
        return initial
    
    def form_valid(self, form):
        # Make sure tenant is set
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            form.instance.tenant = tenant
        
        # Handle the admission cycle from GET parameter
        if not form.instance.admission_cycle_id:
            cycle_id = self.request.GET.get('cycle')
            if cycle_id and tenant:
                try:
                    cycle = AdmissionCycle.objects.get(
                        id=cycle_id,
                        tenant=tenant
                    )
                    form.instance.admission_cycle = cycle
                except AdmissionCycle.DoesNotExist:
                    pass
        
        # Set created_by if user is authenticated
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        
        response = super().form_valid(form)
        
        # Auto-login if user was created and not currently logged in
        if not self.request.user.is_authenticated and self.object.created_by:
            from django.contrib.auth import login
            # We need to specify the backend, or let Django find the default
            login(self.request, self.object.created_by, backend='django.contrib.auth.backends.ModelBackend')
            
        messages.success(
            self.request,
            f'Application submitted! Your application number: {self.object.application_number}'
        )
        return response

class AdmissionSuccessView(TemplateView):
    template_name = 'admission/public/success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = get_object_or_404(
            OnlineApplication, 
            application_number=self.kwargs.get('application_number')
        )
        return context

class AdmissionStatusView(FormView):
    template_name = 'admission/public/status.html'
    form_class = AdmissionStatusCheckForm
    
    def form_valid(self, form):
        app_num = form.cleaned_data['application_number']
        dob = form.cleaned_data['date_of_birth']
        
        try:
            application = OnlineApplication.objects.get(
                application_number=app_num,
                date_of_birth=dob
            )
            return render(self.request, self.template_name, {
                'form': form,
                'application': application,
                'status_checked': True
            })
        except OnlineApplication.DoesNotExist:
            messages.error(self.request, _("Application not found or details incorrect."))
            return self.render_to_response(self.get_context_data(form=form))

# ==================== STAFF VIEWS ====================

class AdmissionListView(LoginRequiredMixin, ListView):
    model = OnlineApplication
    template_name = 'admission/staff/list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by tenant if applicable
        if hasattr(self.request, 'tenant'):
            queryset = queryset.filter(tenant=self.request.tenant)
            
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Search by name or application number
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(application_number__icontains=search)
            )
        return queryset

class AdmissionDetailView(LoginRequiredMixin, DetailView):
    model = OnlineApplication
    template_name = 'admission/staff/detail.html'
    context_object_name = 'application'

class AdmissionUpdateView(LoginRequiredMixin, UpdateView):
    model = OnlineApplication
    fields = ['status', 'review_date', 'decision_date', 'comments']
    template_name = 'admission/staff/form.html'
    success_url = reverse_lazy('admission:staff_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Application updated successfully."))
        return response

class AdmissionDeleteView(LoginRequiredMixin, DeleteView):
    model = OnlineApplication
    template_name = 'admission/staff/confirm_delete.html'
    success_url = reverse_lazy('admission:staff_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _("Application deleted successfully."))
        return super().delete(request, *args, **kwargs)

# ==================== ADMISSION CYCLE MANAGEMENT ====================

class AdmissionCycleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AdmissionCycle
    template_name = 'admission/staff/cycle_list.html'
    context_object_name = 'cycles'
    permission_required = 'admission.view_admissioncycle'

class AdmissionCycleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = AdmissionCycle
    fields = ['name', 'academic_year', 'code', 'school_level', 'start_date', 'end_date', 'merit_list_date', 'admission_end_date', 'status', 'max_applications', 'application_fee', 'is_active', 'instructions', 'terms_conditions']
    template_name = 'admission/staff/cycle_form.html'
    success_url = reverse_lazy('admission:cycle_list')
    permission_required = 'admission.add_admissioncycle'

    def form_valid(self, form):
        messages.success(self.request, "Admission Cycle created successfully.")
        return super().form_valid(form)

class AdmissionCycleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = AdmissionCycle
    fields = ['name', 'academic_year', 'code', 'school_level', 'start_date', 'end_date', 'merit_list_date', 'admission_end_date', 'status', 'max_applications', 'application_fee', 'is_active', 'instructions', 'terms_conditions']
    template_name = 'admission/staff/cycle_form.html'
    success_url = reverse_lazy('admission:cycle_list')
    permission_required = 'admission.change_admissioncycle'

    def form_valid(self, form):
        messages.success(self.request, "Admission Cycle updated successfully.")
        return super().form_valid(form)

class AdmissionCycleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = AdmissionCycle
    template_name = 'admission/staff/confirm_delete.html'
    success_url = reverse_lazy('admission:cycle_list')
    permission_required = 'admission.delete_admissioncycle'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Admission Cycle deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== ADMISSION PROGRAM MANAGEMENT ====================

class AdmissionProgramListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AdmissionProgram
    template_name = 'admission/staff/program_list.html'
    context_object_name = 'programs'
    permission_required = 'admission.view_admissionprogram'

class AdmissionProgramCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = AdmissionProgram
    fields = ['admission_cycle', 'program_name', 'program_type', 'class_grade', 'stream', 'total_seats', 'general_seats', 'reserved_seats', 'min_age_years', 'min_age_months', 'max_age_years', 'max_age_months', 'min_qualification', 'min_percentage', 'entrance_exam_required', 'interview_required', 'eligibility_criteria', 'application_fee', 'tuition_fee', 'is_active']
    template_name = 'admission/staff/program_form.html'
    success_url = reverse_lazy('admission:program_list')
    permission_required = 'admission.add_admissionprogram'

    def form_valid(self, form):
        messages.success(self.request, "Admission Program created successfully.")
        return super().form_valid(form)

class AdmissionProgramUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = AdmissionProgram
    fields = ['admission_cycle', 'program_name', 'program_type', 'class_grade', 'stream', 'total_seats', 'general_seats', 'reserved_seats', 'min_age_years', 'min_age_months', 'max_age_years', 'max_age_months', 'min_qualification', 'min_percentage', 'entrance_exam_required', 'interview_required', 'eligibility_criteria', 'application_fee', 'tuition_fee', 'is_active']
    template_name = 'admission/staff/program_form.html'
    success_url = reverse_lazy('admission:program_list')
    permission_required = 'admission.change_admissionprogram'

    def form_valid(self, form):
        messages.success(self.request, "Admission Program updated successfully.")
        return super().form_valid(form)

class AdmissionProgramDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = AdmissionProgram
    template_name = 'admission/staff/confirm_delete.html'
    success_url = reverse_lazy('admission:program_list')
    permission_required = 'admission.delete_admissionprogram'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Admission Program deleted successfully.")
        return super().delete(request, *args, **kwargs)

# ==================== MULTI-STEP ADMISSION VIEWS ====================

from .forms import (
    ApplicationStep1Form, ApplicationStep2Form, ApplicationStep3Form, 
    ApplicationDocumentForm
)

class AdmissionRegistrationView(CreateView):
    """Step 1: Registration & Personal Information"""
    model = OnlineApplication
    form_class = ApplicationStep1Form
    template_name = 'admission/public/step1_registration.html'
    
    def get_initial(self):
        initial = super().get_initial()
        cycle_id = self.request.GET.get('cycle')
        program_id = self.request.GET.get('program')
        
        if cycle_id:
            initial['admission_cycle'] = get_object_or_404(AdmissionCycle, id=cycle_id)
        if program_id:
            initial['program'] = get_object_or_404(AdmissionProgram, id=program_id)
            
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set tenant on instance before validation
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            form.instance.tenant = tenant
            
        # Set cycle and program from GET parameters (for initial load) or POST (if passed as hidden)
        # Note: We use the ID fields directly to avoid DB lookups if not needed
        cycle_id = self.request.GET.get('cycle')
        program_id = self.request.GET.get('program')
        
        if cycle_id:
            form.instance.admission_cycle_id = cycle_id
        if program_id:
            form.instance.program_id = program_id
            
        return form

    def form_valid(self, form):
        # Set tenant
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            form.instance.tenant = tenant
            
        # Set cycle and program from GET if not in form (though they should be handled by context/hidden fields)
        cycle_id = self.request.GET.get('cycle')
        program_id = self.request.GET.get('program')
        
        if cycle_id:
            form.instance.admission_cycle_id = cycle_id
        if program_id:
            form.instance.program_id = program_id
            
        # Set status to DRAFT
        form.instance.status = 'DRAFT'
        
        response = super().form_valid(form)
        
        # Store application ID in session
        self.request.session['application_id'] = str(self.object.id)
        return response

    def get_success_url(self):
        return reverse('admission:apply_step2', kwargs={'pk': self.object.pk})


class AdmissionContactView(UpdateView):
    """Step 2: Contact Information"""
    model = OnlineApplication
    form_class = ApplicationStep2Form
    template_name = 'admission/public/step2_contact.html'
    
    def get_queryset(self):
        # Ensure user can only edit their own application or session-based application
        qs = super().get_queryset()
        # Add security check here if needed (e.g. check session ID matches)
        return qs

    def get_success_url(self):
        return reverse('admission:apply_step3', kwargs={'pk': self.object.pk})


class AdmissionAcademicView(UpdateView):
    """Step 3: Academic Information"""
    model = OnlineApplication
    form_class = ApplicationStep3Form
    template_name = 'admission/public/step3_academic.html'

    def get_success_url(self):
        return reverse('admission:apply_step4', kwargs={'pk': self.object.pk})


class AdmissionDocumentView(DetailView):
    """Step 4: Document Upload"""
    model = OnlineApplication
    template_name = 'admission/public/step4_documents.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_form'] = ApplicationDocumentForm(application=self.object)
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ApplicationDocumentForm(request.POST, request.FILES, application=self.object)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Document uploaded successfully.")
            return redirect('admission:apply_step4', pk=self.object.pk)
        
        context = self.get_context_data()
        context['document_form'] = form
        return self.render_to_response(context)


class AdmissionReviewView(DetailView):
    """Step 5: Review & Submit"""
    model = OnlineApplication
    template_name = 'admission/public/step5_review.html'
    
    def post(self, request, *args, **kwargs):
        application = self.get_object()
        
        if application.status == 'DRAFT':
            application.submit_application()
            messages.success(request, f"Application submitted successfully! Your Application Number is {application.application_number}")
            return redirect('admission:apply_success', application_number=application.application_number)
            
        return redirect('admission:apply_success', application_number=application.application_number)
