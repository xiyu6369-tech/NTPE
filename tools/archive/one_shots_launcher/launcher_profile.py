from core.project_profile import load_project_profile, get_profile_summary

if __name__ == "__main__":
    profile = load_project_profile()
    summary = get_profile_summary(profile)

    print("NTPE Project Profile v1.0")
    print("=========================")
    for key, value in summary.items():
        print(f"{key}: {value}")
