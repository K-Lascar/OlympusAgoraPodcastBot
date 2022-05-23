def format_episode_title(title):
    title_substring = ""
    if title.startswith(("Ep", "FOHMO3")):
        initial_position = title.find("-")
        secondary_position = title.find("-", initial_position + 1)
        title_substring = title[:initial_position + 2] + title[secondary_position + 1:].strip()
        if title.startswith("FOHMO3"):
            title_substring = "FOHMO3 " + title_substring
    elif title.startswith(("Bonus Ep - Bong Bears")):
        initial_position = title.find("-")
        title_substring = "FOHMO3 " + title[initial_position + 1:].strip()
    else:
        title_substring = title
    return title_substring