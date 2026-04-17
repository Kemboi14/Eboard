from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.views.decorators.http import require_POST

from .models import AccessibilityAudit, AccessibilityIssue, AccessibilityRemediation


# ─── Accessibility Audit Views ─────────────────────────────────────────────────

class AccessibilityAuditListView(LoginRequiredMixin, ListView):
    """List all accessibility audits"""
    model = AccessibilityAudit
    template_name = 'accessibility/audits.html'
    context_object_name = 'audits'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        wcag_level = self.request.GET.get('wcag_level')
        
        if status:
            queryset = queryset.filter(status=status)
        if wcag_level:
            queryset = queryset.filter(wcag_level=wcag_level)
        return queryset


class AccessibilityAuditDetailView(LoginRequiredMixin, DetailView):
    """View accessibility audit details"""
    model = AccessibilityAudit
    template_name = 'accessibility/audit_detail.html'
    context_object_name = 'audit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        audit = self.object
        context['issues'] = audit.issues.all()
        context['can_edit'] = self.request.user.role in ['it_administrator', 'compliance_officer']
        return context


class AccessibilityAuditCreateView(LoginRequiredMixin, CreateView):
    """Create a new accessibility audit"""
    model = AccessibilityAudit
    template_name = 'accessibility/audit_form.html'
    fields = ['title', 'description', 'wcag_level', 'target_url', 'target_page', 'audit_method', 'tools_used', 'scheduled_date']
    success_url = reverse_lazy('accessibility:audits')
    
    def form_valid(self, form):
        form.instance.audited_by = self.request.user
        form.instance.status = 'pending'
        messages.success(self.request, 'Accessibility audit created successfully.')
        return super().form_valid(form)


@login_required
@require_POST
def start_accessibility_audit(request, pk):
    """Start an accessibility audit"""
    audit = get_object_or_404(AccessibilityAudit, pk=pk)
    
    if audit.status != 'pending':
        messages.error(request, 'Audit is not in pending status.')
        return redirect('accessibility:audit_detail', pk=pk)
    
    audit.status = 'in_progress'
    audit.save()
    
    messages.success(request, 'Audit started successfully.')
    return redirect('accessibility:audit_detail', pk=pk)


@login_required
@require_POST
def complete_accessibility_audit(request, pk):
    """Complete an accessibility audit"""
    audit = get_object_or_404(AccessibilityAudit, pk=pk)
    
    if audit.status != 'in_progress':
        messages.error(request, 'Audit is not in progress.')
        return redirect('accessibility:audit_detail', pk=pk)
    
    # Calculate compliance score
    issues = audit.issues.all()
    total_issues = issues.count()
    
    if total_issues > 0:
        critical_issues = issues.filter(severity='critical').count()
        serious_issues = issues.filter(severity='serious').count()
        moderate_issues = issues.filter(severity='moderate').count()
        minor_issues = issues.filter(severity='minor').count()
        
        # Calculate a simple compliance score (inverse of issue severity)
        max_score = total_issues * 4  # 4 points per issue max
        actual_score = total_issues * 4 - (critical_issues * 4) - (serious_issues * 3) - (moderate_issues * 2) - (minor_issues * 1)
        compliance_score = int((actual_score / max_score) * 100) if max_score > 0 else 0
    else:
        compliance_score = 100
    
    audit.status = 'completed'
    audit.completed_at = timezone.now()
    audit.compliance_score = compliance_score
    audit.total_issues = total_issues
    audit.save()
    
    messages.success(request, f'Audit completed successfully. Compliance score: {compliance_score}%')
    return redirect('accessibility:audit_detail', pk=pk)


# ─── Accessibility Issue Views ────────────────────────────────────────────────

class AccessibilityIssueListView(LoginRequiredMixin, ListView):
    """List all accessibility issues"""
    model = AccessibilityIssue
    template_name = 'accessibility/issues.html'
    context_object_name = 'issues'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        audit_id = self.request.GET.get('audit')
        severity = self.request.GET.get('severity')
        status = self.request.GET.get('status')
        
        if audit_id:
            queryset = queryset.filter(audit_id=audit_id)
        if severity:
            queryset = queryset.filter(severity=severity)
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class AccessibilityIssueDetailView(LoginRequiredMixin, DetailView):
    """View accessibility issue details"""
    model = AccessibilityIssue
    template_name = 'accessibility/issue_detail.html'
    context_object_name = 'issue'


class AccessibilityIssueCreateView(LoginRequiredMixin, CreateView):
    """Create a new accessibility issue"""
    model = AccessibilityIssue
    template_name = 'accessibility/issue_form.html'
    fields = ['audit', 'title', 'description', 'wcag_criteria', 'severity', 'element_type', 'element_selector', 'reproduction_steps', 'expected_behavior', 'actual_behavior', 'suggested_fix']
    
    def get_success_url(self):
        return reverse('accessibility:audit_detail', kwargs={'pk': self.object.audit.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Issue created successfully.')
        return super().form_valid(form)


class AccessibilityIssueUpdateView(LoginRequiredMixin, UpdateView):
    """Update an accessibility issue"""
    model = AccessibilityIssue
    template_name = 'accessibility/issue_form.html'
    fields = ['title', 'description', 'wcag_criteria', 'severity', 'status']
    
    def get_success_url(self):
        return reverse('accessibility:issue_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Issue updated successfully.')
        return super().form_valid(form)


# ─── Accessibility Remediation Views ───────────────────────────────────────────

class AccessibilityRemediationListView(LoginRequiredMixin, ListView):
    """List all accessibility remediations"""
    model = AccessibilityRemediation
    template_name = 'accessibility/remediations.html'
    context_object_name = 'remediations'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class AccessibilityRemediationDetailView(LoginRequiredMixin, DetailView):
    """View remediation details"""
    model = AccessibilityRemediation
    template_name = 'accessibility/remediation_detail.html'
    context_object_name = 'remediation'


class AccessibilityRemediationCreateView(LoginRequiredMixin, CreateView):
    """Create a new remediation plan"""
    model = AccessibilityRemediation
    template_name = 'accessibility/remediation_form.html'
    fields = ['issue', 'approach', 'estimated_hours', 'planned_start_date', 'planned_end_date']
    
    def get_success_url(self):
        return reverse('accessibility:remediation_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.status = 'planned'
        messages.success(self.request, 'Remediation plan created successfully.')
        return super().form_valid(form)


class AccessibilityRemediationUpdateView(LoginRequiredMixin, UpdateView):
    """Update a remediation plan"""
    model = AccessibilityRemediation
    template_name = 'accessibility/remediation_form.html'
    fields = ['approach', 'estimated_hours', 'actual_hours', 'status', 'planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date', 'implementation_notes']
    
    def get_success_url(self):
        return reverse('accessibility:remediation_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        if form.instance.status == 'completed':
            form.instance.actual_end_date = form.instance.actual_end_date or timezone.now()
        messages.success(self.request, 'Remediation updated successfully.')
        return super().form_valid(form)


@login_required
@require_POST
def verify_remediation(request, pk):
    """Verify a remediation"""
    remediation = get_object_or_404(AccessibilityRemediation, pk=pk)
    
    if remediation.status != 'completed':
        messages.error(request, 'Remediation must be completed before verification.')
        return redirect('accessibility:remediation_detail', pk=pk)
    
    remediation.verified_by = request.user
    remediation.verified_at = timezone.now()
    remediation.save()
    
    # Mark the issue as resolved
    remediation.issue.status = 'resolved'
    remediation.issue.save()
    
    messages.success(request, 'Remediation verified successfully. Issue marked as resolved.')
    return redirect('accessibility:remediation_detail', pk=pk)
