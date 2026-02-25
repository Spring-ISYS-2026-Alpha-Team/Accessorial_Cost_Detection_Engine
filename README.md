# PACE - Predictive Accessorial Cost Detection Engine

## Team Alpha - Spring 2026
**University of Arkansas - ISYS 43603**

## Project Overview

PACE is a decision-support system that helps freight logistics companies predict and prevent unexpected accessorial charges (detention fees, lumper fees, layovers) before they occur. By leveraging historical shipment data and machine learning models, PACE generates risk scores and cost estimates that enable proactive operational and pricing decisions.

## Sprint 1 Deliverables

Sprint 1 focuses on foundational authentication and data management capabilities:

### Completed User Stories (19 Story Points)
- **PB-1**: User account creation (3 pts) ✅
- **PB-2**: Secure login (3 pts) ✅
- **PB-4**: Secure logout (1 pt) ✅
- **PB-5**: CSV upload for historical shipment data (5 pts) ✅
- **PB-6**: Manual shipment record creation (5 pts) ✅
- **PB-9**: View shipment details (2 pts) ✅

## Technology Stack

- **Backend**: ASP.NET Core Web API (.NET 8)
- **Frontend**: Blazor Server
- **Database**: SQL Server
- **ORM**: Entity Framework Core
- **Authentication**: ASP.NET Core Identity

## Project Structure

```
PACE/
├── Backend/
│   ├── PACE.API/              # Web API project
│   ├── PACE.Data/             # Data access layer
│   └── PACE.Models/           # Domain models
├── Frontend/
│   └── PACE.Blazor/           # Blazor Server UI
├── Database/
│   └── Scripts/               # SQL scripts
└── Documentation/
    └── Sprint1/               # Sprint 1 artifacts
```

## Setup Instructions

### Prerequisites
- .NET 8 SDK
- SQL Server 2019+ (or SQL Server Express)
- Visual Studio 2022 or VS Code
- Git

### Database Setup

1. Update connection string in `appsettings.json`:
```json
"ConnectionStrings": {
  "DefaultConnection": "Server=localhost;Database=PACE_DB;Trusted_Connection=True;TrustServerCertificate=True;"
}
```

2. Run database migrations:
```bash
cd Backend/PACE.API
dotnet ef database update
```

Or manually run the SQL script:
```bash
sqlcmd -S localhost -i Database/Scripts/01_InitialSchema.sql
```

### Running the Application

1. **Start the API**:
```bash
cd Backend/PACE.API
dotnet run
```
API will be available at: `https://localhost:7001`

2. **Start the Blazor UI**:
```bash
cd Frontend/PACE.Blazor
dotnet run
```
UI will be available at: `https://localhost:7002`

### Default Test Account
- **Username**: admin@pace.com
- **Password**: Admin@123

## Features Implemented

### Authentication & Security
- User registration with email validation
- Secure password hashing (ASP.NET Identity)
- Session-based authentication
- Secure logout with session cleanup

### Data Management
- CSV file upload with validation
- Manual shipment entry form
- Shipment listing with pagination
- Detailed shipment view
- Basic data validation

### Data Model
- Users (Authentication)
- Shipments (Core entity)
- Carriers, Facilities, Lanes (Reference data)

## Sample CSV Format

Upload shipment data using this format:

```csv
ShipmentID,OriginCity,OriginState,DestinationCity,DestinationState,CarrierName,FacilityType,AppointmentType,AppointmentDate,AppointmentTime,Distance,Weight,Pallets,EquipmentType,AccessorialOccurred,AccessorialCost
SH001,Memphis,TN,Dallas,TX,Carrier A,Grocery DC,Live Load,2024-01-15,14:00,450,42000,20,Dry Van,Yes,250.00
SH002,Chicago,IL,Indianapolis,IN,Carrier B,Manufacturing,Drop,2024-01-16,08:00,185,38000,18,Dry Van,No,0.00
```

## Team Members

| Name | Role | Responsibilities |
|------|------|-----------------|
| Clayton Josef | Scrum Master | ... |
| Tyler Connolly | Product Owner | ... |
| Bui Vu | Developer | ... |
| Anna Diggs | Developer | ... |
| Kirsten Capangpangan | Developer | ... |

## Sprint 2 Preview

Next sprint will focus on:
- **PB-7**: Update shipment records (3 pts)
- **PB-11**: Data cleaning and standardization (8 pts)
- **PB-12**: Predictive model training - Phase 1 (13 pts)

## Known Issues / Technical Debt
- CSV validation needs enhancement (file size limits, malformed data handling)
- Password complexity requirements could be stronger
- Need to add user role assignment (Admin/Analyst/Viewer)
- API error responses need standardization

## Contributing

1. Create a feature branch: `git checkout -b feature/PB-XX-description`
2. Make your changes
3. Test locally
4. Submit pull request to `dev` branch
5. After code review, merge to `main`

## License

Academic project for ISYS 43603 - University of Arkansas

## Contact

For questions or issues, contact Team Alpha via course communication channels.

---
**Last Updated**: February 24, 2026  
**Sprint**: 1 of 9  
**Status**: ✅ Sprint 1 Complete
