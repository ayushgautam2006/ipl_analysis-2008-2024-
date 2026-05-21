# IPL Analysis Project

Comprehensive analysis of IPL (Indian Premier League) cricket data from 2008-2024.

## Project Structure

```
ipl_analysis/
├── Data/                          # Raw data files
│   ├── deliveries.csv            # Match deliveries (180K+ records)
│   ├── matches.csv               # Match metadata & results
│   └── deliveries_cleaned.csv    # Cleaned deliveries dataset
│
├── Output_Files/                 # Analysis outputs & exports
│   ├── batsmen_stats.csv         # Top batsmen statistics
│   ├── bowler_stats.csv          # Top bowlers statistics
│   ├── team_stats.csv            # Team performance metrics
│   ├── phase_stats.csv           # Phase-wise analysis (Powerplay, Middle, Death)
│   ├── dismissal_summary.csv     # Dismissal patterns
│   ├── team_venue_performance.csv # Team performance by venue
│   ├── venue_summary.csv         # Venue statistics
│   └── ipl_comprehensive_dashboard.png # 9-panel visualization
│
├── notebooks/                     # Jupyter notebooks
│   └── ipl_insights.ipynb        # Main analysis notebook (42 cells)
│
├── README.md                      # This file
└── .venv/                        # Python virtual environment
```

## Quick Start

### Setup
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies (if needed)
pip install pandas numpy matplotlib seaborn pillow
```

### Run Analysis
```bash
jupyter notebook notebooks/ipl_insights.ipynb
```

## Analysis Sections

1. **Data Cleaning**: Type conversion, missing values, duplicates, validation
2. **Venue Analysis**: Performance by location, pitch characteristics
3. **Player Analysis**: Top batsmen (runs, strike rate), Top bowlers (wickets, economy)
4. **Team Performance**: Win rates, statistics, head-to-head records
5. **Innings Breakdown**: Phase-wise analysis (Powerplay 0-5, Middle 6-15, Death 16-19)
6. **Dismissal Patterns**: Methods, vulnerable players, fielding stats
7. **Comprehensive Dashboard**: 9-panel visualization summary
8. **Data Exports**: 8 CSV files with detailed statistics

## Key Insights

- **Total Matches Analyzed**: 1000+
- **Total Deliveries**: 180,000+
- **Teams**: 19 IPL franchises
- **Venues**: 58 unique cricket grounds
- **Players**: 500+ batsmen, 500+ bowlers

## Output Files

All analysis results are in `Output_Files/`:
- **CSV Files**: Ready for further analysis in Excel/Python
- **Dashboard PNG**: Visual summary of all analyses
- **Venue Files**: Detailed venue-specific performance

## Requirements

- Python 3.13.3+
- pandas
- numpy
- matplotlib
- seaborn
- Pillow

---

*Project completed: May 2026*
*Data: IPL 2008-2024*
