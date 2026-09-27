import http from 'k6/http';
import { check, sleep } from 'k6';

// CivicPulse HPA Load Generator Script (§3.3)
// Simulates concurrent municipal complaint submissions and read traffic
// to drive CPU utilization above the 60% HPA target threshold.

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Baseline warmup
    { duration: '1m', target: 50 },   // Ramp up to trigger CPU scale-out
    { duration: '2m', target: 100 },  // Peak load (pushes replicas towards max 10)
    { duration: '1m', target: 50 },   // Gradual ramp down
    { duration: '30s', target: 0 },   // Cooldown (observes stabilizationWindowSeconds 300)
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests complete under 2s
    http_req_failed: ['rate<0.01'],    // Less than 1% failure rate
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';

const SAMPLE_COMPLAINTS = [
  {
    text: "Burst water main flooding street 14 near park since early morning, water entering garages.",
    location: "Street 14, Sector G-9/2, Islamabad"
  },
  {
    text: "Live high tension electric cable snapped and sparking near central market chowk.",
    location: "Main Commercial Market, Satellite Town, Rawalpindi"
  },
  {
    text: "Huge solid waste trash container overflowing for days, severe foul odor spreading.",
    location: "Block 4, Gulshan-e-Iqbal, Karachi"
  },
  {
    text: "Massive pothole crater on double road causing motorcycle accidents after dusk.",
    location: "Canal Road near Thokar Niaz Baig, Lahore"
  },
  {
    text: "Streetlight fixture knocked down by thunderstorm, complete darkness in residential alley.",
    location: "Lane 7, Saddar Cantt, Multan"
  }
];

export default function () {
  // 1. Submit complaint (POST)
  const complaint = SAMPLE_COMPLAINTS[Math.floor(Math.random() * SAMPLE_COMPLAINTS.length)];
  const postPayload = JSON.stringify({
    text: `${complaint.text} (Load test iteration: ${__VU}-${__ITER})`,
    location: complaint.location,
    reporter_contact: "+923001122334"
  });

  const postParams = {
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': `k6-load-${__VU}-${__ITER}-${Date.now()}`
    },
  };

  const postRes = http.post(`${BASE_URL}/api/complaints`, postPayload, postParams);
  check(postRes, {
    'POST /api/complaints status is 201 or 429': (r) => r.status === 201 || r.status === 429,
  });

  // 2. Query statistics (GET) - exercises Redis read-through cache
  const statsRes = http.get(`${BASE_URL}/api/stats`);
  check(statsRes, {
    'GET /api/stats status is 200': (r) => r.status === 200,
  });

  // Short pause between iterations
  sleep(0.1);
}
