import time
import urllib.request
import json
import threading
import uvicorn
from main import app

def run():
    config = uvicorn.Config(app=app, host='127.0.0.1', port=8000, log_level='error')
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run)
    t.daemon = True
    t.start()
    time.sleep(2)

    endpoints = [
        ('GET', '/api/canteens', None),
        ('GET', '/api/dashboard?canteen_id=canteen-1&date=2026-10-29', None),
        ('GET', '/api/analytics-calendar?canteen_id=canteen-1&year=2026&month=10', None),
        ('GET', '/api/analytics-calendar/date-detail?date=2026-10-29&canteen_id=canteen-1', None),
        ('POST', '/api/forecasting/generate', json.dumps({
            'canteen_id': 'canteen-1',
            'target_date': '2026-10-30',
            'meal_period': 'All',
            'category': 'All',
            'buffer_strategy': 'balanced',
            'kitchen_capacity': 1200
        }).encode()),
        ('POST', '/api/menu-optimizer/optimize', json.dumps({
            'canteen_id': 'canteen-1',
            'week_start_date': '2026-11-02',
            'budget_limit': 35000.0,
            'kitchen_capacity': 1200,
            'priority_profit': 0.35,
            'priority_waste_reduction': 0.25,
            'priority_satisfaction': 0.20,
            'priority_nutrition': 0.20,
            'min_protein_g': 16.0,
            'max_calories': 750,
            'require_vegan_option': True
        }).encode()),
        ('GET', '/api/surplus/listings', None),
        ('GET', '/api/inventory', None),
        ('GET', '/api/inventory/procurement-recommendations', None),
        ('GET', '/api/reports/trends?canteen_id=canteen-1&days=30', None),
        ('GET', '/api/reports/regret-detail?canteen_id=canteen-1&date=2026-10-29', None),
        ('GET', '/api/reports/evaluation?canteen_id=canteen-1', None),
        ('GET', '/api/settings', None)
    ]

    print("\n--- RUNNING CANTEENIQ API VALIDATION SUITE ---")
    all_ok = True
    for method, ep, body in endpoints:
        req = urllib.request.Request(
            'http://127.0.0.1:8000' + ep,
            data=body,
            headers={'Content-Type': 'application/json'} if body else {}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                path_only = ep.split('?')[0]
                status = resp.status
                print(f"PASS: [{method}] {path_only} -> HTTP {status}")
        except Exception as e:
            all_ok = False
            print(f"FAIL: [{method}] {ep} -> {e}")

    server.should_exit = True
    if all_ok:
        print("\nALL 13 API ENDPOINTS PASSED PERFECTLY!\n")
    else:
        print("\nSOME ENDPOINTS FAILED\n")

if __name__ == '__main__':
    run()
