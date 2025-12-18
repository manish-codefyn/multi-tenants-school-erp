from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Avg, Max, Min
from django.views import View
from django.db import models
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView, BaseDetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from apps.core.utils.tenant import get_current_tenant
from .models import ExamType, Exam, GradingSystem, Grade, ExamResult, SubjectResult, MarkSheet, ResultStatistics
from .forms import ExamTypeForm, ExamForm, GradingSystemForm, GradeForm
from apps.students.models import Student
from django.template.loader import render_to_string
from django.http import HttpResponse
import io
from xhtml2pdf import pisa

class ExamDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'exams/dashboard.html'
    permission_required = 'exams.view_exam'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = get_current_tenant()
        
        context['total_exams'] = Exam.objects.filter(tenant=tenant).count()
        context['ongoing_exams'] = Exam.objects.filter(tenant=tenant, status='ONGOING').count()
        context['upcoming_exams'] = Exam.objects.filter(tenant=tenant, status='SCHEDULED').count()
        context['draft_exams'] = Exam.objects.filter(tenant=tenant, status='DRAFT').count()
        context['completed_exams'] = Exam.objects.filter(tenant=tenant, status='COMPLETED').count()
        context['exam_types'] = ExamType.objects.filter(tenant=tenant, is_active=True).count()
        
        return context

# ==================== EXAM TYPE ====================

class ExamTypeListView(BaseListView):
    model = ExamType
    template_name = 'exams/exam_type_list.html'
    context_object_name = 'exam_types'
    permission_required = 'exams.view_examtype'
    search_fields = ['name', 'code']
    filter_fields = ['is_active', 'is_final']

class ExamTypeCreateView(BaseCreateView):
    model = ExamType
    form_class = ExamTypeForm
    template_name = 'exams/exam_type_form.html'
    permission_required = 'exams.add_examtype'
    success_url = reverse_lazy('exams:exam_type_list')

class ExamTypeUpdateView(BaseUpdateView):
    model = ExamType
    form_class = ExamTypeForm
    template_name = 'exams/exam_type_form.html'
    permission_required = 'exams.change_examtype'
    success_url = reverse_lazy('exams:exam_type_list')

class ExamTypeDeleteView(BaseDeleteView):
    model = ExamType
    template_name = 'exams/confirm_delete.html'
    permission_required = 'exams.delete_examtype'
    success_url = reverse_lazy('exams:exam_type_list')

# ==================== EXAM ====================

class ExamListView(BaseListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    permission_required = 'exams.view_exam'
    search_fields = ['name', 'code', 'class_name__name']
    filter_fields = ['exam_type', 'status', 'academic_year']

class ExamCreateView(BaseCreateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    permission_required = 'exams.add_exam'
    success_url = reverse_lazy('exams:exam_list')

class ExamUpdateView(BaseUpdateView):
    model = Exam
    form_class = ExamForm
    template_name = 'exams/exam_form.html'
    permission_required = 'exams.change_exam'
    success_url = reverse_lazy('exams:exam_list')

class ExamDeleteView(BaseDeleteView):
    model = Exam
    template_name = 'exams/confirm_delete.html'
    permission_required = 'exams.delete_exam'
    success_url = reverse_lazy('exams:exam_list')

# ==================== GRADING SYSTEM ====================

class GradingSystemListView(BaseListView):
    model = GradingSystem
    template_name = 'exams/grading_system_list.html'
    context_object_name = 'grading_systems'
    permission_required = 'exams.view_gradingsystem'
    search_fields = ['name', 'code']
    filter_fields = ['is_active', 'is_default']

class GradingSystemCreateView(BaseCreateView):
    model = GradingSystem
    form_class = GradingSystemForm
    template_name = 'exams/grading_system_form.html'
    permission_required = 'exams.add_gradingsystem'
    success_url = reverse_lazy('exams:grading_system_list')

class GradingSystemUpdateView(BaseUpdateView):
    model = GradingSystem
    form_class = GradingSystemForm
    template_name = 'exams/grading_system_form.html'
    permission_required = 'exams.change_gradingsystem'
    success_url = reverse_lazy('exams:grading_system_list')

class GradingSystemDeleteView(BaseDeleteView):
    model = GradingSystem
    template_name = 'exams/confirm_delete.html'
    permission_required = 'exams.delete_gradingsystem'
    success_url = reverse_lazy('exams:grading_system_list')

# ==================== EXAM RESULTS ====================

class ExamResultListView(BaseListView):
    model = ExamResult
    template_name = 'exams/result_list.html'
    context_object_name = 'results'
    permission_required = 'exams.view_examresult'
    search_fields = ['student__first_name', 'student__last_name', 'exam__name']
    filter_fields = ['exam', 'result_status', 'is_published']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Exam
        context['exams'] = Exam.objects.filter(tenant=get_current_tenant())
        return context

class ExamResultDetailView(BaseDetailView):
    model = ExamResult
    template_name = 'exams/result_detail.html'
    context_object_name = 'result'
    permission_required = 'exams.view_examresult'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context['subject_results'] = self.object.subject_results.all().select_related('exam_subject__subject')
        return context

class MarkSheetVerificationView(TemplateView):
    template_name = 'exams/verify_result.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        code = self.request.GET.get('code')
        if code:
            context['mark_sheet'] = MarkSheet.objects.filter(verification_code=code).first()
            if context['mark_sheet']:
                context['result'] = context['mark_sheet'].exam_result
                context['verified'] = True
            else:
                context['error'] = _("Invalid verification code")
        return context

class GenerateResultsView(PermissionRequiredMixin, View):
    permission_required = 'exams.add_examresult'

    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        students = Student.objects.filter(current_class=exam.class_name, is_active=True)
        
        results_count = 0
        for student in students:
            # Create or get ExamResult
            result, created = ExamResult.objects.get_or_create(
                exam=exam,
                student=student,
                defaults={'total_max_marks': exam.total_marks}
            )
            
            # Calculate total marks from subject results
            subject_marks = SubjectResult.objects.filter(exam_result=result).aggregate(
                total=models.Sum('total_marks_obtained')
            )['total'] or 0
            
            result.total_marks_obtained = subject_marks
            result.total_max_marks = exam.total_marks
            result.save() # This triggers rank update and grade determination
            results_count += 1
            
        # Update statistics
        stats, created = ResultStatistics.objects.get_or_create(exam=exam)
        stats.calculate_statistics()
        
        messages.success(request, _(f"Successfully generated/updated results for {results_count} students."))
        return redirect('exams:result_list')


class MarkSheetPDFView(PermissionRequiredMixin, View):
    """
    Generate and download mark sheet as PDF
    """
    permission_required = 'exams.view_examresult'

    def get(self, request, pk):
        result = get_object_or_404(ExamResult, pk=pk)
        
        # Prepare context
        context = {
            'result': result,
            'subject_results': SubjectResult.objects.filter(exam_result=result),
            'tenant': get_current_tenant(),
            'request': request,
        }
        
        # Render HTML to string
        html = render_to_string('exams/pdf/mark_sheet_pdf.html', context)
        
        # Create a file-like object to receive PDF data
        result_pdf = io.BytesIO()
        
        # Create PDF
        pisa_status = pisa.CreatePDF(html, dest=result_pdf)
        
        # Return error if something went wrong
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)
        
        # Set response headers
        response = HttpResponse(result_pdf.getvalue(), content_type='application/pdf')
        filename = f"Mark_Sheet_{result.student.roll_number}_{result.exam.name}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
