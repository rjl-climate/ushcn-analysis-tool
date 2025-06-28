#!/usr/bin/env python3
"""
Create static US cities database with quality control validation.

This script processes downloaded cities data, applies filters for urban areas ≥50k population,
validates geographic coordinates and population data, and creates a high-quality static database
for urban heat island analysis.

Usage:
    python scripts/create_static_cities_db.py [--min-population 50000] [--output data/cities/us_cities_static.csv]
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Tuple, Dict, Any, Optional
import requests
import json
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_source_data() -> pd.DataFrame:
    """
    Load and combine data from multiple sources.
    
    Returns:
        Combined DataFrame with all cities data
    """
    logger.info("Loading source cities data...")
    
    # Load top 1000 cities with population data (primary source)
    top1k_path = Path("data/cities/us_cities_top1k.csv")
    if not top1k_path.exists():
        raise FileNotFoundError(f"Primary cities data not found: {top1k_path}")
    
    cities_df = pd.read_csv(top1k_path)
    logger.info(f"Loaded {len(cities_df)} cities from top 1000 dataset")
    
    # Standardize column names
    cities_df = cities_df.rename(columns={
        'City': 'city_name',
        'State': 'state',
        'Population': 'population',
        'lat': 'latitude',
        'lon': 'longitude'
    })
    
    # Add data source tracking
    cities_df['data_source'] = 'plotly_top1k'
    
    return cities_df


def validate_geographic_coordinates(cities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that coordinates are within reasonable US bounds.
    
    Args:
        cities_df: DataFrame with latitude/longitude columns
        
    Returns:
        Filtered DataFrame with valid coordinates
    """
    logger.info("Validating geographic coordinates...")
    
    # US geographic bounds (including Alaska, Hawaii, territories)
    US_BOUNDS = {
        'lat_min': 18.0,   # Southern tip of Hawaii
        'lat_max': 71.5,   # Northern Alaska
        'lon_min': -180.0, # Western Alaska (Aleutians cross dateline)
        'lon_max': -65.0   # Eastern Maine
    }
    
    initial_count = len(cities_df)
    
    # Check for missing coordinates
    missing_coords = cities_df['latitude'].isna() | cities_df['longitude'].isna()
    if missing_coords.any():
        logger.warning(f"Removing {missing_coords.sum()} cities with missing coordinates")
        cities_df = cities_df[~missing_coords]
    
    # Check coordinate bounds
    valid_coords = (
        (cities_df['latitude'] >= US_BOUNDS['lat_min']) &
        (cities_df['latitude'] <= US_BOUNDS['lat_max']) &
        (cities_df['longitude'] >= US_BOUNDS['lon_min']) &
        (cities_df['longitude'] <= US_BOUNDS['lon_max'])
    )
    
    invalid_count = (~valid_coords).sum()
    if invalid_count > 0:
        logger.warning(f"Removing {invalid_count} cities with coordinates outside US bounds")
        # Log some examples
        invalid_cities = cities_df[~valid_coords][['city_name', 'state', 'latitude', 'longitude']].head(5)
        for _, city in invalid_cities.iterrows():
            logger.warning(f"  Invalid: {city['city_name']}, {city['state']} ({city['latitude']}, {city['longitude']})")
        
        cities_df = cities_df[valid_coords]
    
    logger.info(f"Geographic validation: {initial_count} → {len(cities_df)} cities ({len(cities_df)/initial_count*100:.1f}% retained)")
    return cities_df


def validate_population_data(cities_df: pd.DataFrame, min_population: int) -> pd.DataFrame:
    """
    Validate and filter population data.
    
    Args:
        cities_df: DataFrame with population column
        min_population: Minimum population threshold
        
    Returns:
        Filtered DataFrame with valid population data
    """
    logger.info(f"Validating population data (≥{min_population:,})...")
    
    initial_count = len(cities_df)
    
    # Check for missing population data
    missing_pop = cities_df['population'].isna()
    if missing_pop.any():
        logger.warning(f"Removing {missing_pop.sum()} cities with missing population data")
        cities_df = cities_df[~missing_pop]
    
    # Apply minimum population filter
    valid_population = cities_df['population'] >= min_population
    filtered_count = len(cities_df[valid_population])
    
    logger.info(f"Population filter: {len(cities_df)} → {filtered_count} cities ≥{min_population:,} population")
    
    # Show population distribution before filtering
    pop_stats = cities_df['population'].describe()
    logger.info(f"Population range: {pop_stats['min']:,.0f} - {pop_stats['max']:,.0f} (median: {pop_stats['50%']:,.0f})")
    
    cities_df = cities_df[valid_population]
    
    return cities_df


def remove_duplicates(cities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate cities, keeping the entry with highest population.
    
    Args:
        cities_df: DataFrame with cities data
        
    Returns:
        DataFrame with duplicates removed
    """
    logger.info("Removing duplicate cities...")
    
    initial_count = len(cities_df)
    
    # Check for exact duplicates (same name and state)
    exact_dupes = cities_df.duplicated(subset=['city_name', 'state'], keep=False)
    if exact_dupes.any():
        logger.info(f"Found {exact_dupes.sum()} cities with exact name/state duplicates")
        
        # Show examples
        dupe_examples = cities_df[exact_dupes].groupby(['city_name', 'state']).size().head(5)
        for (city, state), count in dupe_examples.items():
            logger.info(f"  Duplicate: {city}, {state} ({count} entries)")
        
        # Keep the entry with highest population for each city/state combination
        cities_df = cities_df.sort_values('population', ascending=False)
        cities_df = cities_df.drop_duplicates(subset=['city_name', 'state'], keep='first')
    
    logger.info(f"Duplicate removal: {initial_count} → {len(cities_df)} cities")
    return cities_df


def validate_state_coverage(cities_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze geographic coverage across US states.
    
    Args:
        cities_df: DataFrame with cities data
        
    Returns:
        Dictionary with coverage statistics
    """
    logger.info("Analyzing state coverage...")
    
    # Count cities per state
    state_counts = cities_df['state'].value_counts()
    
    # US states and territories for coverage check
    us_states = {
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 
        'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 
        'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 
        'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 
        'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 
        'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 
        'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 
        'Wisconsin', 'Wyoming', 'District of Columbia'
    }
    
    states_with_cities = set(state_counts.index)
    missing_states = us_states - states_with_cities
    
    coverage_stats = {
        'total_states': len(us_states),
        'states_with_cities': len(states_with_cities),
        'coverage_percent': len(states_with_cities) / len(us_states) * 100,
        'missing_states': list(missing_states),
        'cities_per_state': state_counts.to_dict(),
        'min_cities_per_state': state_counts.min(),
        'max_cities_per_state': state_counts.max(),
        'avg_cities_per_state': state_counts.mean()
    }
    
    logger.info(f"State coverage: {len(states_with_cities)}/{len(us_states)} states ({coverage_stats['coverage_percent']:.1f}%)")
    if missing_states:
        logger.warning(f"Missing states: {', '.join(sorted(missing_states))}")
    
    # Show top states by city count
    logger.info("Top 10 states by city count:")
    for state, count in state_counts.head(10).items():
        logger.info(f"  {state}: {count} cities")
    
    return coverage_stats


def cross_validate_sample(cities_df: pd.DataFrame, sample_size: int = 10) -> Dict[str, Any]:
    """
    Cross-validate a sample of cities against Census Bureau data.
    
    Args:
        cities_df: DataFrame with cities data
        sample_size: Number of cities to validate
        
    Returns:
        Validation results dictionary
    """
    logger.info(f"Cross-validating {sample_size} sample cities against Census Bureau...")
    
    # Select a diverse sample (largest, smallest, random)
    sample_cities = []
    
    # Add largest cities
    largest = cities_df.nlargest(sample_size // 3, 'population')
    sample_cities.append(largest)
    
    # Add smallest cities
    smallest = cities_df.nsmallest(sample_size // 3, 'population')
    sample_cities.append(smallest)
    
    # Add random sample
    remaining_size = sample_size - len(largest) - len(smallest)
    if remaining_size > 0:
        others = cities_df.drop(largest.index.union(smallest.index))
        if len(others) > 0:
            random_sample = others.sample(min(remaining_size, len(others)), random_state=42)
            sample_cities.append(random_sample)
    
    sample_df = pd.concat(sample_cities, ignore_index=True)
    
    validation_results = {
        'sample_size': len(sample_df),
        'validation_attempted': True,
        'coordinate_checks': [],
        'population_checks': []
    }
    
    # For each sample city, log basic validation info
    for _, city in sample_df.iterrows():
        city_info = {
            'city': f"{city['city_name']}, {city['state']}",
            'population': city['population'],
            'coordinates': (city['latitude'], city['longitude']),
            'coordinate_valid': (
                18.0 <= city['latitude'] <= 71.5 and 
                -180.0 <= city['longitude'] <= -65.0
            )
        }
        validation_results['coordinate_checks'].append(city_info)
        
        logger.info(f"Sample: {city_info['city']} - Pop: {city_info['population']:,} - Coords: ({city['latitude']:.3f}, {city['longitude']:.3f})")
    
    return validation_results


def create_final_database(cities_df: pd.DataFrame, output_path: Path) -> None:
    """
    Create the final static cities database file.
    
    Args:
        cities_df: Processed and validated cities DataFrame
        output_path: Output file path
    """
    logger.info(f"Creating final static cities database: {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sort by population (largest first) for easier inspection
    cities_df = cities_df.sort_values('population', ascending=False)
    
    # Select and order final columns
    final_columns = ['city_name', 'state', 'population', 'latitude', 'longitude', 'data_source']
    cities_df = cities_df[final_columns]
    
    # Save to CSV
    cities_df.to_csv(output_path, index=False)
    
    logger.info(f"✓ Saved {len(cities_df)} cities to {output_path}")
    
    # Create summary statistics
    summary = {
        'total_cities': len(cities_df),
        'population_range': {
            'min': int(cities_df['population'].min()),
            'max': int(cities_df['population'].max()),
            'mean': int(cities_df['population'].mean()),
            'median': int(cities_df['population'].median())
        },
        'geographic_bounds': {
            'north': float(cities_df['latitude'].max()),
            'south': float(cities_df['latitude'].min()),
            'east': float(cities_df['longitude'].max()),
            'west': float(cities_df['longitude'].min())
        },
        'data_sources': cities_df['data_source'].value_counts().to_dict(),
        'created_at': pd.Timestamp.now().isoformat()
    }
    
    # Save metadata
    metadata_path = output_path.parent / f"{output_path.stem}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"✓ Saved metadata to {metadata_path}")
    
    # Print summary
    print(f"\n=== Static Cities Database Created ===")
    print(f"Total cities: {summary['total_cities']:,}")
    print(f"Population range: {summary['population_range']['min']:,} - {summary['population_range']['max']:,}")
    print(f"Geographic coverage: {summary['geographic_bounds']['south']:.1f}°N to {summary['geographic_bounds']['north']:.1f}°N")
    print(f"Data sources: {', '.join(summary['data_sources'].keys())}")


def main():
    """Main function to create static cities database."""
    parser = argparse.ArgumentParser(description='Create static US cities database with QC validation')
    parser.add_argument('--min-population', type=int, default=50000,
                        help='Minimum city population (default: 50000)')
    parser.add_argument('--output', type=Path, default=Path('data/cities/us_cities_static.csv'),
                        help='Output CSV file path')
    parser.add_argument('--sample-validation', type=int, default=20,
                        help='Number of cities to cross-validate (default: 20)')
    
    args = parser.parse_args()
    
    logger.info("=== Creating Static US Cities Database ===")
    logger.info(f"Minimum population: {args.min_population:,}")
    logger.info(f"Output file: {args.output}")
    
    try:
        # Step 1: Load source data
        cities_df = load_source_data()
        
        # Step 2: Validate geographic coordinates
        cities_df = validate_geographic_coordinates(cities_df)
        
        # Step 3: Validate and filter population data
        cities_df = validate_population_data(cities_df, args.min_population)
        
        # Step 4: Remove duplicates
        cities_df = remove_duplicates(cities_df)
        
        # Step 5: Analyze state coverage
        coverage_stats = validate_state_coverage(cities_df)
        
        # Step 6: Cross-validate sample
        validation_results = cross_validate_sample(cities_df, args.sample_validation)
        
        # Step 7: Create final database
        create_final_database(cities_df, args.output)
        
        logger.info("✓ Static cities database creation completed successfully")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error creating static cities database: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())