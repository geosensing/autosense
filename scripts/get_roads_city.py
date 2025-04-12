import os
import shapefile
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from pathlib import Path

class OSMCityPipeline:
    def __init__(self, base_shapefile_path, output_dir="./output"):
        """
        Initialize the OSM city pipeline.
        
        Args:
            base_shapefile_path (str): Path to the base shapefile containing city boundaries
            output_dir (str): Directory to save output maps and data
        """
        self.base_shapefile_path = base_shapefile_path
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def process_city(self, city_name, city_field_name="NAME_2", 
                     roads_shapefile_path=None, road_types_of_interest=None):
        """
        Process a single city: extract boundaries, get roads, create visualizations.
        
        Args:
            city_name (str): Name of the city to process (e.g., "Mumbai City")
            city_field_name (str): Field name in the shapefile that contains city names
            roads_shapefile_path (str): Path to roads shapefile, if None will be inferred
            road_types_of_interest (list): List of road types to include, defaults to common types
        """
        print(f"\nProcessing {city_name}...")
        
        # Set default road types if not provided
        if road_types_of_interest is None:
            road_types_of_interest = ["residential", "primary", "secondary", "tertiary"]
        
        # 1. Extract city boundaries
        city_shapes, bbox = self._extract_city_boundaries(city_name, city_field_name)
        
        # 2. Generate BBBike URL for data extraction
        bbbike_url = self._generate_bbbike_url(bbox)
        print(f"BBBike Extract URL for {city_name}: {bbbike_url}")
        
        # 3. Plot and save city boundaries
        self._plot_city_boundaries(city_name, city_shapes)
        
        # 4. Process roads if shapefile is provided or can be inferred
        if roads_shapefile_path is None:
            # Try to infer the roads shapefile path from base shapefile path and city name
            base_dir = os.path.dirname(self.base_shapefile_path)
            country_code = os.path.basename(self.base_shapefile_path).split('_')[1]
            roads_shapefile_path = os.path.join(base_dir, f"{country_code}_{country_code}.20_1+{city_name}_roads.shp")
            print(f"Inferred roads shapefile path: {roads_shapefile_path}")
        
        if os.path.exists(roads_shapefile_path):
            road_shapes, road_df = self._extract_road_data(roads_shapefile_path, road_types_of_interest)
            self._plot_city_roads(city_name, road_shapes)
            
            # 5. Save road data to CSV
            output_csv = os.path.join(self.output_dir, f"{city_name.replace(' ', '_')}_roads.csv")
            road_df.to_csv(output_csv, index=False)
            print(f"Road data saved to {output_csv}")
        else:
            print(f"Warning: Road shapefile not found at {roads_shapefile_path}")
        
        print(f"Completed processing {city_name}")
        return {
            "city_name": city_name,
            "bbox": bbox,
            "bbbike_url": bbbike_url
        }
    
    def _extract_city_boundaries(self, city_name, city_field_name):
        """Extract city boundary shapes from the base shapefile."""
        sf = shapefile.Reader(self.base_shapefile_path)
        fields = [field[0] for field in sf.fields[1:]]  # Ignore DeletionFlag
        records = sf.records()
        
        # Find the index of the city field name
        try:
            name_index = fields.index(city_field_name)
        except ValueError:
            print(f"Field '{city_field_name}' not found in shapefile. Available fields: {fields}")
            raise
        
        # Extract shapes for the specified city
        city_shapes = [shape for record, shape in zip(records, sf.shapes()) 
                       if record[name_index] == city_name]
        
        if not city_shapes:
            raise ValueError(f"City '{city_name}' not found in the shapefile using field '{city_field_name}'")
        
        # Calculate bounding box
        all_points = [point for shape in city_shapes for point in shape.points]
        min_x = min(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_x = max(p[0] for p in all_points)
        max_y = max(p[1] for p in all_points)
        
        bbox = (min_x, min_y, max_x, max_y)
        return city_shapes, bbox
    
    def _generate_bbbike_url(self, bbox):
        """Generate a BBBike URL for extracting OSM data for the specified bounding box."""
        min_x, min_y, max_x, max_y = bbox
        return f"http://extract.bbbike.org/?sw_lng={min_x}&sw_lat={min_y}&ne_lng={max_x}&ne_lat={max_y}"
    
    def _plot_city_boundaries(self, city_name, city_shapes):
        """Plot and save city boundaries."""
        plt.figure(figsize=(10, 8))
        for shape in city_shapes:
            x, y = zip(*shape.points)
            plt.plot(x, y, 'b', linewidth=1)
        plt.title(f"{city_name} - Administrative Boundaries")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.grid(True)
        
        # Save the figure
        output_file = os.path.join(self.output_dir, f"{city_name.replace(' ', '_')}_boundaries.png")
        plt.savefig(output_file, dpi=300)
        plt.close()
        print(f"City boundaries map saved to {output_file}")
    
    def _extract_road_data(self, roads_shapefile_path, road_types_of_interest):
        """Extract road data from the roads shapefile."""
        sf = shapefile.Reader(roads_shapefile_path)
        fields = [field[0] for field in sf.fields[1:]]
        records = sf.records()
        
        # Find the road type field
        road_type_candidates = ["type", "highway", "road_type", "roadtype", "class"]
        road_type_field = None
        
        for candidate in road_type_candidates:
            if candidate in fields:
                road_type_field = candidate
                break
        
        if road_type_field is None:
            print(f"Warning: Could not find road type field. Available fields: {fields}")
            print("Using first field as fallback")
            road_type_field = fields[0]
        
        road_type_index = fields.index(road_type_field)
        print(f"Using '{road_type_field}' as road type field")
        
        # Get unique road types
        unique_road_types = set(record[road_type_index] for record in records)
        print(f"Unique road types: {unique_road_types}")
        
        # Extract roads of interest
        selected_roads = [shape for record, shape in zip(records, sf.shapes()) 
                         if record[road_type_index] in road_types_of_interest]
        
        # Extract road data for DataFrame
        road_data = []
        for record, shape in zip(records, sf.shapes()):
            if record[road_type_index] not in road_types_of_interest:
                continue
            if shape.shapeType == 3:  # Ensure it's a polyline
                if shape.points:  # Check if there are any points
                    start_lat, start_long = shape.points[0]
                    end_lat, end_long = shape.points[-1]
                    road_data.append(list(record) + [start_lat, start_long, end_lat, end_long])
        
        # Create DataFrame
        df_roads = pd.DataFrame(road_data, columns=fields + ["start_lat", "start_long", "end_lat", "end_long"])
        
        return selected_roads, df_roads
    
    def _plot_city_roads(self, city_name, road_shapes):
        """Plot and save city roads."""
        plt.figure(figsize=(12, 10))
        for shape in road_shapes:
            x, y = zip(*shape.points)
            plt.plot(x, y, 'b', linewidth=0.8)
        plt.title(f"Roads in {city_name}")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.grid(True)
        
        # Save the figure
        output_file = os.path.join(self.output_dir, f"{city_name.replace(' ', '_')}_roads.png")
        plt.savefig(output_file, dpi=300)
        plt.close()
        print(f"City roads map saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Process OSM road data for multiple cities')
    parser.add_argument('--base_shapefile', required=True, help='Path to base shapefile with city boundaries')
    parser.add_argument('--output_dir', default='./output', help='Directory to save output maps and data')
    parser.add_argument('--cities', required=True, nargs='+', help='List of city names to process')
    parser.add_argument('--city_field', default='NAME_2', help='Field name in shapefile for city names')
    parser.add_argument('--road_types', nargs='+', default=['residential', 'primary', 'secondary', 'tertiary'],
                        help='Road types to include')
    parser.add_argument('--roads_shapefile', default=None, help='Optional path to roads shapefile')
    
    args = parser.parse_args()
    
    # Initialize the pipeline
    pipeline = OSMCityPipeline(args.base_shapefile, args.output_dir)
    
    # Process each city
    for city_name in args.cities:
        try:
            pipeline.process_city(city_name, args.city_field, args.roads_shapefile, args.road_types)
        except Exception as e:
            print(f"Error processing {city_name}: {e}")
    
    print("\nAll cities processed. Output saved to:", args.output_dir)


if __name__ == "__main__":
    main()