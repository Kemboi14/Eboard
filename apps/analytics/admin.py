from django.contrib import admin

from .models import (
    AnalyticsMetric, AnalyticsDataPoint, AnalyticsDashboard,
    AnalyticsWidget, BoardAnalyticsSnapshot, UserAnalyticsProfile, AnalyticsReport,
    ComplianceScorecard, AttendanceAnalytics, DecisionTracking, CustomReport
)


@admin.register(AnalyticsMetric)
class AnalyticsMetricAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "metric_type",
        "frequency",
        "is_active",
        "unit",
        "created_at",
    )
    list_filter = ("metric_type", "frequency", "is_active")
    search_fields = ("name", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("created_by",)
    ordering = ("metric_type", "name")


@admin.register(AnalyticsDataPoint)
class AnalyticsDataPointAdmin(admin.ModelAdmin):
    list_display = (
        "metric",
        "value",
        "value_text",
        "timestamp",
        "created_at",
    )
    list_filter = ("timestamp",)
    search_fields = ("metric__name",)
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("metric",)
    ordering = ("-timestamp",)


@admin.register(AnalyticsDashboard)
class AnalyticsDashboardAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_public",
        "created_by",
        "created_at",
    )
    list_filter = ("is_public", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("created_by",)
    ordering = ("-created_at",)


@admin.register(AnalyticsWidget)
class AnalyticsWidgetAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "widget_type",
        "dashboard",
        "position_x",
        "position_y",
        "width",
        "height",
        "created_at",
    )
    list_filter = ("widget_type", "dashboard")
    search_fields = ("title", "description")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("dashboard", "metric")
    ordering = ("dashboard", "position_y", "position_x")


@admin.register(BoardAnalyticsSnapshot)
class BoardAnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "snapshot_date",
        "created_at",
    )
    list_filter = ("snapshot_date", "created_at")
    search_fields = ()
    readonly_fields = ("id", "created_at")
    ordering = ("-snapshot_date",)


@admin.register(UserAnalyticsProfile)
class UserAnalyticsProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("user__email",)
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("user",)
    ordering = ("-created_at",)


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "report_type",
        "format",
        "start_date",
        "end_date",
        "status",
        "generated_by",
        "created_at",
    )
    list_filter = ("report_type", "format", "status", "created_at")
    search_fields = ("title",)
    readonly_fields = ("id", "created_at", "generated_at")
    raw_id_fields = ("generated_by",)
    ordering = ("-created_at",)


@admin.register(ComplianceScorecard)
class ComplianceScorecardAdmin(admin.ModelAdmin):
    list_display = (
        "period_start",
        "period_end",
        "overall_score",
        "status",
        "governance_score",
        "financial_score",
        "operational_score",
        "reviewed_by",
        "created_at",
    )
    list_filter = ("status", "period_start", "period_end", "created_at")
    search_fields = ("findings", "recommendations")
    readonly_fields = ("id", "created_at", "updated_at", "reviewed_at")
    raw_id_fields = ("reviewed_by",)
    ordering = ("-period_end",)


@admin.register(AttendanceAnalytics)
class AttendanceAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "user",
        "attended",
        "arrived_late",
        "left_early",
        "participation_score",
        "questions_asked",
        "comments_made",
        "created_at",
    )
    list_filter = ("attended", "arrived_late", "left_early", "created_at")
    search_fields = ("meeting__title", "user__email")
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("meeting", "user")
    ordering = ("-created_at",)


@admin.register(DecisionTracking)
class DecisionTrackingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "decision_type",
        "status",
        "decision_date",
        "implementation_date",
        "target_completion_date",
        "decision_maker",
        "implementer",
        "created_at",
    )
    list_filter = ("decision_type", "status", "decision_date", "created_at")
    search_fields = ("title", "description", "outcome")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("meeting", "motion", "decision_maker", "implementer")
    ordering = ("-created_at",)


@admin.register(CustomReport)
class CustomReportAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "report_type",
        "status",
        "output_format",
        "schedule",
        "next_run",
        "created_by",
        "created_at",
        "last_generated_at",
    )
    list_filter = ("report_type", "status", "output_format", "created_at")
    search_fields = ("title", "description")
    readonly_fields = ("id", "created_at", "updated_at", "last_generated_at")
    raw_id_fields = ("created_by",)
    ordering = ("-created_at",)
