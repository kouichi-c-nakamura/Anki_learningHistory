# LearningHistory Tracker - Visualise your card mastery over time 

While Anki tracks interval statistics, it doesn't natively log your exact subjective feeling or trial-by-trial progress directly on the card.

LearningHistory Tracker adds a row of 4 rating buttons (✕, △, ◯, ◎) directly above Anki's standard answer buttons on the Back side of your card. After a trial, each press appends the corresponding symbol to a field named LearningHistory, letting you visually track how you went from struggling to mastering a card over time!

# Key Features

- Visual History in Note Field: Watch your progress grow (e.g., ✕✕△△△△◯◯◯△◯◯◎◎◎).
- One-Click / Shortcut Logging: Buttons/Shortcuts are active only once per review to prevent accidental double-logging.
- Mac Shortcuts Support: Press `Control + 1` (2, 3, or 4) on macOS for seamless workflow.

# Symbol Definitions

- ✕ : Failed to understand the concept.
- △ : Couldn't answer correctly, but understood the explanation.
- ◯ : Answered correctly, but lack confidence.
- ◎ : 100% confident in this card.

# ⚠️ Important Notice

Because the learning history is stored directly inside the LearningHistory Note Field (rather than standard Anki database stats), please be careful not to overwrite or wipe out this field when updating decks from external .apkg files!
