% QuantumSafe IDS model routing: fixed, auditable SWI-Prolog program.
% Facts are generated from locally trained and hash-verified checkpoints only.
% Format: eligible(ModelToken,ThreatToken,RecallPermille,PrecisionPermille,
%                  FalsePositivePermille,LatencyUs,Support,Integrity).
% A selected model is for SHADOW inference only, not network blocking.
:- dynamic eligible/8.

candidate(M,Threat,Score) :-
    eligible(M,Threat,Recall,Precision,Fpr,Latency,Support,1),
    Support >= 5,
    Recall >= 600,
    Fpr =< 200,
    Latency =< 500000,
    Score is (6 * Recall) + (3 * Precision) - (8 * Fpr) - (Latency // 10).

best(Threat, Model, Score) :-
    candidate(Model,Threat,Score),
    \+ (candidate(Other,Threat,OtherScore),
        (OtherScore > Score ; (OtherScore =:= Score, Other @< Model))).

run :-
    forall(best(T,M,S), (write(T),write('|'),write(M),write('|'),writeln(S))).
