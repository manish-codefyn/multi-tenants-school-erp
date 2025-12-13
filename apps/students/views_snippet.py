from django.http import FileResponse, Http404

class DocumentDownloadView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """View to securely download student documents"""
    model = StudentDocument
    permission_required = 'students.view_student'
    
    def get_queryset(self):
        return StudentDocument.objects.filter(tenant=self.request.tenant)
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Ensure file exists
        if not self.object.file:
            raise Http404(_("File not found"))
            
        # Check if user has permission to verify (optional, for stricter access)
        # For now, view_student permission is sufficient as per plan
        
        response = FileResponse(self.object.file)
        response['Content-Disposition'] = f'attachment; filename="{self.object.file_name}"'
        return response
