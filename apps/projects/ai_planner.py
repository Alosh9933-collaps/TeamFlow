
def generate_task_suggestions(*, description):
    """
    Generate mock task suggestions from a project description.

    This is a local mock implementation.
    It does not call an external AI API.
    """

    description = description.strip()

    if not description:
        raise ValueError("Project description cannot be empty.")

    return [
        {
            "title": "Define project requirements",
            "description": (
                f"Identify the main requirements for: {description}"
            ),
            "priority": "high",
        },
        {
            "title": "Design the implementation plan",
            "description": (
                "Break the project into smaller technical steps."
            ),
            "priority": "high",
        },
        {
            "title": "Implement the core functionality",
            "description": (
                "Build and integrate the main features."
            ),
            "priority": "medium",
        },
        {
            "title": "Write tests",
            "description": (
                "Test the main functionality and important edge cases."
            ),
            "priority": "medium",
        },
        {
            "title": "Review and document the project",
            "description": (
                "Review the implementation and document how to use it."
            ),
            "priority": "low",
        },
    ]
