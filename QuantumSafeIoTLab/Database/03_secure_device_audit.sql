/* SQL Server 2022: repeatable encrypted virtual device event audit migration.
   Do not store ciphertext/session secrets/private keys in SQL. */
USE [QuantumSafeIoTLab];
GO
IF OBJECT_ID(N'dbo.VirtualGatewayEvents',N'U') IS NOT NULL
BEGIN
    IF COL_LENGTH('dbo.VirtualGatewayEvents','CryptoAlgorithm') IS NULL ALTER TABLE dbo.VirtualGatewayEvents ADD CryptoAlgorithm NVARCHAR(64) NULL;
    IF COL_LENGTH('dbo.VirtualGatewayEvents','CryptoRecipient') IS NULL ALTER TABLE dbo.VirtualGatewayEvents ADD CryptoRecipient NVARCHAR(64) NULL;
    IF COL_LENGTH('dbo.VirtualGatewayEvents','CryptoVerified') IS NULL ALTER TABLE dbo.VirtualGatewayEvents ADD CryptoVerified BIT NULL;
    IF COL_LENGTH('dbo.VirtualGatewayEvents','CryptoCiphertextBytes') IS NULL ALTER TABLE dbo.VirtualGatewayEvents ADD CryptoCiphertextBytes INT NULL;
    IF COL_LENGTH('dbo.VirtualGatewayEvents','CryptoKEMCiphertextBytes') IS NULL ALTER TABLE dbo.VirtualGatewayEvents ADD CryptoKEMCiphertextBytes INT NULL;
    IF COL_LENGTH('dbo.VirtualGatewayEvents','CryptoCiphertextSha256') IS NULL ALTER TABLE dbo.VirtualGatewayEvents ADD CryptoCiphertextSha256 CHAR(64) NULL;
END;
GO
/* Verify durable evidence of encrypted virtual messages (requires authenticated events). */
SELECT TOP (20) EventTimeUtc, DeviceId, CryptoRecipient, Decision, Reason,
    CryptoAlgorithm, CryptoVerified, CryptoCiphertextBytes,
    CryptoKEMCiphertextBytes, CryptoCiphertextSha256
FROM dbo.VirtualGatewayEvents WHERE RequestType='encrypted_mesh' ORDER BY EventId DESC;
GO
