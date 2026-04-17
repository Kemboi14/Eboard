from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView

from apps.accounts.decorators import role_required
from apps.accounts.permissions import CAN_VOTE
from apps.accounts.mixins import BranchOrganizationFilterMixin

from .forms import (
    MotionForm,
    MotionSearchForm,
    VoteForm,
    VoteOptionForm,
    VotingSessionForm,
)
from .models import (
    Motion, Vote, VoteOption, VoteResult, VotingSession,
    ProxyVote, QuorumTracking, DecisionDocumentation,
    VotingPattern, VotingHistory
)


class MotionListView(LoginRequiredMixin, BranchOrganizationFilterMixin, ListView):
    """List view for motions with role-based filtering"""

    model = Motion
    template_name = "voting/motion_list.html"
    context_object_name = "motions"
    paginate_by = 10

    def get_queryset(self):
        """Filter motions based on user role and branch membership"""
        user = self.request.user
        queryset = Motion.objects.select_related("meeting", "meeting__branch")

        # Organization and branch filtering
        queryset = self.filter_queryset_by_branch(queryset, branch_field='meeting__branch')

        # Role-based filtering within branch context
        if user.role == "it_administrator":
            return queryset
        elif user.role in ["company_secretary", "executive_management"]:
            return queryset
        elif user.role == "board_member":
            return queryset.filter(
                status__in=["proposed", "debate", "voting", "passed", "failed"]
            )
        else:
            return queryset.filter(status__in=["passed", "failed"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = MotionSearchForm(self.request.GET or None)
        context["can_create"] = self.request.user.role in [
            "company_secretary",
            "executive_management",
            "it_administrator",
        ]
        return context


class MotionDetailView(LoginRequiredMixin, DetailView):
    """Detail view for individual motions"""

    model = Motion
    template_name = "voting/motion_detail.html"
    context_object_name = "motion"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        motion = self.get_object()
        user = self.request.user

        can_manage = user.role in [
            "company_secretary",
            "executive_management",
            "it_administrator",
        ]

        context["can_vote"] = user.role in CAN_VOTE
        context["can_manage"] = can_manage
        context["can_create"] = can_manage
        context["has_voted"] = Vote.objects.filter(motion=motion, voter=user).exists()
        context["vote_options"] = motion.vote_options.all().order_by("order")
        context["user_vote"] = Vote.objects.filter(motion=motion, voter=user).first()
        context["vote_form"] = (
            VoteForm(motion=motion)
            if context["can_vote"] and motion.is_voting_open
            else None
        )

        return context


class CreateMotionView(LoginRequiredMixin, CreateView):
    """Create view for new motions"""

    model = Motion
    form_class = MotionForm
    template_name = "voting/create_motion.html"
    success_url = reverse_lazy("voting:motion_list")

    def dispatch(self, request, *args, **kwargs):
        """Only users who can create motions can access"""
        if request.user.role not in [
            "company_secretary",
            "executive_management",
            "it_administrator",
        ]:
            messages.error(request, "You do not have permission to create motions.")
            return redirect("voting:motion_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Set proposed_by and create activity"""
        form.instance.proposed_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Motion created successfully!")
        return response


@login_required
def cast_vote(request, pk):
    """Handle vote casting"""
    motion = get_object_or_404(Motion, pk=pk)
    user = request.user

    if user.role not in CAN_VOTE:
        messages.error(request, "You do not have permission to vote.")
        return redirect("voting:motion_detail", pk=pk)

    if not motion.is_voting_open:
        messages.error(request, "Voting is not currently open for this motion.")
        return redirect("voting:motion_detail", pk=pk)

    if Vote.objects.filter(motion=motion, voter=user).exists():
        messages.error(request, "You have already voted on this motion.")
        return redirect("voting:motion_detail", pk=pk)

    if request.method == "POST":
        form = VoteForm(motion=motion, data=request.POST)
        if form.is_valid():
            vote = form.save(commit=False)
            vote.motion = motion
            vote.voter = user
            vote.ip_address = request.META.get("REMOTE_ADDR")
            vote.save()

            messages.success(request, "Your vote has been recorded!")
            return redirect("voting:motion_detail", pk=pk)
    else:
        form = VoteForm(motion=motion)

    return render(
        request,
        "voting/cast_vote.html",
        {
            "motion": motion,
            "form": form,
        },
    )


@role_required("company_secretary", "executive_management", "it_administrator")
def manage_voting_session(request, pk=None):
    """Manage voting sessions"""
    if pk:
        session = get_object_or_404(VotingSession, pk=pk)
        motions = session.motions.all()
    else:
        session = None
        motions = Motion.objects.none()

    if request.method == "POST":
        form = VotingSessionForm(request.POST)
        if form.is_valid():
            form.instance.created_by = request.user
            form.save()
            messages.success(request, "Voting session created successfully!")
            return redirect("voting:manage_session", pk=form.instance.id)
    else:
        form = VotingSessionForm()

    return render(
        request,
        "voting/manage_session.html",
        {
            "session": session,
            "motions": motions,
            "form": form,
        },
    )


@login_required
def motion_search(request):
    """Search motions based on form criteria"""
    form = MotionSearchForm(request.GET)
    motions = Motion.objects.all()

    # Apply role-based filtering
    user = request.user
    if user.role == "it_administrator":
        pass  # See all
    elif user.role in ["company_secretary", "executive_management"]:
        pass  # See all
    elif user.role == "board_member":
        motions = motions.filter(
            status__in=["proposed", "debate", "voting", "passed", "failed"]
        )
    else:
        motions = motions.filter(status__in=["passed", "failed"])

    if form.is_valid():
        query = form.cleaned_data.get("query", "")
        search_type = form.cleaned_data.get("search_type", "all")
        status = form.cleaned_data.get("status")
        voting_type = form.cleaned_data.get("voting_type")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")

        if query:
            if search_type == "title":
                motions = motions.filter(title__icontains=query)
            elif search_type == "description":
                motions = motions.filter(description__icontains=query)
            elif search_type == "background":
                motions = motions.filter(background__icontains=query)
            else:  # all fields
                motions = motions.filter(
                    Q(title__icontains=query)
                    | Q(description__icontains=query)
                    | Q(background__icontains=query)
                )

        if status:
            motions = motions.filter(status=status)
        if voting_type:
            motions = motions.filter(voting_type=voting_type)
        if date_from:
            motions = motions.filter(created_at__date__gte=date_from)
        if date_to:
            motions = motions.filter(created_at__date__lte=date_to)

    return render(
        request,
        "voting/motion_list.html",
        {
            "motions": motions,
            "search_form": form,
            "can_create": request.user.role
            in ["company_secretary", "executive_management", "it_administrator"],
        },
    )


@login_required
def vote_results(request, pk):
    """Show voting results for a motion"""
    motion = get_object_or_404(Motion, pk=pk)

    # Check if user can view results
    user = request.user
    if user.role not in [
        "company_secretary",
        "executive_management",
        "it_administrator",
    ]:
        if motion.status not in ["passed", "failed"]:
            messages.error(request, "Results are not yet available for this motion.")
            return redirect("voting:motion_detail", pk=pk)

    try:
        result = motion.result
    except VoteResult.DoesNotExist:
        result = None

    return render(
        request,
        "voting/vote_results.html",
        {
            "motion": motion,
            "result": result,
            "can_manage": user.role
            in ["company_secretary", "executive_management", "it_administrator"],
        },
    )


@require_POST
@role_required("company_secretary", "executive_management", "it_administrator")
def propose_motion(request, pk):
    """Transition a motion from draft → proposed."""
    motion = get_object_or_404(Motion, pk=pk)
    if motion.status != "draft":
        messages.error(
            request,
            f"Motion must be in Draft status to propose it (currently: {motion.get_status_display()}).",
        )
        return redirect("voting:motion_detail", pk=pk)
    motion.status = "proposed"
    motion.save(update_fields=["status", "updated_at"])
    messages.success(request, f'Motion "{motion.title}" has been proposed.')
    return redirect("voting:motion_detail", pk=pk)


@require_POST
@role_required("company_secretary", "executive_management", "it_administrator")
def open_debate(request, pk):
    """Transition a motion from proposed → debate."""
    motion = get_object_or_404(Motion, pk=pk)
    if motion.status != "proposed":
        messages.error(
            request,
            f"Motion must be in Proposed status to open debate (currently: {motion.get_status_display()}).",
        )
        return redirect("voting:motion_detail", pk=pk)
    motion.status = "debate"
    motion.save(update_fields=["status", "updated_at"])
    messages.success(request, f'Debate has been opened for "{motion.title}".')
    return redirect("voting:motion_detail", pk=pk)


@require_POST
@role_required("company_secretary", "executive_management", "it_administrator")
def open_voting(request, pk):
    """Open voting on a motion (transitions status from proposed/debate → voting)."""
    motion = get_object_or_404(Motion, pk=pk)

    try:
        motion.open_voting(opened_by=request.user)
        messages.success(
            request,
            f'Voting has been opened for "{motion.title}".',
        )
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect("voting:motion_detail", pk=pk)


@require_POST
@role_required("company_secretary", "executive_management", "it_administrator")
def close_voting(request, pk):
    """
    Close voting on a motion and record the certified result.

    An optional POST parameter ``force_status`` may be passed with one of
    ``passed``, ``failed``, ``tabled``, or ``withdrawn`` to override the
    automatic pass/fail determination.
    """
    motion = get_object_or_404(Motion, pk=pk)

    force_status = request.POST.get("force_status") or None
    valid_overrides = {"passed", "failed", "tabled", "withdrawn"}
    if force_status and force_status not in valid_overrides:
        messages.error(
            request,
            f'Invalid force_status value "{force_status}". '
            f"Must be one of: {', '.join(sorted(valid_overrides))}.",
        )
        return redirect("voting:motion_detail", pk=pk)

    try:
        motion.close_voting(
            closed_by=request.user,
            force_status=force_status,
        )
        outcome_label = motion.get_status_display()
        messages.success(
            request,
            f'Voting has been closed for "{motion.title}". Outcome: {outcome_label}.',
        )
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect("voting:vote_results", pk=pk)


@login_required
def voting_dashboard(request):
    """Main voting dashboard with active sessions and motions"""
    user = request.user

    # Get active voting session
    active_session = VotingSession.objects.filter(
        status="active", eligible_voters=user
    ).first()

    # Get motions user can vote on
    if user.role in CAN_VOTE:
        votable_motions = Motion.objects.filter(
            status="voting", voting_deadline__gt=timezone.now()
        ).exclude(votes__voter=user)
    else:
        votable_motions = Motion.objects.none()

    # Get user's voting history
    user_votes = Vote.objects.filter(voter=user).select_related("motion")

    return render(
        request,
        "voting/voting_dashboard.html",
        {
            "active_session": active_session,
            "votable_motions": votable_motions,
            "user_votes": user_votes,
            "can_create": user.role
            in ["company_secretary", "executive_management", "it_administrator"],
        },
    )


# ─── Proxy Voting Views ─────────────────────────────────────────────────────────

class ProxyVoteListView(LoginRequiredMixin, ListView):
    """List all proxy votes"""
    model = ProxyVote
    template_name = 'voting/proxy_votes.html'
    context_object_name = 'proxy_votes'
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        # Users can see their own proxy votes and those they've been granted
        queryset = queryset.filter(Q(principal=user) | Q(proxy=user))
        return queryset


class ProxyVoteCreateView(LoginRequiredMixin, CreateView):
    """Create a new proxy vote"""
    model = ProxyVote
    template_name = 'voting/proxy_vote_form.html'
    fields = ['proxy', 'motion', 'valid_from', 'valid_until', 'voting_instructions', 'supporting_document']
    success_url = reverse_lazy('voting:proxy_votes')
    
    def form_valid(self, form):
        form.instance.principal = self.request.user
        messages.success(self.request, 'Proxy vote granted successfully.')
        return super().form_valid(form)


class ProxyVoteRevokeView(LoginRequiredMixin, DetailView):
    """Revoke a proxy vote"""
    model = ProxyVote
    template_name = 'voting/proxy_vote_confirm_revoke.html'
    context_object_name = 'proxy_vote'
    
    def post(self, request, *args, **kwargs):
        proxy_vote = self.get_object()
        if proxy_vote.principal != request.user and request.user.role not in ['it_administrator', 'company_secretary']:
            messages.error(request, "You don't have permission to revoke this proxy vote.")
            return redirect('voting:proxy_votes')
        
        proxy_vote.is_revoked = True
        proxy_vote.revoked_at = timezone.now()
        proxy_vote.save()
        
        messages.success(request, 'Proxy vote revoked successfully.')
        return redirect('voting:proxy_votes')


# ─── Quorum Management Views ───────────────────────────────────────────────────

class QuorumTrackingListView(LoginRequiredMixin, ListView):
    """List quorum tracking records"""
    model = QuorumTracking
    template_name = 'voting/quorum_tracking.html'
    context_object_name = 'quorum_records'
    ordering = ['-checked_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        meeting_id = self.request.GET.get('meeting')
        if meeting_id:
            queryset = queryset.filter(meeting_id=meeting_id)
        return queryset


class QuorumTrackingDetailView(LoginRequiredMixin, DetailView):
    """View quorum tracking details"""
    model = QuorumTracking
    template_name = 'voting/quorum_tracking_detail.html'
    context_object_name = 'quorum_record'


# ─── Decision Documentation Views ───────────────────────────────────────────────

class DecisionDocumentationListView(LoginRequiredMixin, ListView):
    """List all decision documentation"""
    model = DecisionDocumentation
    template_name = 'voting/decision_documentation.html'
    context_object_name = 'decisions'
    ordering = ['-created_at']


class DecisionDocumentationDetailView(LoginRequiredMixin, DetailView):
    """View decision documentation details"""
    model = DecisionDocumentation
    template_name = 'voting/decision_documentation_detail.html'
    context_object_name = 'decision'


class DecisionDocumentationCreateView(LoginRequiredMixin, CreateView):
    """Create decision documentation"""
    model = DecisionDocumentation
    template_name = 'voting/decision_documentation_form.html'
    fields = ['motion', 'decision_summary', 'legal_basis', 'compliance_notes', 'implementation_plan', 'implementation_deadline', 'supporting_documents']
    success_url = reverse_lazy('voting:decision_documentation')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Decision documentation created successfully.')
        return super().form_valid(form)


# ─── Voting Pattern Analysis Views ─────────────────────────────────────────────

class VotingPatternListView(LoginRequiredMixin, ListView):
    """List voting patterns"""
    model = VotingPattern
    template_name = 'voting/voting_patterns.html'
    context_object_name = 'patterns'
    ordering = ['-last_calculated_at']


class VotingPatternDetailView(LoginRequiredMixin, DetailView):
    """View voting pattern details"""
    model = VotingPattern
    template_name = 'voting/voting_pattern_detail.html'
    context_object_name = 'pattern'


class VotingHistoryListView(LoginRequiredMixin, ListView):
    """List voting history"""
    model = VotingHistory
    template_name = 'voting/voting_history.html'
    context_object_name = 'history'
    ordering = ['-voting_session_date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.GET.get('user')
        category = self.request.GET.get('category')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if category:
            queryset = queryset.filter(motion_category=category)
        return queryset
