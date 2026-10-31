/* QuantumSafe IoT Lab — Phase 2 PROPOSED schema.
   SQL Server 2022. Run only on a verified local dev database.
   No credentials, ML-KEM secret keys, shared secrets or ciphertext stored.
   NOT YET TESTED on the user's SQL Server instance. */

IF DB_ID(N'QuantumSafeIoTLab') IS NULL
    EXEC(N'CREATE DATABASE [QuantumSafeIoTLab]');
GO
USE QuantumSafeIoTLab;
GO

IF OBJECT_ID(N'dbo.Users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Users (
        UserId INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        Username NVARCHAR(50) NOT NULL UNIQUE,
        PasswordHash NVARCHAR(255) NOT NULL,
        RoleName VARCHAR(20) NOT NULL
            CONSTRAINT CK_Users_Role CHECK (RoleName IN ('Admin', 'Researcher', 'Viewer')),
        IsActive BIT NOT NULL CONSTRAINT DF_Users_Active DEFAULT (1),
        CreatedAtUtc DATETIME2(3) NOT NULL CONSTRAINT DF_Users_Created DEFAULT (SYSUTCDATETIME())
    );
END;
GO

IF OBJECT_ID(N'dbo.Experiments', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Experiments (
        ExperimentId INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        OwnerId INT NOT NULL,
        Algorithm VARCHAR(12) NOT NULL
            CONSTRAINT CK_Experiments_Algorithm CHECK (Algorithm IN ('ML-KEM-512','ML-KEM-768','ML-KEM-1024')),
        TrialCount SMALLINT NOT NULL
            CONSTRAINT CK_Experiments_TrialCount CHECK (TrialCount BETWEEN 1 AND 1000),
        RunStatus VARCHAR(12) NOT NULL
            CONSTRAINT DF_Experiments_Status DEFAULT ('Pending')
            CONSTRAINT CK_Experiments_Status CHECK (RunStatus IN ('Pending','Running','Completed','Failed')),
        EnvInfo NVARCHAR(MAX) NULL, /* JSON metadata only: platform, package version, etc. */
        StartedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_Experiments_Start DEFAULT (SYSUTCDATETIME()),
        EndedAtUtc DATETIME2(3) NULL,
        CONSTRAINT FK_Experiments_Users FOREIGN KEY (OwnerId)
            REFERENCES dbo.Users(UserId),
        CONSTRAINT CK_Experiments_EnvInfo CHECK (EnvInfo IS NULL OR ISJSON(EnvInfo) = 1),
        CONSTRAINT CK_Experiments_EndTime CHECK (EndedAtUtc IS NULL OR EndedAtUtc >= StartedAtUtc)
    );
END;
GO

IF OBJECT_ID(N'dbo.Measurements', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Measurements (
        MeasurementId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        ExperimentId INT NOT NULL,
        OperationName VARCHAR(15) NOT NULL
            CONSTRAINT CK_Measurements_Operation CHECK (OperationName IN ('KeyGen','Encaps','Decaps')),
        TrialIndex SMALLINT NOT NULL
            CONSTRAINT CK_Measurements_Trial CHECK (TrialIndex BETWEEN 1 AND 1000),
        DurationNs BIGINT NOT NULL
            CONSTRAINT CK_Measurements_Duration CHECK (DurationNs >= 0),
        CreatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_Measurements_Created DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_Measurements_Experiments FOREIGN KEY (ExperimentId)
            REFERENCES dbo.Experiments(ExperimentId),
        CONSTRAINT UQ_Measurements_RunOpTrial UNIQUE (ExperimentId, OperationName, TrialIndex)
    );
END;
GO

IF OBJECT_ID(N'dbo.SecureDemoTests', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SecureDemoTests (
        DemoTestId INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        UserId INT NOT NULL,
        Algorithm VARCHAR(12) NOT NULL
            CONSTRAINT CK_Demo_Algorithm CHECK (Algorithm IN ('ML-KEM-512','ML-KEM-768','ML-KEM-1024')),
        Tampered BIT NOT NULL,
        Passed BIT NOT NULL, /* expected outcome met (tamper is rejected) */
        StatusDetail NVARCHAR(160) NULL,
        CreatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_Demo_Created DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_Demo_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(UserId)
    );
END;
GO

IF OBJECT_ID(N'dbo.AuditLogs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.AuditLogs (
        AuditId BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        UserId INT NULL, /* anonymous failed login may not resolve to user */
        ActionName VARCHAR(40) NOT NULL,
        WasSuccessful BIT NOT NULL,
        ShortDetail NVARCHAR(160) NULL, /* never log passwords/secrets */
        CreatedAtUtc DATETIME2(3) NOT NULL
            CONSTRAINT DF_Audit_Created DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_Audit_Users FOREIGN KEY (UserId) REFERENCES dbo.Users(UserId)
    );
END;
GO

/* Create the very first Admin through a one-time Python setup routine that
   hashes password with Argon2id. Never hard-code a plaintext password here. */
