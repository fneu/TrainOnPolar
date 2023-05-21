
def unique_zones(workout):
    speed_steps = []
    for step in workout["steps"]:
        speed_steps.extend(step_zones(step))

    speed_steps.sort(key=lambda x: x[0])
    merged = []
    for step in speed_steps:
        if not merged or merged[-1][1] < step[0]:
            merged.append(step)
        else:
            merged[-1][1] = max(merged[-1][1], step[1])

    # min 7min/km if possible to avoid 0.0 lower bound
    if merged[0][0] == 0.0:
        merged[0][0] = min(2.38, merged[0][1] - 0.2)
    return merged


def step_zones(step):
    if step["type"] == "WorkoutStep":
        if step["targetType"] == "SPEED":
            return [[step["targetValueLow"], step["targetValueHigh"]]]
        elif step["targetType"] == "OPEN":
            return []
        else:
            raise AttributeError(
                f"unknown targetType {step['targetType']} of workout step"
            )
    elif step["type"] == "WorkoutRepeatStep":
        steps = []
        for s in step["steps"]:
            steps.extend(step_zones(s))
        return steps
    raise AttributeError(
        f"unknown step type {step['type']}"
    )


def ensure_five(steps):
    while len(steps) != 5:
        if len(steps) > 5:
            steps = remove_one(steps)
        else:
            steps = append_one(steps)
    return steps


def remove_one(steps):
    return [[steps[0][0], steps[1][1]]] + steps[2:]


def append_one(steps):
    biggest_gap = 0
    gap_index = 0
    for i in range(len(steps) - 1):
        gap = steps[i+1][0] - steps[i][1]
        if gap > biggest_gap:
            biggest_gap = gap
            gap_index = i

    if biggest_gap == 0.0:
        steps.append([steps[-1][1], steps[-1][1]+0.2])
    else:
        steps = (steps[:gap_index+1]
                 + [[steps[gap_index][1], steps[gap_index+1][0]]]
                 + steps[gap_index+1:])
    return steps


def lower_bounds(steps):
    bounds = [steps[0][0]]
    for i in range(1, len(steps)):
        bounds.append((steps[i-1][1] + steps[i][0])/2)
    return bounds


def lower_kph_bounds(workout):
    return [x*3.6 for x in lower_bounds(ensure_five(unique_zones(workout)))]
