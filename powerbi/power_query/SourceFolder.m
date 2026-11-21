// ============================================================================
// Parameter: SourceFolder
// Description: Defines the folder path containing the exported star schema CSV files.
// Set this parameter in Power BI Desktop to your local data/processed/powerbi_input directory path.
// Example: "C:\Projects\Olist\data\processed\powerbi_input" or relative "./data/processed/powerbi_input"
// ============================================================================

"./data/processed/powerbi_input" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
