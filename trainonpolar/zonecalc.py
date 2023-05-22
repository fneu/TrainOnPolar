
def unique_speed_targets(workout):
    speed_steps = []
    for step in workout["steps"]:
        speed_steps.extend(step_targets(step))
    return sorted(list(set(speed_steps)))


def step_targets(step):
    if step["type"] == "WorkoutStep":
        if step["targetType"] == "SPEED":
            return [step["targetValue"]]
        elif step["targetType"] == "OPEN":
            return []
        else:
            raise AttributeError(
                f"unknown targetType {step['targetType']} of workout step"
            )
    elif step["type"] == "WorkoutRepeatStep":
        steps = []
        for s in step["steps"]:
            steps.extend(step_targets(s))
        return steps
    raise AttributeError(
        f"unknown step type {step['type']}"
    )
