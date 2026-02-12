def check_eligibility(age, weight, health_issues):
    if age < 18:
        return False
    if weight < 50:
        return False
    if health_issues:
        return False
    return True
