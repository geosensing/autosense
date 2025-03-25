## AutoSense: Automated Street Condition Assessment

AutoSense is an automated system for assessing street conditions at scale using geospatial data, street-level imagery, and computer vision. The system works by:

1. Randomly sampling street locations from OpenStreetMap (OSM)
2. Fetching street-level imagery from Google Street View API
3. Analyzing the imagery using Google Cloud Vision API to assess street conditions

This tool enables urban planners, transportation departments, and researchers to efficiently evaluate road infrastructure quality without extensive manual fieldwork.

## Features

- **Random Street Sampling**: Extracts and samples street segments from OpenStreetMap data
- **Coordinate Interpolation**: Generates evenly distributed sampling points along street segments
- **Street View Image Acquisition**: Retrieves high-quality street-level imagery with randomized viewing angles
- **Computer Vision Analysis**: Leverages Google's Vision API to detect and classify:
  - Road surface conditions (potholes, cracks, etc.)
  - Street furniture (signs, lights, benches)
  - Accessibility features (ramps, tactile paving)
  - Vegetation and green infrastructure

## Prerequisites

- Python 3.8+
- Google Cloud Platform account with the following APIs enabled:
  - Google Street View Static API
  - Google Cloud Vision API
- API keys stored in separate text files (for security)
- OSM data for your region of interest

