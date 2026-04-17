from django.contrib import admin

from .models import (
    Motion, Vote, VoteOption, VoteResult, VotingSession,
    ProxyVote, QuorumTracking, DecisionDocumentation,
    VotingPattern, VotingHistory
)


@admin.register(Motion)
class MotionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "status",
        "voting_type",
        "proposed_by",
        "voting_deadline",
        "created_at",
    )
    list_filter = ("status", "category", "voting_type")
    search_fields = ("title", "description", "reference_number")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "voting_started_at",
        "voting_ended_at",
    )
    raw_id_fields = ("proposed_by", "seconded_by", "meeting")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "id",
                    "title",
                    "description",
                    "background",
                    "category",
                    "reference_number",
                    "meeting",
                )
            },
        ),
        (
            "Voting Configuration",
            {
                "fields": (
                    "voting_type",
                    "required_votes",
                    "voting_deadline",
                    "allow_anonymous",
                )
            },
        ),
        (
            "Status & People",
            {
                "fields": (
                    "status",
                    "proposed_by",
                    "seconded_by",
                )
            },
        ),
        (
            "Outcome",
            {"fields": ("result_notes",)},
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                    "voting_started_at",
                    "voting_ended_at",
                    "tabled_at",
                ),
            },
        ),
    )


@admin.register(VotingSession)
class VotingSessionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "start_time",
        "end_time",
        "created_by",
        "motions_count",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("title", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("created_by", "meeting")
    filter_horizontal = ("motions", "eligible_voters")
    ordering = ("-start_time",)

    @admin.display(description="Motions")
    def motions_count(self, obj):
        return obj.motions.count()


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = (
        "motion",
        "voter_display",
        "choice",
        "is_anonymous",
        "cast_at",
    )
    list_filter = ("choice", "is_anonymous", "cast_at")
    search_fields = ("motion__title",)
    readonly_fields = ("id", "cast_at", "ip_address", "user_agent")
    raw_id_fields = ("motion", "voter", "vote_option")
    ordering = ("-cast_at",)

    @admin.display(description="Voter")
    def voter_display(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.voter.get_full_name() if obj.voter else "—"


@admin.register(VoteOption)
class VoteOptionAdmin(admin.ModelAdmin):
    list_display = ("motion", "text", "order", "vote_count")
    list_filter = ()
    search_fields = ("motion__title", "text")
    readonly_fields = ("id",)
    raw_id_fields = ("motion",)
    ordering = ("motion", "order")

    @admin.display(description="Votes")
    def vote_count(self, obj):
        return obj.votes.count()


@admin.register(VoteResult)
class VoteResultAdmin(admin.ModelAdmin):
    list_display = (
        "motion",
        "passed",
        "total_votes",
        "yes_votes",
        "no_votes",
        "abstain_votes",
        "certified_by",
        "certified_at",
    )
    list_filter = ("passed", "voting_type")
    search_fields = ("motion__title",)
    readonly_fields = ("id", "certified_at", "updated_at")
    raw_id_fields = ("motion", "certified_by")
    ordering = ("-certified_at",)


@admin.register(ProxyVote)
class ProxyVoteAdmin(admin.ModelAdmin):
    list_display = (
        "principal",
        "proxy",
        "motion",
        "voting_instructions",
        "status",
        "executed",
        "approved_at",
    )
    list_filter = ("status", "executed")
    search_fields = ("principal__email", "proxy__email", "motion__title")
    readonly_fields = ("id", "created_at", "approved_at")
    raw_id_fields = ("principal", "proxy", "motion", "approved_by")
    ordering = ("-created_at",)


@admin.register(QuorumTracking)
class QuorumTrackingAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "voting_session",
        "status",
        "required_members",
        "present_members",
        "quorum_percentage",
        "checked_at",
    )
    list_filter = ("status", "checked_at")
    search_fields = ("meeting__title",)
    readonly_fields = ("id", "quorum_met_at", "quorum_lost_at", "checked_at")
    raw_id_fields = ("meeting", "voting_session")
    ordering = ("-checked_at",)


@admin.register(DecisionDocumentation)
class DecisionDocumentationAdmin(admin.ModelAdmin):
    list_display = (
        "motion",
        "compliance_status",
        "compliance_score",
        "implementation_deadline",
        "implementation_status",
        "created_at",
    )
    list_filter = ("compliance_status", "implementation_status", "created_at")
    search_fields = ("motion__title", "decision_summary", "legal_basis")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("motion",)
    filter_horizontal = ("supporting_documents",)
    ordering = ("-created_at",)


@admin.register(VotingPattern)
class VotingPatternAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "total_votes",
        "votes_in_favor",
        "votes_against",
        "abstentions",
        "participation_rate",
        "consistency_score",
        "last_calculated_at",
    )
    list_filter = ("typically_votes_with_majority", "often_abstains", "frequently_dissents", "last_calculated_at")
    search_fields = ("user__email",)
    readonly_fields = ("id", "last_calculated_at", "created_at")
    raw_id_fields = ("user",)
    ordering = ("-last_calculated_at",)


@admin.register(VotingHistory)
class VotingHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "motion_title",
        "motion_category",
        "vote_choice",
        "motion_outcome",
        "voting_session_date",
        "vote_weight",
        "was_decisive_vote",
        "aligned_with_majority",
        "recorded_at",
    )
    list_filter = ("vote_choice", "motion_outcome", "was_decisive_vote", "aligned_with_majority", "voting_session_date")
    search_fields = ("user__email", "motion_title", "meeting_title")
    readonly_fields = ("id", "recorded_at")
    raw_id_fields = ("user", "vote")
    ordering = ("-voting_session_date",)
