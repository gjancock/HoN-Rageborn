import utilities.constants as constant


def crop_draft_team_regions(screenshot):
    """
    Crop Legion and Hellbourne player lists
    from the HoN draft / ban screen.
    """

    # 🔴 TUNE THESE ONCE (based on your resolution)
    LEGION_REGION = {
        "x": 674 + 25,   # expand left
        "y": 755,
        "w": 126,   # expand width
        "h": 93,
    }

    HELLBOURNE_REGION = {
        "x": 1115 + 20,
        "y": 755,
        "w": 123,
        "h": 93,
    }

    regions = {}

    lx, ly, lw, lh = (
        LEGION_REGION["x"],
        LEGION_REGION["y"],
        LEGION_REGION["w"],
        LEGION_REGION["h"],
    )

    hx, hy, hw, hh = (
        HELLBOURNE_REGION["x"],
        HELLBOURNE_REGION["y"],
        HELLBOURNE_REGION["w"],
        HELLBOURNE_REGION["h"],
    )

    regions[constant.TEAM_LEGION] = screenshot[ly : ly + lh, lx : lx + lw]
    regions[constant.TEAM_HELLBOURNE] = screenshot[hy : hy + hh, hx : hx + hw]

    return regions
