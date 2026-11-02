% Local and deterministic: rules explain evidence, never train or deploy models.
:- dynamic flag/1.
recommendation(no_training) :- \+ flag(has_training).
recommendation(high_fpr) :- flag(high_fpr).
recommendation(unstable_folds) :- flag(unstable_folds).
recommendation(truncated_dataset) :- flag(dataset_truncated).
recommendation(blocked_incidents) :- flag(blocked_events).
recommendation(known_attack_types) :- flag(known_attack_types).
recommendation(live_unverified).
