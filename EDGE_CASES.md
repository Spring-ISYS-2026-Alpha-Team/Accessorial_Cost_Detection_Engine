# Edge Cases and Failure Modes

## Purpose
This document catalogs known edge cases, system limitations, and potential failure modes for the Predictive Accessorial Cost Detection Engine (PACE). Use this as a reference for testing, validation, and error handling implementation.

**Last Updated:** February 25, 2026  
**Maintained By:** Team Alpha - Data Engineering & QA

---

## 1. CSV Upload Edge Cases

### 1.1 Empty CSV File
**Description:** User uploads a CSV with only headers, no data rows  
**Impact:** System cannot train ML model or display data  
**Expected Handling:** Display error message "CSV file is empty - no data rows found. Please upload a file with at least 10 shipment records."  
**Test Case:** Upload file with only header row

### 1.2 Missing Required Columns
**Description:** CSV is missing one or more required fields (ShipmentID, CarrierName, Origin, Destination, etc.)  
**Impact:** Validation fails, cannot process data  
**Expected Handling:** List all missing required columns in validation error message  
**Test Case:** Upload CSV missing "CarrierName" column

### 1.3 Extra/Unknown Columns
**Description:** CSV contains columns not defined in schema (e.g., "InternalNotes", "CustomerPO")  
**Impact:** Extra columns are ignored, may confuse users  
**Expected Handling:** Display warning listing extra columns that will be ignored  
**Test Case:** Upload CSV with additional "Notes" column

### 1.4 File Size Exceeds Limit
**Description:** CSV file larger than 10MB  
**Impact:** Slow processing, potential timeout, memory issues  
**Expected Handling:** Reject with error "File size exceeds 10MB limit. Please split into smaller files."  
**Test Case:** Upload 15MB CSV file

### 1.5 Invalid File Extension
**Description:** User uploads .xlsx, .txt, or other non-CSV file  
**Impact:** Parser fails or reads garbage data  
**Expected Handling:** Reject with error "Only .csv files are supported. Please export as CSV format."  
**Test Case:** Upload Excel file (.xlsx)

### 1.6 Encoding Issues (Non-UTF-8)
**Description:** CSV saved with Latin-1, CP1252, or other encoding  
**Impact:** Special characters (é, ñ, ™) display incorrectly  
**Expected Handling:** Auto-detect encoding or display warning "Special characters detected - ensure file is UTF-8 encoded"  
**Test Case:** Upload CSV with facility name "Frëïght™ Wårehouse"

### 1.7 Malformed CSV Structure
**Description:** Unclosed quotes, inconsistent column counts per row  
**Impact:** CSV parser fails completely  
**Expected Handling:** Display parsing error with specific line number where error occurred  
**Test Case:** Upload CSV with unclosed quote in row 15

---

## 2. Data Validation Edge Cases

### 2.1 Null Values in Required Fields
**Description:** Critical fields like CarrierName, Distance, or AppointmentDate are empty/NULL  
**Impact:** Cannot process record, violates database constraints  
**Expected Handling:** List all rows with null required fields in validation report before import  
**Test Case:** Row 10 has empty CarrierName field

### 2.2 Negative Distance or Weight
**Description:** Distance = -500 or Weight = -10000  
**Impact:** Physically impossible, corrupts ML model training  
**Expected Handling:** Flag as validation error "Row X: Distance must be greater than 0"  
**Test Case:** Distance = -450.00

### 2.3 Distance Greater Than 5000 Miles
**Description:** Shipment distance exceeds realistic US domestic limit  
**Impact:** Likely data entry error or international shipment  
**Expected Handling:** Warning "Row X: Distance of 6000 miles exceeds typical US range. Verify accuracy."  
**Test Case:** Distance = 6500 miles

### 2.4 Future Appointment Dates
**Description:** AppointmentDate is tomorrow or later  
**Impact:** Cannot be historical training data  
**Expected Handling:** Warning "Row X: Future date detected. Use only historical data for training."  
**Test Case:** AppointmentDate = 2026-03-01 (future)

### 2.5 Invalid Categorical Values
**Description:** FacilityType = "Unknown" or AppointmentType = "TBD" (not in predefined list)  
**Impact:** ML model cannot process unknown categories  
**Expected Handling:** Error listing invalid values and showing valid options  
**Test Case:** FacilityType = "Customer Warehouse" (not in valid list)

### 2.6 Duplicate Shipment IDs
**Description:** Same ShipmentID appears in multiple rows  
**Impact:** Database primary key constraint violation  
**Expected Handling:** List all duplicate IDs, allow user to choose: skip duplicates, update existing, or cancel  
**Test Case:** ShipmentID "SH001" appears in rows 5 and 12

### 2.7 Text in Numeric Fields
**Description:** Distance = "approximately 1000" or Weight = "heavy"  
**Impact:** Type conversion fails  
**Expected Handling:** Error "Row X: Distance must be numeric value"  
**Test Case:** Distance = "about 500"

### 2.8 Invalid State Codes
**Description:** OriginState = "ZZ" or "California" instead of "CA"  
**Impact:** Lookup failures, invalid location data  
**Expected Handling:** Error "Row X: Invalid state code 'ZZ'. Use 2-letter abbreviation."  
**Test Case:** OriginState = "Texas" (should be "TX")

### 2.9 AccessorialCost Without AccessorialOccurred Flag
**Description:** AccessorialOccurred = No, but AccessorialCost = $250  
**Impact:** Data inconsistency  
**Expected Handling:** Warning "Row X: Cost present but flag is 'No'. Auto-correcting flag to 'Yes'."  
**Test Case:** AccessorialOccurred = false, AccessorialCost = 150.00

---

## 3. Machine Learning Model Edge Cases

### 3.1 Insufficient Training Data (<100 Records)
**Description:** Dataset has only 50 shipments  
**Impact:** High variance, unreliable predictions, overfitting  
**Expected Handling:** Block model training with error "Minimum 100 historical records required. Current: 50."  
**Test Case:** Upload CSV with 75 rows

### 3.2 No Variation in Outcomes (All True or All False)
**Description:** All shipments have AccessorialOccurred = Yes  
**Impact:** Model cannot learn patterns (no negative examples to contrast)  
**Expected Handling:** Error "Cannot train model - all records have same outcome. Need both Yes and No examples."  
**Test Case:** 200 rows all with AccessorialOccurred = true

### 3.3 Extreme Class Imbalance
**Description:** 98% of shipments have AccessorialOccurred = No, 2% = Yes  
**Impact:** Model biased toward majority class, poor minority class predictions  
**Expected Handling:** Warning "Severe class imbalance detected (98/2). Model may have low sensitivity. Consider class weighting."  
**Test Case:** 980 No, 20 Yes

### 3.4 Missing Features During Prediction
**Description:** Historical data has "Weight" field, new shipment missing it  
**Impact:** Prediction fails or uses default/imputed values  
**Expected Handling:** Use median weight from training set as default, display warning  
**Test Case:** Training data has Weight, prediction input omits it

### 3.5 Feature Values Outside Training Range
**Description:** Training max distance = 4000 miles, new shipment = 6000 miles  
**Impact:** Model extrapolating beyond known data (unreliable)  
**Expected Handling:** Warning "Distance 6000 exceeds training maximum of 4000. Prediction reliability reduced."  
**Test Case:** Predict with Distance = 6500 when training max = 4200

### 3.6 Single Carrier Dominance
**Description:** 95% of training data from one carrier  
**Impact:** Model works well for that carrier, poorly for others  
**Expected Handling:** Warning "Training data dominated by CarrierA (95%). Predictions may be unreliable for other carriers."  
**Test Case:** 950 rows "Carrier A", 50 rows all other carriers

---

## 4. Database Edge Cases

### 4.1 Database Connection Failure
**Description:** SQL Server is unreachable (wrong credentials, server down, network issue)  
**Impact:** Cannot save or retrieve any data  
**Expected Handling:** Display connection error page with troubleshooting steps, suggest checking .env credentials  
**Test Case:** Stop SQL Server service, attempt CSV upload

### 4.2 Database Timeout on Large Insert
**Description:** Inserting 10,000 rows takes >30 seconds  
**Impact:** Operation times out before completion  
**Expected Handling:** Use bulk insert operations, increase timeout, or batch into chunks of 1000  
**Test Case:** Upload 15,000 row CSV

### 4.3 Duplicate Carrier Names with Different Casing
**Description:** "ABC Freight" and "abc freight" treated as different carriers  
**Impact:** Lookup ambiguity, data fragmentation  
**Expected Handling:** Normalize to Title Case on insert, warn user of near-duplicates  
**Test Case:** Upload rows with "XPO Logistics", "xpo logistics", "XPO LOGISTICS"

### 4.4 Missing Foreign Key (Carrier Doesn't Exist)
**Description:** Shipment references CarrierID = 99 but Carriers table only has IDs 1-50  
**Impact:** Foreign key constraint violation  
**Expected Handling:** Auto-create missing carrier entry OR reject with error  
**Test Case:** Reference non-existent CarrierID

### 4.5 Concurrent Write Conflicts
**Description:** Two users upload CSVs simultaneously  
**Impact:** Race conditions, duplicate inserts, or partial failures  
**Expected Handling:** Implement transaction isolation, queue uploads  
**Test Case:** Two users click "Upload" at exact same time

---

## 5. API & Integration Edge Cases

### 5.1 Unauthenticated API Access Attempt
**Description:** External tool tries to call API without valid authentication token  
**Impact:** Security breach risk  
**Expected Handling:** Return 401 Unauthorized with error message  
**Test Case:** Call /api/shipments without Authorization header

### 5.2 Malformed JSON in API Request
**Description:** POST request body has invalid JSON syntax  
**Impact:** Cannot parse request  
**Expected Handling:** Return 400 Bad Request with JSON parsing error details  
**Test Case:** Send request with missing closing brace `}`

### 5.3 SQL Injection Attempt
**Description:** User enters `'; DROP TABLE Shipments; --` in carrier name field  
**Impact:** Potential data loss if not using parameterized queries  
**Expected Handling:** Parameterized queries prevent execution, value stored as literal string  
**Test Case:** Enter SQL commands in text fields

---

## 6. UI/UX Edge Cases

### 6.1 Browser Zoom at 150%+
**Description:** User has browser zoom set to 200%  
**Impact:** Layout breaks, buttons overlap, text truncated  
**Expected Handling:** Responsive CSS ensures usability at zoom levels 100-200%  
**Test Case:** Set browser zoom to 175%, navigate all pages

### 6.2 Extremely Long Facility Names
**Description:** FacilityName = "Amazon Fulfillment Center - Dallas-Fort Worth Regional Distribution Warehouse #5"  
**Impact:** Breaks table layout, overflows columns  
**Expected Handling:** Truncate display to 50 chars, show full name in tooltip on hover  
**Test Case:** Enter 200-character facility name

### 6.3 Slow Network Connection
**Description:** User on 3G mobile connection uploads 5MB CSV  
**Impact:** Long wait with no progress indicator  
**Expected Handling:** Display upload progress bar, allow cancellation  
**Test Case:** Throttle network to 3G speed, upload large file

---

## 7. Known System Limitations

| Limitation | Description | Workaround |
|------------|-------------|------------|
| **File Format** | Only CSV supported (not Excel, JSON, XML) | Export Excel to CSV first |
| **Authentication** | No user login system (planned Sprint 4) | Single-user mode only |
| **Real-time Prediction** | Batch processing only, no API endpoint | Upload all predictions as batch |
| **Model Retraining** | Manual trigger only (no automatic) | Admin must manually retrain |
| **Data Export** | Limited to CSV (PDF export planned Sprint 3) | Use CSV export for now |
| **Concurrent Users** | No session management or multi-user support | Single user at a time |
| **Max File Size** | 10MB upload limit | Split large files into chunks |
| **Historical Data Only** | No real-time carrier API integration | Manual data entry |

---

## Testing Recommendations

### High Priority Test Scenarios
1. **Upload empty CSV** - verify error message clarity
2. **Upload CSV with null required fields** - verify validation catches all issues
3. **Upload CSV with negative distance** - verify range validation
4. **Train model with <100 records** - verify minimum data requirement enforced
5. **Train model with all same outcome** - verify error handling

### Medium Priority Test Scenarios
6. **Upload CSV with special characters** - verify encoding handling
7. **Upload very large file (15MB)** - verify size limit enforcement
8. **Duplicate ShipmentID** - verify duplicate handling logic
9. **Database connection failure** - verify graceful error display
10. **Extreme class imbalance (99/1)** - verify warning appears

### Low Priority Test Scenarios
11. **Browser zoom edge cases** - verify responsive design
12. **Slow network upload** - verify progress indication
13. **Long facility names** - verify text truncation

---

## Maintenance Notes

This document should be updated whenever:
- New validation rules are added
- New data fields are introduced
- Edge cases are discovered in production
- System limitations change

**Review Schedule:** End of each sprint  
**Owner:** Data Engineering Team

---

**Document Version:** 1.0  
**Created:** February 25, 2026  
**Contributor:** Kirsten Capangpangan