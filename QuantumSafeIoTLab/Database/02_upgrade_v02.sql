/* QuantumSafe v0.2: ADDITIVE upgrade for existing SQL Server 2022 database.
   Run in SSMS after creating database with 01_create_database.sql.
   SAFE: does not delete or change your existing Users, Experiments, or results.
   Security events contain metadata ONLY; never keys, passwords or readings. */
USE QuantumSafeIoTLab;
GO
IF OBJECT_ID(N'dbo.SecurityEvents', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SecurityEvents (
        EventId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ActorId INT NULL,
        EventName VARCHAR(40) NOT NULL,
        Outcome VARCHAR(12) NOT NULL
            CONSTRAINT CK_SecurityEvents_Outcome CHECK (Outcome IN ('Accepted','Rejected','Error')),
        SourceIp VARCHAR(64) NULL,
        Algorithm VARCHAR(12) NULL
            CONSTRAINT CK_SecurityEvents_Algorithm CHECK (
                Algorithm IS NULL OR Algorithm IN ('ML-KEM-512','ML-KEM-768','ML-KEM-1024')),
        CreatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_SecurityEvents_Created DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_SecurityEvents_Actor FOREIGN KEY (ActorId) REFERENCES dbo.Users(UserId)
    );
    CREATE INDEX IX_SecurityEvents_Recent ON dbo.SecurityEvents(EventId DESC);
END;
GO
SELECT name FROM sys.tables WHERE name = N'SecurityEvents';
GO
