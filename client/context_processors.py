import json
from .models import Notice, JobListing

def marquee_context(request):
    """Makes marquee data available on ALL pages"""
    
    # Get latest notices (you can adjust the number)
    notices = Notice.objects.order_by("-issue_date", "-created_at")[:8]
    
    # Get some recent active jobs
    jobs = JobListing.objects.filter(is_active=True).order_by("-created_at")[:3]

    marquee_items = []

    # Add Notices
    for notice in notices:
        marquee_items.append({
            "text": notice.title,
            "url": f"/notices/{notice.id}/"
        })

    # Add some Jobs (optional)
    for job in jobs:
        marquee_items.append({
            "text": f"Job Opening: {job.job_title} | {job.department}",
            "url": f"/jobs/{job.id}/"
        })

    return {
        "marquee_notices_json": json.dumps(marquee_items, ensure_ascii=False),
    }