import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_dashboard_data(job_id: str):
    """
    Generate real-time dashboard data from analysis results
    
    Args:
        job_id: Analysis job ID
    
    Returns:
        dict with dashboard metrics and alerts
    """
    try:
        base_path = f"my_volume/sentiment_analysis/{job_id}"
        
        # Load performance summary
        summary_path = os.path.join(base_path, "performance_summary.json")
        if not os.path.exists(summary_path):
            raise FileNotFoundError("Performance summary not found")
        
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        sentiment_dist = summary.get('sentiment_distribution', {})
        
        # Calculate positive percentage
        total = sentiment_dist.get('POSITIVE', 0) + sentiment_dist.get('NEUTRAL', 0) + sentiment_dist.get('NEGATIVE', 0)
        positive_pct = (sentiment_dist.get('POSITIVE', 0) / total * 100) if total > 0 else 0
        
        # Load sentiment trends
        trends_path = os.path.join(base_path, "sentiment_trends.json")
        trends = []
        if os.path.exists(trends_path):
            with open(trends_path, 'r') as f:
                trends_data = json.load(f)
                trends = trends_data.get('trends', [])
        
        # Generate alerts based on thresholds
        alerts = []
        
        negative_pct = (sentiment_dist.get('NEGATIVE', 0) / total * 100) if total > 0 else 0
        
        if negative_pct > 30:
            alerts.append({
                'severity': 'critical',
                'icon': '🚨',
                'message': f'Hoher Anteil negativer Kommentare: {negative_pct:.1f}%',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        elif negative_pct > 20:
            alerts.append({
                'severity': 'warning',
                'icon': '⚠️',
                'message': f'Erhöhter Anteil negativer Kommentare: {negative_pct:.1f}%',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        
        if positive_pct < 50:
            alerts.append({
                'severity': 'warning',
                'icon': '⚠️',
                'message': f'Positiv-Rate unter 50%: {positive_pct:.1f}%',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        
        return {
            'job_id': job_id,
            'sentiment_distribution': sentiment_dist,
            'positive_percentage': positive_pct,
            'sentiment_trends': trends if trends else [sentiment_dist],
            'alerts': alerts,
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard data: {e}")
        raise Exception(f"Dashboard data generation failed: {str(e)}")

def export_dashboard_csv(job_id: str):
    """Export dashboard data as CSV"""
    try:
        data = get_dashboard_data(job_id)
        
        # Create CSV content
        csv_lines = []
        csv_lines.append('Metric,Value')
        csv_lines.append(f"Job ID,{job_id}")
        csv_lines.append(f"Positive Percentage,{data['positive_percentage']:.2f}%")
        csv_lines.append(f"Positive Count,{data['sentiment_distribution'].get('POSITIVE', 0)}")
        csv_lines.append(f"Neutral Count,{data['sentiment_distribution'].get('NEUTRAL', 0)}")
        csv_lines.append(f"Negative Count,{data['sentiment_distribution'].get('NEGATIVE', 0)}")
        csv_lines.append(f"Total Alerts,{len(data['alerts'])}")
        csv_lines.append(f"Last Updated,{data['last_updated']}")
        
        return '\n'.join(csv_lines)
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise Exception(f"CSV export failed: {str(e)}")
