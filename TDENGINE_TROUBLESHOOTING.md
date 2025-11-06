# TDengine Connection Troubleshooting

## 🔍 Diagnostic Results

### Issue Identified: Out of Disk Space on TDengine Server

**Status**: ❌ TDengine server at `35.90.244.93:6041` is out of disk space

### Test Results:

```
✅ TEST 0: Server Reachability - PASSED
✅ TEST 1: Basic Connection - PASSED  
✅ TEST 2: Database Access - PASSED
❌ TEST 3: Table Access - FAILED (Out of disk space)
❌ TEST 4: Sample Query - FAILED (Out of disk space)
```

### What This Means:

- ✅ The server is **online and reachable**
- ✅ Your **credentials are correct**
- ✅ The **database exists**
- ❌ **Cannot query the table** due to disk space issues on the server

## 🔧 Solutions

### Immediate Action Required

**This is a server-side issue** that requires administrator intervention:

1. **Contact Server Administrator**
   - Server: 35.90.244.93
   - Issue: Disk space full
   - Impact: Cannot execute queries on sensor_frames table

2. **Check Disk Usage** (if you have server access):
   ```bash
   ssh user@35.90.244.93
   df -h
   du -sh /var/lib/taos/data/*
   ```

3. **Clean Up Options** (requires admin access):
   - Delete old log files
   - Archive or delete old sensor data
   - Clean up TDengine temporary files
   - Increase disk capacity

### Temporary Workarounds

While waiting for disk space to be freed:

#### Option 1: Use Cached/Backup Data

If you have previously exported data or backups:
```bash
# Use existing exported data
uv run python create_annotation_video.py \
    --data Data/Gen3_Annotated_Data_MVP/Raw/SL18_R1.txt \
    --annotation Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json
```

#### Option 2: Request Pre-Exported Data

Ask the server administrator to:
1. Export data directly on the server (where more space may be available)
2. Transfer the exported file to you via SCP/FTP
3. Place it in `Data/exported_from_tdengine/`

#### Option 3: Alternative TDengine Server

If there's a backup or development TDengine server:
```python
# Modify connection settings in dependent_tools/tdengine_export/tdengine_exporter.py
DEFAULT_HOST = "BACKUP_SERVER_IP"
DEFAULT_PORT = 6041
```

## 🔬 Running Diagnostics

To check the status at any time, run:

```bash
uv run python diagnose_tdengine.py
```

This will test:
- Server reachability
- Authentication
- Database access
- Table queries
- Sample data retrieval

## 📊 Understanding the Error

### TDengine Error: "Out of disk space"

This error occurs when:
1. **Disk is full**: No space for query results or temporary files
2. **Write operations**: TDengine needs space for intermediate results
3. **Large queries**: COUNT(*) queries may need temporary storage

### Why Can Connect But Not Query?

- **Connection**: Requires minimal resources
- **Queries**: Need disk space for:
  - Query execution plans
  - Temporary result sets
  - Index operations
  - Cache writes

## 🛠️ Prevention

### For Server Administrators

1. **Monitor Disk Usage**:
   ```bash
   # Set up CloudWatch alarms
   # Alert when disk usage > 80%
   ```

2. **Regular Cleanup**:
   ```bash
   # Clean old logs
   find /var/log/taos -mtime +30 -delete
   
   # Compress old data
   # Archive data older than 90 days
   ```

3. **Data Retention Policy**:
   - Implement automatic data archival
   - Set retention periods for different data types
   - Move old data to S3 or cold storage

4. **Increase Capacity**:
   - Add more disk space to the server
   - Use EBS volumes on AWS
   - Implement tiered storage

## 📞 Contact Information

### Server Details

- **Host**: 35.90.244.93
- **Port**: 6041
- **Database**: thermal_sensors_pilot
- **Issue**: Disk space full

### What to Report

When contacting the administrator, provide:

```
Subject: TDengine Server Disk Space Full

Server: 35.90.244.93:6041
Database: thermal_sensors_pilot
Error: "Out of disk space" when querying sensor_frames table
Impact: Cannot export thermal sensor data
Time: [Current date/time]

Diagnostic results: Connection works, but queries fail
Tests passed: 2/5 (Connection + Database access OK, Table queries fail)

Please free up disk space or increase storage capacity.
```

## ✅ When Issue is Resolved

After the server administrator frees up disk space:

1. **Re-run Diagnostic**:
   ```bash
   uv run python diagnose_tdengine.py
   ```

2. **Test List Sensors**:
   ```bash
   ./export_from_tdengine.sh list
   ```

3. **Export Your Data**:
   ```bash
   ./export_from_tdengine.sh 02:00:1a:62:51:67 '2025-10-13 00:35:00' '2025-10-13 01:20:00' LA
   ```

## 📝 Alternative: Manual Export

If you have SSH access to the TDengine server, you can export data manually:

```bash
# SSH to server
ssh user@35.90.244.93

# Run export on server (where there may be more space)
cd /tmp
python3 tdengine_exporter.py \
    --mac 02:00:1a:62:51:67 \
    --start "2025-10-13 07:35:00" \
    --end "2025-10-13 08:20:00" \
    --format multi_frame

# Transfer file back
scp exported_file.txt your_local_machine:~/path/
```

Note: Times need to be in UTC when running on the server (add 7 hours to LA time during PDT).

---

**Issue**: Out of disk space on TDengine server  
**Status**: ⚠️ Requires administrator action  
**Diagnostic Tool**: `diagnose_tdengine.py`  
**Last Checked**: November 6, 2025

