from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from apps.agencies.models import Branch, Committee, CommitteeMembership
from django.contrib.auth import get_user_model

User = get_user_model()


def check_admin_or_role(*roles):
    """Decorator to check if user is admin or has specific role"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return wrapper
    return decorator


@login_required
def branch_list(request):
    """List all branches"""
    branches = Branch.objects.all()
    can_create = request.user.is_superuser or request.user.role in ['it_administrator', 'executive_management']
    
    context = {
        'branches': branches,
        'can_create': can_create,
        'title': 'Branch Management',
    }
    return render(request, 'organization/branch_list.html', context)


@login_required
@check_admin_or_role('it_administrator', 'executive_management')
def branch_create(request):
    """Create a new branch"""
    from apps.agencies.models import Organization
    
    if request.method == 'POST':
        try:
            # Get or create default organization
            organization = Organization.objects.first()
            if not organization:
                organization = Organization.objects.create(
                    name="Enwealth",
                    legal_name="Enwealth Financial Services",
                    created_by=request.user
                )
            
            branch = Branch.objects.create(
                organization=organization,
                name=request.POST.get('name'),
                code=request.POST.get('code'),
                country=request.POST.get('country', 'Kenya'),
                city=request.POST.get('city', ''),
                address=request.POST.get('address', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                branch_type=request.POST.get('branch_type', 'regional_office'),
                status=request.POST.get('status', 'active'),
                created_by=request.user
            )
            
            messages.success(request, f'Branch "{branch.name}" created successfully!')
            return redirect('agencies:branch_detail', pk=branch.pk)
        except Exception as e:
            messages.error(request, f'Error creating branch: {str(e)}')
    
    context = {
        'title': 'Create New Branch',
    }
    return render(request, 'organization/branch_form.html', context)


@login_required
def branch_detail(request, pk):
    """View branch details"""
    branch = get_object_or_404(Branch, pk=pk)
    members = branch.memberships.all()
    committees = branch.committees.all()
    can_edit = request.user.is_superuser or request.user.role in ['it_administrator', 'executive_management']
    
    context = {
        'branch': branch,
        'members': members,
        'committees': committees,
        'can_edit': can_edit,
        'title': f'Branch: {branch.name}',
    }
    return render(request, 'organization/branch_detail.html', context)


@login_required
@check_admin_or_role('it_administrator', 'executive_management')
def branch_update(request, pk):
    """Update branch details"""
    branch = get_object_or_404(Branch, pk=pk)
    
    if request.method == 'POST':
        try:
            branch.name = request.POST.get('name', branch.name)
            branch.code = request.POST.get('code', branch.code)
            branch.country = request.POST.get('country', branch.country)
            branch.city = request.POST.get('city', branch.city)
            branch.address = request.POST.get('address', branch.address)
            branch.email = request.POST.get('email', branch.email)
            branch.phone = request.POST.get('phone', branch.phone)
            branch.branch_type = request.POST.get('branch_type', branch.branch_type)
            branch.status = request.POST.get('status', branch.status)
            
            branch.save()
            messages.success(request, f'Branch "{branch.name}" updated successfully!')
            return redirect('agencies:branch_detail', pk=branch.pk)
        except Exception as e:
            messages.error(request, f'Error updating branch: {str(e)}')
    
    context = {
        'branch': branch,
        'title': f'Update Branch: {branch.name}',
    }
    return render(request, 'organization/branch_form.html', context)


@login_required
def committee_list(request):
    """List all committees"""
    committees = Committee.objects.all()
    can_create = request.user.is_superuser or request.user.role in ['it_administrator', 'company_secretary', 'executive_management']
    
    context = {
        'committees': committees,
        'can_create': can_create,
        'title': 'Committee Management',
    }
    return render(request, 'organization/committee_list.html', context)


@login_required
@check_admin_or_role('it_administrator', 'company_secretary', 'executive_management')
def committee_create(request):
    """Create a new committee"""
    if request.method == 'POST':
        try:
            branch_id = request.POST.get('branch')
            branch = Branch.objects.get(id=branch_id) if branch_id else None
            
            committee = Committee.objects.create(
                branch=branch,
                name=request.POST.get('name'),
                code=request.POST.get('code'),
                committee_type=request.POST.get('committee_type', 'other'),
                description=request.POST.get('description', ''),
                mandate=request.POST.get('mandate', ''),
                meeting_frequency=request.POST.get('meeting_frequency', 'Monthly'),
                status=request.POST.get('status', 'active'),
                created_by=request.user
            )
            
            # Set parent committee if provided (creates sub-committee)
            parent_committee_id = request.POST.get('parent_committee')
            if parent_committee_id:
                committee.parent_committee = Committee.objects.get(id=parent_committee_id)
            
            # Set chairperson if provided
            chairperson_id = request.POST.get('chairperson')
            if chairperson_id:
                committee.chairperson = User.objects.get(id=chairperson_id)
            
            # Set secretary if provided
            secretary_id = request.POST.get('secretary')
            if secretary_id:
                committee.secretary = User.objects.get(id=secretary_id)
            
            committee.save()
            
            messages.success(request, f'Committee "{committee.name}" created successfully!')
            return redirect('agencies:committee_detail', pk=committee.pk)
        except Exception as e:
            messages.error(request, f'Error creating committee: {str(e)}')
    
    # Get potential committee members
    potential_members = User.objects.filter(
        role__in=['board_member', 'company_secretary', 'executive_management', 'compliance_officer']
    )
    branches = Branch.objects.all()
    # Get existing committees that can be parent committees
    potential_parent_committees = Committee.objects.filter(status='active', is_active=True)
    
    # Pre-select parent committee if provided in query parameter
    selected_parent_committee = None
    parent_committee_id = request.GET.get('parent_committee')
    if parent_committee_id:
        try:
            selected_parent_committee = Committee.objects.get(id=parent_committee_id)
        except Committee.DoesNotExist:
            pass
    
    context = {
        'potential_members': potential_members,
        'branches': branches,
        'potential_parent_committees': potential_parent_committees,
        'selected_parent_committee': selected_parent_committee,
        'title': 'Create New Committee',
    }
    return render(request, 'organization/committee_form.html', context)


@login_required
def committee_detail(request, pk):
    """View committee details"""
    committee = get_object_or_404(Committee, pk=pk)
    members = committee.memberships.all()
    can_edit = request.user.is_superuser or request.user.role in ['it_administrator', 'company_secretary']
    
    context = {
        'committee': committee,
        'members': members,
        'can_edit': can_edit,
        'title': f'Committee: {committee.name}',
    }
    return render(request, 'organization/committee_detail.html', context)


@login_required
@check_admin_or_role('it_administrator', 'company_secretary')
def committee_update(request, pk):
    """Update committee details"""
    committee = get_object_or_404(Committee, pk=pk)
    
    if request.method == 'POST':
        try:
            committee.name = request.POST.get('name', committee.name)
            committee.code = request.POST.get('code', committee.code)
            committee.committee_type = request.POST.get('committee_type', committee.committee_type)
            committee.description = request.POST.get('description', committee.description)
            committee.mandate = request.POST.get('mandate', committee.mandate)
            committee.meeting_frequency = request.POST.get('meeting_frequency', committee.meeting_frequency)
            committee.status = request.POST.get('status', committee.status)
            
            # Update chairperson
            chairperson_id = request.POST.get('chairperson')
            if chairperson_id:
                committee.chairperson = User.objects.get(id=chairperson_id)
            else:
                committee.chairperson = None
            
            # Update secretary
            secretary_id = request.POST.get('secretary')
            if secretary_id:
                committee.secretary = User.objects.get(id=secretary_id)
            else:
                committee.secretary = None
            
            # Update branch
            branch_id = request.POST.get('branch')
            if branch_id:
                committee.branch = Branch.objects.get(id=branch_id)
            else:
                committee.branch = None
            
            # Update parent committee
            parent_committee_id = request.POST.get('parent_committee')
            if parent_committee_id:
                committee.parent_committee = Committee.objects.get(id=parent_committee_id)
            else:
                committee.parent_committee = None
            
            committee.save()
            messages.success(request, f'Committee "{committee.name}" updated successfully!')
            return redirect('agencies:committee_detail', pk=committee.pk)
        except Exception as e:
            messages.error(request, f'Error updating committee: {str(e)}')
    
    potential_members = User.objects.filter(
        role__in=['board_member', 'company_secretary', 'executive_management', 'compliance_officer']
    )
    branches = Branch.objects.all()
    # Get existing committees that can be parent committees (excluding this one to prevent circular reference)
    potential_parent_committees = Committee.objects.filter(status='active', is_active=True).exclude(pk=committee.pk)
    
    context = {
        'committee': committee,
        'potential_members': potential_members,
        'branches': branches,
        'potential_parent_committees': potential_parent_committees,
        'title': f'Update Committee: {committee.name}',
    }
    return render(request, 'organization/committee_form.html', context)


@login_required
@check_admin_or_role('it_administrator', 'company_secretary')
def committee_add_member(request, pk):
    """Add member to committee"""
    committee = get_object_or_404(Committee, pk=pk)
    
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user')
            role = request.POST.get('committee_role', 'member')
            
            if user_id:
                user = User.objects.get(id=user_id)
                member, created = CommitteeMembership.objects.get_or_create(
                    committee=committee,
                    user=user,
                    defaults={
                        'committee_role': role,
                        'added_by': request.user
                    }
                )
                
                if created:
                    messages.success(request, f'{user.get_full_name()} added to committee successfully!')
                else:
                    messages.warning(request, f'{user.get_full_name()} is already a member of this committee.')
                
                return redirect('organization:committee_detail', pk=committee.pk)
        except Exception as e:
            messages.error(request, f'Error adding member: {str(e)}')
    
    # Get users who can be committee members
    potential_members = User.objects.filter(
        role__in=['board_member', 'company_secretary', 'executive_management', 'compliance_officer']
    ).exclude(committee_memberships__committee=committee)
    
    context = {
        'committee': committee,
        'potential_members': potential_members,
        'title': f'Add Member to {committee.name}',
    }
    return render(request, 'organization/add_committee_member.html', context)


@login_required
@check_admin_or_role('it_administrator', 'company_secretary')
def committee_remove_member(request, pk, member_id):
    """Remove member from committee"""
    committee = get_object_or_404(Committee, pk=pk)
    member = get_object_or_404(CommitteeMembership, pk=member_id, committee=committee)
    
    if request.method == 'POST':
        member.delete()
        messages.success(request, f'{member.user.get_full_name()} removed from committee successfully!')
        return redirect('organization:committee_detail', pk=committee.pk)
    
    context = {
        'committee': committee,
        'member': member,
        'title': f'Remove Member from {committee.name}',
    }
    return render(request, 'organization/remove_committee_member.html', context)
