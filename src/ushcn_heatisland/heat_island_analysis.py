"""Heat island analysis functions for urban temperature investigation."""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import stats
from scipy.spatial.distance import cdist


def calculate_urban_rural_statistics(
    results_gdf: gpd.GeoDataFrame,
    classification_column: str = 'urban_classification'
) -> Dict[str, Any]:
    """
    Calculate urban vs rural temperature anomaly statistics.
    
    Args:
        results_gdf: GeoDataFrame with anomaly results and urban classification
        classification_column: Column name containing urban/rural classification
        
    Returns:
        Dictionary with comprehensive urban vs rural statistics
    """
    if classification_column not in results_gdf.columns:
        raise ValueError(f"Classification column '{classification_column}' not found in data")
    
    # Determine the anomaly column to analyze
    anomaly_col = None
    if 'anomaly_celsius' in results_gdf.columns:
        anomaly_col = 'anomaly_celsius'
    elif 'adjustment_impact' in results_gdf.columns:
        anomaly_col = 'adjustment_impact'
    else:
        raise ValueError("No suitable anomaly column found in results")
    
    # Remove stations with missing data
    clean_data = results_gdf.dropna(subset=[anomaly_col, classification_column]).copy()
    
    if len(clean_data) == 0:
        return {'error': 'No valid data for urban/rural analysis'}
    
    # Group by classification
    grouped = clean_data.groupby(classification_column)[anomaly_col]
    
    # Basic statistics by classification
    stats_by_class = {}
    for classification, values in grouped:
        values_array = values.values
        stats_by_class[str(classification)] = {
            'count': int(len(values_array)),
            'mean': float(np.mean(values_array)),
            'median': float(np.median(values_array)),
            'std': float(np.std(values_array)),
            'min': float(np.min(values_array)),
            'max': float(np.max(values_array)),
            'q25': float(np.percentile(values_array, 25)),
            'q75': float(np.percentile(values_array, 75))
        }
    
    # Urban vs Rural comparison (if both exist)
    urban_categories = ['urban_core', 'urban']
    rural_categories = ['rural']
    
    urban_data = clean_data[clean_data[classification_column].isin(urban_categories)][anomaly_col]
    rural_data = clean_data[clean_data[classification_column].isin(rural_categories)][anomaly_col]
    
    comparison_stats = {}
    
    if len(urban_data) > 0 and len(rural_data) > 0:
        # Calculate Urban Heat Island Intensity (UHII)
        uhii = float(urban_data.mean() - rural_data.mean())
        
        # Statistical tests
        # T-test (assumes normal distribution)
        t_stat, t_p_value = stats.ttest_ind(urban_data, rural_data)
        
        # Mann-Whitney U test (non-parametric)
        u_stat, u_p_value = stats.mannwhitneyu(urban_data, rural_data, alternative='two-sided')
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(urban_data) - 1) * urban_data.std()**2 + 
                             (len(rural_data) - 1) * rural_data.std()**2) / 
                            (len(urban_data) + len(rural_data) - 2))
        cohens_d = uhii / pooled_std if pooled_std > 0 else np.nan
        
        # Confidence interval for UHII (95% CI)
        urban_se = urban_data.std() / np.sqrt(len(urban_data))
        rural_se = rural_data.std() / np.sqrt(len(rural_data))
        combined_se = np.sqrt(urban_se**2 + rural_se**2)
        ci_margin = 1.96 * combined_se  # 95% CI
        
        comparison_stats = {
            'urban_heat_island_intensity': uhii,
            'uhii_confidence_interval_lower': uhii - ci_margin,
            'uhii_confidence_interval_upper': uhii + ci_margin,
            'urban_mean': float(urban_data.mean()),
            'rural_mean': float(rural_data.mean()),
            'urban_std': float(urban_data.std()),
            'rural_std': float(rural_data.std()),
            'urban_count': int(len(urban_data)),
            'rural_count': int(len(rural_data)),
            't_test_statistic': float(t_stat),
            't_test_p_value': float(t_p_value),
            'mannwhitney_u_statistic': float(u_stat),
            'mannwhitney_p_value': float(u_p_value),
            'cohens_d_effect_size': float(cohens_d),
            'statistical_significance': 'significant' if min(t_p_value, u_p_value) < 0.05 else 'not_significant'
        }
        
        # Effect size interpretation
        abs_cohens_d = abs(cohens_d) if not np.isnan(cohens_d) else 0
        if abs_cohens_d < 0.2:
            effect_interpretation = 'negligible'
        elif abs_cohens_d < 0.5:
            effect_interpretation = 'small'
        elif abs_cohens_d < 0.8:
            effect_interpretation = 'medium'
        else:
            effect_interpretation = 'large'
        
        comparison_stats['effect_size_interpretation'] = effect_interpretation
    
    return {
        'statistics_by_classification': stats_by_class,
        'urban_vs_rural_comparison': comparison_stats,
        'total_stations_analyzed': int(len(clean_data)),
        'anomaly_column_analyzed': anomaly_col
    }


def analyze_distance_gradients(
    results_gdf: gpd.GeoDataFrame,
    cities_gdf: gpd.GeoDataFrame,
    max_distance: float = 200.0,
    distance_bins: int = 10
) -> Dict[str, Any]:
    """
    Analyze temperature vs distance from urban centers.
    
    Args:
        results_gdf: GeoDataFrame with anomaly results and distance information
        cities_gdf: GeoDataFrame with city locations
        max_distance: Maximum distance to analyze (km)
        distance_bins: Number of distance bins for analysis
        
    Returns:
        Dictionary with gradient analysis results
    """
    # Check for required columns
    if 'distance_to_nearest_city_km' not in results_gdf.columns:
        raise ValueError("Distance to nearest city information not found")
    
    # Determine the anomaly column
    anomaly_col = None
    if 'anomaly_celsius' in results_gdf.columns:
        anomaly_col = 'anomaly_celsius'
    elif 'adjustment_impact' in results_gdf.columns:
        anomaly_col = 'adjustment_impact'
    else:
        raise ValueError("No suitable anomaly column found")
    
    # Clean data
    clean_data = results_gdf.dropna(subset=[anomaly_col, 'distance_to_nearest_city_km']).copy()
    clean_data = clean_data[clean_data['distance_to_nearest_city_km'] <= max_distance]
    
    if len(clean_data) == 0:
        return {'error': 'No valid data for gradient analysis'}
    
    # Create distance bins
    distances = clean_data['distance_to_nearest_city_km']
    anomalies = clean_data[anomaly_col]
    
    bin_edges = np.linspace(0, max_distance, distance_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    binned_stats = []
    for i in range(len(bin_edges) - 1):
        bin_mask = (distances >= bin_edges[i]) & (distances < bin_edges[i + 1])
        bin_data = anomalies[bin_mask]
        
        if len(bin_data) > 0:
            binned_stats.append({
                'distance_bin_center': float(bin_centers[i]),
                'distance_bin_min': float(bin_edges[i]),
                'distance_bin_max': float(bin_edges[i + 1]),
                'count': int(len(bin_data)),
                'mean': float(bin_data.mean()),
                'median': float(bin_data.median()),
                'std': float(bin_data.std()),
                'std_error': float(bin_data.std() / np.sqrt(len(bin_data)))
            })
    
    # Overall correlation analysis
    correlation_coef, correlation_p = stats.pearsonr(distances, anomalies)
    spearman_coef, spearman_p = stats.spearmanr(distances, anomalies)
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(distances, anomalies)
    
    # City size analysis (if population data available)
    city_size_analysis = {}
    if len(cities_gdf) > 0 and 'population' in cities_gdf.columns:
        # Categorize cities by size
        city_populations = cities_gdf['population']
        large_cities_threshold = city_populations.quantile(0.75)
        medium_cities_threshold = city_populations.quantile(0.25)
        
        # Analyze gradients by city size
        for city_size, threshold in [('large', large_cities_threshold), 
                                    ('medium', medium_cities_threshold)]:
            if city_size == 'large':
                city_mask = cities_gdf['population'] >= threshold
            else:
                city_mask = (cities_gdf['population'] >= threshold) & (cities_gdf['population'] < large_cities_threshold)
            
            large_cities = cities_gdf[city_mask]
            
            if len(large_cities) > 0:
                # Find stations near these cities
                city_analysis_data = []
                for _, city in large_cities.iterrows():
                    # Find stations within max_distance of this city
                    city_point = np.array([[city.geometry.x, city.geometry.y]])
                    station_points = np.array([[pt.x, pt.y] for pt in clean_data.geometry])
                    
                    distances_to_city = cdist(station_points, city_point).flatten() * 111  # Convert to km
                    nearby_mask = distances_to_city <= max_distance
                    
                    if np.any(nearby_mask):
                        nearby_stations = clean_data[nearby_mask].copy()
                        nearby_stations['distance_to_this_city'] = distances_to_city[nearby_mask]
                        city_analysis_data.append(nearby_stations)
                
                if city_analysis_data:
                    combined_data = pd.concat(city_analysis_data, ignore_index=True)
                    city_correlation, city_p = stats.pearsonr(
                        combined_data['distance_to_this_city'], 
                        combined_data[anomaly_col]
                    )
                    
                    city_size_analysis[f'{city_size}_cities'] = {
                        'count_cities': int(len(large_cities)),
                        'correlation_coefficient': float(city_correlation),
                        'correlation_p_value': float(city_p),
                        'stations_analyzed': int(len(combined_data))
                    }
    
    return {
        'binned_analysis': binned_stats,
        'correlation_analysis': {
            'pearson_correlation': float(correlation_coef),
            'pearson_p_value': float(correlation_p),
            'spearman_correlation': float(spearman_coef),
            'spearman_p_value': float(spearman_p)
        },
        'linear_regression': {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_value**2),
            'p_value': float(p_value),
            'standard_error': float(std_err)
        },
        'city_size_analysis': city_size_analysis,
        'analysis_parameters': {
            'max_distance_km': float(max_distance),
            'distance_bins': int(distance_bins),
            'stations_analyzed': int(len(clean_data))
        }
    }


def calculate_heat_island_intensity(
    urban_temps: np.ndarray,
    rural_temps: np.ndarray
) -> Dict[str, float]:
    """
    Calculate Urban Heat Island Intensity (UHII) with statistics.
    
    Args:
        urban_temps: Array of urban temperature anomalies
        rural_temps: Array of rural temperature anomalies
        
    Returns:
        Dictionary with UHII and related statistics
    """
    if len(urban_temps) == 0 or len(rural_temps) == 0:
        return {'error': 'Insufficient data for UHII calculation'}
    
    # Remove NaN values
    urban_clean = urban_temps[~np.isnan(urban_temps)]
    rural_clean = rural_temps[~np.isnan(rural_temps)]
    
    if len(urban_clean) == 0 or len(rural_clean) == 0:
        return {'error': 'No valid temperature data after cleaning'}
    
    # Urban Heat Island Intensity
    uhii = float(np.mean(urban_clean) - np.mean(rural_clean))
    
    # Standard errors
    urban_se = float(np.std(urban_clean) / np.sqrt(len(urban_clean)))
    rural_se = float(np.std(rural_clean) / np.sqrt(len(rural_clean)))
    uhii_se = float(np.sqrt(urban_se**2 + rural_se**2))
    
    # Confidence intervals (95%)
    ci_margin = 1.96 * uhii_se
    
    # Statistical significance test
    t_stat, p_value = stats.ttest_ind(urban_clean, rural_clean)
    
    return {
        'uhii_celsius': uhii,
        'uhii_standard_error': uhii_se,
        'uhii_95_ci_lower': uhii - ci_margin,
        'uhii_95_ci_upper': uhii + ci_margin,
        'urban_mean': float(np.mean(urban_clean)),
        'rural_mean': float(np.mean(rural_clean)),
        'urban_count': int(len(urban_clean)),
        'rural_count': int(len(rural_clean)),
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'statistically_significant': bool(p_value < 0.05)
    }


def generate_heat_island_report(
    results_gdf: gpd.GeoDataFrame,
    urban_context: Dict[str, Any],
    cities_gdf: Optional[gpd.GeoDataFrame] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive heat island analysis report.
    
    Args:
        results_gdf: GeoDataFrame with anomaly results and urban classification
        urban_context: Urban context summary from UrbanContextManager
        cities_gdf: GeoDataFrame with city locations for gradient analysis
        
    Returns:
        Comprehensive heat island analysis report
    """
    report = {
        'analysis_metadata': {
            'total_stations': len(results_gdf),
            'analysis_type': 'urban_heat_island_investigation',
            'urban_context_summary': urban_context
        }
    }
    
    try:
        # Urban vs Rural statistical analysis
        urban_rural_stats = calculate_urban_rural_statistics(results_gdf)
        report['urban_rural_analysis'] = urban_rural_stats
        
        # Distance gradient analysis (if cities data available)
        if cities_gdf is not None and len(cities_gdf) > 0:
            try:
                gradient_analysis = analyze_distance_gradients(results_gdf, cities_gdf)
                report['distance_gradient_analysis'] = gradient_analysis
            except Exception as e:
                report['distance_gradient_analysis'] = {'error': str(e)}
        
        # Heat island intensity summary
        if 'urban_vs_rural_comparison' in urban_rural_stats:
            uhii_data = urban_rural_stats['urban_vs_rural_comparison']
            if 'urban_heat_island_intensity' in uhii_data:
                report['heat_island_summary'] = {
                    'heat_island_detected': bool(uhii_data['urban_heat_island_intensity'] > 0),
                    'intensity_celsius': uhii_data['urban_heat_island_intensity'],
                    'statistical_significance': uhii_data['statistical_significance'],
                    'effect_size': uhii_data.get('effect_size_interpretation', 'unknown'),
                    'confidence_interval': [
                        uhii_data.get('uhii_confidence_interval_lower', np.nan),
                        uhii_data.get('uhii_confidence_interval_upper', np.nan)
                    ]
                }
        
        # Scientific interpretation
        interpretation = generate_scientific_interpretation(report)
        report['scientific_interpretation'] = interpretation
        
    except Exception as e:
        report['analysis_error'] = str(e)
    
    return report


def generate_scientific_interpretation(report: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate scientific interpretation of heat island analysis results.
    
    Args:
        report: Heat island analysis report
        
    Returns:
        Dictionary with scientific interpretation and conclusions
    """
    interpretation = {}
    
    # Heat island detection
    if 'heat_island_summary' in report:
        summary = report['heat_island_summary']
        
        if summary.get('heat_island_detected', False):
            intensity = summary.get('intensity_celsius', 0)
            significance = summary.get('statistical_significance', 'unknown')
            effect_size = summary.get('effect_size', 'unknown')
            
            interpretation['heat_island_conclusion'] = (
                f"Urban heat island effect detected with intensity of {intensity:.2f}°C. "
                f"The difference between urban and rural temperatures is {significance} "
                f"with {effect_size} effect size."
            )
            
            # Contextual interpretation
            if intensity > 2.0:
                interpretation['intensity_assessment'] = "Strong heat island effect observed."
            elif intensity > 1.0:
                interpretation['intensity_assessment'] = "Moderate heat island effect observed."
            elif intensity > 0.5:
                interpretation['intensity_assessment'] = "Weak heat island effect observed."
            else:
                interpretation['intensity_assessment'] = "Minimal heat island effect observed."
        else:
            interpretation['heat_island_conclusion'] = (
                "No significant urban heat island effect detected in this analysis."
            )
    
    # Statistical confidence
    if 'urban_rural_analysis' in report:
        stats_data = report['urban_rural_analysis']
        if 'urban_vs_rural_comparison' in stats_data:
            comparison = stats_data['urban_vs_rural_comparison']
            
            urban_count = comparison.get('urban_count', 0)
            rural_count = comparison.get('rural_count', 0)
            
            interpretation['data_quality_assessment'] = (
                f"Analysis based on {urban_count} urban stations and {rural_count} rural stations. "
                f"Sample sizes {'provide adequate' if min(urban_count, rural_count) >= 30 else 'may be limited for'} "
                f"statistical power."
            )
    
    # Gradient analysis interpretation
    if 'distance_gradient_analysis' in report:
        gradient = report['distance_gradient_analysis']
        if 'correlation_analysis' in gradient:
            corr = gradient['correlation_analysis']['pearson_correlation']
            p_val = gradient['correlation_analysis']['pearson_p_value']
            
            if p_val < 0.05:
                if corr < -0.3:
                    interpretation['spatial_pattern'] = (
                        "Strong negative correlation between distance from cities and temperature "
                        "anomalies, indicating clear heat island footprint."
                    )
                elif corr < -0.1:
                    interpretation['spatial_pattern'] = (
                        "Moderate negative correlation suggests measurable heat island influence "
                        "with distance from urban centers."
                    )
                else:
                    interpretation['spatial_pattern'] = (
                        "Weak spatial correlation between distance and temperature anomalies."
                    )
            else:
                interpretation['spatial_pattern'] = (
                    "No significant spatial correlation between distance from cities and "
                    "temperature anomalies detected."
                )
    
    return interpretation