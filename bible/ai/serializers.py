from rest_framework import serializers

# --- Serializers para Views de AI ---


class ToolTestRequestSerializer(serializers.Serializer):
    """Serializer for testing an AI tool."""

    tool = serializers.CharField(help_text="Name of the tool to test.")
    params = serializers.JSONField(required=False, help_text="Parameters for the tool.")


class ToolTestResponseSerializer(serializers.Serializer):
    """Serializer for AI tool test response."""

    tool = serializers.CharField()
    status = serializers.CharField()
    message = serializers.CharField()


class AgentRunCreateRequestSerializer(serializers.Serializer):
    """Serializer for creating an AI agent run."""

    agent = serializers.CharField(help_text="Name of the agent to run.")
    input_payload = serializers.JSONField(help_text="Input data for the agent run.")


class AgentRunResponseSerializer(serializers.Serializer):
    """Serializer for AI agent run details and responses."""

    agent = serializers.CharField(required=False)
    run_id = serializers.IntegerField(required=False)
    status = serializers.CharField()
    message = serializers.CharField()


class AgentRunApproveRequestSerializer(serializers.Serializer):
    """Serializer for approving an AI agent run."""

    run_id = serializers.IntegerField(help_text="ID of the agent run to approve.")
    note = serializers.CharField(required=False, help_text="Optional note for approval.")
