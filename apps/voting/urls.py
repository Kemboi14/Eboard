from django.urls import path

from . import views

app_name = "voting"

urlpatterns = [
    path("", views.MotionListView.as_view(), name="motion_list"),
    path("dashboard/", views.voting_dashboard, name="voting_dashboard"),
    path("search/", views.motion_search, name="motion_search"),
    path("motions/create/", views.CreateMotionView.as_view(), name="create_motion"),
    path("motions/<uuid:pk>/", views.MotionDetailView.as_view(), name="motion_detail"),
    path("motions/<uuid:pk>/vote/", views.cast_vote, name="cast_vote"),
    path("motions/<uuid:pk>/results/", views.vote_results, name="vote_results"),
    path("motions/<uuid:pk>/propose/", views.propose_motion, name="propose_motion"),
    path("motions/<uuid:pk>/debate/", views.open_debate, name="open_debate"),
    path("motions/<uuid:pk>/open-voting/", views.open_voting, name="open_voting"),
    path("motions/<uuid:pk>/close-voting/", views.close_voting, name="close_voting"),
    path("session/", views.manage_voting_session, name="manage_session"),
    path(
        "session/<uuid:pk>/", views.manage_voting_session, name="manage_session_detail"
    ),
    
    # Proxy Voting
    path("proxy-votes/", views.ProxyVoteListView.as_view(), name="proxy_votes"),
    path("proxy-votes/create/", views.ProxyVoteCreateView.as_view(), name="proxy_vote_create"),
    path("proxy-votes/<uuid:pk>/revoke/", views.ProxyVoteRevokeView.as_view(), name="proxy_vote_revoke"),
    
    # Quorum Management
    path("quorum-tracking/", views.QuorumTrackingListView.as_view(), name="quorum_tracking"),
    path("quorum-tracking/<uuid:pk>/", views.QuorumTrackingDetailView.as_view(), name="quorum_tracking_detail"),
    
    # Decision Documentation
    path("decision-documentation/", views.DecisionDocumentationListView.as_view(), name="decision_documentation"),
    path("decision-documentation/<uuid:pk>/", views.DecisionDocumentationDetailView.as_view(), name="decision_documentation_detail"),
    path("decision-documentation/create/", views.DecisionDocumentationCreateView.as_view(), name="decision_documentation_create"),
    
    # Voting Pattern Analysis
    path("voting-patterns/", views.VotingPatternListView.as_view(), name="voting_patterns"),
    path("voting-patterns/<uuid:pk>/", views.VotingPatternDetailView.as_view(), name="voting_pattern_detail"),
    path("voting-history/", views.VotingHistoryListView.as_view(), name="voting_history"),
]
