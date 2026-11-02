% Read-only incident classification. Fixed offline Prolog program.
% event_counts(DeviceToken,Blocked,Replay,CryptoAuthFailures,UnknownDevice,RateLimit).
:- dynamic event_counts/6.

severity(D, Severity) :-
    event_counts(D, Blocked, Replay, Crypto, Unknown, Rate),
    (   (Replay >= 3 ; Crypto >= 3) -> Severity = critical
    ;   (Blocked >= 5 ; Unknown >= 2 ; Rate >= 3) -> Severity = high
    ;   Severity = medium
    ).

advice(D, rotate_review) :- event_counts(D,_,_,Crypto,_,_), Crypto >= 2.
advice(D, quarantine_review) :- event_counts(D,_,Replay,_,Unknown,_), (Replay >= 3 ; Unknown >= 2).
advice(D, investigate) :- event_counts(D,Blocked,_,_,_,_), Blocked >= 1.

run :-
    forall(severity(D,S), (write('risk|'),write(D),write('|'),writeln(S))),
    forall(advice(D,A), (write('advice|'),write(D),write('|'),writeln(A))).
