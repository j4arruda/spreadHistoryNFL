### This is my first personal project, i wall attempting to be making an NFL 
### prediction app that can predict outcomes on bets. 

from pathlib import Path
import math

import nflreadpy as nfl
import pandas as pd


def doginput(week, spread, season):
    if not 2015 <= season <= 2025:
        raise ValueError("Season must be between 2015 and 2025.")

    if not 1 <= week <= 18:
        raise ValueError("Week must be between 1 and 18.")

    if not math.isfinite(spread) or spread <= 0:
        raise ValueError("Spread must be a positive number.")

    seasons = [season]
    schedules = nfl.load_schedules(seasons).to_pandas()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    # Save the downloaded data for inspection or later analysis.
    schedules.to_csv(output_dir / f"nfl_schedules_{season}.csv",index=False,)

    # Select completed regular-season games with a known spread.
    dogs = schedules.loc[
        (schedules["game_type"] == "REG")
        & (schedules["week"] == week)
        & schedules["result"].notna()
        & schedules["spread_line"].notna()
        & (schedules["spread_line"].abs() >= spread)
    ].copy()

    # Positive spread: away team is the underdog.
    dogs["dog_team"] = dogs["away_team"].where(
        dogs["spread_line"] > 0,
        dogs["home_team"],
    )

    # Positive margin means the underdog covered.
    dogs["dog_cover_margin"] = (
        dogs["spread_line"] - dogs["result"]
    ).where(
        dogs["spread_line"] > 0,
        dogs["result"] - dogs["spread_line"],
    )

    dogs["outcome"] = "LOSS"
    dogs.loc[dogs["dog_cover_margin"] > 0, "outcome"] = "COVER"
    dogs.loc[dogs["dog_cover_margin"] == 0, "outcome"] = "PUSH"

    print(f"\nWEEK {week}: Underdogs getting +{spread:g} or more")
    print("Records show covers-losses-pushes.\n")

    summary = []

    for season in seasons:
        games = dogs.loc[dogs["season"] == season]

        covers = int((games["outcome"] == "COVER").sum())
        losses = int((games["outcome"] == "LOSS").sum())
        pushes = int((games["outcome"] == "PUSH").sum())
        decided = covers + losses

        # Exclude pushes from the cover percentage.
        cover_rate = covers / decided if decided else None
        rate_text = f"{cover_rate:.1%}" if decided else "N/A"

        print(
            f"Season {season}: {rate_text} "
            f"({covers}-{losses}-{pushes})"
        )

        summary.append({
            "season": season,
            "games": len(games),
            "covers": covers,
            "losses": losses,
            "pushes": pushes,
            "cover_rate": cover_rate,
        })

    covers = int((dogs["outcome"] == "COVER").sum())
    losses = int((dogs["outcome"] == "LOSS").sum())
    pushes = int((dogs["outcome"] == "PUSH").sum())
    decided = covers + losses


    print("\nUnderdogs that covered:")
    for game in dogs.loc[dogs["outcome"] == "COVER"].itertuples():
        print(f"{game.season}: {game.dog_team} ({game.game_id})")

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(output_dir / "underdog_summary.csv", index=False)
    dogs.to_csv(output_dir / "underdog_games.csv", index=False)

    return summary_df, dogs


if __name__ == "__main__":
    try:
        season = int(input("Enter a season (2015-2025): "))
        week = int(input("Enter a week (1-18): "))
        spread = float(input("Enter a minimum underdog spread: "))

        summary, games = doginput(week, spread, season)
    except ValueError as error:
        print(f"Invalid input: {error}")